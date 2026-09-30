# silo-function-policy 軸の生成器対照の本走 — 事前登録を発効させ、4 arm × 12 系列を回し、登録どおりの判定を出す (2026-09-30〜、[T-2867])

- 位置づけ: 事前登録 `docs/silo-policy-generator-contrast-preregistration.md` (以下「本書」) の本走の一次記録。発効の決定は本 wave の decisions fragment
  (`docs/spool/decisions/2026-09-30-dev-wave-t2867-contrast-run-1.md`、fold 後は decisions.md の「生成器対照 … を 4 arm × n = 12 で発効させ」の項)。実装と生死確認は `output/insights/2026-09-29/t2867-silo-policy-contrast-impl/README.md`。
  本 insight は記録で、可変状態の正本 (worklog 末尾・`docs/phase3.md`) にはしない。
- wave: branch `worktree-dev-wave-t2867-contrast-run`、起点 local main `4f412c67b` (2026-09-30 12:1x JST に開始 gate rc=0)。軽量版 (段 2・3 省略、段 5 実装子 2 本、段 6 review 1 本・焦点再レビュー 1 本)。
- 逐語 (`verbatim/`): 依頼 `request-md_11.md`・`request-common-4.md`、段 4 裁定 `s4-ruling.md`・`s4-ruling-2-driver-fix.md`、段 6 裁定 `s6-ruling-1.md`・`s6-ruling-2.md`、
  Codex の報告 `codex-*.md`、駆動 loop の本文 `contrast-runner.md` と試験 `contrast-runner-test.md`、本走の config `config-v1.json`。
