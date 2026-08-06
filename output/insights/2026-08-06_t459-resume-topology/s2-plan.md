結論は、未終端 attempt を identity 照合済みの resume seam で原子的に recovery-abort し、その後だけ新 attempt を許す案です。P1・P3・P4には同意します。P2は配置方針には同意しますが、現行 `wal.replay` は trigger orphan 時に実際には書き込むため、その副作用も明示的 resume seam へ移す必要があります。

以下は静的調査だけに基づく実装プランです。書き込み・pytest 実行・緑の確認は行っていません。

## 現行挙動の確定

|順序|書く／判定する関数|file:line|確定した挙動|
|---:|---|---|---|
|1|`pipeline.evaluate`（書き手）|[`pipeline.py:585-709`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/pipeline.py:585)|新しい `build_attempt_id = secrets.token_hex(16)` を生成し、receipt 有りの通常経路では `emit(..., STAGE_BUILD_START, ...)` を無条件実行する。campaign 経路の `emit` は `wal.log`（同 556-559）。|
|2|`wal.log` → `wal.append`（書き手）|[`wal.py:324-419`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:324)、[`wal.py:542-549`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:542)|record の基本形だけを検査して `O_APPEND`、`flock`、file/dir `fsync` する。append 時には attempt topology を検査しないため、二つ目の start 自体は書けてしまう。|
|3|crash 境界|[`pipeline.py:709-728`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/pipeline.py:709)|start 後、`_abort`、`build_done`、`commit` の前に process が死ぬと、receiptful/receiptless を問わず active attempt が残る。通常 `Exception` は loop の 272-290 で abort 化されるが、process death・`BaseException`・kill は通らない。|
|4|`ident.ensure_resumable_wal`（現行 resume seam）|[`ident.py:185-196`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/ident.py:185)|逐語では `ensure_campaign_identity(...)` の後に `return wal.repair_truncated_tail(layout)` だけ。未終端 attempt は閉じない。|
|5|`wal._validate_attempt_topology`（初回 replay の判定）|[`wal.py:898-940`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:898)|一つ目の start を `active[variant]` に登録するが、EOF 時に active が残ること自体は拒否しない。995 行でそのまま返す。|
|6|`wal.replay` / `EvalState`（再評価を選ぶ）|[`wal.py:998-1045`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:998)、[`model.py:144-164`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/model.py:144)|未終端だけなら `terminal=False`、`resumable=True`。既往 abort がある場合も `last_terminal` が retryable reason なら再評価される。|
|7|`loop.run_campaign`（再評価への導線）|[`loop.py:170-192`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/loop.py:170)、[`loop.py:240-271`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/loop.py:240)|skip 集合は terminal だけ。未終端 variant は `done` に入らず、再び `evaluate` へ進む。|
|8|`pipeline.evaluate`（二つ目の書き手）|[`pipeline.py:585`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/pipeline.py:585)、[`pipeline.py:709`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/pipeline.py:709)|別 ID の二つ目の `build_start` を追記する。後続の build/commit まで書けても、最初の active attempt と二つ目の start の順序は修復できない。|
|9|`wal._validate_attempt_topology`（拒否点）|[`wal.py:902-910`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:902)|次の replay で逐語 `build_start: variant に未終端 attempt がある` を送出する。後ろにある commit/abort はここへ到達する前なので救済にならない。|
|10|`artifact_admission._inspect_campaign`（campaign 全体の拒否点）|[`artifact_admission.py:637-663`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/artifact_admission.py:637)|全 records を `_validate_attempt_topology` に渡し、例外を一つの `ArtifactAdmissionError` に翻訳する。variant 単位ではなく `require_admitted_campaign` 全体が失敗する。|

補助的な start 書き手も同じ危険を持ちます。

- receiptless pre-build start: [`pipeline.py:597-613`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/pipeline.py:597)
- loop の identity-error start: [`loop.py:219-232`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/loop.py:219)
- quarantine reject start: [`p3_s4_loop.py:249-270`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop.py:249)

## 親裁定への評価

- P1 recovery-abort: 同意。

  `BuildAttemptState` が保持するのは ID、receipt SHA、stage の bool だけで、build directory・binary・receipt body は復元しません（[`model.py:112-123`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/model.py:112)）。一方、`evaluate` は毎回 ID を新規生成し、source evidence と admission を再導出します。既存 ID の継続は別の状態機械と partial-build 再現契約を必要とします。abort は `build_done` を要求せず active attempt を正当に閉じられるため（[`wal.py:975-994`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:975)）、最小かつ正しい seam です。

