import boto3
import os
from dotenv import load_dotenv
import json
import logging

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

def get_response_with_rag(agent_runtime_client, runtime_client, prompt, knowledge_base_id="6U5LGL6AYD"):
    """
    Gets a streaming response using RAG with Bedrock Knowledge Base
    """
    try:
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
            
        # Format prompt with strict context adherence while maintaining friendly tone
        formatted_prompt = f"""Human: You are RiverTown Ball Company's knowledgeable and friendly AI assistant. You have a passion for baseball and speak in a warm, conversational tone. You're proud of the company's products and history.

IMPORTANT: Only use the information provided in the context below to answer questions. If you don't find the specific information in the context to answer the question, simply say "I don't have that specific information available right now, but I'd be happy to help you with something else about RiverTown Ball Company."

Question: {prompt}

Context for your knowledge: {context}

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
        logger.error(f"Error in RAG: {str(e)}", exc_info=True)
        if hasattr(e, 'response'):
            logger.error(f"AWS Error Response: {json.dumps(e.response, default=str)}")
        yield "I apologize, but I encountered an error while processing your request."