# 段 1 brief — [T-2583] 高域での勾配符号の振る舞い

## 研究前進

**進む主張: B-10 (機序説明の帯域外への拡張)。** D1932 は刻み応答の非単調性の機序を
「歩行が高い `Backoff_` へ居着く (滞在分布)」と定めた。しかし**なぜ歩行が高域から戻れないのか**は
測っていない。その候補の 1 つが計数ノイズによる勾配符号の劣化であり、事前登録 J1 はそれを測ろうとして
**両条件が重なる低域 (`Backoff_` <= 12 µs の 12 辺) しか見られず** `not_supported` に終わった。
D1932 は却下枝に「**計数ノイズの寄与を否定するものではない**」と明記している。ここが空白である。

**土台としての止まっている実測:** 高域 (`Backoff_` > 50 µs) の勾配符号は 1 度も測られていない。
**完了判定:** 高域の符号の振る舞いの実測値、または「既存 J1 経路では測れない」という**構造**
(何が足りないか、どの対照なら成立するか) が insight に載ること。

## scope

- **本題の実測だけ。** 高域の勾配符号を、既に記録済みの trace から測れるところまで測る。
- **既存 J1 経路が高域を実行できるかを先に測る** (`DW-G01` の生死実験)。使い捨て probe で行い、
  段 6 後に repo 外へ退避する。**repo の実装面差分はゼロで終える。**
- **scope 外 (ユーザー明示):** 仮想リスク向けの gate・検査・台帳・一般化の追加。新しい Pegasus 実測。
  解析器への band 引数の恒久追加。J1 判定の再裁定。

## 確定済みユーザー裁定

- 「できるかを先に実測し、できなければ差分ゼロで返す」(依頼本文)。
- `Codex author = D95` — 実装面 (probe を含む) は Codex `role=author` の子が書く。親は直接編集しない。
- D1932: 機序 = 滞在分布。J1 は低域のみで不支持。計数ノイズの寄与は否定されていない。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1)** 「既存 J1 経路」= `orchestrator/campaign/backoff_nonmonotonicity_analysis.py:507-646` の
  `_edge_observations` / `_edge_counts` / `_fixed_edge_comparison` / `_j1_sign_instability` の 4 関数。
- **(P2)** 「高域の辺」= 直前 event の順序なし辺 `{backoff_before, backoff_after}` の**両端が > 50 µs**。
  代替 (max > 50 / min > 50) も同時に出して感度を示す。
- **(P3)** 「実行できる」= 既存経路の bytes を変えずに、高域に限った符号不一致率の比較が
  事前登録の `common_support_minimum = 10` を満たす共通辺を持つこと。
- **(P4)** 推定量・帯域・対照の組は **probe を走らせる前に**凍結する。J1 は
  `estimator_specified_after_data: true` を自認しており、同じ弱点を繰り返さない。

## 不変条件

- **規律 2 を緩めない。** 本 wave は correctness gate・verifier・受理集合に触らない。
- **凍結:** `s4-ruling.md` §6 の J1〜J4 事前登録の文言を変えない。解析器の J0〜J4 の出力 field を変えない。
- **規律 7:** 2026-09-10 の J1 判定 (`not_supported`) を遡って昇格・撤回しない。訂正は追記だけ。
- **非認証:** trace は `headline_eligible = false` / `throughput_scope = diagnostic_only`。
  本 wave の値は headline・formal B-10・floor・fitness・variant 採用に使えない。
- 射程は write-heavy / 48 スレッド / records 1,000,000 / extime 3 秒 / 1 rep / Pegasus に限る。

## 成果物の形

- `output/insights/2026-09-15/t2583-backoff-high-band-sign/README.md` と `verbatim/`。
- worklog / decisions / failures は `docs/spool/` fragment。
- **実装面 (コード・テスト・probe) の repo 差分はゼロ。** 変異 matrix は `DW-S04` により免除、
  受入全走は免除しない。

## 入力 (実在確認済み)

- trace: `/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace-t2188/stage1-rep0-0_989505.nqsv.json`
  (140,354,574 bytes)。6 セル。`nm-step1` 65,536 events / `nm-step1-u2560` 1,170 events。
- 既知の滞在 (J2): 時間加重 `P(Backoff_ > 50)` は `nm-step1` 0.8412、`nm-step1-u2560` **0.0000**、
  `nm-step2` 0.9819、`nm-step25` 0.9617、`nm-step100` 0.9547、`nm-step0.5` 0.0000。

## 分割方針

段 2 plan 1 本 → 段 3 敵対 2 本 (レンズ A = 循環・帰属・事後推定量、レンズ B = 実行可能性・scope・
「測れない」の証明責任) → 段 4 裁定 + 事前登録凍結 → 段 5 probe 実装子 1 本 → 段 6 レビュー 2 本 + fix。
