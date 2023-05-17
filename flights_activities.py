from dataclasses import dataclass
from datetime import datetime, timedelta
from temporalio import activity


@dataclass
class GetFlightsInput:
    origin: str
    destination: str


@activity.defn
async def get_flights(input: GetFlightsInput) -> list[dict]:
    current_time = datetime.now()

    flights = [{
        'flight_number': f'Flight {i}',
        'origin': input.origin,
        'destination': input.destination,
        'time': (current_time + timedelta(hours=i)).strftime('%H:%M')
    } for i in range(1, 11)]

    print(f"Retrieved flights:\n{flights}")
    return flights
