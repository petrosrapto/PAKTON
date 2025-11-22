"""
Description:
BERT-based similarity checker using sentence transformers to compute cosine similarity between text inputs for conversation flow control.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
from sentence_transformers import SentenceTransformer, util

# Load a pre-trained sentence transformer model for computing text similarity.
model = SentenceTransformer('all-MiniLM-L6-v2')

def similarity_check(text1: str, text2: str, threshold: float = 0.9) -> bool:
    """
    Computes the cosine similarity between two text inputs and determines 
    whether their similarity exceeds a given threshold.

    Args:
        text1 (str): The first text input.
        text2 (str): The second text input.
        threshold (float, optional): The similarity threshold to determine if 
                                     the texts are considered similar. Default is 0.9.

    Returns:
        bool: True if the similarity score meets or exceeds the threshold, otherwise False.
    """
    
    # Encode the input texts into numerical embeddings using the transformer model.
    embeddings = model.encode([text1, text2], convert_to_tensor=True)

    # Compute the cosine similarity between the two embeddings.
    similarity = util.cos_sim(embeddings[0], embeddings[1])

    # Return True if similarity is above the threshold, otherwise False.
    return similarity.item() >= threshold