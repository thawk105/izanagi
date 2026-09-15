## 現状の非対称

行番号は確認した現行ファイルを基準とする。以下、`A` は `orchestrator/campaign/s8b_holdout_admission.py`、`T` は `orchestrator/tests/test_s8b_holdout_admission.py`、`C` は `orchestrator/campaign/s8b_floor_campaign.py`。

- `A:5822–5841` は canonical failed planned の完了行を legacy 候補に残す。
- `A:5851–5852` は使用済み trigger の registry recovery 候補を収集前に除外する。
- その結果、同じ trigger に両根拠があっても `A:5860` を通過し、`A:5881–5885` が legacy 認可を返す。
- consume は `A:5767` の `len(trigger_sessions) + len(recovery.candidates) != 1` で同じ履歴を拒否する。

production の到達経路は `C:6524` の `run()` → resume 分岐 `C:6548` → `_retry_round` 呼出し `C:6595` → `_round_failed_cells` → `_retry_authorization`（`C:6164–6190`）。新しい Runner では認可キャッシュが空になる（`C:6103`）ため、retry start が残った履歴を再問い合わせする。

## 実装プラン (file:line)

**`A:5881–5885` の legacy 返却ブロックだけを次に置換する。**

```python
        if legacy:
            trigger = str(legacy[0]["attempt_id"])
            evidence = _floor_registry_recovery_evidence_locked(
                state, records=records, trigger=trigger,
            )
            if evidence.candidates:
                raise HoldoutAdmissionError(
                    "retry trigger has both completion and recovery evidence"
                )
            return FloorRetryAuthorization(
                trigger_attempt_id=trigger,
                source="legacy-failed-session",
            )
```

ここでは legacy 完了候補が既に一意なので、consume の件数条件を満たすには recovery 候補が **0 件**でなければならない。`evidence.candidates` の非空判定で十分であり、検証済み recovery への絞り込みや replay は不要。

**P1 は比較検討したうえで採用する。**

- 使用済み除外を削除するだけの案は、使用済み recovery を再び認可候補にし、既存の一回限定設計を変える。
- legacy も使用済み除外する案は、正当な複数 retry と resume を壊す。
- 収集ループの並べ替えや候補キャッシュの追加は、この局所チェックより変更範囲が広い。
- `None` は消費側の拒否を表現しない。既存の逆方向チェックと同じ例外文言を再利用する。

## 不変条件の保持

- **I1:** consume と最終 inspection は変更せず、query の誤った legacy 認可だけを拒否へ変える。
- **I2:** `used_recovery_triggers` を legacy の除外条件に加えず、同じ trigger による次の retry を許す。
- **I3:** registry 不在・slot identity 不明では既存 helper が空候補を返すため、この追加条件は発火しない（`A:5455–5462`）。
- **I4:** production の一ブロックと既存 `T` へのテスト追加に限定し、新規ファイル・gate・台帳・framework を作らない。
- **I5:** `A:5494` 付近の既存候補収集結果をそのまま使い、使用済み・座標の正否・authority・replay 成否で候補を減らさない。
- **I6:** production 差分を `floor_retry_trigger_for_round` 内に閉じ、共有 helper の意味を変えない。

## 追加テスト

### 確認した既存 helper

| helper | 実在箇所 | 用途 |
|---|---|---|
| `_issued_cell` | `T:1825` | 実 admission、schedule、planned start を作る |
| `_append_journal_rows` | `T:1893` | journal 行を追記する |
| `_write_verified_recovery_registry` | `T:1900` | 対象 planned slot の registry と独立 receipt を作る |
| `_pin_test_recovery_authority` | `T:44` | テストの authority を独立に pin する |
| `_issued_inspection_kwargs` | `T:1854` | 同じ履歴の最終 inspection 入力を作る |

全追加先は **`T:3543`、既存の両根拠排他テスト直後**とする。

### 1. 使用済み trigger の両根拠を拒否する

**関数名:**  
`test_used_legacy_trigger_query_rejects_registry_recovery_candidates`

