# 方針

以下の行番号は編集前の現行スナップショット基準である。

provisional P1 はそのまま採用しない。`tools/pegasus/admission_registry.py` を新設すると、[test_hooks.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_hooks.py:1223) の inventory が拡張子 `.py` を無条件に実行体と数え、25 entry 目になって「24 entry 不変」と衝突するためである。

| 裁定 | 採否 | プラン本体 |
|---|---|---|
| P1 | 変更 | JSON は `tools/pegasus/admission_registry.json`、共有 loader は inventory 外の `tools/pegasus_admission_registry.py` に置く。`tools/pegasus/__init__.py` は作らない |
| P2 | 採用・具体化 | runbook に全24件の `(path, class, evidence kind)` 投影表を置き、JSON と集合完全一致させる |
| P3 | 強化 | legacy 例外では registry の evidence prefix だけでなく、unknown 表の該当行に `local-ok` と正確な evidence を明記させる |
| P4 | 採用・強化 | direct/qsub 判定を実装し、Pegasus path を含むが静的に分類不能な command は無視せず赤にする |
| P5 | 採用 | 孤立行を unknown 表へ戻し、孤立した table row 自体も checker で赤にする |

# 新設ファイルの完全仕様

## `tools/pegasus/admission_registry.json`

形式は次の v1 schema とする。

```text
Document:
{
  "schema_version": "pegasus-admission-registry/v1",
  "entries": {
    <Path>: <Entry>,
    ...
  }
}

Path:
  - JSON string
  - POSIX の repo-relative path
  - 必ず "tools/pegasus/" で始まる
  - 空 segment、"."、".."、backslash、絶対 path を禁止
  - Unicode code point 順で昇順
  - v1 は exact 24 keys

Entry:
{
  "class": <Class>,
  "reason": <NonBlankString>,
  "primary_gate": <NonBlankString>,
  "evidence": <EvidenceString>
}

Class:
  "local-ok" | "dispatch-required" | "unknown"
```

物理形式も validator の契約に含める。

- UTF-8、BOM なし。
- 改行は LF のみ。
- 2-space indent、`ensure_ascii=False` 相当。
- top-level key 順は `schema_version`, `entries`。
- entry key 順は `class`, `reason`, `primary_gate`, `evidence`。
- path key は辞書順。特に `.pbs` は対応する `.py` より先。
- duplicate key、NaN/Infinity、追加 field、欠落 fieldを拒否。
- trailing whitespace なし、末尾は exact 1 LF。
- canonical serializer は次と同値にする。

```python
json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
```

24件の値は [guard_bash.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/hooks/guard_bash.py:183)〜328から、class 定数だけ文字列へ展開して移す。`reason`、`primary_gate`、`evidence` は一文字も変更しない。

この仕様での期待値は次で固定する。

- entry 数: 24
- class 数: `local-ok=5`, `dispatch-required=10`, `unknown=9`
- canonical bytes: 6,358 bytes
- SHA-256: `2a5712dbeb78d76c3ff56d39ca02f35bccbe26f9731decdcbff94519b1dfe5e0`

digest が違った場合は digest を更新して通さず、移送時の文字差を調べる。

## `tools/pegasus_admission_registry.py`

新規 module の公開面は次の4点だけに絞る。

```python
REGISTRY_RELATIVE_PATH = "tools/pegasus/admission_registry.json"

class AdmissionRegistryError(ValueError):
    ...

def evidence_kind(evidence: str) -> str:
    ...

def load_admission_registry(repo_root: str | Path) -> dict[str, dict[str, str]]:
    ...
```

`evidence_kind()` の写像は次で固定する。

- `legacy-admitted` で始まる → `legacy-admitted`
- exact `runbook §7.0 実測` → `runbook-measured`
- `static ` で始まる → `static`
- `unmeasured` で始まる → `unmeasured`
- それ以外 → `AdmissionRegistryError`

