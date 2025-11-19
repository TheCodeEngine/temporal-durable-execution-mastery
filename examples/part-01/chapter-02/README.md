# Chapter 2 Examples: Kernbausteine

## Prerequisites
- Python 3.13
- uv package manager
- Temporal server running

## Setup

```bash
uv sync
```

## Examples

- `workflow.py` - Workflow definition and execution
- `activities.py` - Activity implementations
- `worker.py` - Worker setup and execution

## Running

```bash
# Terminal 1: Start the worker
uv run python worker.py

# Terminal 2: Run the workflow
uv run python workflow.py
```
