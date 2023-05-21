from flask import Flask, render_template, request, abort
import asyncio
import random
import string
from datetime import datetime, timedelta
from temporalio.client import Client, WorkflowFailureError
from flights_activities import GetFlightsInput, GetPaymentInput
import uuid
from typing import List, Dict

# Import the workflow from the previous code
from flights_workflow import GetFlightsWorkflow, GetSeatConfigurationWorkflow, CreatePaymentWorkflow, FlightBookingWorkflow


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
async def index():
    reservation_id = str(uuid.uuid4().int)[:6]    
 
    if request.method == 'POST':
        # Get form data
        input = GetFlightsInput(
            origin=request.form.get('origin'),
            destination=request.form.get('destination'),
        )   

        # Start Temporal workflow
        client = await Client.connect("localhost:7233")

        booking_workflow = await client.start_workflow(
            FlightBookingWorkflow.run,
            input,
            id=f'booking-{input.origin}-{input.destination}-{reservation_id}',
            task_queue="default",
        )

        flights: List[Dict] = []
        while not flights:
            await asyncio.sleep(1)
            flights=await booking_workflow.query(FlightBookingWorkflow.flights)
        
        return render_template('flights.html', reservation_id=reservation_id, flights=flights)
    return render_template('index.html', cities=generate_cities())


@app.route('/select/<reservation_id>/<origin>/<destination>/<flight_number>/<flight_model>', methods=['GET', 'POST'])
async def select_seat(reservation_id, origin, destination, flight_number, flight_model):

    if request.method == 'POST':
        # Get form data
        seat = request.form.get('seat')

        return render_template('payment.html', reservation_id=reservation_id, origin=origin, destination=destination, flight_number=flight_number, flight_model=flight_model, seat=seat)
    else:
        # Start Temporal workflow
        client = await Client.connect("localhost:7233")

        booking_workflow = client.get_workflow_handle(f'booking-{origin}-{destination}-{reservation_id}')
        await booking_workflow.signal(FlightBookingWorkflow.update_plane_model, flight_model)

        seat_rows: int = None
        while seat_rows is None:
            await asyncio.sleep(1)
            seat_rows=await booking_workflow.query(FlightBookingWorkflow.seat_rows)

        return render_template('select_seat.html', reservation_id=reservation_id, origin=origin, destination=destination, flight_number=flight_number, flight_model=flight_model, seat_rows=seat_rows)

@app.route('/payment/<reservation_id>/<origin>/<destination>/<flight_number>/<flight_model>/<seat>', methods=['GET', 'POST'])
async def payment(reservation_id, origin, destination, flight_number, flight_model, seat):
    if request.method == 'POST':
        # Get form data
        input = GetPaymentInput(
            amount='149999',
            token=request.form.get('credit-card'),
            currency='usd'
        )   

        # Start Temporal workflow
        client = await Client.connect("localhost:7233")
        
        isPayment = False
        while isPayment is not True:
            try:
                receipt_url = await client.execute_workflow(
                    CreatePaymentWorkflow.run,
                    input,
                    id=f'payment-{origin}-{destination}-{reservation_id}',
                    task_queue="default",
                )

                isPayment = True
            except WorkflowFailureError:
                return render_template('payment.html',reservation_id=reservation_id, origin=origin, destination=destination, flight_number=flight_number, flight_model=flight_model, seat=seat, error_message="Invalid Credit Card.")

        # Generate confirmation number: 6 characters, uppercase letters and digits
        confirmation_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        return render_template('confirmation.html', flight_number=flight_number, seat=seat, receipt_url=receipt_url,confirmation_number=confirmation_number)
    return render_template('payment.html',reservation_id=reservation_id, origin=origin, destination=destination, flight_number=flight_number, flight_model=flight_model, seat=seat)


def generate_cities():
    # List of cities
    cities = [
        'New York',
        'Los Angeles',
        'Chicago',
        'San Francisco',
        'Seattle',
        'Miami',
        'Atlanta',
        'Boston',
        'Dallas',
        'Denver'
    ]    
    return cities    

if __name__ == '__main__':
    app.run(debug=True)