- 台帳・evidence・LLM の round・loop の状態は repo の外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/` (本走は `v1/`、前走は `preflight/`・`preflight2/`)、
  trace の保全は `/work/1/SFC/tanab/izanagi-repro-archive/t2867-contrast-v1/` (前走は `…-preflight-20260930/`・`…-preflight2-20260930/`)。

## 0. 要約

1. **結果:** 4 arm × 12 系列を登録どおり完走し (51 項目すべて `b-complete`、欠測・fallback・anomaly 0)、report の判定は **4 比較とも「同等 (観測差が比較 floor 内)」**。
   どの LLM 構成も、登録した条件付き優越 (族ごとに Holm 補正後に有意、かつ median(d) > δ = 0.0296) を満たさなかった。本書の失敗条件 (c) の成立で、正当な negative の結末として報告する。
   族 B (LLM×C++ 対 非 LLM) の raw p は 0.042・0.045 で最も小さいが、Holm の初段 0.025 に届かず、median(d) も 0.011〜0.018 で δ 以下。
2. **arm の姿:** score の median はどの arm も約 3.93 M tps (静的 10 µs 比 約 0.99、stock 比 約 2.9)。観測した 12 系列の最大値は LLM の 2 arm (静的 10 µs 比 1.06〜1.11) が非 LLM の 2 arm より大きいが、
   最大値どうしは登録した比較ではなく、登録した 4 比較の median(d) はいずれも floor 内だった。
   endpoint が初期点のままだった系列は random 10/12・LLM×IR 7/12・LLM×C++ 5/12・進化 3/12。
3. **公平性の目視:** 本文の目視では、特定の worker を恒常的に駐車させる明示的な構造は見つからなかった (実走の偏り・飢餓は観測点が無く未計測)。上限のある偏りの懸念 (中 3 本) は LLM の arm にだけ出た。
4. **本走の前に見つけて直した欠陥 2 件:** 静的 10 µs の参照 slot で condition gate が落ちる driver の欠陥 (commit `1da88472b`)、駆動 loop の再起動が拒否される欠陥 (fix 2)。どちらも v1 の外の前走で見つけた。
5. **費用:** 計算 579 job・63.5 node 時間 (見積り 61〜70 の範囲)、LLM 249 機会 (直列 45.1 時間、同時 4 親で暦 約 16 時間、うち 429 の保留 1 回 47 分と利用上限の一旦停止 2.4 時間)。

## 1. 依頼と裁定

- 依頼 (`verbatim/request-md_11.md`): 本書 §12 の発効束を生死確認の実測で埋めて日付付きの決定にする、本走の最初の単位で未実走部品 (score job・参照 job・進化×IR) を確かめる、
  48 系列を別ノードへ割って投げる (LLM 親は同時 4、LLM の待ちは login、429 は保留)、系列が揃ったら report を実台帳で 1 通し回す。
- 上位の裁定: D2305 項 1 (4 arm × n = 12、計算確認済み 約 61〜70 node 時間・契約上限 183、CCBench の pin は C `68106660` に固定、Silo の修正を待たない)、D2216 (LLM 親 4)、D2258 項 1・2。
- 段 4 の親の裁定 (`verbatim/s4-ruling.md`): (P1) 未実走部品は v1 の外の試験版 cohort で先に確かめる (台帳が checkout の HEAD を束縛するので、v1 の走行中の欠陥は直せず欠測になる)。
  (P2) 48 系列 + 参照 3 本を回す駆動 loop は repo の外に置き Codex author が書く (起動器・親を呼ぶだけで台帳・driver に書かない)。(P3) submit checkout 16 本、系列同時 16・LLM 親 4、組を r 順・組内はラテン方格順。

## 2. 駆動 loop (段 5・6)

- 実装子 x (Codex author) が `contrast_runner.py` と自己試験を書いた (段 5、`verbatim/codex-author-x.md`)。親が全文を読み、計算ノードで自己試験 7/7 (request 37754)。
- 段 6 review 1 本 (`verbatim/codex-review-1.md`、NO-GO・must-fix 4): 二重起動の排他、親起動・submit・init と state 保存の窓、qstat の遅延表示を終了と誤認、停止後の init。
  裁定 1 (`verbatim/s6-ruling-1.md`) で 5 件を fix 1 へ (flock、起動前の intent 記録と再起動時の attention、不在は 120 秒経過かつ連続 2 回で確定、init 前の停止確認)。
  焦点再レビュー 1 (`verbatim/codex-focus-1.md`) の新 2 件は裁定 2 (`verbatim/s6-ruling-2.md`) で nit として閉じた (結果の値・受理集合を変えない)。
- 実機で見つけた欠陥 (fix 2): 前走の loop を SIGTERM で止めて修正版で再起動したら `state schedule differs from config` で起動しなかった。state は key を辞書順で書くのに、
  照合が schedule の並びとの一致を要求していた (自己試験の再起動試験は schedule が辞書順だった)。集合の比較に直し、辞書順でない schedule の再起動試験を足した。自己試験 13/13 (request 37799)。
- 実機で確かめたこと: SIGTERM での停止 (走行中の job を殺さない)、修正版での再起動と走行中 job の引き継ぎ、2 本目の loop の lock による拒否 (`runner already running`、rc=2)。
- 本走で使った版: SHA-256 `d12eb6cd32bdb14a22abafb47d9ac112a5e2f3f588ff3d7dafd16b44f31b12f2` (`verbatim/contrast-runner.md`)。

## 3. 前走 (試験版 cohort、本書 §10 の未実走部品)

版文字列は試験版 `silo-policy-contrast-test-2026-09-29` (v1 の preimage は引いていない)。

| 系列 | HEAD | 結果 |
|---|---|---|
| reference-1 (c01、request 37757) | `4f412c67b` | stock 5 slot は certified・品質正常 (1.358〜1.369 M tps)。静的 10 µs の 1 slot 目で condition gate が `config.h: No such file or directory` → driver rc=1、slot は dead-job (Elapse 878 s) |
| reference-2 (c01、request 37880) | `1da88472b` (修正後) | 10 slot すべて certified・品質正常 (stock 1.355〜1.373 M、静的 10 µs 3.998〜4.028 M)、Elapse 2,135 s、`b-complete` |
| evo-ir-1 (c02、37758 ほか) | `4f412c67b` | job 1 (stock 1.349 M、初期点 3.860 M・3.877 M)、原提案 10 回すべて preview を通過し評価 10 回すべて certified・品質正常 (0.864〜3.993 M)、endpoint = eval-4、score 5 session 3.958〜3.974 M (Elapse 1,207 s)、`b-complete` |

- driver の欠陥 (段 4 追加裁定 2、`verbatim/s4-ruling-2-driver-fix.md`): 方策 driver の静的 10 µs 経路 (`run_stock_control` の `fixed10`) が condition gate を
  offline 供給の configure 引数なしで呼んでいた。本流 `p3_s4_loop` と同じく receipt があるときだけ `_condition_gate_offline_configure_args` の射影を渡す最小修正を
  Codex author (子 y、`verbatim/codex-author-y.md`) が書き、commit `1da88472b` とした。焦点走 731 passed (request 37868)、変異 2 件 (M1 = 引数を渡さない、M2 = receipt 無しでも射影を呼ぶ) は
  baseline PASSED・2/2 KILLED で期待 node と完全一致 (request 37909)。進化×IR の前走は修正前の HEAD のまま完走させた (修正は静的 10 µs の経路だけで、評価と score の経路は変わらない)。
- 見積りとの照合: 参照 job 2,135 s は草稿 §11.0 の換算 (1 本 2,088〜2,398 s) の範囲、score job 1,207 s も換算 (1,163〜1,360 s) の範囲。

## 4. 本走の構成

- 対象 commit `1da88472b` (= local main `4f412c67b` + driver の最小修正 1 commit)。submit checkout 16 本 (`trees/c01`〜`c16`、AI worktree 容器の外、detach・submodule・hydrate・lock) すべてこの HEAD。
- 版文字列 `silo-policy-generator-contrast-v1`、cohort `silo-policy-contrast-v1`、PIN `6810666`。walltime: job 1 1,800 s、評価 900 s、score 2,700 s、参照 3,600 s。
- schedule (`verbatim/config-v1.json`): 参照 1 → 組 1〜4 → 参照 2 → 組 5〜8 → 参照 3 → 組 9〜12。組 r の順は (LLM×C++・LLM×IR・random×IR・進化×IR) を (r − 1) mod 4 左へ巡回。
- 2026-09-30 14:35:55 JST に loop を起動。参照 1 と組 1〜4 の 15 系列 (上限 16) を開き、最初の 16 job を 38070〜38085 として投入した。

## 5. 投入の一覧・経過

- 期間: 2026-09-30 14:35:55 JST 起動 → 2026-10-01 06:48:50 JST に loop が `done.json` を書いて rc=0 で終了 (約 16.2 時間)。
  うち 10/1 00:47〜03:11 JST は、利用上限の一旦停止の指示 (land 調整役の中継) で loop に pause file を置き、新しい LLM 親・job を止めた (走行中は完走)。
- 終了: 51 項目 (48 系列 + 参照 3) すべて `b-complete`。attention 0 (dead-job・rc≠0・二重投入なし)。全 48 系列が B = 10 を使い切り (A の枯渇での終了なし)。
- 計算 job (Elapse は各 job の scheduler 記録、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/v1/evidence/*/*/job.stderr`):

