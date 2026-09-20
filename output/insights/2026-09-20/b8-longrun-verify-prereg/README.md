# 2026-09-20 B-8 (種を変えた長時間実行による最終候補の検証) の事前登録 v1 を作った記録

- wave: `dev-wave-b8-longrun-verify-prereg` / branch `worktree-dev-wave-b8-longrun-verify-prereg`
- 基点 main: `947fd160a` (13:26 JST に fresh worktree)。記録前の main 取り込みは §「検査と land」に書く
- 依頼: B-8 の事前登録 v1 を docs-only で起草し land まで。発効・試走・本走は含めない。B-5 の事前登録 (D2158、未発効) と同型。
  台帳 ID 未起票 (出所 = 論文ストーリー 2026-09-20 §8 B-8「未取得」と D2160 の仕分け)。両対象案を択で並記し推奨を付ける。
  統計文は反例を作ってから書く。実装差分ゼロ、段 6 の read-only レビュー 1 本は残す
- 成果物: `docs/b8-final-candidate-longrun-verify-preregistration.md` (v1、未発効)、`docs/README.md` の 1 bullet。実装面差分ゼロ
- 専用 handoff: repo 外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b8-longrun-verify-prereg/handoff.md`

## 一行で

**B-8 が「未取得」のまま動かない理由は、論文ストーリーの仕分けが挙げた 3 要件 (対象・種・長時間) のどれにも
結果を見る前の操作的定義が無いことである。事前登録 v1 で、対象は 2 案 (S-1 最終候補 g_rl / g_rt を推奨、採用静的
backoff 2 genome を代替) を択として登録し、「種」は S-1 層 2 の登録定義 (独立 process の自己シード)、「長時間」は
「3 s より長い extime を {6, 10} s の校正で決め 3 s へ丸めない」と定めた。判定は D2160 項 3・5 を継承した。発効・試走・
本走・runner 改版は認可されていない。**

## 段 1 実測 (親、一次資料)

| 要素 | 実測 |
|---|---|
| S-1 (iv 付属) の対象 | 系側 gate 構成 g_rl (balanced / read-heavy) / g_rt (write-heavy)。gate 述語・flags は `output/s1-freeze/known_axes_freeze.json` の `entries.<workload>.system_gate` (逐語は `materials/` に写していない — JSON をそのまま読む)。`ccbench_pin` は `d706650c…`、`frozen_at_head` は `2066ce6b4…` |
| S-1 の検証相 (24 verify) | 実施されていない。`output/reports/s1_direct_comparison/report.md` 冒頭「本設計は独立な検証相を持たない」(`materials/05`) |
| 07-16 の校正 | `output/env/linux-baremetal/calibration/s1_verify_extime.json`: g_rl read-heavy 3 s = verifier 433.33 s / maxrss_gb 25.68 / txns 5,283,740、6 s = 974.73 s / 51.43 / 10,447,714、両方 serializable・certified、`src_token` `4608a96e…`、ccbench `d706650`。`chosen_extime` 3、`limit_s` 600 |
| S-1 freeze の状態 | `IZANAGI_FREEZE_HOLD` (`s1-known-axes.ccbench-submodule-head-pin`、release = explicit-user-command-only) — pin が d706650 から現行へ進んだため (2026-09-11 の t2527 receipt に逐語) |
| 案 A の build 経路 | `patches/silo-backoff-trigger-gating-variant.patch` + `orchestrator/campaign/axis_trigger_gating.py` (`TEMPLATE_PATCH`) + `s8a_trigger_sweep._genome(1)`。`s1_verify_extime_calibration.py` が旧 pin で同経路を使った実績。現行 pin への `patch -F0 --dry-run -p1`: `cc/silo/transaction.cc` の全 hunk が当たる (hunk #10 は offset 13 行)、`cmake/Options.cmake` は patch の `index 0000000..0000000` 行を GNU patch が「新規 file」と読んで判定不能 (`silo-backoff-fixed.patch` も同形式で、D2160 の runner は `git apply` で通している)。**driver と同じ厳密適用・trace-enabled build・identity 導出は未実測** |
| 採用候補 2 genome (案 B) | D2160: fixed-5 `678b7203…`、fixed-10 `16c29935…` (現行 patch 下)。3 s × 8 反復 × 3 workload = 24 + 校正完走 6 = 30 verify / 候補、anomaly 0、pass。校正 6 s は 3 workload とも完走 (write-heavy 247.5 / 250.6 s、balanced 357.0 / 344.0 s、read-heavy 864.3 / 807.8 s、read-heavy maxrss 85.6 / 80.2 GiB)。10 s は balanced SIGKILL (294.9 / 303.1 s、2 node)、write-heavy hard timeout 3600 s。本走実消費 6316 / 6134 S (≈ 263 S / verify)。trace 保全 213.3 GB → 48.9 GB (64 走 × 48 file、4.36×) |
| CCBench の乱数 | `include/random.hh` `Xoroshiro128Plus::init()`: `std::random_device rnd; s[0] = rnd(); s[1] = splitMix64(s[0]);`。`include/ycsb.hh` `YcsbWorkload()` が `rnd_.init()`。`common/runner.hh` `worker_body` が worker thread ごとに `Workload workload;` を構築。ycsb の gflags は rmw / max_ope / rratio / tuple_num / zipf_skew の 5 つで seed は無い (`materials/06`) |
| S-1 の「seed×N」 | 層 2「独立 N 反復、決定論的 seed 固定は導入しない (D16)、独立性は操作的仮定」(`materials/03`) |
| roadmap §3.2 | 「seed を変えた複数 run は未観測バグの機会を増やすが … 数値的な信頼度や完全保証には変換しない。報告するのは条件、seed、trace 規模、観測 verdict」(`materials/04`) |
| 並行 wave | `dev-wave-verifier-capacity` (13:16 JST 開始、job dir に handoff) が 10 s 未完走 2 型の原因同定と省メモリ化を扱う。本 wave の編集面 (新 file + README 1 bullet) と交差しない。本書は同 wave の成果を前提条件にせず、校正規則で吸収する |
| DW-O09 pin 閉包 | `docs/README.md` は `check_docs.py` の LIVING_DOCS (行番号参照・pin literal・現況主張の lint) の対象で、sha pin は無い。新 file は LIVING_DOCS に入れない (B-5 と同じ) |
| 起動 gate | `check_wave_startup.py --mode fresh --external-handoff` rc=0 (13:29 JST)。submodule 初期化 rc=0、`external/ccbench` = 現行 pin |

## 段 4 裁定 (親、軽量版)

段 2 plan・段 3 相談は省略 (DW-C00 の既定軽量版、設計択一は brief の (P1)〜(P5) として本文へ明示し段 6 の独立レビューで
攻撃対象にした)。`rulings-stage4.md`: P1 対象 (案 A 推奨・案 B 代替・択一は発効時)、P2 種 (S-1 層 2 の定義)、P3 長時間
(≥ 6 s、校正 {6, 10}、上限 1800 s、丸めない)、P4 費用 (案 B 6 s の算術のみ)、P5 判定 (D2160 項 3・5 継承)。
統計文 4 つを反例付きで「書かない」へ。親が実測で支えていない否定命題 4 つを列挙してレビューに反証を求めた。

## 段 6 (Codex、read-only、全段 `gpt-6-astra` / medium、受理は `check_codex_output.py` rc=0)

| 段 | 子 | 受理 | 要点 |
|---|---|---|---|
| 6 独立レビュー | `codex/review.md` (12 call、288 秒) | accepted | 一次資料との照合: 数値・identity・gate 述語・D 参照は一致。must 2 (失格と pass の排他性 / 発効束と校正の循環)、should 4 (保全容量の母集団 = 3 s 54 走 + 6 s 6 走 + 10 s 4 走、統計文の反例と確率表現、不在断定の確認範囲、予算段下げと適格集合)、nit 1 (件数内訳・参照・per-verify 値)。否定命題 8 件はすべて「読解のみ」、反証なし |
| 6 fix (親、docs) | §1.1・§1.3・§2.2・§2.3・§3.1・§5・§6.1・§7・§8・§11・§12 | — | 判定を「失格 → pass → 未確定」の排他 3 値へ、校正完走 verdict に certified を要求しない、発効束から校正結果と本走 walltime を外す、保全容量を「仮定の算術」の桁の目安へ、ε ∈ {0, 1} の説明、二重 init、確認範囲の限定、段下げは適格集合内。結合文字 U+0302 を平文 B へ (`rulings-stage6.md`) |
| 6 焦点再レビュー 1 | `codex/focus.md` (6 call、152 秒) | accepted | closed 2 (保全容量、段下げ) / partial 5。再計算は全項一致 (3 s 相当 79.3 走、2.689 GB、129.1 GB、29.6 GB、n²/2³³ = 1.545 × 10⁻⁴ / 6.180 × 10⁻⁴、13,000 s、余裕 1,401 s、58.4 %)。新規 must 1 (失格条件と失格時に書く事実の不一致)、should 5 (ε の意味の反転、§0 の指示語、§12 の段下げ後の記録、既知結果表の無限定断定、(3d) の効能否定)、nit 1 |
| 6 fix 2 (親、docs) | §0・§1.1・§1.3・§2.3・§4.4・§6.2・§6.3・§8・§12 の 12 箇所 | — | 失格の報告を verdict + anomaly の観測値へ、ε を見逃し確率で統一、発効束の項目だけを発効条件に、段下げ後の本走 extime を記録対象へ、断定に確認範囲を添える、(3d) の理由を予算と資源依存へ、比較を「既知結果の追試か初回検証か」の区別へ |
| 6 焦点再レビュー 2 | `codex/focus2.md` (5 call、76 秒) | accepted | closed 6 / partial 1。新規 must 1 (追記文言が anomaly ≥ 1 ∧ verdict serializable の入力で観測と異なる verdict を報告する) |
| 6 fix 3 (親、docs) | §1.1・§6.3 | — | 失格文を「anomaly を検出した verify i 件 (計 a 件)、serializable でない verdict j 件、観測していない側は 0」へ。DW-O16 の 3 巡上限内で、残った所見は報告文の量化 1 点で新しい主張・派生値を含まないため、3 巡目を起動せず親が閉じた |

親の統計文は、独立レビューと焦点 1 巡目が続けて倒した (ε の定義の反転、反例でなく「非自明な ε を置けない」例)。
「反例を作ってから書く」を適用しても、定義の一貫性 (§1.2 の ε と §1.3 の ε) までは自分で検算できていなかった。

## 検査と land

- `python3 tools/check_docs.py` — 違反なし (修正のたびに再走、最終 14:22 JST)。
- `git diff --check` — 空 (tracked 差分)。事前登録本文・README bullet・fragment・本 README の末尾空白 0。NFC — 事前登録本文の
  結合文字 U+0302 (B̂) を平文 B に置換して 0。**Codex 逐語 3 file は末尾 2 space (Markdown の改行記法) を原文のまま保持**しており
  `git diff --cached --check` はこれを trailing whitespace として挙げる (可視文字不変、正規化していない。原本は job dir の
  同名 file と byte 一致、sha256 は下表)。

| file | bytes | sha256 |
|---|---:|---|
| `codex/review.md` | 12371 | `4e18abd5cb86779d477418f1bb770888bf093f4abaf1a740f53567611b21dbf6` |
| `codex/focus.md` | 8246 | `bc2c8722b2132e4fb79a2dade737171567c0c493e90cef89022ab42581bec08e` |
| `codex/focus2.md` | 3224 | `b1c4531039b7d25dc8d90d2bc10e8f631f50d63ba50fc1b60c6d09fa3efe6454` |
- `python3 -m orchestrator.campaign.s8b_holdout_freeze search` — rc 1 だが hit は既存 4 file (official floor 校正の journal / manifest / result と
  `holdout_freeze.v2.g1.json`) で、本 wave の 2 file に hit なし。
- `python3 tools/spool_fold.py --dry-run` — rc 0 (fragment 2 本、形式 OK)。
- 変異 matrix — 実装面差分ゼロで免除 (DW-S04)。受入全走 — 記録 commit の tip に対して投入 (結果は worklog fragment と land の receipt)。
- local main は着手 (`947fd160a`) から 14:1x JST に `d4af98f15` (T-2610 docs wave の land、実装面ゼロ) へ進んだ (peer 通知を契機に
  記録直前に読み直し、ff-only で取り込んだ。編集面の重なりは無い)。

## dev-wave 改善候補

- ゼロ。隔離 session の Bash guard が submodule path を含む `git apply --check`・複合 shell・heredoc を拒否したのは既知の型
  (memory 既載) で、`patch -F0 --dry-run` と job dir の python script (Write tool) で代替した。手順の欠落ではない。
