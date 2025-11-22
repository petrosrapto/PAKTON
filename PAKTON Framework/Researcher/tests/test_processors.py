"""
Tests for processor components like query extractors, report generators, and routers.
"""
import unittest
from unittest.mock import patch, MagicMock

from src.processors.query_extractor import extract_query
from src.processors.report_generator import generate_report
from langchain_core.messages import AIMessage


class TestQueryExtractor(unittest.TestCase):
    """Test cases for the query extractor processor."""
    
    def test_extract_query_from_state(self):
        """Test extracting query from state with query already provided."""
        state = {"query": "test query"}
        result = extract_query(state)
        
        self.assertEqual(result["query"], "test query")
        
    def test_extract_query_missing(self):
        """Test extracting query when none is provided."""
        state = {"other_key": "value"}
        
        with self.assertRaises(ValueError) as context:
            extract_query(state)
            
        self.assertIn("No query provided", str(context.exception))


class TestReportGenerator(unittest.TestCase):
    """Test cases for the report generator processor."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_llm = MagicMock()
        self.mock_llm.invoke.return_value = AIMessage(content="Generated report content")
        
        self.test_state = {
            "query": "What is AI?",
            "context": ["AI is artificial intelligence", "AI is used in many applications"],
            "retrieval_source": "web",
            "response": "AI stands for artificial intelligence.",
            "llm": self.mock_llm,
            "config": {
                "report": {
                    "format": "markdown",
                    "include_sources": True
                }
            }
        }
    
    def test_generate_report(self):
        """Test basic report generation."""
        result = generate_report(self.test_state)
        
        # Check that LLM was called
        self.mock_llm.invoke.assert_called_once()
        
        # Check that report is in result
        self.assertIn("report", result)
        self.assertEqual(result["report"], "Generated report content")
    
    def test_generate_report_with_string_context(self):
        """Test report generation with string context instead of list."""
        # Update state with string context
        state_with_string = self.test_state.copy()
        state_with_string["context"] = "AI is a technology that simulates human intelligence."
        
        result = generate_report(state_with_string)
        
        # Verify report was generated
        self.assertIn("report", result)
    
    @patch('src.processors.report_generator.get_default_llm')
    def test_generate_report_with_default_llm(self, mock_get_default_llm):
        """Test report generation with default LLM when none provided in state."""
        # Create a state without an LLM
        state_without_llm = self.test_state.copy()
        del state_without_llm["llm"]
        
        # Setup mock default LLM
        default_llm = MagicMock()
        default_llm.invoke.return_value = AIMessage(content="Default LLM report")
        mock_get_default_llm.return_value = default_llm
        
        result = generate_report(state_without_llm)
        
        # Verify default LLM was used
        mock_get_default_llm.assert_called_once()
        default_llm.invoke.assert_called_once()
        self.assertEqual(result["report"], "Default LLM report")
    
    def test_generate_report_with_custom_format(self):
        """Test report generation with custom format configuration."""
        # Create state with custom format
        custom_format_state = self.test_state.copy()
        custom_format_state["config"]["report"]["format"] = "outline"
        
        result = generate_report(custom_format_state)
        
        # Check prompt formatting
        prompt_call = self.mock_llm.invoke.call_args[0][0]
        self.assertIn("outline", prompt_call)
    
    def test_generate_report_without_sources(self):
        """Test report generation with sources disabled."""
        # Create state with sources disabled
        no_sources_state = self.test_state.copy()
        no_sources_state["config"]["report"]["include_sources"] = False
        
        result = generate_report(no_sources_state)
        
        # Check prompt formatting
        prompt_call = self.mock_llm.invoke.call_args[0][0]
        self.assertIn("False", prompt_call)
    
    def test_generate_report_with_non_message_response(self):
        """Test handling of non-AIMessage response types."""
        # Make LLM return a string instead of an AIMessage
        self.mock_llm.invoke.return_value = "Plain string report"
        
        result = generate_report(self.test_state)
        
        # Check correct handling of string response
        self.assertEqual(result["report"], "Plain string report")


class TestResponseGenerator(unittest.TestCase):
    """Test cases for the response generator processor."""
    
    @patch('src.processors.response_generator.generate_response')
    def test_response_generation(self, mock_generate):
        """Test response generation from retrieved information."""
        # Setup mock
        mock_generate.return_value = {"response": "Generated answer about AI"}
        
        # Import here to avoid circular imports in test setup
        from src.processors.response_generator import generate_response
        
        # Test with sample state
        state = {
            "query": "What is AI?",
            "context": ["AI refers to artificial intelligence"],
        }
        
        result = generate_response(state)
        self.assertEqual(result["response"], "Generated answer about AI")


class TestRouter(unittest.TestCase):
    """Test cases for the router processor."""
    
    @patch('src.processors.router.route_query')
    def test_query_routing(self, mock_route):
        """Test routing of queries to appropriate retrievers."""
        # Setup mock
        mock_route.return_value = {"retrieval_source": "web"}
        
        # Import here to avoid circular imports in test setup
        from src.processors.router import route_query
        
        # Test with sample state
        state = {
            "query": "What is the latest news about AI?",
            "retrievers": ["web", "wikipedia"]
        }
        
        result = route_query(state)
        self.assertEqual(result["retrieval_source"], "web")


if __name__ == '__main__':
    unittest.main()