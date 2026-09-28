FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN groupadd --system sensor && useradd --system --gid sensor --home /app sensor
WORKDIR /app
COPY packages/sensor-sdk /tmp/sensor-sdk
COPY apps/ssh-honeypot/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir /tmp/sensor-sdk -r /tmp/requirements.txt
COPY apps/ssh-honeypot /app
RUN mkdir /data && chown -R sensor:sensor /app /data
USER sensor
EXPOSE 2222
CMD ["python", "main.py"]
