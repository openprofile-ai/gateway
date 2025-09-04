"""Tests for the DynamoDBRepository implementation."""

import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from boto3.dynamodb.conditions import Key

from gateway.db.dynamodb_repository import DynamoDBRepository
from gateway.exceptions import RepositoryError


class TestDynamoDBRepository:
    """Test suite for DynamoDBRepository class."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Set up mock objects for all tests."""
        # Mock table resources
        self.mock_dynamodb_table = AsyncMock()
        self.mock_fact_pod_table = AsyncMock()
        
        # Mock DynamoDB resource
        self.mock_dynamodb_resource = AsyncMock()
        
        # Mock aioboto3 session
        self.mock_session = MagicMock()
        
        # Patch the aioboto3.Session
        self.session_patcher = patch("aioboto3.Session", return_value=self.mock_session)
        self.mock_session_class = self.session_patcher.start()
        
        # Setup the repository with test configuration
        self.repository = DynamoDBRepository(
            table_name="test-table", 
            region_name="us-test-1",
            fact_pod_config_table_name="test-fact-pod-table"
        )
        
        # Setup the mock chain for DynamoDB resources
        self.mock_session.resource.return_value.__aenter__.return_value = self.mock_dynamodb_resource
        
        # Configure the resource to return different tables based on name
        async def mock_get_table(table_name):
            if table_name == "test-fact-pod-table":
                return self.mock_fact_pod_table
            return self.mock_dynamodb_table
            
        self.mock_dynamodb_resource.Table = mock_get_table
        
        # Initialize the tables
        self.repository._tables = {
            "test-table": self.mock_dynamodb_table,
            "test-fact-pod-table": self.mock_fact_pod_table
        }
        
        yield
        
        # Stop patches after test
        self.session_patcher.stop()

    @pytest.mark.asyncio
    async def test_get_table_success(self):
        """Test successful table connection."""
        table = await self.repository._get_table()
        assert table == self.mock_dynamodb_table

    @pytest.mark.asyncio
    async def test_get_table_with_name(self):
        """Test successful connection to named table."""
        table = await self.repository._get_table(self.repository.fact_pod_config_table_name)
        assert table == self.mock_fact_pod_table

    @pytest.mark.asyncio
    async def test_get_table_error(self):
        """Test error handling when connecting to table."""
        # Clear cached tables
        self.repository._tables = {}
        
        # Force an error when creating a new resource
        self.mock_session.resource.side_effect = Exception("Connection error")
        
        # Verify exception handling
        with pytest.raises(RepositoryError) as excinfo:
            await self.repository._get_table()
        
        assert "Failed to connect to DynamoDB" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the DynamoDB connection."""
        # Set up the resource
        self.repository._resource = self.mock_dynamodb_resource
        
        await self.repository.close()
        self.mock_dynamodb_resource.__aexit__.assert_called_once()
        assert self.repository._resource is None
        assert self.repository._tables == {}

    @pytest.mark.asyncio
    async def test_get_categories_success(self):
        """Test successful retrieval of categories."""
        # Setup mock response
        self.mock_dynamodb_table.scan.return_value = {
            'Items': [
                {'name': 'Category1', 'item_type': 'category'},
                {'name': 'Category2', 'item_type': 'category'},
                {'name': 'Category3', 'item_type': 'category'},
            ]
        }
        
        # Call the method
        result = await self.repository.get_categories()
        
        # Verify results
        assert len(result) == 3
        assert 'Category1' in result
        assert 'Category2' in result
        assert 'Category3' in result
        
        # Verify the scan was called with the correct parameters
        self.mock_dynamodb_table.scan.assert_called_once()
        call_args = self.mock_dynamodb_table.scan.call_args[1]
        assert 'FilterExpression' in call_args
        # Instead of comparing object identity, verify the expression works with 'category'
        filter_expr = call_args['FilterExpression']
        # Just check that it's a Key expression
        assert isinstance(filter_expr, Key('item_type').eq('category').__class__)

    @pytest.mark.asyncio
    async def test_get_categories_pagination(self):
        """Test pagination for category retrieval."""
        # Setup mock responses with pagination
        self.mock_dynamodb_table.scan.side_effect = [
            {
                'Items': [
                    {'name': 'Category1', 'item_type': 'category'},
                    {'name': 'Category2', 'item_type': 'category'},
                ],
                'LastEvaluatedKey': {'id': '2'}
            },
            {
                'Items': [
                    {'name': 'Category3', 'item_type': 'category'},
                ]
            }
        ]
        
        # Call the method
        result = await self.repository.get_categories()
        
        # Verify results
        assert len(result) == 3
        assert result == ['Category1', 'Category2', 'Category3']
        
        # Verify the scan was called twice with correct parameters
        assert self.mock_dynamodb_table.scan.call_count == 2
        # Second call should include the ExclusiveStartKey
        second_call_args = self.mock_dynamodb_table.scan.call_args_list[1][1]
        assert second_call_args['ExclusiveStartKey'] == {'id': '2'}

    @pytest.mark.asyncio
    async def test_get_categories_error(self):
        """Test error handling for category retrieval."""
        # Setup mock to raise an exception
        self.mock_dynamodb_table.scan.side_effect = Exception("DynamoDB error")
        
        # Verify the exception is properly handled
        with pytest.raises(RepositoryError) as excinfo:
            await self.repository.get_categories()
        
        assert "Failed to fetch categories" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_get_fact_pod_config_found(self):
        """Test successful retrieval of fact pod configuration."""
        # Setup mock response for the fact pod config table
        mock_item = {
            'site': 'example.com',
            'enabled': True,
            'created_at': '2025-06-25T12:00:00Z',
        }
        self.mock_fact_pod_table.get_item.return_value = {'Item': mock_item}
        
        # Call the method
        result = await self.repository.get_fact_pod_config('example.com')
        
        # Verify results
        assert result == mock_item
        
        # Verify the get_item was called with the correct parameters
        self.mock_fact_pod_table.get_item.assert_called_once_with(
            Key={'site': 'example.com'}
        )

    @pytest.mark.asyncio
    async def test_get_fact_pod_config_not_found(self):
        """Test retrieval of non-existent fact pod configuration."""
        # Setup mock response for item not found
        self.mock_fact_pod_table.get_item.return_value = {}
        
        # Call the method
        result = await self.repository.get_fact_pod_config('unknown.com')
        
        # Verify results
        assert result is None
        
        # Verify the get_item was called with the correct parameters
        self.mock_fact_pod_table.get_item.assert_called_once_with(
            Key={'site': 'unknown.com'}
        )

    @pytest.mark.asyncio
    async def test_get_fact_pod_config_error(self):
        """Test error handling for fact pod configuration retrieval."""
        # Setup mock to raise an exception
        self.mock_fact_pod_table.get_item.side_effect = Exception("DynamoDB error")
        
        # Verify the exception is properly handled
        with pytest.raises(RepositoryError) as excinfo:
            await self.repository.get_fact_pod_config('example.com')
        
        assert "Failed to get fact pod configuration" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_store_fact_pod_config_success(self):
        """Test successful storage of fact pod configuration."""
        # Create a sample config
        config = {
            'site': 'example.com',
            'enabled': True,
            'description': 'Example site configuration'
        }
        
        # Call the method
        await self.repository.store_fact_pod_config(config)
        
        # Verify put_item was called with the correct parameters
        self.mock_fact_pod_table.put_item.assert_called_once()
        call_args = self.mock_fact_pod_table.put_item.call_args[1]
        
        # Check that the item contains all required fields and timestamps were added
        item = call_args['Item']
        assert item['site'] == 'example.com'
        assert item['enabled'] is True
        assert item['description'] == 'Example site configuration'
        assert 'created_at' in item
        assert 'updated_at' in item

    @pytest.mark.asyncio
    async def test_store_fact_pod_config_missing_site(self):
        """Test error handling when site is missing from config."""
        # Create an invalid config without site
        invalid_config = {
            'enabled': True,
            'description': 'Invalid config'
        }
        
        # Verify the exception is properly handled
        with pytest.raises(RepositoryError) as excinfo:
            await self.repository.store_fact_pod_config(invalid_config)
        
        assert "Fact pod config must contain 'site' key" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_store_fact_pod_config_error(self):
        """Test error handling for fact pod configuration storage."""
        # Setup mock to raise an exception
        self.mock_fact_pod_table.put_item.side_effect = Exception("DynamoDB error")
        
        # Verify the exception is properly handled
        with pytest.raises(RepositoryError) as excinfo:
            await self.repository.store_fact_pod_config({
                'site': 'example.com',
                'enabled': True
            })
        
        assert "Failed to store fact pod configuration" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_get_user_site_connection_found(self):
        """Test successful retrieval of user-site connection."""
        # Setup mock response
        mock_item = {
            'pk': 'USER#user123',
            'sk': 'SITE#example.com',
            'user_id': 'user123',
            'site': 'example.com',
            'client_id': 'client123',
            'client_secret': 'secret123',
            'redirect_url': 'https://example.com/callback',
            'created_at': 1625097600,
        }
        self.mock_dynamodb_table.get_item.return_value = {'Item': mock_item}
        
        # Call the method
        result = await self.repository.get_user_site_connection('user123', 'example.com')
        
        # Verify results
        assert result == mock_item
        
        # Verify the get_item was called with the correct parameters
        self.mock_dynamodb_table.get_item.assert_called_once_with(
            Key={'pk': 'USER#user123', 'sk': 'SITE#example.com'}
        )

    @pytest.mark.asyncio
    async def test_get_user_site_connection_not_found(self):
        """Test retrieval of non-existent user-site connection."""
        # Setup mock response for item not found
        self.mock_dynamodb_table.get_item.return_value = {}
        
        # Call the method
        result = await self.repository.get_user_site_connection('user123', 'unknown.com')
        
        # Verify results
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_site_connection_error(self):
        """Test error handling for user-site connection retrieval."""
        # Setup mock to raise an exception
        self.mock_dynamodb_table.get_item.side_effect = Exception("DynamoDB error")
        
        # Verify the exception is properly handled
        with pytest.raises(RepositoryError) as excinfo:
            await self.repository.get_user_site_connection('user123', 'example.com')
        
        assert "Failed to get user-site connection" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_store_oauth_config_success(self):
        """Test successful storage of OAuth configuration."""
        # Call the method
        await self.repository.store_oauth_config(
            'user123',
            'example.com',
            'client123',
            'secret123',
            'https://example.com/callback'
        )
        
        # Verify put_item was called with the correct parameters
        self.mock_dynamodb_table.put_item.assert_called_once()
        call_args = self.mock_dynamodb_table.put_item.call_args[1]
        
        # Check that the item contains all required fields
        item = call_args['Item']
        assert item['pk'] == 'USER#user123'
        assert item['sk'] == 'SITE#example.com'
        assert item['user_id'] == 'user123'
        assert item['site'] == 'example.com'
        assert item['client_id'] == 'client123'
        assert item['client_secret'] == 'secret123'
        assert item['redirect_url'] == 'https://example.com/callback'
        assert 'created_at' in item
        assert 'updated_at' in item
        assert item['item_type'] == 'oauth_config'

    @pytest.mark.asyncio
    async def test_store_oauth_config_error(self):
        """Test error handling for OAuth configuration storage."""
        # Setup mock to raise an exception
        self.mock_dynamodb_table.put_item.side_effect = Exception("DynamoDB error")
        
        # Verify the exception is properly handled
        with pytest.raises(RepositoryError) as excinfo:
            await self.repository.store_oauth_config(
                'user123',
                'example.com',
                'client123',
                'secret123',
                'https://example.com/callback'
            )
        
        assert "Failed to store OAuth configuration" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_store_oauth_state_success(self):
        """Test successful storage of OAuth state."""
        # Mock time.time() to return a fixed value
        with patch('time.time', return_value=1625097600):
            # Call the method
            await self.repository.store_oauth_state('state123', 'user123', 'example.com')
            
            # Verify put_item was called with the correct parameters
            self.mock_dynamodb_table.put_item.assert_called_once()
            call_args = self.mock_dynamodb_table.put_item.call_args[1]
            
            # Check that the item contains all required fields
            item = call_args['Item']
            assert item['pk'] == 'STATE#state123'
            assert item['sk'] == 'STATE'
            assert item['state'] == 'state123'
            assert item['user_id'] == 'user123'
            assert item['site'] == 'example.com'
            assert item['created_at'] == 1625097600
            assert item['item_type'] == 'oauth_state'
            
            # Check TTL is set correctly based on settings
            from gateway.config import settings
            assert item['expires_at'] == 1625097600 + settings.oauth_state_ttl_seconds
            assert item['ttl'] == 1625097600 + settings.oauth_state_ttl_seconds

    @pytest.mark.asyncio
    async def test_store_oauth_state_error(self):
        """Test error handling for OAuth state storage."""
        # Setup mock to raise an exception
        self.mock_dynamodb_table.put_item.side_effect = Exception("DynamoDB error")
        
        # Verify the exception is properly handled
        with pytest.raises(RepositoryError) as excinfo:
            await self.repository.store_oauth_state('state123', 'user123', 'example.com')
        
        assert "Failed to store OAuth state" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_verify_oauth_state_valid(self):
        """Test verification of valid OAuth state."""
        # Current time is 1625097600
        current_time = 1625097600
        # State expires 10 minutes (600 seconds) later
        expires_at = current_time + 600
        
        # Setup mock response
        mock_item = {
            'pk': 'STATE#state123',
            'sk': 'STATE',
            'state': 'state123',
            'user_id': 'user123',
            'site': 'example.com',
            'created_at': current_time,
            'expires_at': expires_at,
        }
        self.mock_dynamodb_table.get_item.return_value = {'Item': mock_item}
        
        # Mock time.time() to return a fixed value
        with patch('time.time', return_value=current_time):
            # Call the method
            result = await self.repository.verify_oauth_state('state123')
            
            # Verify results
            assert result is not None
            assert result['user_id'] == 'user123'
            assert result['site'] == 'example.com'
            
            # Verify the get_item was called with the correct parameters
            self.mock_dynamodb_table.get_item.assert_called_once_with(
                Key={'pk': 'STATE#state123', 'sk': 'STATE'}
            )
            
            # Delete should not be called for valid state
            assert not self.mock_dynamodb_table.delete_item.called

    @pytest.mark.asyncio
    async def test_verify_oauth_state_expired(self):
        """Test verification of expired OAuth state."""
        # Current time is 1625097600
        current_time = 1625097600
        # State expired 60 seconds ago
        expires_at = current_time - 60
        
        # Setup mock response
        mock_item = {
            'pk': 'STATE#state123',
            'sk': 'STATE',
            'state': 'state123',
            'user_id': 'user123',
            'site': 'example.com',
            'created_at': current_time - 660,  # Created 11 minutes ago
            'expires_at': expires_at,
        }
        self.mock_dynamodb_table.get_item.return_value = {'Item': mock_item}
        
        # Mock time.time() to return a fixed value
        with patch('time.time', return_value=current_time):
            # Call the method
            result = await self.repository.verify_oauth_state('state123')
            
            # Verify results
            assert result is None
            
            # Verify the get_item was called with the correct parameters
            self.mock_dynamodb_table.get_item.assert_called_once_with(
                Key={'pk': 'STATE#state123', 'sk': 'STATE'}
            )
            
            # Verify expired state was deleted
            self.mock_dynamodb_table.delete_item.assert_called_once_with(
                Key={'pk': 'STATE#state123', 'sk': 'STATE'}
            )

    @pytest.mark.asyncio
    async def test_verify_oauth_state_not_found(self):
        """Test verification of non-existent OAuth state."""
        # Setup mock response for item not found
        self.mock_dynamodb_table.get_item.return_value = {}
        
        # Call the method
        result = await self.repository.verify_oauth_state('unknown_state')
        
        # Verify results
        assert result is None
        
        # Verify the get_item was called with the correct parameters
        self.mock_dynamodb_table.get_item.assert_called_once_with(
            Key={'pk': 'STATE#unknown_state', 'sk': 'STATE'}
        )
        
        # Delete should not be called for non-existent state
        assert not self.mock_dynamodb_table.delete_item.called

    @pytest.mark.asyncio
    async def test_verify_oauth_state_error(self):
        """Test error handling for OAuth state verification."""
        # Setup mock to raise an exception
        self.mock_dynamodb_table.get_item.side_effect = Exception("DynamoDB error")
        
        # Verify the exception is properly handled
        with pytest.raises(RepositoryError) as excinfo:
            await self.repository.verify_oauth_state('state123')
        
        assert "Failed to verify OAuth state" in str(excinfo.value)
