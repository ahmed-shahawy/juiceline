FROM swift:5.9-focal

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy package files
COPY Package.swift .
COPY Sources ./Sources
COPY Tests ./Tests

# Build dependencies
RUN swift package resolve

# Expose common ports for development
EXPOSE 8080

# Default command
CMD ["swift", "test"]