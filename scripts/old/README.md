# Архивные скрипты

Эти скрипты использовались при первоначальной настройке и больше не нужны в основной работе.

## Назначение

- `install_ollama_host.sh` - установка Ollama на хост (уже установлено)
- `configure_ollama.sh` - настройка Ollama для прослушивания на 0.0.0.0
- `setup_gpu.sh` - настройка NVIDIA Container Toolkit (уже настроено)
- `start_ollama_gpu.sh` - запуск Ollama с GPU в Docker (не используется, Ollama на хосте)
- `fix_docker_*.sh` - исправления Docker/firewall (уже применены)
- `fix_ollama_ipv4.sh` - исправление IPv4 для Ollama (уже применено)
- `restart_docker.sh` - перезапуск Docker (используем `docker compose restart`)
- `daemon.json` - конфигурация Docker daemon (уже применена в `/etc/docker/daemon.json`)
- `check_ollama.sh` - проверка статуса Ollama (используем `ollama list`)

## Статус

**Архивировано**: 16 октября 2025

Скрипты оставлены для истории, но НЕ используются в текущем workflow.

