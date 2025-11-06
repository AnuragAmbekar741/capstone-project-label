.PHONY: run dev test docker

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8080

dev:
	LOG_LEVEL=DEBUG uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

test:
	pytest -q

docker:
	docker build -t email-llm:latest .
