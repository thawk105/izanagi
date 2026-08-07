# 段 1 brief — [T-624] activation record の no-op 拒否

基準 commit: `bb824d8b` (= 開始時 main HEAD)。branch `worktree-dev-wave-t624-activation-noop`。

## 確定済みユーザー裁定 (前提。攻撃対象ではない)

- **[T-624] = (a)** (2026-08-07 /rulings 第 3 回)。activation record の世代遷移規則を
  **「全 env の delta ∈ {0,1} かつ少なくとも 1 env の delta == 1」**へ明文化し、
  全 env 据置の no-op record を拒否する ([T-529] 裁定 D の意図の明文化)。
- 既存で生きている関連裁定: **[T-529] 裁定 B(a)** = `DW-G04` を T-529 に限り上書きしない。
  **D196** = 活性化権限 (record からの権威導出 + 全入口 receipt) は historical resolver 配線より先に実装しない。
  **D176** = 契約世代機構は data 層だけ先に置き、bootstrap fuse で 2 世代目登録を拒否する。

## scope (P1 を含む)

- **単位 1 (docs):** 裁定 (a) の文言を decisions へ明文化する fragment を書く。
- **単位 2 (実装、(P1)):** `orchestrator/campaign/env_contract.py` へ、activation record の
  世代 mapping (env → generation) 間の遷移を判定する**純 data-layer 述語**を 1 本置き、
  `orchestrator/tests/test_env_contract.py` へ表駆動テストを 1 本足す。
  **権威導出・入口 receipt・fuse 除去・g2 登録は行わない。**

## 不変条件 (破ったら停止)

1. `ExecutionEnvironmentContract` / `_canonical_obj` / `contract_sha256` / `REGISTRY` /
   `GENERATIONS` / `lookup` / `is_valid_successor` / `validate_generations` の挙動と bytes を変えない。
2. bootstrap fuse を外さない。2 世代目の登録経路を作らない。
3. 新述語は **data であって権限ではない**。issuer の型 gate・活性化権限として使わない旨を docstring に書く。
4. env 固有 literal を `_build_registry` の外へ出さない (γ-16 の AST 検査)。
5. 正しさゲートを緩める方向の変異を採らない (規律 2)。既存テストを弱めない。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 単位 2 を今日 land してよい。** 根拠 = D176 の射程が「世代列が 1 本の間、隣接遷移の検査は
  production で一度も発火しない。純関数として test からのみ発火する」を明示的に許しており、
  裁定 B(a) / D196 が掛かるのは**権威導出と入口 receipt** であって、権威を主張しない述語ではない。
- **(P2) `DW-G05` の成果物影響が「今日はゼロ」でも実装してよい。** 実装しない場合に今日の
  certified 選択・レポート・試行台帳の値・受理集合・参照は 1 つも変わらない (production consumer が
  activation record を持たないため)。効くのは activation record 導入後であり、no-op record を
  受理すると contract が同一のまま activation 参照だけが分岐する。
- **(P3) 述語の signature は `Mapping[str, int]` の before/after 2 引数とし、env 集合の追加・削除を
  拒否する。** 新 env 登録時の遷移表現は本 wave では定義しない (裁定文言が「全 env の delta」を
  前提にしているため)。

## 前提実測 (親、本 worktree、read-only + 実編集即時復元)

| # | 実測 | 手段 |
|---|---|---|
| A | `activation_serial` / `activation_state_sha256` / `ActivationRecord` / `activation_record` は repo の Python に **0 件**。activation record は未実装 | `grep -rn --include=*.py` |
| B | `env_contract.py` へ public 関数を 1 本足しても `test_env_contract.py` + `test_silo_ladder_rung1_evidence.py` は **136 passed** (実編集 → `git checkout --` で復元、tree clean 復帰を確認) | `tools/run_tests.py` |
| C | `env_contract.py` の bytes を 64hex literal で pin する台帳・test は 0 件。identity 閉包 (`qualification/contract.py`) と runtime module binding (`silo_ladder_rung1.py`) はいずれも**実行時計算**で、B のとおり緑 | `grep` + B |
| D | baseline (無変更) の `test_env_contract.py` は **135 passed** | `tools/run_tests.py` |
| E | [T-529] 側の稼働 wave は**なし** (稼働 worktree = t139 / t474 / t609 / t619 / rulings)。重複なし | `git worktree list` |

## 既存被覆と純増検出力 (性質で検索した結果)

- 既存: `is_valid_successor` の表 (`no-op` 行) は **単一 env の contract 同一性**を拒否する。
  `validate_generations` は世代列の形・番号連続・cross-env hash 衝突を拒否する。
- **純増検出力:** 「**複数 env をまたぐ record 単位の世代 mapping** に対し、(i) 全 env 据置の no-op、
  (ii) skip (delta ≥ 2)、(iii) downgrade (delta < 0) を拒否する」検出力は現在 **0 件**。

## 成果物の形

コード 1 file (述語 1 本) + テスト 1 file (表駆動 1 本) + decisions fragment + worklog fragment +
`output/insights/2026-08-07_t624-activation-noop/` の逐語・変異台帳。

## 分割方針と検証子

`DW-C00` の軽量版条件に**該当しない** (正しさ防壁の設計に触り、述語の受理集合を定義する) ため、
敵対検証子を省かない。段 2 プラン 1 本、段 3 敵対 2 レンズ、段 5 実装子 1 本 (単位が 1 file 対で
分割不能なほど小さい)、段 6 レビュー 2 本 + fix。受入・実測は Pegasus login node から
`tools/run_tests.py` (dispatch 経由)。性能計測は行わない。
