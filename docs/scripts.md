# Скрипты проекта

Все серверные скрипты предназначены для Linux. Реальные секреты создаются на сервере и не входят в репозиторий. Генераторы с режимом x не заменяют существующие файлы.

| Скрипт | Назначение |
| --- | --- |
| generate_phone_auth.py | Auth для 3000/3001; параметр --output меняет путь результата |
| generate_cc_phones.py / generate_tp_phones.py | Endpoint и AoR для 3300–3399 / 3400–3499 |
| generate_cc_auth.py / generate_tp_auth.py | Случайные пароли для групп КЦ и ТП |
| generate_cc_queue.py | Очередь cc со 100 статическими участниками |
| generate_ami_auth.py | Локальная учётная запись AMI tp-sync |
| generate_ivr_prompts.py | Три русских приглашения eSpeak NG + SoX |
| inspect_ivr_prompts.py | Проверка формата и длительности WAV |
| sync_tp_contacts.py | Чтение регистраций через AMI и запись tp/snapshot с --write |
| run_provider_uas.sh | Один исходящий из АТС вызов с RTP-эхом |
| run_provider_uac.sh | Один входящий DID, по умолчанию 74990000010 |
| test_queue_headers.sh | Входящий DID 000 с временной SIP-трассой |
| test_queue_headers_parallel.sh | Два одновременных входящих вызова с разными X-Customer-ID |
| test_general_dids.sh | Последовательная проверка DID 001–009 с ответами оператора |
| prepare_parallel_headers.py | Создание отдельных параллельных копий XML и тестового shell-скрипта |

Конфигурации endpoint/AoR и очереди уже включены в config/. Повторная генерация при обычном развёртывании не требуется. prepare_parallel_headers.py также не нужен для штатной установки: готовые копии уже есть в sipp/ и scripts/.

## Синхронизация ТП

```bash
python3 /usr/local/sbin/sync_tp_contacts.py
```

Без --write выполняется только чтение: номер, qualify-статус и срок контакта. Автоматическая запись выполняется tp-sync.service через --write; для внеочередного запуска использовать systemctl start tp-sync.service, чтобы systemd не создавал параллельный экземпляр. Алгоритм и формат данных — [tp-sync.md](tp-sync.md).

## Провайдерские сценарии

Запускать по одному процессу на порту 5062, из-под пользователя с доступом к журналам:

```bash
sh /usr/local/sbin/run_provider_uas.sh
sh /usr/local/sbin/run_provider_uac.sh 74990000010
```

Это разные проверки, их не запускать одновременно. UAS ожидает исходящий вызов сотрудника; UAC инициирует входящий и ожидает завершение сотрудником в течение 90 секунд. Предварительная установка файлов описана в [setup.md](setup.md), протокол — [provider-lab.md](provider-lab.md).

## Локальные тесты AMI и фильтра

Из корня репозитория:

```bash
python3 -m unittest discover -s tests -v
```

Семь тестов не требуют работающего Asterisk. Функциональные результаты реального стенда — [матрица проверок](../tests/acceptance.md).
