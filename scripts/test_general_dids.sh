#!/bin/sh
# Sequential DID tests: SIPp success + exact Request-URI + Queue + answer by 3300.
# Keep 3300 registered, answer each call and finish it on that phone.
set -eu

if [ "$#" -eq 0 ]; then
  set -- 74990000001 74990000002 74990000003 \
    74990000004 74990000005 74990000006 \
    74990000007 74990000008 74990000009
fi
for did in "$@"; do
  case "$did" in
    7499000000[0-9]) ;;
    *) echo "Use general DIDs 74990000000-74990000009" >&2; exit 2 ;;
  esac
done

channel="lab-did-range.log"
capture="/var/log/asterisk/${channel}"
cleanup() {
  asterisk -rx "logger remove channel ${channel}" || true
  printf '\nRange capture: %s\n' "$capture"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

asterisk -rx "logger add channel ${channel} verbose"
test -f "$capture"

count_queue() {
  grep -Fc 'Queue(' "$capture" || true
}
count_answers() {
  grep -Ec 'PJSIP/3300[^ ]* answered PJSIP/lab-provider-' "$capture" || true
}

passed=0
failed=0
for did in "$@"; do
  queue_before=$(count_queue)
  answers_before=$(count_answers)
  message_log="/var/log/asterisk/sipp-inbound-${did}-messages.log"
  error_log="/var/log/asterisk/sipp-inbound-${did}-errors.log"
  screen_log="/var/log/asterisk/sipp-inbound-${did}-screen.log"
  printf '\nDID %s: answer 3300, then finish the call on that phone.\n' "$did"
  sip_status=0
  if sipp 127.0.0.1:5060 \
    -sf /etc/asterisk/sipp/provider-uac.xml -s "$did" \
    -i 127.0.0.1 -p 5062 -mi 127.0.0.1 -mp 6000 \
    -rtp_echo -r 1 -m 1 -nostdin \
    -trace_msg -message_file "$message_log" \
    -trace_err -error_file "$error_log" >"$screen_log" 2>&1; then
    :
  else
    sip_status=$?
  fi
  queue_after=$(count_queue)
  answers_after=$(count_answers)
  if [ "$sip_status" -eq 0 ] \
    && grep -Fq "INVITE sip:${did}@127.0.0.1:5060 SIP/2.0" "$message_log" \
    && [ "$queue_after" -gt "$queue_before" ] \
    && [ "$answers_after" -gt "$answers_before" ]; then
    passed=$((passed + 1))
    printf 'PASS %s: SIP, Request-URI, Queue, answer 3300\n' "$did"
  else
    failed=$((failed + 1))
    printf 'FAIL %s: sip=%s queue=%s->%s answer=%s->%s; see %s\n' \
      "$did" "$sip_status" "$queue_before" "$queue_after" \
      "$answers_before" "$answers_after" "$screen_log"
  fi
done
printf '\nRESULT: passed=%s failed=%s\n' "$passed" "$failed"
if [ "$failed" -gt 0 ]; then
  exit 1
fi
