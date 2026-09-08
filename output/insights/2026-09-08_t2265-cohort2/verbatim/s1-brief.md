# 段 1 brief — [T-2265] 独立 cohort で反実仮想 ITT の主判定を確定させる

**研究前進.** B-10 の機序節が問う「制御器が選んだ一歩の向きは、直後の窓の commit 速度を変えるか」に
確認的証拠を入れる。前 2 wave は事前登録どおりに動いた結果いずれも `inconclusive` で、原因は
(1) 走り出しの `seq = 0` 窓 (v2 の位置除外で解消済み) と (2) 主層 12 run のうち 1 run に残る
`seq >= 1` の `window_commits = 0` 窓である。**完了判定:** 新 cohort の成果物に対して新解析器が
`decision` を返し、かつ `window_commits = 0` と「後続窓を持たない割当」がどちらも**構成上起きえない**
ことを実測で示すこと。判定が等価・優越・inconclusive のいずれでも事前登録どおりに報告する
(検出力不足による inconclusive は結論であって失敗ではない)。

**確定済みユーザー裁定.** D1515 の再訪条件は未充足なので上流還元に触れない。規律 1 (trace 無効 =
性能、trace 有効 = 正しさ、別ビルド別 run) と規律 2 を緩めない。仮想リスク向けの gate・検査・台帳・
一般化は scope 外。計測は計算ノードを占有し、条件を割って複数ノードへ同時投入する。着手直前の
local main (`cc9bba523`) から fresh worktree を作った。

**scope.** S1 新 cohort の事前登録 (docs、親が書く)。S2 patch C を改訂し「全割当に後続窓」と
「commit 0 の窓が出ない窓構成」を実現。S3 driver / `.pbs` の trace 契約へ新 cell 集合・新観測長を追加。
S4 cohort 2 専用解析 module (v2 の位置除外を逐語継承 + 割当列と seed の LCG 一致検査)。
S5 `plot_dynamic_backoff.py` が 12 field cell と新 event 項目を理解する。S6 cohort 2 が使う policy≠0
cell の直列性認証 (trace 無効・別 job)。S7 実測 12 job を複数ノードへ同時投入。

**不変条件.**
- `docs/backoff-counterfactual-preregistration.md` (v2、sha256 `526d9384…`) の bytes を変えない。
  cohort 1 用 `orchestrator/campaign/backoff_counterfactual_analysis.py` の受理集合・定数も変えない
  (§9「将来 cohort 用の互換層は作らない」)。
- 既存 12 成果物と cohort 1 の判定を動かさない (規律 7)。
- 新 cohort の outcome を 1 つも見る前に新事前登録を commit で凍結し、順序を commit で示す。
  生死確認で見た構造量は新事前登録の「見たものの列挙」節へ全て書く。
- 除外規則を緩めない。落としてよいのは「位置が先頭」と「後続窓なし」だけで、outcome・割当・
  clamp・trigger による除外を新設しない。
- 実測済み: F660 に当たらない (driver と `.pbs` は main 側 `tools/pegasus/admission_registry.json` に
  登録済み、登録簿は path のみを key にし内容 hash を pin しない)。patch C の sha256 を literal pin
  する箇所は無い (literal pin は patch A の `EXPECTED_PATCH_A_SHA256` だけ)。

**(P1) 事前登録は新規文書とする** — `docs/backoff-counterfactual-cohort2-preregistration.md`。v2 §7 の
位置除外と「残存 event に 0 commit が 1 件でもあれば主判定全体を inconclusive」を逐語で引き継ぐ。
**(P2) 窓構成は「必ず commit 数で閉じる」形にする** — 時間 cap を観測長以上へ上げ、全 event の
`trigger = 1`・`window_commits >= count_window > 0` を構成上保証する。新 cell 集合を 12 field で足す。
**(P3) 観測長は「extime 経過後、最初に窓が閉じた時点まで」とする** — これで最後の割当も後続窓を持ち、
末尾に短い部分窓 (commit 0 になりうる) を作らない。S2 の patch 改訂で実現する。
**(P4) patch C はその場で改訂する** — 新 patch D を足すと `_patch_stack_identity` の 3 本固定構造と
`patch_stack_sha256` が全走行で変わり、certify 系へ波及する。C の sha は file から算出されるので
literal pin を壊さない。
**(P5) 直列性認証の対象は cohort 2 が実際に使う policy≠0 cell とする** — 旧 `cw-as-dyn-p1/p2` は
未認証のまま残ることを明記する。
**(P6) 解析は cohort 2 専用 module を新設する** — cohort 1 の module を分岐で汎用化しない。

**変更面 (実アンカー).**

