# Synarmo local development Makefile
#
# Common commands:
#   make help         Show available targets.
#   make dev          Install Synarmo with dev, service, and llama extras.
#   make test         Run the Python test suite.
#   make serve        Run the local service in the foreground.
#   make start        Start the local service in the background.
#   make stop         Stop the background service started by make start.
#   make ui           Print the browser UI URL.
#   make model-ensure Check/download the configured llama.cpp model.
#
# Configuration:
#   PYTHON=.venv/bin/python    Python interpreter to use.
#   SYNARMO=.venv/bin/synarmo  Synarmo CLI executable to use.
#   HOST=127.0.0.1             Service host.
#   PORT=8765                  Service port.
#   BACKEND=llama-cpp          Backend for real local inference.
#   PROFILE=default            User profile name.
#
# Examples:
#   make serve BACKEND=mock
#   make start PORT=8766
#   make suggest TEXT="I want to" CONTEXT="At home, asking for help"

.PHONY: help install dev llama test compile serve serve-mock start start-mock stop restart status health ui docs suggest compose models model-current model-ensure clean

PYTHON ?= .venv/bin/python
SYNARMO ?= .venv/bin/synarmo
HOST ?= 127.0.0.1
PORT ?= 8765
BACKEND ?= llama-cpp
PROFILE ?= default
TEXT ?= I want to
CONTEXT ?= At home, asking for help
PID_FILE ?= .synarmo-service.pid
LOG_FILE ?= .synarmo-service.log
LOCAL_MODELS_CACHE ?= $(shell grep -E '^LOCAL_MODELS_CACHE=' .env 2>/dev/null | tail -1 | cut -d= -f2-)
SYNARMO_MODEL ?= $(shell grep -E '^SYNARMO_MODEL=' .env 2>/dev/null | tail -1 | cut -d= -f2-)
SYNARMO_MODEL_REPO_ID ?= $(shell grep -E '^SYNARMO_MODEL_REPO_ID=' .env 2>/dev/null | tail -1 | cut -d= -f2-)

help:
	@echo "Synarmo local development"
	@echo ""
	@echo "Setup:"
	@echo "  make install      Install Synarmo package only"
	@echo "  make dev          Install dev, service, and llama extras"
	@echo "  make llama        Install llama and service extras"
	@echo ""
	@echo "Checks:"
	@echo "  make test         Run pytest"
	@echo "  make compile      Run compileall over src and tests"
	@echo ""
	@echo "Service:"
	@echo "  make serve        Run service in foreground with BACKEND=$(BACKEND)"
	@echo "  make serve-mock   Run service in foreground with mock backend"
	@echo "  make start        Start service in background; logs go to $(LOG_FILE)"
	@echo "  make start-mock   Start mock service in background"
	@echo "  make stop         Stop background service"
	@echo "  make restart      Stop then start background service"
	@echo "  make status       Show background service status"
	@echo "  make health       Call /health"
	@echo ""
	@echo "Testing UI/API:"
	@echo "  make ui           Print browser UI URL"
	@echo "  make docs         Print FastAPI docs URL"
	@echo "  make suggest      Call /suggest with TEXT and CONTEXT"
	@echo "  make compose      Run interactive CLI compose loop"
	@echo "  make models       List GGUF files in LOCAL_MODELS_CACHE"
	@echo "  make model-current Show the selected SYNARMO_MODEL"
	@echo "  make model-ensure Check/download the configured llama.cpp model"
	@echo ""
	@echo "Overrides:"
	@echo "  BACKEND=mock PORT=8766 TEXT='Can you' CONTEXT='Asking for help'"

# Install package in editable mode.
install:
	$(PYTHON) -m pip install -e .

# Install all dependencies needed for local development and real GGUF inference.
dev:
	$(PYTHON) -m pip install -e ".[dev,service,llama]"

# Install only service and llama extras for local inference.
llama:
	$(PYTHON) -m pip install -e ".[service,llama]"

# Run tests.
test:
	$(PYTHON) -m pytest

# Run a fast syntax/import smoke check.
compile:
	python3 -m compileall src tests

# Run the service in the foreground. Use Ctrl-C to stop. For llama.cpp, this
# checks LOCAL_MODELS_CACHE and downloads SYNARMO_MODEL from SYNARMO_MODEL_REPO_ID
# when the selected GGUF file is missing.
serve:
	$(SYNARMO) serve --host $(HOST) --port $(PORT) --profile $(PROFILE) --backend $(BACKEND)

# Run the deterministic mock backend in the foreground.
serve-mock:
	$(SYNARMO) serve --host $(HOST) --port $(PORT) --profile $(PROFILE) --backend mock

