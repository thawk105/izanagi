# [T-189] 段 4 裁定 + plan v2 + 変異事前登録

親が段 3 の 2 レンズ (A = 正しさ境界 / B = 実効性・変異帰属) の所見を real/refuted、採用/不採用、
scope 内/外へ裁定した。両レンズとも NO-GO。plan v2 は下記のとおり。

## 所見の裁定

| ID | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|
| A1 | 平坦な Codex 集合が `mini/none` を拒否し `mini/max` を admission する | **real** | **部分採用** | 過剰拒否側は「capability ではなく repo policy」と明示して解決。model×reasoning 対応表は **scope 外** (F56 恒久対応 (c)、所有は T-183/T-184) → 裁定パッケージ |
| A2 | 正本が `_supervisor_digest()` の閉包外に置かれ trust-root が漏れる | **real (blocker)** | **採用** | 正本の置き場所を `tools/dev_waves/effort_levels.py` へ変更 |
| A3 | F56 限界 insight が所有から脱落 | **real** | **採用** | insight は親の段 7 所有。内容を下記に事前登録 |
| A4 | 正例が `high`/`max` だけで 5 値の受理集合を固定できない | **real** | **採用** | 正例を全許可値で parameterize |
| A5 | `tools/task_runs/cli.py --reasoning` が無制限 | **real** | **不採用 (scope 外)** | 観測台帳であり拒否でなく requested/validity 分離が妥当という論点付きで裁定パッケージへ |
| A6 | profile 経路が拒否前に worktree/spec artifact を作る | **real** | **不採用 (nit → backlog)** | 成果物影響が `FAILED` wave の残骸に留まる |
| A7 | M1 は documented vocabulary であり実受理集合の実測ではない | **real** | **採用** | module docstring と insight の文言を是正 |
| B1 | 面 3 の単層変異を child E2E の証明にすると F28 を再発 | **real** | **採用** | 単層 API 変異と両層同時変異を**別枠**で事前登録 (`DW-M04`) |
| B2 | 「正本 1 箇所」は plan 後も成立しない | **real / 主張の縮小** | **部分採用** | 3 面が 1 正本を参照するのは真。role policy / 実験 arm / manifest / frontmatter / docs 条文は別集合として残る。**`launcher.py` と `spec.py` の集合 ⊆ 正本 の機械検査を追加**。manifest / frontmatter / docs 条文の束縛は裁定パッケージ |
| B3 | 3 面は実 Codex/Claude 経路を十分には守らない | **real** | **採用 (主張の縮小)** | レンズ B の択 2 を採る。成果物影響を正直に縮小し、真になる範囲を worklog / insight へ明記 |
| B4 | `test_dev_waves_cli.py` の plain runner が新テストを黙って飛ばす | **real (F42 型)** | **採用** | 新関数を `_run()` へ追加 |
| B5 | M6 は既存依存でなく `tools/dev_waves → codex_roles` の新規辺 | **real** | **採用** | A2 の解と同時に解消 |

## 親の追加実測 (裁定根拠)

- **M16** `_supervisor_digest()` は `Path(__file__).parent` = `tools/dev_waves/` を**非再帰 glob** し、
  `*.py` と `*.json` だけを hash する (`tools/dev_waves/daemon.py:179-186`)。
  よって `orchestrator/codex_roles/` 配下の新規 leaf は閉包外である → A2 は real。
- **M17** `trust_root()` が拾うのは `tools/check_*.py`、`tools/run_tests.py`、
  `tools/task_run_check.py`、`tools/task_runs/`、`orchestrator/tests/` だけ
  (`tools/dev_waves/git_state.py:801-830`)。`tools/dev_waves/` も
  `tools/codex_worker_launch.py` も git trust root の外である (既存事実、本 wave で悪化させない)。
- **M18** supervisor digest の**リテラル値を pin するテストは存在しない** (実測)。
  digest は run 内の before/after 等号比較にのみ使う (`daemon.py:1114,1211`)。
  よって `tools/dev_waves/` へ file を足しても既存期待値を壊さない。
- **M19** plain runner の型: `test_codex_worker_launch.py:1790` は `pytest.main` 委譲、
  `test_dev_waves_schema.py:319` は `globals()` の `test_*` glob、
  `test_dev_waves_cli.py:357` だけが**手列挙**。→ B4 は `test_dev_waves_cli.py` に限って real。
- **M20** `test_dev_waves_isolation_contract.py` はテスト直列化 group の契約であり、
  import 境界を禁じていない。面 1 が `tools.dev_waves` を import しても抵触しない。

