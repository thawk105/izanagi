# 段 2 実装プラン

指定資料はすべて読了できた。以下は親 brief の (P1)「CR/LF のみ」と (P2) の reason 語をそのまま採用する。ファイル変更・pytest 実走は行っておらず、緑は主張しない。

## 編集ハンク

### 1. `read_blob_at` の入口拒否

対象: [orchestrator/campaign/s8c_preregistration.py:960](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t714-evidence-path-ctrlchar/orchestrator/campaign/s8c_preregistration.py:960)

挿入位置: 関数先頭、現行 963 行の `root = ...` より前。少なくとも 965 行の `spec` 構築と 966 行の Git batch 入力より前に置く。

```python
if isinstance(path, str) and ("\r" in path or "\n" in path):
    raise PreregistrationError("path-control-char")
```

意図:

- path 中の U+000D/U+000A だけを caller 非依存で拒否する。
- `isinstance` を付け、非文字列入力の既存挙動をこの変更で別 reason に変えない。
- path を Git の行指向 `--batch-check` 入力へ渡す前に止め、末尾 CR の CRLF 終端化・埋め込み LF の要求分割を防ぐ。
- 生 path は例外 detail に入れない。

### 2. `_safe_path` の明示的な path 専用拒否

対象: [orchestrator/campaign/s8c_preregistration_evidence.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t714-evidence-path-ctrlchar/orchestrator/campaign/s8c_preregistration_evidence.py:183)

挿入位置: `_safe_path` の先頭、現行 184 行の `_nonempty_string` 呼出しより前。

```python
if isinstance(value, str) and ("\r" in value or "\n" in value):
    raise EvidenceContractError("contract-path-control-char", repr(where))
path = _nonempty_string(value, where=where)
```

意図:

- trailing CR/LF も既存の付随的 `contract-string` ではなく、新しい `contract-path-control-char` で拒否する。
- 埋め込み CR/LF は `strip()` では落ちないため、この明示検査が検出主体になる。
- `where` は診断位置として残すが `repr()` で単一行化する。拒否対象の `value` は message に入れない。
- 後続の `PurePosixPath` による absolute、`..`、非 canonical path の `contract-path` 判定は変更しない。

`_nonempty_string` 自体は変更しない。ここへ CR/LF 検査を入れると、path 以外の `artifact_kind`、`field_paths`、`reachable_from`、`entrypoints`、`negative_control_id`、`proof`、`static_only_note` まで新しく拒否し、(P1) の scope を越える。

### 3. core の実 Git 回帰テスト

対象: [orchestrator/tests/test_s8c_preregistration_core.py:947](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t714-evidence-path-ctrlchar/orchestrator/tests/test_s8c_preregistration_core.py:947)

既存の limit 複合テストの直前へ、独立した次のテストを追加する。

- `test_read_blob_at_rejects_trailing_cr_without_aliasing`
- `test_read_blob_at_rejects_embedded_path_control_chars[embedded-cr]`
- `test_read_blob_at_rejects_embedded_path_control_chars[embedded-lf]`

`_init_repo`、`_write`、`_commit` を使った tmp Git repository を使う。詳細は「テスト計画」に示す。

### 4. evidence contract loader の回帰テスト

対象: [orchestrator/tests/test_s8c_preregistration_predicates.py:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t714-evidence-path-ctrlchar/orchestrator/tests/test_s8c_preregistration_predicates.py:180)

既存の contract loader 検査直後へ、`CONTRACT_FILE` を JSON object として読み、path field だけをメモリ上で差し替えるテスト群を追加する。JSON は `json.dumps()` で再直列化し、JSON 構文エラーではなく `_safe_path` まで確実に到達させる。

## caller 閉包

### `read_blob_at` の全 caller

