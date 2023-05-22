# airline-reservation
Airline Reservation System Built on Temporal

Select an origin and destination. This will trigger a ```booking workflow```. It will kick off an activity to calculate the distance and then use that in another activity which will dynamically generate a list of flights. Once a flight is selected another activity is started via a signal to generate a seat configuration based on the flight selected. The booking workflow completes but stores the state of the reservation which can be queried at any time.

Once a seat is selected the price is shown. Entering a credit card will kick off a new ```payment workflow``` which uses Stripe. If the payment fails the workflow will be failed and user notified. If the payment succeeds the workflow will complete and a confirmation of the booking will be provided.

# Prerequisites
Uses ChatGPT to get flight information and Stripe for payment. For both an API key is needed by the worker. Register for both services and generate API keys.

# Setup
```bash
$ mkdir .venv
$ curl -sSL https://install.python-poetry.org | python3 -
$ poetry install
```

# Run App
```bash
$ poetry run python app.py
```

# Run Worker
```bash
$ export CHATGPT_API_KEY=mykey
$ export STRIPE_API_KEY=mykey
```

```bash
$ poetry run python worker.py
```

# Walkthrough
![Airline Reservation](/static/index.png)
![Airline Reservation](/static/flights.png)
![Airline Reservation](/static/seats.png)
![Airline Reservation](/static/payment.png)
![Airline Reservation](/static/confirmation.png)
