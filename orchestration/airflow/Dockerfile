FROM python:3.10-slim
WORKDIR /dags
COPY dags/ ./dags/
RUN pip install --no-cache-dir apache-airflow==2.6.3

# This container is a helper to package DAGs; it is not intended to run Airflow itself in production.
CMD ["/bin/true"]
