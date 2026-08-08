# 段 2 実装プラン

指定資料はすべて読了した。以下は静的検査に基づくプランであり、テスト・分類実測は一切実行していない。P1〜P4 はそのまま採用し、`tools/**` の prefix 閉包は導入しない。

## 受理集合の before / after

例示する登録済み非 Pegasus path は、今回 `unknown` で追加する `tools/claude_session_ledger.py`。現状は正規 registry に追加できず、強制追加すると loader 全体が失敗するため、「現行」は実際の `decide()` 結果を示す。

| registry 状態・入力例 | 現行 LOGIN | 現行 SUSPECT | 現行 OTHER | 変更後 LOGIN | 変更後 SUSPECT | 変更後 OTHER |
|---|---:|---:|---:|---:|---:|---:|
| 登録予定の非 Pegasus `python3 tools/claude_session_ledger.py --scan` | allow | allow | allow | **deny (`unknown`)** | **deny (`unknown`)** | allow |
| 未登録非 Pegasus `python3 tools/unregistered_for_admission.py` | allow | allow | allow | allow | allow | allow |
| 登録済み Pegasus `unknown` (`collect_receipt.py`) | deny | deny | allow | deny | deny | allow |
| 登録済み Pegasus `dispatch-required` (`exec_calibrate.py`) | deny | deny | allow | deny | deny | allow |
| 登録済み Pegasus `local-ok` (`fetch_third_party.py`) | allow | allow | allow | allow | allow | allow |
| 未登録 `tools/pegasus/future/nested.py` | deny | deny | allow | deny | deny | allow |
| registry load 失敗時の `claude_session_ledger.py` | allow | allow | allow | **deny (静的 fallback)** | **deny (静的 fallback)** | allow |
| registry load 失敗時の任意 `tools/pegasus/*`（既存 local-ok を含む） | deny | deny | allow | deny | deny | allow |
| registry load 失敗時の未登録非 Pegasus path | allow | allow | allow | allow | allow | allow |

`PEGASUS_COMPUTE` は `OTHER` と同じく admission 判定を行わず allow のままにする。

既存 deny が allow へ移らない根拠は次のとおり。

- 現行 JSON の全 Pegasus entry の class と受理 bit は変更しない。
- `tools/pegasus/` の未登録 sentinel 分岐を残す。
- 新規 entry は `unknown` であり、許可集合ではなく拒否集合だけを増やす。
- P4 の sanctioned 差し引きは許可集合を縮める方向にしか作用しない。
- 非 Pegasus の未登録 path は引き続き管轄外 `None`。`tools/**` 閉包にはしない。
- 将来、正本 JSON に非 Pegasus `local-ok` を追加すればその exact path は許可対象になり得るが、本 wave ではそのような entry を追加しない。

## 編集面

### 1. loader の path domain 一般化

[tools/pegasus_admission_registry.py:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/tools/pegasus_admission_registry.py:69)

