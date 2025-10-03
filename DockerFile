FROM python:3.11-slim
WORKDIR /app
COPY server.py /app
COPY www /app/www
EXPOSE 8080
CMD ["python", "server.py", "www"]
