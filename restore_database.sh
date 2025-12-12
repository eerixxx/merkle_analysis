#!/bin/bash

# Скрипт для восстановления базы данных из дампа

echo "Запуск контейнера базы данных..."
docker-compose up -d db

echo "Ожидание готовности базы данных..."
sleep 10

echo "Восстановление базы данных из дампа..."
docker-compose exec -T db psql -U postgres -d hierarchy_db < database_dump.sql

echo "База данных восстановлена!"
