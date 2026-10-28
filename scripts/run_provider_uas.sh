#!/bin/sh
# One lab-provider call with RTP echo; run on the VPS after configuring Asterisk.
set -eu
exec sipp -sn uas -i 127.0.0.1 -p 5062 \
  -mi 127.0.0.1 -mp 6000 -rtp_echo -m 1 \
  -trace_msg -message_file /var/log/asterisk/sipp-outbound-messages.log \
  -trace_err -error_file /var/log/asterisk/sipp-outbound-errors.log
