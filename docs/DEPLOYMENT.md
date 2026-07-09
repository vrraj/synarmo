---
layout: default
title: "Deployment Guide | Synarmo"
description: "Installation and deployment instructions for synarmo package."
---

# Deployment Guide

This guide explains how to deploy the Synarmo package on other machines.

## Package Files

After building, the following distribution files are created in the `dist/` directory:
- `synarmo-0.x.x-py3-none-any.whl` (wheel file, recommended for installation)
- `synarmo-0.x.x.tar.gz` (source distribution)

## Installation on Target Machine

### Option 1: Install from PyPI (Recommended)

Install the base package:

```bash
pip install synarmo
```

Install with llama.cpp and service dependencies:

```bash
pip install "synarmo[llama,service]"
```

### Option 2: Install from Wheel File

1. **Transfer the wheel file** to the target machine:
   ```bash
   # From your local machine
   scp dist/synarmo-0.x.x-py3-none-any.whl user@target-machine:/path/to/deploy/
   ```

2. **Install the package** on the target machine:
   ```bash
   pip install synarmo-0.x.x-py3-none-any.whl
   ```

3. **Install with extras** if needed:
   ```bash
   pip install "synarmo-0.x.x-py3-none-any.whl[llama,service]"
   ```

### Option 3: Install from Source Distribution

1. **Transfer the tar.gz file** to the target machine:
   ```bash
   scp dist/synarmo-0.x.x.tar.gz user@target-machine:/path/to/deploy/
   ```

2. **Install the package** on the target machine:
   ```bash
   pip install synarmo-0.x.x.tar.gz
   ```

### Option 4: Install from Git Repository

If you have a git repository:

```bash
pip install git+https://github.com/vrraj/synarmo.git
```

With extras:

```bash
pip install "git+https://github.com/vrraj/synarmo.git[llama,service]"
```

## Model Configuration

### Configure Local Model Cache

Create the models cache directory:

```bash
mkdir -p ~/models/synarmo
```

### Set Up Environment Variables

Create a `.env` file in your project directory:

```bash
cp .env.example .env
```

Edit `.env` with your model configuration:

```dotenv
LOCAL_MODELS_CACHE=~/models/synarmo
SYNARMO_MAX_SUGGESTIONS=3
SYNARMO_MODEL_REPO_ID=hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF
SYNARMO_MODEL=llama-3.2-1b-instruct-q4_k_m.gguf
```

### Manual Model Download

If you prefer to download the model manually:

```bash
# Download from Hugging Face
cd ~/models/synarmo
wget https://huggingface.co/hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF/resolve/main/llama-3.2-1b-instruct-q4_k_m.gguf
```

Then update `.env`:

```dotenv
LOCAL_MODELS_CACHE=~/models/synarmo
SYNARMO_MODEL=llama-3.2-1b-instruct-q4_k_m.gguf
```

## Running the Service

### Start the Service

After installation, start the FastAPI service:

```bash
synarmo serve --backend llama-cpp
```

With a specific model path:

```bash
synarmo serve \
  --backend llama-cpp \
  --model-path ~/models/synarmo/Llama-3.2-1B.Q4_K_M.gguf
```

The service starts on `http://127.0.0.1:8765`

### Service Endpoints

- `GET /health` - Health check endpoint
- `POST /suggest` - Basic suggestions endpoint
- `POST /evaluate/autocomplete` - Autocomplete evaluation endpoint
- `GET /ui` - Interactive test UI
- `WS /ws/suggest` - WebSocket endpoint for real-time suggestions

### Using as a Library

### Basic Library Usage

```python
from synarmo import SynarmoEngine

engine = SynarmoEngine.load(
    backend="llama-cpp",
    model_path="~/models/synarmo/Llama-3.2-1B.Q4_K_M.gguf"
)

suggestions = engine.suggest(
    text="I want to",
    context="At home, asking for help"
)
print([s.text for s in suggestions])
```

### Integration with Your Application

```python
from fastapi import FastAPI
from synarmo import SynarmoEngine

app = FastAPI()
engine = SynarmoEngine.load(backend="llama-cpp")

@app.post("/api/suggest")
async def get_suggestions(request: dict):
    text = request.get("text")
    context = request.get("context")
    
    # Get suggestions
    suggestions = engine.suggest(text=text, context=context)
    
    return {"suggestions": [s.text for s in suggestions]}
```

## System Requirements

