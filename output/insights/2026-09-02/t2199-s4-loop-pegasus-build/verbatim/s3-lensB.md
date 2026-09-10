## 総括

現行 scope の実装 plan としては **採用不可**です。plan 自身が正しく見抜いたとおり、`preprocess-failed` を除いても、現行 `p3_s4_loop.py` は Pegasus contract の authorization で build 前に必ず停止します。
`config.h` 仮説は有力ですが未実測で、同じ `preprocess-failed` へ落ちる 7 条件のうち 1 条件内の一原因しか説明しません。
所有境界について、t2145 を前提条件にすること自体は越境ではありませんが、新規専用 test file は許可された「既存の登録・内容走査テスト」更新を越えています。
独自推奨は、**今 wave では投入せず、t2145 が site-aware contract 配線を land した後に Pegasus で再開**です。cygnus の過去成功は現在の限界費用も接続可能性も証明せず、既定のユーザー方針にも反します。
以下は静的検査のみです。pytest、configure、preprocess、build、qsub は実行していません。

## 所見

1.

- 種別: real
- 対象: `brief.md:32-34`, `s2-plan.md:3-6`, `orchestrator/campaign/p3_s4_loop.py:1428-1433`, `orchestrator/campaign/loop.py:377-382`, `orchestrator/campaign/execution_guard.py:129-159`
- 内容: brief の P4「env_tag と物理環境の不一致は block 理由にしない」は現行コードに反します。`linux-baremetal` authorization は Pegasus compute で一意な required Pegasus contract ではないため、build より前の authorization で拒否されます。plan の停止判断は正しいです。
- 成果物影響: job script だけでは BUILD_START、build、terminal verdict のどれにも到達できません。
- 再現・確認の手順: t2145 未反映の HEAD で preprocess を通した後、Pegasus compute 上で同 fixture CLI を実行し、`CertifiedWriterAuthorizationError` と WAL の BUILD_START 不在を保存する。

2.

- 種別: 未確認
- 対象: `s2-plan.md:22-38,53-73`, `orchestrator/campaign/condition_meaning_gate.py:1370-1399,1993-2012`
- 内容: `preprocess-failed` の literal 発火元は plan 記載どおり 3 箇所です。実条件は、compiler `--version` の起動失敗・非 0・stderr 非空、owner preprocess の起動失敗・非 0・stderr 非空、version stdout 先頭行空の計 7 条件です。`config.h` 不在は owner preprocess 非 0 の一原因にすぎません。
- 成果物影響: 仮説が外れれば Masstree を事前 build しても reason は同じままで、停止点が前進したとは言えません。
- 再現・確認の手順: wrapper 適用走で compiler version の argv・rc・stdout・stderrと、requested/control 双方の実 preprocess argv・cwd・rc・stderrを別々に保存する。`config.h: No such file` が無ければ原因を確定せず、残る 6 条件を順に照合する。

3.

- 種別: real
- 対象: `s2-plan.md:267,274`, `docs/pegasus-runbook.md:124-149`
- 内容: plan は `python3.10` の検査と直接起動だけを挙げ、孫 process 用の `python3 -> python3.10` PATH shim を落としています。runbook は raw qsub では interpreter 固定だけでは不十分とし、shim なしで 19 failure が残った実測を記録しています。
- 成果物影響: node の既定 PATH 次第で子孫 process が Python 3.9 を拾い、build・検証経路が terminal verdict 前に停止します。
- 再現・確認の手順: 計算ノードで job 冒頭と p3 起動直前に `command -v python3`, `python3 -V`, `command -v python3.10` を保存する。`$TMPDIR/bin/python3` shim の有無で同じ fixture を比較する。

4.

- 種別: real
- 対象: `s2-plan.md:266,276-277`, `docs/pegasus-runbook.md:1544-1549`
- 内容: raw `qsub` 用の `-o` / `-e` repo 外転送が plan にありません。job directive へ機体固定の絶対 path を書くことも runbook が禁じるため、README の投入手順で外部 file path を渡す必要があります。plan の終了検査は tracked status のみで、scheduler が作る untracked `.o/.e` を検出しません。
- 成果物影響: job の出力自身が worktree を汚し、後続の pinned-clean 起動を止めます。
- 再現・確認の手順: worktree を submit directory にして `-o/-e` 無しで投入し、終了後に `git status --short --untracked-files=all` と `<script>.o<ID>`, `<script>.e<ID>` の所在を確認する。

