import stripe
import asyncio
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from temporalio import activity

stripe.api_key = os.environ.get('STRIPE_API_KEY')

@dataclass
class GetFlightsInput:
    origin: str
    destination: str

@dataclass
class GetPaymentInput:
    amount: str
    currency: str
    token: str

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

@activity.defn
async def create_payment(input: GetPaymentInput):
    await asyncio.sleep(3)

    try:
        # Create a customer
        customer = stripe.Customer.create(
            source=input.token
        )

        # Charge the customer
        charge = stripe.Charge.create(
            amount=input.amount,
            currency=input.currency,
            customer=customer.id
        )

        # Return the charge object
        return charge

    except stripe.error.StripeError as e:
        # Handle any Stripe errors
        raise Exception(e.user_message)
