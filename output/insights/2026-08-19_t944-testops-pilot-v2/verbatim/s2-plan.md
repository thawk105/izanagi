# dev-wave t944 — 有界 task-run 観測 pilot v2 段2 plan

段2の read-only 起草。現行 HEAD は `a31832d9a021a907907266647ea49b9b7f0b5de5`、worktree は clean。pytest・mutation・受入走行は実施していない。

## 結論

- `P1` は、Unit B に dispatch transport の補助面を追加する条件付き採用。
- `P2` は、`git-common-dir` から導く repo 兄弟 path を採用する。digest、HOME/XDG fallback、任意 base override は採用しない。
- `P3` は、trigger を推測せず `unspecified` とする限定採用。trigger が解決したとは主張せず、README に未分類の限界を明記する。
- Q1(a) により、自動 rollover は実装しない。閉鎖世代から次世代を作る操作は明示 API のみとする。
- Q2(a) により、repo 外兄弟に保存するが改竄検出は主張しない。
- Q3(a) により、被覆は `tools/run_tests.py` 経由だけとし、素の pytest、mutation local mode、別 clone は未被覆と明記する。

## 現行静的確認

| 面 | 現況 |
|---|---|
| `ledger.py` | `start_run()` は `repo_root` を持たず、外部 root では `root` 自体を `_git_head()` に渡す (`tools/task_runs/ledger.py:527-575`) |
| 閉鎖判定 | final marker、run cap、age cap は `:544-557`。damaged/unknown は `:551-552` の独立した `LedgerError` |
| root 安全性 | `_assert_safe_root()` は `:144-156`。検査後に元の未解決 `root` を返すため、generation 側の fd anchoring が必要 |
| 4 gate | 定数表 `tools/run_tests.py:74-122`、gate 本体は brief anchor の `:388-560`（現 tree の関数表示では `:402-579`）。この面は無差分とする |
| auto marker | 現在なし。記録は `IZANAGI_TASK_RUN_ID` がある場合だけ (`tools/run_tests.py:836-1025,1521-1574,1678-1689,1913-1916`) |
| sidecar | `pytest_stats.py:87-145` は通常の `Exception` を pytest hook の外側で吸収する `conftest.py:674-803` により A1 は refuted |
| dispatch | `dispatch_compute.py:57-60,76-91,570-580,643-669` が task-run ID/root/sidecar を除去するため、B3 は `run_tests.py` 単独では閉じない |
| schema | `task-run/v1` の exact-key 契約 (`schema.py:266-306`, `schema_v1.json:61-86`)。generation 情報を task/event に追加しない |

A1 は対象外とし、`pytest_stats.py` と `conftest.py` は変更しない。A11 の signal 非捕捉と衝突するため、hook 側の `except Exception` を `BaseException` へ広げない。

## P1〜P3 の裁定

### P1 — 条件付き採用

元の Unit A / Unit B 分割は ledger-core と wrapper lifecycle の境界として妥当。ただし B3 の counts/digest は、以下の dispatch transport を変更しない限り閉じない。

Unit A:

- `tools/task_runs/ledger.py`
- `tools/task_runs/generation.py` 新規
- `tools/task_runs/schema.py`
- `tools/task_runs/schema_v1.json`
- `tools/task_runs/cli.py`
- `tools/task_runs/__init__.py`
- `orchestrator/tests/test_task_run_ledger.py`
- `orchestrator/tests/test_task_run_generation.py` 新規

Unit B:

- `tools/run_tests.py`
- `tools/pegasus/dispatch_compute.py` の task-run sidecar transport 部分
- `orchestrator/tests/test_run_tests_task_run.py`
- `orchestrator/tests/test_run_tests_testops_observation.py` 新規
- `orchestrator/tests/test_pegasus_dispatch_compute.py`
- `output/task-runs/README.md`

Unit A を先行完了し、その所有 path 限定 patch を Unit B に渡す。dispatch transport は Unit B の補助面であり、独立 Unit C には分けない。

### P2 — digest 方式を棄却し、repo 兄弟を採用

`generation.py` は次の導出だけを許す。

1. `git rev-parse --show-toplevel` で現在 worktree の repo root を確認する。
2. `git rev-parse --git-common-dir` を取得し、realpath の親を linked worktree 共通の main repo root とする。
3. `<common_repo_root.parent>/<common_repo_root.name>-task-runs/` を series base とする。

現環境では `/work/1/SFC/tanab/izanagi-task-runs/` になる。

`IZANAGI_TASK_RUNS_BASE`、XDG、HOME fallback、common-dir digest namespace は自動経路では使わない。既存の `IZANAGI_TASK_RUNS_ROOT` は manual ID 経路だけに残す。path containment、symlink、TOCTOU の拒否は行うが、外部台帳の改竄検出や trust anchor とは主張しない。

### P3 — 限定採用

自動経路で trigger の意味を推測しない。

- `IZANAGI_TEST_TRIGGER` が既存の許可値なら従来どおり使う。
- 未設定・不正値は `trigger="unspecified"`。
- route、git dirty 状態、full-suite 形状から `baseline` や `final` を推測しない。
- `trigger_unspecified` を解消した、trigger cohort が比較可能になった、とは README/report に書かない。

これは M3 を黙って放置する設計ではなく、「自動経路の trigger は未分類」という明示契約で閉じる。trigger cohort が必要になった場合は、schema/裁定を伴う別 wave とする。

## Unit A / Unit B interface contract

`generation.py` の public contract は次の形に固定する。