実装順は、raw bytes 読取、UTF-8 decode、duplicate-aware JSON parse、schema・path・class・evidence kind 検査、canonical bytes 再生成との一致確認、の順とする。全24件を検査し終わるまで返却用 mapping を公開せず、部分成功を返さない。ファイル不在、symlink/非 regular、decode/parse/schema/canonical 違反はすべて `AdmissionRegistryError` に正規化する。

外部 JSON Schema ファイルは増やさない。schema 正本はこの validator と `schema_version` であり、entry データの正本は JSON だけとする。

# 実装単位 A：JSON・loader・hook

## `hooks/guard_bash.py`

1. [guard_bash.py:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/hooks/guard_bash.py:49) 付近に `importlib.util` を追加する。

2. [guard_bash.py:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/hooks/guard_bash.py:58)〜69の `_repo_root()` と `_BOOTSTRAP_ROOT` は維持する。registry の探索に cwd、環境変数、現在の worktree path を使わない。

3. [guard_bash.py:179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/hooks/guard_bash.py:179)〜328の literal `_PEGASUS_ADMISSION_REGISTRY` 全体を、次の all-or-nothing loader に置換する。

```python
def _load_pegasus_admission_registry(repo_root: str) -> tuple[dict, str | None]:
    # <repo_root>/tools/pegasus_admission_registry.py を
    # spec_from_file_location で exact path import
    # load_admission_registry(repo_root) を呼ぶ
    # 成功: (registry, None)
    # BaseException/SystemExit を含む失敗: ({}, diagnostic)
```

module import 時の `.pyc` 書込みを避けるため、既存 `_check_spool_guard` と同様に `sys.dont_write_bytecode` と `sys.modules` を try/finally で復元する。loader import 自体の `SystemExit(0)` も許可へ倒さない。

```python
_PEGASUS_ADMISSION_REGISTRY, _PEGASUS_ADMISSION_REGISTRY_ERROR = (
    _load_pegasus_admission_registry(_BOOTSTRAP_ROOT)
)
```

4. [guard_bash.py:330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/hooks/guard_bash.py:330)〜339は構造を維持する。

```python
_SANCTIONED_PATHS = frozenset(
    _NON_PEGASUS_SANCTIONED_PATHS
    | {
        path for path, entry in _PEGASUS_ADMISSION_REGISTRY.items()
        if entry["class"] == _PEGASUS_LOCAL_OK
    }
)
```

別の local-ok 表は作らない。load 失敗時は registry が空なので、Pegasus 由来 path はゼロ、`tools/run_tests.py` と `tools/check_ai_provenance.py` は残る。

5. [guard_bash.py:596](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/hooks/guard_bash.py:596)〜604の `_pegasus_admission_entry()` は prefix fallback を維持する。空 registry でも全 `tools/pegasus/**` が `_PEGASUS_UNREGISTERED` になることが重要である。

6. [guard_bash.py:1176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/hooks/guard_bash.py:1176)〜1183では、unregistered sentinel かつ `_PEGASUS_ADMISSION_REGISTRY_ERROR` がある場合だけ、拒否理由を「registry 読込不能」にする。判定 bit は通常の未登録と同じ DENY のまま。

失敗時の実経路は次になる。

```text
loader import/read/schema/unknown-class 失敗
  → registry = {}
  → _SANCTIONED_PATHS = 非 Pegasus 2本のみ
  → tools/pegasus/** は _PEGASUS_UNREGISTERED
  → _script_targets() が target として保持
  → _heavy_segment_violation() が sanctioned 判定より前に拒否
  → LOGIN / SUSPECT では main() が rc=2
```

[guard_bash.py:1631](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/hooks/guard_bash.py:1631)〜1637の汎用例外 handler に頼ってはならない。`tools/pegasus/` は `_MENTION_RE` の防護対象語ではないため、loader 例外をそこまで漏らすと rc=0 になり得る。必ず module 初期化内で空 registry へ縮退させる。

`OTHER` / `PEGASUS_COMPUTE` の既存 ALLOW bit は変えない。「全拒否」は admission が効く LOGIN / SUSPECT 上での全 Pegasus path を指す。

## main checkout の hook 配線

