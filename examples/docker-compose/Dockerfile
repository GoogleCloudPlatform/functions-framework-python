# Use the Python base image
FROM python

# Set a working directory
WORKDIR /func

# Copy all the files from the local directory into the container
COPY . .

# Install the Functions Framework
RUN pip install functions-framework

# Install any dependencies of the function
RUN pip install -r requirements.txt

# Run the function
CMD ["functions-framework", "--target=hello", "--debug"]