```python
@dataclass(frozen=True)
class AutomaticRun:
    generation_root: Path
    task_run_id: str
    generation_name: str

def start_automatic_test_run(
    repo_root: Path,
) -> tuple[AutomaticRun | None, str | None]:
    """
    成功: (AutomaticRun(...), None)
    pilot 閉鎖: (None, "pilot-closed:final|max-task-runs|max-days")
    記録不能: (None, "recording-unavailable:<closed-code>")
    KeyboardInterrupt/SystemExit は送出し、ここで吸収しない。
    """

def finish_automatic_test_run(
    run: AutomaticRun,
    outcome: str,
) -> str | None:
    """
    成功: None
    通常 Exception: "recording-unavailable:finish"
    KeyboardInterrupt/SystemExit: 送出
    """
```

`result is None, diagnostic is None` は Unit B が明示 opt-out を選んだ場合に限る。generation の失敗と opt-out を同じ状態にしない。

M1 の診断は、例外本文・repo path・argv・selector・node IDを含まない固定語彙だけを使う。Unit B は一度だけ次の形式を stderr に出す。

```text
IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:series-lock-timeout
```

許可する diagnostic code の例:

- `pilot-closed:final`
- `pilot-closed:max-task-runs`
- `pilot-closed:max-days`
- `recording-unavailable:series-invalid`
- `recording-unavailable:series-lock-timeout`
- `recording-unavailable:filesystem`
- `recording-unavailable:sidecar`
- `recording-unavailable:statistics`
- `recording-unavailable:append`
- `recording-unavailable:finish`

Unit B の `_record_task_run()` は `None` 返却から次へ変える。

```python
tuple[bool, str | None]
# (True, None)                    event を記録できた
# (True, "recording-unavailable:statistics")  # event は記録、metrics 欠測
# (False, "recording-unavailable:append")     # event を記録できなかった
```

この返り値は child の rc と分離する。通常の `Exception` は診断へ変換して child rc/stdout/stderr を保つ。`KeyboardInterrupt` と `SystemExit` はどの wrapper からも捕捉しない。

## 20 所見の file:line 粒度 plan

### Blocker

#### A2 — 4 gate の凍結範囲不足

対象:

- `tools/run_tests.py:74-122`
- `tools/run_tests.py:388-560`（現 tree の gate 定義は `:402-579`）
- `tools/run_tests.py:1714-1916`
- `orchestrator/tests/test_run_tests_task_run.py:71-136`

置換前の骨子:

- task-run session の追加時に gate caller、`PYTEST_ADDOPTS`、定数表の影響を固定していない。
- `:367-560` の hunk が無いことだけでは受理集合を固定できない。

置換後:

- 4 gate の定数・関数本体・呼出し順・`PYTEST_ADDOPTS` の読み方は変更しない。
- recording session の初期化は gate、site/preflight、dispatch/scope 選択の後に行う。
- session は `args` を変更せず、`PYTEST_ADDOPTS` も変更しない。
- truth-table characterization を新設し、direct/dispatch/scope の session 前後で4 gateの値が一致することを固定する。

契約:

- 4 gate の入力から task-run の有無を推測しない。
- `--help`、`--version`、selector、compact option、値付き option、壊れた quoting、unknown option は現行判定を維持する。
- production diff に gate 本体と定数表への hunkを置かない。

#### A3 — 外部 base の証拠 namespace / symlink / TOCTOU

対象:

- `tools/task_runs/ledger.py:144-172`
- `tools/task_runs/ledger.py:296-347`
- `tools/task_runs/ledger.py:527-563`
- `tools/task_runs/generation.py:new:1-290`

置換前の骨子:

- external base を作る前の全 component 検査がない。
- `_assert_safe_root()` は resolve 前の path を返す。
- ledger 側で拒否する前に generation/lock/pilot を作り得る。

置換後:

- repo sibling base を realpath と directory-fd で検査する。
- 既存 component の symlink、非 directory、banned namespace、repo 内解決を拒否する。
- create/open/rename は検査済み parent fd と `O_NOFOLLOW` を使う。
- base、lock、staging generation、pilot のいずれも、検査失敗時には1 byteも作らない。
- automatic 経路では `IZANAGI_TASK_RUNS_ROOT` を base override として使わない。

契約:

- repo sibling は運用上の置き場であり、改竄検出の anchor ではない。
- symlink差し替えを検出できない場合は記録を諦め、pytest は通常実行する。
- damaged/unknown は `PilotClosedError` に変換しない。

#### A4 — 自動 rollover が Q1(a) に反する

対象:

- `tools/task_runs/ledger.py:544-557`
- `tools/task_runs/generation.py:new:110-190`
- `output/task-runs/README.md:14-24,91-99`

置換前の骨子:

```python
except PilotClosedError:
    generation = create_next_generation()
    ...
```

置換後:

- `PilotClosedError` は `final`、`max_task_runs`、`max_days` の理由を持つ型付き例外にする。
- `start_automatic_test_run()` はこれを捕捉して diagnostic を返すだけ。
- 自動経路から `create_next_generation()` を呼ばない。
- `open_next_generation(repo_root)` は明示操作として分離し、automatic caller から到達不能にする。
- t944 の最初の generation は D341/Q1(a) で明示承認された pilot の初期作成として扱い、閉鎖後の generation-2 以降は自動作成しない。

契約:

- `ledger.py:551-552` の damaged/unknown raise は通常の `LedgerError` のまま。
- `PilotClosedError` 以外の `LedgerError` を rollover 条件にしない。
- generation cap は既存 v1 の 10 runs / 14 days を維持する。

#### A5 — series 全体の fail-closed reader 不在

対象:

- `tools/task_runs/generation.py:new:191-260`
- `tools/task_runs/cli.py:40-52,125-129,197-239`
- `tools/task_runs/ledger.py:442-524`

置換前の骨子:

- 個別 generation だけを選んで `validate_root()` / report できる。
- 他 generation の damaged/unknown を無視できる。
- series 全体の reader がない。

置換後:

```python
def validate_series(repo_root: Path) -> SeriesReport:
    ...
```

- series base の許可 entry は `.generation.lock`、`generation-NNNNNN`、一時 transport directoryだけに限定する。
- generation番号の欠落、重複、symlink、unknown entry、staging残留を拒否する。
- 全 generation に `ledger.validate_root()` を適用する。
- 1世代でも damaged/incomplete/unknown なら series report 全体を失敗させる。
- `cli.py` に read-only の `validate-series` を追加する。`--repo-root` は追加しない。
- 世代横断 aggregate/report は作らず、report は個別 generation 単位のままにする。

契約:

- 健全な generation だけを選んで「series は valid」と返さない。
- series reader の invalid は pilot closed ではない。

#### B1 — 並行 start の cap race

対象:

- `tools/task_runs/ledger.py:541-557`
- `tools/task_runs/ledger.py:578-601`
- `tools/task_runs/generation.py:new:80-160`

置換前の骨子:

- generation discovery と `start_run()` の間に series lock がない。
- cap が task_end 済み run 数で判定される実装へ変異し得る。

置換後:

- series lock を取得して generation discovery、selfcheck、`start_run()` の呼び出しまでを直列化する。
- generation root の既存 root lock は維持する。
- cap は task marker が publish 済みの run を数える。task_end の有無を cap 判定に使わない。
- task.json publish 後の未完 runも cap を消費する。

契約:

- 20 concurrent start でも generation あたり最大10 task directory。
- 11件目以降は `pilot-closed:max-task-runs`。
- series lock除去だけの変異も、空seriesの同時初期化または世代選択競合で検出する。

#### B2 — generation 作成途中 crash

対象:

- `tools/task_runs/ledger.py:359-379`
- `tools/task_runs/ledger.py:578-601`
- `tools/task_runs/generation.py:new:120-190`

置換前の骨子:

- `mkdir`、`init_pilot()`、generation publish が別々で、途中 directory が正式世代として残る。

置換後:

1. `generation-NNNNNN.staging` を O_EXCL で作る。
2. staging root 内へ `init_pilot()` を実行する。
3. pilot bytes と directory entry を fsync する。
4. no-replace rename で `generation-NNNNNN` へ publish する。
5. crash後に valid pilot の staging だけは series lock 下で recovery して renameする。
6. pilot欠落・破損 staging は削除せず、fail-closed diagnostic とする。

契約:

- 正式 layout に incomplete generation を見せない。
- stagingを無視して次番号へ進まない。
- recovery は generation creation の再開であり、閉鎖世代からの自動 rollover ではない。

#### B3 — dispatch / bounded scope の payload 欠測

対象:

- `tools/run_tests.py:825-1025`
- `tools/run_tests.py:1396-1574`
- `tools/pegasus/dispatch_compute.py:57-60,76-91,570-580,643-669,1507-1562`
- `orchestrator/tests/test_pegasus_dispatch_compute.py:460-490,957-999,3043-3051`

置換前の骨子:

- directだけが sidecar を読める。
- dispatch/scope は `sidecar=None`。
- dispatch transport が sidecarを allowlist・job script・compute childから除去する。

置換後:

- Unit A の sibling transport directory に一時 sidecar leaseを作る。
- direct child、bounded child、dispatch childへ同じ sidecar pathを渡す。
- childには `IZANAGI_TASK_RUN_AUTO_RECORD=0` を渡し、child自身の generation startを禁止する。
- manual `TASK_RUN_ID` / `TASK_RUNS_ROOT` は引き続き childへ渡さない。
- `dispatch_compute.py` の tests task allowlistへ sidecarとauto-off markerだけを追加する。
- job script と `_job_run()` は sidecarを保持し、manual ID/rootだけを除去する。
- parentはchild終了後にsidecarを読み、counts/digestを `record_test_run()` へ渡す。
- sidecarが無い場合も event は null metricsで記録し、`statistics` diagnosticを出す。

契約:

- 正常な direct/dispatch/scope の test event は同じ counts/digest shapeを持つ。
- CAP_OOM fallbackでは task-runは1件のまま、scope eventとcompute eventを同じ task-runへ追記する。
- sidecar bytesにnode IDは含めない。
- transport pathはtask payloadへ保存しない。

#### B4 — bounded scope の OOM / timeout / infra failure 未記録

対象:

- `tools/run_tests.py:1396-1508`
- `tools/run_tests.py:1521-1574`
- `tools/run_tests.py:1804-1830`

置換前の骨子:

```python
result = _run_bounded_scope(args, cap)
if result.outcome is not _ScopeOutcome.CHILD_RC:
    return result
```

置換後:

- `CHILD_RC`、`CAP_OOM`、`DISPATCH_INFRA` のすべてで recording sessionへ結果を渡す。
- child rcが無い場合は既存の infra rc (`_PEGASUS_DISPATCH_RC`) を `exit_status` として記録する。
- CAP_OOM後の fallback dispatchは同じ session/同じ task-runを再利用する。
- 最終 route終了後に task_endを一度だけ追記する。
- setup failureでも「pytest childが実際に起動した」と偽らず、attempted scopeの infra eventとして記録する。

