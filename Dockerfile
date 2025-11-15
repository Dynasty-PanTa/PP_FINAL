FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p uploads
ENV FLASK_APP=run.py
CMD ["gunicorn", "-b", "0.0.0.0:5000", "run:app"]
