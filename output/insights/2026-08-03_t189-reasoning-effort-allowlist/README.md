# [T-189] reasoning / effort 許可リストの機械強制 — 実装と限界

**wave**: `worktree-dev-wave-t189-reasoning-allowlist` / base `e0b9073` / 実装 commit `b971c46`
**受入環境**: Pegasus gen_S 計算ノード (`tools/run_tests.py` の自動 dispatch)
**ユーザー裁定**: [T-189] 択 (a) — 不正な reasoning 値の拒否 (許可リスト検証) だけ先に実装し、
served model の attest 経路が無い点 (F56) は実験の限界として明記する。model routing の比較実験は
本 wave の scope 外。

---

## 1. 何を実装したか

子起動 CLI の 3 面に、reasoning / effort の値域検査 (許可リスト) を入れた。

| 面 | 場所 | 変更前 | 変更後 |
|---|---|---|---|
| 1 | `tools/codex_worker_launch.py` の `--reasoning` | `required=True` のみ。任意文字列を受理 | `choices=CODEX_REASONING_EFFORTS` |
| 2 | `tools/dev_waves/cli.py` の `--effort` | `required=True` のみ。任意文字列を受理 | `choices=CLAUDE_EFFORTS` |
| 3 | `tools/dev_waves/schema.py` の `parse_worker_spec` / `validate_child_argv` | `_EFFORT_RE` の形検査のみ | 形検査の**後段**に membership |

許可集合の正本は `tools/dev_waves/effort_levels.py` の 2 定数
(`CLAUDE_EFFORTS` / `CODEX_REASONING_EFFORTS`、いずれも `low, medium, high, xhigh, max`)。
`none` は repo 内に呼び出し実績がないため含めない。

`orchestrator/codex_roles/launcher.py` の `{low, medium, high, xhigh}` と `spec.py` の
`{medium, high}` は **role manifest の policy 集合**であり capability 集合ではない。
値を変えずに命名だけを与え、正本の部分集合であることを機械検査する meta-test を足した。

## 2. 正本の置き場所 — 段 2 案を却下した理由

段 2 の codex プランは `orchestrator/codex_roles/effort_levels.py` を提案し、親の provisional 裁定
(P3) もそれを支持した。段 3 の敵対レビュー (レンズ A) が **blocker** として却下した。

`tools/dev_waves/daemon.py` の `_supervisor_digest()` は `Path(__file__).parent`
(= `tools/dev_waves/`) を**非再帰**に glob し、`*.py` と `*.json` だけを hash する。
この digest は run manifest に記録され、checker が run 内の before/after 等号で
`trust-root=pass` を出す。したがって許可集合を `tools/dev_waves/` の外へ置くと、
**受理集合だけが変わって `supervisor_code_sha256` が同値のまま**になる経路が残る。

加えて `tools/dev_waves/` は `orchestrator.*` を Python import しておらず、段 2 案は
`tools/dev_waves → orchestrator.codex_roles` の**新規依存辺**を作り、
`codex_roles/__init__.py` の eager import (spec / policy / review ledger) を dev_waves の
standalone テスト収集へ持ち込むことになる。

一方 `tools/codex_worker_launch.py` は既に `from tools.dev_waves.schema import ...` を
import しているため (`:41`)、正本を `tools/dev_waves/` へ置いても面 1 に新規辺は増えない。

## 3. この gate が守る範囲と、守らない範囲

**守る**:

- `codex_worker_launch.py run` の**新規 CLI 入力**としての requested reasoning token
- `dev_waves serve` の**新規 CLI 入力**としての effort
- 正規の `WorkerSpec` / child argv の **spawn 前 repo-policy 検査**
  (永続 profile 経由で不正値が入っても、child argv 構築で fail-closed になる)

**守らない (実験の限界。F56 の未実装部分)**:

- `DW-O01` が規定する生の `codex exec -c model_reasoning_effort=...` 直接起動。
  dev-wave の段 2 / 段 3 / 段 5 はこの経路を使っており、3 面のいずれも通らない。
