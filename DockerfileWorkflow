FROM python:3.11
RUN mkdir /app 
COPY . /app
COPY pyproject.toml /app 
WORKDIR /app
RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --with encryption
CMD [ "poetry", "run", "python", "/app/app.py" ]
