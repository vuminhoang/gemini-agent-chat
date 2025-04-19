FROM python:3.10-slim

WORKDIR /app

COPY services/assistant/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY services/assistant /app

CMD ["uvicorn", "webhook:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

