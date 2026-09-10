# 段 4 裁定 — [T-639] admission 縮小版の制度化

段 2 プランと段 3 レンズ A / B の全所見を real/refuted、採用/不採用、scope 内/外へ裁定する。

## 所見裁定表

| 所見 | 判定 | 採否 | scope | 根拠 |
|---|---|---|---|---|
| A1 非 pegasus `local-ok` が既存 deny を allow へ反転 | **real** | 採用 | 内 | `_SYNTHETIC_VALID_ENTRY` は `local-ok` であり、`pytest`/`cmake` を sanctioned 早期許可へ載せられる。受理集合を広げる方向で裁定 (縮小版) に反する |
| A2 既存防壁テストの削除・未列挙 | **real** | 採用 (ただし A1 の設計で**削除不要**になる) | 内 | 下記 v2 設計では `test_bash_pegasus_entry_lookup_rejects_registry_keys_outside_subtree`・negative corpus `outside-path`・`loader-outside-local-ok` の 3 本が**逐語のまま緑**になる |
| A3 / B1 `main()` 内部例外時に非 pegasus path が rc=0 で fail-open | **real** | 採用 | 内 | `_PEGASUS_RAW_MENTION_RE` は `tools/pegasus` しか見ない。fallback path を raw-mention 検出へ加える |
| A4 親の実測 3 からの過剰一般化 | **real** | 採用 | 内 | 実測が示したのは「非 pegasus key を登録できない」までで、`local-ok` 許可の必要性ではない |
| A5 変異事前登録に最危険変異が欠落 | **real** | 採用 | 内 | 下記 M2 / M4 / M10 を追加 |
| A6 / B3 cwd 相対・`python3 -c`・Codex 子・端末は塞がらない | **real** | **不採用 (実装しない)** | **外** | F121 / [T-518] の既知残穴。本 wave は「Claude Bash の parser が exact target と認識した綴り」に限ると明記し、裁定パッケージへ返す |
| B2 登録 key と実ファイルの結線欠落 | **real** | 採用 | 内 | 非 pegasus key の実在 meta-test を足す。pegasus 側は inventory テストが既に担保 |
| B4 `tools/README.md` の scope 文が stale になる | **real** | 採用 | 内 | 親 docs 所有へ追加 |
| B5 実測表 parser は非 pegasus 行を表現できない | **real** | 部分採用 | 一部外 | 今回は非 pegasus `local-ok`/実測 entry を**作らない**ので赤にならない。parser 一般化は将来の裁定パッケージへ |
| B6 brief の pin 記述が不正確 | **real** | 採用 (記録訂正のみ) | 内 | 「投影のみ」→「frozen pin なし。consumer は投影・canonical loader・literal golden」 |
| A5 の変異 1〜9 の帰属 | 帰属成立 | 採用 | 内 | レンズ A が恒真変異なしと判定。M2 / M4 / M10 を追加して 10 本にする |

## plan v2 (実装子への確定指示)

### 中核不変条件 — 受理集合は単調に縮む

**非 `tools/pegasus/` の registry entry は deny 側 class (`unknown` / `dispatch-required`) しか
取れない。** これを loader と hook wrapper と lookup の 3 層で強制する。この結果、本変更で
allow へ移る入力は 1 つも存在しない。

gate の禁止 (署名形):

```
拒否: load_admission_registry(repo_root) に
      entries[path]["class"] == "local-ok" かつ not path.startswith("tools/pegasus/")
      である path が 1 つでもあるとき → AdmissionRegistryError
通る正例: entries["tools/claude_session_ledger.py"]["class"] == "unknown" (受理される)
```

### 1. loader `tools/pegasus_admission_registry.py`

