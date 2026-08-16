---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t1112-8c-live-pilot-b
seq: 1
title: 8c live pilot が実機で S2 verify を越え bench へ到達した — numactl の閂は外れ、次の閂は exploration campaign の layer3 provenance に移った (計測 + docs、branch worktree-dev-wave-t1112-8c-live-pilot-b)
---

## 本文

**到達目標 ([T-1249]) は達成した。** 実機 9 走のうち 4 走が build → legacy verify → **S2 verify** →
bench を完走した。8c live pilot が S2 verify を越えたのはこれが初めてである。

| 走 | Request | node | verify[legacy] | verify[s2] | bench 中央値 |
|---|---|---|---|---|---|
| c | 0:914555.nqsv | bnode005 | serializable / 0 anomalies | serializable / 0 anomalies (1,728,318 commits, 483,354 aborts) | 355,591 tps (CV 2.31%) |
| e | 0:914557.nqsv | bnode035 | serializable / 0 anomalies | serializable / 0 anomalies (1,622,809 commits, 597,796 aborts) | 346,909 tps (CV 0.44%) |
| h | 0:914565.nqsv | bnode090 | serializable / 0 anomalies | serializable / 0 anomalies (1,612,588 commits, 592,620 aborts) | 348,289 tps (CV 1.09%) |
| i | 0:914566.nqsv | bnode092 | serializable / 0 anomalies | serializable / 0 anomalies (1,579,935 commits, 547,583 aborts) | 344,338 tps (CV 0.52%) |

4 走とも `[campaign] done: 1 committed / 0 aborted / 0 skipped`。走行 HEAD は `5a19b8ab`。
**pilot であり 8c の科学的主張の証拠に数えない** (`--allow-unregistered-exploratory`、
report の `claim_scope.scientific_claim` は false、eligibility は全 false)。数値は配線確認の規模
(100k records / 4 threads) で得たもので、headline 性能でも有意差でもない。

**[T-1174] の numactl 契約 gate は実機で通った。** 前回 wave (2026-08-16) の 2 走目は
`extra_correctness に numactl 必須の構成があるが numactl 未指定` で evaluate が abort し、
そこが残る唯一の閂と記録されていた。本走ではその abort が消え、S2 verify が
`fullscale_isolated=True` の pass として実行された。**解析では通ると分かっていたが、
実機で踏むまで「閂が外れた」とは書かなかった** (brief の provisional 裁定 P1)。

**perf 不在の degrade も実機で確認した。** 4 走とも campaign WAL に `"use_perf":false` が入り、
bench は perf なしで完走した。並行セッションから「`p3_autonomous_workload_trial.py` に
`use_perf_from_receipt` の結線が無いので bench 段で `perf not found` に落ちる」という指摘を
受けたが、**call chain を辿ると誤りである。** 8c は同 module で evaluate を呼ばず、
`p3_s4_loop_trigger_gating.py` → `loop.run_campaign` を経由し、`loop.py` が `do_bench` のとき
必ず preflight を 1 回走らせて `use_perf=False` を evaluate へ積む。指摘は撤回された。
file 単位の grep が call chain を跨げなかった型である。

