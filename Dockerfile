# Controller image. The simulator is NOT baked in: the grader runs its own copy and passes its URL.
ARG BASE_IMAGE=python:3.12-slim
FROM ${BASE_IMAGE}
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONHASHSEED=0
WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY controller/ controller/
VOLUME ["/app/state"]
ENTRYPOINT ["python", "-m", "controller"]
CMD ["run", "--url", "http://127.0.0.1:8700", "--db", "/app/state/controller.db"]
