PYTHON ?= .venv/bin/python
export PYTHONPATH := src

.PHONY: help install install-ml install-orchestration test compile smoke demo wild retrieval subset api ui

help:
	@printf '%s\n' 'make install  Create the local virtualenv and install pinned dependencies' \
		'make install-ml Install optional CPU BGE/FAISS retrieval dependencies' \
		'make install-orchestration Install optional LangGraph orchestration' \
		'make test     Run the offline test suite' \
		'make compile  Compile-check Python sources' \
		'make smoke    Run the configuration smoke check' \
		'make demo     Generate the reproducible six-question v2 judge demo' \
		'make wild     Evaluate the 22-question v2 wild robustness set offline' \
		'make retrieval Compare hash and BGE/FAISS retrieval on dev and wild sets' \
		'make subset   Regenerate the committed fixed 40-question test subset' \
		'make api      Start the FastAPI server' \
		'make ui       Start the Streamlit demo'

install:
	python3 -m venv .venv
	$(PYTHON) -m pip install pip==26.2.1
	$(PYTHON) -m pip install -r requirements.lock
	$(PYTHON) -m pip check

install-ml:
	@test -x "$(PYTHON)" || (printf '%s\n' 'Missing .venv. Run: make install' >&2; exit 1)
	$(PYTHON) -m pip install -r requirements.lock -r requirements-ml.lock
	$(PYTHON) -m pip check

install-orchestration:
	@test -x "$(PYTHON)" || (printf '%s\n' 'Missing .venv. Run: make install' >&2; exit 1)
	$(PYTHON) -m pip install -r requirements.lock -r requirements-orchestration.lock
	$(PYTHON) -m pip check

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

retrieval:
	@test -x "$(PYTHON)" || (printf '%s\n' 'Missing .venv. Run: make install' >&2; exit 1)
	TRUTHGUARD_OFFLINE=true PYTHONPATH=.:src $(PYTHON) scripts/evaluate_retrieval.py --backend hash --output /tmp/truthguard-retrieval-hash.json
	TRUTHGUARD_OFFLINE=true TRUTHGUARD_ALLOW_BGE_OFFLINE=true PYTHONPATH=.:src $(PYTHON) scripts/evaluate_retrieval.py --backend bge --output /tmp/truthguard-retrieval-bge.json

subset:
	$(PYTHON) scripts/create_eval_subset.py

api:
	@test -x "$(PYTHON)" || (printf '%s\n' 'Missing .venv. Run: make install' >&2; exit 1)
	$(PYTHON) -m uvicorn truthguard.api:app --host 127.0.0.1 --port 8000

ui:
	@test -x "$(PYTHON)" || (printf '%s\n' 'Missing .venv. Run: make install' >&2; exit 1)
	$(PYTHON) -m streamlit run app/streamlit_app.py --server.address=127.0.0.1 --server.port=8501
