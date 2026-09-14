# [T-2497] role sink 非干渉 node の report status 検査 — 変異台帳と実測

`authority: none` / `default_effect: no-state-change`。
可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc であり、本書はその射影ではない。

- wave: `dev-wave-t2497-role-sink-status` (branch `worktree-dev-wave-t2497-role-sink-status`)
- base commit: `7dc4ecc39`
- 実装 commit: `6babfe8e0` (`orchestrator/tests/test_p3_autonomous_workload_trial.py` のみ、71 insertions / 2 deletions)
- 変更面: test file 1 件。production file は不変 (D1847)。

## 1. 段 1 の実測 — DW-O13 の到達可能性

既存 node を base commit のまま 1 回走らせ、`--basetemp` を repo 外へ向けて
`run_trial` が書いた `report.json` を走行後も残した。

- 結果: `1 passed in 9.77s` (pytest session の経過時間であって node 単体の所要ではない)。
  Pegasus `gen_S@nqsv` request 996883.nqsv へ dispatch された。
- 32 本の `report.json` を `jq` で読んだ集計:
  - `.status` — **32/32 が `"complete"`**
  - `has("fatal_error")` — **32/32 が `false`**
  - `.cells[0].stop_reason` — **32/32 が `"fixed-generation-budget"`**

よって `assert report["status"] == "complete"` は現行構成で到達可能であり、baseline を赤にしない。

## 2. pin 閉包 (DW-O09)

`git grep -ln` で当該 test 名を持つ tracked file は 8 件 (worklog archive 4・decisions・failures・
`acceptance_duration_ledger.json`・当該 test file)。`FROZEN_MANIFEST`・generator source hash pin・
registry・trust root 側の直接参照は未発見。当該 test に `pytest.mark` も `xdist_group` も無い。
所要台帳の loader (`orchestrator/tests/conftest.py:1546`) は fail-soft で完全性 gate ではない。

**「pin 0 件」とは書かない。** directory 列挙から動的に対象を作る型の gate は名前検索に現れず、
その網羅監査は未実施である。段 3 の 2 レンズが独立に同じ限界を指摘し、
うち 1 レンズは `tools` / `hooks` / `.claude` / `.codex` と `conftest.py:2123` 以降の収集処理を
独自に検索して同じ「直接参照は未発見」に達した。

## 3. 焦点走

変更 test file 全 node + node 集合を pin する meta-test 3 群を 1 投入で直列に流した。

- 対象: `test_p3_autonomous_workload_trial.py` 全体、
  `test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`、
  `test_acceptance_schedule_order.py`、`test_pytest_collection_config.py`
- 結果: **423 passed / 0 failed (105.65 秒)**

親は別経路でも既存 test の消失を検査した。`grep -oE "^def (test_|_)"` の集合 diff で
**277 → 279、削除・改名 0 件、追加は helper 1 件と負例 node 1 件のちょうど 2 件**。
段 6 レンズ B は AST 比較で 230 → 231 (test 関数のみ) と報告し、同じ結論に達した。

## 4. 変異台帳

harness = `tools/mutation_harness.py`、`--runner-mode dispatch --detached`。
runner = `python3 tools/run_tests.py --force-dispatch <node...> -rf`。
repo_head = `6babfe8e07b7743307313d2d6c8a35054050510d`。

### 4.1 probe 走 (観測 node を集める。全件 SURVIVED で登録)

spec sha256 = `50ecb598cca2b72827430c928b29274c7505697a34431ba0d10d77b4194b1706`。
runner の選択 node = 本 node + 負例 node。baseline = PASSED (`2 passed in 9.29s`)。

| id | 実測 | 観測 node |
|---|---|---|
| M1 helper の assert 本体を除去 | MISMATCH | 負例 node |
| M2 述語を `report.get("fatal_error") is None` へ弱化 | MISMATCH | 負例 node |
| M3 受理を `in {"complete","partial"}` へ拡大 | MISMATCH | 負例 node |
| M4 `run_wire` の helper 呼出し行を除去 | MISMATCH | 本 node |
| M5 producer の status 算出を partial 固定 | MISMATCH | 本 node |
| M6 述語を `stop_reason not in {...}` へ書換え | SURVIVED | なし |
| M7 呼出し行を `cell = report["cells"][0]` へ置換 | SURVIVED | なし |

観測 node は段 6 レンズ A の静的予測と完全に一致した。

### 4.2 final 走

spec sha256 = `1200be847fca7c9480720025a88538fb9d777785b11cec6e384673d89ed81417`。
baseline = PASSED。summary = `KILLED 5 / SURVIVED 2 / MISMATCH 1 / matching 7 / registered 8`。

| id | 期待 | 実測 | 一致 |
|---|---|---|---|
| M1 | KILLED (負例 node) | KILLED | ○ |
| M2 | KILLED (負例 node) | KILLED | ○ |
| M3 | KILLED (負例 node) | KILLED | ○ |
| M4 | KILLED (本 node) | KILLED | ○ |
| M5 | KILLED (本 node) | KILLED | ○ (ただし理由が誤り。4.3 参照) |
| M5' | SURVIVED | **MISMATCH (KILLED)** | × |
| M6 | SURVIVED | SURVIVED | ○ |
| M7 | SURVIVED | SURVIVED | ○ |

注入 diff の sha256 は変異ごとに相異なり、`anchor_counts` は各置換 1 件だった。
したがって SURVIVED は no-op ではない (DW-M04)。

### 4.3 erratum — M5 / M5' の取り下げ (DW-M01 / DW-M02)

