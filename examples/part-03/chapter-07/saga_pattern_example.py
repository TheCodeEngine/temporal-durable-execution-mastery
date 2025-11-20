"""
SAGA Pattern Example - Trip Booking

Chapter: 7 - Error Handling und Retry Policies
Demonstrates: SAGA Pattern für Distributed Transactions mit Compensations
"""

import asyncio
import sys
from pathlib import Path
from datetime import timedelta
from dataclasses import dataclass
from typing import Optional, List, Tuple, Callable

# Add project root to path for shared utilities
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError, ActivityError
from shared.temporal_helpers import create_temporal_client
from shared.examples_common import setup_logging
import logging


# ==================== Data Models ====================

@dataclass
class BookingRequest:
    user_id: str
    car_id: str
    hotel_id: str
    flight_id: str

@dataclass
class BookingResult:
    success: bool
    car_booking: Optional[str] = None
    hotel_booking: Optional[str] = None
    flight_booking: Optional[str] = None
    error: Optional[str] = None


# ==================== Forward Activities ====================

@activity.defn
async def book_car(car_id: str) -> str:
    """Book car reservation"""
    activity.logger.info(f"Booking car: {car_id}")
    await asyncio.sleep(0.5)

    if "invalid" in car_id:
        raise ValueError(f"Invalid car ID: {car_id}")

    booking_id = f"car_booking_{car_id}"
    activity.logger.info(f"✓ Car booked: {booking_id}")
    return booking_id

@activity.defn
async def book_hotel(hotel_id: str) -> str:
    """Book hotel reservation"""
    activity.logger.info(f"Booking hotel: {hotel_id}")
    await asyncio.sleep(0.5)

    if "invalid" in hotel_id:
        raise ValueError(f"Invalid hotel ID: {hotel_id}")

    booking_id = f"hotel_booking_{hotel_id}"
    activity.logger.info(f"✓ Hotel booked: {booking_id}")
    return booking_id

@activity.defn
async def book_flight(flight_id: str) -> str:
    """Book flight reservation"""
    activity.logger.info(f"Booking flight: {flight_id}")
    await asyncio.sleep(0.5)

    if "invalid" in flight_id:
        raise ValueError(f"Invalid flight ID: {flight_id}")

    booking_id = f"flight_booking_{flight_id}"
    activity.logger.info(f"✓ Flight booked: {booking_id}")
    return booking_id


# ==================== Compensation Activities ====================

@activity.defn
async def undo_book_car(booking_id: str) -> None:
    """Cancel car reservation"""
    activity.logger.info(f"⚠ Cancelling car booking: {booking_id}")
    await asyncio.sleep(0.3)
    activity.logger.info(f"✓ Car booking cancelled: {booking_id}")

@activity.defn
async def undo_book_hotel(booking_id: str) -> None:
    """Cancel hotel reservation"""
    activity.logger.info(f"⚠ Cancelling hotel booking: {booking_id}")
    await asyncio.sleep(0.3)
    activity.logger.info(f"✓ Hotel booking cancelled: {booking_id}")

@activity.defn
async def undo_book_flight(booking_id: str) -> None:
    """Cancel flight reservation"""
    activity.logger.info(f"⚠ Cancelling flight booking: {booking_id}")
    await asyncio.sleep(0.3)
    activity.logger.info(f"✓ Flight booking cancelled: {booking_id}")


# ==================== SAGA Workflow ====================

