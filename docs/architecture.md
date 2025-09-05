# Gateway Service Architecture

## Overview

The Gateway Service provides OAuth and OpenID Connect integration for Fact Pods, enabling secure authentication and authorization flows between users and third-party services. The service follows clean architecture principles with clear separation of concerns between handlers, services, repositories, and clients.

## Directory Structure

The project follows a modular structure with clear separation of components:

```
gateway/
├── docs/                  # Documentation
│   └── architecture.md    # This architecture documentation
├── src/
│   └── gateway/
│       ├── clients/          # External service clients
│       │   ├── http_client.py      # Async HTTP client
│       │   └── openid_client.py    # OpenID Connect client
│       ├── db/               # Data persistence layer
│       │   ├── dynamodb_repository.py  # DynamoDB implementation
│       │   └── repository.py           # Repository interface
│       ├── handlers/         # FastMCP tool handlers
│       │   ├── base_handler.py         # Base handler with common functionality
│       │   └── enable_fact_pod_handler.py  # Handler for enabling fact pods
│       ├── models/           # Domain models and DTOs
│       │   ├── auth/              # Authentication-related models
│       │   │   ├── jwk.py         # JSON Web Key models
│       │   │   ├── oauth.py       # OAuth models
│       │   │   └── openid.py      # OpenID Connect models
│       │   └── fact_pod/          # Fact Pod specific models
│       │       ├── config.py      # Fact Pod configuration models
│       │       ├── connection.py  # User-to-FactPod connection models
│       │       └── facts.py       # Fact-related models
│       ├── services/        # Business logic services
│       │   └── fact_pod_service.py    # Fact Pod OAuth service
│       ├── config.py        # Application configuration
│       ├── exceptions.py    # Custom exception hierarchy
│       └── main.py          # Application entry point
├── tests/
│   ├── integration/        # Integration tests
│   │   └── test_handler_registration.py
│   └── unit/               # Unit tests by component
│       └── gateway/
│           ├── db/                # Repository tests
│           ├── handlers/          # Handler tests
│           └── services/          # Service tests
├── .env.sample            # Environment variable template
├── Dockerfile             # Container definition
├── docker-compose.yml     # Local development environment
├── pyproject.toml         # Python project definition and dependencies
└── pytest.ini             # Test configuration
```

## Key Components

### Handlers

FastMCP tool handlers that serve as the entry points to the application:

- **BaseHandler**: Abstract base class providing common functionality for all handlers
- **EnableFactPodHandler**: Handles the OAuth flow for connecting users to fact pods

### Services

Business logic services that implement core application functionality:

- **FactPodOAuthService**: Manages OAuth flows for fact pod connections
  - Fetches OpenID configuration from fact pod providers
  - Registers OAuth clients with providers
  - Stores configuration and state information
  - Generates authorization URLs for users

### Repository Layer

Data persistence abstractions and implementations:

- **Repository**: Abstract base class defining the persistence interface
- **DynamoDBRepository**: AWS DynamoDB implementation of the repository interface
  - Stores OAuth configurations, states, and fact pod configurations
  - Uses composite key patterns for efficient querying

### Clients

External service clients:

- **AsyncHTTPClient**: HTTP client wrapping httpx with async/await support
- **HttpOpenIDClient**: OpenID Connect client for discovery and registration

### Models

Domain models organized by domain context:

- **Auth Models**:
  - OAuth: ClientRegistrationRequest, ClientRegistrationResponse, OAuthConfig
  - OpenID: OpenIDConfiguration, JWK sets
- **Fact Pod Models**:
  - Config: Provider configurations
  - Connection: User-to-fact-pod connections
  - Facts: Fact data structures

### Configuration

The application uses a centralized configuration system:

- **GatewaySettings**: Pydantic-based settings with environment variable support
  - Database settings (table names, region)
  - OAuth settings (redirect templates, state TTL)
  - Service settings (logging, CORS)
  - Server settings (host, port)
  - Optional telemetry settings

### Exception Handling

Structured exception hierarchy for better error handling:

```
GatewayError (Base exception)
├── HTTPError - For client communication issues
├── RepositoryError - For data persistence issues
└── FactPodServiceError - For business logic issues
```

## Architectural Patterns

### Dependency Injection

The application uses constructor-based dependency injection for testability:

```python
class FactPodOAuthService:
    def __init__(self, openid_client: HttpOpenIDClient, repository: Repository):
        self.openid_client = openid_client
        self.repository = repository
```

### Repository Pattern

The Repository interface abstracts data access operations:

```python
class Repository(ABC):
    @abstractmethod
    async def get_fact_pod_config(self, site: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a fact pod site."""
        pass
```

### Async/Await Pattern

All I/O-bound operations use async/await for better performance:

```python
async def enable_fact_pod(self, user_id: str, site: str) -> Dict[str, Any]:
    """Enable fact pod for user."""
    # Async implementation
```

## Data Flow

1. FastMCP tools call handler methods
2. Handlers delegate to services
3. Services use clients to interact with external systems
4. Services use repositories to store and retrieve data
5. Services return structured responses to handlers
6. Handlers format responses for clients

## Security Considerations

- OAuth state parameters for CSRF protection
- Secure storage of client secrets in DynamoDB
- Environment variable configuration for sensitive values
- Input validation through Pydantic models

## Testing Approach

- Unit tests for individual components with mocked dependencies
- Integration tests to verify component interactions
- Test fixtures for DynamoDB using localstack
- Pytest for test running and assertions
