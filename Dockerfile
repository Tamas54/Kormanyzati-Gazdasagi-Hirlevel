FROM python:3.11-slim

WORKDIR /app

# Install minimal requirements first
COPY requirements_minimal.txt .
RUN pip install --upgrade pip
RUN pip cache purge
RUN pip install --no-cache-dir -r requirements_minimal.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]