M5' の MISMATCH を受けて赤の**本文**を読んだところ、M5 の赤は追加した検査ではなかった。

```
orchestrator.campaign.autonomous_trial_completeness.AutonomousTrialCompletenessError:
[terminal-projection] report status must be 'complete'
orchestrator/campaign/autonomous_trial_completeness.py:448
```

`_check_status_projection` (`autonomous_trial_completeness.py:2886`) が producer と同じ述語
(cells 数 / `fatal_error is None` / stop_reason / admission) を独立に再計算し、
`report["status"]` と一致しなければ落とす。この gate は
`p3_autonomous_workload_trial.py:3902` から `run_trial` の末尾で**無条件に**呼ばれる。

**F820 が言う「同じ入力を拒否する層が内側にある」状態であり、M5 は実効 gate を測っていない。**
M5 と M5' を取り下げ、初回結果は本節に残す。

### 4.4 再照準 — 2 回続けて内側の層に masked された

| 試み | 変異 | 実測 | 殺した層 |
|---|---|---|---|
| 2 回目 | report へ `fatal_error` を直接注入 | (静的に却下) | 同 file 2405「journal event を伴わない `fatal_error`」 |
| 3 回目 M8 | `cell.pop("_deferred_wall_generation", 1)` で wall budget 経路を強制 | MISMATCH (両 node) | `[workload-coverage] wall-budget terminal event has no missing workload` |

probe2 spec sha256 = `9a3ffa38c570a401317796fd62859aa0f9e85fb5ff87931bc420de02b04caf1e`。baseline = PASSED。

**この 3 度の mask 自体が実測である** — report の完了性について production 側に既に厚い層がある。

### 4.5 差分確定走 — DW-M08 の「新テストだけが検出する差分」

4 回目の再照準で差分が出た。`_run_pending_critics` (`p3_autonomous_workload_trial.py:3462`) の
末尾へ `raise RuntimeError(...)` を注入すると、cell が完成し 4 role の payload も WAL も揃った後に
`supervisor-error` が立ち、内側 gate をすべて通過した**本物の partial report** が返る。

spec sha256 = `58d7e4438cfda75e7cb518037b93ac2fe9f4ad5bb81458f47200a94b9a7d7e80`。
runner の選択 node = **本 node のみ**。baseline = PASSED。
summary = `KILLED 1 / SURVIVED 1 / MISMATCH 0 / matching 2 / registered 2`、rc=0。

| id | 変異 | 期待 | 実測 |
|---|---|---|---|
| M9 | 上記 `raise` 注入だけ | KILLED (本 node) | **KILLED** ○ |
| M9' | M9 + 呼出し接続を `cell = report["cells"][0]` へ外す | SURVIVED | **SURVIVED** ○ |

M9 における本 node の赤の本文は次のとおりで、**追加した検査そのもの**である。

```
E       AssertionError: wire=00000: expected complete, got status=partial
E       assert 'partial' == 'complete'
```

**同じ producer 欠陥に対して、検査ありでは赤・検査を外すと緑になる。**
これが受理集合が真に縮まったことの実測である。

なお両 node を選択した probe3 では、M9 / M9' とも負例 node が
`[state-machine] supervisor-error cell 'ycsb-a' has invalid role history` で落ちた。
これは注入した `raise` が負例自身の前提を壊す巻き添えであり、本 node の差分とは別事象である。
単一理由性を保つため、差分確定走では本 node だけを選択した。

## 5. 生存する弱化 — 塞がずに測った

M6 と M7 は段 6 レンズ A が静的に見つけ、親が「塞がず測って記録する」と裁定した生存変異である。

- **M6**: helper の述語を `report["cells"][0]["stop_reason"] not in {"supervisor-error", "role-invalid"}`
  へ書き換えると、負例の partial 2 形はどちらも同じメッセージで拒否されるので負例は通り、
  本 node の `fixed-generation-budget` も通る。**status を一度も読まない helper が両 node を緑にできる。**
- **M7**: 呼出し行を `cell = report["cells"][0]` へ 1 行置換しても両 node は緑のまま。

いずれも D387 (gate と検査を同じ主体が変更できる限り、repo 内の挙動検査は意図的な弱体化への
完全な防壁ではない) の射程である。負例 node の docstring にも明記した。

## 6. 受入全走

`tools/dev_wave_wait.py acceptance` を 1 回投入し、attempt 1 で通った。
投入時の login node load average は `43.00 / 58.39 / 54.62` (1分 < 5分 < 15分 の下降局面、1分 ≤ 50)。

- verdict = `child-green`、`child_rc = 0`、`red_nodeids = []`、`flake_nodeids = []`
- tested_main = `c347c049bdab05491a70ebdd8df19aee3d642aca`
- tested_tip = `d8556c3ed5f59c8ff46c34e9d480ac02332aa610`
- 件数 = **23315 passed / 68 skipped / 0 failed**

tool が main を wave branch へ post-claim merge した (`d8556c3ed merge main`)。
merge 後の main 比の変更面は `orchestrator/tests/test_p3_autonomous_workload_trial.py` 1 件だけである。

## 7. 子の逐語

`verbatim/` に段 2 plan・段 3 consult 2 本・段 5 author・段 6 review 2 本・段 6 fix の出力を凍結する。
段 5 / 段 6 fix の実装子はいずれも sandbox から dispatch できず (`qstat -Q preflight rc=1`、runner rc=16)、
**実走 0 件**を正直に申告した。実測はすべて親が行った。