| callsite | path の由来 | 新拒否の発火可能性 |
|---|---|---|
| `s8c_preregistration.py:987` `parse_preregistration_at` | `SOURCE_PATH` | 定数なので発火しない |
| `s8c_preregistration.py:1487` `_module_blob` | wrapper 引数 | 下記 2 caller は定数なので発火しない |
| `s8c_preregistration.py:1555` `_module_blob(..., CORE_MODULE_PATH)` | `CORE_MODULE_PATH` | 発火しない |
| `s8c_preregistration.py:1556` `_module_blob(..., EVALUATOR_MODULE_PATH)` | `EVALUATOR_MODULE_PATH` | 発火しない |
| `s8c_preregistration.py:1561` `_activation_report_at` | `SOURCE_PATH` | 発火しない |
| `s8c_preregistration.py:1712` `prepare_revision` | `generation_path(...)` | 発火しない |
| `s8c_preregistration_evidence.py:376` `_ConditionProbe.read_kind` | 契約の `RequiredEvidence.path` | loader を経れば `_safe_path` が先に拒否。手組み dataclass・将来 caller が loader を迂回しても `read_blob_at` が拒否 |
| `s8c_preregistration_evidence.py:677` `PredicateRegistry.evaluate_all` | `EVIDENCE_CONTRACT_PATH` | 定数なので発火しない |
| `test_s8c_preregistration_invariant.py:143` | `generation_path(...)` | テスト専用、発火しない |
| `test_s8c_preregistration_invariant.py:154` | `EVIDENCE_CONTRACT_PATH` | テスト専用、発火しない |
| `test_s8c_preregistration_core.py:978` | `"large.bin"` | テスト専用、発火しない |
| `premise_probe.py:28` | probe の可変 path | CR/LF ケースで新 reason が発火する意図どおりの経路 |

repository-wide の symbol 検索では以上が全参照である。公開関数なので未知の外部 caller は静的列挙できず、そのため検査を `read_blob_at` 自身に置く。

### `_safe_path` と loader の全 caller

`_safe_path` の production caller は次の 2 箇所だけである。

- `s8c_preregistration_evidence.py:223`: `required_evidence[*].path`
- `s8c_preregistration_evidence.py:250`: `consumer_requirement.path`

probe の直接 caller は `premise_probe.py:43`。既存テストからの直接 caller はない。

`load_contract_bytes` の下流は次のとおり。

- `s8c_preregistration_evidence.py:268` `semantic_contract_sha256`: 新しく無効となる CR/LF path 契約では `EvidenceContractError` を伝播する。正常契約の hash は不変。
- `s8c_preregistration_evidence.py:688` `PredicateRegistry.evaluate_all`: error を捕捉し、従来の predicate reason `evidence-contract-invalid` で 12 件とも `ERROR` にする。
- predicate tests の 68、169、178、380 行: 現行契約または既存負例。現行契約には CR/LF path がないため非発火。

### `EvidenceRef` までの流れ

`EvidenceRef` の production 構築は 2 箇所だけである。

- `s8c_preregistration_evidence.py:379`: `_safe_path` 済みの required-evidence pathを 376 行で読み、blob が存在した場合だけ構築する。loader が迂回されても `read_blob_at` の第二防壁が先に拒否するため、CR/LF path の `EvidenceRef` は作られない。
- `s8c_preregistration_evidence.py:684`: `EVIDENCE_CONTRACT_PATH` 定数から契約自身の ref を構築する。新拒否は発火しない。

`consumer_requirement.path` は現状、型付き契約へ格納された後の production consumer がない。それでも schema 上の path であり、将来利用時に不正値を持ち越さないよう loader で拒否する。

### 定数経路の確認

- `SOURCE_PATH` (`s8c_preregistration.py:34`) は固定 ASCII 相対 path。
- `EVIDENCE_CONTRACT_PATH` (`:37-39`) は固定 ASCII 相対 path。
- `EVALUATOR_MODULE_PATH` (`:40`) と `CORE_MODULE_PATH` (`:41`) も固定 ASCII 相対 path。
- `generation_path` (`:991-996`) は検査済み正整数を固定 ASCII template に埋めるだけで、CR/LF は生成しない。
- 現行 evidence contract の path 値にも CR/LF はない。

したがって既存の source、evaluator、contract、freeze generation の定数経路は新拒否で壊れない。

## 例外型・reason・message

既存慣行は次のとおり。

