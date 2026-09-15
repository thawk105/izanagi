## 最小差分

変更対象は [s8b_floor_campaign.py:6283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2596-abort-not-runtime/orchestrator/campaign/s8b_floor_campaign.py:6283)。`self.measure_fn(...)` の直後、既存の `except (RuntimeError, subprocess.TimeoutExpired)` の**前**に2行挿入する。

```diff
             scale_point = self.measure_fn(
                 cell_id, attempt_id, binary, cell["records"], cell["threads"],
                 cell["workload"],
             )
+        except CampaignAbort:
+            raise
         except (RuntimeError, subprocess.TimeoutExpired) as exc:
             measure_error = exc
```

`CampaignAbort → FloorCampaignError → RuntimeError` という継承関係（同:360、408）のため、順序が必須。bare `raise` で元の例外を保持する。precedence、post-probe の既存位置、`_finish_session` は変更しない。

以下、`C` は `orchestrator/campaign/s8b_floor_campaign.py`、`L` は `orchestrator/campaign/s8b_floor_attempt_launcher.py`、`R` は `orchestrator/calibrator/runner.py`、`T` は `orchestrator/tests/test_s8b_floor_campaign.py` を指す。行番号は変更前。

## 射程の比較 (P1)

**結論：`CampaignAbort` だけの再送出を採用する。**

| 案 | 効果 | 裁定材料 |
|---|---|---|
| `CampaignAbort` を再送出 | 停止命令が `launch_failure` へ変換される問題を修復 | brief の局所修正と一致 |
| `FloorCampaignError` 全体を再送出 | 非 abort の親例外も従来と異なる扱いになる | 今回確認した既定測定経路には必要性がない。C:7955 の aborted 記録も親例外全体には対応していない |

**既定の実装経路から非 `CampaignAbort` の `FloorCampaignError` が到達するか：no。**

経路は次のとおり。

1. C:7926 で `_wrap_admission_aware_measure` を作り、C:7938 で `_Runner.measure_fn` に渡す。
2. C:6279 → C:5978 の `measure_attempt`。
3. admission 不在は C:5983、座標不一致は C:5988、admission 拒否の翻訳は C:6002。いずれも `CampaignAbort`。
4. C:6008／6012 から実測 callback。既定 closure は C:7871、`measure_point` 呼び出しは C:7880／7886。
5. `runner.py` は `FloorCampaignError` を参照・生成していない。起動失敗の処理は R:963、1184、plain `RuntimeError` の送出は R:967、1188、1281 など。

C:7924 の `FloorCampaignError` は admission の予約・確定時に発生し、`runner.run()` **より前**なので対象 except に入らない。

ただし、**注入可能な callback を含めた到達可能性は yes**。任意の callback が親例外を投げれば、C:6012 → C:6279 → C:6283 と到達する。これは既定実装での発生箇所とは区別する必要がある。注入 callback の親例外まで意味を変更する根拠は今回の scope にない。

## β-7 との整合 (P2)

**結論：今回の `CampaignAbort` 再送出では post-probe を実行しない。plain `RuntimeError`／`TimeoutExpired` では従来どおり実行する。**

根拠は以下。

- β-7 の具体的な処理は、測定起動失敗を保持し、post-probe の競合を `launch_failure` より優先して session を記録するもの（C:6275、6286、6330）。
- admission wrapper の3つの abort は実測 callback 呼び出し（C:6008／6012）より前に発生する。
- `CampaignAbort` は session の除外理由へ落とさず、外側の C:7955 が `terminal/status=aborted` を記録して再送出する。
- 現実装も真の `finally` ではない。たとえば `_SimulatedCrash(Exception)` は既存 except を通らず、post-probe を実行しない（T:10461、10647）。

ただし、**冒頭 C:32 の「measure が例外を投げた経路でも必ず」を文字どおり全例外へ適用すると、この結論とは一致しない**。「全 rep 起動不能」という局所コメントと既存 β-7 テストに基づき、session として分類する測定失敗への規定と解釈する。これは本文に明記済みの例外規定ではなく、今回の裁定材料である。

`strict_probe` 自身も `CampaignAbort` を投げる。

- C:1711：timeout
- C:1713：`OSError`
- C:1717：競合の有無を確定できない

abort 後にも post-probe を実行すると、そこで発生した別の `CampaignAbort` が表に出て、元の admission 拒否が外側の terminal reason から失われうる。今回の bare `raise` では post-probe に進まないため、この入れ替わりは起きない。

