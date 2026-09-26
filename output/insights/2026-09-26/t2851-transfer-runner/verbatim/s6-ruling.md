# 段 6 裁定 (1 巡目) — 2026-09-23 21:40 JST、対象 commit 5290cff62

review A (codex/s6-review-a.md) と B (codex/s6-review-b.md) は両方 NO-GO。

| ID | 判定 | 採否 | fix の内容 |
|---|---|---|---|
| R-A1 (= P-1) | real | 採用 | A/B 共通の JSON 契約に統一 (下の「契約」)。A の実出力をそのまま B に渡す境界 test を 1 本以上足す |
| R-A2 (= P-2) | real | 採用 | M = 族ごとに、cell ごとの重複除去済み (候補 identity, 強い参照 identity) の数 (same_identity を除く)。系列との対応は comparisons に別に保持 |
| R-A3 (= P-3) | real | 採用 | 異なる参照 identity どうし (R0–R1、R0–R2、R1–R2、MOCC/TPC-C は凍結した参照間) を記述の比較として凍結 |
| R-A4 | real | 採用 | run-job / verify の実行前に凍結本文の canonical hash を再計算し `sha256` field と一致を要求 |
| R-A5 | real | 採用 | 再検証の回数は実際に trace を走らせた検証だけで数える。同 hostname の拒否記録は数えない |
| R-A6 | real | 採用 | cohort 2 の run-job は cohort 1 の全 job 記録の一覧を受け、最後の end_utc と同じ (段, protocol, cell) の hostname を記録から導出 (`cohort1_last_end_utc` の直接入力は廃止) |
| R-B1 | real | 採用 | `_adopt_jobs` の不成立 attempt への fallback を削除。不成立値は attempt 行 (記述) だけ |
| R-B2 | refuted | 不採用 | binary 内容の sha256 照合は v1 §5「両 cohort で同じ identity の build」と §13.1 の束縛を保つ検査 (規律 7 が妨げない束縛の検査)。仮想リスク向けの追加 gate ではない。維持 |
| R-B3 | real (一部) | 採用 | witness 判定は pipeline.py の該当条件 (file:line を comment) と同等であることを、各条件 1 つずつ外した負例 test で固定 |
| R-B4 | real | 採用 | job 失敗・単独性違反の 1 回目 (resubmit) と 2 回目 (retry-exhausted) の test |
| R-B5 | real | 採用 | 順序 test の期待値を独立に固定 (K=3 の具体置換を定数で書く。親の手計算値は下) と、鍵 1 文字違いで置換が変わる例 |
| R-B6 | real | 採用 | `previous_record` を削除し `attempt_history` 一つに寄せる |
| 削除推奨 walltime | refuted | 不採用 | 発効時の費用見積り (v1 §12・§13.1) に 1 走の所要が要る。維持 |
| 削除推奨 verifier 全量 | refuted | 不採用 | v1 §8 が anomaly の種別と依存の構造の報告を要求 (規律 3)。維持 |
| 未使用 import | real | 採用 | 削除 |
| 親追加 ycsb_rmw 表記 | real | 採用 | 既存 pipeline (`S2_FLAGS`・`CorrectnessWorkload`) と同じ `"true"`/`"false"` にする |

## 契約 (A が書き B が読む。field 名はこれを正本とする)
- 検証 status の語彙: `certified` / `disqualified` / `indeterminate` (ASCII。docstring に v1 §8 の certified / 失格 / 未確定 との対応を書く)。
- freeze.comparisons の各要素: `stage`、`protocol`、`cell`、`anchor` (比較が結び付く錨 cell 名)、`factor` (錨なら null)、`level` (動かした引数の値、錨なら null)、`candidate`、`reference`、`kind` (`primary` / `descriptive` / `known_separate`)、`comparison_type` (`selected` / `reference_pair`)、`reference_mode` (`a`/`b`/`c`、YCSB silo は `a`)、`same_identity`、`series` (この (候補, cell) を選んだ全系列の [task, method, independent_search] の一覧。reference_pair は空)。M は `m_by_family` だけが持つ。手法別の記述集約は B が `series` と freeze.series から組む。
- run-job 記録: `stage`、`cohort`、`protocol`、`cell`、`attempt` (同じ job key の attempt_history 件数 + 1)、`hostname`、`start_utc`、`end_utc`、`isolation_start`、`isolation_end`、`completed_blocks`、`within_retry_limit`、`separate_allocation`、`next_action`、`blocks[] = {block, order, runs: {identity: {tps (数値 or null), rc, reason?, walltime?, transaction_counts?}}}`。B は `runs[identity].tps` を読む。
- verify 記録: `stage`、`protocol`、`cell`、`identity`、`hostname`、`status`、`reason`、`anomalies`、`attempt` (実際に trace を走らせた回だけ番号を持つ。拒否記録は `attempt: null`)、`verifier`。

## 親の手計算 (R-B5 の独立期待値の出所)
fix 子が自分で独立に計算して定数にすること。親は値を渡さない (同じ算法での自己生成を避けるため、test では hashlib を使わず定数の置換列を書き、その値は fix 子が手元で一度だけ算出して報告に書く。親が別途 python で照合する)。

## 変異 anchor
M7 (検証 3 値) の old 文字列は語彙変更で変わる。fix 後の報告で M1〜M12 の一意 old 文字列を書き直させる。
