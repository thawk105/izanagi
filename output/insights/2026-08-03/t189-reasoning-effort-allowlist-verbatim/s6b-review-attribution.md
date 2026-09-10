判定は **NO-GO**。統合コード自体には import 循環や既存 consumer の許可値逸脱を認めないが、変異帰属 V3〜V10 の一部が現状のままでは成立しない。

### V3/V4 の old block は二重出現し、V6 は二定数への同時注入が未指定

- 深刻度: blocker
- 根拠: `tools/dev_waves/schema.py:803` と `tools/dev_waves/schema.py:860` に同一 membership block。`tools/dev_waves/effort_levels.py:17` と `:18` は別々の tuple。`tools/mutation_harness.py:652-657` は old が exactly-one でなければ停止する。
- 失敗シナリオ: V3/V4 が `if effort not in CLAUDE_EFFORTS:` blockだけを old にすると count=2 で `ANCHOR_ERROR`。V6 が片方の tuple だけへ `none` を足すと、面1または面3の一方が変化せず期待赤が欠ける。
- 成果物影響: mutation ledger が未生成または片面だけの変異を正本参照の証拠として誤帰属する。

再照準する old 逐語は次のとおり。

V3 (`tools/dev_waves/schema.py:801`、1箇所):

```python
    model = _required_string(item["model"], _MODEL_RE, label="model")
    effort = _required_string(item["effort"], _EFFORT_RE, label="effort")
    if effort not in CLAUDE_EFFORTS:
        raise DevWavesError(ReasonCode.INVALID_ARGS, {
            "label": "effort", "kind": "unknown",
        })
```

V4 (`tools/dev_waves/schema.py:858`、1箇所):

```python
    if not _MODEL_RE.fullmatch(model) or not _EFFORT_RE.fullmatch(effort):
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "child-argv", "kind": "model-effort"})
    if effort not in CLAUDE_EFFORTS:
        raise DevWavesError(ReasonCode.INVALID_ARGS, {
            "label": "effort", "kind": "unknown",
        })
```

V6 は `tools/dev_waves/effort_levels.py` 内で次の2 replacementを累積適用すべきで、各 old は1箇所。

```python
CLAUDE_EFFORTS: tuple[str, ...] = ("low", "medium", "high", "xhigh", "max")
```

```python
CODEX_REASONING_EFFORTS: tuple[str, ...] = (
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
)
```

### V5 の両層 E2E 期待赤が存在せず、直接テストも同一 node に畳まれている

- 深刻度: blocker
- 根拠: `orchestrator/tests/test_dev_waves_schema.py:272-283` は spec/argv を一関数で検査し、先頭の spec assertion が赤になると argv 部へ到達しない。`tools/mutation_harness.py:686-688` は同一 expected node の重複登録を拒否する。`orchestrator/tests/test_dev_waves_worker.py:83` の `build_child_argv` 入力は `high` だけ。
- 失敗シナリオ: V3+V4を同時注入すると schema test は `parse_worker_spec` 側で直ちに赤となり、`validate_child_argv` と E2E は未実行。それでも単一 node を見て V5 KILLED と誤記録できる。
- 成果物影響: policy外 `effort=none` が実 child まで到達し得る退行を、worker run ledgerの正常 baselineとして残せる。

実経路自体は存在する。`daemon.py:1225` の `build_child_argv`→`validate_child_argv`、`worker.py:602`/`:643` の spec parse、`worker.py:394` の再度の `build_child_argv` を通る。

再照準は以下が必要。

- `test_dev_waves_schema.py:272` の関数を spec負例とargv負例の別 nodeへ分割する。
- `test_dev_waves_worker.py:79` 付近に、永続化した `effort=none` specを `build_child_argv(load_worker_spec(path))` へ渡す負例を追加する。単層変異では残存層が拒否して緑、V3+V4同時時だけ赤になる形にする。

### V7/V9 の正例は変異対象の定数を反復するため、削除値を試さない

