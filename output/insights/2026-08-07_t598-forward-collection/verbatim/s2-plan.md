# 段 2 実装プラン

推奨は、現 collector の report 生成を公開関数へ抽出し、専用 helper がその Python dict を envelope 化して repo 外へ create-only 保存する案である。P1/P2/P6 の方向は妥当だが、P3/P4/P5/P7を強化し、P8 は修正が必要である。

## 1. helper の設計

### collector の最小 refactor

現状は `tools/claude_session_ledger.py:905-1029` の `main()` 内で report を作り、`tools/claude_session_ledger.py:1014-1018` で JSON 化している。既存の `_empty_report()` (`:836-893`) は空の器しか返さないため、そのまま import しても収集できない。

`tools/claude_session_ledger.py:905` を起点に次の形へ抽出する。

```python
@dataclass(frozen=True)
class CollectionResult:
    report: dict[str, Any]
    exit_code: int
    as_json: bool
    strict: bool

def collect_report(argv: Sequence[str] | None = None) -> CollectionResult:
    ...
```

- 現行 `main()` の parse・収集部分を `collect_report()` へ移す。
- `main()` は `collect_report()` の結果を `json.dumps()` または `_render()` へ渡し、stderr と rc を処理する薄い CLI adapter にする。
- helper は次を import する。

```python
from claude_session_ledger import collect_report
```

実装後の定義位置は現行 `tools/claude_session_ledger.py:905` 付近、約 `:912` を見込む。helper は `collect_report()` が返した dict を直接使うため、collector JSON の `json.loads()` や subprocess 再実行は不要となる。schema version 2 と既存 CLI 出力は変えない。

純移動を除く追加は約25〜35行。

### 新規 helper

新規 path:

```text
tools/collect_claude_wave_usage.py
```

公開関数:

```python
def collect_wave_usage(
    *,
    wave_id: str,
    projects_root: Path | None,
    base_project: str,
    wave_project: str,
    cwd_contains: str,
    since: str,
    until: str,
    max_files: int,
) -> dict[str, Any]:
    ...

def main(argv: Sequence[str] | None = None) -> int:
    ...
```

想定配置:

- `:1-30` — bytecode 抑止付き import。`claude_session_ledger` の import 前に `sys.dont_write_bytecode = True` とし、既存 loader 問題を再発させない。
- `:31-70` — CLI parser、repo 外 path 検証、selector 検証。
- `:71-125` — `collect_wave_usage()`、status 判定、envelope 作成。
- `:126-160` — mode `0o600` の create-only writer と非 gate の `main()`。

CLI:

```text
--wave-id WAVE_ID             必須
--out OUT_JSON                必須。絶対 path、repo 外、既存でない file
--base-project BASE_PROJECT   必須
--wave-project WAVE_PROJECT   必須
--cwd-contains WORKTREE_NAME  必須
--since START_ISO8601         必須
--until END_ISO8601           必須
--max-files N                 必須
--projects-root PATH          任意。省略時は collector の既定
```

`--include-sidechains` と `--strict` は呼出側へ公開せず、helper が常に collector argv へ付ける。これにより「付け忘れ」という新しい偽ゼロ経路を作らない。`--max-files` は既定値を持たせず、手順側で `200` を明示する。

`--out` は `Path.resolve()` 後にも repo 配下でないことを検査し、既存 file は上書きしない。親 directory は helper が暗黙作成せず、呼出側が用意する。

### 出力 JSON schema

```json
{
  "artifact_type": "izanagi.dev-wave.claude-usage",
  "schema_version": 1,
  "wave_id": "string",
  "requested_population": {
    "projects_root": "string-or-null",
    "project_slugs": {
      "base": "string",
      "wave": "string"
    },
    "cwd_contains": "string",
    "since_inclusive": "string",
    "until_exclusive": "string",
    "max_files": 200,
    "include_sidechains": true,
    "strict": true
  },
  "collection": {
    "status": "complete | missing | incomplete | error",
    "collector_exit_code": "integer-or-null",
    "observed_zero": "boolean-or-null",
    "reasons": ["string"],
    "error": {
      "kind": "string",
      "message": "string"
    }
  },
  "ledger_report": "claude-session-ledger schema v2 object or null"
}
```

