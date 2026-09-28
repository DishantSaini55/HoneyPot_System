.PHONY: up down migrate test lint train

up:
	docker compose up --build

down:
	docker compose down

migrate:
	docker compose run --rm migrate

test:
	.venv/Scripts/python -m pytest

lint:
	.venv/Scripts/python -m ruff check apps packages ml
	cd apps/web && npm run lint && npm run typecheck

train:
	.venv/Scripts/python -m ml.train
