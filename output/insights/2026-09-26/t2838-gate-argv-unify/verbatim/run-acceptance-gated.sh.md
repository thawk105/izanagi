# 門番雛形の逐語 (sha256 b30be0fbafe5ea9be50476becd37a102649c528272b2d9672d6cf0ca18726623)

設置先: `/work/1/SFC/tanab/dev-wave-jobs/_shared-templates/run-acceptance-gated.sh` (repo 外、D2211 項 4)。repo には .sh として置かない。
**この file は設置時点の記録であって写し元ではない。** 門番を作るときは必ず repo 外の上の 1 本を写す (雛形が後で直されても、この写しは更新されない)。

```bash
#!/bin/bash
# 受入門番の写し元 (雛形 1 本、[T-2838] D2211 項 4、2026-09-26)。受入全走 (門番 + 再投入 loop)。
# 写し方: wave の job dir へ cp し、下の JOBDIR / WT / SLUG の 3 行だけを置換する (SLUG は wave branch 名の末尾、DW-O27)。
#   leader 行・条件値 (maxl / maxload / maxpigz)・周期・再カウントは変えない (閾値の変更はユーザー裁定)。
#   条件を締める一時措置 (例: 見送り中の maxl=-1) は job dir の gate.conf (毎周回 source) で行う。緩める変更は gate.conf でもユーザー裁定。
# 出自: dev-wave-t2273-shard0-local-copy/run-acceptance-gated.sh (sha256 ae9af50d…) の 3 値とこのコメントだけを替えた。
#  門番: 他 session の受入 leader <= maxl (自 slug 除外、argv 先頭一致) かつ 1 分 load <= maxload かつ pigz <= maxpigz を 100〜140 秒周期で判定。
#        2 回連続で開いたら 0〜45 秒の乱数後に再カウントして投入。
#  取り込み: main の取り込みは dev_wave_wait.py acceptance の post-claim merge に任せる (DW-O20)。
#  停止: child-green (受領証あり) / 赤が F945 型以外 / attempt 上限 / terminal-merge。
# 引数: <TAG>。set -e は使わない。
JOBDIR=__JOBDIR__
WT=__WT__
SLUG=__SLUG__
TAG=$1
MAXTRY=3
GATE_MAX_ROUNDS=90
export IZANAGI_WAVE_LEASE_DIR=/work/1/SFC/tanab/dev-wave-jobs/land-lease
export PYTHONDONTWRITEBYTECODE=1
CHAIN="$JOBDIR/acceptance-$TAG.chain.log"
echo $$ > "$JOBDIR/acceptance-$TAG.pid"
cd "$WT" || { echo 90 > "$JOBDIR/acceptance-$TAG.done"; exit 90; }
log() { echo "$(date '+%H:%M:%S') $*" >> "$CHAIN"; }

owned=()
if [ -f "$JOBDIR/owned-paths-$TAG.txt" ]; then
  while read -r p; do [ -n "$p" ] && owned+=(--owned-path "$p"); done < "$JOBDIR/owned-paths-$TAG.txt"
fi

gate_open() {
  read -r l1 l5 l15 _ < /proc/loadavg
  leaders=$(ps -eo args | grep -E '^(python3|[^ ]*/python3?) [^ ]*dev_wave_wait\.py acceptance' | grep -vc "$SLUG")
  workers=$(ps -eo args | grep -c '[r]un_tests.py')
  pigz=$(ps -eo comm | grep -c '^pigz$')
  maxl=1; maxload=60; maxpigz=2
  if [ -f "$JOBDIR/gate.conf" ]; then . "$JOBDIR/gate.conf"; fi
  log "gate: load=$l1/$l5/$l15 leaders=$leaders workers=$workers pigz=$pigz (cond leaders<=$maxl l1<=$maxload pigz<=$maxpigz)"
  python3 - "$l1" "$leaders" "$maxl" "$maxload" "$pigz" "$maxpigz" <<'PY'
import sys
l1, leaders, maxl, maxload, pigz, maxpigz = float(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
ok = leaders <= maxl and l1 <= maxload and pigz <= maxpigz
sys.exit(0 if ok else 1)
PY
}

jitter_period() { sleep $((100 + RANDOM % 41)); }

rc=99
attempt=0
round=0
stable=0
while [ "$attempt" -lt "$MAXTRY" ] && [ "$round" -lt "$GATE_MAX_ROUNDS" ]; do
  round=$((round + 1))
  if ! gate_open; then
    stable=0
    jitter_period
    continue
  fi
  stable=$((stable + 1))
  if [ "$stable" -lt 2 ]; then
    jitter_period
    continue
  fi
  recheck_wait=$((RANDOM % 46))
  log "gate open twice -> jitter ${recheck_wait}s then recount"
  sleep "$recheck_wait"
  if ! gate_open; then
    log "gate closed at recount -> back to gate"
    stable=0
    jitter_period
    continue
  fi
  stable=0
  attempt=$((attempt + 1))
  A="$TAG-$attempt"
  MAIN=$(git rev-parse refs/heads/main)
  log "attempt $attempt: tip=$(git rev-parse HEAD) main=$MAIN"
  git rev-parse HEAD > "$JOBDIR/acceptance-$A.tip-before.txt"
  echo "$MAIN" > "$JOBDIR/acceptance-$A.main-before.txt"
  date '+%Y-%m-%dT%H:%M:%S%z' > "$JOBDIR/acceptance-$A.started.txt"
  python3 tools/dev_wave_wait.py acceptance \
    --wave "$SLUG" \
    --lease-dir /work/1/SFC/tanab/dev-wave-jobs/land-lease \
    --lease-optional \
    --receipt-file "$JOBDIR/acceptance-receipt-$A.json" \
    --log-file "$JOBDIR/acceptance-child-$A.log" \
    "${owned[@]}" \
    --max-wait-seconds 5400 \
    -- python3 tools/run_tests.py \
    > "$JOBDIR/acceptance-$A.log" 2>&1
  rc=$?
  date '+%Y-%m-%dT%H:%M:%S%z' > "$JOBDIR/acceptance-$A.finished.txt"
  git rev-parse HEAD > "$JOBDIR/acceptance-$A.tip-after.txt"
  log "attempt $attempt: rc=$rc tip-after=$(git rev-parse HEAD)"
  if [ "$rc" -eq 0 ] && [ -f "$JOBDIR/acceptance-receipt-$A.json" ]; then
    log "child-green with receipt -> stop"
    cp "$JOBDIR/acceptance-receipt-$A.json" "$JOBDIR/acceptance-receipt-$TAG-green.json"
    break
  fi
  if [ ! -f "$JOBDIR/acceptance-child-$A.log" ]; then
    if grep -q "terminal-merge" "$JOBDIR/acceptance-$A.log"; then
      log "terminal-merge (post-claim merge の実 conflict) -> stop for parent merge"
      break
    fi
    if grep -q "terminal-postcheck" "$JOBDIR/acceptance-$A.log"; then
      log "postcheck race -> back to gate"
      continue
    fi
    if [ "$rc" -eq 70 ]; then
      log "no child log and rc=70 -> back to gate (resubmit)"
      continue
    fi
    log "no child log and not postcheck -> stop"
    break
  fi
  ROOT=$(grep -o '"session_root":"[^"]*"' "$JOBDIR/acceptance-child-$A.log" | head -1 | cut -d'"' -f4)
  total=0; f945=0
  if [ -n "$ROOT" ]; then
    total=$(cat "$ROOT"/shard-*/junit.xml 2>/dev/null | grep -ao '<failure message="\|<error message="' | wc -l)
    f945=$(cat "$ROOT"/shard-*/junit.xml 2>/dev/null | grep -ao '<error message="failed on setup with &quot;subprocess.TimeoutExpired\|<error message="failed on setup with &quot;RuntimeError: real-repo lock deadline exceeded' | wc -l)
  fi
  log "reds: total=$total f945_setup_timeout=$f945 session_root=$ROOT"
  if [ "$total" -gt 0 ] && [ "$total" -eq "$f945" ]; then
    log "all reds are F945 setup timeouts -> back to gate"
    continue
  fi
  log "reds not all F945 -> stop for adjudication"
  break
done
echo "$rc" > "$JOBDIR/acceptance-$TAG.done"
exit "$rc"
```
