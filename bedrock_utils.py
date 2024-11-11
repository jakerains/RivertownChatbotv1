import boto3
import os
from dotenv import load_dotenv
import json
import logging
from dynamo_utils import get_customer_orders, init_dynamodb
import re
import requests
from typing import Dict, Any, Tuple

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def init_bedrock():
    """Initialize and return Bedrock clients"""
    load_dotenv('.env.local')
    
    # Initialize bedrock-runtime client
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name="us-east-1"
    )
    
    # Initialize bedrock-agent-runtime client for knowledge base operations
    bedrock_agent_runtime = boto3.client(
        service_name="bedrock-agent-runtime",
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name="us-east-1"
    )
    
    return bedrock_agent_runtime, bedrock_runtime

def extract_customer_name(prompt: str) -> tuple[str, str] | None:
    """Extract first and last name from prompt using regex"""
    patterns = [
        r"show\s+(?:me\s+)?(?:the\s+)?(?:orders?\s+(?:for|of)\s+)?([a-zA-Z]+)\s+([a-zA-Z]+)",
        r"(?:what\s+(?:are|were)\s+)?([a-zA-Z]+)\s+([a-zA-Z]+)(?:'s)?\s+orders?",
        r"find\s+(?:the\s+)?orders?\s+(?:for|of)\s+([a-zA-Z]+)\s+([a-zA-Z]+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, prompt.lower())
        if match:
            return match.group(1).title(), match.group(2).title()
    return None

def format_order_table(orders: list) -> str:
    """Format orders into a clean markdown table with emojis"""
    # Create markdown table header with emojis
    table = "\n📦 **Order History**\n"
    table += "| 🔖 Order ID | ⚪ Product | 🔢 Quantity | 📅 Date | 💰 Total |\n"
    table += "|------------|------------|-------------|---------|----------|\n"
    
    # Add each order as a row
    for order in orders:
        # Truncate order_id if too long
        order_id = order['order_id'][:8] + "..." if len(order['order_id']) > 8 else order['order_id']
        
        # Format the row
        table += f"| {order_id} | {order['product']} | {order['quantity']} | {order['order_date']} | ${order['total_price']:.2f} |\n"
    
    return table

def get_response_with_rag(agent_runtime_client, runtime_client, prompt, phone_number=None, dynamodb=None, knowledge_base_id="6U5LGL6AYD"):
    """Gets a streaming response using RAG with Bedrock Knowledge Base and order lookup"""
    try:
        # 1. First priority: Check for order lookup request
        name_match = extract_customer_name(prompt)
        if name_match and dynamodb:
            first_name, last_name = name_match
            orders = get_customer_orders(dynamodb, first_name, last_name)
            
            if orders:
                order_table = format_order_table(orders)
                yield f"🔍 Here are the orders for {first_name} {last_name}:\n{order_table}"
                return
            else:
                yield f"❌ I couldn't find any orders for {first_name} {last_name}."
                return

        # 2. Second priority: Handle customer service calls
        cs_keywords = [
            'speak to someone',
            'talk to a person', 
            'customer service',
            'representative',
            'speak to a human',
            'talk to someone',
            'call me',
            'contact me'
        ]
        
        is_cs_request = any(keyword in prompt.lower() for keyword in cs_keywords)
        is_just_numbers = sum(c.isdigit() for c in prompt) >= 10
        
        if is_cs_request or phone_number or is_just_numbers:
            cs_response = handle_customer_service_request(prompt, phone_number)
            if cs_response:
                yield cs_response
                return

        # 3. Fall back to RAG if no specific handlers matched
        logger.info(f"No specific handlers matched, falling back to RAG for: {prompt}")
        
        # Get retrieved passages from knowledge base
        retrieve_response = agent_runtime_client.retrieve(
            knowledgeBaseId=knowledge_base_id,
            retrievalQuery={
                "text": prompt
            },
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": 3
                }
            }
        )
        
        # Extract and combine retrieved passages
        retrieved_passages = []
        for result in retrieve_response.get('retrievalResults', []):
            content = (
                result.get('content', {}).get('text', '') or
                result.get('content', '') or
                ''
            )
            if content:
                retrieved_passages.append(content)
        
        context = "\n".join(retrieved_passages)
        
        # Format prompt for the model
        formatted_prompt = f"""Human: You are RiverTown's enthusiastic product specialist! You love talking about our artisanal creations and have a warm, friendly personality. You're passionate about craftsmanship and excited to share details about our products.

Remember to:
- Be enthusiastic and engaging
- Use natural, conversational language
- Share your excitement about our products
- Keep responses friendly and warm
- If you don't know something specific, be honest but stay positive

Question: {prompt}

Context: {context}

Assistant:"""

        # Get streaming response
        body = json.dumps({
            "prompt": formatted_prompt,
            "max_tokens_to_sample": 2048,
            "temperature": 0.7,
            "top_p": 1,
            "stop_sequences": ["\n\nHuman:", "\n\nAssistant:"],
            "anthropic_version": "bedrock-2023-05-31"
        })
        
        logger.debug("Sending request to model...")
        response = runtime_client.invoke_model_with_response_stream(
            modelId="anthropic.claude-instant-v1",
            body=body,
            contentType="application/json",
            accept="application/json"
        )
        
        # Stream the response chunks with debug logging
        for event in response.get('body'):
            if 'chunk' in event:
                chunk_data = json.loads(event['chunk']['bytes'].decode())
                completion = chunk_data.get('completion', '')
                logger.debug(f"Received chunk: {completion}")
                yield completion
        
    except Exception as e:
        logger.error(f"Error in response generation: {str(e)}", exc_info=True)
        yield "I apologize, but I encountered an error while processing your request."