| 種別 | 本数 | Elapse (s) | 平均 (s) | 合計 (node h) |
|---|---:|---|---:|---:|
| job 1 (系列開始 stock + 初期点 2) | 48 | 700〜754 | 722 | 9.63 |
| 評価 | 480 | 188〜326 | 266 | 35.51 |
| score (5 session) | 48 | 1,184〜1,283 | — | 約 16.6 |
| 参照 (stock 5 + 静的 10 µs 5) | 3 | 2,133〜2,195 | 2,160 | 1.80 |
| **計** | **579** | | | **63.53** |

  承認の見積り (約 61〜70 node 時間、D2305 項 1) の範囲。前走 (試験版) と試験の計算は別に約 3 node 時間。
- slot の結果: 894 件すべて certified・品質正常 (anomaly 0、品質欠測 0、機械故障 0)。判定器の版 (`campaign_verifier_epoch`) を記録しているのは候補と初期点の 576 件 (初期点 96 + 評価 480) で、
  すべて `E1:aec05476f07c426820098705d96c70835de5be21be0aa812a6326d9ead3a512c`。残る 318 件 (系列開始 stock 48・score 240・参照 30) の slot 結果はこの field を持たず、版は照合していない。
- LLM の親: 249 機会 (LLM×C++ 121・LLM×IR 128)、すべて rc=0 (proposed 240・rejected 9)。1 機会の所要は中央値 545 s、90% 点 754 s、最長 4,326 s (429 の保留を含む)、直列の合計 45.1 時間。
- 429 (利用上限) の保留: 16 件 = 4 機会 × 各 4 回 (llm-cpp-6 a5・llm-ir-5 a8・llm-ir-8 a2・llm-cpp-7 a4、2026-09-30 20:10〜20:57 JST)。本書 §5.5 のとおり同じ a で 15 分おきに再開し、A・B を消費せず欠測にもならなかった。
  親の起動は計 265 回で、429 を返した起動は 17 回。16 回は上の保留、残る 1 回 (llm-cpp-5 a8、20:11:02 JST) は finalize が台帳に `proposed` を書いた 1 秒後に親の最終応答が 429 になったもので、
  親は台帳の終端を先に読んで `proposed` のまま終えた (結果への影響なし)。model を使った 252 回の `modelUsage` はすべて `claude-opus-5-5` だけ (残る 13 回は 429 で使用記録なし)。