- P2 `ident.ensure_resumable_wal`: 配置には同意、現状認識には一部反対。

  identity 確定後だけ物理修復する契約は [`ident.py:185-196`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/ident.py:185) に既にあります。ただし現行 `wal.replay` は [`wal.py:1014-1025`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1014) で trigger-binding orphan の abort を書きます。したがって「read-only のまま」は現状の逐語的事実ではありません。

  代案は、既存 orphan 修復も新しい未終端-attempt 修復も `wal.recover_interrupted_attempts`（新設）へ集約し、`ident.ensure_resumable_wal` だけから呼ぶことです。`wal.replay` から 1014-1025 の書き込みを除き、純粋な read/validate/state projection にします。orphan の受理規則は変えず、書く場所だけ移します。

- P3 retryable reason: 同意。

  recovery abort 後は `EvalState.aborted=True` になるため、reason を [`RETRYABLE_ABORT_REASONS`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/model.py:104) に入れないと、loop 172-192 と screening 161-166 が永久 skip します。再評価後も correctness/build-admission gate は通常どおり全実行されるため、retryable 化は certified の受理条件を緩めません。

- P4 sweep 系 entry point: 同意。同一 wave に含めます。

  各 entry point は `run_campaign` より前に quarantine/auditor reject を WAL へ書き得ます。したがって後段の `run_campaign` 内 repair では遅すぎます。段 4 の独立実装単位にはできますが、受入条件は同じ wave で全入口を塞ぐことです。

## 実装プラン

### 1. reason の正本

対象: [`model.py:104-109`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/model.py:104)

変更前の逐語:

```python
RETRYABLE_ABORT_REASONS = frozenset({
    "identity-error", "bench-probe-error", "verify-probe-error"})
```

変更後の意図:

- `INCOMPLETE_ATTEMPT_RECOVERY_REASON = "recovery-abort-incomplete-attempt"` を定義する。
- 同値を `RETRYABLE_ABORT_REASONS` に追加する。
- loop、screening、trigger provenance が文字列を再定義せず同じ定数を使う。

この seam を選ぶ理由は、retryable 判定の正本が既に `model.py` に一本化され、`EvalState.retryable_abort`、loop、screening が共有しているためです。

### 2. WAL の原子的な scan→validate→append

対象: [`wal.append:324-419`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:324)、新設関数は [`wal.py:886-995`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:886) の直後。

変更前の逐語は、`append` 内の `fcntl.flock(fd, fcntl.LOCK_EX)` と、その後の `os.write`／`os.fsync` です。

変更後の意図:

1. `append` の「既に flock 済み fd へ一つの完全 frame を書いて fsync する部分」を private helper に抽出する。外部 `append` の例外型、short-write、file/dir fsync 契約は不変。
2. `recover_interrupted_attempts(layout, *, admission_policy)` を新設する。
3. WAL fd の exclusive flock を一度取得した状態で、現 snapshot を strict parse する。
4. tail trigger-binding orphan があれば、現行と同じ `recovery-abort-trigger-binding-orphan` tombstone を prospective records の先頭修復として組む。
5. attempt-schema marker を持つ start が一つでもあれば、`validate_trigger_bindings` と `_validate_attempt_topology` をそのまま呼ぶ。既存 topology 違反なら一 byte も追記せず失敗する。
6. `committed=False and aborted=False` の attempt を start 順に列挙し、各 attempt の recovery abort を組む。
7. tombstone と全 recovery abort を加えた prospective records 全体を、同じ二つの validator でもう一度検査する。
8. 検査済み frame だけを同じ flock 下で append/fsync する。複数 variant の途中で crash した場合も、次 resume が残りだけを閉じる。
9. attempt-schema key を全く持たない guided/no-build WAL は no-op とする。receipt や receipt SHA を持つのに ID がない混在形は strict topology へ送り拒否する。

この seam が必要なのは、単純な `replay → wal.log` では二つの concurrent resume が同じ attempt に abort を二重追記し、二つ目が [`wal.py:983-986`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:983) で topology 違反になるためです。generic recovery abort には trigger orphan tombstone の重複許容規則（692-719）がないので、scan と append を一つの flock transaction にします。

### 3. receiptless trigger attempt の閉集合

対象: [`wal.py:58-60`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:58)

変更前の逐語:

```python
_SOURCE_NULL_ABORT_REASONS = frozenset({
    "identity-error", "admission-error", "diff-quarantine",
})
```