| # | path | 現状のアンカー | 変更 |
|---|---|---|---|
| A1 | `patches/cicada-adaptive-counterfactual.patch` | 707 行。`izanagi_backoff_trace_window_commits = committed_diff` (patch 内 439 行付近)、`trigger = committed_diff >= kCountWindow ? 1 : 2` | 最終窓 flush と窓構成の option を追加 |
| A2 | `tools/pegasus/probes/t2187_adaptive_const_probe.py` | `_validate_backoff_trace_contract` (2732)、`_artifact_contract_metadata` (2761)、`COUNTERFACTUAL_TRACE_CELLS_TEXT` (272)、`_certification_contract` (1185)、`CERT_CELLS` (242) | cohort 2 の cell 集合・観測長・事前登録 sha、certify 契約へ policy≠0 cell |
| A3 | `tools/pegasus/probes/t2187_adaptive_const_probe.pbs` | `COUNTERFACTUAL_TRACE_CELLS_RAW` (21)、cells 検査 (151)、`--extime 3` (415)、`elapstim_req=00:40:00` (5) | cohort 2 の raw cell・観測長・walltime |
| A4 | `orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py` (新規) | — | v2 規則の逐語継承 + LCG 一致検査 |
| A5 | `tools/plotting/plot_dynamic_backoff.py` | `TRACE_CELLS` (76)、cell spec 表 (87)、field 数表 (96)、`parity_branch` 検査 (474) | 12 field cell と `assigned_invert` 等の新 event 項目 |
| A6 | `orchestrator/tests/test_dynamic_backoff_transitions.py` | `PATCH_C` 構造検査 (1146/1174/1185/1202/1348)、適用可否 (731/740/750) | patch C 改訂に追随 |
| A7 | `orchestrator/tests/test_ccbench_spawn_sites.py` | driver の spawn site 行番号 pin (923/936/2688/2693/2702) | 行ずれの再導出 |
| A8 | `orchestrator/tests/test_t2187_adaptive_const_probe.py` / `test_plot_dynamic_backoff.py` / `test_condition_meaning_gate.py` | 各 exact literal 検査 | 追随 |

**成果物.** 新事前登録 docs、patch C 改訂、driver / `.pbs` 契約、cohort 2 解析 module と test、plot 拡張、
certify 契約拡張、`output/insights/2026-09-08_t2265-cohort2/` (README + verbatim + 変異台帳 +
`analysis-result.json`)、worklog / decisions / failures の spool fragment。

**並列分割.** 段 5 は所有を 3 分割する — unit A = patch C と `test_dynamic_backoff_transitions.py`、
unit B = driver `.py` / `.pbs` と関連 test (spawn site pin を含む)、unit C = cohort 2 解析 module と
plot 拡張。certify 契約拡張は unit B に含める (同一 file)。

**受入・実測環境.** 受入は `tools/dev_wave_wait.py acceptance`。実測は Pegasus gen_S (48 物理コア、
HT 無効)、機体固有の作法は `docs/pegasus-runbook.md`。12 job は seed ごとに binary が変わるため、
buildcache の claim/publish 衝突を避けて job ごとに detached submit-tree を分け、複数ノードへ同時投入
する。生死確認 (DW-G01) を事前登録の凍結**前**に 1 job だけ走らせ、見た構造量を事前登録へ列挙する。

## 段 1 の実測 (DW-G01 の最安の生死確認 / DW-O13 の到達可能性)

cohort 1 の 12 成果物 (既に完全開示済み) から構造量だけを数えた。逐語は同 job dir の
`probe-window-structure.txt` と `probe-cap-events.txt`、probe 本体は `probe_window_structure.py` /
`probe_cap_events.py` (repo 外の使い捨て)。theta / D[r] / CI / decision は計算していない。

- **`seq >= 1` の `window_commits = 0` は全 18 cell・12 run・約 155,000 event でちょうど 2 件。**
  どちらも主層 `cw-as-dyn-p2` write-heavy 48t の同一 run (seed `13467815584134101060`) の
  `seq = 10` と `seq = 11`、**2 件とも `trigger = cap`**、`window_us` はそれぞれ 10,308 / 10,279。
- **`trigger = count` の窓は定義上 `window_commits >= count_window = 10,000` で、0 になりえない。**
  0 になるのは時間 cap で閉じた窓だけである。`seq >= 1` の cap 窓は全体で 206 件
  (p1 balanced 24t が 201、p1 write-heavy 48t が 1、p2 write-heavy 48t が 4)。
- `seq = 0` の窓は起動の暖機を丸ごと含み、`window_us` が 15,000〜75,557 と定常 (p50 2,560〜10,486) の
  数倍〜30 倍で、commit 0 で cap により閉じる。v2 の位置除外はこれを落としている。
- 主層の event 数は 555〜671 (中央値 617)。job 所要は 18 run で 135.9〜138.7 秒。
- 各 run の最後の event の `window_us` は 2,560〜10,846 で、末尾の部分窓は現在捨てられている。

**(P2) の根拠が実測で固まった。** 時間 cap を観測長以上へ上げれば通常窓はすべて commit 数で閉じ、
`window_commits = 0` は**構成上**起きえなくなる。統計的な期待ではない。
**(P3) の限界も明示する。** 末尾 flush 窓だけは commit 数で閉じないので構成上の保証が及ばない。
flush 窓の commit が 0 になるのは run 終了が更新と同時刻に当たる場合だけで、実測の窓長
(p50 5,139 µs) と 1 commit あたりの時間から確率は 10^-6 の桁である。**それでも規則は緩めない** —
残存 event に 0 が 1 件でもあれば主判定は inconclusive のままとする。