- 深刻度: blocker
- 根拠: `orchestrator/tests/test_dev_waves_cli.py:151-154` と `test_dev_waves_schema.py:286-290` は `for effort in CLAUDE_EFFORTS`。独立した逐語 oracle は `test_effort_levels.py:39-42` にしかない。
- 失敗シナリオ: V7で`max`、V9で`low`を tuple から削除すると、parserとテスト反復集合が同時に縮み、登録した面2/面3正例はその値を一度も入力せず緑。赤になるのは exact-vocabulary meta-testだけで、受理経路の killではない。
- 成果物影響: 正規の `low`/`max` workerを拒否する過剰縮小が、面2/面3の受入証拠を持つと誤記録される。

両ファイルの old 逐語は各ファイル内で1箇所:

```python
    for effort in CLAUDE_EFFORTS:
```

これを独立したリテラル5値による parameterize に替え、`[low]`/`[max]` nodeを実在させる必要がある。

### V8 は live launcherへ入る前の定数 assertionで赤になる

- 深刻度: must-fix
- 根拠: `orchestrator/tests/test_codex_worker_launch.py:554-557` は5値をリテラル化しているが、`:562` の membership assertionが`:564`の `_run_case` より先にある。
- 失敗シナリオ: V8で`max`を削除すると `[max]` nodeは`:562`で停止し、CLI subprocessを起動しない。「live経路の保護」という事前登録理由は実証されない。
- 成果物影響: mutation proof chainが、実際には行っていない launcher/receipt 経路検査を実施済みと表示する。

再照準は `test_codex_worker_launch.py:562` の一意な old:

```python
    assert reasoning in LAUNCHER.CODEX_REASONING_EFFORTS
```

を外し、リテラル `max` を `_run_case` まで通すこと。

### V10 は `_EFFORT_RE` の単純削除だと diagnostic遷移ではなくTypeErrorになる

- 深刻度: must-fix
- 根拠: `_required_string` は pattern必須 (`tools/dev_waves/schema.py:564-567`)。対象呼び出しは`:802`。期待テストは `DevWavesError.detail` を検査する (`test_dev_waves_schema.py:293-304`)。
- 失敗シナリオ: `_EFFORT_RE,`だけを削除すると必須 positional argument欠落の`TypeError`となり、`kind=string → unknown`は起きない。nodeは赤でも diagnostic pinとして帰属不能。
- 成果物影響: structured failure signalの感度を証明していないのに、diagnostic pin済みとmutation ledgerへ記録される。

oldは1箇所:

```python
    effort = _required_string(item["effort"], _EFFORT_RE, label="effort")
```

newを明示的に次へ固定すべき。

```python
    effort = item["effort"]
```

### 新規テストのmeta-testを段5・統合後対象走のどちらでも実行していない

- 深刻度: nit
- 根拠: `s5a-report.md:69` はテスト非実走。既存の統合後receipt `output/pegasus-dispatch/c674ed828fa34eace76ccfdfba9d32c4/receipt.json:51-59` にも `test_plain_runner_coverage.py` は含まれない。一方、新規ファイルは `_run()`/`__main__` を持つ (`test_effort_levels.py:62-85`)。
- 失敗シナリオ: self-runner判定に見落としがあっても受入全走まで露出しない。今回は静的にはF42契約を満たす形である。
- 成果物影響: 現差分に具体的な成果物変化を認めないためnit。親の受入全走でmeta-testを含める必要がある。

## V1〜V11 判定表

