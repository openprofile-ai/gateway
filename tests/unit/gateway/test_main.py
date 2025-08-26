import unittest
from unittest.mock import MagicMock, patch

from fastmcp.server import FastMCP

from gateway.main import create_application


class TestMain(unittest.TestCase):
    """Test cases for the main application module."""

    def setUp(self):
        """Set up test fixtures before each test."""
        # Create a mock for FastMCP
        self.mock_mcp = MagicMock(spec=FastMCP)

    @patch('gateway.main.EnableFactPodHandler')
    @patch('gateway.main.DisableFactPodHandler')
    @patch('gateway.main.ListOfCategoriesHandler')
    @patch('gateway.main.FactsByCategoryHandler')
    def test_create_application_with_instance(self, mock_facts, mock_list, mock_disable, mock_enable):
        """Test create_application when an MCP instance is provided."""
        # Act
        result = create_application(self.mock_mcp)

        # Assert
        # Verify that all handlers were initialized with the MCP instance
        mock_enable.assert_called_once_with(self.mock_mcp)
        mock_disable.assert_called_once_with(self.mock_mcp)
        mock_list.assert_called_once_with(self.mock_mcp)
        mock_facts.assert_called_once_with(self.mock_mcp)

        # Verify that the provided MCP instance is returned
        self.assertEqual(result, self.mock_mcp)

    @patch('gateway.main.FastMCP')
    @patch('gateway.main.EnableFactPodHandler')
    @patch('gateway.main.DisableFactPodHandler')
    @patch('gateway.main.ListOfCategoriesHandler')
    @patch('gateway.main.FactsByCategoryHandler')
    def test_create_application_without_instance(self, mock_facts, mock_list, mock_disable, mock_enable, mock_fastmcp):
        """Test create_application when no MCP instance is provided."""
        # Arrange
        mock_new_mcp = MagicMock(spec=FastMCP)
        mock_fastmcp.return_value = mock_new_mcp

        # Act
        result = create_application()

        # Assert
        # Verify FastMCP was created with the default server name
        mock_fastmcp.assert_called_once_with("OpenProfile.AI")

        # Verify all handlers were initialized with the new MCP instance
        mock_enable.assert_called_once_with(mock_new_mcp)
        mock_disable.assert_called_once_with(mock_new_mcp)
        mock_list.assert_called_once_with(mock_new_mcp)
        mock_facts.assert_called_once_with(mock_new_mcp)

        # Verify that the new MCP instance is returned
        self.assertEqual(result, mock_new_mcp)


if __name__ == '__main__':
    unittest.main()
