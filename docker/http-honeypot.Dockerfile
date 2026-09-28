FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN groupadd --system sensor && useradd --system --gid sensor --home /app sensor
WORKDIR /app
COPY packages/sensor-sdk /tmp/sensor-sdk
COPY apps/http-honeypot/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir /tmp/sensor-sdk -r /tmp/requirements.txt
COPY apps/http-honeypot /app
RUN chown -R sensor:sensor /app
USER sensor
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