契約:

- OOM/timeout/attestation failureの早期 returnが記録を飛ばさない。
- recording failureはscope結果やchild rcを置換しない。
- fallbackが行われた場合は local scope failure と compute result の両方を観測可能にする。

#### B5 — 親の実測値から全経路への一般化が成立していない

対象:

- `output/task-runs/README.md:68-75,91-99`
- `tools/run_tests.py:1714-1916`
- `orchestrator/tests/test_run_tests_testops_observation.py:new`

置換前の骨子:

- IDなし direct、login dispatch、bounded、compute、mutation local の分母を測らず、台帳への記録を全走行と読める余地がある。

置換後:

- READMEに「被覆対象は `tools/run_tests.py` が実際に childを起動した wrapper invocation」と明記する。
- preflight/gate拒否、raw pytest、mutation local、別 cloneは記録率の分母に含めない。
- diagnosticは記録停止を示すが、未記録走行の完全な分母を復元するものではない。
- reportの主張範囲を「記録された event のみ」に固定する。

契約:

- 「全走行を記録する」「欠測率を母集団の率として測る」と書かない。
- A10と同じ旧briefのゼロ主張を復活させない。

### Must-fix

#### A6 — direct pytest child の再帰記録

対象:

- `tools/run_tests.py:867-927`
- `tools/run_tests.py:930-937`
- `tools/run_tests.py:1396-1409`
- `tools/run_tests.py:1678-1704`

置換前の骨子:

- dispatch/scope childからmanual task-run envを消すが、direct childに所有 markerがない。
- nested `run_tests.py` がauto startし得る。

置換後:

- direct child、dispatch child、bounded scope childの全てに `AUTO_RECORD=0` を設定する。
- direct/scopeはsidecarを保持する。
- dispatchはsidecarだけを transportし、ID/rootは除去する。
- childがnested `run_tests.py`を起動しても新規task-runを作らない。

契約:

- parentがtask-run所有者であり、childは統計sidecarのproducerだけ。
- fallbackは同一 sessionを使い、nested auto startをしない。

#### A7 — series lock の無期限 block

対象:

- `tools/task_runs/generation.py:new:60-110`
- `tools/task_runs/ledger.py:669-680`

置換前の骨子:

- series lockにtimeout/nonblocking契約がない。

置換後:

- `.generation.lock` は regular file、`O_NOFOLLOW`、owner-onlyで開く。
- `LOCK_NB` + monotonic deadlineで待つ。
- timeoutは `recording-unavailable:series-lock-timeout` を返し、pytestを起動する。
- `finally`で必ずunlock/closeする。process死による flock解放を前提に stale owner fileを信用しない。

契約:

- lock contentionでpytest wrapper自体を無期限に止めない。
- lock fileのsymlink・非regular fileは timeout ではなく `series-invalid` とする。

#### A8 — `repo_root` による間接的な HEAD caller 指定

対象:

- `tools/task_runs/ledger.py:296-347,527-575`
- `tools/task_runs/generation.py:new:20-80`
- `tools/task_runs/cli.py:40-45,197-212`

置換前の骨子:

```python
base_commit = _git_head(root)
```

置換後:

- `start_run(..., repo_root: Path | None = None)` を keyword-onlyで追加する。
- automatic external generationだけが `repo_root` を渡す。
- `root.parent` が `repo_root` から導出した sibling base と一致することを検査する。
- repo Aのgeneration rootへrepo Bの`repo_root`を渡す呼出しは拒否する。
- base commitは常に `_git_head(repo_root)` で実測する。
- CLI parserに `--repo-root` 相当を追加しない。

契約:

- callerがbase commit文字列を渡すAPIは作らない。
- path bindingはnamespace取り違え防止であり、外部台帳の改竄検出とは主張しない。
- `repo_root=None` の既存checkout-local manual経路は互換維持する。

#### A9 — privacy test が file path を見逃す

対象:

- `tools/task_runs/schema.py:287-305`
- `tools/task_runs/schema_v1.json:61-86`
- `tools/run_tests.py:782-818`
- `tools/task_runs/generation.py:new:140-190`
- `orchestrator/tests/test_run_tests_task_run.py:127-136`

置換前の骨子:

- objectiveは `/` を許し、旧planの自動objectiveに `tools/run_tests.py` が入り得る。
- privacy testはselector/node IDの一部だけを見る。

置換後:

- task-run/v1のまま、objectiveの既存自由文契約を狭め、`/`、`\`、`::`、CR/LFを拒否する。
- `schema.py` と `schema_v1.json` のpatternを同期する。
- automatic objectiveは固定文字列 `"automatic test observation"` とする。
- slugは `"pytest-run"`、suite_idは既存の12 hex digestだけとする。
- diagnostic、sidecar、task/event bytesにargv、selector、node ID、repo file pathを入れない。
- stdout/stderrはtask-runへ保存しない。

契約:

- `task-run/v1` のversion、field、event keyは増やさない。
- privacy testは sentinelをtask.json、events.jsonl、sidecar、diagnosticへ通し、文字列不在を確認する。

#### A10 — 観測できない母集団をゼロと一般化する問題

対象:

- `output/task-runs/README.md:68-75,91-99`
- `output/task-runs/README.md:101-116`
- `orchestrator/tests/test_run_tests_testops_observation.py:new`

置換前の骨子:

- frozen pilotの「新規 event ゼロ」を、IDなし wrapper invocation全体のゼロと混同し得る。

置換後:

- frozen pilotの実測は「writerが拒否したため新規記録がない」とだけ扱う。
- new pilotの記録数はwrapperが作ったtask/event数としてのみ表示する。
- raw pytest等を分母にするcoverage率は出さない。
- READMEに記録不能eventは台帳内から復元不能と明記する。

契約:

- A10の旧一般化を再導入しない。
- testは、READMEに未被覆経路と「記録されたeventのみ」の表現があることを固定する。

#### A11 — `KeyboardInterrupt` / `SystemExit` の例外安全性

対象:

- `tools/run_tests.py:836-927`
- `tools/run_tests.py:953-970`
- `tools/run_tests.py:973-1025`
- `tools/run_tests.py:1521-1574`
- `tools/task_runs/ledger.py:814-835,885-888`

置換前の骨子:

- recording周辺の複数の `try/except` と dispatch wrapperを一括変更すると、signalを通常例外へ畳み得る。

置換後:

- 通常の `Exception` だけを fail-open diagnosticへ変換する。
- bootstrap、child rc取得後のrecord、fallback後のrecord、finishの各地点で `KeyboardInterrupt/SystemExit` を送出する。
- child processが負のsignal rcを返した場合はそのrcをeventへ保存し、wrapper rcを変更しない。
- `finally` のsidecar cleanupも `Exception` だけを扱い、signalを隠さない。
- `_invoke_dispatch()` の dispatcher固有infra契約と task-run writer の signal契約を混同しない。

契約:

- signal発生時に task_end を無理に追加しない。
- 通常例外時は未完task-runを残せるが、child rcは保持する。
- `SystemExit`を `Exception` と同じ診断へ変換しない。

#### M1 — fail-open の無言化

対象:

- `tools/task_runs/generation.py:new:1-290`
- `tools/run_tests.py:836-1025`
- `tools/run_tests.py:1521-1574`
- `tools/run_tests.py:1913-1916`

置換前の骨子:

- generation bootstrap、sidecar、record appendの失敗を全て無言で吸収する。

置換後:

- Unit Aは上記の `(result, diagnostic)` を返す。
- Unit Bは診断を固定形式の stderr 1行へ変換する。
- child stdout/stderrをcaptureして書き換えない。wrapperの診断はchild完了後の別行とする。
- diagnostic自体のstderr write failureは通常例外として無視し、rcは保持する。
- 例外本文を出力しないためpath/argv漏洩と揮発payloadを避ける。

契約:

- auto recordingが全走行で停止しても、diagnosticを見れば判別できる。
- `PilotClosedError` は「正常なpilot閉鎖」、series/FS/append failureは「記録不能」として別コードになる。
- pytest rcをdiagnostic rcで置換しない。

#### M2 — manual CLI の series lock 迂回

対象:

- `tools/task_runs/cli.py:40-52,121-129,197-239`
- `tools/task_runs/generation.py:new:60-110`

置換前の骨子:

- `--root generation-NNNNNN` に対する CLI start/event/finishが直接ledgerへ到達する。

置換後:

- `validate-series` はread-only commandとして追加する。
- managed generation rootに対する `init-pilot`、`start`、`event`、`finish` はCLIから拒否する。
- managed generationへの書込みはgeneration managerのseries lock付きAPIだけに限定する。
- manual CLIのcheckout-local root互換は維持する。
- READMEでmanaged generationのwrite入口を明記する。

契約:

- CLIに`--repo-root`、任意base、generation番号指定のwrite flagを追加しない。
- CLI拒否はbytesを作る前に行う。
- `validate --all` による個別generationのreadは許可する。

#### M3 — trigger の無手番化不足

対象:

- `tools/run_tests.py:877-879,991-993,1537-1539`
- `tools/task_runs/schema.py:436-449`
- `output/task-runs/README.md:93-110`

置換前の骨子:

- IDだけを自動化しても、triggerは未設定のまま意味不明になり得る。

置換後:

- auto triggerは明示的に `unspecified`。
- invalid envも `unspecified` に正規化する。
- routeからtriggerを推測しない。
- READMEのmissingness表に「automatic test observationはtrigger未分類」と追記する。

契約:

- `trigger_unspecified` の改善やtrigger cohortの比較を成果に含めない。
- `trigger=baseline` 等を恒真の分類として自動生成しない。

#### M4 — default rootの filesystem 契約不足

対象:

- `tools/task_runs/generation.py:new:20-110,260-290`
- `tools/task_runs/ledger.py:891-987`
- `output/task-runs/README.md:78-81`

置換前の骨子:

- sibling pathの実FSが `flock`、O_EXCL、O_APPEND、fsyncを満たすか自動起動時に確認しない。

置換後:

- generation初期作成後、auto start前に既存 `ledger.selfcheck()` を実rootへ適用する。
- selfcheck失敗は `recording-unavailable:filesystem` とし、pytest自体は実行する。
- selfcheckの一時entryは既存契約どおりcleanupし、series layoutへ恒久entryを追加しない。
- per-generation markerをschemaへ追加しないため、selfcheckは毎回またはgeneration open時に実行する。

契約:

- default sibling rootを実FS保証済みと宣言するのは selfcheck 成功後だけ。
- selfcheck未実施を緑や「記録可能」と報告しない。

#### M5 — 142行目標と安全面の不整合

対象:

- briefの見積り表
- `tools/task_runs/generation.py:new:1-290`
- `tools/run_tests.py:825-1025,1396-1574,1678-1916`
- `tools/pegasus/dispatch_compute.py:57-91,570-580,643-669`

置換前の骨子:

- lock、crash recovery、series reader、route payload、diagnosticを約142行へ圧縮する。

置換後:

- 人為的な142行上限は置かない。
- lock、recovery、reader、transport、signal契約をそれぞれ独立した関数・テストへ分ける。
- production diffの増加は段4で裁定材料にする。
- いずれかの安全面を削って行数を合わせる場合は実装せず、再裁定へ返す。

契約:

- 「短く収めた」ことを安全性の代替にしない。
- 下記見積りの上限を超える場合、原因と削っていない要求一覧を記録する。

## generation layout と lifecycle

```text
/work/1/SFC/tanab/
├── izanagi/                    # repo/common repo root
└── izanagi-task-runs/          # repo sibling series base
    ├── .generation.lock
    ├── transport/              # 一時 sidecar。series readerが管理entryとして扱う
    ├── generation-000001/
    │   ├── pilot.json
    │   └── <task-run-id>/
    └── generation-000002/      # 明示 open APIでのみ作成