| ID | old 逐語が一意か | 期待赤は妥当か | mask の有無 | kill か diagnostic pin か | 再照準の要否 |
|---|---|---|---|---|---|
| V1 | ○、1箇所 | ○ | 無 | semantic kill | 不要 |
| V2 | ○、1箇所 | ○ | 無 | semantic kill | 不要 |
| V3 | ×、membership blockが2箇所 | 一意注入後なら○ | 直接呼出しでは無 | kill意図、現状は注入不能 | 要 |
| V4 | ×、同上 | 一意注入後なら○ | 直接呼出しでは無 | kill意図、現状は注入不能 | 要 |
| V5 | ×、V3/V4を継承 | ×、E2E nodeなし | 単層maskは意図どおりだが、現テストはV3でV4を短絡 | kill未実証 | 要 |
| V6 | ×、二定数への2-site指定が必要 | 両site注入後なら○ | 片siteだけでは他面不変 | kill意図 | 要 |
| V7 | ○、CLAUDE tuple行1箇所 | ×、`max`を反復しない | 変異定数によるtest-data mask | 実受理集合は縮むが登録nodeはSURVIVED | 要 |
| V8 | ○、CODEX側`"max",`は1箇所 | nodeは赤だがlive理由ではない | test内pre-assertion | semantic source pin、live kill未実証 | 要 |
| V9 | ○、CLAUDE tuple行1箇所 | ×、`low` case自体が消える | 変異定数によるtest-data mask | 登録kill未実証 | 要 |
| V10 | ○、assignment行1箇所 | newを明記すれば○ | membership残存は意図どおり | diagnostic pin、killに数えない | 要 |
| V11 | ○、launcher set行1箇所 | ○ | meta-test直呼出しには無 | subset meta-test、killに数えない | 不要 |

## 統合・consumer波及の静的確認

- import循環なし。`codex_worker_launch.py:41`からsubmodule importすると`tools/dev_waves/__init__.py:3-4`がdaemon/schemaをeager importするが、daemon側からcodex launcherへの逆辺はない。従来も直後のschema importで同じpackage初期化が発生していた。
- `schema.py:878-890`の`__all__`を変更しないのは正しい。`CLAUDE_EFFORTS`をschema APIとして再exportしていない。package `__init__.py`にも再exportなし。
- `conftest.py`と共有fixtureの変更なし。新規helperは各test file内だけ。
- `parse_worker_spec`のtrackedな直接callerは `worker.py:592` とschema testの`:274,289,295,350,353,356`。`daemon.py:98`は未使用import。productionでは`spawn_worker:602`とworker main`:643`から間接到達する。
- `validate_child_argv`のtrackedな直接callerは `worker.py:246` とschema testの`:259,263,266,269,280,290,301`。productionではdaemon`:1225`とworker `_spawn_stopped`:394`から間接到達する。
- worker testの正常値は`high` (`test_dev_waves_worker.py:53`)、daemon/integration profileは`low` (`test_dev_waves_integration.py:250`ほか)、CLI永続profileも`low` (`test_dev_waves_cli.py:161,238`)。checker testはeffortを渡さない。いずれも許可集合内。
- `orchestrator/tests/`全体の集合外表記は、新規負例の`none`、provenance用`reasoning=default`など別APIのfixtureだけ。新gateへ到達する既存正常系には集合外値なし。
- `_supervisor_digest()`のリテラルpinはテスト中に存在しない。値はmanifest記録 (`daemon.py:736`) と同一run内比較 (`:1114,1211`) にだけ使われるため、新ファイル追加による値変更の静的波及なし。
- F28はV7/V9の自己参照fixtureとV8の手前assertionで再発。F33の「両層kill期待未登録」自体はV5で登録済みだが、実在nodeと一意anchorが欠け、偽SURVIVED型の危険は残る。F42は手順上再発。F41はhandoff `:100-102`にcheckoutが併記されており再発なし。

## 総括

- GO / NO-GO: **NO-GO** — 必須mutation matrixの一意注入・両層E2E・過剰拒否の帰属が成立しない。
- blocker: **3件** — V3/V4/V6のanchor不成立；V5のE2E node欠落；V7/V9正例の自己参照mask。
- 帰属が成立しない変異のID: **V3, V4, V5, V6, V7, V8, V9, V10**
- 新しい拒否によって赤くなる既存テストのfile:line: **無し（静的検索上）**
- pytest: **本レビューでは走らせていない。静的検査のみ。**