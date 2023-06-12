from flask import Flask, render_template, request, abort
import asyncio
import random
import string
from temporalio.exceptions import FailureError
from temporalio.client import WorkflowFailureError
from flights_activities import GetFlightDetailsInput, GetPaymentInput
from flights_workflow import FlightReservationInfo
import uuid
from typing import List, Dict
from flights_client import get_client
import os

# Import the workflow from the previous code
from flights_workflow import CreatePaymentWorkflow, FlightBookingWorkflow


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
async def index():
    reservation_id = str(uuid.uuid4().int)[:6]    
 
    if request.method == 'POST':
        # Get form data
        flight_details_input = GetFlightDetailsInput(
            origin=request.form.get('origin'),
            destination=request.form.get('destination'),
        )   

        # Start booking workflow
        client = await get_client()

        booking_workflow = await client.start_workflow(
            FlightBookingWorkflow.run,
            flight_details_input,
            id=f'booking-{reservation_id}',
            task_queue=os.getenv("TEMPORAL_TASK_QUEUE"),
        )

        # Get the flights from booking workflow query. Can take a few queries to succeed.
        flights: List[Dict] = []
        while not flights:
            try:
                flights=await booking_workflow.query(FlightBookingWorkflow.flights)
            except:
                pass

        return render_template('flights.html', reservation_id=reservation_id, flights=flights)
    return render_template('index.html', cities=generate_cities())


@app.route('/select/<reservation_id>/<origin>/<destination>/<flight_number>/<flight_model>', methods=['GET', 'POST'])
async def select_seat(reservation_id, origin, destination, flight_number, flight_model):
    # Get booking workflow handle and signal the plane model based on selected flight
    client = await get_client()

    if request.method == 'POST':
        # Get seat selection
        seat = request.form.get('seat')

        # Save reservation info in booking workflow using signal and query cost of flight
        reservation_info=FlightReservationInfo(reservation_id=reservation_id, origin=origin, destination=destination, flight_number=flight_number, flight_model=flight_model, seat=seat)        
        booking_workflow = client.get_workflow_handle(f'booking-{reservation_id}')
        await booking_workflow.signal(FlightBookingWorkflow.update_reservation_info, reservation_info)
        flight_details=await booking_workflow.query(FlightBookingWorkflow.flight_details)
    
        return render_template('payment.html', reservation_id=reservation_id, cost_estimate=flight_details.cost)
    else:
        booking_workflow = client.get_workflow_handle(f'booking-{reservation_id}')
        await booking_workflow.signal(FlightBookingWorkflow.update_plane_model, flight_model)

        # Query booking workflow for the seat configuration
        seat_rows: int = None
        while seat_rows is None:
            await asyncio.sleep(1)
            seat_rows=await booking_workflow.query(FlightBookingWorkflow.seat_rows)

        return render_template('select_seat.html', reservation_id=reservation_id, origin=origin, destination=destination, flight_number=flight_number, flight_model=flight_model, seat_rows=seat_rows)

@app.route('/payment/<reservation_id>', methods=['GET', 'POST'])
async def payment(reservation_id):
    # Get booking workflow handle and query for reservation_info and cost of flight
    client = await get_client()
    booking_workflow = client.get_workflow_handle(f'booking-{reservation_id}')
    reservation_info=await booking_workflow.query(FlightBookingWorkflow.reservation_info)
    flight_details=await booking_workflow.query(FlightBookingWorkflow.flight_details)

    if request.method == 'POST':
        # Get form data, define a working credit card number
        credit_card: string = None
        if request.form.get('credit-card') == '1234123412341234':
            credit_card ='tok_visa'
        else:
            credit_card = request.form.get('credit-card') 

        input = GetPaymentInput(
            amount=str(flight_details.cost * 100),
            token=credit_card,
            currency='usd'
        )   
        
        # Ensure credit card is valid otherwise throw error
        isPayment = False
        while isPayment is not True:
            try:
                receipt_url = await client.execute_workflow(
                    CreatePaymentWorkflow.run,
                    input,
                    id=f'payment-{reservation_info.reservation_id}',
                    task_queue=os.getenv("TEMPORAL_TASK_QUEUE"),
                )

                isPayment = True   
            except WorkflowFailureError:
                return render_template('payment.html',reservation_id=reservation_info.reservation_id, origin=reservation_info.origin, destination=reservation_info.destination, flight_number=reservation_info.flight_number, flight_model=reservation_info.flight_model, seat=reservation_info.seat, cost_estimate=flight_details.cost, error_message="Invalid Credit Card.")
            except FailureError:
                return render_template('payment.html',reservation_id=reservation_info.reservation_id, origin=reservation_info.origin, destination=reservation_info.destination, flight_number=reservation_info.flight_number, flight_model=reservation_info.flight_model, seat=reservation_info.seat, cost_estimate=flight_details.cost, error_message="Payment is already processing")
        # Generate confirmation number: 6 characters, uppercase letters and digits
        confirmation_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        return render_template('confirmation.html', flight_number=reservation_info.flight_number, seat=reservation_info.seat, receipt_url=receipt_url,confirmation_number=confirmation_number)
    return render_template('payment.html',reservation_id=reservation_id, cost_estimate=flight_details.cost)


def generate_cities():
    # List of cities
    cities = [
        'New York',
        'Los Angeles',
        'Frankfurt',
        'Chicago',
        'San Francisco',
        'Seattle',
        'Tokyo',
        'Miami',
        'Atlanta',
        'Boston',
        'Sydney',
        'Dallas',
        'Denver',
        'Dubai'
    ]    
    return cities    

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)    