```

generation root内の task/event は既存 `task-run/v1` のまま。generation番号やseries pathをtask.json/eventへ追加しない。

automatic startの状態遷移は次のとおり。

```text
gate/preflight
    │
    ├─ reject/no execution → task-runを作らず通常rc
    │
    └─ child実行へ進む
          │
          ├─ auto off → task-runなし
          ├─ manual ID →既存rootへ記録、auto finishなし
          └─ auto on
                │
                ├─ generationなし → t944の初期generationを明示承認済みとして作成
                ├─ active generation → start_run
                ├─ closed generation → diagnostic、次世代は作らない
                └─ damaged/unknown/lock/FS failure → diagnostic、pytestは続行
```

CAP_OOM fallbackでは、同一 `_RecordingSession` が以下を行う。

1. bounded scope eventを記録。
2. fallback dispatchを実行。
3. compute sidecarを読み、同じtask-runへ二つ目の test eventを記録。
4. task_endを一度だけ追記。

## 新規・更新テストの nodeid 案と kill 対応

変異は段4で事前登録する。表の `mut-*` は実装時の登録名案であり、未実走の期待殺傷対応である。

| nodeid 案 | 対象 | 殺す具体的変異 |
|---|---|---|
| `test_task_run_generation.py::test_default_base_is_repo_sibling_and_linked_worktrees_share_series` | P2/A3 | HOME/XDG fallback、worktree path直下、common-dir digest namespaceへ戻す変異 |
| `test_task_run_generation.py::test_auto_root_override_is_ignored_and_no_repo_bytes_created` | A3 | `IZANAGI_TASK_RUNS_ROOT` をauto baseに使う変異、repo内にgenerationを作る変異 |
| `test_task_run_generation.py::test_external_start_observes_repo_head_not_generation_root` | A8 | `_git_head(root)`へ戻す変異、`repo_root`を無視する変異 |
| `test_task_run_generation.py::test_foreign_repo_root_cannot_bind_to_existing_generation` | A8 | repo Aのgenerationへrepo BのHEADを渡す変異 |
| `test_task_run_generation.py::test_external_symlink_or_evidence_namespace_is_rejected_before_create` | A3 | ledger到達後にだけbanned check、symlink追従、lock先行作成 |
| `test_task_run_generation.py::test_external_root_toctou_swap_creates_no_generation_bytes` | A3 | resolve後path open、fd再確認なし、`O_NOFOLLOW`除去 |
| `test_task_run_generation.py::test_pilot_closed_error_is_distinct_from_damaged_unknown` | A4/A5 | `except LedgerError`への拡大、`:551-552`を`PilotClosedError`へ変更 |
| `test_task_run_generation.py::test_closed_generation_returns_diagnostic_without_rollover` | A4 | `PilotClosedError` catch後の自動create、final/cap/ageで次世代作成 |
| `test_task_run_generation.py::test_explicit_open_next_generation_is_the_only_next_generation_path` | A4 | automatic callerからexplicit open APIへの到達、明示引数なし作成 |
| `test_task_run_generation.py::test_series_reader_rejects_one_bad_generation_instead_of_skipping_it` | A5 | healthy generationだけを返す、damaged generationを無視する変異 |
| `test_task_run_generation.py::test_series_reader_rejects_unknown_and_staging_entries` | A5/B2 | unknown entry/stagingを無視、番号欠落を許可する変異 |
| `test_task_run_generation.py::test_series_lock_timeout_returns_bounded_diagnostic` | A7 | blocking flock、timeoutなし、lock exceptionをpytestへ伝播する変異 |
| `test_task_run_generation.py::test_parallel_starts_count_unfinished_published_runs_against_cap` | B1 | task_end済みだけをcapに数える、root lock除去、cap後も同世代へ作る変異 |
| `test_task_run_generation.py::test_staging_generation_recovers_after_crash_between_init_and_publish` | B2 | mkdir→init→renameの原子性除去、staging無視、永久停止 |
| `test_task_run_generation.py::test_generation_documents_remain_exact_task_run_v1` | A4/A5/M5 | generation/version fieldをtask/eventへ追加、schema versionを増やす変異 |
| `test_task_run_generation.py::test_objective_rejects_path_like_text_without_changing_schema_version` | A9 | objectiveの`/`・`\`・`::`拒否を削除、schema_v1.jsonだけ/実装だけ変更する不一致 |
| `test_task_run_generation.py::test_managed_generation_write_is_rejected_by_cli` | M2 | CLI start/event/finishがmanaged generationへ直接書く変異 |
| `test_task_run_generation.py::test_selfcheck_failure_is_diagnostic_and_does_not_stop_pytest` | M4/M1 | selfcheck結果を無視、filesystem failureをchild rcへ置換、診断なし |
| `test_run_tests_testops_observation.py::test_unset_id_starts_one_lazy_auto_run_after_preflight` | A6/M1 | ID必須分岐を戻す、gate前に空task-run作成、routeごとの二重resolve |
| `test_run_tests_testops_observation.py::test_explicit_auto_off_preserves_exact_pytest_argv_and_call_shape` | A2 | pytest argvへmarker/flagを追加、auto-offを無視、child call shape変更 |
| `test_run_tests_testops_observation.py::test_four_gate_truth_table_is_unchanged_across_recording_modes` | A2 | gate定数の1項削除、callerの`PYTEST_ADDOPTS`変更、auto session前後の値差 |
| `test_run_tests_testops_observation.py::test_bootstrap_failure_emits_diagnostic_and_preserves_rc_output` | M1 | bootstrap exceptionを伝播、固定rcで上書き、stderr診断なし、child output破壊 |
| `test_run_tests_testops_observation.py::test_diagnostic_is_bounded_and_contains_no_path_selector_or_nodeid` | M1/A9 | `str(exc)`の直接出力、argv/path/node IDのdiagnostic混入 |
| `test_run_tests_testops_observation.py::test_direct_child_receives_auto_off_and_sidecar` | A6/B3 | direct childへのauto-off marker欠落、sidecar除去、nested auto start |
| `test_run_tests_testops_observation.py::test_force_dispatch_consumes_shared_sidecar_once` | B3 | dispatch sessionのsidecar未伝達、parent/child双方記録、counts/digest欠測 |
| `test_run_tests_testops_observation.py::test_bounded_scope_records_all_outcomes` | B4 | `CHILD_RC`以外の早期return、OOM/timeout event欠落 |
| `test_run_tests_testops_observation.py::test_cap_oom_fallback_uses_one_task_run_and_finishes_once` | B1/B3/B4 | fallbackで新task-run、event一件だけ、task_end二重/先行 |
| `test_run_tests_testops_observation.py::test_missing_sidecar_records_null_metrics_with_diagnostic` | B3/M1 | sidecar欠落を無言、record全体を中止、null metricsを不正に0へ置換 |
| `test_run_tests_testops_observation.py::test_manual_task_run_is_not_auto_finished` | M2 | manual IDへautomatic start/finishを適用する変異 |
| `test_run_tests_testops_observation.py::test_recording_signal_is_re_raised[bootstrap]` | A11 | bootstrapの`KeyboardInterrupt/SystemExit`をException扱いにする変異 |
| `test_run_tests_testops_observation.py::test_recording_signal_is_re_raised[record]` | A11 | append時のsignalを診断へ変換、rcを返して続行する変異 |
| `test_run_tests_testops_observation.py::test_recording_signal_is_re_raised[finish]` | A11 | finish時のsignalを吸収、task_endを偽追加する変異 |
| `test_run_tests_testops_observation.py::test_auto_trigger_is_unspecified_without_explicit_trigger` | M3/P3 | routeからbaseline/finalを推測、invalid triggerを別enumへする変異 |
| `test_run_tests_testops_observation.py::test_coverage_contract_names_only_run_tests_routes` | A10/B5/Q3 | READMEからraw pytest/mutation local/別cloneの未被覆明記を削除、「全走行」を追加する変異 |
| `test_pegasus_dispatch_compute.py::test_tests_task_env_allowlist_carries_only_recording_transport` | B3/A6 | sidecar/auto-offのallowlist欠落、manual ID/rootのallowlist追加 |
| `test_pegasus_dispatch_compute.py::test_job_script_preserves_sidecar_and_auto_off` | B3/A6 | job scriptのsidecar/auto-off除去、manual ID/root保持 |
| `test_pegasus_dispatch_compute.py::test_job_run_passes_sidecar_and_auto_off_to_tests_child` | B3/A6 | compute child envからsidecar/auto-offをpopする変異 |
| `test_task_run_ledger.py::test_pilot_cap_rejects_eleventh_published_run` | A4/B1 | 期待例外を通常型に戻す、未完taskをcapから除外する変異 |
| `test_task_run_ledger.py::test_pilot_age_cap_uses_manifest_clock` | A4 | age capを通常`LedgerError`へ戻し、generation managerが誤ってrolloverする変異 |
| `test_task_run_ledger.py::test_validate_root_classifies_damaged_and_unknown` | A3/A4/A5 | damaged/unknownをclosedと分類する変異 |
| `test_run_tests_task_run.py::test_sidecar_setup_and_record_failures_preserve_rc_and_output` | A1/M1 | sidecar/append exceptionでchild rc/stdout/stderrを置換する変異。診断行は許容し、child bytesの順序を固定 |
| `test_run_tests_task_run.py::test_scope_child_cannot_record_task_run_directly` | A6 | scope childへmanual ID/rootを渡す変異 |
| `test_run_tests_task_run.py::test_cap_oom_fallback_records_authoritative_compute_once` | B3/B4 | fallback event欠落、二重task、scope failureの未記録 |
| `test_run_tests_task_run.py::test_recording_interrupts_are_not_swallowed` | A11 | `KeyboardInterrupt`だけでなく`SystemExit`を吸収する変異 |

既存 nodeid の変更案:

- `test_opt_out_preserves_exact_command_and_call_shape` → `test_explicit_auto_off_preserves_exact_command_and_call_shape`
- `test_opt_in_keeps_pytest_argv_and_records_monotonic_result` → `test_manual_id_keeps_pytest_argv_and_records_monotonic_result`
- dispatch/scope child env assertionに `IZANAGI_TASK_RUN_AUTO_RECORD == "0"` を追加
- `test_sidecar_setup_and_record_failures_preserve_rc_and_output` は、child output保持に加えて固定 diagnostic codeを検査
- `test_cap_oom_fallback_records_authoritative_compute_once` は、record call 1回ではなく同一task-run内のroute eventとfinish回数を検査
- `test_tests_task_env_allowlist_is_exact` と `test_m7_dispatcher_request_allowlist_isolated_redundant_gate` は新transportの許可集合へ更新

## README 更新契約

対象: `output/task-runs/README.md:14-24,37-50,53-81,91-116`

更新内容:

- tracked `output/task-runs/` は凍結済み旧pilot archive。
- live automatic seriesは repo sibling。
- `generation-NNNNNN` は directory groupingでありschema generationではない。
- 10 runs / 14 days / final markerで世代は閉じる。
- closed generationからの次世代作成は explicit APIだけ。
- manual CLIはmanaged generationへwriteしない。
- automatic `tools/run_tests.py` のみ被覆対象。
- raw pytest、mutation local mode、別 clone、gate/preflight拒否は未被覆。
- `trigger=unspecified` は自動経路の既知の限界。
- repo外保存のため改竄検出は主張しない。
- task payloadへargv、selector、node ID、repo file pathを保存しない。
- generation横断report、retention、cross-clone共有、runtime全経路観測は今回実装しない。
- diagnosticは欠測を知らせるが、未記録走行の完全な分母を復元しない。

## production diff 見積り

| file | 見積り | 主な差分 |
|---|---:|---|
| `tools/task_runs/generation.py` 新規 | 220–290行 | sibling導出、fd安全検査、series lock、staging recovery、explicit open、series reader、sidecar lease、diagnostic |
| `tools/task_runs/ledger.py` | 35–55行 | `PilotClosedError`、`repo_root` binding、safe-root/TOCTOU補強、既存lock再利用 |
| `tools/task_runs/schema.py` | 15–25行 | `PilotClosedError`、objective privacy pattern |
| `tools/task_runs/schema_v1.json` | 3–8行 | v1のままobjective patternをschema実装と同期 |
| `tools/task_runs/__init__.py` | 2–5行 | 新型/API export |
| `tools/task_runs/cli.py` | 15–30行 | managed generation write拒否、`validate-series`、help |
| `tools/run_tests.py` | 150–220行 | lazy session、全route lifecycle、sidecar、M1 diagnostic、B4 outcome、A11 signal |
| `tools/pegasus/dispatch_compute.py` | 15–30行 | sidecar/auto-offのallowlist、job script、compute child env |
| **production code 小計** | **455–663行** | briefの320–505行より増える |
| `output/task-runs/README.md` | 35–55行 | live series、Q1〜Q3、被覆・privacy・trigger契約 |

briefの320–505行との差は、元の「run_tests.pyだけ」の見積りに以下が含まれていなかったためである。

- 自動 rollover禁止に伴う explicit generation APIとstaging recovery
- series全体fail-closed reader
- dispatch transportのsidecar受け渡し
- bounded scopeの複数event lifecycle
- CLIによるmanaged generation write拒否
- schema実装と`schema_v1.json`のprivacy同期

この差分を142行へ圧縮する目標は採用しない。安全面を削る場合は実装せず裁定へ戻す。

## 静的検査と実装後の受入手順

段2時点で行う検査:

- `git status --short --branch`
- `rg` による全caller・env marker・payload fieldの棚卸し
- changed Python の `ast.parse` による構文検査。pycacheを生成しない方式を使う
- `git diff --check`
- gate本体・定数表へのhunkがないことの確認
- `schema.py` と `schema_v1.json` のobjective pattern同期確認
- task/event/sidecar/diagnosticへのargv・selector・node ID・repo file path経路のsource scan
- auto経路で`IZANAGI_TASK_RUNS_ROOT`をbaseに使っていないことのsource scan

実装後のpytestは、指定どおり必ず `tools/run_tests.py` 経由で行う。素の pytest、mutation local mode、別 clone はこのpilotの受入結果・緑判定・被覆主張に含めない。

未実施のものを緑と報告してはならない。関連テスト、`tools/check_codex_agents.py`、`tools/check_docs.py`、commit後の`tools/check_ai_provenance.py`は実装 waveの親が別途実施する。

## 総括

結論は、Q1〜Q3に適合する有界 pilot の実装骨格は成立するが、元のP1をそのまま採用せず、dispatch transportをUnit Bへ追加する必要がある。未確認事項は、staging crash recoveryの実FS挙動、共有 sibling transportがcompute nodeから可視であること、sidecar I/O失敗時の実child rc保持、4 gate characterizationと20件のmutation殺傷結果である。sandbox=read-onlyのためpytest・mutation・受入走行は未実施であり、現時点で緑とは報告しない。