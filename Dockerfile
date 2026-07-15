FROM python:3.9-slim

# Set up a new user named "user" with user ID 1000 (Required for Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Copy requirements and install
COPY --chown=user requirements.txt .

# Install CPU-only PyTorch first (saves a huge amount of space/memory on free CPU tiers)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install the rest of the requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY --chown=user . /app

# Create upload and output directories with correct permissions
RUN mkdir -p /app/uploads /app/outputs && chmod 777 /app/uploads /app/outputs

EXPOSE 7860

CMD ["python", "app.py"]
