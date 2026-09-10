## 検査結果

### 所見 1 — P1-a の「T-2228 が 2 本目を被覆」は一般化しすぎている

**主張:** (P1-a) は不支持。T-2228 は 2 要素の一例を示す間接証拠だが、本件の 3 要素列における 2 本目を被覆したとは言えない。

**根拠 (file:line):** T-2228 の例示は `40 hex, absolute path` の順序である一方、official 最大構成は `32 hex, 32 hex, absolute path` である (`t2228_driver_gate_liveness_probe.pbs:7-12`, `submit_floor.sh:632-638`)。T-2228 は 2 本目を必須化して利用しているので、その request に限った到達証拠はある (`t2228_driver_gate_liveness_probe.pbs:100-115`)。しかし brief が挙げる request `980554.nqsv` / `980676.nqsv` の実 result は今回の射影資料に含まれず、値、投入 argv、時刻を独立検証できない (`s1-brief.md:41-46`)。

**これが放置されると成果物の何が変わるか:** 最終報告が「T-2228 で 2 本目は既証明」と過大に書かれる。値の個数、位置、名前、長さ、順序が変わった現在の構成に対する証拠強度を誤る。

**提案:** T-2228 は「2 要素の当該一例での plausibility」に格下げする。本 probe の承認あり result で 1、2、3 本目をすべて新規の直接観測として扱い、投入側 manifest に exact `-v` 文字列、argv 配列、各値の byte 長、順序を残す。`explicit_env_order` を job 側の観測値とは呼ばない。job の `os.environ` から元の `-v` 順序は復元できない。

### 所見 2 — P1-b の「承認ありの実 shell argv は観測しない」は妥当

**主張:** (P1-b) は支持する。`floor_campaign.sh` を実行して承認あり argv まで到達する方法は、本件の禁止条件と両立しない。

**根拠 (file:line):** `floor_campaign.sh` は §8 より前に外部 checkpoint directory/file を作り (`floor_campaign.sh:61-149`)、repo 内 scratch/staging を作る (`floor_campaign.sh:267-366`)。§8 は `:545-566`、依存 build は `:1002-1140`、実 driver argv の組立てはようやく `:1216-1225` である。plan 自身もこの非対称を明記している (`s2-plan.md:9-10,161-169`)。

**これが放置されると成果物の何が変わるか:** この方針を崩すと official campaign 前段が動き、repo 不変条件、稼働中 wave との非干渉、official 投入禁止を破る。

**提案:** 承認あり側は raw env 観測と現行 source への射影に限定する。ただし最終成果物では必ず「shell 分岐と shell が生成した argv の実行観測ではない」と明記する。

### 所見 3 — P1-c の 6 file 構成は概ね閉じているが、焦点検査が分類の実効性を通していない

**主張:** (P1-c) の変更 file 集合は概ね支持する。新規 `.pbs/.py` は registry、2 個の literal golden、runbook 投影表への同期が必要で、新規 test は self-run または allowlist が必要である。ただし plan の焦点検査は新 entry の login 拒否、compute 許可を直接通していない。

**根拠 (file:line):** literal golden は `test_hooks.py:3032-3525`、registry 完全一致は `:3926-3937`、再帰 execution inventory は `:4360-4386`。site bit の動的検査は `:4270-4283` にあるが、plan の焦点 command は schema と inventory だけである (`s2-plan.md:293-303`)。runbook 表は registry の機械投影である (`pegasus-runbook.md:456-484`)。`tools/pegasus/README.md` は言及した一部実行体だけの表なので、本 probe を手順として追加しない限り編集不要である (`tools/pegasus/README.md:22-35`)。

独自検索と件数は次のとおり。

