from datetime import timedelta

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