- 過去 receipt と `check-receipt --expect-reasoning` (監査互換性のため意図的に据え置き)。
- `tools/task_runs/cli.py --reasoning` (観測台帳。値域検査なし)。
- `tools/codex_reasoning_ab.py` の arm (直接 `codex exec` 起動面。`max|high` に閉じた凍結実験)。
- **model×reasoning の対応**。F56 (c) のとおり Codex の受理集合は model 依存であり、
  `gpt-5.4-mini` は `max` を拒否し `none` を受理する。本 gate は平坦な集合しか見ないため、
  `gpt-5.4-mini` × `max` は本 wave 後も admission される。
- **served model の identity**。rollout receipt は**要求値の記録**であって attest ではない。

恒久対応の所有は T-183 (失敗分類) と T-184 (policy 採用) にある。

## 4. `max` の扱い — 段 1 実測が親の provisional 裁定を反証した

親は段 1 brief の (P1) で「許可集合は `{low, medium, high, xhigh, max}` とし、
`max` を許すのは codex 経路だけに限る」と provisional に裁定した。**段 1 の実測がこれを反証した。**

`claude --help` は `--effort <level>  Effort level for the current session
(low, medium, high, xhigh, max)` と表示する。**`max` は Claude 側でも文書化された正当値**であり、
codex 経路に限る理由がない。

`max` が live であることも確認した — `docs/dev-wave/workers.md` の `DW-S02` / `DW-S03` が
`reasoning=max` を規定し、本 wave の段 2・3・6 自身がその値で走った。
`launcher.py` の集合には `max` が無いため、brief の警告どおりそのまま流用すれば段 2 が落ちる。

ただし段 3 レンズ A の指摘どおり、**`claude --help` の記載は「文書化された語彙」であって
実受理集合の実測ではない**。`none`・大文字・前後空白について Claude が拒否・正規化・fallback の
どれを行うかは未実測である。この区別は正本 module の docstring に書いた。

## 5. 段 3 と段 6 の敵対レビューが何を止めたか

4 本のレビューはすべて NO-GO を返した。実装本体の欠陥は 0 件で、**止めたのは設計の置き場所と
テストの検出力**だった。

- 段 3 レンズ A: 正本が supervisor digest の閉包外 (§2)。平坦集合の model 依存性 (§3)。
- 段 3 レンズ B: 「正本 1 箇所」の主張が過大 (role policy / 実験 arm / manifest / frontmatter /
  docs 条文で計 7 層に散っている)。3 面が実 Codex/Claude 経路を十分には守らない (§3)。
- 段 6 レンズ R1: **正例テストが許可集合の定数自身を反復していた**。正本から値を 1 つ消すと
  テストの入力集合も同時に縮むため、消した値を一度も試さずに緑のままになる (test-data mask)。
  `build_child_argv` を通る E2E 負例が無い。
- 段 6 レンズ R2: 変異 11 件のうち 8 件が現状では帰属しない。`schema.py` の membership block が
  同一 bytes で 2 箇所あり、短い anchor では harness が `ANCHOR_ERROR` で止まる。
  面 1 の正例に `_run_case()` より手前の `assert reasoning in ...` があり、`max` 削除時に
  実 CLI を一度も起動せず終わる。
- 焦点再レビュー: fix 後の帰属を再判定し closed 14 / partial 2 / regressed 0。
  さらに**親が書いた変異 spec が段 4 の事前登録から逸脱している** (V6 を 2 件に分割、
  V9 の削除対象を `low` から `xhigh` へ変更) ことを blocker として指摘した。親は
  事前登録どおり V1〜V11 へ戻した。

## 6. 実測

すべて Pegasus gen_S 計算ノード、checkout = `worktree-dev-wave-t189-reasoning-allowlist`。