## plan v2 (段 5 の実装契約)

### 正本の置き場所 — 段 2 案から**変更**

`orchestrator/codex_roles/effort_levels.py` (段 2 案) を**却下**し、
**`tools/dev_waves/effort_levels.py`** に置く。理由:

1. `_supervisor_digest()` の閉包 (`tools/dev_waves/*.py|*.json`) に**入る** (M16)。
   面 2・3 の受理集合が run 中に差し替えられれば digest が動き、checker が検出する。
   段 2 案では受理集合だけ変わって `supervisor_code_sha256` が同値のままになる (A2)。
2. `tools/dev_waves/` は現在 `orchestrator.*` を import していない (M11)。
   段 2 案は `tools/dev_waves → orchestrator.codex_roles` の新規辺を作り、
   `codex_roles/__init__.py` の eager import (spec / policy / review ledger) を
   dev_waves の standalone テスト収集へ持ち込む (B5)。本案はこの辺を作らない。
3. 面 1 (`tools/codex_worker_launch.py`) は既に `orchestrator.codex_roles.events` を import しており、
   どちらへ置いても新規辺が 1 本増える。面 1 自身は digest 閉包の外なので、
   置き場所を面 1 に合わせても integrity 上の利得がない。

module は **標準ライブラリのみに依存する leaf** とし、`tools/dev_waves/__init__.py` へ再 export しない。

### 集合の形

```python
CLAUDE_EFFORTS = ("low", "medium", "high", "xhigh", "max")
CODEX_REASONING_EFFORTS = ("low", "medium", "high", "xhigh", "max")
```

- `none` は含めない。repo 内に呼び出し実績がなく、値域を広げない不変条件に従う。
- **module docstring に次を必ず書く** (A1 / A7 / B3 の採用分):
  - この 2 定数は **izanagi の repo policy** であって、CLI の capability 集合の attest ではない。
  - `CLAUDE_EFFORTS` の出典は `claude --help` の**文書化された語彙**であり、実受理集合の実測ではない。
  - Codex の受理集合は **model 依存**である (F56: `gpt-5.4-mini` は `max` を拒否し `none` を受理)。
    本 gate は requested token だけを検査し、model×reasoning の対応も served model の identity も
    保証しない。その実装所有は T-183 / T-184 にある。
- model 別の絞り込みは本 wave では実装しない。

### 面 1 / 面 2 / 面 3

段 2 案のとおり。面 1・2 は `argparse` の `choices=`、面 3 は `_EFFORT_RE` の**後段**に membership を重ねる
(P2 維持)。ReasonCode は既存 `INVALID_ARGS` + `{"label": "effort", "kind": "unknown"}` を使い、新設しない。
`check-receipt --expect-reasoning` と `_validate_receipt` は変更しない (過去 receipt の監査互換)。

### 追加分 (段 3 の採用所見)

- **B2-partial**: `orchestrator/codex_roles/launcher.py:355` の `{low,medium,high,xhigh}` と
  `spec.py:610` の `{medium,high}` を、**値を変えずに** module 定数へ命名する。
  新規テストで両者が `CODEX_REASONING_EFFORTS` の**部分集合**であることを機械検査する。
  **集合を広げてはならない。**
- **A4**: 3 面の正例を許可集合の**全値**で parameterize する。
- **B4**: `test_dev_waves_cli.py` へ足した新関数を同ファイルの `_run()` へ登録する
  (`test_codex_worker_launch.py` / `test_dev_waves_schema.py` は自動収集なので不要、M19)。

### 成果物影響 (B3 採用により段 1 から縮小)

本 gate が守るのは次に限る。

- `codex_worker_launch.py run` の**新規 CLI 入力**としての requested reasoning token
- `dev_waves serve` の**新規 CLI 入力**としての effort
- 正規の `WorkerSpec` / child argv の **spawn 前 repo-policy 検査**

守らないもの (insight と worklog に明記する): `DW-O01` の生 `codex exec` 直接起動、
過去 receipt と `check-receipt`、`tools/task_runs` 台帳、`tools/codex_reasoning_ab.py` の arm、
model×reasoning 対応、served model identity、および D74 により未開放の real Claude 子。
面 2・3 は現時点で実 Claude 子を 1 本も守らない。今入れる価値は
**real 開放前に永続 spec / argv の契約を固定し、不正値を将来の正常 baseline にしないこと**である。

### 実装単位 (所有は素集合)