変更後の意図:

- `INCOMPLETE_ATTEMPT_RECOVERY_REASON` だけを追加する。
- [`wal.py:850-870`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:850) の receiptless trigger 制約、verify/build/commit 禁止、binding/start 一対一は変更しない。

これは receiptless `_prebuild_abort` や trigger quarantine が start 直後に crash した場合を閉じるために必要です。

### 4. identity 照合済み resume seam

対象: [`ident.ensure_resumable_wal:185-196`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/ident.py:185)

変更前の逐語:

```python
ensure_campaign_identity(cfg, layout, admission_policy=admission_policy)
return wal.repair_truncated_tail(layout)
```

変更後の意図:

```text
identity 照合
→ truncated tail repair
→ recover_interrupted_attempts
→ 従来どおり WalTailRepairResult を返す
```

戻り型を変えず、`loop`、screening、guided、S-1 の既存 repair 表示を壊しません。未終端修復の証跡は WAL の exact reason record 自体です。

### 5. `wal.replay` を read-only にする

対象: [`wal.replay:998-1045`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:998)

変更前の逐語:

```python
orphan = _tail_trigger_orphan(records)
if orphan is not None:
    log(...)
    records = read_records(layout)
```

変更後の意図:

- この書き込み分岐を削除する。
- tail orphan は validation 上の resumable 状態として読むだけにする。
- explicit resume の `ensure_resumable_wal` が同じ exact tombstone を書く。
- docstring に「WAL bytes を変更しない」を明記する。

これにより全 `wal.replay` caller を真正な read path にできます。

### 6. loop の再評価表示

対象: [`loop.run_campaign:173-186`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/loop.py:173)

変更前の逐語は、`terminal = terminal - retryable` と表示文字列 `"(identity/probe-error) → 再評価"`。

変更後の意図:

- 集合演算は変更しない。
- コメントと表示を `identity/probe/recovery-abort` または単に `retryable abort` に更新する。
- [`screening_driver.py:161-166`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/screening_driver.py:161) のコメントも同じ正本理由へ合わせる。

### 7. sweep／autonomous loop の早期入口

すべて、変更前の逐語 `ident.ensure_campaign_identity(...)` を `ident.ensure_resumable_wal(...)` に置換します。戻った tail repair receipt は後段 `run_campaign` がもう表示できないため、各 entry の既存 `log` へ一度だけ surface します。

|変更関数|file:line|なぜここか|
|---|---|---|
|`s6_sort_sweep.run_sweep`|[`s6_sort_sweep.py:215,277-301`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/s6_sort_sweep.py:215)|`_eval_one` が run_campaign より先に `record_diff_reject` を書ける。|
|`s8a_trigger_sweep.run_sweep`|[`s8a_trigger_sweep.py:312,379-403`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/s8a_trigger_sweep.py:312)|s6 と同型で quarantine reject が先行する。|
|`p3_s4_loop.run_one_iteration`|[`p3_s4_loop.py:663,706-733`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop.py:663)|dry/build の双方で reject start を書く。|
|`p3_s4_loop_sort.run_one_iteration`|[`p3_s4_loop_sort.py:211,236-252`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_sort.py:211)|auditor/diff reject が run_campaign より先。|
|`p3_s4_loop_trigger_gating._run_one_iteration_resolved`|[`p3_s4_loop_trigger_gating.py:519,541-572`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_trigger_gating.py:519)|receiptless trigger reject と raw binding を先に書くため、generic recovery と orphan recovery の両方が必要。|

`guided.cmd_start` の [`guided.py:159-181`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/guided.py:159) は fresh-only 入口なので置換しません。

### 8. trigger proposal provenance

現状の `_wal_attempt_provenance` は [`p3_s4_loop_trigger_gating.py:499-516`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_trigger_gating.py:499) で `records_by_stage` の最後の start 一つしか転記しません。一方 admission は全 start の集合一致を要求します（[`artifact_admission.py:449-483`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/artifact_admission.py:449)）。

変更案:

- provenance document に optional な `recovered_attempts` mapping を追加する。

```json
{
  "recovered_attempts": {
    "<attempt-id>": {
      "variant": "...",
      "build_attempt_id": "...",
      "trigger_gate_binding_commitment": "..."
    }
  }
}
```

