# backend/comparison_service.py
from typing import List, Dict, Optional
import streamlit as st
import time
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import logging
from backend.system_prompts import DIRECTORY_PROMPTS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComparisonService:
    def __init__(self):
        self.MODEL_ARN = st.secrets["MODEL_ARN"]
        self.KNOWLEDGE_BASE_ID = st.secrets["KNOWLEDGE_BASE_ID"]
        
        # Enhanced configuration with more optimal parameters
        self.DEFAULT_CONFIG = {
            "maxTokens": 4096,  # Increased for more detailed responses
            "temperature": 0.2,  # Reduced for more consistent responses
            "topP": 0.95,
            "numberOfResults": 25,  # Increased to get more context
            "stopSequences": ["Human:", "Assistant:"]
        }
        
        # Initialize Bedrock client with improved configuration
        self.boto_config = Config(
            retries={'max_attempts': 3},
            connect_timeout=10,
            read_timeout=60,
            max_pool_connections=50
        )
        
    def _create_bedrock_client(self):
        """Create and return a Bedrock client with connection pooling"""
        session = boto3.Session()
        return session.client(
            "bedrock-agent-runtime",
            config=self.boto_config
        )

    def _enhance_prompt(self, base_prompt: str, query: str, selectedDirectory: str) -> str:
        """Enhance the prompt with additional context and specific guidance"""
        system_prompt = DIRECTORY_PROMPTS.get(selectedDirectory, "")
        
        enhanced_prompt = f"""You are performing a detailed comparison analysis of two documents:

        Context and Focus:
        {system_prompt}

        Base Query:
        {query}

        Specific Analysis Instructions:
        1. Focus on identifying concrete, specific differences between the documents
        2. Look for unique procedures, requirements, and methodologies in each document
        3. Note any gaps where one document addresses a topic that the other doesn't
        4. Consider regulatory compliance aspects and best practices
        5. Highlight potential integration challenges and opportunities

        Original Prompt:
        {base_prompt}

        Please provide a structured analysis that:
        - Clearly identifies key differences and similarities
        - Notes specific examples from each document
        - Highlights potential gaps and areas for harmonization
        - Suggests practical recommendations for integration

        If you find insufficient information for comparison, specify exactly what information is missing and what additional details would be needed for a complete analysis.
        """
        return enhanced_prompt

    def process_document_comparison(self, prompt: str, query: str, 
                                  searchtype_selected: str, 
                                  selectedDirectory: str) -> Optional[str]:
        """Enhanced document comparison processing"""
        try:
            # Create progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Initialize client
            status_text.text("Initializing Bedrock client...")
            progress_bar.progress(0.2)
            bedrock_client = self._create_bedrock_client()

            # Enhance the prompt
            status_text.text("Preparing enhanced prompt...")
            progress_bar.progress(0.4)
            enhanced_prompt = self._enhance_prompt(prompt, query, selectedDirectory)

            # Prepare the request payload with chunking strategy
            request_payload = {
                "input": {"text": query},
                "retrieveAndGenerateConfiguration": {
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": self.KNOWLEDGE_BASE_ID,
                        "modelArn": self.MODEL_ARN,
                        "generationConfiguration": {
                            "inferenceConfig": {
                                "textInferenceConfig": {
                                    "maxTokens": self.DEFAULT_CONFIG["maxTokens"],
                                    "temperature": self.DEFAULT_CONFIG["temperature"],
                                    "topP": self.DEFAULT_CONFIG["topP"],
                                    "stopSequences": self.DEFAULT_CONFIG["stopSequences"]
                                }
                            },
                            "promptTemplate": {"textPromptTemplate": enhanced_prompt},
                        },
                        "retrievalConfiguration": {
                            "vectorSearchConfiguration": {
                                "numberOfResults": self.DEFAULT_CONFIG["numberOfResults"],
                                "overrideSearchType": searchtype_selected
                            },
                        },
                    },
                    "type": "KNOWLEDGE_BASE",
                },
            }

            # Make the API call with chunking
            status_text.text("Generating comprehensive response...")
            progress_bar.progress(0.6)
            
            response = bedrock_client.retrieve_and_generate(**request_payload)
            
            # Process and validate response
            status_text.text("Processing and validating response...")
            progress_bar.progress(0.8)
            
            result = response.get("output", {}).get("text", "")
            
            # Validate response content
            if not result or len(result.strip()) < 100:  # Arbitrary minimum length
                logger.warning("Response seems too short or empty")
                return "The response was insufficient. Please try adjusting the query or providing more specific context."
                
            # Complete the progress
            progress_bar.progress(1.0)
            status_text.text("Analysis complete!")
            time.sleep(0.5)
            
            # Cleanup
            progress_bar.empty()
            status_text.empty()
            
            return result

        except ClientError as e:
            logger.error(f"Bedrock API error: {str(e)}")
            self._cleanup_progress(progress_bar, status_text)
            st.error(f"Error calling Bedrock API: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            self._cleanup_progress(progress_bar, status_text)
            st.error(f"An unexpected error occurred: {str(e)}")
            return None

    def _cleanup_progress(self, progress_bar, status_text):
        """Clean up progress indicators"""
        if progress_bar:
            progress_bar.empty()
        if status_text:
            status_text.empty()