- 原提案の拒否 (A だけ消費): LLM×C++ 1 (単独 TU compile の時間切れ)、LLM×IR 8 (coder の schema 5、auditor の schema 1、compile 2)、random×IR 18 (compile error)、進化×IR 0。
- 一意な評価候補 (arm 内の source digest): LLM×C++ 120/120、random×IR 120/120、LLM×IR 117/120、進化×IR 110/120。

## 6. report の結果

`orchestrator/campaign/silo_policy_contrast_report.py --ledger-root <v1/ledgers> --n 12` を本走と同じ HEAD の checkout (`trees/c01`、`1da88472b`) から 2026-10-01 06:49 JST に 1 回通した (rc=0)。
出力は `report-v1.json` (SHA-256 `0e0fae69117981a46d2d91557b9dea908b5f8994f39394273891c3f9036346f1`)。endpoint の本文は `endpoints-v1.json`。

- floor: 参照 job の stock 15 session の CV = 0.69% (batch 別 0.91%・0.60%・0.66%)。等価域 f = max(0.03, CV) = 0.03、δ = ln 1.03 = 0.0296。
  精度 gate (endpoint の 5 session の CV > 2f = 0.06 で精度不足) に当たった対は無い (4 比較とも判定が §7.4 の手順 4 を越えて手順 6 まで進んだ。記述の LLM×C++ 対 LLM×IR の endpoint CV は 0.29〜1.04%)。
- 欠測・fallback・anomaly の波及: すべて 0 (certified endpoint 数は 4 arm とも 12/12)。本書 §7.4 の手順 1〜4 (規約不適合・判定不能・生成不成立・対不足) には当たらない。
- 4 比較 (族ごとに Holm、family-wise α = 0.05、初段 0.025):