- L69 の直前に private helper `_is_canonical_repo_relative_path(path)` を追加する。
- helper は以下をすべて要求する。

  - `str` かつ空でない。
  - `os.path.isabs(path)` が偽。
  - `/` 区切り component に `..` がない。特に `../x` は `normpath` だけでは排除できないため独立条件にする。
  - 後置 `/`、`\`、Unicode category `Cc` を含まない。
  - `os.path.normpath(path) == path`。`./`、二重 slash、途中の `.` / `..` を拒否する。

- `_validated_document()` L86–102 の `path.startswith("tools/pegasus/")` 条件を helper 呼び出しへ置換する。
- entry の四 field、class 閉集合、canonical JSON bytes、並び順の検査は変更しない。
- path の実在検査や `tools/` prefix 要求は加えない。認可対象は正本 JSON に exact key として登録されたものだけとする。

### 2. hook の registry 投影・fallback・sanctioned 衝突

[hooks/guard_bash.py:175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/guard_bash.py:175)

- L189–194 の sanctioned 定数の隣に、P2 専用の静的投影を追加する。

```python
_NON_PEGASUS_ADMISSION_FALLBACK_PATHS = frozenset({
    "tools/claude_session_ledger.py",
})
```

- この集合は正本ではなく、loader 障害時の fail-closed 用投影であることをコメントに明記する。

[hooks/guard_bash.py:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/guard_bash.py:197)

- `_is_canonical_pegasus_path()` を `_is_canonical_admission_path()` に改名し、loader と同じ canonical repo-relative 条件へ一般化する。
- L233–244 の wrapper postcondition は新 helper を使い、canonical な非 Pegasus key を受理する。field/class の二重検証は維持する。

[hooks/guard_bash.py:246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/guard_bash.py:246)

- 正常 load 時は次の二集合を導出する。

  - `local_ok_paths`: registry の `class == "local-ok"`。
  - `non_local_paths`: registry の `class != "local-ok"`。

- `_SANCTIONED_PATHS` は次の形にする。

```python
(_NON_PEGASUS_SANCTIONED_PATHS - non_local_paths) | local_ok_paths
```

- これにより sanctioned と非 `local-ok` entry が衝突しても、load 時点で sanctioned 側から消える。
- load 失敗時の sanctioned 集合も、将来の fallback 衝突で fail-open しないよう
  `_NON_PEGASUS_SANCTIONED_PATHS - _NON_PEGASUS_ADMISSION_FALLBACK_PATHS`
  とする。現行二本には fallback path が含まれないため、現在の sanctioned bit は変わらない。

[hooks/guard_bash.py:563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/guard_bash.py:563)

`_pegasus_admission_entry()` の分岐順を次に固定する。

1. `_PEGASUS_ADMISSION_REGISTRY.get(path)` があれば、prefix を問わず entry を返す。
2. path が `_NON_PEGASUS_ADMISSION_FALLBACK_PATHS` にあれば `_PEGASUS_UNREGISTERED` を返す。
3. `path == "tools/pegasus"` または `tools/pegasus/` 配下なら `_PEGASUS_UNREGISTERED`。
4. それ以外は `None`。

これにより正常時の非 Pegasus exact entry と、load 失敗時の静的 fallback の双方が既存の admission 判定へ流れる。

[hooks/guard_bash.py:1082](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/guard_bash.py:1082)  
[hooks/guard_bash.py:1130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/guard_bash.py:1130)

- admission 判定の位置は sanctioned 早期許可より前のまま動かさない。
- L1155–1157 の診断文だけ、非 Pegasus entry にも正しくなるよう「Pegasus 実行体」から「admission 実行体」へ一般化する。
- `_script_targets()`、`_baseline_first_token_violation()`、`_executor_output_violation()` は一般化した lookup を既に呼ぶため、構造変更しない。

### 3. 正本 registry への一件追加

[tools/pegasus/admission_registry.json:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/tools/pegasus/admission_registry.json:3)

辞書順で既存 Pegasus entry より前へ次を追加する。

```json
"tools/claude_session_ledger.py": {
  "class": "unknown",
  "reason": "input caps and capped-input measurement are incomplete",
  "primary_gate": "hook deny pending admission evidence",
  "evidence": "unmeasured; unbounded input surfaces remain"
}
```

`legacy-admitted` や実測済みを示す evidence は使わない。`tools/collect_wave_usage.py` は追加しない。

### 4. hook / loader テスト

[orchestrator/tests/test_hooks.py:1278](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/orchestrator/tests/test_hooks.py:1278)

既存 fixture・golden の変更:

- `_PEGASUS_EXPECTED_CLASSES` と `_PEGASUS_EXPECTED_ENTRIES` に新 entry を追加する。
- stale な「24 entry」診断は固定数を消すか、変更後の 29 entry に合わせる。
- `_PEGASUS_DIRECT_COMMANDS` は comprehension により新 path を自動取得させる。
- `expected_local_evidence` は現行五本のままにし、新 entry が local-ok/legacy へ紛れないことを固定する。
- `_assert_failed_registry_is_closed()` は新 direct command も LOGIN/SUSPECT で deny するため、既存の全 loader/JSON failure parameter が P2 の縮退検査になる。
- `_PEGASUS_REGISTRY_FAILURES` と `_LOADER_FIXTURE_SOURCES` の `loader-outside-local-ok` は、非 Pegasus canonical path が合法になるため削除する。wrapper postcondition の負例は absolute path を返す `loader-absolute-local-ok` へ置換する。
- `_negative_registry_bytes()` / `_NEGATIVE_REGISTRY_CASES` から `outside-path` を除き、`leading-parent`、`trailing-slash`、`backslash` を追加する。absolute、途中 `..`、二重 slash、制御文字は維持する。
- `test_bash_pegasus_execution_inventory_is_synchronized()` L2181–2204 は registry 側を `tools/pegasus/` key に絞って比較する。非 Pegasus 全体の閉集合検査へ拡張しない。

新規 test 関数:

- `test_pegasus_registry_loader_accepts_canonical_non_pegasus_path`
  - tmp registry に `tools/claude_session_ledger.py` を単独登録し、loader が同一 mapping を返すことを検査。
- `test_bash_registered_non_pegasus_unknown_site_matrix`
  - 実 registry の ledger path が LOGIN/SUSPECT で deny、OTHER/COMPUTE で allow。
- `test_bash_unregistered_non_pegasus_path_remains_allowed`
  - `tools/unregistered_for_admission.py` が LOGIN/SUSPECT/OTHER で allow。P1 の過剰拒否検出用正例。
- `test_bash_non_pegasus_fallback_set_matches_registry_projection`
  - fallback 集合と、実 registry のうち `tools/pegasus/` 外の key 集合が完全一致。
- `test_bash_non_local_registry_entry_overrides_sanctioned_path`
  - synthetic loader が `tools/run_tests.py = unknown` を返す fixture を作る。
  - load 後に同 path が `_SANCTIONED_PATHS` から消えていることを検査。
  - テスト内で sanctioned 集合へ一時的に同 path を再注入しても、LOGIN/SUSPECT の admission が先に deny することを検査。
  - OTHER は allow として過剰拒否も検査。
- 既存 `test_bash_login_rejects_unregistered_nested_pegasus_entry` は変更せず、Pegasus prefix 閉包の回帰検出器として残す。

### 5. check_docs の投影挙動テスト

[orchestrator/tests/test_check_docs.py:980](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/orchestrator/tests/test_check_docs.py:980)

新規 `test_admission_non_pegasus_registry_entry_requires_projection_only` を追加する。

1. synthetic registry に canonical な非 Pegasus `unknown` entry を辞書順で追加する。
2. docs 無変更では admission finding が投影表の集合不一致一件だけになることを検査する。
3. 投影表へ `(path, class, evidence)` 行を追加すると admission finding がゼロになることを検査する。
4. unknown 表、実測表、README 宣言表は変更しない。

[tools/check_docs.py:2290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/tools/check_docs.py:2290) 自体は編集しない。

## check_docs 投影検査への影響

| 検査面 | 非 Pegasus `unknown` entry だけを正本へ追加 | 根拠 |
|---|---|---|
| runbook 投影表 | **赤** | `_check_admission_projection()` L2676–2685 は全 registry entry の `(path,class,evidence)` と集合完全一致を要求 |
| runbook unknown 表 | 赤にならない | `_check_admission_unknown_table()` L2707–2708 は `tools/pegasus/` 外の row を registry 検査対象から除外し、unknown 全件掲載も要求しない |
| runbook 実測表 | 赤にならない | `_check_admission_measured_table()` L2776–2780 の期待集合は evidence が完全一致で `runbook §7.0 実測` の entry だけ |
| `tools/pegasus/README.md` 宣言表 | 赤にならない | `_check_admission_readme()` は掲載済み row の registry 整合を検査するが、registry 全 key の掲載は要求しない。path scanner も `tools/pegasus/` 専用 |
| `tools/pegasus/README.md` 本文/fence | 赤にならない | `_ADMISSION_PATH_RE` L2305–2309 が `tools/pegasus/...` だけを抽出 |

実装子が JSON を変更し、親 docs がまだ入っていない時点では、`test_real_repo_clean` と `tools/check_docs.py` に期待される admission finding は「runbook §7.0 投影表が registry と集合完全一致しない」の一件である。それ以外の finding は回帰として扱う。

## 親が行う docs 編集

実装子は次を編集しない。

[docs/pegasus-runbook.md:424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/docs/pegasus-runbook.md:424)

- L424–429 を「registry が exact 登録した path は配置場所を問わず三値 admission」「未登録 deny の prefix 閉包は `tools/pegasus/` にだけ残る」と改訂。
- L433–435 の load failure 説明へ、「全 `tools/pegasus/` と静的 fallback に載る登録済み非 Pegasus path を拒否」を追記。
- L441–442 の grandfather 四本限定は維持。
- 投影表 L448–477 に ledger の `(unknown, unmeasured; unbounded input surfaces remain)` 行を辞書順で追加。
- unknown 表と実測表には行を追加しない。

[hooks/README.md:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/README.md:78)

- L79 の「`tools/pegasus/` 配下の admission」を「registry に exact 登録された path の admission」へ変更。
- 未登録 deny は `tools/pegasus/` 配下だけ、load failure 時は静的 fallback の非 Pegasus path も deny、と明記。
- JSON が唯一の正本であり、fallback は障害時投影であることを明記。

[tools/pegasus/README.md:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/tools/pegasus/README.md:17) は編集しない。同表は当該 README が言及する `tools/pegasus/` 実行体の宣言表であり、全 registry key の inventory ではない。

## meta-test が恒真でない根拠

### P2 fallback drift

`test_bash_non_pegasus_fallback_set_matches_registry_projection` は、JSON loader 由来の集合と hook 内の静的 literal という独立二表現を比較する。

- JSON だけに非 Pegasus entry を追加すると meta-test が赤。
- fallback constant だけを増減しても赤。
- fallback を正常 registry から動的導出して恒真化しても、loader failure fixture では registry が空になるため `_assert_failed_registry_is_closed()` の ledger deny が赤になる。
- fallback lookup 分岐を消しても同じ failure matrix が赤になる。

### P4 sanctioned 衝突

`test_bash_non_local_registry_entry_overrides_sanctioned_path` は synthetic registry と既存 sanctioned literal の衝突を実際に作る。

- sanctioned 差し引きを削除すると `_SANCTIONED_PATHS` 非包含 assert が赤。
- admission 判定を sanctioned 早期許可の後ろへ移すと、テストが再注入した衝突 path が allow になり decision assert が赤。
- class を `local-ok` へ変えると deny assert が赤。
- OTHER allow も同時に置くため、「安全側」の名目で全 site を deny する実装も赤になる。

## 変異事前登録候補

1. loader の canonical 条件を `path.startswith("tools/pegasus/")` に戻す  
   → `test_pegasus_registry_loader_accepts_canonical_non_pegasus_path` が赤。

2. loader/helper の `".. not in path.split('/')"` を削除する  
   → negative corpus の `leading-parent` case が赤。

3. `_pegasus_admission_entry()` 冒頭に旧来の非 Pegasus `return None` を戻す  
   → `test_bash_registered_non_pegasus_unknown_site_matrix` が赤。

4. fallback literal から `tools/claude_session_ledger.py` 一行を削除する  
   → `test_bash_non_pegasus_fallback_set_matches_registry_projection` と loader failure matrix が赤。

5. fallback path 分岐の返値を `_PEGASUS_UNREGISTERED` から `None` に変える  
   → registry failure matrix の ledger case が赤。

6. sanctioned 導出の `- non_local_paths` を削除して単純 union に戻す  
   → `test_bash_non_local_registry_entry_overrides_sanctioned_path` の集合 assert が赤。

7. `tools/pegasus/` 未登録分岐を `_PEGASUS_UNREGISTERED` から `None` に変える  
   → `test_bash_login_rejects_unregistered_nested_pegasus_entry` が赤。

8. 非登録 fallback 判定を `path.startswith("tools/")` へ広げる  
   → 正例 `test_bash_unregistered_non_pegasus_path_remains_allowed` が赤。

9. JSON の ledger class 一行を `unknown` から `local-ok` に変える  
   → literal golden と `test_bash_registered_non_pegasus_unknown_site_matrix` が赤。

## 実装単位

一単位で足りる。loader・hook・JSON・literal golden・failure fixture が相互依存し、テストファイルを分けると共有 fixture 所有が衝突するためである。

Codex `role=author` の所有集合:

- `tools/pegasus_admission_registry.py`
- `hooks/guard_bash.py`
- `tools/pegasus/admission_registry.json`
- `orchestrator/tests/test_hooks.py`
- `orchestrator/tests/test_check_docs.py`

親の docs 所有集合は `docs/pegasus-runbook.md` と `hooks/README.md` で、上記と素集合。`tools/check_docs.py` と `tools/pegasus/README.md` は非編集とする。

親は統合後、少なくとも上記新規 nodeid、関連テスト二ファイル、`tools/check_docs.py`、`tools/check_codex_agents.py`、所定の全受入・変異 matrix を実走する。分類の性能実測は実施対象に含めない。

## 総括

- exact 登録された非 Pegasus path だけを admission 対象へ加え、未登録 `tools/**` は従来どおり allow に残す。
- 新規 ledger entry は `unknown` で、正常時・loader 障害時とも LOGIN/SUSPECT の拒否集合だけを増やす。
- 最大リスクは静的 fallback と JSON の drift、および sanctioned 衝突であり、独立 meta-test と failure fixture で固定する。
- 親の残作業は docs 二ファイルの同期と実走検証。現時点で追加裁定が必要な未決事項はない。