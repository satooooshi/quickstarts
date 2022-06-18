FROM python:3.7.1-alpine3.8
RUN pip install --upgrade pip
COPY . /app
WORKDIR /app
RUN pip install flask flask_cors dapr cloudevents uvicorn requests fastapi
EXPOSE 5003
CMD ["python", "app.py"]