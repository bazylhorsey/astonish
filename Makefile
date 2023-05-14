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