| 族 | 比較 (X 対 Y) | median d | raw p | Holm 補正 p | d > 0 の対 | 判定 |
|---|---|---:|---:|---:|---:|---|
| A | LLM×IR 対 random×IR | 0.0070 | 0.0872 | 0.1743 | 8/12 | 同等 (floor 内) |
| A | LLM×IR 対 進化×IR | 0.0017 | 0.1294 | 0.1743 | 7/12 | 同等 (floor 内) |
| B | LLM×C++ 対 random×IR | 0.0177 | 0.0422 | 0.0845 | 8/12 | 同等 (floor 内) |
| B | LLM×C++ 対 進化×IR | 0.0113 | 0.0454 | 0.0845 | 8/12 | 同等 (floor 内) |

  **どの LLM 構成も条件付き優越を満たさない** (族 A・B とも初段の raw p が 0.025 を超え、median d も δ 以下)。4 比較とも本書 §7.4 の手順 6 = 失敗条件 (c) の成立
  「観測差が比較 floor 内だった」(母集団の等価性の証明ではない)。記述: LLM×C++ 対 LLM×IR の median d = −0.0034。
- arm ごとの記述:

| arm | score の median (tps) | 範囲 | 静的 10 µs 比 (median) | endpoint が初期点 | 探索点が初期点を超えた系列 | A の使用 |
|---|---:|---|---:|---:|---:|---:|
| LLM×C++ | 3,929,440 | 3,850,979〜4,212,496 | 0.992 | 5/12 | 7/12 | 121 |
| LLM×IR | 3,931,966 | 3,852,206〜4,403,973 | 0.993 | 7/12 | 5/12 | 128 |
| random×IR | 3,938,571 | 3,855,501〜3,956,505 | 0.994 | 10/12 | 2/12 | 138 |
| 進化×IR | 3,934,752 | 3,849,903〜4,019,139 | 0.993 | 3/12 | 9/12 | 120 |

  stock (適応 backoff) 比はどの arm も約 2.8〜3.2 倍。既知最良の静的 10 µs (元の適用方法、参照 job の median 約 3.96 M tps) にはどの arm の median も届かず約 0.99 倍。
  観測した 12 系列の最大値は、LLM×IR が 4.40 M (静的 10 µs 比 1.112)、LLM×C++ が 4.21 M (1.063)、進化×IR が 4.02 M、random×IR が 3.96 M。
  最大値どうしの大小は登録した比較ではなく、生成器の優越を意味しない。登録した 4 比較の対差の中央値 median(d) は、いずれも floor 内だった
  (個々の対差には |d| > δ の対が表の順に 2/12・3/12・5/12・5/12 ある。例: LLM×IR 対 random×IR の r = 11 は d = 0.118)。

### 6.1 公平性の目視 (本書 §6 末尾)

score の確定後・報告の前に role `auditor` が 48 本の endpoint 本文を目視した (逐語 `verbatim/auditor-fairness.md`)。所見は score・判定・系列を変えない。
- 本文の目視では、特定の worker を恒常的に優先・駐車させる明示的な構造は 48 本とも見つからなかった (API は thread 番号を渡さず、状態は thread_local で全 worker に同じ規則)。
  これは構造の目視であり、実走の偏り・飢餓は未計測。
- 上限のある一時的な偏りの懸念が 2 型: 連続 abort で待ちを伸ばし commit で戻す型 (勝った worker が勝ち続けやすい)、lock 競合で待ち 0 の再試行を続ける型 (backoff を実質切る、prefix lock を握ったまま周回)。
  重さ「中」は llm-ir-3・llm-ir-2・llm-ir-11 の 3 本、「低〜中」は llm-cpp-10、「低」は llm-cpp-1・6・7・12、llm-ir-4・7。abort 後の待ちの最大は約 64 µs、lock 再試行の待ちは全員 0 µs。
- arm の傾向: random×IR と進化×IR の endpoint は対称な定数 backoff の範囲に留まり懸念なし。LLM の 2 arm は状態を持つ適応型へ動き、懸念はそこに集まる (LLM×IR は乱数なし・長い再試行に寄る)。
- 分からないこと: worker ごとの commit・abort の観測点が無く、偏りが実走で起きたかは判定できない。
- **親の射影の誤り:** 目視に渡した `endpoints-v1.json` に探索時の性能値 (`search_tps`) を入れていた。auditor は「所見は本文の構造だけから出した」と明記したが、入力の隔離としては誤りで、次からは性能値を除いた射影で渡す。

