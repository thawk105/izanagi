# 段 6 レビュー裁定 (2026-08-18 14:33 JST、親)

レビュー A (5 所見) / レビュー B (6 所見) とも NO-GO。親が裁定する。

## real・採用 (fix 対象)

| # | 出所 | 所見 | 担当 |
|---|---|---|---|
| F1 | A-1 | 負の対照が `_arm_execution_authorizes_reason_drop` を monkeypatch するため、実装を `return True` へ変える変異を殺せない (**恒真ガード**) | fixB |
| F2 | A-2 | pairwise / descriptor の 2 対照が `parse` しか呼ばず report・journal を協調整合させないため、対象 gate 以外の拒否で赤になる (単一理由性なし) | fixB |
| F3 | A-5 | 逆射影が `input_schema_version` を期待値なしで pop する | fixB |
| F4 | B-1 | `origin_terminal_projection` が v2 で許可されながら parsed 型へ保持されず再照合もされない | fixB |
| F5 | A-3 | C02 評価器が名前と文字列の存在だけを見てデータフローを要求しない。`_live_nodes` が `if True: return` 後を打ち切らない | fixA |
| F6 | A-4 / B-2 | メタ検査が chain の先頭 hop しか検査せず、非 identifier root と別 module root を黙って skip する | fixA |
| F7 | B-3 | U3 の docs 更新範囲が不足 (measurement HEAD の記述、§3 の arm 要約、evaluator 数 6、§7 の anchor 説明) | 親 (U3) |
| F8 | B-4 | U3 生成後に並行 wave が先行 land した場合の race 手順が未定義 | 親 (裁定訂正) |

## GO と確認された面 (レビュー B)

- 公開定数・型・allowlist の live caller は全件 v2 / legacy へ追随済み
  (`MANDATORY_NON_CERTIFYING_REASONS`、`SCHEMA_VERSION`、`LEGACY_SCHEMA_VERSION`、
  `AcceptanceReceipt`、`VerifiedAcceptanceReceipt`、`AcceptanceSummary`、`DECIDER_VERSION`、
  `MACHINE_CHECKABLE_CONDITION_IDS`、`SATISFIABLE_CONDITION_IDS`、`NEGATIVE_CONTROL_CASES`)。
- 新規 test file の自走 harness は `test_plain_runner_coverage.py` の自動発見に乗る。
- C03/C07/C08 を scope 外に残す裁定と、非機械条件をメタ検査対象外にする実装は整合している (B-5、GO)。
- SATISFIED を返す evaluator 経路は無く、allowlist 外の SATISFIED は ERROR 化され、
  receipt の `certifying=True` は構造的に拒否される (A 総括で確認)。

## F5 の scope — データフロー要求は限定する

完全なデータフロー解析は評価器を脆くする。**採る形を限定する。**

- namespace を構成する f-string が、当該関数の `return` の値であること
  (直接 return するか、return される名前へ代入されていること) を要求する。
  「計算はするが使わない」実装を落とすのはこれで足りる。
- `_live_nodes` は `if <literal true>: return` の後続を dead として打ち切る。
- 完全な束縛解決 (alias 追跡) は**採らない**。scope 外として裁定パッケージへ書く。

## F6 の形 — 「検査しない」も exact に pin する

chain 内の全 token を 3 分類し、**3 集合すべてを exact pin** する。

1. `checked` — 当該 module の AST に実在を要求した `(condition, path, name)`。
2. `excluded` — 非 identifier root (例: C04 の `run_trial crash handler`) や
   別 module root (例: C10 の `assert_trial_registry_acceptance`) を、**除外理由付きで** pin する。
3. `missing` — 実在しない名前。空でなければ赤。

分類できない token が 1 つでも出たら赤にする (fail-closed)。黙って通過する経路を残さない。

## F8 の訂正 — 「1 回」は確定 main snapshot ごと

段 4 裁定 §5 を次に訂正する。

- 世代 record の発行は **確定した main snapshot 1 つにつき 1 回**である。
- U3 生成後に並行 wave が先行 land して land が stale になった場合、
  **自 wave が生成した record を成果集合から外し**、新 main を統合したうえで
  次世代を**再生成**し、受入を再走する。
- 相手の世代 record を通常 merge で取り込むことはしない (全履歴を走る不変検査が落ちる)。
- 生成済み record を持ち越して merge しない。

## 変異事前登録の追補 (`DW-M01`)

段 4 §9 の 13 件に次を足す。

| ID | 位置 | 期待 |
|---|---|---|
| `t822.m14-reason-drop-always-true` | `_arm_execution_authorizes_reason_drop` を `return True` へ | KILLED (F1 の裏取り) |
| `t822.m15-namespace-unused` | namespace f-string を計算するが return しない形へ | KILLED (F5 の裏取り) |
| `t822.m16-meta-exclusion-silent` | メタ検査の除外集合 pin を外す | KILLED (F6 の裏取り) |
| `t822.m17-origin-projection-unbound` | `origin_terminal_projection` の再照合を外す | KILLED (F4 の裏取り) |

`t822.m14` は F1 が閉じたことの直接の検定である。fix 前は SURVIVED するはずであり、
fix 後に KILLED へ変わることを確認する。

## 3 巡上限 (`DW-O16`)

本 fix が 1 巡目。所見ごとの closed / partial / regressed 対応表を要求する。
NO-GO が続いても 3 巡を上限とし、それ以降は親が変異で裏取りして real/refuted を裁定して閉じる。
