.PHONY: up down migrate test lint train docker-up docker-down

up:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/native-stack.ps1 start

down:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/native-stack.ps1 stop

migrate:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/native-infra.ps1 start
	cd apps/api && ../../.venv/Scripts/python -m alembic upgrade head

docker-up:
	docker compose up --build

docker-down:
	docker compose down

test:
	.venv/Scripts/python -m pytest

lint:
	.venv/Scripts/python -m ruff check apps packages ml
	cd apps/web && npm run lint && npm run typecheck

train:
	.venv/Scripts/python -m ml.train
