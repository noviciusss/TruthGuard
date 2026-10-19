FROM python:3.11.2-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TRUTHGUARD_OFFLINE=true

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt -r requirements-dev.txt

COPY config.yaml .env.example README.md Makefile ./
COPY src ./src
COPY bench ./bench
COPY app ./app
COPY tests ./tests
COPY data ./data
COPY reports ./reports

ENV PYTHONPATH=/app/src

EXPOSE 8501 8000

CMD ["streamlit", "run", "app/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
