import boto3
import os
from dotenv import load_dotenv
import json

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

def get_response_with_rag(agent_runtime_client, runtime_client, prompt, knowledge_base_id="A2QCDWSKKV"):
    """
    Gets a streaming response using RAG with Bedrock Knowledge Base
    """
    try:
        # Complete system prompt
        system_prompt = """You are a friendly and knowledgeable question-answering agent for the Rivertown Ball Company. Your mission is to assist users by answering their questions based on a set of provided search results. Your goal is to provide accurate, helpful, and engaging answers. Remember, your personality shines through—you are warm, approachable, and helpful, while also being precise and trustworthy. Also note the company sells High end exotic designer wooden craft balls. while we do have many different designs, styles, and options. We do not make sports balls. 

I will provide you with a set of search results that may contain the information needed to answer the user's question. The user will ask you a question, and it's your job to answer it using only the information from the search results. If the search results do not contain the information needed to answer the question, let the user know politely that you don't know the answer to their question.

Don't let the user know you searched for the answer, just present it as you knew it the entire time as fact. Do not ever cite any sources.

If the user asserts something as a fact, don't automatically accept it—double-check it against the search results to make sure it's accurate. Your job is to be both supportive and trustworthy, so validating information is key."""
        
        # Query the knowledge base using bedrock-agent-runtime
        retrieve_response = agent_runtime_client.retrieve_and_generate(
            input={
                'text': prompt
            },
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': knowledge_base_id,
                    'modelArn': "anthropic.claude-instant-v1",
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': 3
                        }
                    }
                }
            }
        )

        # Extract retrieved passages
        retrieved_passages = []
        for result in retrieve_response.get('retrievalResults', []):
            retrieved_passages.append(result.get('content', ''))
        
        # Format prompt
        context = "\n".join(retrieved_passages)
        formatted_prompt = f"\n\nHuman: {system_prompt}\n\nContext: {context}\n\nHuman: {prompt}\n\nAssistant:"

        # Get streaming response
        body = json.dumps({
            "prompt": formatted_prompt,
            "max_tokens_to_sample": 2048,
            "temperature": 0.7,
            "top_p": 1,
            "stop_sequences": ["\n\nHuman:", "\n\nAssistant:"],
            "anthropic_version": "bedrock-2023-05-31"
        })
        
        response = runtime_client.invoke_model_with_response_stream(
            modelId="anthropic.claude-instant-v1",
            body=body,
            contentType="application/json",
            accept="application/json"
        )
        
        # Stream the response chunks
        for event in response.get('body'):
            if 'chunk' in event:
                chunk_data = json.loads(event['chunk']['bytes'].decode())
                yield chunk_data.get('completion', '')
        
    except Exception as e:
        print(f"Error: {e}")
        yield "I apologize, but I encountered an error while processing your request."