- `_is_canonical_repo_relative_path(path)` を新設: `str` かつ非空、`os.path.isabs` が偽、
  `/` 分割 component に `..` を含まない、後置 `/` なし、`\` なし、Unicode `Cc` なし、
  `os.path.normpath(path) == path`。
- `_validated_document()` の path 条件を
  「canonical repo 相対」かつ「`tools/pegasus/` 配下 **または** `entry["class"] != "local-ok"`」へ置換。
- 他 (4 field、class 閉集合、canonical bytes、並び順、size cap) は不変。
- path の実在検査は loader に入れない (loader は tmp fixture でも動く必要がある。実在は meta-test 側)。

### 2. hook `hooks/guard_bash.py`

- `_is_canonical_pegasus_path` を `_is_canonical_admission_path` へ一般化し、
  **wrapper postcondition でも非 pegasus `local-ok` を拒否**する (load 失敗 = 空 registry へ縮退)。
- 静的 fallback を追加する。正本ではなく loader 障害時の投影であるとコメントに明記する。

  ```python
  _NON_PEGASUS_ADMISSION_FALLBACK_PATHS = frozenset({"tools/claude_session_ledger.py"})
  ```

- `_pegasus_admission_entry(path)` の分岐順を固定する。
  1. `entry = registry.get(path)` があり、かつ (`tools/pegasus/` 配下 **または**
     `entry["class"] != "local-ok"`) なら entry を返す。
     ← この class 条件が defense-in-depth であり、registry を直接 patch する既存テスト
     `test_bash_pegasus_entry_lookup_rejects_registry_keys_outside_subtree` を**逐語のまま緑**に保つ。
  2. `path in _NON_PEGASUS_ADMISSION_FALLBACK_PATHS` → `_PEGASUS_UNREGISTERED`。
  3. `path == "tools/pegasus"` または `tools/pegasus/` 配下 → `_PEGASUS_UNREGISTERED`。
  4. それ以外 → `None`。
- `_SANCTIONED_PATHS` = `(_NON_PEGASUS_SANCTIONED_PATHS - 非 local-ok 登録 path
  - _NON_PEGASUS_ADMISSION_FALLBACK_PATHS) | {registry の local-ok path}`。
  **非 pegasus path を sanctioned へ入れる経路を作らない。**
  load 失敗時も同じ差し引きを適用する。
- **A3 / B1**: `main()` の内部例外 fail-closed 判定 (`_PEGASUS_RAW_MENTION_RE` の隣) に、
  fallback 集合の path を raw mention として加える。`tools/claude_session_ledger.py`、
  `tools.claude_session_ledger` (module 綴り) の双方に当てる。
- 診断文言: `tools/pegasus/` 配下の既存メッセージ書式は変えない (既存 pin を壊さない)。
  非 pegasus entry には admission 用の別文言を使う。

### 3. registry `tools/pegasus/admission_registry.json`

辞書順の正しい位置へ 1 件だけ追加する。

```json
"tools/claude_session_ledger.py": {
  "class": "unknown",
  "reason": "input caps and capped-input measurement are incomplete",
  "primary_gate": "hook deny pending admission evidence",
  "evidence": "unmeasured; unbounded input surfaces remain"
}
```

`tools/collect_wave_usage.py` は追加しない (自己 gate 済み、かつ `DW-S09` が段 9 で実行を要求する)。

### 4. テスト (実装子所有)

**変更を明示的に許可する既存期待値はこの 2 件だけである。**

- `test_bash_pegasus_execution_inventory_is_synchronized`: registry 側を `tools/pegasus/` key に
  絞って比較する (非 pegasus entry の追加で赤にならないようにする)。閉包は緩めない。
- entry 数の stale な固定数 (`24` 系) と、それに紐づく診断文言。

**逐語のまま維持する既存テスト (弱体化禁止)。**

- `test_bash_pegasus_entry_lookup_rejects_registry_keys_outside_subtree`
- negative corpus の `outside-path` case、loader fixture の `loader-outside-local-ok`
- `test_bash_login_rejects_unregistered_nested_pegasus_entry`
- `test_bash_sanctioned_pegasus_paths_are_derived_from_registry`

**新規テスト。**

- `test_pegasus_registry_loader_accepts_canonical_non_pegasus_path` (deny class のみ)
- `test_pegasus_registry_loader_rejects_non_pegasus_local_ok`
- `test_bash_registered_non_pegasus_unknown_site_matrix` (LOGIN/SUSPECT deny、OTHER/COMPUTE allow)
- `test_bash_unregistered_non_pegasus_path_remains_allowed` (**過剰拒否を検出する正例**)
- `test_bash_non_pegasus_fallback_set_matches_registry_projection` (drift meta-test)
- `test_bash_non_pegasus_registry_keys_exist_as_regular_files` (B2)
- `test_bash_main_internal_error_conservatively_rejects_non_pegasus_admission_mentions`
  (実 subprocess で exact rc=2。A3 / B1)
- `test_bash_non_local_registry_entry_overrides_sanctioned_path` (P4 衝突)
- `test_admission_non_pegasus_registry_entry_requires_projection_only` (check_docs 側)

### 5. docs (親所有、実装子は編集しない)

- `docs/pegasus-runbook.md` §7.0: 投影表へ ledger 行を辞書順で追加。admission 段落を
  「registry が exact 登録した path は配置場所を問わず 3 値 admission。未登録 deny の閉包は
  `tools/pegasus/` にだけ残る。**非 `tools/pegasus/` entry は deny class のみ**」へ改訂。
  load failure 時に fallback path も拒否することを追記。強制面が
  「Claude Bash の parser が exact target と認識した綴り」に限られることを明記 (A6 / B3)。
- `hooks/README.md`: 同じ射程文の同期。
- `tools/README.md`: 「`tools/pegasus/` 配下」と限定している 2 箇所を同期 (B4)。

## 変異事前登録 (`DW-M01`、10 本)

| # | 変異 (production 1 箇所) | 期待赤 node (単一理由) |
|---|---|---|
| M1 | loader の path 条件を `startswith("tools/pegasus/")` に戻す | `test_pegasus_registry_loader_accepts_canonical_non_pegasus_path` |
| M2 | loader の「非 pegasus は非 local-ok のみ」条件を削除 | `test_pegasus_registry_loader_rejects_non_pegasus_local_ok` |
| M3 | `_pegasus_admission_entry` の registry-first 分岐を旧 `return None` へ戻す | `test_bash_registered_non_pegasus_unknown_site_matrix` |
| M4 | lookup の class ガード (非 pegasus `local-ok` → `None`) を削除 | `test_bash_pegasus_entry_lookup_rejects_registry_keys_outside_subtree` |
| M5 | fallback literal から ledger 1 行を削除 | `test_bash_non_pegasus_fallback_set_matches_registry_projection` |
| M6 | fallback 分岐の返値を `_PEGASUS_UNREGISTERED` → `None` | registry failure matrix の ledger case |
| M7 | sanctioned 導出の非 local-ok 差し引きを削除 | `test_bash_non_local_registry_entry_overrides_sanctioned_path` |
| M8 | `tools/pegasus/` 未登録分岐を `_PEGASUS_UNREGISTERED` → `None` | `test_bash_login_rejects_unregistered_nested_pegasus_entry` |
| M9 | fallback 判定を `path.startswith("tools/")` へ拡大 | **正例** `test_bash_unregistered_non_pegasus_path_remains_allowed` |
| M10 | `main()` の raw-mention 検出から fallback path を外す | `test_bash_main_internal_error_conservatively_rejects_non_pegasus_admission_mentions` |

- **正例 (過剰拒否検出) = M9。** 受理集合を縮小する wave の義務 (`DW-M01`) を満たす。
- B2 の実在 meta-test は、production に対応する変異点がない (registry key 自体が対象) ため
  変異 matrix へ入れず、**親が `DW-O19` に従って registry key を実在しない canonical path へ
  一時変異させ、赤を実測**して diagnostic sensitivity として台帳へ記録する。

## 裁定パッケージ候補 (scope 外 real — 実装せずユーザーへ返す)

1. **強制面の残穴 (A6 / B3)**: cwd 相対綴り (`cd tools && python3 claude_session_ledger.py`)、
   `python3 -c`、wrapper script / subprocess 内部、Codex 子、ユーザー端末・IDE・cron は
   本 gate の対象外。F121 / [T-518] の既知残穴と同型。閉じるなら parser へ cwd を渡す設計か、
   tool 自身の site gate (F159 恒久対応と同型) の付与になる。**どちらも別裁定。**
2. **実測表 parser の一般化 (B5)**: `_check_admission_measured_table` の期待集合は
   `evidence == "runbook §7.0 実測"` で prefix 非依存だが、row parser は `tools/pegasus/` しか
   解析できない。将来ユーザーが非 pegasus tool を実測して `local-ok` を付けるとき、
   parser 一般化と「非 pegasus は deny class のみ」条件の緩和が同時に要る。
3. **他 tool の登録**: `tools/collect_wave_usage.py` ほかを registry へ載せるかは
   「分類完備は目指さない」裁定どおり見送り。[T-638] の測定手番が済んだ時点で再訪。

## 訂正 (B6)

brief の「registry bytes を pin するのは check_docs 投影のみ」は不正確。正しくは
**frozen artifact pin はない。consumer は (i) check_docs の投影表集合一致、(ii) loader の
canonical bytes 検査、(iii) `test_hooks.py` の literal golden の 3 つ**である。
いずれも実装子・親の所有内にあり、追加の pin 閉包は生じない。