```bash
rg -n --hidden -g '!.git/**' -F \
  't2228_driver_gate_liveness_probe' . | awk '...'
# HIT_COUNT=251

rg -n --hidden -g '!.git/**' \
  -e '_PEGASUS_EXPECTED_CLASSES' \
  -e '_PEGASUS_EXPECTED_ENTRIES' \
  -e 'test_bash_pegasus_execution_inventory_is_synchronized' \
  -e '_ADMISSION_PROJECTION_HEADER' \
  -e '_check_admission_projection' \
  -e 'PYTEST_ONLY_ALLOWLIST' \
  -e 'test_every_test_file_is_self_runnable_or_allowlisted' . | awk '...'
# HIT_COUNT=126

rg -n \
  -e 'admission_registry\.json' \
  -e '_PEGASUS_EXPECTED_CLASSES' \
  -e '_PEGASUS_EXPECTED_ENTRIES' \
  -e 'test_bash_pegasus_execution_inventory_is_synchronized' \
  -e '_ADMISSION_PROJECTION_HEADER' \
  -e '_check_admission_projection' \
  -e 'PYTEST_ONLY_ALLOWLIST' \
  -e 'test_every_test_file_is_self_runnable_or_allowlisted' \
  tools hooks orchestrator/tests docs/pegasus-runbook.md
# HIT_COUNT=58, FILE_COUNT=21
```

**これが放置されると成果物の何が変わるか:** file 追加による既知の閉包赤は避けられる見込みだが、「登録済みだが login で許可された」などの分類配線ミスを焦点走が見逃す。

**提案:** 6 file は維持し、焦点走へ少なくとも `test_bash_pegasus_registry_login_and_suspect_bits_are_pinned` と `test_bash_other_and_compute_keep_all_pegasus_entry_bits` を加える。第 7 の登録簿 file は現時点で必要と認めない。

### 所見 4 — P1-d の名前は衝突していないが、ambient 不在の陽性対照がない

**主張:** (P1-d) の固有名選択は支持するが、現行測定設計は不支持。job 側の absent だけでは「NQSV が継承しなかった」と「投入 shell で export されなかった」を分離できない。

**根拠 (file:line):** plan は subshell 内で `export` して直後に `qsub` するが (`s2-plan.md:106-127`)、その shell の実 env を成果物へ残さない。job 側では absent も正常とする (`s2-plan.md:137-159`)。独自検索では `T1259_NQSV_AMBIENT_SENTINEL` と `T1259_QSUB_SECOND_HEX` はともに `HIT_COUNT=0` で、repo 内衝突はない。しかし固定値 `t1259-ambient-sentinel-v1` は、投入時に実際に export されたことの証拠ではない。

**これが放置されると成果物の何が変わるか:** 両 job で absent なら、成果物は非継承と export 手順失敗を区別できない。両 result の `ok=true` だけを見て「ambient 非継承」と誤報できる。

**提案:** attempt ごとの random sentinel を生成し、各 `qsub` の直前に、同じ変数と同じ argv 配列から create-only の submission manifest を外部 evidence dir へ書く。manifest には qsub process が見た sentinel の存在、exact 値、PID、時刻、`-v` bytes を記録する。独立に値を再入力した witness ではなく、実 qsub に渡す Bash 配列と同じオブジェクトから生成する。

### 所見 5 — P1-e は CLI 本体について成立するが、「永続 state 変更なし」全体は未証明

**主張:** (P1-e) の中心、すなわち「有効な未承認 official argv は protocol loader より前に rc=2 で拒否される」は支持する。ただし process 起動全体の無副作用まで一般化するのは早い。

**根拠 (file:line):** parser は `--protocol` を `Path` にするだけ (`s8b_floor_campaign.py:8396-8413`)。`main()` は parse 後、承認 flag 不在を `:8608-8615` で拒否し、path 解決と loader は `:8617-8622` 以後である。`take_checkpoint_environment()` は private core の `:7259-7261` なので未到達である。一方、CLI gate より前に production module 群を import する (`s8b_floor_campaign.py:90-164`)。plan の検査は tracked-clean と scratch entry 差分だけである (`s2-plan.md:64-75,171-184`)。

