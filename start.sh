#!/bin/bash
echo "Запуск инфраструктуры презентаций..."
docker compose up -d
echo "Готово! Приложение доступно на http://localhost:5174"
