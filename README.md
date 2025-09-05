# OpenProfile.AI Gateway

The OpenProfile.AI Gateway is a gateway for the user (local on user machine initially) that will be controlling user's personal information and preferences from many other 3rd party services and allow user to granually control what they want to share with AI Assistant (for context enrichment) or with other 3rd party services.

## Architecture

The gateway acts as a central hub for managing personal data. It exposes an MCP (Multi-Context Protocol) server interface for AI assistants to connect to. It also connects to other 3rd party MCP servers as an MCP client to retrieve and manage user data from various services. A local database is used to store authentication tokens and other metadata for the user.


## Installation

1. Install [uv](https://github.com/astral-sh/uv) if you haven't already:
   ```bash
   curl -sSf https://astral.sh/uv/install.sh | sh
   ```

2. Create and activate a virtual environment:
   ```bash
   # Create a new virtual environment in the .venv directory
   uv venv
   
   # Activate the virtual environment
   # On macOS/Linux:
   source .venv/bin/activate
   # On Windows:
   # .venv\Scripts\activate
   ```

3. Install the project dependencies:
   ```bash
   uv pip install -e '.[dev]'
   ```

4. To add new dependency to the project:
   ```bash
   uv add package_name
   ```

## Configuration

The gateway uses a centralized configuration system based on Pydantic Settings. This allows for flexible configuration through environment variables or a `.env` file.

### How Configuration Loading Works

The configuration system loads settings in the following priority order:
1. Environment variables (highest priority)
2. Values from the `.env` file (if present)
3. Default values defined in the `GatewaySettings` class (lowest priority)

All environment variables for this project use the `GATEWAY_` prefix. For example, to set the database table name, use `GATEWAY_DB_TABLE_NAME`.

### Configuration Options

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| Primary Database Table | `GATEWAY_DB_TABLE_NAME` | gateway-table | Primary DynamoDB table name |
| Fact Pod Config Table | `GATEWAY_FACT_POD_CONFIG_TABLE_NAME` | fact-pod-config-table | Fact Pod configuration DynamoDB table name |
| Database Region | `GATEWAY_DB_REGION_NAME` | us-east-1 | AWS region for DynamoDB |
| OAuth Redirect | `GATEWAY_OAUTH_REDIRECT_TEMPLATE` | https://{site}/oauth/callback | Template for OAuth redirect URLs |
| OAuth State TTL | `GATEWAY_OAUTH_STATE_TTL_SECONDS` | 600 | Time-to-live for OAuth state tokens (seconds) |
| Log Level | `GATEWAY_LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| CORS Origins | `GATEWAY_CORS_ORIGINS_STR` | * | Comma-separated list of allowed CORS origins |
| Server Host | `GATEWAY_SERVER_HOST` | 0.0.0.0 | Host address to bind the server |
| Server Port | `GATEWAY_SERVER_PORT` | 8080 | Port to run the server on |

### Using Environment Variables

You can configure the application by setting environment variables:

```bash
# Example
export GATEWAY_DB_TABLE_NAME=my_table
export GATEWAY_FACT_POD_CONFIG_TABLE_NAME=my_fact_pod_table
export GATEWAY_LOG_LEVEL=DEBUG
uv run -m gateway.main
```

### Using .env File

Alternatively, create a `.env` file in the project root with your configuration:

```
# Database settings
GATEWAY_DB_TABLE_NAME=my_table
GATEWAY_FACT_POD_CONFIG_TABLE_NAME=my_fact_pod_table
GATEWAY_DB_REGION_NAME=us-east-1

# Service settings
GATEWAY_LOG_LEVEL=DEBUG
```

A sample configuration file is provided at `.env.sample`. Copy it to create your own:

```bash
cp .env.sample .env
```

Then edit the `.env` file to set your custom configuration values.

## Running the Application

To run the gateway, execute it as a module from the root of the project:

```bash
uv run -m gateway.main
```

## Running Tests

To run the test suite, use the following command:

```bash
uv run pytest tests/
```

For more detailed test output, you can use:

```bash
uv run pytest -v tests/
```

## Database Model

The Gateway service uses AWS DynamoDB for data storage with two separate tables:

### Tables

1. **Primary Table** - Stores most Gateway data including categories, user-site connections, OAuth configurations, and OAuth states.
   - Environment variable: `GATEWAY_DB_TABLE_NAME`
   - Default name: `gateway-table`

2. **Fact Pod Configuration Table** - Dedicated table for storing fact pod configurations.
   - Environment variable: `GATEWAY_FACT_POD_CONFIG_TABLE_NAME`
   - Default name: `fact-pod-config-table`
   - This separation allows for independent scaling and management of fact pod configurations.

### Data Models

#### Categories
Stored in the primary table with the following attributes:
- `name`: String - Name of the category
- `item_type`: String - Always set to `"category"` (used for filtering)

#### Fact Pod Configurations
Stored in the dedicated fact pod configuration table with the following attributes:
- `site`: String - Domain name of the site (Primary Key)
- `enabled`: Boolean - Whether the fact pod is enabled
- `created_at`: Number/String - Timestamp when the configuration was first created
- `updated_at`: Number/String - Timestamp when the configuration was last updated
- Additional configuration fields may be included based on specific site requirements

#### User-Site Connections
Stored in the primary table with the following attributes:
- `pk`: String - Partition key in format `"USER#{user_id}"`
- `sk`: String - Sort key in format `"SITE#{site}"`
- `user_id`: String - ID of the user
- `site`: String - Domain name of the connected site
- `client_id`: String - OAuth client ID
- `client_secret`: String - OAuth client secret
- `redirect_url`: String - OAuth redirect URL
- `created_at`: Number - Unix timestamp of creation
- `updated_at`: Number - Unix timestamp of last update
- `item_type`: String - Always set to `"oauth_config"`

#### OAuth States
Stored in the primary table with the following attributes:
- `pk`: String - Partition key in format `"STATE#{state}"`
- `sk`: String - Sort key, always `"STATE"`
- `state`: String - Random state string used for CSRF protection
- `user_id`: String - ID of the user
- `site`: String - Domain name of the site
- `created_at`: Number - Unix timestamp of creation
- `expires_at`: Number - Unix timestamp when the state expires
- `ttl`: Number - DynamoDB TTL attribute (same as expires_at)
- `item_type`: String - Always set to `"oauth_state"`

### Access Patterns

The repository supports the following access patterns:

1. **Get Categories** - Scan the primary table for items with `item_type = "category"` with pagination support.
2. **Get Fact Pod Configuration** - Direct lookup by `site` in the fact pod configuration table.
3. **Store Fact Pod Configuration** - Insert or update configuration in the fact pod configuration table.
4. **Get User-Site Connection** - Direct lookup by composite key `(USER#{user_id}, SITE#{site})` in the primary table.
5. **Store OAuth Configuration** - Insert or update OAuth configuration in the primary table.
6. **Store OAuth State** - Insert OAuth state with TTL in the primary table.
7. **Verify OAuth State** - Verify state exists and hasn't expired, automatically deleting expired states.

### DynamoDB Features Used

- **Composite Keys** - Using partition key (`pk`) and sort key (`sk`) for efficient lookups
- **TTL (Time to Live)** - Automatic expiration of OAuth states
- **Pagination** - Support for handling large result sets (e.g., categories)
- **Scan with Filters** - Used for category retrieval
- **Error Handling** - Comprehensive error handling with custom `RepositoryError` exceptions

### Best Practices

- Tables are initialized lazily to improve performance
- Connections are reused and properly closed
- Error handling includes detailed logging
- Timestamps are used for auditing and TTL
- Consistent naming conventions for composite keys