**これが放置されると成果物の何が変わるか:** protocol/campaign state は動かなくても、import 時の予期しない file write、core dump、hang を「P1-e が保証済み」と誤認する。subprocess timeout が無いため、異常時は 10 分の allocation を使い切りうる。

**提案:** subprocess に短い timeout、scratch を `cwd`、`ulimit -c 0`、`-I -B` を付ける。前後比較は tracked 状態だけでなく untracked 集合も含める。これを満たしたうえで P1-e を「protocol loader、campaign core、repo の観測可能な content 変更なし」に限定して採用する。

### 所見 6 — scheduler log の fd 親を evidence dir とみなす設計が未実証

**主張:** plan 最大の測定上の欠陥は、`/proc/$$/fd/{1,2}` の親が `qsub -o/-e` の最終 directory だと仮定している点である。T-2228 はこの同一性を証明していない。

**根拠 (file:line):** 先行 probe は stdout/stderr fd が repo 外の live regular fileであることだけを検査し、要求された `-o/-e` pathとの一致や親 directory を返していない (`t2228_driver_gate_liveness_probe.pbs:44-71`)。runbook は stdout/stderr が「ジョブ終了後に投入時 directory へ戻る」と記す (`pegasus-runbook.md:103-106`)。これは実行中 fd が scheduler spool を指す可能性と両立する。ところが plan は fd の親を evidence dir とし、3 本目が落ちても result を残せるとする (`s2-plan.md:34,53,186-210`)。

**これが放置されると成果物の何が変わるか:** 3 本すべてが正しく届いていても fd 親不一致で false negative になりうる。逆に evidence env が落ちた場合、result を置く独立経路まで失敗し、「届かなかった」と「probe の evidence routing が壊れた」を区別できない。

**提案:** PBS stdout 自体を一次 evidence channel にする。observer は結果を識別可能な単一行として stdout に必ず出し、job 終了後に login 側が指定済み `pbs.stdout` から回収する。`result.json` は補助に格下げする。fd 親同一性を実測済み事実として扱わない。

### 所見 7 — brief の ambient リスクは sanctioned official 経路へそのまま一般化できない

**主張:** generic ambient 継承の有無は測れるが、brief の「承認束縛の前提そのものに関わる」は過大である。raw probe と sanctioned official 投入は同一経路ではない。

**根拠 (file:line):** real `submit_floor.sh` は承認引数なしなら staging 前に拒否する (`submit_floor.sh:84-87`)。承認ありでは生成 nonce を明示 `-v` に入れる (`submit_floor.sh:632-650`)。raw `qsub` で承認 env を組む経路は D926 の保証外である (`pegasus-runbook.md:1647-1650`, `verbatim-t2324-insight.md:74-85`)。plan の承認あり job は production の「最大 3 名」を模倣するだけで、`submit_floor.sh` 自身は実行しない (`s2-plan.md:131-133`)。

**これが放置されると成果物の何が変わるか:** probe が ambient 継承を検出しただけで、sanctioned wrapper の承認を bypass できる、または official qsub の全環境と同一だと誤報する。

**提案:** 最終主張を「同一 queue の raw qsub 2 request における env 到達」に限定する。sanctioned 経路について言えるのは source 上の `export_spec` 一致だけとする。実運用上の衝突まで測るなら、承認あり probe の qsub process にだけ異なる ambient approval 値を置き、明示 `-v` 値との precedence を観測する。official campaign は起動しない。

### 所見 8 — 2 job は必要だが、A/B 因果比較と paired 完了契約が成立していない

**主張:** `-v` は job 単位なので、承認 env の「qsub 時点での不在」を測るには別 request が必要である。同一 job 内の `unset` は同じ命題ではない。ただし現在の一対だけから承認条件の因果差は言えず、group completion も機械化されていない。

