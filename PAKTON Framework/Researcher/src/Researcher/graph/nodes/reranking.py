"""
Description:
Document reranking node using cross-encoder models for improving retrieval relevance.
Provides semantic reranking of retrieved documents using transformer-based models
with configurable similarity thresholds and top-k filtering.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""
import torch

from Researcher.types import RetrievalState
from Researcher.utils import logger, config

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

reranker_config = config.get("reranking", {})
top_k = reranker_config.get("top_k", 5)
similarity_threshold = reranker_config.get("similarity_threshold", None)
reranker_type = reranker_config.get("reranker_type", "cross-encoder")
model = reranker_config.get("model", None)
use_reranker = reranker_config.get("use_reranker", False)
use_fp16 = reranker_config.get("use_fp16", False)
cutoff_layers = reranker_config.get("cutoff_layers", None)

# Import and initialize appropriate reranker based on configuration
if use_reranker:
    reranker = None
    if reranker_type == "cross-encoder":
        try:
            from sentence_transformers import CrossEncoder
            reranker = CrossEncoder(model, default_activation_function=torch.nn.Sigmoid(), trust_remote_code=True)
            logger.info(f"Initialized CrossEncoder reranker with model {model}")
        except ImportError:
            logger.error("Failed to import CrossEncoder. Make sure sentence-transformers is installed.")
            raise
    elif reranker_type == "flag-reranker":
        try:
            from FlagEmbedding import FlagReranker
            reranker = FlagReranker(model, use_fp16=use_fp16, trust_remote_code=True)
            logger.info(f"Initialized FlagReranker with model {model} (use_fp16={use_fp16})")
        except ImportError:
            logger.error("Failed to import FlagReranker. Make sure FlagEmbedding is installed.")
            raise
    elif reranker_type == "llm-reranker":
        try:
            from FlagEmbedding import LayerWiseFlagLLMReranker
            reranker = LayerWiseFlagLLMReranker(model, use_fp16=use_fp16, trust_remote_code=True)
            logger.info(f"Initialized LayerWiseFlagLLMReranker with model {model} (use_fp16={use_fp16})")
        except ImportError:
            logger.error("Failed to import LayerWiseFlagLLMReranker. Make sure FlagEmbedding is installed.")
            raise
    else:
        raise ValueError(f"Unknown reranker type: {reranker_type}")

def rerank(state: RetrievalState) -> RetrievalState:
    """
    Re-ranks retrieved documents using the configured reranker model.
    
    The function takes the `retrievedDocuments` list from the state, 
    assigns a relevance score using the selected reranker, and sorts them in descending order.

    Args:
        state (RetrievalState): The current agent state.

    Returns:
        RetrievalState: The updated state with re-ranked documents.
    """

    retrieved_documents = state["retrievedDocuments"]

    if not retrieved_documents:
        return {"responseContext": []}

    if not use_reranker:
        return {"responseContext": retrieved_documents[:top_k]}
    
    logger.info(f"Re-ranking {len(retrieved_documents)} documents using {model} with {reranker_type}")

    query = state["query"]  # Retrieve query from state

    # the whole document will not have the "--- ORIGINAL SPAN OF THE DOCUMENT ---" tag
    retrieved_documents = [doc for doc in retrieved_documents if "--- ORIGINAL SPAN OF THE DOCUMENT ---" in doc.page_content]

    # Check if we have any documents after filtering
    if not retrieved_documents:
        logger.info("No documents left after filtering.")
        return {"responseContext": []}

    # Compute similarity scores based on reranker type
    if reranker_type == "cross-encoder":
        # Generate query-document pairs for cross-encoder (tuples)
        pairs = [(query, doc.page_content) for doc in retrieved_documents]
        scores = reranker.predict(pairs)
    elif reranker_type == "flag-reranker" or reranker_type == "llm-reranker":
        # For FlagReranker, we need list format instead of tuples
        if len(retrieved_documents) == 1:
            # Single document case
            pair_list = [query, retrieved_documents[0].page_content]
            if cutoff_layers:
                scores = [reranker.compute_score(pair_list, cutoff_layers=[cutoff_layers], normalize=True)]
            else:
                scores = [reranker.compute_score(pair_list, normalize=True)]
        else:
            # Multiple documents case - prepare list of lists for FlagReranker
            pairs_list = [[query, doc.page_content] for doc in retrieved_documents]
            # Check if pairs_list is empty before calling compute_score
            if not pairs_list:
                logger.warning("Empty pairs list for reranker.")
                return {"responseContext": []}
            if cutoff_layers:
                scores = reranker.compute_score(pairs_list, cutoff_layers=[cutoff_layers], normalize=True)
            else:
                scores = reranker.compute_score(pairs_list, normalize=True)
    else:
        raise ValueError(f"Unknown reranker type: {reranker_type}")

    # Sort documents by score in descending order
    reranked_docs = sorted(zip(retrieved_documents, scores), key=lambda x: x[1], reverse=True)

    # Add scores to metadata and create new list
    final_docs = []
    for doc, score in reranked_docs:
        if similarity_threshold and score < similarity_threshold:
            continue
        doc.metadata["reranker_score"] = float(score)  # Store score in metadata
        final_docs.append(doc)

    final_docs = final_docs[:top_k]  # Select top-k documents
    logger.info(f"Re-ranked and selected {len(final_docs)} documents.")

    return {"responseContext": final_docs}