`registry_case` を `"valid-one"`、`"corrupt-one"`、`"valid-plus-corrupt"` で parameterize する。

**journal / registry の構築**

1. `_issued_cell` で得た planned attempt を consume し、planned start を保存する。
2. `_write_verified_recovery_registry(..., trigger_start=planned_start)` と `_pin_test_recovery_authority` を使う。
3. `T:3522–3533` と同じ形で、同じ attempt の failed planned 完了行と、それを trigger にした `retry1` の start を追記する。
4. registry の変形は次のとおりとする。
   - `valid-one`: helper の出力をそのまま使う。
   - `corrupt-one`: 唯一の recovery の `configuration_id` を `"corrupt-extra-coordinate"` に変える。対象 start hash と receipt の対象 hash は維持し、canonical JSONL で書き戻す。
   - `valid-plus-corrupt`: `T:3285–3300` の既存手順で、座標だけ異なる recovery を追加する。

**assert**

```python
with pytest.raises(
    admission.HoldoutAdmissionError,
    match=r"^retry trigger has both completion and recovery evidence$",
):
    admission.floor_retry_trigger_for_round(
        admitted, round_no=planned_start["round"],
    )
```

加えて、同じ履歴の `consume_attempt_ticket(..., attempt_id=retry_id)` が `"exactly one"` で拒否されることを確認する。query 呼出し前後の journal bytes が等しいことも確認する。

**修正前→修正後:** 3 ケースとも修正前は使用済み trigger の recovery を丸ごと見落として認可を返すため失敗し、修正後は未除外の候補が非空なので通る。`corrupt-one` は座標不正を理由に候補を捨てる実装を検出する。

### 2. registry 不在で使用済み legacy trigger を再認可する

**関数名:**  
`test_used_legacy_trigger_without_registry_authorizes_second_retry`

**journal / registry の構築**

- `_issued_cell` と `_append_journal_rows` を使う。registry は作らない。
- failed planned 完了行を追加し、query が legacy 認可を返すことを確認する。
- `retry1` start を追加して consume する。完了行を追加せず、consume 後の crash 状態を残す。
- query を再実行して同じ認可を確認する。
- `seq=len(state.schedule)+1`、`retry_ordinal=2`、同じ planned trigger の `retry2` start を追加し、consume する。

**assert**

- 前後の query がともに次と等しい。

```python
admission.FloorRetryAuthorization(
    trigger_attempt_id=attempt_id,
    source="legacy-failed-session",
)
```

- retry1、retry2 の consume token の `attempt_id` がそれぞれ一致する。
- `permitted_run_once_calls == protocol["reps"]`。

**修正前→修正後:** これは前後とも通る保存すべき正例である。使用済み legacy の一律除外や、空候補まで拒否する変異で失敗する。

### 3. production resume が同じ legacy trigger で retry2 を作る

**関数名:**  
`test_resume_campaign_preserves_used_legacy_trigger_without_registry`

既存 `T` 内で `test_s8b_floor_campaign` をローカル import し、以下の実在 helper を再利用する。

- `_freeze_document:344`、`_freeze_sha:360`、`_verified_freeze:367`、`_protocol:371`
- `_run_campaign:815`、`_make_measure_fn:948`
- `_only_run_dir:990`、`_read_journal_lines:1747`

**journal / registry の構築**

- retry 枠 2 の protocol を使い、registry は作らない。
- measure fixture は最初に呼ばれた cell を対象とし、その初回だけ `RuntimeError` を上げ、実際の failed planned 完了を作る。他 cell は通常の fake measurement を返す。
- 同じ cell の次の measurement 呼出しで専用の `BaseException` を上げる。retry1 の start と consume 証拠が残り、完了行は残らない。
- `_run_campaign(..., resume_dir=run_dir)` を、成功する measure fixture で再実行する。
- query は実関数へ委譲する spy で記録し、戻り値を偽装しない。

**assert**