- `PreregistrationError` (`s8c_preregistration.py:114-119`) は固定 reason を `.reason` に保持し、任意 detail を message にだけ加える。
- `EvidenceContractError` (`s8c_preregistration_evidence.py:43-48`) は同型で `.reason_code` を保持する。
- reason は lowercase kebab-case。今回も brief 指定どおり `path-control-char` と `contract-path-control-char` を使う。
- `repr(number)` など、防護的な文字列化を既に用いる箇所がある。

注意点:

- `read_blob_at` は現在、965 行で生 path を `spec` に入れ、970、973、977 行の既存 message に流しうる。新検査を必ずそれより前へ置く。
- `path-control-char` は detail なしで投げ、生 path を message に含めない。
- `contract-path-control-char` は `repr(where)` だけを detail にし、対象 path 自体は含めない。
- テストでは reason 属性に加え、`str(exc)` に実際の `"\r"` / `"\n"` が存在しないことも固定する。
- `ReasonCode` enum / `REASON_CODES` は predicate 結果用である。今回の parser 例外 reason を追加しない。invalid contract は既存の `evidence-contract-invalid` へ写像されるため、12 述語の reason 値域は変わらない。

## テスト計画

### core: 実 Git alias と埋め込み制御文字

`test_read_blob_at_rejects_trailing_cr_without_aliasing`:

1. `_init_repo(tmp_path)` で repository を作る。
2. `_write(root, "alias-target.txt", b"sentinel\n")` と `_commit(...)` で実 blob を commit する。
3. 正例として `read_blob_at(..., "alias-target.txt") == b"sentinel\n"` を確認する。
4. `"alias-target.txt\r"` は bytes を返さず `PreregistrationError` になることを確認する。
5. `.reason == "path-control-char"`、message に実 CR/LF がないことを確認する。

`test_read_blob_at_rejects_embedded_path_control_chars` は次の 2 parameter ID とする。

- `[embedded-cr]`: `"alias-\r-target.txt"`
- `[embedded-lf]`: `"alias-\n-target.txt"`

各 case で実 repository の有効 commit を渡し、`.reason == "path-control-char"` と単一行 message を確認する。

### evidence loader: 明示検査の識別

`test_contract_loader_rejects_embedded_path_control_chars` は次の 4 nodeid とする。

- `[required-cr]`
- `[required-lf]`
- `[consumer-cr]`
- `[consumer-lf]`

各 case では `CONTRACT_FILE` を `json.loads` し、C01 の `required_evidence[0].path` または `consumer_requirement.path` を `"dir/in\rside.py"` / `"dir/in\nside.py"` に差し替える。

各 candidate について事前に `candidate == candidate.strip()` を assert する。これにより `_nonempty_string` の既存 `value != value.strip()` では拒否されない入力だと固定する。その後:

- `load_contract_bytes` が `EvidenceContractError` を投げる。
- `.reason_code == "contract-path-control-char"`。
- message に実 CR/LF がない。

検査順を固定する追加 nodeid:

- `test_contract_loader_reports_explicit_path_reason_for_trailing_controls[trailing-cr]`
- `test_contract_loader_reports_explicit_path_reason_for_trailing_controls[trailing-lf]`

C01 required path の末尾に CR/LF を付け、既存の `contract-string` ではなく `contract-path-control-char` が出ることを確認する。これは guard が `_nonempty_string` より後へ移動する変異を殺す。

正例:

- `test_contract_loader_accepts_normal_relative_paths`

C01 の required path と consumer path をそれぞれ `"nested/evidence.py"`、`"nested/consumer.py"` に置換して load し、同値の path が型付き契約に残ることと `semantic_contract_sha256` が生成できることを確認する。

runtime 統合:

- `test_registry_rejects_control_char_contract_before_evidence_ref_construction`

埋め込み LF の required path を持つ契約を `_init_repo` / `_write` / `_commit` で commit し、registry 結果が 12 件すべて `ERROR`・`evidence-contract-invalid` で、evidence ref は安全な `EVIDENCE_CONTRACT_PATH` だけであることを確認する。

### 既存回帰

親の実測対象として、少なくとも次を維持する。

