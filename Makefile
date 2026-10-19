PYTHON ?= .venv/bin/python
export PYTHONPATH := src

.PHONY: help install test compile smoke

help:
	@printf '%s\n' 'make install  Create the local virtualenv and install pinned dependencies' \
		'make test     Run the offline test suite' \
		'make compile  Compile-check Python sources' \
		'make smoke    Run the configuration smoke check'

install:
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt -r requirements-dev.txt

test:
	@test -x "$(PYTHON)" || (printf '%s\n' 'Missing .venv. Run: make install' >&2; exit 1)
	$(PYTHON) -m pytest -q

compile:
	@test -x "$(PYTHON)" || (printf '%s\n' 'Missing .venv. Run: make install' >&2; exit 1)
	$(PYTHON) -m compileall -q src bench app tests

smoke:
	@test -x "$(PYTHON)" || (printf '%s\n' 'Missing .venv. Run: make install' >&2; exit 1)
	$(PYTHON) -m truthguard.config
