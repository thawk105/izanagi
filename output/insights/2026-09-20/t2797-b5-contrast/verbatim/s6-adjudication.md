# 段 6 裁定 — review A / B の所見と fix2 の指示

作成 2026-09-20 21:25 JST。対象 HEAD = 統合 commit 3 `92b5c4939` (commit 2 `e57481558` + fix1 登録 + README)。review A = `codex/s6-review-A.md` (NO-GO、must-fix 3)、
review B = `codex/s6-review-B.md` (NO-GO、must-fix 2)。

## 1. 所見の裁定

| # | 所見 | 判定 | 採否 / 親判断 |
|---|---|---|---|
| A1 | 帰属不一致・loader の候補起因拒否が `unclassified-missing` (系列終了) や `pre-start-failure` (機械 retry) になる | real / must-fix | **採用**: `p3_s4_loop` が B-5 mode で候補起因の前処理拒否 (loader の schema / 値域 / K2 semantic、`AttributionMismatch`、文法 preflight) を sidecar `proposal-rejected.json` {reason_class, exception, message} に durable 記録して rc 3 で終わる。driver は sidecar を見て `rejected-preprocess` (A のみ) → 次の opportunity。sidecar が一つも無い失敗だけが `pre-start-failure` (機械 retry) |
| A2 | verify 側の環境故障 (`verify-probe-error` / `verify-competing-tenant`) が候補起因になり fallback に化ける | real / must-fix | **採用**: `MACHINE_FAILURE_ABORT_REASONS` に 2 つを足す (bench 側と同型の「候補と独立な入出力障害」)。`indeterminate` は足さない (A10 refuted、証拠なし retry はしない)。retry 上限後は `unclassified-missing` (score None、fallback 無し) を test で固定 |
| A3 | job 全体打切り時、sidecar `pipeline-submitted` はあるが台帳 event が無く B・物理 attempt が過少 | real / must-fix | **採用**: driver は subprocess 起動**前**に `slot-attempt-start` event (slot_key, logical_slot, attempt, kind, a, b, sidecar_dir) を durable に書く。report は `slot-attempt-start` に対応する終端 event が無い attempt の sidecar (`pipeline-submitted.json`) を読み、B 消費 (search は論理 1 回だけ) と物理 attempt を `submitted-unresolved` として計上 (元 event は改変しない) |
| A4 | k ≥ 2 で診断が両方欠けても継承検査を通る | real / should | **採用**: `assert_inherited_inputs` は `next_evaluation ≥ 2` で `k2_critic_diagnosis` を両入力に必須にする (親は各評価の後に必ず critic を回す。critic の出力が使えなければ critic を回し直す — 候補の再抽選ではない) |
| A5 / B03 | 拒否・timeout・不一致の待機時間が集計から落ちる | real / should | **採用**: `_handshake` の全終了枝で `proposal_wait_wall_s` と `handshake_status` を返し、`proposal-rejected` / `series-end` event に載せる。report は opportunity 単位で重複なく集計。親手番の実時間・queue 待ち・job Elapse は外部証拠 (insight) に置き、report は null のまま |
| A6 / B02 | consumer が `fitness_tps == bench_payload.median_tps` を検査しない (fixture も不整合) | real / must-fix (B) | **採用**: `_validate` に一致検査、fixture を整合させ、不一致の負例を追加 |
| A11 | 変異の kill は静的評価、登録重み表を使う end-to-end vector を補う | 根拠不足 / should | **採用** (TB に登録 1000 重み表の固定候補 vector を 1 本、期待値は親が独立 script で算出して定数化 → 親が fix 後に値を検算) |
| A12 | 探索中の品質欠測を系列欠測にするか | 根拠不足 | **親判断**: 探索の品質欠測は当該 session の endpoint 資格だけを失う (§5.3「その session は品質欠測」)。系列は継続し、§7.4(2) の系列単位の品質欠測は score session と stock session (score / floor の材料) に限る。report は `exploration_quality_missing` を記述統計に出し、対照例 (探索 1 件欠測 + 正常 endpoint → 判定に進む / score 1 件欠測 → 欠測) を test に置く |
| A13 | brief の「verifier 費用の 5/6」は回数比 | nit | 採用 (insight の文言を「6 回中 5 回が performance verify」に) |
| B01 | B と評価履歴の不一致 (1 評価で B=10) を正常受理 | real / must-fix | **採用**: 完了系列 (`series-end` あり) は `evaluation-result` の件数 == 終端 b、b が 1..b で連番、を検査。不一致は `invalid`。fixture は producer が作れる形 (10 評価) に直し、1 評価で B=10 は負例 |
| B04 | `logical_sessions` が A-only 試行も数える | real / should | **採用**: `logical_sessions` = 投入済み論理 slot 数 (stock-start + submitted search (同 slot は 1 回) + score + block-stock)、`attempted_logical_slots` / `physical_attempts` / `preprocess_rejections` を別に出す |
| B05 | dry-run は Git 読取りを行う | real / should | docs (親): 「Git による読取り検証は行う、qsub と mkdir はしない」に統一 |
| B06 | launcher が自 checkout の PIN を使う | real / should | **採用**: 投入対象 checkout の `orchestrator/campaign/p3_s4_loop.py` から `^PIN = "…"` を正規表現で読む (subprocess を増やさない) |
| B07 | module CLI が llm の部分 K2 を受理 | real / should | **採用**: `run-series --arm llm` は `--knowledge-manifest` / `--knowledge-classification` / `--knowledge-de-novo-claim` の 3 つ全部を必須 (job body と同じ受理集合) |
| B12 | 重複 `wal_timing`、未使用 `baseline` 引数、launcher の env 再構築 | nit | **採用** (意味を保つ縮約だけ) |
| B13 | README の旧 K2 規則と B-5 例外・stock argv の明記 | real / should | docs (親): §7 の文言を直す |
| B14 | 1800 秒の根拠 | 根拠不足 | 記録: 暫定の開始余裕 (見積り 12〜14 分の約 2.1〜2.5 倍)。本走値は試走の実測から |
| A7〜A9, A10, B08〜B11 | refuted / 根拠不足 | — | 変更なし |

