FROM python:3.11.9-slim

RUN useradd --no-create-home --shell /bin/false appuser

WORKDIR /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R appuser:appuser /workspace

USER appuser

EXPOSE 8000

CMD ["python", "main.py"]
