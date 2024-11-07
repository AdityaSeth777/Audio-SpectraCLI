# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Debug: List files to ensure requirements.txt is present
RUN ls -al /app

# Install dependencies if requirements.txt exists
RUN if [ -f "requirements.txt" ]; then pip3 install --no-cache-dir -r requirements.txt; fi

# Command to run your module
CMD ["python", "-m", "Audio_SpectraCLI.main"]
