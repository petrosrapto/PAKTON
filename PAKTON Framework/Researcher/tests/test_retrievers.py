"""
Tests for the graph building and execution system.
"""
import unittest
from unittest.mock import MagicMock, patch

from src.graph.builder import GraphBuilder


class TestGraphBuilder(unittest.TestCase):
    """Test cases for the graph builder."""
    
    def setUp(self):
        """Set up test environment."""
        self.graph_builder = GraphBuilder()
        self.test_retriever = MagicMock()
        self.test_retriever.name = "test_retriever"
        
    def test_add_retriever(self):
        """Test adding a retriever to the graph."""
        self.graph_builder.add_retriever("test_retriever", self.test_retriever)
        self.assertIn("test_retriever", self.graph_builder.retrievers)
        self.assertEqual(self.graph_builder.retrievers["test_retriever"], self.test_retriever)
        
    def test_add_node(self):
        """Test adding a custom node to the graph."""
        mock_node = MagicMock()
        self.graph_builder.add_node("custom_node", mock_node)
        self.assertIn("custom_node", self.graph_builder.nodes)
        self.assertEqual(self.graph_builder.nodes["custom_node"], mock_node)
    
    def test_add_edge(self):
        """Test adding an edge between nodes."""
        self.graph_builder.add_node("node1", MagicMock())
        self.graph_builder.add_node("node2", MagicMock())
        self.graph_builder.add_edge("node1", "node2")
        
        self.assertIn(("node1", "node2"), self.graph_builder.edges)
        
    def test_compile(self):
        """Test compiling the graph."""
        # Setup basic mock components
        query_extractor = MagicMock()
        router = MagicMock()
        response_generator = MagicMock()
        
        # Mock the internal methods
        with patch.object(GraphBuilder, '_create_query_extractor', return_value=query_extractor), \
             patch.object(GraphBuilder, '_create_router', return_value=router), \
             patch.object(GraphBuilder, '_create_response_generator', return_value=response_generator), \
             patch('langchain.graph.graph.Graph') as mock_graph:
            
            # Add a test retriever
            self.graph_builder.add_retriever("test_retriever", self.test_retriever)
            
            # Compile the graph
            result = self.graph_builder.compile(MagicMock(), "test-run")
            
            # Assert graph was created
            mock_graph.assert_called()
            self.assertIsNotNone(result)
            
    @patch('src.processors.query_extractor.extract_query')
    def test_create_query_extractor(self, mock_extract_query):
        """Test creation of query extractor component."""
        mock_extract_query.return_value = {"query": "test query"}
        
        # Access the protected method for testing
        extractor = self.graph_builder._create_query_extractor()
        
        # Invoke the extractor with test data
        test_state = {"query": "test query"}
        result = extractor.invoke(test_state)
        
        # Check results
        mock_extract_query.assert_called_with(test_state)
        self.assertEqual(result["query"], "test query")


if __name__ == '__main__':
    unittest.main()