## 7. 限界

- **job の長さ (2026-09-30 19:5x のユーザー指示との関係):** ユーザーは「計算 job は 1 本 5 分を目安に分割して多数を並行に投げる」と指示した (land 調整役と md_11 の作成元が中継、common-4 §4)。
  本走の評価 job は 1 本 4〜5 分で目安どおりだが、job 1 (約 12 分: 系列開始 stock + 初期点 2)、score (約 20 分: 5 session)、参照 (約 35 分: stock 5 + 静的 10 µs 5) は長い。
  これらは本書 §5.6 が全 arm 共通の単位として固定したもので、stock と初期点・静的 10 µs を同じ job (同じノード) に置くのは同時刻の対照のためである。
  分割すると処置とノードが 1 対 1 になり (同じ指示が禁じる形)、発効後・走行中に単位を変えると系列間で揃わない。中継の指示どおり登録を優先し、本走はこの単位で完走させた。
  次の登録 (母集団型の探索 [T-2892] など) では、同時刻対照を保ったまま 5 分に収まる単位 (例: 対照 1 + 候補 1 の job を多数) を設計の段で検討する。

- 主張の範囲 (本書 §1.2・§13): write-heavy の較正動作点だけ。評価数の上限 (B = 10) を揃えた比較で、時間・費用を揃えた比較ではない (LLM は 1 機会 9 分前後の待ちを持つ)。
  結論は「登録した独立性の仮定の下で」であり、対差の独立性と符号対称性は検定していない。族 B の差は表現 (policy-C++ v1 と IR) と探索法を合わせた差。
  random と進化の支持集合は定数の分布で狭められている。段階 D の二値と射程文、auditor は LLM の arm にだけ掛かる。
- certified の射程: 観測した有限の trace の判定であり、verify と perf で同じ分岐を踏んだとは言えない。
- numactl: 本書 §5.2 は「性能構成 verify と bench は numactl interleave」と書くが、Pegasus の環境契約は numactl が空で、bench は prefix なしで走った
  (WAL の `bench_done.payload.run_cmd`)。1 CPU・1 NUMA ノードなので割り当ては変わらず、全 slot・全 arm が同じ条件。本書に Erratum 16.1 として追記した。
- 対象 commit と main の差: 本走は `1da88472b` (main `4f412c67b` + driver の最小修正 1 commit)。この差は本 wave の land で main に入る。
- 駆動 loop は repo の外の道具で、LLM 親の割当ては待ち時間順でなく schedule 順 (早い系列が先に親を得る)。台帳の規則には関わらない。
- 同等の判定は「観測差が floor 内」であって、母集団の等価性の証明ではない。stock に対する利得 (約 2.8〜3.2 倍) は全 arm に共通で、生成器間の差とは別物。

## 8. 確かめたこと / 確かめていないこと

- 確かめた: 51 項目の終了理由 (`done.json`)、894 slot の結果の内訳、579 job の Elapse の和 (scheduler 記録を grep で合計)、429 の 16 件 (台帳の `opportunity-end` の outcome)、
  LLM 親 249 機会の rc と outcome (loop の `actions.jsonl`)、親の起動 265 回の `modelUsage` と 429 (`rounds/*/a*/attempt-*/out.json`)、report の 4 比較の判定と数値 (`report-v1.json`)、版を記録した 576 slot で判定器の版が 1 種類であること。
- 確かめていない: stock・score・参照の 318 slot の判定器の版 (slot 結果に field が無い)、trace 保全の完全性。
  report の統計計算は、段 6 の記録 review (Codex、1 回目は委任検出で不受理、`verbatim/codex-review-2-unaccepted.md`) が 4,096 通りの符号反転で独立に再計算して一致したと報告した。
