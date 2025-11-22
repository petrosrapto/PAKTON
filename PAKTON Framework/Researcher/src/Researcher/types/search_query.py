"""
Description:
Pydantic model definition for search queries used in the Researcher agent.
Defines the SearchQuery class with structured fields for query validation and processing.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""
from pydantic import BaseModel, Field

class SearchQuery(BaseModel):
    search_query: str = Field(None, description="Short search query for retrieval.")