- Python 3.9 or higher
- pip package manager

### For llama.cpp Backend:
- `llama-cpp-python` package (install with `[llama]` extra)
- A compatible GGUF model file

### For Service Mode:
- FastAPI (install with `[service]` extra)
- Uvicorn (install with `[service]` extra)

## Verification

After installation, verify the package is working:

```python
python -c "from synarmo import SynarmoEngine; print('Installation successful')"
```

Test with mock backend (no model required):

```python
python -c "from synarmo import SynarmoEngine; e=SynarmoEngine.load(backend='mock'); print(e.suggest('hello'))"
```

Test the service:

```bash
synarmo serve --backend mock
# Then in another terminal:
curl http://localhost:8765/health
```

Test with real model:

```bash
synarmo suggest "I want to" \
  --context "At home" \
  --backend llama-cpp
```

## Building the Package

If you want to build the package from source:

```bash
# Install build dependencies
pip install build

# Clean previous builds
rm -rf dist/ build/ src/*.egg-info

# Build new package
python -m build
```

The built files will be in the `dist/` directory.

## Troubleshooting

### Import Errors

If you get import errors, ensure you're using the correct Python environment where the package was installed:

```bash
# Check which Python you're using
which python
which pip

# Install in the correct environment
pip install synarmo
```

### Model Not Found

If the model is not found:

1. Check your `.env` file configuration
2. Verify the model path is correct
3. Ensure the models cache directory exists:
   ```bash
   mkdir -p ~/models/synarmo
   ```
4. Check file permissions on the model file

### llama-cpp-python Installation Issues

If you have trouble installing `llama-cpp-python`:

```bash
# Pre-built wheel (recommended)
pip install llama-cpp-python

# Or build from source
CMAKE_ARGS="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS" pip install llama-cpp-python --no-cache-dir --force-reinstall
```

### Service Won't Start

If the service won't start:

1. Ensure you installed with service dependencies:
   ```bash
   pip install "synarmo[service]"
   ```
2. Check if the port is already in use:
   ```bash
   lsof -i :8765
   ```
3. Verify the model is configured correctly in `.env`

### Permission Errors

Use a virtual environment to avoid permission issues:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install "synarmo[llama,service]"
```

## Production Deployment

For production deployment, consider:

1. **Use a process manager** (systemd, supervisor) to keep the service running
2. **Use a reverse proxy** (nginx) in front of the service
3. **Configure proper logging** and monitoring
4. **Use environment variables** for configuration
5. **Set up model caching** to avoid repeated downloads
6. **Configure resource limits** (CPU, memory)

### Example systemd Service

Create `/etc/systemd/system/synarmo.service`:

```ini
[Unit]
Description=Synarmo Auto-Suggest Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/your/app
Environment="PATH=/path/to/venv/bin"
EnvironmentFile=/path/to/your/app/.env
ExecStart=/path/to/venv/bin/synarmo serve --backend llama-cpp
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable synarmo
sudo systemctl start synarmo
sudo systemctl status synarmo
```

### Example nginx Configuration

Create `/etc/nginx/sites-available/synarmo`:

```nginx
upstream synarmo_backend {
    server 127.0.0.1:8765;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://synarmo_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ui {
        proxy_pass http://synarmo_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/synarmo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY pyproject.toml .
RUN pip install --no-cache-dir "synarmo[llama,service]"

# Copy application code
COPY . .

# Create models directory
RUN mkdir -p /models/synarmo

# Expose port
EXPOSE 8765

# Run service
CMD ["synarmo", "serve", "--backend", "llama-cpp", "--host", "0.0.0.0"]
```

Build and run:

```bash
docker build -t synarmo .
docker run -p 8765:8765 -v ~/models/synarmo:/models/synarmo synarmo
```

## Security Considerations

1. **Don't expose the service publicly** without authentication
2. **Use HTTPS** in production with a reverse proxy
3. **Validate and sanitize** all user inputs
4. **Rate limit** API endpoints to prevent abuse
5. **Keep models** and user profiles secure
6. **Use environment variables** for sensitive configuration
7. **Regularly update** dependencies for security patches

## Monitoring

### Health Checks

Monitor the health endpoint:

```bash
curl http://localhost:8765/health
```

### Logging

Configure logging in your application:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Metrics

Consider adding metrics collection for:
- Request latency
- Suggestion generation time
- Error rates
- Model load time

## License

MIT License - see LICENSE file for details.