**残る 5 走を止めたのは numactl ではなく role 出力の契約非適合だった** (auditor 2 / coder 2 /
planner 1)。すべて envelope は `subtype=success` / `stop_reason=end_turn` / `is_error=False` で、
truncation ではなく生成のばらつきである。内訳は (i) 入力の `descriptor_binding` を出力へ写して
top-level が 7 キーになった (契約は 6 キー厳格一致)、(ii) JSON を ```json フェンスで包んだ、
(iii) JSON の区切り文字を落とした。**`retry=False` なので 1 回の逸脱で 1 世代が失われる。**
契約自体は充足可能で、前回 wave の 2 走目と本 wave の 4 走は正確に適合している。
**役の中で auditor が最も長い出力 (約 3,600〜3,800 token) を返し、逸脱も auditor に多い。**

**次の閂は構造的で、確率的ではない。** bench を完走した 4 走はいずれも `report.json` を
書けずに rc=1 で終わった。`assert_campaign_layer3_chain` が
`[campaign-chain] cells[0] failure campaign remains independently admitted` で停止する。
真因は 1 段手前にあり、`layer3_report.render` が `generated_from_head` を
`git -C <campaign_dir> rev-parse HEAD` で引くのに対し、exploration campaign は
[T-422] / F98 の要求で **repo 外**に置かれるため、この lookup は必ず
`rc=128 not a git repository` で失敗する。同 campaign root で再現済み
(`Layer3ReportError: git HEAD を取得できない`)。**2 つの要求が正面から衝突しており、
8c pilot は build へ到達した瞬間に必ず report を出せない。**
排除法で確定した — `reports/` は実在し (「no reports directory」ではない)、
`layer3_report.json` は不在で (「already has a Layer-3 report」でもない)、
残る raise 経路は `Layer3ReportError` の変換だけである。4 走すべてで同じ状態を確認した。
呼び手が `generated_from_head` を渡せば `_git_head` は呼ばれない実装になっている。
本 wave は**実装しないと裁定し**、実装差分ゼロで終える (裁定どおり別 wave で扱う)。

**副産物: [T-1175] の land が実機で効いた。** 前回 wave の 2 走は
`build cell campaign has no reports directory` が完全性検査の手前で例外になり report が
残らなかったが、本 wave の 5 走では cell の `admission_decision`
(`p3-autonomous-workload-trial-cell-admission-failure/v1`) として記録され report.json が書かれた。
ただし **bench 到達走では report 自体が書かれないため、layer3 の失敗文言はどこにも永続しない。**
関門の診断が実行時 stdout の traceback だけに残る形になっている。

**計測条件。** bench 到達 4 走はすべて別ノードで、単独性を before / after の両方で記録した —
`tanab` は 7 プロセス (本 job のみ)、競合 `ycsb_*.exe` は before / after とも NONE、
loadavg は before 0.08〜0.29。従量経路の env (`ANTHROPIC_API_KEY` / `ANTHROPIC_AUTH_TOKEN` /
`ANTHROPIC_BASE_URL` / `CLAUDE_CODE_USE_BEDROCK` / `CLAUDE_CODE_USE_VERTEX`) は全走 unset で、
transport receipt の `admitted_env_keys` は `http_proxy` / `https_proxy` の 2 つだけ、
TLS trust override は source / forwarded とも空である。

**job script は 1 バイトも変えていない** ([T-1097] の保全物)。exploration root だけは走ごとに
分けた — 前回走の campaign には abort が terminal 記録されており、同じ root を使うと同一 code を
合成した走が WAL terminal skip で評価を飛ばし、numactl 修正の効果が測れなくなるためである。

## 次の一手差分

### 完了

- [T-1112] 8c A/B/C live pilot を実機へ再投入し、9 走の結果を記録した。
  remaining: none
  base: f59f3b299e3d52e6f484cf24f748649cce8d3a824e005b89b8f11de08d85f088
- [T-1249] S2 verify を越えて bench へ到達するかを実機で測り、到達を確認した。
  次の閂も同じ方式 (実機走の WAL stage) で特定した。
  remaining: none
  base: 0020b749a643676ecfbc871d0202ca23be936d73a5af4263793c69179b776200

### 新規

- {{T:layer3-head-outside-repo}} **P1・新規**: `layer3_report.render` が
  `generated_from_head` を `git -C <campaign_dir> rev-parse HEAD` で引くため、
  repo 外に置かれる exploration campaign では必ず失敗する。8c pilot が build へ到達した
  4 走すべてが `report.json` を書けずに終わった直接の原因である。呼び手が
  `generated_from_head` を渡す経路は既に実装にある。どの値を権威とするか
  (driver が走る repo の HEAD か、campaign.lock が束縛する pin か) は設計判断なので、
  敵対検証つきで裁定する。official 経路の受理集合を緩める向きへは進めない。
- {{T:role-output-conformance}} **P2・新規**: role 出力の契約非適合が 8c live pilot の
  主要な歩留まり要因である (実機 9 走中 5 走。auditor 2 / coder 2 / planner 1)。
  `retry=False` のため 1 回の生成ばらつきで 1 世代が失われる。retry を足すか
  role 契約文を締めるかは設計判断で、**parser を緩める方向 (フェンス剥がし・未知キー許容) は
  採らない** (規律 2)。判断材料として、逸脱は auditor に集中し出力長が最長である。
- {{T:scheduler-job-waiter}} **P2・新規 (段 8 自己改善候補)**: 計算ノード job (qsub) の完了を
  待つ正本の待ち手が存在しない。`tools/dev_wave_wait.py` は `acceptance` が受入専用、
  `producer` が `--pid` / `--pid-file` を必須とするが、scheduler へ投げた job には
  ローカルの producer pid が無い。runbook §7.3 は「待ち手を自分で書き起こさない ([T-740])」を
  求めているのに、実測を伴う wave は毎回 shell の待ち手を書き起こすほかない状態である
  (本 wave も 3 本書いた)。判定材料は既に確定していて (done-marker の実在と scheduler 会計
  サマリ `Ended Request Time:` の論理和、`qstat` の rc は使わない)、あとは正本へ載せるだけである。
  実装面なので別 wave で扱う。
- {{T:layer3-failure-diagnostic-lost}} **P2・新規**: bench 到達走では `report.json` が
  書かれないため、cell の `admission_decision` に入るはずの layer3 失敗文言がどこにも
  永続しない。関門の診断が実行時 stdout の traceback だけに残る。
  {{T:layer3-head-outside-repo}} を直した後も、別の layer3 失敗で同じ盲点が再発する。
