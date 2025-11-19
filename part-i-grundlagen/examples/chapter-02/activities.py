"""
Activity Implementations

Chapter: 2 - Kernbausteine
Demonstrates: Activity definition and implementation
"""

from temporalio import activity
import logging


@activity.defn
async def process_data(data: str) -> str:
    """
    Process incoming data.

    This activity demonstrates:
    - Activity definition using @activity.defn
    - Async activity execution
    - Activity logging

    Args:
        data: Input data to process

    Returns:
        Processed data
    """
    activity.logger.info(f"Processing data: {data}")

    # Simulate data processing
    result = data.upper()

    activity.logger.info(f"Data processed successfully: {result}")
    return result


@activity.defn
async def send_notification(message: str) -> None:
    """
    Send a notification.

    This activity demonstrates:
    - Simple notification activity
    - Side effects in activities

    Args:
        message: Notification message
    """
    activity.logger.info(f"Sending notification: {message}")

    # In a real application, this would send an actual notification
    # (email, SMS, webhook, etc.)
    print(f"📧 Notification: {message}")

    activity.logger.info("Notification sent successfully")
