#!/bin/bash

# Wait for the database directory to be available
while [ ! -d "/var/lib/estateai" ]; do
    echo "Waiting for database directory..."
    sleep 1
done

# Ensure correct permissions
chmod 777 /var/lib/estateai

# Initialize the database
python3 startup.py

# If database initialization was successful, start the app
if [ $? -eq 0 ]; then
    echo "Database initialized successfully, starting Streamlit app..."
    streamlit run app.py --server.port=8501 --server.address=0.0.0.0
else
    echo "Database initialization failed!"
    exit 1
fi