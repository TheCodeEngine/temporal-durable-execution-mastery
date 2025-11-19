"""
Common utilities for example scripts.

Provides logging setup, argument parsing, and other
helper functions used across example scripts.
"""

import logging
import argparse
from typing import Any, Dict


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure logging for example scripts.

    Args:
        level: Logging level (default: logging.INFO)

    Example:
        ```python
        from shared.examples_common import setup_logging
        setup_logging()
        logging.info("Example started")
        ```
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def parse_common_args() -> argparse.Namespace:
    """
    Parse common command-line arguments for examples.

    Returns:
        Parsed arguments namespace with:
        - target: Temporal server address
        - namespace: Temporal namespace
        - task_queue: Task queue name

    Example:
        ```python
        from shared.examples_common import parse_common_args
        args = parse_common_args()
        client = await create_temporal_client(args.target, args.namespace)
        ```
    """
    parser = argparse.ArgumentParser(
        description='Temporal Example Script',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '--target',
        type=str,
        default='localhost:7233',
        help='Temporal server address'
    )

    parser.add_argument(
        '--namespace',
        type=str,
        default='default',
        help='Temporal namespace'
    )

    parser.add_argument(
        '--task-queue',
        type=str,
        default='book-examples',
        help='Task queue name'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )

    return parser.parse_args()


def format_workflow_result(result: Any) -> str:
    """
    Format workflow result for display.

    Args:
        result: Workflow execution result

    Returns:
        Formatted string representation of result

    Example:
        ```python
        result = await handle.result()
        print(format_workflow_result(result))
        ```
    """
    if isinstance(result, dict):
        return "\n".join([f"  {k}: {v}" for k, v in result.items()])
    elif isinstance(result, list):
        return "\n".join([f"  - {item}" for item in result])
    else:
        return str(result)
