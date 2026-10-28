# Подтверждение базовой загрузки PJSIP

Стенд: Asterisk 22.11.0. Результаты получены при ручной проверке на VPS. Они подтверждают загрузку модулей и конфигурации двух номеров; регистрации и звонки проверяются отдельно.

## Загруженные модули

```bash
asterisk -rx "module show like pjsip"
```

Команда вывела 51 модуль. Существенные результаты:

| Модуль | Статус |
| --- | --- |
| res_pjsip.so | Running |
| chan_pjsip.so | Running |
| res_pjsip_header_funcs.so | Running |
| res_pjsip_authenticator_digest.so | Running |
| res_pjsip_registrar.so | Running |

app_queue.so в фильтр pjsip не входит; эта проверка не подтверждает его состояние.

## Объекты номеров

```bash
asterisk -rx "pjsip show endpoints"
```

Получены два объекта:

| Endpoint / Caller ID | InAuth | AoR | MaxContact | Транспорт | Состояние |
| --- | --- | --- | --- | --- | --- |
| 3000/3000 | auth3000/3000 | 3000 | 1 | transport-udp, UDP, 0.0.0.0:5060 | Unavailable |
| 3001/3001 | auth3001/3001 | 3001 | 1 | transport-udp, UDP, 0.0.0.0:5060 | Unavailable |

Строк Contact в выводе нет. На момент проверки динамические контакты телефонов отсутствуют; наличие endpoint, auth и AoR не является подтверждением регистрации клиента.

## Последующая регистрация клиента 3000

После настройки отдельного поля Username = 3000 Zoiper показал зарегистрированный аккаунт. Проверка на АТС:

```bash
asterisk -rx "pjsip show contacts"
```

| AoR | Пользователь в URI контакта | Статус | RTT, мс |
| --- | --- | --- | --- |
| 3000 | 3000 | Avail | 250.486 |

Objects found: 1. Адрес, порт клиента и идентификаторы контакта здесь опущены. Это подтверждает регистрацию первого клиента и ответ на OPTIONS; регистрация 3001 и аудиозвонок ещё не проверены.

## Одновременная регистрация двух клиентов: F02

Повторная команда pjsip show contacts после подключения 3001:

| AoR | Пользователь в URI контакта | Статус | RTT, мс |
| --- | --- | --- | --- |
| 3000 | 3000 | Avail | 225.752 |
| 3001 | 3001 | Avail | 199.913 |

Objects found: 2. Адреса, порты и идентификаторы контактов опущены. F02 выполнен: оба клиента зарегистрированы одновременно и отвечают на qualify. Аудиозвонок ещё не проверен.

## Проверка пользователя процесса и модуля очереди

ps -C asterisk -o pid,user,group,args подтвердил USER=asterisk и GROUP=asterisk у процесса /usr/sbin/asterisk -f -C /etc/asterisk/asterisk.conf.

Команда asterisk -rx "module show like app_queue" вернула app_queue.so, True Call Queueing, Running, core и 1 modules loaded. Это подтверждает загрузку модуля. Настройка очереди и распределение звонков ещё не проверены.