- [`_write_provenance_header:264-293`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_trigger_gating.py:264) で mapping を保持・初期化する。
- `drive_iteration` の [`736-745`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_trigger_gating.py:736) で、通常 iteration entry より先に recovery-abort 済み start/binding を同期する。checkpoint は従来どおり provenance 成功後だけ進める。
- [`artifact_admission._validate_trigger_provenance:432-484`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/artifact_admission.py:432) は、通常 `entries` と `recovered_attempts` の union を全 WAL start と比較する。
- recovered mapping の各 IDについて、同じ attempt に exact recovery reason の abort があること、mapping key と payload ID が一致することを追加検査する。
- 変更前の逐語 `if starts != provenance_attempts:` は、union 構築後もそのまま最終防壁として残す。

これにより「回復済み start を provenance 検査から除外」せず、欠けていた証明を追加します。

### 9. 変更しない correctness seam

- [`wal._validate_attempt_topology:886-995`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:886) の拒否条件は一切緩めない。
- [`pipeline.evaluate:585-709`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/pipeline.py:585) の新 ID 生成と start emit も維持する。caller precondition を docstring に追記するだけとし、pipeline 内で active attempt を無視しない。
- [`artifact_admission.py:646`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/artifact_admission.py:646) の topology 直呼びを維持する。

## recovery-abort payload 設計

|項目|設計|`wal._validate_attempt_topology` との対応|
|---|---|---|
|stage|`abort` / `STAGE_ABORT`|975 行の唯一の正規終端分岐へ入る。|
|reason|`recovery-abort-incomplete-attempt`|retryable reason の正本へ追加。trigger receiptless の閉集合にも同じ定数を追加。|
|variant|元 `build_start.variant` と完全一致|983-986 行の `attempt.variant == record.variant` を満たす。|
|env_tag|元 `build_start.env_tag` を再利用|別 run の現在 env へ付け替えず、attempt-local provenance を保つ。|
|`build_attempt_id`|常に存在し、元 start と完全一致|欠落すると active があるため 977-981 行で拒否。別 ID／inactive ID は 983-986 行で拒否。|
|`build_admission_receipt_sha256`|start が receiptful のときだけ存在し、検証済み `BuildAttemptState.receipt_sha256` と完全一致|receiptless に載せると 987-989 行で拒否。receiptful で欠落・不一致なら 990-991 行で拒否。|
|その他|載せない。特に `build_admission` body、fitness、verify payload は載せない|既存 receipt を再導出せず、終端だけを表す。|

最小 payload は次の二形です。

```python
{"reason": "recovery-abort-incomplete-attempt",
 "build_attempt_id": old_attempt_id}
```

```python
{"reason": "recovery-abort-incomplete-attempt",
 "build_attempt_id": old_attempt_id,
 "build_admission_receipt_sha256": old_receipt_sha}
```

## 受理集合の変化

|入力／経路|変更前|変更後|防壁を弱めない根拠|
|---|---|---|---|
|receiptful start だけで crash → explicit resume → retry|二つ目の start を生成し、次 replay/admission が拒否|旧 attempt を exact SHA 付き abort 後、新 attempt を受理|validator は同じ。入力を書き換えず、正規 terminal を間に追加する。|
|receiptless non-trigger start で crash|retry start により topology 破壊|SHA 無し recovery abort 後に retry|987-989 行の「SHA を載せない」条件を維持。|
|receiptless trigger start で crash|generic recovery reason は閉集合外、または二重 start|exact recovery reason を閉集合へ一件だけ追加|binding/start 一対一、verify/build/commit 禁止、active-ID 一致は全て残る。|
|複数 variant が各一つ active|各 variant の次 start が順次 campaign を壊す|同一 flock transaction で各 active を一度ずつ終端|同一 variant に複数 active があれば修復前 validation で拒否。|
|recovery 後の trigger proposal provenance|最初の start が report に無く admission 拒否|`recovered_attempts` に exact attempt/commitment を記録して受理|WAL start 全集合との equality は維持し、recovery abort の存在も追加検査。|
|既に二つ目の start が書かれた WAL|拒否|拒否のまま|過去の順序違反を後ろの abort で後付け許容しない。|
|wrong/missing receipt SHA、別 attempt ID、inactive attempt abort|拒否|拒否のまま|975-994 行を変更しない。|
|terminal campaign、空 WAL、attempt-schema 無し guided WAL|受理／no-op|同じ。bytes 不変|active attempt がなければ recovery writer は一 frameも書かない。|
|tail trigger-binding orphan の read-only replay|replay が tombstone を書く|同じ resumable state を返すが bytes は不変。explicit resume が tombstone を書く|受理規則は同じで、副作用だけ writer seam へ移す。|

