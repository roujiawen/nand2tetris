.PHONY: pyenv-check pyenv-install venv deps-check test test-compiler test-tokenizer clean

SHELL := bash
.ONESHELL:

PYENV ?= pyenv
PYTHON_VERSION ?= 3.12.7
VENV_DIR ?= .venv
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_PIP := $(VENV_DIR)/bin/pip

pyenv-check:
	@command -v $(PYENV) >/dev/null 2>&1 || ( \
		echo "pyenv is not installed or not on PATH."; \
		echo "Install pyenv, then re-run: make venv"; \
		exit 1; \
	)

pyenv-install: pyenv-check
	# Install the pinned interpreter (no-op if already present)
	$(PYENV) install -s $(PYTHON_VERSION)
	# Ensure this directory uses the pinned interpreter
	$(PYENV) local $(PYTHON_VERSION)

venv: pyenv-install
	# Create a hermetic venv using the pyenv-selected interpreter
	if [[ ! -x "$(VENV_PYTHON)" ]]; then
		$(PYENV) exec python -m venv "$(VENV_DIR)"
	fi
	"$(VENV_PIP)" install -U pip
	"$(VENV_PIP)" install -r requirements-dev.txt

deps-check: venv
	@"$(VENV_PYTHON)" -c "import pytest" >/dev/null 2>&1 || ( \
		echo "pytest is not installed in $(VENV_DIR)."; \
		echo "Recreate env with: make clean && make venv"; \
		exit 1; \
	)

test:
	# Prefer the hermetic pyenv+venv+pytest flow when available, but allow running the
	# stdlib unittest suite when pyenv isn't installed (useful in minimal environments).
	if command -v "$(PYENV)" >/dev/null 2>&1; then \
		$(MAKE) deps-check test-compiler; \
	else \
		python3 -m unittest discover -s tests -p 'test_*.py'; \
	fi

test-compiler: deps-check
	"$(VENV_PYTHON)" -m pytest -k compiler

test-tokenizer: deps-check
	"$(VENV_PYTHON)" -m pytest -k tokenizer

clean:
	rm -rf "$(VENV_DIR)"

