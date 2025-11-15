# MiniMart REST API (Flask) — PostgreSQL & Docker-ready Guide

This repository contains a Flask-based MiniMart REST API with JWT authentication, product image uploads (2 MB limit), categories, invoices, and basic reporting. The project is configured to work with SQLite for quick local testing and with PostgreSQL for production or Dockerized development.

This guide explains step-by-step how to set the project up from scratch on your machine and how to run it with Docker Compose using PostgreSQL.

## Prerequisites
1. Git installed on your machine.
2. Docker and Docker Compose installed (for Docker steps).
3. Python 3.10+ and pip (for local development without Docker).

## Quick local development (SQLite)
Clone the repo and create a virtual environment:

```
git clone <your-repo> minimart
cd minimart
python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Initialize the database and run migrations:

```
export FLASK_APP=run.py
flask db init
flask db migrate -m "initial"
flask db upgrade
```

Start the app:

```
flask run
```

Swagger UI will be available at http://localhost:5000/ and the Postman collection provided can be used to test endpoints.

## Full Docker Compose setup with PostgreSQL (recommended)
This uses the included `docker-compose.yml` which defines two services: db (Postgres) and web (Flask app).

1. From the project root run:

```
docker-compose build
docker-compose up
```

The `web` service in docker-compose runs `flask db upgrade` on startup (if the migrations exist). If you haven't created migrations locally, you can either run them inside the container or create them locally and rebuild. To create migrations inside the running container:

```
# open a shell in the running web container
docker-compose exec web bash
flask db init
flask db migrate -m "initial"
flask db upgrade
exit
```

After migrations run, the API will be available at http://localhost:5000/ and the Swagger UI will show all endpoints.

## Environment variables
The web container uses these environment variables defined in `docker-compose.yml`:

- DATABASE_URL: postgresql://postgres:password@db:5432/minimart
- JWT_SECRET_KEY: change-me
- SECRET_KEY: change-me
- FLASK_APP: run.py
- FLASK_ENV: development

You can override these values in your environment or in a .env file when running locally. For Docker Compose, you can create a `.env` file or export variables before starting.

## Common troubleshooting
- If the web service fails because Postgres is not ready yet, the `depends_on` helps but doesn't wait for DB readiness; the compose command runs `flask db upgrade || true` so the service will continue. If migrations fail, run them manually inside the container after the DB is ready.
- To inspect logs: `docker-compose logs -f web` and `docker-compose logs -f db`.
- If you get a connection refused error, ensure Docker Desktop is running and no other service occupies port 5000.

## Postman
A basic Postman collection is included as `postman_collection.json`. Import it into Postman and update the `baseUrl` if needed.

## Notes on production
- Use a managed Postgres instance or secure your DB password.
- Use environment variables to store secrets; never commit secrets to Git.
- Use an object store (S3) for images in production instead of local uploads.

If you want I can:
  * Recreate a fresh ZIP with these Postgres changes (I already updated the repo here), or
  * Run through each command with exact outputs to help you on your machine step-by-step.

