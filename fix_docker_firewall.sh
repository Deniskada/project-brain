#!/bin/bash
# Исправление firewall для доступа из Docker к хосту

echo "Добавление правила iptables для доступа к Ollama..."

# Разрешить доступ из Docker bridge к порту 11434 на хосте
sudo iptables -I INPUT -i docker0 -p tcp --dport 11434 -j ACCEPT

echo ""
echo "Проверка из контейнера:"
docker exec project-brain-api curl http://172.17.0.1:11434/api/tags | head -1

echo ""
echo ""
echo "✅ Готово! Если видите JSON - firewall настроен"
echo ""
echo "Теперь протестируйте API:"
echo "curl -X POST http://localhost:8003/api/query -H \"Content-Type: application/json\" -d '{\"query\": \"Привет!\", \"project\": \"staffprobot\"}'"