`collection.error` は正常時 `null`、`ledger_report` は collector 自体を呼べなかった `error` だけ `null` とする。collector が rc=2 を返しても partial report は捨てない。

helper 自身の rc は、selector 不足、collector rc=2、例外、出力失敗を含めて `0` とし、診断は stderr と、作成可能な場合は artifact に残す。`KeyboardInterrupt` などの process 制御例外までは握り潰さない。

helper 本体は約140〜165行。

## 2. 欠測判定

`report["population"]` と strict collector 結果から次の順で分類する。

```python
population = report["population"]

if population["files_scanned"] == 0:
    status = "missing"
elif (
    population["limit_reached"]
    or collection_result.exit_code != 0
    or any(report["issues"].values())
):
    status = "incomplete"
else:
    status = "complete"
```

意味は次のとおり。

- `missing`
  - `population.files_scanned == 0`。
  - 空の project directory、消えた wave slug、存在しない root、真に transcript がない場合を区別せず欠測へ倒す。
  - token/model call のゼロ値を観測値として採用しない。

- `incomplete`
  - `files_scanned > 0` だが `population.limit_reached == true`。
  - または strict issue / fatal issue が存在する。
  - `issues.missing_project` 単独でも、base 側を走査できていれば `missing` にはしないが、宣言した二つの project の一方を確認できないため `incomplete` とする。

- `complete`
  - 1 file 以上を走査し、打切りも issue もない。
  - このときだけ `ledger_report.combined` の `model_calls`、`tool_calls`、`raw_input_tokens`、`output_tokens` がすべて 0 なら `observed_zero=true` とする。それ以外は `false`。
  - `missing` / `incomplete` / `error` では `observed_zero=null`。

区別不能なケースが残る。

- 存在するが誤った project slugを指定し、その directory に別 transcript がある場合。
- 誤った `cwd_contains` がどの record にも一致しない場合。
- 正しい selector の対象に本当に request がない場合。

これらはいずれも `files_scanned > 0`、`limit_reached=false`、metric 0 になり得る。現 schema には「cwd filter に一致した record/file 数」がなく、`records_seen` は filter 前の件数なので区別には使えない。従って `observed_zero` は「指定された selector を正しいと仮定した範囲内の 0」であり、全体としての真の消費 0 とは主張できない。

## 3. `DW-S09` の契約行

現在の `docs/dev-wave/core.md:111` の後、次の空行の前へ1行だけ挿入する。

```text
wave 終了時の消費収集は `docs/README.md` に従う。
```

UTF-8/LFで、末尾改行込み **63 bytes**。

静的 byte 収支:

- 現在の4文書合計: 25,134 bytes
- 追加後: 25,197 bytes
- ceiling: 25,200 bytes
- 残り: 3 bytes
- `core.md` 単体: 8,584 → 8,647 bytes、個別上限9,600 bytes以内

したがって66 bytesを超えず、予算引上げや他節の縮約は不要である。後から文言を膨らませず、詳細はすべて `docs/README.md` に置く。

## 4. `docs/README.md` の追記

まず `docs/README.md:67-69` の「production consumer は未結線」を削除し、次へ置き換える。

```markdown
  `claude_session_ledger.py` = claude session transcript から model call と raw token 交通量を
  母集団付きで集計する read-only 台帳 (D206。費用・課金・利用枠ではない) /
```

次に現在の `docs/README.md:70` の後、`hooks/` 項目の前へ tools 項目の継続として次を置く。

```markdown
  **Claude 消費の wave 前向き収集 (D220):** `DW-O23` の結果確定後、最終報告前に次を 1 回だけ実行する。

  ```text
  python3 tools/collect_claude_wave_usage.py \
    --wave-id WAVE_ID \
    --out OUT_JSON \
    --base-project BASE_PROJECT \
    --wave-project WAVE_PROJECT \
    --cwd-contains WORKTREE_NAME \
    --since START_ISO8601 \
    --until END_ISO8601 \
    --max-files 200
  ```

  大文字の operand は実行時に明示する。`OUT_JSON` は既存でない repo 外の絶対 path とし、
  project slug と cwd selector を作業 directory から導出しない。sidechain と strict 判定は
  helper が常に有効にする。`collection.status` が `missing` / `incomplete` / `error`、
  または artifact を作れなかった場合も wave の gate にせず、既存 artifact は上書きしない。
  Pegasus の実行場所は `tools/README.md` と `docs/pegasus-runbook.md` §7.0 に従う。
```

