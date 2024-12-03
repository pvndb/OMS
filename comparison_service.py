# backend/comparison_service.py
from typing import List, Dict, Tuple
import streamlit as st
import time
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import logging
from backend.system_prompts import DIRECTORY_PROMPTS
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_ARN = st.secrets["MODEL_ARN"]
KNOWLEDGE_BASE_ID = st.secrets["KNOWLEDGE_BASE_ID"]

class ChunkingStrategy:
    @staticmethod
    def create_chunks_by_size(text: str, chunk_size: int = 2000, overlap: int = 200) -> List[Dict]:
        """Fixed size chunking with overlap"""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + chunk_size, text_length)
            
            if start > 0:
                start = start - overlap
            
            chunk = text[start:end]
            
            # Adjust chunk boundaries
            if end < text_length:
                break_points = [
                    chunk.rfind('. '),
                    chunk.rfind('\n\n'),
                    chunk.rfind('. \n'),
                    chunk.rfind('? '),
                    chunk.rfind('! ')
                ]
                last_break = max(break_points)
                
                if last_break != -1:
                    chunk = chunk[:last_break + 1]
                    end = start + last_break + 1

            chunks.append({
                'text': chunk.strip(),
                'start_pos': start,
                'end_pos': end,
                'type': 'size_based'
            })
            
            start = end - overlap

        return chunks

    @staticmethod
    def create_chunks_by_section(text: str) -> List[Dict]:
        """Section-based chunking using headers or section markers"""
        chunks = []
        section_patterns = [
            r'\n#{1,6}\s+.*?\n',  # Markdown headers
            r'\n[A-Z][^.!?]*[:]\n',  # Section titles
            r'\n\d+\.\s+[A-Z][^.!?]*\n'  # Numbered sections
        ]
        
        current_pos = 0
        text_length = len(text)
        
        while current_pos < text_length:
            next_section_start = text_length
            
            # Find next section boundary
            for pattern in section_patterns:
                matches = list(re.finditer(pattern, text[current_pos:]))
                if matches:
                    pos = matches[0].start() + current_pos
                    next_section_start = min(next_section_start, pos)
            
            chunk_text = text[current_pos:next_section_start].strip()
            if chunk_text:
                chunks.append({
                    'text': chunk_text,
                    'start_pos': current_pos,
                    'end_pos': next_section_start,
                    'type': 'section_based'
                })
            
            current_pos = next_section_start + 1

        return chunks

    @staticmethod
    def create_semantic_chunks(text: str, max_chunk_size: int = 2000) -> List[Dict]:
        """Semantic chunking based on content coherence"""
        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = ""
        current_start = 0
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < max_chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'start_pos': current_start,
                        'end_pos': current_start + len(current_chunk),
                        'type': 'semantic'
                    })
                current_chunk = para + "\n\n"
                current_start = current_start + len(current_chunk)
        
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'start_pos': current_start,
                'end_pos': current_start + len(current_chunk),
                'type': 'semantic'
            })
        
        return chunks