- `test_s8c_preregistration_predicates.py::test_predicate_registry_is_exactly_c01_through_c12`
- `test_s8c_preregistration_predicates.py::test_current_repository_gap_reason_snapshot_requires_cross_wave_review`
- `test_s8c_preregistration_predicates.py::test_contract_semantic_hash_ignores_formatting_but_not_values`
- `test_s8c_preregistration_core.py::test_evidence_contract_hash_is_semantic_canonical_json`
- `test_s8c_preregistration_core.py::test_recorded_revision_is_accepted_and_ruling_is_checked_at_revision_commit`
- `test_s8c_preregistration_core.py::test_effective_requires_all_twelve`
- `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`

契約 JSON、freeze record、hash algorithm、12 述語 evaluator、既存 assert は一切変更しない。実走は親が `tools/run_tests.py` 経由で行い、この段では結果を緑と記録しない。

## 変異事前登録

production だけを書き換え、テストは固定する。

| # | file:line | 変異 | 最初に落ちるべき nodeid |
|---|---|---|---|
| M01 | `s8c_preregistration.py:960-965` | CR/LF guard を削除 | `test_read_blob_at_rejects_trailing_cr_without_aliasing` |
| M02 | 同上 | CR だけを検査し LF 条件を削除 | `test_read_blob_at_rejects_embedded_path_control_chars[embedded-lf]` |
| M03 | 同上 | LF だけを検査し CR 条件を削除 | `test_read_blob_at_rejects_trailing_cr_without_aliasing` |
| M04 | 同上 | reason を `blob-missing` に変更 | `test_read_blob_at_rejects_trailing_cr_without_aliasing` |
| M05 | 同上 | exception detail に生 `path` を追加 | `test_read_blob_at_rejects_embedded_path_control_chars[embedded-lf]` の単一行 message assert |
| M06 | `s8c_preregistration_evidence.py:183-188` | `_safe_path` の新 guard を削除 | `test_contract_loader_rejects_embedded_path_control_chars[required-cr]` |
| M07 | 同上 | guard を `_nonempty_string` の後へ移動 | `test_contract_loader_reports_explicit_path_reason_for_trailing_controls[trailing-cr]` |
| M08 | 同上 | CR だけを検査し LF 条件を削除 | `test_contract_loader_rejects_embedded_path_control_chars[required-lf]` |
| M09 | 同上 | reason を既存 `contract-path` に変更 | `test_contract_loader_rejects_embedded_path_control_chars[required-cr]` |
| M10 | 同上 | detail に生 `value` を入れる | `test_contract_loader_rejects_embedded_path_control_chars[required-lf]` の単一行 message assert |
| M11 | `s8c_preregistration_evidence.py:223` | required path の `_safe_path` を `_nonempty_string` に置換 | `test_contract_loader_rejects_embedded_path_control_chars[required-cr]` |
| M12 | `s8c_preregistration_evidence.py:250` | consumer path の `_safe_path` を `_nonempty_string` に置換 | `test_contract_loader_rejects_embedded_path_control_chars[consumer-cr]` |

## 異論・残余観測

(P1)/(P2) の実装方向に異論はない。CR/LF だけを拒否するため NUL・tab・その他制御文字の既存挙動は残るが、これは裁定済み scope 境界であり本 wave では一般化しない。

## やらないこと

- NUL、tab、その他制御文字の拒否
- `ruleops.py` の同型欠陥（別タスク `[T-510]`）
- `_nonempty_string` 全体への制御文字検査
- evidence contract JSON、freeze artifact、docs の編集
- 既存テスト期待値の緩和
- commit
- この read-only 段での pytest 実走や緑の報告

実装後の静的確認は、差分が上記 4 ファイルだけであること、AST 構文解析、caller 再検索、`git diff --check` までとする。

## 総括

- `read_blob_at` は Git 入力前、`_safe_path` は `_nonempty_string` 前に CR/LF を明示拒否する。
- reason は brief 指定の 2 語に固定し、生 path を例外 message に出さない。
- 定数 path と正常契約は非発火で、動的 evidence path だけが新たに fail-closed になる。
- 実 Git alias、両 caller、正例、12 述語・semantic hash・freeze 回帰をテストで固定する。