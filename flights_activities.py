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
        'time': (current_time + timedelta(hours=i)).strftime('%H:%M'),
        'flight_model': 'A330' if i % 2 != 0 else 'B767'
    } for i in range(1, 11)]

    print(f"Retrieved flights:\n{flights}")
    return flights

@activity.defn
async def get_seat_rows(model: str) -> int:
    rows = 10 if model == 'A330' else 20

    print(f"Retrieved seat rows:\n{rows}")
    return rows
