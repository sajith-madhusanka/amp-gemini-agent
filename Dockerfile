FROM python:3.11.9-slim

RUN useradd --no-create-home --shell /bin/false appuser

WORKDIR /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R appuser:appuser /workspace

USER appuser

EXPOSE 8000

# AMP overrides CMD with its own gunicorn launcher. GUNICORN_CMD_ARGS is
# appended to gunicorn's argv regardless of which config file (-c) it uses,
# making it more reliable than gunicorn.conf.py for forcing async workers.
ENV GUNICORN_CMD_ARGS="--worker-class uvicorn.workers.UvicornWorker --timeout 300 --workers 1"

CMD ["python", "main.py"]
