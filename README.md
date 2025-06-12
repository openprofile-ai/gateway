# OpenProfile.AI Gateway

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
   uv pip install -r requirements.txt
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
