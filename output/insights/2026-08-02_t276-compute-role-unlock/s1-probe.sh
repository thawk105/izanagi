#!/bin/bash

#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=00:20:00

cd "$PBS_O_WORKDIR" || exit 1

OUT="probe-out.txt"
{
  echo "=== node ==="
  hostname
  date -Iseconds
  echo "=== proxy/CA related env key names (values shown for proxy only) ==="
  env | grep -iE '^(http_proxy|https_proxy|ftp_proxy|all_proxy|no_proxy)=' | sort
  echo "--- CA / TLS override keys (names only) ---"
  env | grep -iE '^(SSL_CERT_FILE|SSL_CERT_DIR|REQUESTS_CA_BUNDLE|CURL_CA_BUNDLE|NODE_EXTRA_CA_CERTS|NODE_TLS_REJECT_UNAUTHORIZED|SSLKEYLOGFILE)=' | sed 's/=.*/=<set>/' | sort
  echo "--- (empty above means unset) ---"
  echo "=== uppercase variants explicitly ==="
  for k in HTTP_PROXY HTTPS_PROXY NO_PROXY ALL_PROXY FTP_PROXY; do
    if [ -n "${!k+x}" ]; then echo "$k=${!k}"; else echo "$k=<unset>"; fi
  done
  echo "=== claude executable ==="
  command -v claude || echo "claude: not on PATH"
  echo "=== A: allowlist(5) + lowercase proxy 2 ==="
  ARGV_HOME="$HOME"
  timeout 240 env -i \
    PATH="$PATH" HOME="$ARGV_HOME" LANG="${LANG:-C}" LC_ALL="${LC_ALL:-C}" TERM=dumb \
    http_proxy="$http_proxy" https_proxy="$https_proxy" \
    claude -p --output-format json --setting-sources "" --disable-slash-commands \
      --no-session-persistence "Answer with the single integer only: 4817 + 2906" \
    > a.json 2> a.err
  echo "A rc=$?"
  head -c 600 a.json; echo; echo "--- a.err (head) ---"; head -c 400 a.err
  echo "=== B: allowlist(5) only (expect failure) ==="
  timeout 240 env -i \
    PATH="$PATH" HOME="$ARGV_HOME" LANG="${LANG:-C}" LC_ALL="${LC_ALL:-C}" TERM=dumb \
    claude -p --output-format json --setting-sources "" --disable-slash-commands \
      --no-session-persistence "Answer with the single integer only: 4817 + 2906" \
    > b.json 2> b.err
  echo "B rc=$?"
  head -c 600 b.json; echo; echo "--- b.err (head) ---"; head -c 400 b.err
  echo "=== done ==="
  date -Iseconds
} > "$OUT" 2>&1