5.

- 種別: real
- 対象: `s2-plan.md:277`, `tools/check_docs.py:4598-4669,4671-4679`, `tools/pegasus/README.md:20-53`
- 内容: plan は README の site 宣言表追加しか要求していません。しかし `qsub-job-body` の全宣言 path は、site tag を先頭に置いた fenced command 内で実際の `qsub` 引数としても集合完全一致する必要があります。
- 成果物影響: registry、runbook、README 表を同期しても `tools/check_docs.py` は赤になります。
- 再現・確認の手順: synthetic diff で registry と README 表に `p3_s4_loop_build.sh` を追加し、tagged `qsub ... tools/pegasus/p3_s4_loop_build.sh` command を追加せず `tools/check_docs.py` を実行する。

6.

- 種別: real
- 対象: `brief.md:5-8,12,16`, `s2-plan.md:264-265,278`
- 内容: **scope 外。** t2145 が `p3_s4_loop.py` を直すまで現在の wave が停止する、という step 1-2 は越境ではありません。一方、新規 `orchestrator/tests/test_p3_s4_loop_pegasus_job_contract.py` は「登録に要る既存 registry・内容走査テスト」の更新ではなく、新しい 11 項目級の専用 gate です。
- 成果物影響: 許可された diff 面を越え、t2145 所有面とは別の review・保守対象を増やすため、この scope の成果物として land できません。
- 再現・確認の手順: 実装後の `git diff --name-only` を brief の許可集合と比較する。新規専用 test file を除き、既存 `test_hooks.py` など必要な投影更新だけで登録義務が満たせるか確認する。

7.

- 種別: refuted
- 対象: `s2-plan.md:196-198,260,279`, `orchestrator/tests/test_ccbench_spawn_sites.py:508-512,764-812,2581-2586`
- 内容: process API census 自体が shell を数えない、という plan の説明は正しいです。ただし同じ test file は `tools/pegasus/` を内容走査し、shell の `cmake --build --target ycsb_*` を別の build sink として検出します。計画どおり p3 CLI だけを起動し、直接 ycsb target を build しないなら発火しません。
- 成果物影響: 計画どおりなら追加登録不要ですが、job 内で ycsb を直接 build する変更へ逸脱すると受入赤になります。
- 再現・確認の手順: 完成 script に `cmake --build ... --target ycsb_silo.exe` が無いことを確認し、`test_define_sink_cross_product_has_no_unreviewed_ungated_member` を焦点実行する。

8.

- 種別: 未確認
- 対象: `s2-plan.md:278-279`, `orchestrator/tests/test_official_perf_closure.py:471-543,888-905`
- 内容: plan が焦点 suite から落としている内容走査があります。新 shell の `if` / `[[` / `case` 行に `perf` が現れると、repository-wide perf surface inventory が新規 production file を検出します。ただし計画は perf binary の直起動を禁じており、現物が無い現在は発火すると断定できません。
- 成果物影響: perf 条件分岐を job に足した場合、reviewed perf file ledger 未登録で受入赤になります。
- 再現・確認の手順: 完成 script に対して `rg -n 'perf'` を行い、該当行が条件式なら `test_outer_perf_file_and_added_guard_inventory_is_exact` を実行する。条件式が無ければ本懸念は refute できる。

9.

- 種別: real
- 対象: `s2-plan.md:274-276`, `brief.md:45-50`
- 内容: plan は terminal verdict 未到達を成功扱いしない点では正しい一方、成功した 1 回から言える範囲を exact commit、pin、value、allocation、contract generation の 1 tuple に制限していません。「評価経路が生きている」という一般化を防ぐ成果物文言が実装条件にありません。
- 成果物影響: 1 node・1 value・1 attempt の成功が、別 node、別 value、再走でも有効な一般的 liveness と誤記されます。
- 再現・確認の手順: receipt の主張文を検査し、job ID、host、boot ID、HEAD、script SHA、CCBench pin、contract generation、fixture value の全てを限定句へ含める。いずれかを変えた再走なしに一般形の文を許さない。

