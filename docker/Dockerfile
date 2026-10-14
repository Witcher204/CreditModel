FROM python:3.11-slim

WORKDIR /app

COPY docker/requirements.txt ./docker/

RUN pip install --no-cache-dir -r docker/requirements.txt

COPY frontend/ ./frontend/

COPY MLmodel/credit_model.joblib ./MLmodel/

COPY MLmodel/predict.py ./MLmodel/

EXPOSE 8001

CMD ["python", "MLmodel/predict.py"]