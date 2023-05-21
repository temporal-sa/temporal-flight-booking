import stripe
import openai
import json
import asyncio
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from temporalio import activity

stripe.api_key = os.environ.get('STRIPE_API_KEY')
openai.api_key = os.environ.get('CHATGPT_API_KEY')

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
    await asyncio.sleep(1)

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

@activity.defn
async def estimate_flight_cost(input: GetFlightsInput) -> int:
    model_id = 'gpt-3.5-turbo'
    messages = [ {"role": "user", "content": f'provide cost estimate for a flight between {input.origin} and {input.destination}, cost does not need to be real time. Respond JSON using a field called cost. Value should be a single integer, not a range, number only.'} ]

    # Call the API
    completion = openai.ChatCompletion.create(
    model=model_id,
    messages=messages
    )

    # Extract and return the generated answer
    print(f'ChatGPT {completion.choices[0].message.content}')
    cost = json.loads(completion.choices[0].message.content)
    answer = cost["cost"]

    return answer   