`.claude/settings.json` は `"$CLAUDE_PROJECT_DIR/hooks/guard_bash.py"` を起動し、現セッションで実際に発火するのは main checkout 側である。さらに Bash 呼出しごとに新しい Python process になる。

したがって、

- worktree 内の単体テストは worktree の hook・JSONを読む。
- land 前の live hook は main checkout の旧 hook・旧表を使う。
- land 後は次の Bash 呼出しから main checkout の新 hook が main checkout の JSON を毎回読む。
- hook と JSON の片方だけを main に置く時間を避け、A の4ファイルを同一 commit/land 単位にする。
- 仮に hook だけ先に見えても JSON 不在で全 Pegasus DENY になるため、fail-open にはならない。

# 実装単位 B：`check_docs` の投影検査

## `tools/check_docs.py`

1. [check_docs.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:16)〜25に `shlex` を追加する。

2. [check_docs.py:1841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:1841)付近へ次を追加する。

```python
_PEGASUS_RUNBOOK = "docs/pegasus-runbook.md"
_PEGASUS_PROCEDURE = "tools/pegasus/README.md"
_PEGASUS_REGISTRY = "tools/pegasus/admission_registry.json"
_PEGASUS_REGISTRY_LOADER = "tools/pegasus_admission_registry.py"
```

`_DISPATCH_RUNBOOK` は `_PEGASUS_RUNBOOK` を参照させる。

3. [check_docs.py:1869](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:1869)〜1913の §7.0 抽出を、既存 dispatch 検査と新検査が共有できる helper に切り出す。現行と同じ条件を守る。

- visible な `### 7.0` が exact 1件。
- visible な親 `## 7` が exact 1件。
- §7.0 がその直下。
- code fence、HTML comment、raw HTML 内の decoy は不可視。
- 見出しを抽出できなければ finding を追加して `None`。

4. [check_docs.py:2268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:2268)の直後へ、`_check_pegasus_admission_projection(findings)` と補助関数を追加する。finding prefix は `tools/check_docs.py: Pegasus admission drift — ` に統一する。

検査は次の順で行い、前段を読めない場合は派生比較をせず、その読取・parse failure 自体を赤にする。

### A. canonical registry

- loader module を exact path で import。
- `load_admission_registry(REPO)` と `evidence_kind()` が callable であることを確認。
- import、JSON読取、schema、未知 class/evidence kind の例外を finding 化。
- traceback を外へ漏らさない。
- registry が確定しなければ以後の集合比較を停止する。

### B. runbook の完全投影表

§7.0 内の exact header を1個要求する。

```markdown
| path | class | evidence kind |
|---|---|---|
```

各 data row は3列、各 cell は単一 backtick literal、path 重複なし、0行不可とする。抽出した

```python
{path: (class_name, evidence_kind)}
```

を registry から導出した同じ mapping と完全一致させる。赤にする差分は以下。

- registry にだけある path
- runbook にだけある path
- 共通 path の class 差
- 共通 path の evidence kind 差
- header/separator/row の malformed、duplicate、hidden table

`reason` / `primary_gate` の散文投影は作らない。これらは JSON raw digest と hook test が不変を守る。

### C. 既存 unknown 表

exact header `| 経路 | なぜ \`unknown\` か |` を1個要求し、第一列の inline codeから `tools/pegasus/**` を抽出する。

各 path は次のいずれかだけを許可する。

- registry class が `unknown`
- class が `local-ok`、evidence が `legacy-admitted` で始まり、同じ行の説明 cell に exact `` `local-ok` `` と registry の exact evidence literalがある

後者の追加条件により、現状の `submit_silo_ladder_rung1.sh` 行を直さず checker だけ追加して緑にすることを防ぐ。未登録、`dispatch-required`、非 legacy の `local-ok` は赤。

### D. 実測 local-ok 表

exact header `| 経路 | 観測ピーク | certified peak | 分類 |` を1個要求する。`同 fetch` 等は直前の explicit path を引き継ぐ。全行の分類 cell が `local-ok` であることを確認し、抽出した path 集合を registry の `evidence kind == runbook-measured` 集合と完全一致させる。

### E. orphan table row

