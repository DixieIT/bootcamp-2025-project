.PHONY: dev lint typecheck test run docker-build docker-run

dev: ## run app locally
	uvicorn app.main:app --reload --port 8081

lint:
	ruff check .

typecheck:
	mypy .

test:
	PYTHONPATH=. pytest -q

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8080

docker-build:
	docker build -t prompted-doc-processor:local -f docker/Dockerfile .

docker-run:
	docker run --rm -p 8080:8080 --env-file .env prompted-doc-processor:local