- **単位 A (先行)**: `tools/dev_waves/effort_levels.py` (新規)、
  `orchestrator/codex_roles/launcher.py`、`orchestrator/codex_roles/spec.py`、
  `orchestrator/tests/test_effort_levels.py` (新規)
- **単位 B**: `tools/codex_worker_launch.py`、`orchestrator/tests/test_codex_worker_launch.py`
- **単位 C**: `tools/dev_waves/cli.py`、`tools/dev_waves/schema.py`、
  `orchestrator/tests/test_dev_waves_cli.py`、`orchestrator/tests/test_dev_waves_schema.py`

A を完了させ、所有パス限定 patch を B・C の worktree へ展開してから B・C を並列投入する。

## 変異事前登録 (DW-M01 / DW-M04 / DW-M08)

各変異は「手前に同じ入力を拒否する検査がないこと」を段 3 レンズ B の前段検査表と親の M12 で確認済み。
期待赤 node は**直接呼び出しの単体テスト**に固定する (B1 採用。e2e では上流層が下流変異を mask する)。

### kill 変異 (受理集合が期待方向へ変わる)

| ID | 変異 | 期待赤 | 単一理由性の根拠 |
|---|---|---|---|
| V1 | 面 1 の `choices=CODEX_REASONING_EFFORTS,` を削除 | 面 1 の `none` 負例 | 手前は subcommand / required / token 検査のみ |
| V2 | 面 2 の `choices=CLAUDE_EFFORTS,` を削除 | 面 2 の `none` 負例 | 手前は required / token 検査のみ |
| V3 | `parse_worker_spec` の membership を削除 | `parse_worker_spec` 直接呼び出しの `none` 負例**のみ** | 手前は `_EFFORT_RE` だけで `none` を通す (M12) |
| V4 | `validate_child_argv` の membership を削除 | `validate_child_argv` 直接呼び出しの `none` 負例**のみ** | 同上 |
| V5 | **両層同時** (V3 + V4) | V3・V4 の期待赤に加え、`build_child_argv` 経由の E2E 負例 | 実 child の受理集合が変わった唯一の証拠 (DW-M04) |
| V6 | 正本へ `"none"` を追加 (過剰受理) | 面 1・面 3 の `none` 負例 | 正本が実際に参照されている証拠 |

### 過剰拒否を検出する正例変異 (DW-M01: 受理集合を縮小する wave の義務)

| ID | 変異 | 期待赤 |
|---|---|---|
| V7 | `CLAUDE_EFFORTS` から `"max"` を削除 | 面 2・面 3 の `max` 正例 |
| V8 | `CODEX_REASONING_EFFORTS` から `"max"` を削除 | 面 1 の `max` 正例 (live 経路の保護) |
| V9 | `CLAUDE_EFFORTS` から `"low"` を削除 | parameterize 正例の `low` ケース (A4 の検出力) |

### diagnostic sensitivity pin (kill に数えない、DW-M08 の別枠)

| ID | 変異 | 期待赤 |
|---|---|---|
| V10 | `parse_worker_spec` から `_EFFORT_RE` を外す | `HIGH` の kind が `string` → `unknown` へ変わる P2 保護テスト。受理集合は不変 |

### meta-test の検出力 (B2-partial)

| ID | 変異 | 期待赤 |
|---|---|---|
| V11 | `launcher.py` の命名済み集合へ `"ultra"` を追加 | subset meta-test |

## 裁定パッケージ (ユーザーへ返す。本 wave では実装しない)

1. **A1 / F56 恒久対応 (c) の残り**: model×reasoning の非対応組を起動前に落とす仕組み。
   `gpt-5.4-mini` × `max` は本 wave 後も admission される。所有は T-183 / T-184。
2. **A5**: `tools/task_runs/cli.py --reasoning` の扱い。観測台帳なので拒否でなく
   `requested_reasoning` と validity の分離が妥当という論点付き。
3. **B2 の残り**: `manifest.json` / `.claude/agents/*.md` frontmatter (13 件) /
   `docs/dev-wave/workers.md` の条文が正本の部分集合であることの機械束縛。
   現在 `check_docs.py` は節名と dispatch しか見ておらず、条文の `reasoning=max` を
   `ultra` に書き換えても検出されない。
4. **A6**: profile 経路で不正値が worktree / worker spec artifact を作った後に拒否される点の早期化。

## 段 5・6 を飛ばさない

実装を行うため通常遷移 `4→5→6→7→8→9` とする。
