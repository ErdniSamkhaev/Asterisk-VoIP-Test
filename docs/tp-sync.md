# Список зарегистрированных сотрудников ТП

## Запуск

Установить скрипт в /usr/local/sbin/sync_tp_contacts.py. Он содержит код без секретов. Для ручной проверки:

```bash
python3 /usr/local/sbin/sync_tp_contacts.py
```

Этот режим выполняет Login и PJSIPShowContacts, выводит номер ТП, Status и ExpirationTime; AstDB не изменяет. Запускать от пользователя, которому доступен локальный файл секрета: root либо asterisk при текущих правах. Исполняемый бит для запуска через python3 не требуется.

После проверки формата полей запись включается отдельно:

```bash
python3 /usr/local/sbin/sync_tp_contacts.py --write
asterisk -rx "database show tp"
```

## Алгоритм и формат AstDB

1. Прочитать AMI-секрет из /etc/asterisk/local/manager-tp.conf и подключиться к 127.0.0.1:5038.
2. Получить полный список ContactList, дождаться ContactListComplete и сверить ListItems. ActionID связывает ответы с запросом. Неполный список и ошибка AMI не публикуются.
3. Оставить endpoint 3400–3499 с ExpirationTime (Unix seconds) больше текущего времени. Статический контакт с нулевым сроком не является регистрацией. Повторяющиеся номера убрать.
4. Одним DBPut записать ключ tp/snapshot: `UNIX_TIME|3400,3401`. При отсутствии регистраций записать `UNIX_TIME|`.

Status Reachable показывает ответ на qualify, но сам по себе не определяет наличие регистрации. В список входят действующие динамические регистрации, независимо от qualify-статуса. Доступность выбранного телефона и исчезновение регистрации между обновлением и звонком следует дополнительно обрабатывать в dialplan.

Время наблюдения и список сохраняются в одном значении, чтобы dialplan не прочитал список одного обновления и время другого. При ошибке прежнее значение сохраняется; dialplan отвергает снимок старше60секунд. Истечение регистрации само по себе не переписывает AstDB: для этого настроен периодический systemd.timer. Одновременные ручные и автоматические запуски следует исключать при внедрении.

## Документация

- [PJSIPShowContacts](https://docs.asterisk.org/Asterisk_22_Documentation/API_Documentation/AMI_Actions/PJSIPShowContacts/): список контактов и завершающее событие.
- [ContactList](https://docs.asterisk.org/Asterisk_22_Documentation/API_Documentation/AMI_Events/ContactList/): Endpoint, ExpirationTime, Status.
- [DBPut](https://docs.asterisk.org/Asterisk_22_Documentation/API_Documentation/AMI_Actions/DBPut/): Family, Key, Val.
- [AMI v2 specification](https://docs.asterisk.org/Configuration/Interfaces/Asterisk-Manager-Interface-AMI/AMI-v2-Specification/): сообщения и ActionID.

## Локальная проверка кода

Семь проверок tests/test_tp_sync.py прошли на моделях ответов AMI. Запуск из корня проекта: python3 -m unittest discover -s tests -p test_tp_sync.py -v. Проверяются фильтрация, завершённость списка и отказы. Вход в реальный AMI и ручная запись AstDB затем подтверждены на VPS; автоматические обновления, снятие регистрации, возврат, два ТП и восстановление после restart проверены.

## Автоматическое обновление

Подготовленные systemd/tp-sync.service и systemd/tp-sync.timer разместить в /etc/systemd/system/ под теми же именами в нижнем регистре. Скрипт /usr/local/sbin/sync_tp_contacts.py должен быть доступен на чтение пользователю asterisk, обычно root:root 0644. Секрет остаётся root:asterisk 0640 в каталоге root:asterisk 0750.

После systemd-analyze verify обоих файлов выполнить daemon-reload и enable --now tp-sync.timer. Проверить status таймера, журнал tp-sync.service и изменение времени в database show tp. Установка файлов, verify, daemon-reload и enable --now выполнены. Предупреждения verify относятся к CPUAccounting в службах XFS. Status и журнал подтверждены: служба повторно публикует снимок с 3400, время меняется. Удаление регистрации и пустой список проверены: database show tp показал 1793170611| после отключения 3400.

OnActiveSec=1s запускает первое обновление после активации таймера. OnUnitInactiveSec=10s отсчитывает следующее от завершения сервиса; AccuracySec=1s задаёт окно планирования. Поэтому это примерно 10 секунд плюс длительность скрипта и планирование. Type=oneshot завершает сервис после одного обновления; повторно его запускает timer. Отдельные наложенные экземпляры одного сервиса systemd не создаёт. Для внеочередного обновления после внедрения использовать systemctl start tp-sync.service, чтобы не запускать параллельный процесс Python вручную.

Служба работает как asterisk:asterisk и использует AMI для записи AstDB. TimeoutStartSec=25s ограничивает зависший запуск. Логи смотреть через journalctl -u tp-sync.service. Остановка обновлений: systemctl stop tp-sync.timer; существующая запись AstDB при этом остаётся, и dialplan проверяет её возраст; поведение после остановки обновлений на70секунд проверено.

Читать: [systemd.timer](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html), параметры OnActiveSec, OnUnitInactiveSec и AccuracySec; [systemd.service](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html), Type=oneshot и TimeoutStartSec.