§7.0 内の各 `|...|` 行を、header + separator から始まるいずれかの table block に所属させる。[runbook:438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/docs/pegasus-runbook.md:438)のような孤立 row は赤にする。

### F. `tools/pegasus/README.md` の command

visible な fenced block を CommonMark 互換で抽出し、末尾 `\` の logical lineを結合する。未閉じ fence、壊れた quote、dangling continuation、Pegasus path を含むが invocation を静的確定できない行は赤。

認識する形は次だけとする。

- direct: bare `tools/pegasus/<path>`
- direct: `bash|sh tools/pegasus/<path>`
- direct: `python`, `python3`, `pythonX.Y` prefix
- scheduled: `qsub ... tools/pegasus/<path>`
- leading `./`、shell prompt `$`、環境変数代入、末尾 comment は正規化

照合規則は次。

- direct invocation → registry class が exact `local-ok`
- qsub 引数 → registry class が `local-ok` ではない
- executable-looking `tools/pegasus/**/*.py|sh|pbs` が registry にない → 赤
- 一行で複数 target、未知 wrapper、静的に target を決められない形 → 赤
- direct と qsub の抽出結果がともに0件なら、その面の検査蒸発として赤

5. [check_docs.py:3182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:3182)で既存 `_check_dispatch_inventory(findings)` の直後に新 checker を必ず呼ぶ。

# hook 側テスト計画

[orchestrator/tests/test_hooks.py:1140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_hooks.py:1140)以降を次のように変更する。

- `_PEGASUS_EXPECTED_CLASSES` は24 path/classの literal のまま、一行も JSON 由来にしない。
- `_PEGASUS_DIRECT_COMMANDS` もこの literal golden からの導出を維持する。
- `expected_local_evidence` の literal 5件も維持する。
- 新しい「hook projection」テストで loader 返値と `GB._PEGASUS_ADMISSION_REGISTRY` の全 field一致を確認する。
- raw JSON SHA-256を独立 literal `2a5712...e5e0` と比較する。digest を実データからテスト時に導出しない。
- [test_hooks.py:1223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_hooks.py:1223)〜1246の execution inventory predicateは変更しない。loader を subtree 外へ置く理由である。
- [test_hooks.py:1259](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_hooks.py:1259)〜1268の `_SANCTIONED_PATHS` 導出検査も維持する。

追加する mutation/positive control は次。

- loader module 不在・import exception・`SystemExit(0)`
- JSON 不在、invalid UTF-8、malformed JSON、duplicate key
- schema version違反、top-level/entry key違反、key順違反
- unknown class、unknown evidence kind、empty string、bad path
- BOM、CRLF、末尾改行なし、余分な末尾改行
- 上記の各失敗で registry が部分 mappingでなく `{}` になる
- fallback globals 下で24 direct commandが LOGIN/SUSPECT ですべて DENY
- 同じ fallback 下でも `tools/run_tests.py` と `tools/check_ai_provenance.py` は sanctioned のまま
- OTHER/COMPUTE の既存24 ALLOW bitは通常 registryで維持

# `check_docs` 自体のテスト計画

[orchestrator/tests/test_check_docs.py:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_check_docs.py:45)付近の synthetic 定数へ、最小 registry、完全投影表、unknown/legacy例外、実測表、direct/qsub procedure を加える。

[test_check_docs.py:577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_check_docs.py:577)の fixture writer は次を作るよう拡張する。

- `tools/pegasus/admission_registry.json`
- `tools/pegasus/README.md`
- `tools/pegasus_admission_registry.py` の実 module copy
- admission tables を含む synthetic runbook

[test_check_docs.py:594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_check_docs.py:594)の baseline repo が引き続き rc=0になることを土台とし、既存 dispatch testsの後へ以下を追加する。

- checker の main 配線を通した clean baseline
- JSON/loader不在・invalid schema・unknown classが finding
- projection row削除・追加・class変更・evidence kind変更・duplicate・malformed table
- tableを別節、fence、HTML commentへ隠す変異
- measured path集合の欠落・余分
- unknown表に dispatch-required pathを載せる変異
- local-ok legacy 行から `local-ok` または exact evidenceを消す変異
- local-ok non-legacyを unknown表へ載せる変異
- orphan row
- README direct unknown/dispatch-required
- README qsub local-ok
- README未登録 path
- quote/fence/continuation/未知 wrapperによる解析不能
- direct local-okとqsub non-local-okの正例
- registry/runbook/README の read failureで tracebackなし・rc=1
- registry parse失敗時に大量の派生 mismatch findingを出さない

`test_real_repo_clean` は親の docs 修正まで赤になるのが正しい。B の full testは A と docs の統合後に走らせる。

# docs 差分

## `docs/pegasus-runbook.md` §7.0

[runbook:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/docs/pegasus-runbook.md:367)〜374を次の趣旨へ変更する。

- 正本を `hooks/guard_bash.py` から `tools/pegasus/admission_registry.json` へ移す。
- hook と `check_docs` は共有 validator を通した投影であると記す。
- grandfather 4本は追認済みであり、[T-520] の測定経路確定後に順次実測し、結果に応じて昇格または再裁定する。
- `legacy-admitted` を実測済みと読まない注意は維持する。

直後に次の完全投影表を追加する。

| path | class | evidence kind |
|---|---|---|
| `tools/pegasus/certify_calibration.sh` | `dispatch-required` | `static` |
| `tools/pegasus/collect_receipt.py` | `unknown` | `unmeasured` |
| `tools/pegasus/collect_t126_qualification.py` | `unknown` | `unmeasured` |
| `tools/pegasus/dispatch_compute.py` | `local-ok` | `legacy-admitted` |
| `tools/pegasus/exec_calibrate.py` | `dispatch-required` | `static` |
| `tools/pegasus/fetch_third_party.py` | `local-ok` | `runbook-measured` |
| `tools/pegasus/floor_campaign.sh` | `dispatch-required` | `static` |
| `tools/pegasus/floor_scoping.sh` | `dispatch-required` | `static` |
| `tools/pegasus/make_acquisition_receipt.py` | `dispatch-required` | `static` |
| `tools/pegasus/probes/t139_positive_control_probe.pbs` | `unknown` | `unmeasured` |
| `tools/pegasus/probes/t139_positive_control_probe.sh` | `unknown` | `unmeasured` |
| `tools/pegasus/probes/t293_perf_site_probe.pbs` | `unknown` | `unmeasured` |
| `tools/pegasus/probes/t293_perf_site_probe.py` | `unknown` | `unmeasured` |
| `tools/pegasus/probes/t419_probe_causality.pbs` | `unknown` | `unmeasured` |
| `tools/pegasus/probes/t419_probe_causality.py` | `unknown` | `unmeasured` |
| `tools/pegasus/run_probe.py` | `dispatch-required` | `static` |
| `tools/pegasus/silo_ladder_rung1.sh` | `dispatch-required` | `static` |
| `tools/pegasus/smoke_probe.sh` | `dispatch-required` | `static` |
| `tools/pegasus/submit_certify.sh` | `local-ok` | `legacy-admitted` |
| `tools/pegasus/submit_floor.sh` | `local-ok` | `legacy-admitted` |
| `tools/pegasus/submit_silo_ladder_rung1.sh` | `local-ok` | `legacy-admitted` |
| `tools/pegasus/submit_t126_qualification.sh` | `unknown` | `unmeasured` |
| `tools/pegasus/t126_qualification.sh` | `dispatch-required` | `static` |
| `tools/pegasus/t141_region_profile.sh` | `dispatch-required` | `static` |

[runbook:420](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/docs/pegasus-runbook.md:420)の `submit_silo_ladder_rung1.sh` 行は、入力量としては unknown 相当だが、registry 上は `` `local-ok` / `legacy-admitted (未実測)` `` として grandfather 追認済みであることを明記する。

[runbook:438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/docs/pegasus-runbook.md:438)の孤立した `codex_worker_launch.py` 行は、unknown 表の最終 data rowとして [runbook:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/docs/pegasus-runbook.md:425)直前へ戻す。

[runbook:409](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/docs/pegasus-runbook.md:409)〜411は、既存 TASKS 同期に加えて admission projection・README command semanticsも `check_docs` が検査すると記す。

## `tools/pegasus/README.md`

- [README:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/pegasus/README.md:4)〜11の「login nodeで終了後収集」を訂正し、loginでは結果確認まで、collector実行は確保済み計算ノードで行うとする。
- [README:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/pegasus/README.md:23)〜30へ、submitter は grandfather local-ok・未実測であり、[T-520] 後に実測する注記を足す。
- [README:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/pegasus/README.md:112)〜134で、login directの `collect_receipt.py` は registry `unknown` により拒否されると明記する。
- [README:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/pegasus/README.md:117)〜123の direct fenced commandは削除する。
- 正規経路は「`qlogin` / 明示的 `qsub` で計算ノードを確保し、その中で collectorを実行」。自動 dispatch TASKSには無いので、確保できなければ停止する、とする。
- collector argvを残す必要があれば inline codeで示し、login用 copy-paste command blockにはしない。

## `hooks/README.md`

[hooks/README.md:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/hooks/README.md:78)〜82の「sanctioned exact path の一覧と判定は hook が正本」を、「JSON が正本、hook は共有 validatorによる投影」へ変更する。制約・限界の説明は維持する。

# A / B の所有分離と順序

| 単位 | 編集所有 |
|---|---|
| A | `tools/pegasus/admission_registry.json`, `tools/pegasus_admission_registry.py`, `hooks/guard_bash.py`, `orchestrator/tests/test_hooks.py` |
| B | `tools/check_docs.py`, `orchestrator/tests/test_check_docs.py` |
| 親 | `docs/pegasus-runbook.md`, `tools/pegasus/README.md`, `hooks/README.md` |

所有集合は素集合である。schema/APIを先に固定すればA/Bの起草は並行可能だが、受入順は A → 親docs → B full test とする。B の synthetic fixtureと実repo clean testがAの loaderおよび親docsへ依存するためである。

# 各段階の受入コマンド

Pegasus login nodeでは pytestを直接起動せず、必ず dispatcherを使う。

## A 完了時

```bash
python3 -m py_compile tools/pegasus_admission_registry.py hooks/guard_bash.py
python3 -c 'from pathlib import Path; from tools.pegasus_admission_registry import load_admission_registry; r = load_admission_registry(Path.cwd()); assert len(r) == 24'
python3 tools/run_tests.py orchestrator/tests/test_hooks.py -q
```

## B・親docs統合後

```bash
python3 -m py_compile tools/check_docs.py
python3 tools/check_docs.py
python3 tools/run_tests.py orchestrator/tests/test_check_docs.py -q
```

## 統合受入

```bash
python3 tools/run_tests.py orchestrator/tests/test_hooks.py orchestrator/tests/test_check_docs.py -q
python3 tools/check_codex_agents.py
python3 tools/check_docs.py
git diff --check
```

commit 後:

```bash
python3 tools/check_ai_provenance.py
```

`check_ai_provenance.py` は login nodeから計算ノードへ dispatchされる。rc=16は監査成功ではなくdispatch失敗として扱う。

本回答では sandbox制約に従い、書込み・pytest・受入コマンドは実行していない。したがって緑は主張しない。

## 総括

- 正本は exact 24 entry の `tools/pegasus/admission_registry.json` とし、全文字列を固定 digestで守る。
- loader は25本目の実行体化を避けて `tools/pegasus_admission_registry.py` に置く。
- hook は `__file__` 由来の checkoutから毎process再読し、全失敗を空registryへ縮退させる。
- `check_docs` はJSON、runbook完全投影、unknown/実測表、README command semanticsを照合する。
- `_SANCTIONED_PATHS` はlocal-okからの導出を維持し、独立 literal goldenも残す。
- 最大リスクはmain checkoutのlive hookとworktree実装の差、およびAの非原子的landである。
- 親の裁定事項はP1変更案の承認と、P3を「明示的legacy表記必須」まで強化する点である。
- 静的調査のみであり、テスト成功は未確認である。