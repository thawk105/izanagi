# [T-244] P3 critic 後置 (U-8) — 段 6 レビュー裁定

両レンズとも **NO-GO**。ただし **U-8 の限定要求そのものは達成されている** (レンズ R2 が全分岐を
網羅して確認: production の critic 呼び出しは 1 箇所で、その前に必ず admission が確定する。
admission 前に critic を呼ぶ分岐は無い)。must-fix は例外境界の広がりと、変異・テストの検出力である。

## 裁定表

| 所見 | 判定 | 採否 | 成果物影響 |
|---|---|---|---|
| **R1-a / R2-a: 例外境界が広すぎる** — 仕様が try 外へ出すと決めたのは finalizer 例外だけなのに、critic 準備・provider lookup まで try 外に出た。critic を欠く provider 注入は、従来 `supervisor-error` partial だったのが report 不在 + lifecycle `indeterminate` になる | **real** | **採用 (must-fix F1)** | 同じ 1 世代入力の受理集合が「partial report あり」から「report 不在」へ変わる。未裁定の受理集合変更 |
| **R1-b / R2-b: pending 残留検査が発火不能** — 通常経路では helper が必ず pop するため、guard を削除しても観測差が出ない (恒真 gate) | **real** | **採用 (must-fix F2)** | proof chain が「消費漏れは専用 gate が検出する」と参照すると偽になる |
| **R2-c: M2 / M3 は指定 assert でなく completeness の別 gate に殺される。M3 は変異位置も 2 関数に分かれ非一意。M4 は v5 後の配置で位置が曖昧。M5 は kill node なし** | **real** | **採用 (must-fix F3)** | 変異台帳の kill 理由が偽になり、単一理由性の証拠が成立しない |
| **R2-d: 新設テストの値固定が不足** — 多世代テストは journal の exact 順を見ない (逆順でも緑)、direct pin は pending の長さしか見ない、build モードの invalid critic で positive admission 保持が未検査、順序テストは実 finalizer を丸ごと monkeypatch している | **real** | **採用 (must-fix F4)** | 順序・contract が変わっても境界テストが緑になる (false green) |
| **R1-c: 復元 cell の journal が `supervisor-error → critic → run-finish` になり、terminal event が `run-finish` 直前という要求に反する** | **real** | **採用 (仕様訂正のみ)** | cap=1 では到達不能 (harness 完了後に raise する経路が無いため pending は空)。cap-lift 時は fail-closed。v5 の「順序は壊れない」を「壊れるが fail-closed」へ訂正する。コード変更はしない |
| **R1-d: 多世代では critic reflux を捨ててから遅い fail-closed を行い、その前に proposal / WAL / Layer 3 が既に書かれている** | **real** | **scope 外 (裁定済みの帰結)** | 後置の不可避な帰結。cap-lift 時に還流をどう成立させるかは裁定パッケージ項目 2 で既にユーザーへ返している。新しい D へ明記する |
| **R1-e: partial でも positive Layer 3 material が公開される** | **real だが既存条件** | **scope 外 (A4、裁定パッケージ項目 3)** | 本 wave 前から全 cell が stop_reason に関わらず finalize される。本 wave は順序を変えただけで、材料の存在は変えていない。検出力だけ F4 で足す |
| **R1-f: generation-boundary wall の journal/report 不整合が transport の有無で非対称** | real だが**既存・差分起因でない** | **見送り (D205 の基準)** | 既存不整合。U-8 と独立 |
| R2-nit: finalizer failure test が fake の呼び出し回数を固定していない | nit | 見送り | — |

## fix 指示 (F1〜F4)

**F1. 例外境界を仕様どおりへ狭める。**
`_finish_trial` の workload ループで、`try` の外に置くのは **admission 確定 (finalizer) だけ**とする。
pending critic の処理 (digest 構築・`require_admitted_campaign`・provider lookup・`_invoke`) は、
**従来と同じ `supervisor-error` 回復境界の中**へ戻す。回復時は現行と同じく journal へ
`supervisor-error` event を書き、cell の `stop_reason` を `supervisor-error` にして break する。
`test_cell_admission_failure_is_not_converted_to_supervisor_error` は緑のままでなければならない。

**F2. pending 残留検査に発火経路と pin を与える。**
`admission_decision` を持ちながら pending も残る cell を注入できる seam
(既存 helper を直接呼ぶ wrapper で消費済み pending を cell へ戻す) で、
guard あり = 指定例外 / guard 削除 = private key が report へ流入して publish、を分ける
テストを新設する。テスト名は `test_residual_pending_critics_block_report_publish` とする。

**F3. 変異事前登録を再登録する (v3 §4 / v5 §3 を置き換える)。**

| # | 位置 | 変異 | 期待 kill node | 単一理由性 |
|---|---|---|---|---|
| M1 | workload ループ内の二相処理 | finalize と critic 呼び出しの順を交換 | `test_build_cell_admission_precedes_critic_invocation` | レンズ R2 が kill 成立を確認済み |
| M2' | critic invalid 分岐の `stop_reason` 代入 | 代入を削除 | **helper を直接呼ぶ新設テスト** `test_pending_critic_phase_sets_role_invalid_directly` | completeness を介さないため別 gate に殺されない |
| M3' | 同分岐の優先順位 | 初期 `converged` を後勝ちにする | **同上の direct テスト**の別 assert | 変異位置を 1 関数へ限定し、completeness を経由しない |
| M4' | `status` 代入の位置 | 二相処理より前へ移す | `test_post_admission_invalid_critic_marks_cell_role_invalid` | **`status` 代入が normal / fallback の両 helper 呼び出しより後にあることを AST で構造 pin するテストを併設**して位置を一意化する |
| M5' | pending 残留 guard | guard を削除 | `test_residual_pending_critics_block_report_publish` (F2 で新設) | F2 が発火経路を作るので kill 成立する |

**F4. 新設テストの値固定を強める。**
- 多世代テスト: journal の `(generation, role)` tuple 列を exact に検査し、
  critic payload の generation 列が `[1, 2]` であることを固定する (逆順で緑にならないように)。
- direct pin: pending record の **exact key 集合 (5 個)** と既知値を検査する。
- **build モードの invalid critic テストを追加**し、critic invalid 後も
  `admission_decision` が positive のまま残ることを検査する。
- 順序テスト: 実 `_finalize_build_cell_admission` を残したまま `layer3_report.render` 側を fake にし、
  実 finalizer 本体を no-op にする変異が緑にならないようにする。
  これが fixture 上不可能なら、その理由を docstring と報告に書き、緑と偽らない。

## 仕様訂正 (親)

v5 §2 の「復元 cell は最後なので順序は壊れない」は誤り。正しくは
**「復元 cell が完了済み pending を持つ場合、journal は `supervisor-error → critic → run-finish` となり
terminal event 要求に反するため fail-closed になる。cap=1 では到達不能」**である。
新しい D へこの限界を明記する。
