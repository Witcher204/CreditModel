FROM python:3.11-slim

WORKDIR /app

COPY docker/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY frontend/ ./frontend/
COPY MLmodel/ ./MLmodel/

EXPOSE 8000

CMD ["python", "MLmodel/predict.py"]
