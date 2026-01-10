# Include environment variables from .env file
-include .env

# Define the path to your Python executable
# Use 'python3' or 'python' depending on your system
PYTHON_EXECUTABLE = py
PYTHON ?= $(PYTHON_EXECUTABLE)
VENV_DIR = .venv
PYTHON_VERSION ?= 3.11

# Create venv with specified Python version if it doesn't exist, or activate if it does
venv:
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment already exists. Activating..."; \
	else \
		echo "Creating virtual environment with Python $(PYTHON_VERSION)..."; \
		py -$(PYTHON_VERSION) -m venv $(VENV_DIR); \
		echo "Virtual environment created successfully."; \
	fi

# The install rule now uses the path provided by VS Code
install:
	@echo "Using Python interpreter: $(PYTHON)"
	$(PYTHON) -m pip install -r ../requirements.txt

# The clean rule is often useful too
clean:
	@echo "Cleaning up build artifacts..."
	@find . -name "__pycache__" -exec rm -rf {} +
	@find . -name "*.pyc" -delete

run:
	@$(PYTHON) twilio_call.py