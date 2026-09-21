== dev-wave-t2797-b5-contrast/run-acceptance-gated.sh
24:  leaders=$(ps -eo args | grep '[d]ev_wave_wait.py' | grep ' acceptance' | grep -vc "$SLUG")
25:  workers=$(ps -eo args | grep -c '[r]un_tests.py')
26:  pigz=$(ps -eo comm | grep -c '^pigz$')
27:  maxl=1; maxload=60
29:  log "gate: load=$l1/$l5/$l15 leaders=$leaders workers=$workers pigz=$pigz (cond leaders<=$maxl l1<=$maxload)"
33:ok = leaders <= maxl and l1 <= maxload
38:jitter_period() { sleep $((100 + RANDOM % 41)); }
56:  recheck_wait=$((RANDOM % 46))
== dev-wave-branch-residue-cleanup/run-acceptance-gated.sh
24:  leaders=$(ps -eo args | grep '[d]ev_wave_wait.py' | grep ' acceptance' | grep -vc "$SLUG")
25:  workers=$(ps -eo args | grep -c '[r]un_tests.py')
26:  pigz=$(ps -eo comm | grep -c '^pigz$')
27:  maxl=1; maxload=60
29:  log "gate: load=$l1/$l5/$l15 leaders=$leaders workers=$workers pigz=$pigz (cond leaders<=$maxl l1<=$maxload)"
33:ok = leaders <= maxl and l1 <= maxload
38:jitter_period() { sleep $((100 + RANDOM % 41)); }
56:  recheck_wait=$((RANDOM % 46))
== dev-wave-t2817-acceptance-bottleneck-3/run-acceptance-gated.sh
4:#  門番: 他 session の受入 leader <= maxl (自 slug 除外) かつ 1 分 load <= maxload かつ pigz <= maxpigz を 100〜140 秒周期で判定。
31:  leaders=$(ps -eo args | grep -E '^(python3|[^ ]*/python3?) [^ ]*dev_wave_wait\.py acceptance' | grep -vc "$SLUG")
32:  workers=$(ps -eo args | grep -c '[r]un_tests.py')
33:  pigz=$(ps -eo comm | grep -c '^pigz$')
34:  maxl=1; maxload=60; maxpigz=2
36:  log "gate: load=$l1/$l5/$l15 leaders=$leaders workers=$workers pigz=$pigz (cond leaders<=$maxl l1<=$maxload pigz<=$maxpigz)"
37:  python3 - "$l1" "$leaders" "$maxl" "$maxload" "$pigz" "$maxpigz" <<'PY'
39:l1, leaders, maxl, maxload, pigz, maxpigz = float(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
40:ok = leaders <= maxl and l1 <= maxload and pigz <= maxpigz
45:jitter_period() { sleep $((100 + RANDOM % 41)); }
== dev-wave-t2810-g1-launch-validation/gate-acceptance-loop.sh
14:count_leaders() { ps -eo args | grep "[d]ev_wave_wait.py" | grep " acceptance" | grep -vc "$SELF"; }
23:    ok_load=$(awk -v x="$l1" 'BEGIN{print (x<=60)?1:0}')
24:    if [ "$leaders" -le 1 ] && [ "$ok_load" -eq 1 ]; then streak=$((streak+1)); else streak=0; fi
27:      sleep $(( RANDOM % 46 ))
30:      if [ "$leaders" -le 1 ]; then break; fi
34:    sleep $(( 100 + RANDOM % 41 ))
== dev-wave-t2814-cleanup-command/gate-acceptance-loop.sh
14:count_leaders() { ps -eo args | grep "[d]ev_wave_wait.py" | grep " acceptance" | grep -vc "$SELF"; }
23:    ok_load=$(awk -v x="$l1" 'BEGIN{print (x<=60)?1:0}')
24:    if [ "$leaders" -le 1 ] && [ "$ok_load" -eq 1 ]; then streak=$((streak+1)); else streak=0; fi
27:      sleep $(( RANDOM % 46 ))
30:      if [ "$leaders" -le 1 ]; then break; fi
34:    sleep $(( 100 + RANDOM % 41 ))
== dev-wave-wall-decomp/run-acceptance-gated.sh
24:  leaders=$(ps -eo args | grep '[d]ev_wave_wait.py' | grep ' acceptance' | grep -vc "$SLUG")
25:  workers=$(ps -eo args | grep -c '[r]un_tests.py')
26:  pigz=$(ps -eo comm | grep -c '^pigz$')
27:  maxl=1; maxload=60
29:  log "gate: load=$l1/$l5/$l15 leaders=$leaders workers=$workers pigz=$pigz (cond leaders<=$maxl l1<=$maxload)"
33:ok = leaders <= maxl and l1 <= maxload
38:jitter_period() { sleep $((100 + RANDOM % 41)); }
56:  recheck_wait=$((RANDOM % 46))
== dev-wave-paper-story-20260921/run-acceptance-gated.sh
4:#  門番: 他 session の受入 leader <= maxl (自 slug 除外) かつ 1 分 load <= maxload かつ pigz <= maxpigz を 100〜140 秒周期で判定。
24:  leaders=$(ps -eo args | grep -E '^python3( -u)? tools/dev_wave_wait.py acceptance' | grep -vc "$SLUG")
25:  workers=$(ps -eo args | grep -c '[r]un_tests.py')
26:  pigz=$(ps -eo comm | grep -c '^pigz$')
27:  maxl=1; maxload=60; maxpigz=2
29:  log "gate: load=$l1/$l5/$l15 leaders=$leaders workers=$workers pigz=$pigz (cond leaders<=$maxl l1<=$maxload pigz<=$maxpigz)"
30:  python3 - "$l1" "$leaders" "$maxl" "$maxload" "$pigz" "$maxpigz" <<'PY'
32:l1, leaders, maxl, maxload, pigz, maxpigz = float(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
33:ok = leaders <= maxl and l1 <= maxload and pigz <= maxpigz
38:jitter_period() { sleep $((100 + RANDOM % 41)); }
== dev-wave-paper-abstract-conclusion-ja/run-acceptance-gated.sh
25:  leaders=$(ps -eo args | grep '[d]ev_wave_wait.py' | grep ' acceptance' | grep -vc "$SLUG")
26:  maxl=1; maxload=60
32:ok = leaders <= maxl and l1 <= maxload
37:jitter_period() { sleep $((100 + RANDOM % 41)); }
55:  recheck_wait=$((RANDOM % 46))
== rulings-all-20260921/run-acceptance-gated.sh
3:#  門番 (2026-09-18 の受入調停値): 他 session の受入 leader <= 1 (自 slug 除外) かつ 1 分 load <= 60 を
22:  leaders=$(ps -eo args | grep '[d]ev_wave_wait.py' | grep ' acceptance' | grep -vc "$SLUG")
23:  workers=$(ps -eo args | grep -c '[r]un_tests.py')
28:ok = leaders <= 1 and l1 <= 60.0
41:    sleep $((100 + RANDOM % 41))
46:    sleep $((100 + RANDOM % 41))
49:  jitter=$((RANDOM % 46))
52:  recount=$(ps -eo args | grep '[d]ev_wave_wait.py' | grep ' acceptance' | grep -vc "$SLUG")
== dev-wave-t2344-closure-stage/run-acceptance-gated.sh
24:  leaders=$(ps -eo args | grep '[d]ev_wave_wait.py' | grep ' acceptance' | grep -vc "$SLUG")
25:  workers=$(ps -eo args | grep -c '[r]un_tests.py')
26:  pigz=$(ps -eo comm | grep -c '^pigz$')
27:  maxl=1; maxload=60
29:  log "gate: load=$l1/$l5/$l15 leaders=$leaders workers=$workers pigz=$pigz (cond leaders<=$maxl l1<=$maxload)"
33:ok = leaders <= maxl and l1 <= maxload
38:jitter_period() { sleep $((100 + RANDOM % 41)); }
56:  recheck_wait=$((RANDOM % 46))
== dev-wave-t2803-provenance-receipt/run-acceptance-gated.sh
24:  leaders=$(ps -eo args | grep '[d]ev_wave_wait.py' | grep ' acceptance' | grep -vc "$SLUG")
25:  workers=$(ps -eo args | grep -c '[r]un_tests.py')
26:  maxl=1; maxload=60
32:ok = leaders <= maxl and l1 <= maxload
37:jitter_period() { sleep $((100 + RANDOM % 41)); }
56:  recheck_wait=$((RANDOM % 46))
== dev-wave-t2804-provenance-timeout-contract/gate-acceptance-loop.sh
14:maxl=1; maxload=60
15:count_leaders() { ps -eo args | grep -E '^(python3|[^ ]*/python3?) [^ ]*dev_wave_wait\.py acceptance' | grep -vc "$SELF"; }
25:    ok_load=$(awk -v x="$l1" -v m="$maxload" 'BEGIN{print (x<=m)?1:0}')
27:    echo "$(date '+%H:%M:%S') attempt=$a leaders=$leaders load1=$l1 load5=$l5 ok_load=$ok_load streak=$streak maxl=$maxl maxload=$maxload" >> "$LOG"
29:      sleep $(( RANDOM % 46 ))
36:    sleep $(( 100 + RANDOM % 41 ))
== dev-wave-t2243-collection-diag/run-acceptance-gated.sh
3:#  門番: 他 session の受入 leader <= maxl (自 slug 除外) かつ 1 分 load <= maxload かつ pigz <= maxpigz を 100〜140 秒周期で判定。
25:  leaders=$(ps -eo args | grep -E '^(python3|[^ ]*/python3?) [^ ]*dev_wave_wait\.py acceptance' | grep -vc "$SLUG")
26:  workers=$(ps -eo args | grep -c '[r]un_tests.py')
27:  pigz=$(ps -eo comm | grep -c '^pigz$')
28:  maxl=1; maxload=60; maxpigz=2
30:  log "gate: load=$l1/$l5/$l15 leaders=$leaders workers=$workers pigz=$pigz (cond leaders<=$maxl l1<=$maxload pigz<=$maxpigz)"
31:  python3 - "$l1" "$leaders" "$maxl" "$maxload" "$pigz" "$maxpigz" <<'PY'
33:l1, leaders, maxl, maxload, pigz, maxpigz = float(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
34:ok = leaders <= maxl and l1 <= maxload and pigz <= maxpigz
39:jitter_period() { sleep $((100 + RANDOM % 41)); }
== dev-wave-t2807-b8-prerun/run-acceptance-gated.sh
22:  leaders=$(ps -eo args | grep '[d]ev_wave_wait.py' | grep ' acceptance' | grep -vc "$SLUG")
23:  workers=$(ps -eo args | grep -c '[r]un_tests.py')
24:  maxl=1; maxload=60
30:ok = leaders <= maxl and l1 <= maxload
35:jitter_period() { sleep $((100 + RANDOM % 41)); }
53:  recheck_wait=$((RANDOM % 46))
== dev-wave-k2-loop-originals-lost-downstream/run-acceptance-gated.sh
24:  leaders=$(ps -eo args | grep '[d]ev_wave_wait.py' | grep ' acceptance' | grep -vc "$SLUG")
25:  workers=$(ps -eo args | grep -c '[r]un_tests.py')
26:  pigz=$(ps -eo comm | grep -c '^pigz$')
27:  maxl=1; maxload=60
29:  log "gate: load=$l1/$l5/$l15 leaders=$leaders workers=$workers pigz=$pigz (cond leaders<=$maxl l1<=$maxload)"
33:ok = leaders <= maxl and l1 <= maxload
38:jitter_period() { sleep $((100 + RANDOM % 41)); }
56:  recheck_wait=$((RANDOM % 46))
== dev-wave-t2813-o26-inventory/gate-acceptance-loop.sh
14:count_leaders() { ps -eo args | grep "[d]ev_wave_wait.py" | grep " acceptance" | grep -vc "$SELF"; }
23:    ok_load=$(awk -v x="$l1" 'BEGIN{print (x<=60)?1:0}')
24:    if [ "$leaders" -le 1 ] && [ "$ok_load" -eq 1 ]; then streak=$((streak+1)); else streak=0; fi
27:      sleep $(( RANDOM % 46 ))
30:      if [ "$leaders" -le 1 ]; then break; fi
34:    sleep $(( 100 + RANDOM % 41 ))
== dev-wave-fig13-b10-waiting-grid/gate-acceptance-loop.sh
14:count_leaders() { ps -eo args | grep "[d]ev_wave_wait.py" | grep " acceptance" | grep -vc "$SELF"; }
24:    if [ "$leaders" -le 2 ] && [ "$ok_load" -eq 1 ]; then streak=$((streak+1)); else streak=0; fi
27:      sleep $(( RANDOM % 46 ))
30:      if [ "$leaders" -le 2 ]; then break; fi
34:    sleep $(( 100 + RANDOM % 41 ))
== dev-wave-paper-related-work-ja/run-acceptance-gated.sh
25:  leaders=$(ps -eo args | grep '[d]ev_wave_wait.py' | grep ' acceptance' | grep -vc "$SLUG")
26:  maxl=1; maxload=60
32:ok = leaders <= maxl and l1 <= maxload
37:jitter_period() { sleep $((100 + RANDOM % 41)); }
55:  recheck_wait=$((RANDOM % 46))
== dev-wave-paper-story-20260920b/run-acceptance-gated.sh
3:#  門番: 他 session の受入 leader <= maxl (自 slug 除外) かつ 1 分 load <= maxload かつ pigz <= maxpigz を 100〜140 秒周期で判定。
23:  leaders=$(ps -eo args | grep '[d]ev_wave_wait.py' | grep ' acceptance' | grep -vc "$SLUG")
24:  workers=$(ps -eo args | grep -c '[r]un_tests.py')
25:  pigz=$(ps -eo comm | grep -c '^pigz$')
26:  maxl=1; maxload=60; maxpigz=2
28:  log "gate: load=$l1/$l5/$l15 leaders=$leaders workers=$workers pigz=$pigz (cond leaders<=$maxl l1<=$maxload pigz<=$maxpigz)"
29:  python3 - "$l1" "$leaders" "$maxl" "$maxload" "$pigz" "$maxpigz" <<'PY'
31:l1, leaders, maxl, maxload, pigz, maxpigz = float(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
32:ok = leaders <= maxl and l1 <= maxload and pigz <= maxpigz
37:jitter_period() { sleep $((100 + RANDOM % 41)); }
== dev-wave-t2153-witness-requested-us/run-acceptance-gated.sh
24:  leaders=$(ps -eo args | grep '[d]ev_wave_wait.py' | grep ' acceptance' | grep -vc "$SLUG")
25:  workers=$(ps -eo args | grep -c '[r]un_tests.py')
26:  pigz=$(ps -eo comm | grep -c '^pigz$')
27:  maxl=1; maxload=60
29:  log "gate: load=$l1/$l5/$l15 leaders=$leaders workers=$workers pigz=$pigz (cond leaders<=$maxl l1<=$maxload)"
33:ok = leaders <= maxl and l1 <= maxload
38:jitter_period() { sleep $((100 + RANDOM % 41)); }
56:  recheck_wait=$((RANDOM % 46))