## 2. fix2 の所有 file (一枚岩、横断所見を 1 単位に寄せる)

`orchestrator/campaign/p3_s4_loop.py`、`orchestrator/campaign/b5_generator_contrast.py`、`orchestrator/campaign/b5_generator_contrast_report.py`、
`tools/pegasus/b5_contrast_launch.py`、`orchestrator/tests/test_p3_s4_loop.py`、`orchestrator/tests/test_b5_generator_contrast.py`、
`orchestrator/tests/test_b5_generator_contrast_report.py`、`orchestrator/tests/test_b5_contrast_launch.py`。

## 3. 追加の変異事前登録 (fix2 の所見に対応、DW-M01)

| ID | 位置 | 変異 | 殺す test |
|---|---|---|---|
| M20 | `p3_s4_loop.main` (B-5 mode) | 候補起因拒否で sidecar `proposal-rejected.json` を書かない | TL: loader 拒否 → sidecar 実在 + rc 3 |
| M21 | `_execute_slot` / `classify_slot` | `proposal-rejected.json` を `pre-start-failure` 扱い (retry) | TB: 帰属不一致 proposal → A+1、B 不変、retry 0、系列継続 |
| M22 | `MACHINE_FAILURE_ABORT_REASONS` | verify 側 2 reason を外す | TB: `verify-probe-error` abort → machine-failure → 同 slot retry |
| M23 | `run_series` | `slot-attempt-start` を subprocess 後に書く | TB: runner が例外で落ちる前に event 実在 |
| M24 | report | `slot-attempt-start` 未終端 attempt の sidecar 反映を外す | TR: sidecar のみの attempt で B=1 / physical=1 |
| M25 | report `_validate` | B と evaluation 件数の照合を外す | TR: 1 評価で B=10 → invalid |
| M26 | report `_validate` | fitness == median の照合を外す | TR: 不一致 → invalid |
| M27 | `assert_inherited_inputs` | k ≥ 2 の診断必須を外す | TB: 両方欠落 → 拒否 |
| M28 | launcher | PIN を自 module から読む | launcher test: 対象 tree の PIN 行を変えた fake で拒否 |
