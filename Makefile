include .env
export $(shell sed 's/=.*//' .env)

# Migrations
migrate:
	docker compose exec backend alembic revision --autogenerate -m "$(name)" 

upgrade:
	docker compose exec backend alembic upgrade head

downgrade:
	docker compose exec backend alembic downgrade -1

# Testing
test:
	docker compose exec backend pytest