10.

- 種別: refuted
- 対象: `s2-plan.md:238-260,274-276`
- 内容: 「build が通った = 候補が gate を通った」と「stop reason が変わった = 成功」の誤読は、plan が terminal verdict を必須にしているため refute されます。また費用比較は iteration の到達状況だけで、Pegasus throughput を `linux-baremetal` 数値へ混ぜてはいません。
- 成果物影響: この部分は plan のままで、build-only receipt や reason-change-only receiptを成功成果物から除外できます。
- 再現・確認の手順: build 成功後に correctness gate を意図的に赤にした fixture と、authorization で停止する fixtureを用意し、両方が job の成功分類に入らないことを receipt classifier で確認する。

11.

- 種別: real
- 対象: `brief.md:29-31`, `s2-plan.md:238-244,288`, `docs/worklog.md:543-553`
- 内容: plan は親をなぞっていません。過去の cygnus 4 iteration 成功と Pegasus 6 投入失敗から、逆に cygnus を推奨しています。ただしこれは現在の限界費用比較ではなく、plan 自身も現在の cygnus 到達性を未確認としています。さらに射影された brief の P3 に「cygnus 接続手段が無い」という根拠は書かれておらず、current worklog は「到達不能は未証明、使えるが使わない」と訂正済みです。
- 成果物影響: 過去の sunk cost を将来費用と読み、既定の「新規 evidence は Pegasus」方針に反する実行場所を選ぶおそれがあります。
- 再現・確認の手順: 両環境について、現在の接続可否、同じ HEAD/pin から terminal verdict までの人手・queue 待ち・計算時間を同じ単位で記録する。それまでは費用による cygnus 推奨を確定しない。

## 次に出る阻害要因の予測

1. **別原因による同じ `preprocess-failed` の継続。**
   根拠: `config.h` 仮説が説明するのは owner preprocess 非 0 の一原因だけです。compiler version と owner preprocess の起動・rc・stderr、空 version stdout の全 7 条件が同じ code へ畳まれます。`condition_meaning_gate.py:1370-1399,1993-2012`。

2. **現行 HEAD では Pegasus authorization の拒否。**
   根拠: supply/meaning 後に `run_campaign()` が `linux-baremetal` の env 値と authorization を渡し、authorization は build より前に実行されます。Pegasus compute は一意な required contract 以外を拒否します。`p3_s4_loop.py:111-113,1428-1433`, `loop.py:372-394`, `execution_guard.py:129-159`。

3. **t2145 配線後は attestation の exact 照合。**
   根拠: required Pegasus contract は authorization 直後に calibration bytes と execution receipt を再検算します。世代、calibration SHA、実機観測のいずれかがずれれば claim 作成前に停止します。`loop.py:180-193`, `pegasus-runbook.md:762-769,778-783`。

4. **reservation と claim root の束縛。**
   根拠: single-process contract は 8 環境変数、PBS_JOBID、boot ID、deadline、事前作成済み claims directory を要求します。plan は手組みするため、qstat field、`0:` 正規化、walltime、host のどれかが次の実機依存点になります。`reservation.py:120-175,223-275`, `loop.py:198-215`, `pegasus-runbook.md:786-790,813-814`。

5. **子孫 Python または offline configure。**
   根拠: raw qsub は Python shim が必要で、build-v2 と condition gate の双方が CMake を起動します。shim 欠落、wrapper の configure 判定漏れ、3 SOURCE_DIR の注入漏れのいずれかで terminal verdict 前に止まります。`pegasus-runbook.md:146-149`, `buildcache.py:1922-2006`, `condition_meaning_gate.py:1459-1503`。

## 未確認・限界

- 前 wave の実 preprocessor stderr が無いため、`config.h` 原因は確定していません。
- t2145 が将来 land する contract 配線の具体的な bytes と引数面は未確認です。
- 新規 job script がまだ存在しないため、perf 内容走査と subprocess bytecode 系の発火有無は条件付きです。
- cygnus の現在の接続性、queue 状態、compiler 状態は実測していません。
- pytest、shell syntax、check_docs、configure、build、qsub は一切実行していません。