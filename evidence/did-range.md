# Проверка всех входящих DID

## Основной и специальный номера

| DID | Подтверждение |
| --- | --- |
| 74990000000 | SIPp UAC: 1 success/0 fail, слышимое эхо; журнал подтвердил Queue(cc), ответ 3300 и передачу двух X-* заголовков. См. inbound-cc.md и queue-headers.md |
| 74990000010 | SIPp UAC: 1 success/0 fail и эхо на сотруднике ТП. Выбор между двумя ТП отдельно проверен внутренней серией. См. inbound-tp.md и tp-random-series.md |

## Оставшиеся девять общих номеров

Пользователь выполнил test_general_dids.sh и прислал:

```text
PASS 74990000001: SIP, Request-URI, Queue, answer 3300
PASS 74990000002: SIP, Request-URI, Queue, answer 3300
PASS 74990000003: SIP, Request-URI, Queue, answer 3300
PASS 74990000004: SIP, Request-URI, Queue, answer 3300
PASS 74990000005: SIP, Request-URI, Queue, answer 3300
PASS 74990000006: SIP, Request-URI, Queue, answer 3300
PASS 74990000007: SIP, Request-URI, Queue, answer 3300
PASS 74990000008: SIP, Request-URI, Queue, answer 3300
PASS 74990000009: SIP, Request-URI, Queue, answer 3300
RESULT: passed=9 failed=0
Removed dynamic logger channel 'lab-did-range.log'
```

Каждый PASS требует успешного завершения SIPp, точного Request-URI в его журнале и новых строк Queue/ответа 3300 в verbose-журнале Asterisk по сравнению с состоянием перед вызовом. Вызовы последовательные; другие звонки в сценарий не входят. Это реальные провайдерские UAC-вызовы, а не проверка одного текстового шаблона dialplan.

Итог: все 11 заданных DID проверены в лабораторной схеме. Общие 000–009 доходят через IVR в очередь, специальный 010 — в ТП. Неизвестный DID вне диапазона пока отдельно не проверен. Реальная городская сеть не подключена. Capture диапазона: /var/log/asterisk/lab-did-range.log; исходные файлы журналов в Git не включены.
