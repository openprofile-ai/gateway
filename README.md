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
   uv pip install -e .
   ```

4. Add new dependency to the project:
   ```bash
   uv add package_name
   ```

## Running the Application

To run the gateway, execute it as a module from the root of the project:

```bash
uv run -m gateway.main
```

## Running Tests

To run the test suite, use the following command:

```bash
pytest tests/
```

For more detailed test output, you can use:

```bash
pytest -v tests/
```
