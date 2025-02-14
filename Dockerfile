# Use the official Python image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy necessary files
COPY requirements.txt .
COPY app.py .
COPY auth_original.py .
COPY database.py .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Streamlit default port
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
