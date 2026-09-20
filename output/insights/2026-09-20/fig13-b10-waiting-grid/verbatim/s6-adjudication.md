# 段 6 裁定 — review A (過剰・削除、must-fix 0 / GO) と review B (正しさ境界・限定、must-fix 1 / NO-GO) の所見

| id | 種別 | 判定 | 採否 | 処置 |
|---|---|---|---|---|
| B-1 | must-fix | **real** — FIGURE_CONVENTIONS §6「測定条件 (スレッド数・レコード数・skew・env) は図のサブタイトルかキャプションに必ず出す」に対し、レコード数 1,000,000 と Zipf skew 0.9 が図・caption・provenance に無い。値は report provenance JSON の `calibration.records` (1000000、`calibration.threads` 48) と `preregistration.spec.workloads[].ycsb_zipf_skew` ("0.9" × 3、`ycsb_rratio` 5 / 50 / 95、`ycsb_rmw` "0"、`ycsb_max_ope` "10")、`spec.execution.extime_s` 3 に実在 (親が実測) | 採用 | fix 子: `measurement_conditions` に records / zipf_skew / rratio / rmw / max_ope / extime_s を加え (spec と calibration から読み、3 workload の skew 一致と calibration.threads == execution.threads を要求)、caption の `Conditions:` と図の脚注に records・skew (・rratio) を出す。親が図を再生成し README の caption / SHA を更新 |
| B-2 | should | real — 等価域の端点 (±0.03 ちょうど) を fixture が踏まず `>=` / `<=` の向きが未検査。producer (`2a338449b` の `orchestrator/campaign/b10_backoff_shape_sweep.py` L1895〜1900) は `low >= -m and high <= m` → inside、`high < -m or low > m` → outside、他 → overlaps で、生成器の `_relation` と同一 | 採用 | fix 子: `_relation` の端点 test (両端がちょうど ±margin → inside、`high == -m` / `low == m` → overlaps、`high < -m` → outside) を追加 |
| A-1 / B-3 | should | real — README「Holm 3 行・cell effects 36 行との照合」は実装 (Holm 3 行は値、cell は行数だけ) より広く読める | 採用 (docs) | 親: figures/README「入力」を「Holm 3 行の値と cell effects 36 行という行数」に直す。実装の拡張 (cell 36 行の値照合) は plan v2 どおり行数のみで据え置き (値は JSON 側で全件再計算済み) |
| A-2 | should | **refuted** — `outside-equivalence-range` は producer の語彙そのもので、規則も同一。この report に実例が無いのは事実だが、override 下の受理は producer の意味論の写しであり、拒否へ変えると生成器が producer と食い違う。pin が本番の受理を固定している | 不採用 | B-2 の端点 test が `outside` 分岐の向きも固定する |
| A-3 | nit | real (過剰の起点は閉包契約) | 不採用 | epoch 定数は repo 外を読まない閉包に要る。据え置き |
| A-4 | should | partial — panel 題の raw p 二重表示・和の数値は情報量が多いが、読取不能ではない (review A 自身が PNG で確認) | 不採用 | (P1) どおり据え置き。題の短縮は bytes を変えるだけで値・限定に影響しない。論文本文幅での縮小は組版時の課題として insight に記録 |
| A-5 | should | real — tools/plotting/README の節が拒否条件・固定文を重複記載 | 採用 (docs) | 親: tools/plotting/README の節を用途・command・入力 root・出力・fig13 節への参照に縮める |
| A-6 / B (m4, m13) | should | real — m4 は定数変更だと spec 照合が先に拒否する (登録した probe spec の m4 は係数だけ `1.96` に変える形で、定数は保持 = 再照準済み)。m13 は境界正例と負例が同一 test で、`>` 化は fixture 全般を先に拒否しうる | 採用 | 変異 final spec: m13 を m13a (検査削除 → 9999 の負例が殺す) と m13b (`>=`→`>` → 10000 ちょうどの正例が殺す。fixture 全般が赤なら過剰決定として単独変異の証拠から外し、境界感度として別枠記録) に分ける。他は probe の観測 node で確定 |
| B 値の写し | — | 全項目一致 (raw p 3 組、Holm p、和、集計、境界 4 cell、負の点推定 1、下限正 8、identity、SHA) | — | insight に転記 |
| A/B 言い方 | — | (a)〜(h) の逸脱なし (両 review) | — | — |

brief の誤記 (review A): 「3 workload × 3 block × 15 点 × 5 rep = 135 record」→ 正しくは 135 record × 5 sample = 675 sample。fixture には伝播していない。insight で訂正。

## fix1 の所有と契約

- unit worktree `.codex/worktrees/fig13-b10-unit-impl` に branch `dev-wave-fig13-b10-unit-fix1` (author 終端 commit 5b68f9313 の上)。所有 = 生成器 + test (author と同じ)。
- 段 5 実装子契約 (DW-S05-A/B/C) を全文継承。既存 (他 file) の test の期待値は変えない。本 wave の test file は B-1 / B-2 に必要な範囲でだけ更新し、緩和・skip・削除はしない。
- fix 後: 親が図を再生成 → README 更新 → 焦点再レビュー 1 本 (DW-O16) → 変異を新 anchor で再 probe → final。
