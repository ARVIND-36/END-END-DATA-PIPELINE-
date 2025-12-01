# End-to-End Data Pipeline

A real-time data pipeline using Kafka, Debezium, PostgreSQL, MinIO, and Apache Airflow.

## 🚀 Quick Start

```bash
# Start all services
docker compose up -d

# Initialize Airflow database (first time only)
docker compose exec airflow-scheduler airflow db migrate

# Create Airflow admin user
docker compose exec airflow-webserver airflow users create \
    --username admin \
    --firstname FIRST_NAME \
    --lastname LAST_NAME \
    --role Admin \
    --email admin@example.org \
    --password yourpassword
```

## 📦 Services

| Service | Port | Description |
|---------|------|-------------|
| Airflow UI | [localhost:8080](http://localhost:8080) | Workflow orchestration |
| MinIO Console | [localhost:9001](http://localhost:9001) | Object storage |
| Kafka Connect | [localhost:8083](http://localhost:8083) | CDC connector API |
| PostgreSQL | localhost:5432 | Banking database |
| Kafka | localhost:9092 / 29092 | Message broker |
| Zookeeper | localhost:2181 | Kafka coordination |

## 🛠️ Useful Commands

```bash
# Stop all services
docker compose stop

# Start all services
docker compose start

# View logs
docker compose logs -f <service-name>

# Check service status
docker compose ps
```

## 📁 Project Structure

```
├── docker-compose.yml      # Service definitions
├── dockerfile-airflow.dockerfile
├── docker/
│   ├── dags/               # Airflow DAGs
│   ├── logs/               # Airflow logs
│   └── postgres/data/      # PostgreSQL data
├── consumer/               # Kafka consumers
├── data-generator/         # Test data generation
└── banking_dbt/            # dbt models
```

## 🗄️ Connect PostgreSQL to DBeaver

To connect the **Banking database** to DBeaver:

1. Open DBeaver → **Database** → **New Database Connection**
2. Select **PostgreSQL** and click **Next**
3. Enter the following connection details:

| Setting | Value |
|---------|-------|
| Host | `localhost` |
| Port | `5432` |
| Database | `banking` |
| Username | `postgres` |
| Password | `postgres` |

4. Click **Test Connection** to verify
5. Click **Finish**

> **Note:** Make sure Docker services are running (`docker compose up -d`) before connecting.