@workflow.defn
class TripBookingSaga:
    """SAGA Pattern Implementation für Trip Booking"""

    @workflow.run
    async def run(self, request: BookingRequest) -> BookingResult:
        """Execute SAGA with compensations on failure"""
        # Track completed steps with their compensation functions
        compensations: List[Tuple[Callable, str]] = []
        result = BookingResult(success=False)

        workflow.logger.info(f"Starting trip booking for user {request.user_id}")

        try:
            # ========== Step 1: Book Car ==========
            workflow.logger.info("→ Step 1/3: Booking car...")
            result.car_booking = await workflow.execute_activity(
                book_car,
                args=[request.car_id],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            # Add compensation to stack
            compensations.append((undo_book_car, result.car_booking))
            workflow.logger.info(f"✓ Step 1 complete: {result.car_booking}")

            # ========== Step 2: Book Hotel ==========
            workflow.logger.info("→ Step 2/3: Booking hotel...")
            result.hotel_booking = await workflow.execute_activity(
                book_hotel,
                args=[request.hotel_id],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    non_retryable_error_types=["ValueError"]
                )
            )
            compensations.append((undo_book_hotel, result.hotel_booking))
            workflow.logger.info(f"✓ Step 2 complete: {result.hotel_booking}")

            # ========== Step 3: Book Flight ==========
            workflow.logger.info("→ Step 3/3: Booking flight...")
            result.flight_booking = await workflow.execute_activity(
                book_flight,
                args=[request.flight_id],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            compensations.append((undo_book_flight, result.flight_booking))
            workflow.logger.info(f"✓ Step 3 complete: {result.flight_booking}")

            # All steps successful!
            result.success = True
            workflow.logger.info("🎉 Trip booking completed successfully!")

            workflow.logger.info(f"Summary:")
            workflow.logger.info(f"  - Car: {result.car_booking}")
            workflow.logger.info(f"  - Hotel: {result.hotel_booking}")
            workflow.logger.info(f"  - Flight: {result.flight_booking}")

            return result

        except Exception as e:
            # ========== SAGA Compensation ==========
            workflow.logger.error(f"❌ Booking failed: {e}")
            workflow.logger.error("Executing compensations in REVERSE order...")
            result.error = str(e)

            # Execute compensations in REVERSE order (LIFO)
            for compensation_activity, booking_id in reversed(compensations):
                try:
                    await workflow.execute_activity(
                        compensation_activity,
                        args=[booking_id],
                        start_to_close_timeout=timedelta(seconds=30),
                        retry_policy=RetryPolicy(
                            maximum_attempts=5,  # Compensations more resilient!
                            initial_interval=timedelta(seconds=2)
                        )
                    )
                    workflow.logger.info(
                        f"✓ Compensation successful: {compensation_activity.__name__}"
                    )
                except Exception as comp_error:
                    # Log but continue with other compensations
                    workflow.logger.error(
                        f"⚠ Compensation failed: {compensation_activity.__name__}: {comp_error}"
                    )

            workflow.logger.info("All compensations completed")
            workflow.logger.info(f"Final state: {len(compensations)} steps rolled back")

            return result


# ==================== Client Demo ====================

async def run_saga_example():
    """SAGA Pattern Example"""
    setup_logging()
    logging.info("=== SAGA Pattern Example: Trip Booking ===\n")

    client = await create_temporal_client()

    # Test 1: Successful booking
    logging.info("--- Test 1: Successful Booking ---")
    result1 = await client.execute_workflow(
        TripBookingSaga.run,
        BookingRequest(
            user_id="user-123",
            car_id="car-001",
            hotel_id="hotel-001",
            flight_id="flight-001"
        ),
        id="saga-success",
        task_queue="book-examples"
    )

    print(f"\nTest 1 Result:")
    print(f"  Success: {result1.success}")
    print(f"  Car: {result1.car_booking}")
    print(f"  Hotel: {result1.hotel_booking}")
    print(f"  Flight: {result1.flight_booking}\n")

    # Test 2: Failed booking (invalid flight) - triggers SAGA compensations
    logging.info("\n--- Test 2: Failed Booking (with Compensations) ---")
    result2 = await client.execute_workflow(
        TripBookingSaga.run,
        BookingRequest(
            user_id="user-456",
            car_id="car-002",
            hotel_id="hotel-002",
            flight_id="invalid-flight"  # This will fail!
        ),
        id="saga-failure",
        task_queue="book-examples"
    )

    print(f"\nTest 2 Result:")
    print(f"  Success: {result1.success}")
    print(f"  Car: {result2.car_booking or 'N/A (rolled back)'}")
    print(f"  Hotel: {result2.hotel_booking or 'N/A (rolled back)'}")
    print(f"  Flight: {result2.flight_booking or 'N/A (failed)'}")
    print(f"  Error: {result2.error}\n")

    print("="*60)
    print("SAGA Pattern demonstrated:")
    print("  ✓ Forward transactions with compensations")
    print("  ✓ Automatic rollback on failure")
    print("  ✓ LIFO compensation order")
    print("  ✓ Resilient compensation execution")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(run_saga_example())
