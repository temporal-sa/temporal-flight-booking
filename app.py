from flask import Flask, render_template, request, abort
import asyncio
import random
import string
from temporalio.client import Client, WorkflowFailureError
from flights_activities import GetFlightsInput, GetPaymentInput
from flights_workflow import FlightReservationInfo
import uuid
from typing import List, Dict

# Import the workflow from the previous code
from flights_workflow import CreatePaymentWorkflow, FlightBookingWorkflow


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

        # Start booking workflow
        client = await Client.connect("localhost:7233")

        booking_workflow = await client.start_workflow(
            FlightBookingWorkflow.run,
            input,
            id=f'booking-{input.origin}-{input.destination}-{reservation_id}',
            task_queue="default",
        )

        # Get the flights from booking workflow query
        flights: List[Dict] = []
        while not flights:
            await asyncio.sleep(1)
            flights=await booking_workflow.query(FlightBookingWorkflow.flights)
        
        return render_template('flights.html', reservation_id=reservation_id, flights=flights)
    return render_template('index.html', cities=generate_cities())


@app.route('/select/<reservation_id>/<origin>/<destination>/<flight_number>/<flight_model>', methods=['GET', 'POST'])
async def select_seat(reservation_id, origin, destination, flight_number, flight_model):
    # Get booking workflow handle and signal the plane model based on selected flight
    client = await Client.connect("localhost:7233")

    if request.method == 'POST':
        # Get seat selection
        seat = request.form.get('seat')

        # Save reservation info in booking workflow using signal
        reservation_info=FlightReservationInfo(reservation_id=reservation_id, origin=origin, destination=destination, flight_number=flight_number, flight_model=flight_model, seat=seat)
        
        booking_workflow = client.get_workflow_handle(f'booking-{origin}-{destination}-{reservation_id}')
        await booking_workflow.signal(FlightBookingWorkflow.update_reservation_info, reservation_info)        

        return render_template('payment.html', reservation_id=reservation_id, origin=origin, destination=destination)
    else:
        booking_workflow = client.get_workflow_handle(f'booking-{origin}-{destination}-{reservation_id}')
        await booking_workflow.signal(FlightBookingWorkflow.update_plane_model, flight_model)

        # Query booking workflow for the seat configuration
        seat_rows: int = None
        while seat_rows is None:
            await asyncio.sleep(1)
            seat_rows=await booking_workflow.query(FlightBookingWorkflow.seat_rows)

        return render_template('select_seat.html', reservation_id=reservation_id, origin=origin, destination=destination, flight_number=flight_number, flight_model=flight_model, seat_rows=seat_rows)

@app.route('/payment/<reservation_id>/<origin>/<destination>', methods=['GET', 'POST'])
async def payment(reservation_id, origin, destination):
    # Get booking workflow handle and query for reservation_info
    client = await Client.connect("localhost:7233")
    booking_workflow = client.get_workflow_handle(f'booking-{origin}-{destination}-{reservation_id}')
    reservation_info=await booking_workflow.query(FlightBookingWorkflow.reservation_info)
  
    if request.method == 'POST':
        # Get form data
        input = GetPaymentInput(
            amount='149999',
            token=request.form.get('credit-card'),
            currency='usd'
        )   

        # Start payment workflow
        client = await Client.connect("localhost:7233")
        
        # Ensure credit card is valid otherwise throw error
        isPayment = False
        while isPayment is not True:
            try:
                receipt_url = await client.execute_workflow(
                    CreatePaymentWorkflow.run,
                    input,
                    id=f'payment-{reservation_info.origin}-{reservation_info.destination}-{reservation_info.reservation_id}',
                    task_queue="default",
                )

                isPayment = True
            except WorkflowFailureError:
                return render_template('payment.html',reservation_id=reservation_info.reservation_id, origin=reservation_info.origin, destination=reservation_info.destination, flight_number=reservation_info.flight_number, flight_model=reservation_info.flight_model, seat=reservation_info.seat, error_message="Invalid Credit Card.")

        # Generate confirmation number: 6 characters, uppercase letters and digits
        confirmation_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        return render_template('confirmation.html', flight_number=reservation_info.flight_number, seat=reservation_info.seat, receipt_url=receipt_url,confirmation_number=confirmation_number)
    return render_template('payment.html',reservation_id=reservation_id, origin=origin, destination=destination)


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
