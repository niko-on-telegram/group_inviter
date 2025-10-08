UV = uv
PYTHON_VERSION = 3.13
VENV = .venv
PYTHON = $(VENV)/bin/python
RUFF = $(VENV)/bin/ruff
MYPY = $(VENV)/bin/mypy
INSTALL_EXTRAS ?= dev

.PHONY: setup install run run-bot lint clean

$(VENV)/bin/python:
	$(UV) venv --python $(PYTHON_VERSION) $(VENV)

$(VENV)/.installed: pyproject.toml $(VENV)/bin/python
ifeq ($(strip $(INSTALL_EXTRAS)),)
	$(UV) pip install --python $(PYTHON) --editable .
else
	$(UV) pip install --python $(PYTHON) --editable .[${INSTALL_EXTRAS}]
endif
	touch $@

setup: $(VENV)/.installed

install: setup

run: setup
	$(VENV)/bin/start-bot

run-bot: run

lint: setup
	$(RUFF) check src tests
	$(MYPY) src

clean:
	rm -rf $(VENV)
