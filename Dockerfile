# Use the official Python image
FROM python:3.9

WORKDIR /app

COPY requirements.txt .
COPY app.py .
COPY auth_original.py .
COPY database.py .

RUN pip install --no-cache-dir -r requirements.txt

# Expose Streamlit default port
EXPOSE 8501

# Set environment variables
ENV ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
ENV SEARCH_API_KEY=${SEARCH_API_KEY}
ENV SMTP_SERVER=${SMTP_SERVER}
ENV SMTP_PORT=${SMTP_PORT}
ENV SMTP_USER=${SMTP_USER}
ENV SMTP_PASSWORD=${SMTP_PASSWORD}

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