## 受理集合が変わらない根拠

**certified 経路：対象 except より前に分岐して return する。**

```text
C:6232 _Runner._run_session
  → C:6259 certified_attempt_context があれば return
  → C:8874 _run_certified_floor_session
  → C:8998 launch_probed_floor_attempt
  → L:1605 / 1619 _launch_floor_attempt
  → L:1394 _capture
```

launcher は独自に failure evidence を作り（L:1400）、独自の `finally` で post-probe を実行する（L:1404）。open 時の例外も L:1443 で処理する。`OpenedFloorAttempt.failure` を使う別構造であり、C:6283 には戻らない。

**最終 inspection：`runner.run()` の終了後に別の try 節から呼ぶ。**

- C:7954：`runner.run()`
- C:7964 → C:6674／6680：`_inspect_holdout_admission` → 公開 inspection
- C:7971：inspection 拒否を `artifact-invalid` として扱う
- C:8002：live admission を含む結果自己検査
- finalize-pending resume も C:7820 から inspection を直接呼ぶ

したがって、この2行は certified の判定条件、inspection の入力検証・受理条件を変更しない。**非 certified の abort が inspection まで進まなくなることは、今回意図する変更**である。

## 既存テストへの波及

**静的確認では、この最小差分で期待値変更が必要になる既存テストは見つからない。実走結果ではない。**

以下の nodeid はすべて `orchestrator/tests/test_s8b_floor_campaign.py::` を接頭辞とする。

| measure が投げる型 | 該当 nodeid／発生箇所 | 予想 |
|---|---|---|
| `CampaignAbort` | 直接投げさせる既存テストなし | 今回の欠落 |
| plain `RuntimeError` | `test_post_probe_runs_on_launch_error_and_competing_takes_precedence`。T:9903 の `raise_for` → T:965 | 従来どおり post-probe が走り、競合が優先 |
| `TimeoutExpired` | measure に投げさせる既存テストなし | T:9924 は probe の timeout |
| `_SimulatedCrash` | 下記一覧 | `RuntimeError` 系ではなく、従来どおり伝播 |
| `Cut10Crash(BaseException)` | `test_resume_runner_produces_one_retry_from_admission_selected_recovery`、T:12824、12828 | 従来どおり伝播 |

`_SimulatedCrash` を measure から投げる既存 nodeid は以下。T:1554、10948 の直接送出と、T:10641 の `_crash_at` 利用箇所を確認した。

```text
test_resume_reuses_manifest_perf_preflight_without_reprobing
test_m_running_rejects_invalid_perf_preflight_event
test_resume_forward_only_skips_completed_and_crashed_seqs
test_resume_rejects_tampered_binary_but_succeeds_when_untampered
test_resume_rejects_tampered_manifest_schedule
test_resume_rejects_duplicate_session_start
test_resume_does_not_reissue_retry_slot_after_retry_start_crash
test_official_resume_validates_certificate_and_completes
test_resume_under_unchanged_current_contract_generation_completes
test_resume_rejects_recorded_g1_when_current_contract_is_g2_before_calibration
test_official_resume_rejects_tampered_certificate
test_official_resume_rejects_launch_start_utc_not_bound_to_certificate
test_official_resume_rejects_extra_launch_start_key
test_official_resume_rejects_renamed_run_dir
test_official_resume_rejects_certificate_time_not_bound_to_run_id
test_pilot_resume_rejects_launch_certificate_contamination
```

`_forbid_measure`（T:8624）などの `AssertionError` は、呼ばれないことを検証する sentinel。正常なテスト経路での測定失敗とは区別する。build・scan・最終 inspection で投げる `RuntimeError`／`FloorCampaignError` も、対象 except を通らない。

特に維持すべき回帰確認は次の2系統。

- `test_post_probe_runs_on_launch_error_and_competing_takes_precedence`
- `test_admission_failure_creates_no_result_pending_bytes` の既存パラメータ全件。例外源は T:14495 の最終 inspection であり、measure ではない。

## 新設テスト 2 本

**配置：T:9912 の既存 post-probe テスト終了後、T:9914 の parametrize decorator より前に2本を追加する。**

