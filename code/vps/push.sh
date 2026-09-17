#!/usr/bin/env bash
#
# Выкатка перенаправителя Telegram на VPS. Запускать из Git Bash,
# из папки vps:
#
#   bash push.sh            # развернуть или обновить
#   bash push.sh --check    # только проверить, что уже работает
#   bash push.sh --down     # остановить и убрать
#
# Хост, ключ и номер бота подставь свои (или задай переменными
# окружения ESP32_HOST, ESP32_KEY, ESP32_BOT_ID). Секретов не возит:
# токен бота на сервере не хранится вообще, плата присылает его сама
# в адресе запроса.
#
set -euo pipefail

HOST="${ESP32_HOST:-user@ВАШ_IP}"
KEY="${ESP32_KEY:-$HOME/.ssh/ваш_ключ}"
REMOTE="${ESP32_REMOTE:-/home/user/esp32-tgproxy}"
PORT="${PROXY_PORT:-8099}"
BOT_ID="${ESP32_BOT_ID:-1234567890}"

MODE=up
for a in "$@"; do
  case "$a" in
    --check) MODE=check ;;
    --down)  MODE=down ;;
    -h|--help) sed -n "2,14p" "$0"; exit 0 ;;
    *) echo "неизвестный ключ: $a (см. --help)"; exit 2 ;;
  esac
done

cd "$(dirname "$0")"
SSH="ssh -i $KEY -o StrictHostKeyChecking=no"

if [ "$MODE" = down ]; then
  echo "== останавливаю"
  $SSH "$HOST" "cd $REMOTE 2>/dev/null && PROXY_PORT=$PORT docker compose -f deploy/docker-compose.yml down || echo 'нечего останавливать'"
  exit 0
fi

if [ "$MODE" = up ]; then
  # Проверяем занятость порта ДО заливки. Если он уже кем-то занят,
  # docker упадёт на старте, а старый контейнер соседа мог бы при этом
  # остаться в непонятном состоянии - лучше остановиться раньше.
  echo "== проверяю, свободен ли порт $PORT"
  if $SSH "$HOST" "ss -ltn 2>/dev/null | grep -q ':$PORT '"; then
    echo "! порт $PORT на сервере уже занят"
    echo "  выбери другой:  PROXY_PORT=8098 bash push.sh"
    exit 2
  fi

  echo "== заливаю"
  $SSH "$HOST" "mkdir -p $REMOTE/deploy && chmod 700 $REMOTE"
  scp -i "$KEY" -o StrictHostKeyChecking=no -q \
      docker-compose.yml nginx.conf "$HOST:$REMOTE/deploy/"

  echo "== поднимаю"
  $SSH "$HOST" "cd $REMOTE && PROXY_PORT=$PORT docker compose -f deploy/docker-compose.yml up -d"

  # Порт открывать не нужно. Docker публикует порты собственными правилами
  # в цепочке DOCKER-USER, которая стоит РАНЬШЕ правил ufw, - опубликованный
  # контейнером порт доступен снаружи независимо от того, что настроено
  # в ufw. Плюс sudo на этом сервере всё равно спрашивает пароль.
fi

echo
echo "== проверяю цепочку"
# Шлём заведомо НЕВЕРНЫЙ токен: нужный нам ответ - 401 от самого Telegram.
# Он доказывает, что запрос дошёл до api.telegram.org и вернулся обратно.
# Настоящий токен для этого не нужен и в проверке не участвует.
echo "-- с самого сервера:"
$SSH "$HOST" "curl -s -m 15 'http://127.0.0.1:$PORT/bot$BOT_ID:proverka/getMe' || echo '   НЕ ОТВЕТИЛ'"

echo "-- снаружи, отсюда:"
curl -s -m 15 "http://${HOST#*@}:$PORT/bot$BOT_ID:proverka/getMe" || echo "   НЕ ОТВЕТИЛ"

echo
echo "Оба ответа должны быть:  {\"ok\":false,\"error_code\":401,...}"
echo "Именно 401 - это ответ Telegram, значит запрос дошёл и вернулся."
echo "Пусто или ошибка соединения - цепочка где-то рвётся."
echo
echo "В скетче пропиши:"
echo "  #define TG_PROXY_HOST  \"${HOST#*@}\""
echo "  #define TG_PROXY_PORT  $PORT"
echo
echo "Логи: ssh -i $KEY $HOST 'docker logs -f esp32_tgproxy'"
