#!/bin/sh
# One incoming queue call with a temporary SIP capture; run as root on the VPS.
set -eu
channel="lab-headers.log"

cleanup() {
  asterisk -rx "pjsip set logger off" || true
  asterisk -rx "logger remove channel ${channel}" || true
  printf '\nCapture: /var/log/asterisk/%s\n' "$channel"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

asterisk -rx "logger add channel ${channel} verbose"
asterisk -rx "pjsip set logger on"

sipp 127.0.0.1:5060 \
  -sf /etc/asterisk/sipp/provider-uac.xml -s 74990000000 \
  -i 127.0.0.1 -p 5062 -mi 127.0.0.1 -mp 6000 \
  -rtp_echo -r 1 -m 1 \
  -trace_msg -message_file /var/log/asterisk/sipp-inbound-74990000000-messages.log \
  -trace_err -error_file /var/log/asterisk/sipp-inbound-74990000000-errors.log