tracked 文面には実在する機体固有 path、project slug、時間窓、wave IDを入れない。

## 5. テスト

新規 test file:

```text
orchestrator/tests/test_collect_claude_wave_usage.py
```

| nodeid | 殺す実装ミス |
|---|---|
| `orchestrator/tests/test_claude_session_ledger.py::test_public_collect_report_matches_cli_json_schema_v2` | 抽出した `collect_report()` と既存 `--json` CLI のschema・値がずれる変更を殺す。 |
| `test_collect_claude_wave_usage.py::test_helper_uses_public_collector_without_json_reparse` | subprocess 呼出しや `json.loads()` に戻して第2 consumer/parserを作る変更を殺す。 |
| `...::test_scanned_population_can_be_complete_observed_zero` | 1 file以上を完全走査した0を `missing` にする誤りと、cwd filterを渡し忘れる誤りを殺す。 |
| `...::test_zero_scanned_files_is_missing_not_observed_zero` | `model_calls == 0` をそのまま正常な消費0として保存する偽ゼロを殺す。 |
| `...::test_limit_reached_is_incomplete_with_partial_report` | `limit_reached` を無視してpartial metricをcompleteにする変更を殺す。 |
| `...::test_missing_wave_project_is_incomplete_not_missing` | base側にdataがあるのに `missing_project` だけで全体をmissingにする、またはissueを完全無視する変更を殺す。 |
| `...::test_fatal_collision_is_recorded_but_main_returns_zero` | collectorのrc=2をhelperから伝播してwaveをgate化する変更、またはfatal reportを捨てる変更を殺す。 |
| `...::test_missing_selector_never_falls_back_to_all_projects[base_project]` | base selector欠落時に全project走査へfallbackする変更を殺す。 |
| `...::test_missing_selector_never_falls_back_to_all_projects[wave_project]` | wave selector欠落を黙って許す変更を殺す。 |
| `...::test_missing_selector_never_falls_back_to_all_projects[cwd_contains]` | cwd selectorなしで広域集計する変更を殺す。 |
| `...::test_output_is_repo_external_and_create_only` | repo内出力、相対出力、既存artifact上書きを許す変更を殺す。 |

再利用対象:

- `_load_ledger()` — `orchestrator/tests/test_claude_session_ledger.py:20-32`。aliasを `_load_module` としてhelperのimport testにも使える。
- `_usage()` — `:38-46`
- `_assistant()` — `:49-82`
- `_write_jsonl()` — `:85-109`
- `_run_json()` — `:112-117`。公開 collector と既存 CLI のparity検査に使う。
- `_tree_snapshot()` — `:128-144`。既存file非上書きと予期しない `__pycache__` 作成の検査に使う。

pytestはread-only sandboxでは実走していない。親が `tools/run_tests.py` 経由で実行するまで緑とは扱わない。

## 6. 変異事前登録候補

| 変異 | 赤になるべき nodeid |
|---|---|
| missing 条件を `files_scanned == 0` から `combined.model_calls == 0` へ変更 | `test_scanned_population_can_be_complete_observed_zero`、`test_zero_scanned_files_is_missing_not_observed_zero` |
| `limit_reached` の分岐を削除 | `test_limit_reached_is_incomplete_with_partial_report` |
| strict結果と `issues` をstatus判定から削除 | `test_missing_wave_project_is_incomplete_not_missing` |
| collector argvから `--cwd-contains` を削除 | `test_scanned_population_can_be_complete_observed_zero` |
| `collect_report()` のimport呼出しをsubprocess + `json.loads()`へ置換 | `test_helper_uses_public_collector_without_json_reparse` |
| helperの戻り値を `collector_exit_code` に変更 | `test_fatal_collision_is_recorded_but_main_returns_zero` |
| selector欠落時に `--project` / `--cwd-contains` 無指定でcollectorを呼ぶ | `test_missing_selector_never_falls_back_to_all_projects[...]` |
| outputをcreate-onlyから `"w"` 書込みへ変更 | `test_output_is_repo_external_and_create_only` |

