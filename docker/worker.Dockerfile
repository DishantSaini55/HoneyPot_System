FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/apps/api:/app
RUN groupadd --system app && useradd --system --gid app --home /app app
WORKDIR /app
COPY apps/worker/requirements.txt /tmp/worker.txt
COPY ml/requirements.txt /tmp/ml.txt
RUN pip install --no-cache-dir -r /tmp/worker.txt -r /tmp/ml.txt
COPY apps/api/app /app/apps/api/app
COPY apps/worker /app/apps/worker
COPY ml /app/ml
RUN python -m ml.train --output /app/ml/model/baseline.joblib --report /app/ml/model/evaluation.json
RUN chown -R app:app /app
USER app
CMD ["python", "apps/worker/main.py"]
