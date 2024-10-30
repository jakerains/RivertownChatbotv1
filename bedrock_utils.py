import boto3
import os
from dotenv import load_dotenv
import json
import logging
from dynamo_utils import get_customer_orders, init_dynamodb
import re

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
        region_name=os.getenv('AWS_REGION')
    )
    
    # Initialize bedrock-agent-runtime client for knowledge base operations
    bedrock_agent_runtime = boto3.client(
        service_name="bedrock-agent-runtime",
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )
    
    return bedrock_agent_runtime, bedrock_runtime

def extract_name_from_prompt(prompt: str) -> tuple[str, str] | None:
    """Extract first and last name from prompt using regex"""
    # Look for patterns like "show me jake rains orders" or "jake rains orders"
    patterns = [
        r"(?:show me|get|find|display) ([A-Za-z]+)\s+([A-Za-z]+)(?:'s)? (?:order|orders)",
        r"([A-Za-z]+)\s+([A-Za-z]+)(?:'s)? (?:order|orders)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, prompt.lower())
        if match:
            return match.group(1).title(), match.group(2).title()
    return None

def format_order_table(orders: list) -> str:
    """Format orders into a clean markdown table for Streamlit"""
    # Create markdown table header
    table = "\n| Order ID | Product | Quantity | Date | Total |\n"
    table += "|----------|----------|-----------|------|--------|\n"
    
    # Add each order as a row
    for order in orders:
        # Truncate order_id if too long
        order_id = order['order_id'][:8] + "..." if len(order['order_id']) > 8 else order['order_id']
        
        # Format the row
        table += f"| {order_id} | {order['product']} | {order['quantity']} | {order['order_date']} | ${order['total_price']:.2f} |\n"
    
    return table

def get_response_with_rag(agent_runtime_client, runtime_client, prompt, knowledge_base_id="6U5LGL6AYD"):
    """Gets a streaming response using RAG with Bedrock Knowledge Base and order lookup"""
    try:
        # First, check if this is an order-related query
        name_match = extract_name_from_prompt(prompt)
        
        if any(keyword in prompt.lower() for keyword in ['order', 'purchase', 'bought']) and name_match:
            first_name, last_name = name_match
            logger.info(f"Order query detected for {first_name} {last_name}")
            
            # Initialize DynamoDB and get orders
            dynamodb = init_dynamodb()
            orders = get_customer_orders(dynamodb, first_name, last_name)
            
            if orders:
                response = (
                    f"### 📦 Order History for {first_name} {last_name}\n"
                    f"{format_order_table(orders)}\n"
                    f"*Total Orders: {len(orders)}*"
                )
                yield response
                return  # Exit here if it's an order query
            else:
                yield f"I couldn't find any orders for {first_name} {last_name}."
                return  # Exit here if no orders found

        # Only proceed with RAG if it's not an order query
        logger.info(f"Processing regular RAG query: {prompt}")
        
        logger.info(f"Starting RAG process for prompt: {prompt}")
        logger.info(f"Using knowledge base ID: {knowledge_base_id}")
        
        # First try a simple retrieve to debug
        logger.debug("Attempting direct retrieve first...")
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
        
        # Log the raw retrieve response
        logger.debug(f"Raw retrieve response: {json.dumps(retrieve_response, default=str)}")
        
        # Extract and log retrieved results
        retrieved_results = retrieve_response.get('retrievalResults', [])
        logger.info(f"Number of retrieved results: {len(retrieved_results)}")
        
        retrieved_passages = []
        for result in retrieved_results:
            # Log the full structure of each result
            logger.debug(f"Result structure: {json.dumps(result, default=str)}")
            
            # Try different possible paths to content
            content = (
                result.get('content', {}).get('text', '') or
                result.get('content', '') or
                ''
            )
            if content:
                retrieved_passages.append(content)
                logger.info(f"Retrieved passage: {content}")
            else:
                logger.warning(f"Could not extract content from result: {result}")
        
        # Log the final context
        context = "\n".join(retrieved_passages)
        logger.info(f"Combined context being sent to model: {context}")
        
        if not context:
            logger.warning("No context was retrieved from the knowledge base!")
            
        # Format prompt with a more natural, enthusiastic tone
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