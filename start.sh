#!/bin/bash
echo "Запуск SceneEngine..."
docker compose up -d
echo "Frontend: http://localhost:5175"
echo "Backend:  http://localhost:8002"
echo "Postgres: localhost:5436"
