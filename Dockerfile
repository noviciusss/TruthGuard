FROM python:3.11.2-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TRUTHGUARD_OFFLINE=true

WORKDIR /app

# make supports the same offline test entry point; GitPython requires git.
# Core dependencies use wheels and need no compiler or optional ML system libs.
RUN apt-get update \
    && apt-get install -y --no-install-recommends make git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.lock requirements-ml.lock requirements-orchestration.lock ./
RUN python -m pip install pip==26.2.1 \
    && python -m pip install -r requirements.lock \
    && python -m pip check

COPY config.yaml .env.example .python-version README.md SUBMISSION.md Makefile ./
COPY docs ./docs
COPY src ./src
COPY bench ./bench
COPY app ./app
COPY tests ./tests
COPY scripts ./scripts
# Explicit inputs avoid baking .env, virtualenvs, model caches, SQLite provider
# state, or raw live-evaluation JSONL files into the image.
COPY data/corpus ./data/corpus
COPY data/factsheet ./data/factsheet
COPY data/benchmark ./data/benchmark
COPY reports/*.md reports/review_sheet.csv ./reports/

ENV PYTHONPATH=/app/src

RUN make test PYTHON=python

EXPOSE 8501 8000

CMD ["streamlit", "run", "app/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
