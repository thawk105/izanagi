# 段 1 brief — [T-673] 遷移述語の量化縮退に対する検査方式の判断パッケージ

wave: `dev-wave-t673-transition-pbt-package` / 2026-08-09 / HEAD `4be7a362`

## scope

`_validate_activation_transition` の 2 つの量化点に対する `[:N]` 型 truncation 変異族について、
(A) 現状維持、(B) 生成的 / property-based テスト、(C) 量化の構造的検査、の**コストと検出力を実測**し、
裁定パッケージとしてユーザーへ返す。**本番コードは編集しない。候補テストも land しない**
(land すれば裁定を既成事実にしてしまう)。land するのは docs (worklog fragment) と insights だけ。

## 確定済みユーザー裁定 / 前提

- ユーザー明示: 本番コード編集禁止、コストと検出力は**実測**、出力は裁定パッケージ。
- [T-627] (worklog archive 318) が本件の由来。4 env で止め残穴を docstring 明記、で閉じた。
- `docs/decisions.md` D245 / D176 が遷移述語の設計正本。本 wave は受理集合を変えない。

## 実測で確定した対象の所在 (機構名でなく性質で検索した結果)

- 量化点 A: `orchestrator/campaign/env_contract_activation.py:300`
  `for predecessor, successor in changed:` — successor 述語の適用範囲。
- 量化点 B: 同 `:275` `for successor in successor_rows:` — exactly +1 / no-op 判定の適用範囲。
- 「truncation を殺す」性質を持つ既存被覆 = 拒否側が末尾 env で発火する node のみ:
  `test_transition_rejects_when_{second,third,fourth}_changed_env_successor_is_false` (A 側、最大 4)、
  `test_transition_rejects_fourth_env_downgrade` (B 側、最大 4)。
  受理側 fixture (`..._four_env_simultaneous_plus_one`) は truncation で結果が変わらず殺せない。
- 残穴の明記: `orchestrator/tests/test_env_contract_activation.py:554-556` docstring。
- 純増検出力を測る計器: `tools/mutation_harness.py`。[T-627] 実績で 2 file scope・1 変異 27〜37 秒。

## 不変条件

- 本番 `orchestrator/campaign/**` を 1 byte も変えない。既存テストも変えない。
- 候補テストは Codex `role=author` が書く (実装面)。親は brief・裁定・変異 spec・実測・記録のみ。
- 候補テスト・probe は repo へ .py として入れず、insights へ逐語凍結する ([T-627] 先例)。
- 規律 2/3 を緩める方向 (残穴を「無い」と書く、恒真な保証を謳う) を採らない。

## 成果物の形

1. 変異 spec (親) — A/B 両量化点 × N ∈ {1,2,3,4,8,64} の truncation 変異。
2. 台帳 2 走以上 — (i) 現状の木、(ii) 候補テストを載せた木。同一 spec で frontier の差を測る。
3. コスト表 — 候補ごとに test 実行時間・行数・依存追加の有無・保守面。
4. 裁定パッケージ (択一と推奨、残穴の残り方を各案について 1 行で明示)。

## 成果物影響 (DW-G05)

本 wave 自体は campaign の certified 選択・レポート・台帳の値・受理集合・参照を**一切変えない**
(production 不変、テスト未 land)。実装しない場合の影響は、`changed[:N]` (N≥4) 型の実装退行が
CI をすり抜け、activation 遷移で不正な世代前進が受理されうる残穴が現状のまま残ること。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 「有限 fixture では族全体を殺せない」は property-based テストにも等しく当てはまり、
  hypothesis を入れても残穴は N ≥ (生成上限) へ移動するだけで消えない。したがって (B) は
  「残穴を消す案」ではなく「残穴の位置を動かす案」である。← 実測で反証されうる。
- **(P2)** 残穴を実際に閉じうるのは (C) 構造的検査 (量化式の形を AST で pin する等) だけであり、
  その代償は意味検査でなく形の pin になること。← 代替の構造的 oracle があれば反証されうる。
- **(P3)** env 数 M を増やすコストは純 Python の dict/tuple 操作で M に線形、M=64 でも無視できる。
  ゆえに (B) の実質的な争点は「依存追加」であって「実行時間」ではない。← 実測で決める。
- **(P4)** repo に依存宣言 file が 1 つも無い (`pyproject.toml` / `requirements*.txt` 不在) ため、
  hypothesis 追加は「初の第三者テスト依存」であり宣言機構ごと新設になる。← 実測済み、要再確認。

## 並列分割方針

段 2 = plan 1 本 (read-only)。段 3 = 敵対 2 レンズ (model 混成、(P1)〜(P4) と測定設計を攻撃)。
段 5 = Codex author 1 本で候補テスト B1 (stdlib 生成的)・B2 (hypothesis)・C (構造的) を分離所有で作成。
段 6 = 変異 matrix (親) + 敵対レビュー (測定と結論の乖離を攻撃)。
