# Развёртывание стенда

Проверенная среда: Ubuntu26.04 LTS x86_64, Asterisk22.11.0 из исходников, Python3, systemd, SIPp3.7.7. Конфигурация и сценарии проверены на стенде. Независимое развёртывание всего репозитория на второй чистой машине не проводилось.

## Предварительные условия

Нужны Asterisk с chan_pjsip, res_pjsip, app_queue, res_pjsip_header_funcs, функциями dialplan и воспроизведением WAV/GSM. PJSIP_INHERITABLE_HEADER появился в ветке 22 с 22.9.0. Установка программы из исходников описана в [официальной документации Asterisk](https://docs.asterisk.org/Getting-Started/Installing-Asterisk/Installing-Asterisk-From-Source/Building-and-Installing-Asterisk/).

Пути установки должны соответствовать config/asterisk.conf и systemd/asterisk.service: бинарный файл /usr/sbin/asterisk, модули /usr/lib/asterisk/modules. Для нового сервера проверить ресурсы и действующие службы; конфигурация включает UDP5060, RTP10000–20000 и локальный AMI127.0.0.1:5038. SIPp использует локальные SIP5062 и RTP6000. Настройка NAT и сетевого экрана зависит от окружения. На проверенном VPS публичный IPv4 назначен интерфейсу напрямую; параметры внешнего адреса NAT не требовались. Это лабораторная конфигурация; реальный провайдер не подключён.

Дальнейшие команды выполняются root из корня копии репозитория на Linux. Перед заменой действующей АТС сохранить конфигурацию и рабочие данные; только резервная копия /etc не содержит AstDB и голосовых файлов:

```bash
tar -czf "/var/backups/asterisk-config-$(date -u +%Y%m%dT%H%M%SZ).tar.gz" -C /etc asterisk
```

Команда предполагает существующий /etc/asterisk; на чистой машине без этого каталога этап копирования старых настроек пропустить.

## Пользователь, каталоги и конфигурация

Если служебного пользователя ещё нет:

```bash
useradd --system --user-group --home-dir /var/lib/asterisk --no-create-home --shell /usr/sbin/nologin asterisk
```

Подготовить каталоги и установить публичные конфигурации:

```bash
install -d -o asterisk -g asterisk -m 0750 /var/lib/asterisk /var/log/asterisk /var/spool/asterisk /var/cache/asterisk
install -d -o root -g asterisk -m 0750 /etc/asterisk/local
install -m 0644 config/*.conf /etc/asterisk/
```

Если данные существовали и принадлежали root, проверить и исправить владельца только перечисленных рабочих каталогов, как описано в [operation.md](operation.md). Конфигурации и бинарные файлы остаются под управлением root. Каталог /run/asterisk создаёт systemd через RuntimeDirectory.

Endpoint/AoR КЦ и ТП уже включены в config/: повторно запускать generate_cc_phones.py, generate_tp_phones.py и generate_cc_queue.py не требуется. Они сохранены для объяснения генерации и создают файлы по абсолютным путям; режим x у генераторов телефонов предотвращает перезапись.

## Секреты — создать один раз

На новом стенде без существующих файлов:

```bash
python3 scripts/generate_phone_auth.py
python3 scripts/generate_cc_auth.py
python3 scripts/generate_tp_auth.py
python3 scripts/generate_ami_auth.py
chgrp asterisk /etc/asterisk/local/pjsip-auth.conf
chmod 0640 /etc/asterisk/local/pjsip-auth.conf
```

Первый генератор первоначально создаёт базовый файл с 600; группа и 640 нужны для чтения службой. Остальные генераторы задают группуasterisk и 640 сами. Пароли не печатаются. Существующие секреты генераторы не заменяют. pjsip.conf обязательно включает все три auth-файла; manager.conf — manager-tp.conf. Для клиентских настроек прочитать нужный пароль приватно на сервере.

## Аудио и музыка

В репозитории WAV не поставляются: приглашения воспроизводятся генератором. Нужны eSpeak NG и SoX (на стенде установлены пакетами espeak-ng и sox).

```bash
apt-get install -y python3 espeak-ng sox
python3 scripts/generate_ivr_prompts.py
python3 scripts/inspect_ivr_prompts.py
```

Генератор создаёт три custom/ivr-*.wav: mono PCM8000Hz16bit; существующие файлы не перезаписывает. Музыка класса default использует установленный набор MOH Asterisk. На стенде moh show files подтверждает пять файлов. На новом сервере отдельно обеспечить стандартные MOH-файлы и определить класс default в musiconhold.conf: пример приведён в [audio.md](audio.md).

## Службы и сценарии

```bash
install -m 0644 systemd/*.service systemd/*.timer /etc/systemd/system/
install -m 0755 scripts/sync_tp_contacts.py scripts/run_provider_uas.sh scripts/run_provider_uac.sh scripts/test_queue_headers.sh scripts/test_queue_headers_parallel.sh scripts/test_general_dids.sh /usr/local/sbin/
install -d -m 0755 /etc/asterisk/sipp
install -m 0644 sipp/*.xml /etc/asterisk/sipp/
systemd-analyze verify /etc/systemd/system/asterisk.service /etc/systemd/system/tp-sync.service /etc/systemd/system/tp-sync.timer
systemctl daemon-reload
systemctl enable --now asterisk.service
systemctl enable --now tp-sync.timer
```

Type=exec подтверждает старт процесса; готовность модулей проверять отдельно CLI. tp-sync.service — oneshot: inactive после успешного выполнения нормален; постоянно активен его таймер. AMI слушает только 127.0.0.1. Права AMI system разрешают категории действий, а не только два конкретных вызова; секрет не публикуется.

Для лабораторного провайдера установить sip-tester; на стенде проверена версия 3.7.7:

```bash
apt-get install -y sip-tester
sipp -v
```

Сценарии с портом 5062 запускать по одному: встроенный параллельный тест создаёт два вызова внутри одного процесса. SIPp не является постоянно работающей службой.

## Проверка запуска

```bash
asterisk -rx "core show version"
asterisk -rx "module show like pjsip"
asterisk -rx "module show like app_queue"
systemctl is-enabled asterisk.service tp-sync.timer
asterisk -rx "pjsip show contacts"
asterisk -rx "queue show cc"
asterisk -rx "database show tp"
```

Зарегистрировать клиентов согласно [test-phones.md](test-phones.md). Полный статус и дополнительные непроверенные случаи: [../tests/acceptance.md](../tests/acceptance.md). Перезапуск службы, восстановление контактов, автоматические обновления AstDB, очередь и ТП подтверждены; перезагрузка самого VPS не проводилась.