def process_document_comparison(prompt: str, query: str, searchtype_selected: str, selectedDirectory: str) -> str:
    """
    Process document comparison with advanced chunking strategies
    """
    DEFAULT_CONFIG = {
        "maxTokens": 4000,
        "temperature": 0.2,
        "topP": 0.95,
        "numberOfResults": 50
    }

    try:
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("Initializing chunking process...")
        progress_bar.progress(0.1)

        # Create chunks using different strategies
        size_chunks = ChunkingStrategy.create_chunks_by_size(query)
        section_chunks = ChunkingStrategy.create_chunks_by_section(query)
        semantic_chunks = ChunkingStrategy.create_semantic_chunks(query)

        # Select best chunking strategy based on document structure
        chunks = select_optimal_chunks(size_chunks, section_chunks, semantic_chunks)

        status_text.text("Processing document chunks...")
        progress_bar.progress(0.2)

        boto_config = Config(
            retries={'max_attempts': 3},
            connect_timeout=5,
            read_timeout=30
        )
        
        session = boto3.Session()
        bedrock_client = session.client(
            "bedrock-agent-runtime",
            config=boto_config
        )

        # Process chunks and aggregate results
        chunk_results = []
        total_chunks = len(chunks)

        for i, chunk in enumerate(chunks):
            status_text.text(f"Processing chunk {i+1} of {total_chunks}...")
            progress_value = 0.2 + (0.6 * (i + 1) / total_chunks)
            progress_bar.progress(progress_value)

            chunk_prompt = f"""
            Analyze this document section:
            {chunk['text']}
            
            {prompt}
            """

            request_payload = {
                "input": {"text": chunk_prompt},
                "retrieveAndGenerateConfiguration": {
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                        "modelArn": MODEL_ARN,
                        "generationConfiguration": {
                            "inferenceConfig": {
                                "textInferenceConfig": {
                                    "maxTokens": DEFAULT_CONFIG["maxTokens"],
                                    "temperature": DEFAULT_CONFIG["temperature"],
                                    "topP": DEFAULT_CONFIG["topP"],
                                }
                            },
                            "promptTemplate": {"textPromptTemplate": prompt},
                        },
                        "retrievalConfiguration": {
                            "vectorSearchConfiguration": {
                                "numberOfResults": DEFAULT_CONFIG["numberOfResults"],
                                'overrideSearchType': searchtype_selected
                            },
                        },
                    },
                    "type": "KNOWLEDGE_BASE",
                },
            }

            try:
                response = bedrock_client.retrieve_and_generate(**request_payload)
                chunk_result = response.get("output", {}).get("text", "")
                chunk_results.append({
                    'text': chunk_result,
                    'chunk_info': chunk
                })
                time.sleep(1)  # Rate limiting
            except Exception as e:
                logger.error(f"Error processing chunk {i+1}: {str(e)}")
                continue

        # Synthesize final results
        status_text.text("Synthesizing results...")
        progress_bar.progress(0.9)

        final_result = synthesize_results(chunk_results, prompt, bedrock_client, DEFAULT_CONFIG, searchtype_selected)

        progress_bar.progress(1.0)
        status_text.text("Analysis complete!")
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()

        return final_result

    except Exception as e:
        if 'progress_bar' in locals():
            progress_bar.empty()
        if 'status_text' in locals():
            status_text.empty()
        logger.error(f"Error in document processing: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
        return None

def select_optimal_chunks(size_chunks: List[Dict], section_chunks: List[Dict], 
                        semantic_chunks: List[Dict]) -> List[Dict]:
    """Select the most appropriate chunking strategy"""
    # Evaluate chunk quality
    size_score = evaluate_chunk_quality(size_chunks)
    section_score = evaluate_chunk_quality(section_chunks)
    semantic_score = evaluate_chunk_quality(semantic_chunks)
    
    # Select best strategy
    scores = {
        'size': size_score,
        'section': section_score,
        'semantic': semantic_score
    }
    
    best_strategy = max(scores.items(), key=lambda x: x[1])[0]
    
    if best_strategy == 'size':
        return size_chunks
    elif best_strategy == 'section':
        return section_chunks
    else:
        return semantic_chunks

def evaluate_chunk_quality(chunks: List[Dict]) -> float:
    """Evaluate the quality of chunks based on various metrics"""
    if not chunks:
        return 0.0
    
    # Calculate metrics
    avg_chunk_size = sum(len(chunk['text']) for chunk in chunks) / len(chunks)
    chunk_size_variance = sum((len(chunk['text']) - avg_chunk_size) ** 2 for chunk in chunks) / len(chunks)
    
    # Evaluate coherence (simple heuristic)
    coherence_score = sum(1 for chunk in chunks if len(chunk['text'].split()) > 50) / len(chunks)
    
    # Combined score
    score = (1000 / chunk_size_variance) * coherence_score if chunk_size_variance > 0 else 0
    
    return score

def synthesize_results(chunk_results: List[Dict], prompt: str, 
                      bedrock_client, config: Dict, searchtype: str) -> str:
    """Synthesize results from all chunks"""
    synthesis_prompt = "Synthesize the following analysis results:\n\n"
    
    for result in chunk_results:
        synthesis_prompt += f"Section ({result['chunk_info']['type']}):\n{result['text']}\n\n"

    request_payload = {
        "input": {"text": synthesis_prompt},
        "retrieveAndGenerateConfiguration": {
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                "modelArn": MODEL_ARN,
                "generationConfiguration": {
                    "inferenceConfig": {
                        "textInferenceConfig": {
                            "maxTokens": config["maxTokens"],
                            "temperature": config["temperature"],
                            "topP": config["topP"],
                        }
                    },
                    "promptTemplate": {"textPromptTemplate": prompt},
                },
                "retrievalConfiguration": {
                    "vectorSearchConfiguration": {
                        "numberOfResults": config["numberOfResults"],
                        'overrideSearchType': searchtype
                    },
                },
            },
            "type": "KNOWLEDGE_BASE",
        },
    }

    try:
        response = bedrock_client.retrieve_and_generate(**request_payload)
        return response.get("output", {}).get("text", "")
    except Exception as e:
        logger.error(f"Error in synthesis: {str(e)}")
        return "\n".join(result['text'] for result in chunk_results)

# Export the function
__all__ = ['process_document_comparison']