def init_bland():
    """Initialize Bland API configuration"""
    load_dotenv('.env.local')
    return {
        'headers': {
            'Authorization': os.getenv('BLAND_API_KEY')
        },
        'base_url': 'https://us.api.bland.ai/v1'
    }

def extract_phone_number(prompt: str) -> str | None:
    """Extract phone number from prompt using regex"""
    # Clean the input string of any whitespace and common separators
    cleaned_number = ''.join(filter(str.isdigit, prompt))
    
    # If we have exactly 10 digits, assume it's a valid US phone number
    if len(cleaned_number) == 10:
        return f"+1{cleaned_number}"
    
    # If we have 11 digits and it starts with 1, also valid
    if len(cleaned_number) == 11 and cleaned_number.startswith('1'):
        return f"+{cleaned_number}"
    
    # For any other length, return None
    return None

def handle_customer_service_request(prompt: str, phone_number: str = None) -> str:
    """Handles customer service related requests and initiates calls if needed"""
    try:
        # Check if this is a customer service request or just a phone number
        is_cs_request = any(keyword in prompt.lower() for keyword in [
            'speak to someone', 'talk to a person', 'customer service',
            'representative', 'speak to a human', 'talk to someone',
            'call me', 'contact me'
        ])
        is_just_numbers = sum(c.isdigit() for c in prompt) >= 10
        
        # Initial CS request
        if is_cs_request:
            return ("I'd be happy to have Sara, our customer service specialist, give you a call! "
                   "What's the best phone number to reach you at? You can share it in any format "
                   "like: 123-456-7890 or (123) 456-7890")
        
        # Handle phone number input
        if is_just_numbers:
            formatted_phone = f"+1{''.join(filter(str.isdigit, prompt))[-10:]}"
            
            # Initiate the call
            data = {
                "phone_number": formatted_phone,
                "task": """You are Sara from Rivertown Ball Company following up on a chat conversation they were just having, looking to ask them if they have any questions you can help with. 
                Start the call with: "Hi, this is Sara from Rivertown Ball Company!"
                Be warm, friendly and helpful while assisting with their questions about our artisanal wooden balls.
                Make them feel valued and excited about our products!""",
                "model": "turbo",
                "voice": "Alexa",
                "max_duration": 12,
                "wait_for_greeting": True,
                "temperature": 0.8
            }
            
            bland_config = init_bland()
            response = requests.post(
                f"{bland_config['base_url']}/calls",
                json=data,
                headers=bland_config['headers']
            )
            
            if response.status_code == 200:
                return (f"Perfect! Sara will be calling you right now at " 
                       f"{formatted_phone[-10:-7]}-{formatted_phone[-7:-4]}-{formatted_phone[-4:]}. "
                       "She's looking forward to helping you with any questions you have about our "
                       "artisanal wooden balls!")
            else:
                logger.error(f"Failed to initiate customer service call: {response.text}")
                return ("I apologize, but I'm having trouble connecting with Sara at the moment. "
                       "Please try again in a few minutes or call us directly at (719) 266-2837")
        
        return None
        
    except Exception as e:
        logger.error(f"Error in customer service request handling: {str(e)}", exc_info=True)
        return ("I apologize, but I'm experiencing technical difficulties arranging the call. "
               "Please contact our customer service directly at (719) 266-2837")