#!/usr/bin/make

include .env

install:
	cd backend/app && \
	poetry shell && \
	poetry install

run-build:
	docker compose up --build

run:
	docker compose up

stop:
	docker compose down

add-dev-migration:
	docker compose -f docker-compose.yml exec astonish_server alembic revision --autogenerate && \
	docker compose -f docker-compose.yml exec astonish_server alembic upgrade head && \
	echo "Migration added and applied."