# Start the service in the background and write a PID file.
start:
	@if [ -f "$(PID_FILE)" ] && kill -0 "$$(cat $(PID_FILE))" 2>/dev/null; then \
		echo "Synarmo is already running with PID $$(cat $(PID_FILE))"; \
	else \
		nohup $(SYNARMO) serve --host $(HOST) --port $(PORT) --profile $(PROFILE) --backend $(BACKEND) > "$(LOG_FILE)" 2>&1 & echo $$! > "$(PID_FILE)"; \
		STARTED=0; \
		for attempt in 1 2 3 4 5 6 7 8 9 10; do \
			if curl -fs http://$(HOST):$(PORT)/health >/dev/null 2>&1; then STARTED=1; break; fi; \
			if ! kill -0 "$$(cat $(PID_FILE))" 2>/dev/null; then break; fi; \
			sleep 1; \
		done; \
		if [ "$$STARTED" = "1" ]; then \
			echo "Started Synarmo on http://$(HOST):$(PORT) with PID $$(cat $(PID_FILE))"; \
			echo "Logs: $(LOG_FILE)"; \
		else \
			echo "Synarmo failed to start. See $(LOG_FILE)."; \
			rm -f "$(PID_FILE)"; \
			if [ -s "$(LOG_FILE)" ]; then tail -40 "$(LOG_FILE)"; fi; \
			exit 1; \
		fi; \
	fi

# Start the deterministic mock backend in the background.
start-mock:
	$(MAKE) start BACKEND=mock

# Stop the background service started by make start.
stop:
	@if [ -f "$(PID_FILE)" ]; then \
		PID="$$(cat $(PID_FILE))"; \
		if kill -0 "$$PID" 2>/dev/null; then \
			kill "$$PID"; \
			echo "Stopped Synarmo PID $$PID"; \
		else \
			echo "No running process found for PID $$PID"; \
		fi; \
		rm -f "$(PID_FILE)"; \
	else \
		echo "No $(PID_FILE) found"; \
	fi

# Restart the background service.
restart: stop start

# Show whether the background service is running.
status:
	@if curl -fs http://$(HOST):$(PORT)/health >/dev/null 2>&1; then \
		echo "Synarmo responding at http://$(HOST):$(PORT)"; \
	elif [ -f "$(PID_FILE)" ] && kill -0 "$$(cat $(PID_FILE))" 2>/dev/null; then \
		echo "Synarmo running with PID $$(cat $(PID_FILE)) at http://$(HOST):$(PORT)"; \
	else \
		echo "Synarmo is not running from $(PID_FILE)"; \
	fi

# Call the service health endpoint.
health:
	curl -s http://$(HOST):$(PORT)/health
	@echo ""

# Print the browser UI URL.
ui:
	@echo "http://$(HOST):$(PORT)/ui"

# Print the FastAPI docs URL.
docs:
	@echo "http://$(HOST):$(PORT)/docs"

# Call /suggest with configurable TEXT and CONTEXT.
suggest:
	curl -s -X POST http://$(HOST):$(PORT)/suggest \
		-H 'content-type: application/json' \
		-d '{"text":"$(TEXT)","context":"$(CONTEXT)"}'
	@echo ""

# Run the terminal type-ahead loop.
compose:
	$(SYNARMO) compose "$(TEXT)" --context "$(CONTEXT)" --profile $(PROFILE) --backend $(BACKEND)

# List locally downloaded GGUF model files.
models:
	@CACHE="$${LOCAL_MODELS_CACHE:-$(LOCAL_MODELS_CACHE)}"; \
	CACHE="$${CACHE/#\~/$${HOME}}"; \
	if [ -d "$$CACHE" ]; then \
		find "$$CACHE" -maxdepth 1 -type f -name "*.gguf" -print | sort; \
	else \
		echo "Model cache not found: $$CACHE"; \
	fi

# Show the model selected by .env.
model-current:
	@echo "LOCAL_MODELS_CACHE=$(LOCAL_MODELS_CACHE)"
	@echo "SYNARMO_MODEL_REPO_ID=$(SYNARMO_MODEL_REPO_ID)"
	@echo "SYNARMO_MODEL=$(SYNARMO_MODEL)"

# Load the configured backend once. For llama.cpp this checks the local cache
# and downloads the configured Hugging Face GGUF model if it is missing.
model-ensure:
	@if [ "$(BACKEND)" = "mock" ]; then \
		echo "mock backend does not need a local model"; \
	else \
		$(PYTHON) -c "from synarmo.engine import SynarmoEngine; SynarmoEngine.load(backend='$(BACKEND)'); print('Model ready for $(BACKEND)')"; \
	fi

# Clean local runtime artifacts created by make start and Python tooling.
clean:
	rm -f "$(PID_FILE)" "$(LOG_FILE)"
	find src tests -type d -name __pycache__ -prune -exec rm -rf {} +
	find src tests -type f -name "*.pyc" -delete