共通で `tmp_path`、`_freeze_document`、`_freeze_sha`、`_verified_freeze`、`_protocol`、`_run_campaign`（T:815）、`_only_run_dir`（T:990）、`_read_journal_lines`（T:1747）を再利用する。`_run_campaign` の既定 pilot と実際の admission wrapper を通し、対象 except を差し替えない。

**負例：`test_measure_campaign_abort_propagates_without_launch_failure`**

- 四引数 callback を作り、最初の呼び出しで事前生成した `abort = CampaignAbort("fixture measure abort")` を投げる。
- callback 到達回数・cell ID を記録する。
- probe は通常の `(1, "", "")` を返す。callback 到達後の probe 呼び出しだけ別カウンタに記録する。
- `pytest.raises(CampaignAbort)` に加え、`caught.value is abort` を確認する。
- callback は1回、callback 到達後の probe は0回。
- 実ファイルの journal を読み、次を確認する。

```python
starts = [r for r in journal if r.get("event") == "session-start"]
assert len(starts) == 1
assert starts[0]["cell_id"] == measured_cell_id
attempt_id = starts[0]["attempt_id"]

assert not any(
    r.get("event") == "session"
    and r.get("attempt_id") == attempt_id
    for r in journal
)
assert not any(
    r.get("attempt_id") == attempt_id
    and r.get("excluded_reason") == "launch_failure"
    for r in journal
)
assert journal[-1]["event"] == "terminal"
assert journal[-1]["status"] == "aborted"
assert journal[-1]["reason"] == str(abort)
assert not (run_dir / "result.json").exists()
```

session-start と callback 到達を先に要求し、事前 gate に止められただけの空振りを防ぐ。

**正例：`test_measure_runtime_error_records_launch_failure`**

- T:948 の `_make_measure_fn` を使う。
- `raise_for={"rr79::system_gate"}`、他セルは `_BASE_TPS` の正常値。
- pre/post とも `(1, "", "")`。競合優先で `launch_failure` が隠れない設定にする。
- `_run_campaign` の返却を要求し、実 journal を読む。
- 当該セルの `session` 行が**非空**で、すべて次を満たすことを確認する。

```python
assert rows
assert all(r["excluded_reason"] == "launch_failure" for r in rows)
assert all(r["valid"] is False for r in rows)
assert all(r["session_median"] is None for r in rows)
assert all(r["probe_after"]["competing"] is False for r in rows)
assert all(r["exec_failures"] == protocol["reps"] for r in rows)
```

さらに各行の `attempt_id` に対応する `session-start` が存在し、journal に `terminal/status=aborted` がないことを確認する。固定本数の新たな期待値は追加せず、既存 retry 契約をそのまま使う。

## 変異事前登録の候補

nodeid の接頭辞は前節と同じ。

| 変異内容 | 期待して赤くなる nodeid |
|---|---|
| 追加した `except CampaignAbort: raise` を削除する | `test_measure_campaign_abort_propagates_without_launch_failure` |
| 追加節を `except RuntimeError: raise` に広げる | `test_measure_runtime_error_records_launch_failure` |
| 追加節で bare `raise` の前に `strict_probe(self.probe_fn)` を実行する | `test_measure_campaign_abort_propagates_without_launch_failure`。callback 後 probe 回数が0でなくなる |

負例の直接注入は実 admission を通過した後なので、先行する admission／binary gate で変異が隠れない。削除変異が最終 inspection で別途拒否されても、**元の例外オブジェクトの伝播・当該 session 行の不在**を要求するため代替検出で合格しない。

候補から外すもの：

- **freeze・binary・admission の入力を事前に壊す変異**：先行 gate で止まり、C:6283 の修正を検証しない。
- **certified 分岐や最終 inspection の変更**：別の検査面であり scope 外。
- **再送出型を `FloorCampaignError` に広げるだけの変異**：今回の2本はともに通る。既定経路に非 abort 親例外の発生箇所も確認できず、この2本による有効な殺傷候補ではない。

## 総括

推奨は **`CampaignAbort` の先行再送出2行と、上記テスト2本**。plain 起動失敗の post-probe・precedence は維持する。

P1 は「既定経路では非 abort 親例外の到達なし、注入 callback なら到達可能」。P2 は「session 起動失敗への β-7 を維持し、campaign abort は即時伝播」と裁定する。冒頭の全称表現との差は、解釈上の所見として親へ渡す。

コード編集・commit・pytest 実走は行っていない。以上は静的確認に基づく実装プラン。