- crash 時点で対象 cell の failed planned 完了と retry1 start があり、retry1 完了はない。
- resume 時の実 query が、同じ planned attempt の `legacy-failed-session` を返す。
- `resume-start` が増え、対象 cell の retry ordinals が `[1, 2]`、両 start の trigger が同じ planned attempt。
- retry2 が有効に完了し、campaign の `status == "completed"`。

**修正前→修正後:** 前後とも通るべき production 正例であり、使用済み legacy を排除する退行を検出する。F591 に従い、新しい Runner の `run()` から実 query への到達も確認する。

**要求 3(e) の扱い:** 正例まで「修正前に落ちる」とは主張できない。欠陥検出はテスト 1 の全 parameter、受理集合の保存はテスト 2・3 が担う。

## 通る正例

保存する履歴は次の順序である。

```text
planned start P
→ failed planned completion P
→ retry1 start（trigger=P）
→ retry1 consume
→ crash
→ 新 Runner で resume
→ query が legacy-failed-session(P) を返す
→ retry2 start（trigger=P）
→ retry2 consume・有効完了
```

registry は不在で、retry 枠が一つ残っている。追加チェックの `evidence.candidates` は空なので認可を維持する。`C:6414–6419` の既存 while ループが retry2 を作る。

既存の recovery 連鎖正例 `T:3096` も焦点走に残し、F590 の履歴再検査の退行を監視する。

## 焦点走の対象

以下は名前の類推ではなく、確認した import／呼出し参照から選んだ集合。パスの共通接頭辞は `orchestrator/tests/`。

| 対象 file | 参照根拠 |
|---|---|
| `test_s8b_holdout_admission.py` | `:21` が変更 module を import |
| `test_s8b_floor_campaign.py` | `:62` → `C:127,6073` → 実 query |
| `test_s8b_floor_contract.py` | `:18` → production campaign |
| `test_s8b_attempt_registry.py` | `:29` が admission を直接 import |
| `test_s8b_floor_attempt_launcher.py` | `:26` が admission を直接 import |
| `test_s8b_floor_stats.py` | `:62` が admission を直接 import |
| `test_s8b_holdout_freeze.py` | `:2123,2402` が admission を直接 import |
| `test_s8b_oracle_driver.py` | `:1534` → driver `:44` → admission |
| `test_s8b_oracle_n_pilot.py` | `:19` → n-pilot `:39,1325` → admission |
| `test_s8b_ratified_freeze.py` | `:42,44` → campaign／holdout freeze → admission |
| `test_s8b_ratified_verify.py` | `:868` が admission を直接 import |
| `test_s8b_terminal_evidence.py` | `:20` が admission を直接 import |

これは焦点走の集合であり、全間接 consumer の網羅集合ではない。親の受入全走を置き換えない。実行は親が `tools/run_tests.py` 経由で行う。

## 変異事前登録の候補

変異箇所はすべて **`A:5881` 起点で追加する `if evidence.candidates:`**。実装後の行番号で登録する。

| 変異 ID | 置換内容 | KILL する test |
|---|---|---|
| `MUT-T2595-LEGACY-RECOVERY-OMIT` | `if evidence.candidates:` → `if False:` | テスト 1 の全 parameter |
| `MUT-T2595-LEGACY-RECOVERY-MULTIPLE-ONLY` | → `if len(evidence.candidates) > 1:` | テスト 1 の `valid-one`、`corrupt-one` |
| `MUT-T2595-LEGACY-RECOVERY-SINGLE-ONLY` | → `if len(evidence.candidates) == 1:` | テスト 1 の `valid-plus-corrupt` |
| `MUT-T2595-LEGACY-RECOVERY-EMPTY-REJECT` | → `if evidence.candidates is not None:` | テスト 2・3 |

最後の変異は候補が tuple であるため空でも拒否する。禁止側だけを検証して正当な resume を失うテスト設計になっていないことを確認できる。

## 総括

推奨は **legacy 返却直前の未除外 recovery 候補チェック**。P1 を採用し、既存の例外文言と候補収集 helper を使う。consume・最終 inspection・recovery の一回限定規則は変更しない。

必読 5 ファイルと関連参照を静的に確認した。ファイル変更、commit、pytest、変異実走は行っていない。