"""
Tests for the Researcher agent.
"""
import unittest
from unittest.mock import MagicMock, patch

from MultiAgentFramework.Researcher.src.Researcher.agent import Researcher
from langchain_core.messages import HumanMessage


class TestResearcherAgent(unittest.TestCase):
    """Test cases for the Researcher agent."""

    def setUp(self):
        """Set up test environment."""
        self.config = {
            "enable_web": True,
            "enable_wikipedia": True,
            "run_name": "test-researcher"
        }
        
    def test_initialization(self):
        """Test that the agent initializes correctly."""
        researcher = Researcher(self.config)
        self.assertIsNotNone(researcher.graph)
        self.assertEqual(researcher.config["run_name"], "test-researcher")
        
    def test_setup_retrievers(self):
        """Test that retrievers are set up based on config."""
        with patch('src.agent.researcher.WebRetriever') as mock_web:
            with patch('src.agent.researcher.WikipediaRetriever') as mock_wiki:
                researcher = Researcher(self.config)
                
                # Check that retrievers were initialized
                mock_web.assert_called_once()
                mock_wiki.assert_called_once()
                
    def test_search_with_query(self):
        """Test search functionality with a basic query."""
        researcher = Researcher(self.config)
        researcher.graph = MagicMock()
        researcher.graph.invoke.return_value = {"answer": "Test result"}
        
        result = researcher.search("What is AI?")
        
        researcher.graph.invoke.assert_called_once()
        self.assertEqual(result["answer"], "Test result")
        
    def test_search_with_specific_retriever(self):
        """Test search with a specific retrieval source."""
        researcher = Researcher(self.config)
        researcher.graph = MagicMock()
        
        researcher.search("What is quantum computing?", retrieval_source="wikipedia")
        
        call_args = researcher.graph.invoke.call_args[0][0]
        self.assertEqual(call_args["retrieval_source"], "wikipedia")
        
    def test_interact_with_messages(self):
        """Test interaction with message objects."""
        researcher = Researcher(self.config)
        researcher.graph = MagicMock()
        researcher.graph.invoke.return_value = {"answer": "Response to message"}
        
        messages = [HumanMessage(content="Tell me about climate change")]
        result = researcher.interact(messages)
        
        researcher.graph.invoke.assert_called_once()
        self.assertEqual(result["answer"], "Response to message")
        
    @patch('src.agent.researcher.MemorySaver')
    def test_build_graph(self, mock_memory_saver):
        """Test graph building functionality."""
        mock_memory = MagicMock()
        mock_memory_saver.return_value = mock_memory
        
        researcher = Researcher(self.config)
        researcher.graph_builder = MagicMock()
        
        # Reset and rebuild the graph
        researcher._build_graph()
        
        # Check that graph was compiled with correct parameters
        researcher.graph_builder.compile.assert_called_with(
            memory_saver=mock_memory,
            run_name="test-researcher"
        )


if __name__ == '__main__':
    unittest.main()