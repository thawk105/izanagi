# 段 1 brief — [T-1909] / D1195 非標本 probe の逆到達閉包

## scope

B-4 事前登録 §5.1 (ii) が要求する「結果を生成しない配線調査」について、D1195 が定める形
(権威点からの逆到達閉包で生成経路の不在を導き、完全性は主張しない) を成立させる。
台帳は「これが無い限り事前登録は発効しない」と書いている。

## 確定済みユーザー裁定 (この wave で覆さない)

- D1083: 適格性は結果を生成も閲覧もしない配線調査で測ってよい。
- D1171: 遮断集合は手書き列挙でなく名前付き 3 権威点からの逆到達閉包で導く。完全性は主張しない。
- D1195: §5.1 (ii) の配線調査は上と同じ形で設計する。完全性を主張せず、閉包の外に経路が
  残りうることを明記する。
- 依頼の明示 scope: 本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は行わない。

## 親の provisional 裁定 (攻撃対象)

- **(P1-1) D1195 が要求する機構は既に着地している。** `orchestrator/campaign/p3_b4_wiring_probe.py`
  が 3 権威点を `_GENERATION_SEEDS` に持ち、`_reason_paths` の逆辺 BFS で逆到達閉包を導き、
  `_build_inventory` が遮断目録にし、`_ProcessGuard._profile` が目録該当 code の call で
  `OutcomeGenerationError` を送出する。採番記録では D1171 が実装 wave 自身の裁定、
  D1195 は `rulings-20260827-adopt` による同内容の採択である。
- **(P1-2) 完全性非主張の明記も既にある。** module docstring、証拠 JSON の
  `generation_scope_exclusion`、insight README、事前登録 §10 の 4 面。
- **(P1-3) したがって残差は無く、本 wave は「実装しない」裁定と台帳側の決着へ向かう。**
- **(P1-4) 別の導出法は repo に存在しない。** `_GENERATION_SEEDS` の全件検索は 7 件で、
  すべて probe とその test の内側 (切らずに全件を数えた)。

## 不変条件

- 規律 2 を緩めない。遮断・負例・検査を弱める差分は採らない。
- 完全性を主張しない。閉包が閉じたと読める文言を成果物に書かない。
- 不在の主張は全件検索でだけ行う。切った検索結果を 0 件の根拠にしない。
- §5.1 (i) の人間指名 (記入者・レビュー者) はこの wave の scope 外。§5 の欄は 1 つも埋めない。

## 成果物の形

- 残差が real なら: probe / test の最小差分を Codex `role=author` (D95) が書く。
- 残差が無いなら: 差分ゼロで、worklog と decisions の spool fragment に実測付きで決着を残す。
- どちらでも受入全走の receipt を取る。

## 分割方針

段 2 プラン 1 本 (codex plan、read-only)。段 3 敵対 2 本 —
lens A = 残差の実在を探す、lens B = (P1-1)〜(P1-4) を反証する。段 4 で親が裁定する。

## 変更面アンカー

|path|行|中身|
|---|---|---|
|`orchestrator/campaign/p3_b4_wiring_probe.py`|84|`_GENERATION_SEEDS` (3 権威点)|
|同|1099|`_reason_paths` (逆辺 BFS)|
|同|1135|`_build_inventory` (遮断目録)|
|同|594-610|`_ProcessGuard._profile` (遮断の発火)|
|同|2108-2117|`generation_scope` / `generation_scope_exclusion`|
|`orchestrator/tests/test_p3_b4_wiring_probe.py`|292-318|種除去の負例|
|`docs/phase3-b4-reflux-ablation-preregistration.md`|§5.1 / §10|規範と非閉鎖の明記|

## 受入・実測環境

worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure`、
base main `cb4a11b6e`。実行場所は `tools/run_tests.py` の自動判定。
焦点走 `orchestrator/tests/test_p3_b4_wiring_probe.py` は base main `11b44e2d1` で 59 件緑
(2026-08-31、57.17s、観測ピーク 2563731456 bytes)。

## 既に確認した被覆 (純増だけ書く)

D1171 / T-1769 が機構と証拠を着地済み。本 wave の純増は「D1195 の要求と現行実装の差分を
実測で確定し、残差があれば埋め、無ければ台帳を実測付きで閉じる」ことだけである。
