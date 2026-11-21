# Backend Development PBL — Dockerized TODO app

This repository packages Aryan Malik's [Express, EJS and MongoDB TODO app](https://github.com/KinglyyyY/BackendDevelopment/tree/main/LAB/Exam01B) from the main Backend Development repository. It demonstrates containerization, Compose, route automation, GitHub Actions, and Docker Hub publishing.

## Run with Docker Compose

Requirements: Docker Desktop with Docker Compose.

```bash
docker compose up --build
```

Open <http://localhost:3000>. Compose starts MongoDB first, waits for its health check, then starts the TODO app. The database is stored in the `mongo_data` volume.

Run the route checks from another terminal:

```bash
python3 automationTesting.py
```

Stop the app with `Ctrl+C`, or run `docker compose down`. To remove the saved MongoDB data too, run `docker compose down --volumes`.

## Routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Show tasks in the Do, Schedule, Delegate, and Eliminate groups |
| GET | `/tasks/new` | Show the task form |
| POST | `/tasks` | Validate and save a task |
| POST | `/tasks/:id/delete` | Delete a task |
| GET | `/health` | Check that the app can reach MongoDB |

`automationTesting.py` exercises the app over HTTP, including validation, create/delete behavior, invalid IDs, and the health route. The same script runs in GitHub Actions against the Compose stack.

## GitHub Actions and Docker Hub

`.github/workflows/pbl-ci.yml` starts the app and MongoDB, runs all route checks, then publishes a Docker image on pushes to `main` or manual runs on `main` after the tests pass. Pull requests run the test job without publishing.

To enable Docker Hub publishing, add these repository secrets under **Settings → Secrets and variables → Actions**:

- `DOCKERUSERNAME` — your Docker Hub username
- `DOCKERTOKEN` — a Docker Hub access token

The image tags are `DOCKERUSERNAME/backenddevelopment-pbl:latest` and the commit SHA. If either secret is missing, the tests still run and the publish job reports that publishing was skipped.

## Manual development

Copy `.env.example` to `.env`, start MongoDB locally, then run:

```bash
npm ci
npm start
```

The container configuration uses `mongodb://mongo:27017`, where `mongo` is the Compose service name. Never commit `.env` or Docker Hub credentials.
