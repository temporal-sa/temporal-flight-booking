from datetime import timedelta
import asyncio
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from flights_activities import GetFlightsInput, GetPaymentInput, get_flights, get_seat_rows, create_payment


@workflow.defn
class GetFlightsWorkflow:
    @workflow.run
    async def run(self, input: GetFlightsInput):

        output = await workflow.execute_activity(
            get_flights,
            input,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(
                non_retryable_error_types=["Exception"],
            ),                  
        )

        return output

@workflow.defn
class GetSeatConfigurationWorkflow:
    @workflow.run
    async def run(self, model: str):

        output = await workflow.execute_activity(
            get_seat_rows,
            model,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(
                non_retryable_error_types=["Exception"],
            ),                  
        )

        return output
    
@workflow.defn
class CreatePaymentWorkflow:
    @workflow.run
    async def run(self, input: GetPaymentInput):

        output = await workflow.execute_activity(
            create_payment,
            input,
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
            ),                  
        )

        if not output is None:  
            print(output['receipt_url'])
        return output['receipt_url']

@workflow.defn
class FlightBookingWorkflow:
    def __init__(self) -> None:
        self._flights = None
        self._seat_rows = None    
        self._pending_update_plane_model: asyncio.Queue[str] = asyncio.Queue()
        self._exit = False


    @workflow.run
    async def run(self, input: GetFlightsInput):
        self._flights = GetFlightsInput
        self._seat_rows = int

        flights = await workflow.execute_activity(
            get_flights,
            input,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(
            non_retryable_error_types=["Exception"],
            ),                  
        )
        self._flights = flights

        # Wait for queue item or exit
        await workflow.wait_condition(
            lambda: not self._pending_update_plane_model.empty() or self._exit
        )

        # Drain and process queue
        while not self._pending_update_plane_model.empty():
            seat_rows = await workflow.execute_activity(
                get_seat_rows,
                self._pending_update_plane_model.get_nowait(),
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(
                non_retryable_error_types=["Exception"],
                ),                  
            )
            self._seat_rows = seat_rows                        
            
    @workflow.query
    def flights(self) -> list[dict]:
        return self._flights
    
    @workflow.query
    def seat_rows(self) -> int:
        return self._seat_rows
                    
    @workflow.signal
    async def update_plane_model(self, plane_model: str) -> None:
        await self._pending_update_plane_model.put(plane_model)

    @workflow.signal
    def exit(self) -> None:
        self._exit = True