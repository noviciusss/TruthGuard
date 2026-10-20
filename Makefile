PYTHON ?= .venv/bin/python
export PYTHONPATH := src

.PHONY: help install install-ml install-orchestration test compile smoke demo wild api ui

help:
	@printf '%s\n' 'make install  Create the local virtualenv and install pinned dependencies' \
		'make install-ml Install optional CPU BGE/FAISS retrieval dependencies' \
		'make install-orchestration Install optional LangGraph orchestration' \
		'make test     Run the offline test suite' \
		'make compile  Compile-check Python sources' \
		'make smoke    Run the configuration smoke check' \
		'make demo     Generate the reproducible six-question judge demo' \
		'make wild     Evaluate the 20-question wild robustness set offline' \
		'make api      Start the FastAPI server' \
		'make ui       Start the Streamlit demo'

install:
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt -r requirements-dev.txt

install-ml:
	@test -x "$(PYTHON)" || (printf '%s\n' 'Missing .venv. Run: make install' >&2; exit 1)
	$(PYTHON) -m pip install -r requirements-ml.txt

install-orchestration:
	@test -x "$(PYTHON)" || (printf '%s\n' 'Missing .venv. Run: make install' >&2; exit 1)
	$(PYTHON) -m pip install -r requirements-orchestration.txt

test:
	@test -x "$(PYTHON)" || (printf '%s\n' 'Missing .venv. Run: make install' >&2; exit 1)
	$(PYTHON) -m pytest -q

compile:
	@test -x "$(PYTHON)" || (printf '%s\n' 'Missing .venv. Run: make install' >&2; exit 1)
	$(PYTHON) -m compileall -q src bench app tests

smoke:
	@test -x "$(PYTHON)" || (printf '%s\n' 'Missing .venv. Run: make install' >&2; exit 1)
	$(PYTHON) -m truthguard.config

demo:
	@test -x "$(PYTHON)" || (printf '%s\n' 'Missing .venv. Run: make install' >&2; exit 1)
	TRUTHGUARD_OFFLINE=true $(PYTHON) scripts/run_demo.py

wild:
	@test -x "$(PYTHON)" || (printf '%s\n' 'Missing .venv. Run: make install' >&2; exit 1)
	TRUTHGUARD_OFFLINE=true PYTHONPATH=.:src $(PYTHON) scripts/evaluate_wild.py

api:
	@test -x "$(PYTHON)" || (printf '%s\n' 'Missing .venv. Run: make install' >&2; exit 1)
	$(PYTHON) -m uvicorn truthguard.api:app --host 127.0.0.1 --port 8000

ui:
	@test -x "$(PYTHON)" || (printf '%s\n' 'Missing .venv. Run: make install' >&2; exit 1)
	$(PYTHON) -m streamlit run app/streamlit_app.py --server.address=127.0.0.1 --server.port=8501