| 走 | request | 対象 | 結果 |
|---|---|---|---|
| 変更前 baseline | `878467.nqsv` | 対象 3 ファイル | 86 passed |
| 統合後 (fix 前) | `878496.nqsv` | 対象 6 ファイル | 216 passed / 4 skipped |
| fix 後 | `878507.nqsv` | 対象 8 ファイル (meta-test 含む) | 244 passed / 4 skipped |

## 7. 純増検出力

着手前、`orchestrator/tests/` に reasoning / effort の不正値拒否を検査するテストは **0 件**だった。
本 wave が足した検査はすべて純増である。ただし段 3 レンズ A の指摘どおり、
「関連テスト 0 件」と一般化するのは過大で、正確には
**「本 wave の 3 対象面に well-formed だが値域外の入力を与えるテストが 0 件」**である。
role policy と child argv grammar の既存検査は別に存在する。

## 8. 変異 matrix

`tools/mutation_harness.py` / `--runner-mode dispatch` / anchor は実装 commit `b971c46` に束縛。
事前登録は段 4 (`-verbatim/s4-adjudication.md`) で行い、spec は `mutation-spec.json`。

**結果: 11/11 KILLED、SURVIVED 0。** 台帳は `mutation-ledger.json` (初回) と
`mutation-ledger-v9-erratum.json` (V9 補正後)。

| ID | 種別 | 変異 | 結果 |
|---|---|---|---|
| V1 | negative | 面 1 の `choices=` を削除 | KILLED |
| V2 | negative | 面 2 の `choices=` を削除 | KILLED |
| V3 | negative | `parse_worker_spec` の membership を削除 | KILLED |
| V4 | negative | `validate_child_argv` の membership を削除 | KILLED |
| V5 | both-layers | V3 + V4 を同時適用 | KILLED (E2E node が両層同時でだけ赤) |
| V6 | negative | 正本の両定数へ `none` を追加 | KILLED (6 node) |
| V7 | positive | `CLAUDE_EFFORTS` から `max` を削除 | KILLED |
| V8 | positive | `CODEX_REASONING_EFFORTS` から `max` を削除 | KILLED (`[max]` が実 CLI 起動まで到達) |
| V9 | positive | `CLAUDE_EFFORTS` から `low` を削除 | 初回 MISMATCH → erratum で KILLED |
| V10 | negative | `_EFFORT_RE` を外す | KILLED (diagnostic sensitivity pin) |
| V11 | negative | `launcher.py` の policy 集合へ `ultra` を追加 | KILLED (subset meta-test) |

**V10 は kill に数えない。** 受理集合は変わらず、`HIGH` の診断 `kind` が `string` → `unknown` へ
変わるだけである。`DW-M08` に従い diagnostic sensitivity pin として別枠に記録する。

### V9 の erratum (初回結果は消していない)

初回走で V9 が `MISMATCH` になった。原因は**親の期待 node 登録漏れ**である。
`low` を消費する既存テスト `test_export_is_create_only_and_contains_only_sanitized_wal_view`
(profile `effort="low"` で実 supervisor wave を走らせる) が正当に赤くなるのに、
親は本 wave が追加したテストだけを列挙していた。新しい失敗型として台帳へ記録した。

同じ MISMATCH に `test_all_repo_policy_reasoning_values_are_accepted[xhigh]` も含まれていたが、
これは Codex 側定数を使う経路であり `CLAUDE_EFFORTS` の変異からは到達しえない。
rc も 1 (`invalid choice` の 2 ではない)。erratum 走では再現せず、`DW-O18` に従い
実装差分へ帰属させずフレークとして起票した。

## 9. 受入

すべて Pegasus gen_S 計算ノード、checkout = `worktree-dev-wave-t189-reasoning-allowlist`。

- **受入全走**: request `878534.nqsv` で `orchestrator/tests` 全体 **5244 passed / 19 skipped**、rc=0
- `python3 tools/check_docs.py` rc=0
- `python3 tools/check_ai_provenance.py` (既定 full history) rc=0、791 件・違反なし
