import asyncio
from typing import Optional
import os

from temporalio.client import Client, TLSConfig
from temporalio.worker import Worker

from flights_activities import (
    get_flights,
    get_seat_rows,
    create_payment,
)
from flights_workflow import GetFlightsWorkflow, GetSeatConfigurationWorkflow, CreatePaymentWorkflow, FlightBookingWorkflow


async def main():
    if (
        os.getenv("TEMPORAL_MTLS_TLS_CERT")
        and os.getenv("TEMPORAL_MTLS_TLS_KEY") is not None
    ):
        server_root_ca_cert: Optional[bytes] = None
        with open(os.getenv("TEMPORAL_MTLS_TLS_CERT"), "rb") as f:
            client_cert = f.read()

        with open(os.getenv("TEMPORAL_MTLS_TLS_KEY"), "rb") as f:
            client_key = f.read()

        # Start client
        client = await Client.connect(
            os.getenv("TEMPORAL_HOST_URL"),
            namespace=os.getenv("TEMPORAL_NAMESPACE"),
            tls=TLSConfig(
                server_root_ca_cert=server_root_ca_cert,
                client_cert=client_cert,
                client_private_key=client_key,
            ),
        )
    else:
        client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="default",
        workflows=[GetFlightsWorkflow, GetSeatConfigurationWorkflow, CreatePaymentWorkflow, FlightBookingWorkflow],
        activities=[
            get_flights,
            get_seat_rows,
            create_payment,
        ],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())