**根拠 (file:line):** plan は 2 個の qsub を連続して投げるが (`s2-plan.md:79-129`)、request ID の group manifest、terminal state 回収、2 result の閉集合照合を定めない。node と処置が一対一なら hostname を記録しても node 差を分離できない (`pegasus-runbook.md:1330-1346`)。複数 request は期待集合、ID、terminal state、成果物 hash を揃えて初めて完了とするのが runbook 契約である (`pegasus-runbook.md:1377-1403`)。

**これが放置されると成果物の何が変わるか:** 片方だけ成功した partial run や、ambient が片方だけ present なのに両個別 result が `ok=true` の状態を、wave 全体の green と扱える。差が出ても approval 条件、node、時刻、scheduler occasionを分離できない。

**提案:** 反復を増やして queue を圧迫する代わりに、本 wave の主張を request-specific に限定する。そのうえで外部 group manifest に両 request ID、投入順、時刻、hostname、terminal state、result hash を閉集合で記録し、一方欠落または ambient 判定不一致なら全体を `indeterminate` とする。

### 所見 9 — 稼働中 wave との非干渉確認と資源最小化が投入手順にない

**主張:** 2 job × `gen_S` × 1 node × 10 分は軽い処理内容に対して過大であり、brief の「稼働中床値 wave と競合させない」を手順が実現していない。

**根拠 (file:line):** gen_S は request ごとに 48/48 CPU の logical host、事実上 1 node を占める (`pegasus-runbook.md:45-49,1272-1278`)。runbook は投入前の `qstat -Q`、`pegasusinfo`、並行可否、walltime 適合を要求する (`pegasus-runbook.md:1583-1599`)。brief は競合禁止を不変条件にする (`s1-brief.md:23-26`) が、plan の command には queue、既存 request、他 wave の確認がない (`s2-plan.md:81-129`)。また actual subprocess に timeout がない。

**これが放置されると成果物の何が変わるか:** 2 request が別 node を同時に占有し、床値または受入走行を待たせうる。import hang などで最大 20 node-minutes を保持する。

**提案:** 投入直前に queue availability、混雑、同ユーザーの床値・受入 request を確認し、結果を外部 manifest に残す。期待実行時間を一度測れない以上、scheduler が受理する最短の安全な walltimeへ縮め、内側 subprocess timeoutをさらに短くする。静的 consult 環境では `qstat` の socket 作成が拒否されたため、現在の非干渉状態そのものは確認できていない。

### 所見 10 — 「repo へ 1 byte も書かない」の path 閉包は成立していない

**主張:** plan の列挙は controlled result path の一覧であり、全 write path の閉包ではない。とくに Git optional lock、untracked file、core、login 側 temp、強制終了時 scratch が落ちている。

**根拠 (file:line):** plan は PBS 側で tracked-clean、driver 側 Git だけ `GIT_OPTIONAL_LOCKS=0` とする (`s2-plan.md:32-36,45-46,74`)。先行 probe の shell は `git status --untracked-files=no` を使う (`t2228_driver_gate_liveness_probe.pbs:78-87`)。plan の write 一覧は scheduler log、evidence temp/final、scratchだけである (`s2-plan.md:186-210`)。`-B` は pycache を抑えるが、core dump や Git index refresh を抑えない (`s2-plan.md:182`)。subprocess の cwd も指定されていない (`s2-plan.md:64-72`)。

静的確認時点でも worktree には既存 untracked `output/insights/2026-09-07_t1259-qsub-env-delivery/s1-brief.md` があり、tracked-only 判定ではその存在も後続の untracked 増分も扱えない。

**これが放置されると成果物の何が変わるか:** probe が `ok=true` でも、repo に新規 untracked file、`.git` lock/index metadata、core が残る可能性を排除できない。SIGKILL/node failure では EXIT trap が走らず `/scr` も残る。qsub/PBS の内部 spool や `/tmp` 使用は未検証の疑いであり、「全 path はこれだけ」とは書けない。

