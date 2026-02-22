FROM python:3.11-slim
WORKDIR /app

# Install minimal deps if requirements.txt exists
COPY requirements.txt ./requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && \
    pip install --no-cache-dir -r requirements.txt || true && \
    apt-get remove -y gcc && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Copy repository
COPY . /app
ENV PYTHONPATH=/app

CMD ["/bin/bash"]
