# Gateway Service Architecture

## Overview

The Gateway Service provides OAuth and OpenID client operations for interacting with Fact Pods. The codebase follows GRASP, SOLID, and KISS principles to ensure clean separation of concerns, maintainability, and testability.

## Directory Structure

```
gateway/
├── src/
│   └── gateway/
│       ├── clients/             # Client implementations
│       │   ├── __init__.py     
│       │   ├── http_client.py   # HTTP client implementation
│       │   └── openid_client.py # OpenID client implementation
│       ├── db/                  # Database access implementations
│       │   ├── __init__.py     
│       │   ├── dynamodb_repository.py  # DynamoDB implementation
│       │   └── repository.py    # Repository interface definition
│       ├── handlers/            # FastMCP handlers
│       │   ├── __init__.py
│       │   ├── base_handler.py
│       │   ├── enable_fact_pod_handler.py
│       │   └── disable_fact_pod_handler.py
│       ├── models/              # Data models
│       │   ├── __init__.py     
│       │   ├── fact_pod.py      # Fact Pod specific models
│       │   └── oauth.py         # OAuth and OpenID related models
│       └── services/            # Business logic services
│           ├── __init__.py     
│           └── fact_pod_service.py  # Fact Pod OAuth service
└── tests/
    └── unit/
        └── gateway/
            └── handlers/        # Handler tests
                └── test_enable_fact_pod_handler.py
                └── test_disable_fact_pod_handler.py
```

## Import and Module Organization

For improved code organization and maintainability, imports should always reference the specific module where a class or function is defined rather than using intermediate re-exports.

### Direct Imports Policy

The codebase follows a strict "no re-export" policy in `__init__.py` files. This means:

1. **Never** use `__init__.py` files to re-export symbols from other modules
2. **Always** import directly from the module where the class or function is defined
3. This applies to all modules, including client implementations, handlers, and services

For example:
```python
# Correct approach - direct imports
from gateway.clients.http_client import AsyncHTTPClient
from gateway.clients.openid_client import HttpOpenIDClient
from gateway.services.fact_pod_service import FactPodOAuthService

# INCORRECT approach - using re-exports
from gateway.clients import AsyncHTTPClient, HttpOpenIDClient
from gateway.services import FactPodOAuthService
```

### Client Organization

All client implementations are organized in the `clients` directory:

- `clients/http_client.py`: Implementation of the HTTP client using httpx
- `clients/openid_client.py`: Implementation of the OpenID client

The clients are implemented as concrete classes without interface abstractions, focusing on simplicity and clarity. This approach:

1. Makes dependencies explicit and clear
2. Avoids circular import problems
3. Improves IDE navigation and refactoring support
4. Makes code easier to understand and maintain
5. Reduces unnecessary abstraction layers

## Domain-Specific Exception Handling

The codebase implements a structured exception hierarchy for better error handling, improved debugging, and cleaner code.

### Exception Hierarchy

```
GatewayError (Base exception)
├── HTTPError
├── RepositoryError
└── FactPodServiceError
```

### Exception Handling Principles

1. **Layer-Specific Exceptions**: Each architectural layer has its own exception types
   - Repository layer throws `RepositoryError`
   - HTTP client layer throws `HTTPError`
   - Service layer throws `FactPodServiceError` and its subtypes

2. **Exception Chaining**: Lower-level exceptions are caught and wrapped in layer-appropriate exceptions
   - Preserves original exception context
   - Adds semantic meaning specific to the layer

3. **Descriptive Error Messages**: All exceptions include detailed error messages
   - What operation was being performed
   - What entity was affected
   - Why the operation failed

4. **Handler Error Responses**: Handlers translate exceptions to user-friendly responses
   - Catches specific exception types and returns appropriate error responses
   - Preserves security by not exposing sensitive details

### Benefits

- **Improved Debugging**: Exception hierarchy makes it easier to identify where and why errors occur
- **Consistent Error Handling**: Standardized approach across the codebase
- **Better User Experience**: More specific and helpful error messages
- **Maintainability**: Clear separation between technical errors and domain errors

## Key Components

### Models

- **OAuthConfig**: Configuration for OAuth client registration
- **OAuthState**: OAuth state information for user authorization
- **OpenIDConfiguration**: Discovery information from OpenID providers
- **ClientRegistrationResponse**: Response from registering with an OpenID provider

### Services

- **FactPodOAuthService**: Manages the OAuth flow for Fact Pods
- **HttpOpenIDClient**: Implements OpenID discovery and registration using HTTP

### Handlers

- **EnableFactPodHandler**: Handles user requests to enable Fact Pods
- **DisableFactPodHandler**: Handles user requests to disable Fact Pods

## Testing

The architecture supports comprehensive testing through:
- Clear separation of concerns
- Dependency injection for easier unit testing
