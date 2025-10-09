UV = uv
PYTHON_VERSION = 3.13
VENV = .venv
PYTHON = $(VENV)/bin/python
RUFF = $(VENV)/bin/ruff
MYPY = $(VENV)/bin/mypy
INSTALL_EXTRAS ?= dev
INSTALL_EDITABLE ?= 1

ifeq ($(strip $(INSTALL_EXTRAS)),)
EXTRAS_SUFFIX :=
else
EXTRAS_SUFFIX := [$(INSTALL_EXTRAS)]
endif

.PHONY: setup install run run-bot lint clean docker-up-alert

$(VENV)/bin/python:
	$(UV) venv --python $(PYTHON_VERSION) $(VENV)

$(VENV)/.installed: pyproject.toml $(VENV)/bin/python
ifeq ($(strip $(INSTALL_EDITABLE)),1)
	$(UV) pip install --python $(PYTHON) --editable .$(EXTRAS_SUFFIX)
else
	$(UV) pip install --python $(PYTHON) .$(EXTRAS_SUFFIX)
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

docker-up-alert:
	docker compose up -d
	./scripts/configure_grafana_contact_point.sh