## 7. `tools/check_docs.py` への影響

静的には `check_docs.py` 自体の変更は不要。

- dev-wave予算:
  - 個別上限は `tools/check_docs.py:176-181`
  - aggregate ceilingは `:254`
  - byte算定・個別検査は `:3507-3555`
  - aggregate検査は `:3557-3562`
  - 63 bytes追加後も25,197/25,200なので範囲内。

- dispatch表の集合一致:
  - hard-coded stage/condition集合は `tools/check_docs.py:444-505`
  - command表との比較は `:3874-3915`
  - `DW-S09` のbodyへpointerを足すだけで、H2、段dispatch、条件dispatchの集合は変わらない。
  - `DW-S09` のland helper exact検査 `:3802-3828` にも影響しない。
  - 新helperは `docs/dev-wave/**` の新規referenceでも `tools/pegasus/**` のregistry memberでもないため、集合登録は不要。

- `tools/README.md`:
  - 上限登録は `tools/check_docs.py:185-187`
  - 現在2,989/3,000 bytesで余白11 bytes。
  - 今回は編集しないため予算に触れない。
  - `docs/README.md` は `all_limits` (`:3507-3514`) に含まれず、byte上限対象外。

ただし、これは「静的lintが赤くならない」という意味だけで、実行場所の分類を代替しない。P8の143.7 MiBは単一process RSSであり、`tools/README.md:11-23` と `docs/pegasus-runbook.md:374-403` が要求する全子孫cgroup charged-memoryの測定ではない。数値自体は否定しないが、`local-ok` の導出には使えない。ユーザー端末で正規測定されるまでは `unknown` とし、Pegasusでは計算ノード側で実行するか、収集を欠測として非gateで終える。

## 8. U-4 の置き場所

4条件の恒久正本は既に `docs/decisions.md:10396-10400` のD220決定5にある。ここへ重複追記しない。

元の但し書きは凍結済みの `docs/archive/worklog-phase3-0806-271.md:448-451` にあり、過去記録なので書き換えない。現在のactive itemは `docs/worklog.md:2687-2691` だが、canonical worklogも直接編集しない。

段7で次のworklog fragmentを作るのが正しい。

```text
docs/spool/worklog/2026-08-07-dev-wave-t598-forward-collection-1.md
```

- `## 本文` に、旧但し書きをD220決定5がsupersedeし、起票には `(a)` baseline完了、`(b)` exposureと比較可能な層別、`(c)` 効果量・分散に基づく事前n、`(d)` 欠測非相関の全条件が必要、と記録する。
- `## 次の一手差分` → `### 完了` で `[T-598]` を完了させる。
- `remaining: none` と、実装時に再計算した現行itemの `base:` digestを付ける。
- land時にfoldが新規worklog entryへ追記し、active T-598を閉じる。

D220が既に判断を保持しているため、U-4だけを理由に新しいdecisions fragmentを作る必要はない。

## 総括

推奨案は、公開 `collect_report()` を最小抽出し、`tools/collect_claude_wave_usage.py` が厳格selector付きreportをtyped envelopeへ包み、repo外へcreate-only保存する構成である。

変更を要するprovisional項目:

- **P3:** base/wave/cwd/time/max-filesを必須化し、sidechainとstrictはhelper内で固定する。
- **P4:** `files_scanned == 0` はmissing、打切り・issueはincomplete、完全走査時だけ`observed_zero`を判定する。誤っているが実在するselectorとの区別不能性を明記する。
- **P5:** `--out` 必須に加え、絶対path・repo外・create-onlyを機械強制する。
- **P7:** collector失敗だけでなくselector/config/output失敗も非gate化する。
- **P8:** 単一process RSSからのlogin-node `local-ok` 推論を撤回し、正規cgroup測定までは`unknown`とする。

総行数見積りは、純移動を除き **約445行（400〜485行）**。内訳はcollector refactor 25〜35行、helper 140〜165行、テスト210〜250行、core/README/worklog fragment 25〜35行である。