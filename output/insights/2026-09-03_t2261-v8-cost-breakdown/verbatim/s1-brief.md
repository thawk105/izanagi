# [T-2261] 段 1 brief — V-8 の費用内訳を現行コードで測り直す

- 起点 local main: `c7ed56589`
- wave worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost`
- wave branch: `worktree-dev-wave-t2261-v8-cost`

## scope

`docs/phase3-8c-wiring-design.md` §5.3 が V-8 の (a) に付けた「実行費用が 33 倍」を、現行コードで
測り直す。測った数字を V-8 の裁定へ返すところまでが scope。V-8 の択一そのものは選ばない
(D1561 が「材料を持って裁定する」と決めている)。受理集合・凍結成果物・proof chain には触れない。
gate・検査・台帳・一般化・新しい道具は作らない。

## 確定済みユーザー裁定

- **D1561**: V-8 は費用内訳を再測定してから裁定する。現時点で択一を選ばない。
- **D1555**: V-8 は V-7 → 本番 runtime provisioning → 本番 origin → P6 発火条件の依存鎖の根。
- **D205 (プロトタイプ基準)**: 測るための新機構は作らない。既存の入口と既存の成果物で測る。

## 不変条件

- 絶対規律 2 を緩めない。費用が高いことを理由に正しさ側の要件 (per-query の物理実行保証) を
  緩める提案をしない。
- 絶対規律 7 に従い、測定は「いつ・どのコードで・どの道具で」を併記する。過去の見積りを
  bytes 単位で書き換えず、追記で訂正する。
- 実装面 (コード・テスト・実行可能 script) の差分は 0 を目標とする。必要になったら親が書かず
  Codex `role=author` へ送る (D95)。使い捨ての集計は repo へ入れない。
- 測定値は測った checkout と機体を併記する (`DW-O12`)。

## 成果物の形

`output/insights/2026-09-03_t2261-v8-cost-breakdown/README.md` に、(1) 費用項の per-run / per-row
分類 (file:line 付き)、(2) 各項の実測値と観測 regime、(3) V-8 (a) の倍率の再計算、
(4) この数字が保証しないこと、を書く。worklog fragment で V-8 の裁定へ返す。

## 割れうる前提 — 親の provisional 裁定・攻撃対象

- **(P1) 「33 倍」は campaign run を費用の原子単位と見なした数字である。** (b) を採っても 33 行の
  物理実行そのものは 33 回ある。したがって (a) が余分に払うのは **campaign run の固定費 x 32** だけで、
  倍率は `(33F + 33R) / (F + 33R)` (F=run 固定費、R=1 行の費用) になる。33 倍が正しいのは
  `R ≈ 0` のときだけである。
- **(P2) F の内訳は次で尽きる。** process 起動と import、`_authorize_measurement`
  (`orchestrator/campaign/loop.py:161`)、perf preflight (同 `:108`)、WAL layout 生成と復旧走査
  (同 `:440-462`)、`settle()` を run あたり 1 回 (同 `:463`,`:584`;
  `orchestrator/calibrator/runner.py:271`、上限 20 秒)、campaign claim 取得 (同 `:230`)、終端 seal。
- **(P3) build cache と検査器並列化は R を下げるので、倍率を 33 の側へ押し上げる。** T-2191 の
  実測で検査器は 2.2 倍速くなり、検査器は read-heavy の 1 反復所要の 68-75% を占めていた。
  つまり D1561 の再測定要求は、倍率が小さくなる方向にも大きくなる方向にも効きうる。
- **(P4) V-8 の 33 行が実際にどの workload・どの protocol で走るのかが未確定なら、R は帯でしか
  書けない。** P6 の 32 mask 行の protocol を一次資料で確かめてから R を選ぶ。

## 並列分割方針

実装面の差分 0 を前提とする軽量版。段 2 で plan を 1 本、段 3 で異なるレンズの敵対相談を 2 本。
V-8 は割れている設計択一なので、`DW-C00` に従い敵対検証子は省かない。段 5 は実装面が無ければ飛ばす。
実測は親が行う。

## 実測環境

login node で完結する範囲 (静的分類、import 費用、`settle` の上限、既存 WAL の時刻差集計) を
既定とする。計算ノードの新規投入は、login node で F が決まらないと分かった場合だけ検討し、
その時点で単独性と混雑を確認する。B-10 正式走の WAL は既存成果物であり、新規測定を起こさずに
R を読める一次資料である。
