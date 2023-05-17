from flask import Flask, render_template, request
import random
import string
from datetime import datetime, timedelta
from temporalio.client import Client
import asyncio
from flights_activities import GetFlightsInput
import uuid

# Import the workflow from the previous code
from flights_workflow import GetFlightsWorkflow


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


        # Generate random flights
        #flights = generate_flights(origin, destination)

        # Start Temporal workflow
        client = await Client.connect("localhost:7233")

        result = await client.execute_workflow(
            GetFlightsWorkflow.run,
            input,
            id=f'{input.origin}-{input.destination}-{reservation_id}',
            task_queue="default",
        )

        return render_template('flights.html', flights=result)

    return render_template('index.html')


@app.route('/select/<flight_number>', methods=['GET', 'POST'])
def select_seat(flight_number):
    if request.method == 'POST':
        # Get form data
        seat = request.form.get('seat')

        # Generate confirmation number: 6 characters, uppercase letters and digits
        confirmation_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        return render_template('confirmation.html', flight_number=flight_number, seat=seat, confirmation_number=confirmation_number)

    return render_template('select_seat.html', flight_number=flight_number)


if __name__ == '__main__':
    app.run(debug=True)
