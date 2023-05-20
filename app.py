from flask import Flask, render_template, request, abort
import random
import string
from datetime import datetime, timedelta
from temporalio.client import Client, WorkflowFailureError
from flights_activities import GetFlightsInput, GetPaymentInput
import uuid

# Import the workflow from the previous code
from flights_workflow import GetFlightsWorkflow, GetSeatConfigurationWorkflow, CreatePaymentWorkflow


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

        flights = await client.execute_workflow(
            GetFlightsWorkflow.run,
            input,
            id=f'flights-{input.origin}-{input.destination}-{reservation_id}',
            task_queue="default",
        )
        
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
        
        seat_rows = await client.execute_workflow(
            GetSeatConfigurationWorkflow.run,
            flight_model,
            id=f'seats-{origin}-{destination}-{reservation_id}',
            task_queue="default",
        ) 

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