したがって topology validator 自体の受理集合は、receiptless trigger の exact recovery reason 一件を除いて増えません。主要な改善は「壊れた WAL を受理する」ことではなく、「壊れた WAL を今後生成しない」ことです。

## WAL bytes 不変と read caller 一覧

既存 bytes は prefix として完全保存し、recovery は `O_APPEND` の新 frame だけにします。`ftruncate` を許すのは既存の torn-tail repair（receipt 先行）のみです。親実測では現行 `output/` に active attempt がないため、明示的 resume をしない既存 artifact には一 byte も触れません（[`s1-brief.md:26-31`](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s1-brief.md:26)）。

production の `wal.replay` direct caller は静的に次の全件です。

|caller|file:line|位置付け|
|---|---|---|
|`loop.run_campaign`|[`loop.py:171,279`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/loop.py:171)|初回状態復元／evaluate 例外時の active ID 取得。|
|`screening_driver.evaluate_candidate`|[`screening_driver.py:161,185`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/screening_driver.py:161)|skip 判定／例外 abort の ID 取得。|
|`s6_sort_sweep._eval_one`, `_replay_outcome`|[`s6_sort_sweep.py:368,383`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/s6_sort_sweep.py:368)|outcome の分類。|
|`s8a_trigger_sweep._eval_one`, `_replay_outcome`|[`s8a_trigger_sweep.py:472,484`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/s8a_trigger_sweep.py:472)|outcome の分類。|
|`backoff_sweep.main.unexpected_abort`|[`backoff_sweep.py:206-213`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/backoff_sweep.py:206)|完了後の終了判定。|

test-only caller は `test_campaign.py` の 675、791、806、823、832、966、976、980、990、1030、1045、1065、1076、1086、1101、2398、2634、2725、2758、2766、2776、2788、2799、2804、2817、2834、2849、2864、2949、3107、3152、3866、3954 行、および `test_bench_first_real_wal.py:138`、`test_dev_wave_land.py:2775`、`test_s1_direct_comparison.py:1093` です。

現行では全 caller が trigger orphan 条件下で `replay` 内部の書き込みを誘発し得ます。計画後はこの書き手を `ident.ensure_resumable_wal` に移すため、上記 direct caller はすべて read-only になります。

`artifact_admission` は次のとおり既に read-only です。

- lock/WAL の SHA 取得: [`artifact_admission.py:535-542`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/artifact_admission.py:535)
- WAL parse: 577、600 行の `wal.read_records_checked`
- topology/trigger validation: 646-659 行
- 最終 SHA 再読による TOCTOU 拒否: 696-698 行
- public wrapper: [`artifact_admission.py:715-738`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/artifact_admission.py:715)

`wal.log`、`wal.append`、tail repair を呼ぶ分岐はありません。

## テスト計画

中心となる赤→緑境界テスト案:

`orchestrator/tests/test_campaign.py::test_loop_resume_recovery_aborts_real_pipeline_crash_after_start`

構成:

1. 既存 `_mock_pipeline`（[`test_campaign.py:1897-2089`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:1897)）で外部 build/trace だけを偽装し、`loop.run_campaign` と実 `pipeline.evaluate`、実 `wal.log/append` を使う。
2. 最初の build call だけ custom `BaseException` を送出し、fsync 済み `build_start` の直後で process crash 相当を作る。pipeline と loop の `except Exception` を意図的に通らない。
3. 同じ campaign を再実行し、二回目は実 `pipeline.evaluate` の制御流を最後まで通す。
4. 最終 `wal.replay` と `artifact_admission.require_admitted_campaign` の双方を呼ぶ。
5. record 順が `start(A), abort(A,recovery), start(B), ..., commit(B)`、A/B が別 ID、A の abort SHA が start A と同一であることを検査する。
6. recovery 前 bytes が recovery 後 bytes の exact prefix であることも検査する。

現行で赤になる理由は、二回目の実 `pipeline.evaluate` が [`pipeline.py:709`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/pipeline.py:709) で B を書き、最後の replay が [`wal.py:906-910`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:906) で例外になるためです。修正後は A の abort がその間に入るため緑になる想定ですが、未実測です。

追加 nodeid 案:

