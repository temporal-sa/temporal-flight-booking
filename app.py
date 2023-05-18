from flask import Flask, render_template, request
import random
import string
from datetime import datetime, timedelta
from temporalio.client import Client
from flights_activities import GetFlightsInput
import uuid

# Import the workflow from the previous code
from flights_workflow import GetFlightsWorkflow, GetSeatConfigurationWorkflow


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

        # Generate confirmation number: 6 characters, uppercase letters and digits
        confirmation_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        return render_template('confirmation.html', flight_number=flight_number, flight_model=flight_model, seat=seat, confirmation_number=confirmation_number)
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
