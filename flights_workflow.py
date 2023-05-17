from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from flights_activities import GetFlightsInput, get_flights


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

