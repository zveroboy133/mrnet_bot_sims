#!/bin/bash
# Скрипт для обновления и перезапуска бота 3
# Использование: ./restart_bot3.sh

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Имя сервиса
SERVICE_NAME="pachka-bot-3.service"

echo -e "${GREEN}=== Обновление и перезапуск бота 3 ===${NC}"

# Получаем директорию скрипта
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "\n${YELLOW}[1/4] Обновление репозитория...${NC}"
if git pull origin main; then
    echo -e "${GREEN}✓ Репозиторий обновлен${NC}"
else
    echo -e "${RED}✗ Ошибка при обновлении репозитория${NC}"
    exit 1
fi

echo -e "\n${YELLOW}[2/4] Остановка сервиса ${SERVICE_NAME}...${NC}"
if sudo systemctl stop "$SERVICE_NAME"; then
    echo -e "${GREEN}✓ Сервис остановлен${NC}"
else
    echo -e "${RED}✗ Ошибка при остановке сервиса${NC}"
    exit 1
fi

# Небольшая задержка перед перезапуском
sleep 2

echo -e "\n${YELLOW}[3/4] Перезапуск сервиса ${SERVICE_NAME}...${NC}"
if sudo systemctl start "$SERVICE_NAME"; then
    echo -e "${GREEN}✓ Сервис запущен${NC}"
else
    echo -e "${RED}✗ Ошибка при запуске сервиса${NC}"
    exit 1
fi

# Небольшая задержка перед проверкой статуса
sleep 2

echo -e "\n${YELLOW}[4/4] Проверка статуса сервиса...${NC}"
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${GREEN}✓ Сервис работает${NC}"
    echo -e "\n${GREEN}=== Готово! ===${NC}"
    echo -e "\nДля просмотра логов используйте:"
    echo -e "  ${YELLOW}sudo journalctl -u ${SERVICE_NAME} -f${NC}"
else
    echo -e "${RED}✗ Сервис не запущен${NC}"
    echo -e "\nПроверьте логи:"
    echo -e "  ${YELLOW}sudo journalctl -u ${SERVICE_NAME} -n 50${NC}"
    exit 1
fi

