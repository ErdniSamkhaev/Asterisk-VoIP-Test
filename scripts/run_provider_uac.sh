#!/bin/sh
# One incoming lab DID call; finish it on the employee phone within 90 seconds.
set -eu
did="${1:-74990000010}"
case "$did" in
  7499000000[0-9]|74990000010) ;;
  *) echo "Use a lab DID from 74990000000 to 74990000010" >&2; exit 2 ;;
esac
exec sipp 127.0.0.1:5060 \
  -sf /etc/asterisk/sipp/provider-uac.xml -s "$did" \
  -i 127.0.0.1 -p 5062 -mi 127.0.0.1 -mp 6000 \
  -rtp_echo -r 1 -m 1 \
  -trace_msg -message_file "/var/log/asterisk/sipp-inbound-${did}-messages.log" \
  -trace_err -error_file "/var/log/asterisk/sipp-inbound-${did}-errors.log"