**提案:** PBS shell の最初から `GIT_OPTIONAL_LOCKS=0` と `ulimit -c 0` を適用し、driver は scratch cwd で起動する。repo 前後比較は tracked diffだけでなく full untracked path集合も取る。login 側にも attempt 専用 `TMPDIR` を用意する。scheduler-owned spool は閉包外と明記し、scratch residue は job ID を使って事後確認する。「1 byte」の literal 保証を維持するなら、repo を read-only mount相当で実行する仕組みが必要であり、単なる `git status` では証明できない。

### 所見 11 — 未観測 4 分岐の汎用射影は scope を越えている

**主張:** actual 2 条件は unset と exact-match だけである。set-empty と mismatch を含む汎用四分岐関数とその網羅 test は、「仮想リスク向けの gate・検査・一般化を追加しない」に抵触する。

**根拠 (file:line):** scope 除外は brief に明記される (`s1-brief.md:28`)。plan は observer 内に §8 の四分岐を複製し (`s2-plan.md:55-62`)、新規 test でも unset、empty、mismatch、exact-match をすべて固定する (`s2-plan.md:282-290`)。実 job が生成するのは unset と exact-match のみ (`s2-plan.md:163-167`)。

**これが放置されると成果物の何が変わるか:** 本題の raw measurement に不要な複製ロジックと将来の drift 面が増える。実 production shell を試していないのに、probe 側の自己整合だけが強くなる。

**提案:** result は raw env 三値と source commit/hashを記録し、当該 2 観測だけに現行 source の帰結を添える。四分岐の汎用 evaluator と未観測 empty/mismatch test は削る。外部 path、create-only publish、missing env の負例は false green 防止に必要なので scope 内に残す。

### 所見 12 — probe が green でも言えない範囲を成果物契約として固定する必要がある

**主張:** 現 plan の `ok` は輸送 probe の内部成立を示すだけであり、official end-to-end の成功を示さない。

**根拠 (file:line):** plan 自身、§8 は shell 実行ではなく source への射影だと認める (`s2-plan.md:161-169`)。承認あり job では実 driver を起動しない (`s2-plan.md:64-72`)。official sanctioned 経路は `submit_floor.sh` のみであり raw qsub は保証外 (`pegasus-runbook.md:1647-1650`)。

**これが放置されると成果物の何が変わるか:** 最終 README が green を official 投入可能性、承認束縛、campaign 完走へ広げて読める。

**提案:** green でも次は言えないと明記する。

- `submit_floor.sh` が実際にその request の qsub argv を生成したこと
- probe の全 ambient env と official wrapper の qsub process env が同一であること
- `floor_campaign.sh` §8 が実行され、実 argv に flag が 1 個追加されたこと
- 承認ありの実 driver が CLI、public gate、private gateを通過すること
- official campaign が build、claim、計測、result materializeまで完走すること
- ambient 継承が全変数、全 node、全時刻、他 queueでも同じであること
- 3 要素以外の個数、別順序、別長、comma、空値、重複名にも一般化できること
- evidence overrideを付けない通常の 2-field official 構成を実測したこと
- raw qsub の観測が D926 の認証済み official 投入を構成すること
- repo および scheduler 全体に副作用が皆無であること

## 総括

**NO-GO。**

P1 の判定は、(P1-a) 不支持、(P1-b) 支持、(P1-c) 条件付き支持、(P1-d) 名前選択のみ支持して測定設計は不支持、(P1-e) CLI gate 順序は支持するが無副作用の一般化は条件付き、である。

最も重い所見は次の 3 件である。

1. ambient absent を投入側 export 忘れから分離する陽性対照がない。
2. 3 本目欠落時の evidence channel が、未実証の scheduler fd 親同一性に依存している。
3. queue 非干渉と repo 1-byte 不変条件が、現行手順では実効化されていない。

stdout を独立一次 evidence にし、投入側 manifest、paired 完了判定、queue preflight、core/Git/untracked hardeningを入れれば、本題の実測へ進める。コード編集、test、job 投入は行っていない。