# Chapter 1 Examples: Einführung in Temporal

## Prerequisites
- Python 3.13
- uv package manager
- Temporal server running locally or Temporal Cloud access

## Setup

```bash
# Install dependencies
uv sync

# Run example
uv run python simple_workflow.py
```

## Examples

- `simple_workflow.py` - Basic Temporal workflow demonstrating core concepts

## Running the Temporal Server

### Option 1: Temporal CLI (Recommended)
```bash
temporal server start-dev
```

### Option 2: Docker
```bash
docker run -p 7233:7233 temporalio/auto-setup:latest
```

## Troubleshooting

If you get connection errors, ensure the Temporal server is running on `localhost:7233`.
