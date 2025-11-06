docker build -t email-llm:latest .
docker run -p 8080:8080 -e OBJECT_STORE_IMPL=local -e ADAPTER_BUCKET=/adapters email-llm:latest
