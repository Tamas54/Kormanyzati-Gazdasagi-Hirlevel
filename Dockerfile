FROM python:3.11-slim

WORKDIR /app

# Clean pip cache and install fresh
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip cache purge
RUN pip install --no-cache-dir --force-reinstall -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]