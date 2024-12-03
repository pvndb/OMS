# backend/comparison_service.py
from typing import List, Dict, Optional
import streamlit as st
import time
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import logging
import json
from backend.system_prompts import DIRECTORY_PROMPTS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.MODEL_ARN = st.secrets["MODEL_ARN"]
        self.KNOWLEDGE_BASE_ID = st.secrets["KNOWLEDGE_BASE_ID"]
        self.DEFAULT_CONFIG = {
            "maxTokens": 4000,
            "temperature": 0.2,
            "topP": 0.95,
            "numberOfResults": 25,
            "stopSequences": ["Human:", "Assistant:"]
        }
        
        # Initialize Bedrock client configuration
        self.boto_config = Config(
            retries={'max_attempts': 3},
            connect_timeout=10,
            read_timeout=60,
            max_pool_connections=50
        )

    def create_bedrock_client(self):
        """Create Bedrock client with connection pooling"""
        try:
            session = boto3.Session()
            return session.client(
                "bedrock-agent-runtime",
                config=self.boto_config
            )
        except Exception as e:
            logger.error(f"Failed to create Bedrock client: {str(e)}")
            raise

    def chunk_document(self, text: str, chunk_size: int = 2000) -> List[str]:
        """Split document into manageable chunks"""
        chunks = []
        sentences = text.replace('\n', ' ').split('. ')
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            sentence_size = len(sentence)
            
            if current_size + sentence_size > chunk_size and current_chunk:
                chunks.append('. '.join(current_chunk) + '.')
                current_chunk = []
                current_size = 0
                
            current_chunk.append(sentence)
            current_size += sentence_size
            
        if current_chunk:
            chunks.append('. '.join(current_chunk) + '.')
            
        return chunks

    def enhance_prompt(self, base_prompt: str, chunk: str, context: str) -> str:
        """Enhance prompt with context and specific instructions"""
        return f"""Context: {context}

Document Section to Analyze:
{chunk}

Base Instructions:
{base_prompt}

Please provide:
1. Key points and findings from this section
2. Relevant comparisons with reference documents
3. Any gaps or areas needing clarification
4. Specific recommendations for harmonization

Note: Focus on concrete, specific details rather than general observations."""

    def process_document_comparison(self, prompt: str, query: str, 
                                  searchtype_selected: str, 
                                  selectedDirectory: str) -> str:
        """Process document comparison with enhanced error handling"""
        progress_bar = None
        status_text = None
        
        try:
            # Initialize progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Create client
            status_text.text("Initializing analysis...")
            progress_bar.progress(0.1)
            bedrock_client = self.create_bedrock_client()
            
            # Get context from directory prompts
            context = DIRECTORY_PROMPTS.get(selectedDirectory, "")
            
            # Chunk document
            status_text.text("Processing document...")
            progress_bar.progress(0.2)
            chunks = self.chunk_document(query)
            
            # Process each chunk
            chunk_results = []
            for i, chunk in enumerate(chunks):
                status_text.text(f"Analyzing section {i+1} of {len(chunks)}...")
                progress = 0.2 + (0.6 * (i + 1) / len(chunks))
                progress_bar.progress(progress)
                
                enhanced_prompt = self.enhance_prompt(prompt, chunk, context)
                
                request_payload = {
                    "input": {"text": enhanced_prompt},
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
                
                try:
                    response = bedrock_client.retrieve_and_generate(**request_payload)
                    result = response.get("output", {}).get("text", "")
                    if result:
                        chunk_results.append(result)
                    time.sleep(1)  # Rate limiting
                except ClientError as e:
                    logger.error(f"Bedrock API error processing chunk {i+1}: {str(e)}")
                    continue
                
            # Synthesize results
            status_text.text("Synthesizing analysis...")
            progress_bar.progress(0.9)
            
            if not chunk_results:
                raise ValueError("No valid results obtained from analysis")
                
            final_synthesis = self.synthesize_results(chunk_results, bedrock_client, 
                                                    prompt, searchtype_selected)
            
            # Cleanup
            progress_bar.progress(1.0)
            status_text.text("Analysis complete!")
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            
            return final_synthesis

        except Exception as e:
            logger.error(f"Error in document processing: {str(e)}")
            if progress_bar:
                progress_bar.empty()
            if status_text:
                status_text.empty()
            st.error(f"An error occurred during analysis: {str(e)}")
            return None
            
    def synthesize_results(self, chunk_results: List[str], bedrock_client,
                          original_prompt: str, searchtype: str) -> str:
        """Synthesize results from all chunks"""
        try:
            synthesis_prompt = f"""Synthesize the following analysis results into a coherent summary:

Analysis Sections:
{chr(10).join(f'Section {i+1}:{chr(10)}{result}{chr(10)}' for i, result in enumerate(chunk_results))}

Original Query Context:
{original_prompt}

Please provide:
1. Executive Summary
2. Key Findings
3. Detailed Analysis
4. Recommendations
5. Next Steps"""

            request_payload = {
                "input": {"text": synthesis_prompt},
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
                            "promptTemplate": {"textPromptTemplate": synthesis_prompt},
                        },
                        "retrievalConfiguration": {
                            "vectorSearchConfiguration": {
                                "numberOfResults": self.DEFAULT_CONFIG["numberOfResults"],
                                "overrideSearchType": searchtype
                            },
                        },
                    },
                    "type": "KNOWLEDGE_BASE",
                },
            }

            response = bedrock_client.retrieve_and_generate(**request_payload)
            return response.get("output", {}).get("text", "")

        except Exception as e:
            logger.error(f"Error in synthesis: {str(e)}")
            # Fallback to simple concatenation
            return "\n\n".join([
                "# Analysis Summary",
                "(Note: Detailed synthesis failed, showing individual analyses)",
                *chunk_results
            ])

def process_document_comparison(prompt: str, query: str, 
                              searchtype_selected: str, 
                              selectedDirectory: str) -> str:
    """Main entry point for document comparison"""
    processor = DocumentProcessor()
    return processor.process_document_comparison(
        prompt=prompt,
        query=query,
        searchtype_selected=searchtype_selected,
        selectedDirectory=selectedDirectory
    )

# Export the function
__all__ = ['process_document_comparison']