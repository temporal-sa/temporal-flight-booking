import asyncio
from typing import Optional
import os

from temporalio.client import Client, TLSConfig
from temporalio.worker import Worker

from flights_activities import (
    get_flights,
    get_seat_rows,
    create_payment,
    get_flight_details,
)

from flights_client import get_client
from flights_workflow import CreatePaymentWorkflow, FlightBookingWorkflow


async def main():
    client = await get_client()

    worker = Worker(
        client,
        task_queue="default",
        workflows=[CreatePaymentWorkflow, FlightBookingWorkflow],
        activities=[
            get_flights,
            get_seat_rows,
            create_payment,
            get_flight_details,
        ],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())