- `test_campaign.py::test_ensure_resumable_wal_recovery_payload_receipt_matrix`
- `test_campaign.py::test_concurrent_resume_appends_one_recovery_abort`
- `test_campaign.py::test_replay_is_read_only_for_tail_trigger_binding_orphan`
- `test_campaign.py::test_invalid_existing_topology_is_not_mutated_by_recovery`
- `test_artifact_admission.py::test_recovered_attempt_then_retry_is_admitted_without_wal_mutation`
- `test_artifact_admission.py::test_trigger_recovered_attempt_requires_exact_recovery_provenance`
- `test_p3_s4_loop_trigger_gating.py::test_drive_resume_records_recovered_and_retry_attempts`
- `test_s6_sort_sweep.py::test_public_sweep_recovers_inflight_before_quarantine_write`
- `test_s8a_trigger_sweep.py::test_public_sweep_recovers_inflight_before_quarantine_write`
- backoff/sort/trigger の各 `run_one_iteration` に同型の early-writer 回帰テスト。

穴を隠している既存テストは [`test_loop_identity_error_retryable_survives_inflight_crash:3991-4034`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:3991) です。4011-4014 行で active start を seed しますが、4018-4021 行の fake evaluate は `EvalResult` を返すだけで二つ目の start を書かず、終了後 replay も行いません。共通 helper `_loop_with_fake_eval` も 3735-3737 行で `L.evaluate` 自体を差し替えます。このため topology 破壊点が存在しません。

s6/s8 の既存 resume テストも、[`test_s6_sort_sweep.py:302-318`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_s6_sort_sweep.py:302) と [`test_s8a_trigger_sweep.py:349-369`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_s8a_trigger_sweep.py:349) のように start+abort が完成した reject だけを扱い、crash-after-start を作っていません。

## 波及

所有外 caller:

- 既に `ensure_resumable_wal` を使う `screening_driver`、[`s1_direct_comparison._ensure_campaign:247-253`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/s1_direct_comparison.py:247)、[`guided.cmd_evaluate:191-200`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/guided.py:191) は自動的に新 side effect を受けます。
- guided は attempt-schema 無しなので no-op を固定する回帰テストが必要です。
- qualification の `pipeline.evaluate` は [`QualificationEventSink.emit`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/qualification/artifacts.py:682) へ書く別 schema・no-resume 系であり、campaign WAL recovery の対象外です。

共有 fixture:

- `test_campaign.py` の `_BUILD_CONTEXT`、`_source_evidence`、`_write_receiptful_attempt`（66-144）、`_attempt_start/_attempt_stage`（681-700）、`_mock_pipeline`（1897-2089）を再利用する。
- `test_artifact_admission.py` の `_new_schema_campaign`（152-217）、`_classify_as_trigger`（220-281）は recovery-abort と provenance mapping を生成できるよう補助引数を追加する。
- trigger provenance の既存「全 retry attempt 必須」テスト [`test_artifact_admission.py:667-724`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_artifact_admission.py:667) は残し、recovery attempt を除外しない番人として使う。

consumer test 影響:

- critic: `orchestrator/critic/digest.py:459,706`
- p3 consumers: `p3_s4_loop.py:285,964`、`p3_s4_loop_sort.py:484`、`p3_s4_red.py:170`
- sweep reports: `s6_sort_sweep.py:421`、`s8a_trigger_sweep.py:525`
- layer3/replay/completeness: `layer3_report.py:406`、`campaign/replay.py:107`、`autonomous_trial_completeness.py:1165`

API 型は変えないため consumer 実装変更は不要ですが、回復済み campaign が admission を通る positive control と、SHA/ID/provenance 改竄が引き続き拒否される mutation test を各共有境界で確認します。

最大の残存リスクは、WAL flock が「二つの recovery writer」は直列化できても、古い evaluator が本当に死んだかまでは証明しない点です。生きている evaluator を別 process が recovery-abort した後、旧 process が `build_done` を書けば topology は正しく拒否します。campaign-wide owner lease の導入は別設計になるため、この wave では「resume は旧 evaluator 終了確認後」という運用前提を明記し、二重 resume の原子性だけを機械固定します。

## 総括

- P1 recovery-abort、P3 retryable reason、P4 全 writer entry の早期 repair に同意する。
- P2 の seam には同意するが、現行 `wal.replay` は書くため、既存 orphan 修復も `ident.ensure_resumable_wal` 側へ移す。
- topology validator は変更せず、validated active attempt に exact terminal abort を追記してから新 attempt を始める。
- receipt SHA は元 start に存在するときだけ同値を伝播し、receiptless には載せない。
- trigger proposal は recovered attempt の provenance を追加し、全 start 集合一致を維持する。
- 最大リスクは、WAL flock だけでは旧 evaluator の生死を証明できない点である。