# 段 2 plan (R5 closure) — Claude 子 (opus / read-only) の逐語

親注記: 本 wave は「codex はレートリミットが近いので claude で代替」というユーザー裁定により、
codex subprocess の代わりに Claude subagent を子として使う。以下は子の最終出力の逐語である。
pytest は実走していない (`DW-O05`)。行番号は worktree `codex/dev-wave-improve` (base `72e3800`) 時点。

---

### 1. 現行挙動の確定

#### C1 (resume): `tools/pegasus/test_dispatch.py:6564-6613`

親 brief の `:6555-6566` は現ファイルでは `:6564-6592` に相当する (内容一致、行ずれのみ)。

**現在受理される入力** (`submit-receipt.json` が存在する resume 分岐):

- `:6566-6574` — receipt は `_validate_submit_object` で snapshot/auth/request/result の各 sha に束縛されるが、
  `:2593-2623` の検査項目に **group は無い**。`job_id_normalized` は
  `normalize_job_id(qsub_request_id_raw)` と一致する任意の NQSV ID でよい (`:2620-2621`)。
  `_NQSV_ID_RE` (`:274`) は `0:` 接頭辞を捨てるので、`0:123.nqsv` と `123.nqsv` は同一に正規化される。
- `:6577-6585` — matched WAL の選択キーは 4 項のみ: `event == "scheduler-lookup-result"` /
  `disposition == "matched"` / `candidates` が長さ 1 の list / `candidates[0]["job_id_normalized"] == normalized`。
  - `qsub_request_sha256` / `qsub_result_sha256` で **絞っていない**。対照の `lookup_scheduler_job:4695-4696`
    は両 sha で絞る。よって別 qsub 試行の WAL 行でも選ばれる。
  - `request_name` / `user_name` / `group_name` / `queue` / `account` / `created_epoch_s` / `state` /
    `request_id_raw` を **一切照合しない**。
  - `matched_results[-1]` を採るだけで、一意性 (`len == 1`) も末尾性も要求しない。対照の
    `_validate_scheduler_lookup_chain:3932-3939` は「matched は唯一かつ最後」を要求する。
- `:6586-6592` — 採るのは `execution_hosts` のみ。`type(hosts) is not list` だけ検査し、要素は
  `str(host)` で強制変換する (対照の `:4749` は `isinstance(host, str)` を要求)。
- `:6601-6603` — `matched_results` の有無だけで `identification_source` を `"scheduler-lookup"` /
  `"qsub-result-resume"` と記録する。証跡の出所主張が未検証の WAL 行に依存する。
- 出力先 3 経路 — `:6702-6755` (cancel-intent → `cancel_job` = qdel)、`:6756-6798`
  (unknown completion → `cancel_job` = qdel)、`:6799-6816` (`monitor_job(expected_execution_hosts=lookup_hosts)`)。

**現在拒否される入力**: `hosts` が list でない場合のみ (`:6591`)。group が `policy.account` と異なる
candidate は素通しする。

**非対称の対照** (親 brief の `:4741`、現 `:4726-4758`): `lookup_scheduler_job` の WAL 復元経路は
`request_name == exact_job_name` / `user_name == expected_user` / `group_name == policy.account` (`:4741`) /
`queue.split("@")[0] == policy.queue` / `account == policy.account` / `created_epoch_s >= qsub_started` /
`state ∈ _QSTAT_STATES.values()` / `hosts` 全要素 str を全項照合し、1 つでも外れれば
`DispatchError("scheduler lookup WAL candidate is malformed")` (`:4751`)。
同じ WAL 行を、同じ file の 2 箇所が異なる強度で読む。

**group 証拠がゼロになる resume**: `submit-receipt.json` schema (`:2358 izanagi-test-submit-v2`) に
group 項が無く、matched WAL も無い場合。到達経路は 2 つ。

1. receipt が既にある + matched WAL 無し (既存 test `orchestrator/tests/test_pegasus_test_dispatch.py:2225`)。
2. `:6619-6646` — receipt が無く `qsub.stdout` を再 parse して receipt を新規作成する経路 (既存 test `:2267`)。

この 2 経路では、`normalized` に対する group 検証は **resume 内で一度も行われない**。
`monitor_job:5056-5061` は `expected_group=policy.account` 付きで per-job qstat を検査するが、
group 不一致時の反応は `:5070-5079` の `cancel_for` = **qdel** である
(既存 test `:1070-1090` がこの反応を固定している)。すなわち現状では「他 group の job だと判明した
瞬間に、その job へ qdel を打つ」。`:6702` / `:6756` の 2 分岐に至っては qstat を一切経ずに qdel する。

#### C2 (accounting): 同 file `:3195-3250`

- **受理される入力**: `:3217` の `re.compile(r"Group Name:[ \t]+\S+\Z")` にマッチする任意の非空 token。
  `OTHER`、`root`、`wheel` すべて受理。捕獲群すら無いため値は読まれない。
- **拒否される入力**: `\r` 混入 / 改行終端でない (`:3201-3204`)、行数 < 14 or 末尾が区切りでない
  (`:3206-3209`)、12 パターンの順序・schema 不一致 (`:3225-3237`)、`Request ID` の正規化不一致
  (`:3238-3244`) のみ。
- **呼出 2 箇所**:
  - `:5255` — `monitor_job` の accounting 安定化ループ内。例外は `:5259` で捕捉され
    `accounting_error` に落ち、`accounting is None` のまま `:5414-5416` で `ACCOUNTING_INCOMPLETE` /
    rc 125 になる (fail-closed の形は既存)。`policy` は同スコープに在る。
  - `:4404` — `validate_final_receipt_object` の `if verify_files:` ブロック (`:4290`) 内、
    `if final.get("accounting") is not None:` (`:4392`) の下。**同ブロックの `:4305` に既に
    `bound_policy` がある** (`_validate_qsub_request_object` の戻り値。`:2402-2409` で snapshot 内
    policy を load し `policy_sha256 != snapshot.policy_sha256` なら reject 済み)。
    `:4341` で `_validate_scheduler_lookup_chain` に渡されている。
- 結果として、wrong-group の accounting footer を含む dispatch は `CHILD_RESULT` として封印され、
  `final["accounting"]["lines"]` に他 group 名がそのまま格納される (`:5468`, `:3248`)。

---

### 2. 変更プラン (file:line 粒度)

以下すべて `tools/pegasus/test_dispatch.py`。

#### 変更 A — 共有ヘルパ `_policy_bound_lookup_candidate` の新設 (`:4718` 直前)

`:4733-4751` の candidate 検査述語をそのまま関数に切り出す。

    def _policy_bound_lookup_candidate(
        candidate, *, snapshot, policy, expected_user, qsub_started_epoch_s
    ) -> tuple[str, str, str, tuple[str, ...]]:   # (request_id_raw, normalized, state, hosts)

中身は `:4734-4751` の逐語移送 (`exact_job_name = scheduler_job_name(snapshot)` を内部で算出)。
エラー文言 `"scheduler lookup WAL candidate is malformed"` を維持。純粋な move で受理集合は不変。

#### 変更 B — `lookup_scheduler_job:4726-4758` を変更 A のヘルパ呼出に置換

`:4733-4751` をヘルパ呼出に置換し、`:4752-4758` の `SchedulerLookup(...)` 構築を残す。
述語は逐語同一。この分岐 (WAL 再生) は既存 test 群では未到達であり、既存緑への影響は無い一方、
**この分岐は現状ノーカバレッジ**である。

#### 変更 C — resume の matched WAL 選択を policy 束縛にする (`:6577-6592`)

1. `:6577-6585` の filter に 2 項追加 (`lookup_scheduler_job:4695-4696` と同型):
   `and payload.get("qsub_request_sha256") == request_sha and payload.get("qsub_result_sha256") == result_sha`
2. `:6586` を `if matched_results:` から、`len(matched_results) != 1` で
   `DispatchError("resume lookup match is not unique")` を投げる形に強化。
3. `:6587-6592` を差し替え:

        candidate_raw, candidate_normalized, _state, hosts = _policy_bound_lookup_candidate(
            matched_results[0]["candidates"][0],
            snapshot=snapshot, policy=policy,
            expected_user=str(request["submit_user"]),
            qsub_started_epoch_s=float(started),
        )
        if candidate_raw != qsub_raw or candidate_normalized != normalized:
            raise DispatchError("resume lookup candidate is not the submitted identity")
        lookup_hosts = hosts
        group_verified = True

4. 関数冒頭 (`:6560-6563`) に `group_verified = False` を追加。`:6663-6665` の
   `_recover_submission_identity` 成功後に `group_verified = True` を置く。

**変更後に拒否される入力**: matched WAL candidate の `group_name != policy.account` (単独で成立)、
`account != policy.account`、`request_name != izt-<dispatch_id>`、`user_name != submit_user`、
`queue` 前置が `policy.queue` でない、`created_epoch_s < qsub_started`、未知 state、非 str host、
別 qsub 試行の WAL 行、matched が複数、candidate の raw/normalized が receipt と食い違う組。

**same-group 経路が壊れない根拠**: 正規経路で matched WAL を書くのは `lookup_scheduler_job:4852-4887`
のみで、その `candidate_receipts` は `parse_qstat_candidates:3118-3142` が
`expected_group=policy.account` (`:4836`) 込みで identity 一致と判定した candidate だけを載せる。
`qsub_request_sha256`/`qsub_result_sha256` も `:4873-4874` で同一値が書かれる。

#### 変更 D — group 証拠ゼロの resume に per-job qstat gate を挿入 (`:6694` と `:6695` の間)

    if not group_verified:
        command_sequence = fs.next_sequence(dispatch_dir) + 1
        result = scheduler.run(("qstat", "-f", normalized),
                               timeout=policy.command_timeout_s,
                               environment=scheduler_environment())
        raw_receipt = fs.record_command(dispatch_dir, "resume-group-check",
                                        command_sequence, result)
        status = parse_qstat(result,
                             expected_job_id_normalized=normalized,
                             expected_group=policy.account,
                             was_visible=False)          # ← 不一致はここで DispatchError
        append_journal(journal, {
            "event": "resume-group-check", "job_id_normalized": normalized,
            "expected_group": policy.account, "visible": status.visible,
            "parsed_state": status.state, "raw": raw_receipt,
            "monotonic_s": clock(),
        })
        group_verified = status.visible
    if not group_verified and (cancel_intents_present or unknown_completion):
        raise DispatchError("resume cannot cancel a job whose scheduler group is unverified")

`parse_qstat:3018-3025` が Group Name 不一致で送出する `DispatchError` を **捕まえない**。
よって qdel も monitor も起きずに resume が停止する = fail-closed。
可視でない/transient (`:3007`) の場合は `group_verified` を False のまま monitor へ渡す
(hard fail にすると「job が qstat から消えた後の resume が永久に final を封印できない」liveness
回帰になり、brief の不変条件を破る)。ただし qdel 2 分岐は未検証のままでは通さない。
`lookup_hosts` は gate では触らない。

**新規 WAL event の安全性**: WAL 検証子はいずれも event 名で filter しており、未知 event を拒否する
網羅集合検査は無い (`_validate_scheduler_lookup_chain:3780-3786` / `:3941-3944` / `:3991-3994`、
`cancel_job:3501-3510`、`_publish_pending_final_if_present:4492-4501` を確認済み)。順序制約も
gate event の挿入で崩れない。`journal_head_sha256` は publish 時に再計算される (`:4471-4474`)。

#### 変更 E — `validate_nqsv_accounting` に必須 `expected_group` を追加 (`:3195-3244`)

1. シグネチャを
   `def validate_nqsv_accounting(stderr_text, job_id_normalized, *, expected_group: str)` に変更
   (既定値なし、keyword-only)。
2. `:3217` を `re.compile(r"Group Name:[ \t]+(\S+)\Z", re.ASCII)` に変更 (捕獲群追加)。
3. `:3244` の直後に追加:

        observed_group = matches[5].group(1)
        if observed_group != expected_group:
            raise DispatchError(
                "terminal NQSV accounting Group Name mismatch: "
                f"expected={expected_group!r} observed={observed_group!r}"
            )

4. `expected_group` 自体の型 guard は足さない。`None` / `""` はいずれも `\S+` 由来の実 token と
   一致しないので自動的に fail-closed。

**same group は完全に現行どおり** (`_accounting()` fixture の `SFC` は `policy.account` と一致)。

#### 変更 F — 呼出 2 箇所へ `policy.account` を通す

- `:5255-5258` → `expected_group=policy.account` (`monitor_job` 引数 `:4919`、`:4940` で snapshot 束縛済み)。
- `:4404-4407` → `expected_group=bound_policy.account`。

#### 変更 G (P2 への対案) — `validate_final_receipt_object` にはシグネチャを足さない

親の P2 は「`validate_final_receipt_object` も既定値なしで `expected_group` を受け取る」だが、
**採らないことを推す**。理由 3 点:

1. **二重の真実源になる**。`:4404` の直前 `:4305` には既に `bound_policy` があり、`:2402-2409` で
   `policy_sha256 != snapshot.policy_sha256` を拒否済み。引数で別 group を渡せる設計にすると
   「引数と `bound_policy.account` が食い違ったらどちらが勝つか」を新たに決める必要が生じ、
   一致検査を足せば引数は冗長、足さなければ **呼出側が検査を弱められる新しい穴** になる。
2. **値を持たない呼出元が 4 つある**。`load_final_receipt:4424-4430` → `_completed_dispatch:1149-1161`
   (retention 用。policy を持たず snapshot だけを再構成する) / `:6117` / `:6190`。さらに
   `MonitorFilesystem` protocol の `publish_final` / `stage_final` (`:66-71`) は `(snapshot, document)`
   しか受け取らない seam で、実装は `PathMonitorFilesystem:4530-4551` と test 側 `FakeFilesystem`
   (`test_pegasus_test_dispatch.py:169-200`) の 2 つ。必須引数を波及させると **test の fake が
   group の権威になる**。`_completed_dispatch` が誤った policy を渡せば「完了 dispatch を未完了と
   誤判定し retention が働かない」静かな回帰になる。
3. **3 箇所で引数が死ぬ**。accounting 再検証は `if verify_files:` (`:4290`) の内側なので、
   `verify_files=False` の 3 呼出 (test:178 / test:190 / test:915) では一度も読まれない。

対案 (変更 F の後半) は「関数が既に持っている snapshot 束縛済み policy を使う」であり、省略も
既定値も存在しないので P2 の意図と P3 を満たす。

#### シグネチャ波及先の全列挙

`validate_nqsv_accounting` (実装 `:3195`): 呼出は `:4404` と `:5255` の 2 箇所のみ。
test からの直接呼出は無し。`__all__` (`:6819-6855`) に非掲載。
`orchestrator/campaign/silo_ladder_rung1.py:3662 validate_nqsv_accounting_epilogue` と
その test 群は **別 module の別関数**であり、名前が似ているだけ。触らない。

`validate_final_receipt_object` (実装 `:4038`) — 変更 G を採るならシグネチャ不変:

| 呼出元 | verify_files | accounting 再検証到達 |
| --- | --- | --- |
| `:4430` (`load_final_receipt`) → `:1155` `_completed_dispatch` / `:6117` / `:6190` | 既定 True | 到達しうる |
| `:4437` (`_publish_final`) ← `PathMonitorFilesystem.publish_final:4533` | True | 到達しうる |
| `:4510` (`_publish_pending_final_if_present`) | `isinstance(fs, PathMonitorFilesystem)` | 条件付き |
| `:4538` (`PathMonitorFilesystem.stage_final`) | True | 到達しうる |
| `:6406` (`resume_dispatch`) | `isinstance(fs, PathMonitorFilesystem)` | 条件付き |
| test `:178` / `:190` / `:915` | False | 不到達 |

P2 を字義どおり採る場合は 8 箇所すべてに引数追加が必要で、うち 4 箇所は policy を持たないため
各所で `load_policy(...)` を再実行することになる。

---

### 3. 追加するテスト

すべて `orchestrator/tests/test_pegasus_test_dispatch.py`。

#### fixture の最小変更

- `:400-416 _accounting(job_id=JOB_ID)` → `_accounting(job_id=JOB_ID, *, group="SFC")` とし、
  `:408` を f-string 化。既存呼出 (`:549` / `:933` / `:968`) は無変更で通る。
- `:419-433 _qstat(...)` は既に `group=` を持つので変更不要。`:436-466 _qstat_listing` も変更不要。

#### expected-red 1 — wrong-group accounting (C2)

- 置き場所: `:958` の直後。名前案 `test_monitor_rejects_accounting_group_other_than_policy_account`。
- fixture: `_synthetic_snapshot` (`:302`)、`_monitor_files(snapshot, stderr=_accounting(group="OTHER"))`
  (`:521`)、`FakeScheduler([(("qstat","-f",JOB_ID), _result(stdout=_qstat("Ended","bnode114")))])`、
  `FakeFilesystem` (`:115`)、`FakeClock` (`:44`)、`_monitor` (`:554`)。
- 期待: `_monitor(...) == 125`、`dispatch_outcome == "ACCOUNTING_INCOMPLETE"`、`accounting is None`、
  `"Group Name mismatch" in failure_reason`、`scheduler.assert_drained()`。
- **単一絞り込みの根拠**: `_accounting(group="OTHER")` は既定と 1 token しか違わない。行数 14、区切り、
  12 パターンの順序、`Request ID` はすべて通る。`lines_sha256` は自分自身から計算される (`:3249`)。
  qstat 側 group は既定 `SFC` なので `parse_qstat:3021` は通る。拒否理由になり得るのは変更 E の
  新照合ただ 1 つ。

#### expected-red 2 — wrong-group な matched WAL candidate (C1-a)

- 置き場所: `:2264` の直後。名前案 `test_resume_rejects_lookup_wal_candidate_from_another_group`。
- fixture: `_synthetic_snapshot`、`_qsub_artifacts` (`:1370`)、
  `_append_pre_submit_and_qsub_intent` (`:1418`)、`_append_qsub_return` (`:1438`)、
  `TD.append_journal` で `scheduler-lookup-result` を手組み、`FakeScheduler([])`、`FakeFilesystem`。
- 手組み candidate は group 以外全項正しくする:
  `request_id_raw=JOB_ID_RAW, job_id_normalized=JOB_ID, request_name=TD.scheduler_job_name(snapshot),
  user_name=TD.scheduler_user_name(), group_name="OTHER", queue="gen_S@nqsv", account="SFC",
  created_epoch_s=0, state="running", execution_hosts=["bnode114"]`。
- 期待: `pytest.raises(TD.DispatchError, match="WAL candidate is malformed")`、`scheduler.trace == []`。
- **単一絞り込みの根拠**: `account="SFC"` を保つことで group 項と account 項を分離。2 sha も正しく
  入れるので C-1 の新 filter では落ちず、`len == 1` なので C-2 でも落ちない。
- **現行コードでの赤の形**: `lookup_hosts` のまま monitor へ渡り `("qstat","-f",JOB_ID)` を呼ぶ →
  `FakeScheduler` の空 script が sentinel を送出 → `pytest.raises(DispatchError)` は捕まえず失敗。

#### expected-red 3 (追加提案) — group 証拠ゼロ resume の gate (C1-b)

親が事前登録したのは red 2 件だが、**P1 は 2 節から成る**。red 2 件では後半節が無制約のまま
実装されることになるため 3 件目を推す。親が 2 件に固定するなら変更 D も同時に落とすべきである。

- 名前案 `test_resume_without_group_evidence_verifies_group_before_monitor_or_qdel`。
- fixture: `:2225` と同一構成 (matched WAL 無し)、
  `FakeScheduler([(("qstat","-f",JOB_ID), _result(stdout=_qstat("Running","bnode114", group="OTHER")))])`。
- 期待: `pytest.raises(TD.DispatchError, match="Group Name mismatch")`、
  `assert all(call[0] != "qdel" for call in scheduler.trace)`、`scheduler.trace == [("qstat","-f",JOB_ID)]`。
- **現行コードでの赤の形**: gate が無いので monitor がこの qstat を消費 → `:5062` で捕捉 →
  `cancel_for` → `("qdel", JOB_ID)` が script に無く sentinel。「qdel を打った」ことが赤の理由になる。

#### positive control 1 — same-group resume (C1)

- expected-red 2 と同一構成で `group_name="SFC"`。
  `FakeScheduler([(("qstat","-f",JOB_ID), _result(stdout=_qstat("Ended","bnode114")))])`。
- 期待: 戻り値 0、`CHILD_RESULT`、`assert_drained()`、qdel ゼロ、
  `identification_source == "scheduler-lookup"`。
- **注意 2 点**: (a) `execution_hosts` は `["bnode114"]` にする (`_runner_result:507-508` の
  `hostname_canonical` と一致させないと `:5339-5352` の host mismatch で `INFRA_FAILURE`)。
  (b) `FakeFilesystem` を必ず使う (`PathMonitorFilesystem` だと `_validate_scheduler_lookup_chain:3837`
  が手組み payload の raw 受領書不在を拒否する)。

#### positive control 2 — same-group accounting (C2)

- `_monitor_files(snapshot)` 既定 + `_qstat("Ended","bnode114")` 1 手。
- 期待: 戻り値 0、`CHILD_RESULT`、`accounting["job_id_normalized"] == JOB_ID`、
  `assert policy.account == "SFC"`、
  `assert any(line == "Group Name:             SFC" for line in accounting["lines"])`。

#### 既存 test の必須更新 (script に qstat が 1 手増える)

| test | 現行 script | 更新後 |
| --- | --- | --- |
| `:2225 test_resume_after_submit_receipt_crash_seals_wal_and_monitors_without_qsub` | qstat×1 | qstat×2 |
| `:2267 test_resume_after_qsub_result_crash_seals_return_and_submit` | qstat×1 | qstat×2 |
| `:2404 test_resume_after_cancel_intent_crash_completes_one_qdel` | qdel×1 | qstat×1 → qdel×1 |

`:2308` / `:2364` は `_recover_submission_identity` 経由で `group_verified=True` になるため無変更。
`:2532` / `:2592` は gate に到達しないので無変更。

---

### 4. 波及と危険

**所有外 caller / 共有 seam**

- `MonitorFilesystem` protocol (`:52-86`): `record_command` / `next_sequence` を gate が新規に呼ぶ。
  実装は `PathMonitorFilesystem:4568-4595` と test の `FakeFilesystem:222-239` の 2 つ。追加実装は不要。
  `next_sequence` は `*.rc` を glob するので `00001-resume-group-check.rc` が採番に混ざるが、
  採番連番性を明示検査している test は無く、`_validate_scheduler_lookup_chain:3844-3863` は
  raw 受領書 path を自 payload から読むので影響を受けない。
- `tools/pegasus/submit_tests.py:288/311` と `tools/run_tests.py:1062/1154` は本変更の関数に触れない。
- `orchestrator/campaign/silo_ladder_rung1.py` の `validate_nqsv_accounting_epilogue` は同名接頭辞の
  別実装。**触らない**。誤って一括置換しないこと。

**共有 fixture への波及**: `_accounting` の keyword-only `group` 追加は 3 呼出すべてに無影響。
`_monitor` / `_monitor_files` / `FakeScheduler` / `_qsub_artifacts` は無変更。

**受理集合を意図せず広げる/狭めるリスク**

1. **狭め過ぎ (最大リスク)**: 変更 D の「非可視なら `group_verified` を False のまま monitor へ」を
   採らず hard fail にすると、job が qstat から消えた後の resume が永久に final を封印できなくなる。
   wrong-group と無関係な liveness 回帰であり、brief の不変条件違反。**必ず非可視は通す**こと。
2. **残余 (今回閉じない)**: 非可視のまま monitor へ渡った場合、monitor の visibility timeout →
   `cancel_for` → qdel は依然として group 未検証で発火する (`:5132-5144`)。ただし per-job qstat が
   その id を報告していない以上「他 group の job である」ことも示せない。monitor は前 wave で
   closed 判定済みの consumer であり、ここへ手を入れると `:1070` / `:1110` / `:1140` など既存
   赤/緑の意味が動く。**scope 外として明示的に残す**。親の裁定を仰ぐ点。
3. **変更 C の広げ過ぎリスク**: `len(matched_results) != 1` の raise 追加は、正規経路で matched が
   複数書かれ得ないことに依存する。`lookup_scheduler_job:4888-4896` は matched を得た時点で return
   するため 1 attempt 1 matched で終了し、`_validate_scheduler_lookup_chain:3936-3939` も唯一性を
   要求している。よって正規 WAL では常に 1。
4. **カバレッジの穴 2 件**:
   - `lookup_scheduler_job:4721-4758` の WAL 再生分岐は既存 test で未到達。変更 B の move の
     正しさを守る test が無い。expected-red 2 / positive 1 が resume 側から同じヘルパを叩くので、
     move 後は間接的に被覆される。
   - `validate_final_receipt_object:4404` の accounting 再検証は、**accounting 非 None かつ
     `verify_files=True`** の組でしか走らない。既存 test でこの組に到達するものは無い。
     したがって変更 F の `:4404` 側は **無被覆のまま**になる。

---

### 5. 変異候補

**M1 (C2 の中核)**: `:3244` 直後の group 照合を削除、または `!=` を `==` に反転。
前段の不在根拠: `:3201-3209` は改行/行数/区切り、`:3225-3237` は 12 パターンの順序と schema、
`:3238-3244` は Request ID のみ。`Group Name` 行は `\S+` にマッチするだけで値は読まれない。
殺す test: expected-red 1。

**M2 (C2 の束縛先)**: `:5255` の `expected_group=policy.account` を `policy.queue` に差し替える。
殺す test: positive control 2。**過剰拒否を検出する正例**として機能する。

**M3 (未被覆の警告)**: `:4404` の `expected_group=bound_policy.account` を `bound_policy.queue` に
差し替える。現状の test 群では **どれも殺さない** 見込み。この位置を守るには、accounting 付き
final を実 FS で `load_final_receipt` に通す test が要る。**この不足は緑と主張しない。**

**M4 (C1-a の中核)**: `_policy_bound_lookup_candidate` 内の `group_name != policy.account` 項を削除。
前段の不在根拠: resume 側の選択 filter は event / disposition / candidates 長 / normalized / 2 sha
しか見ず group を読まない。`_validate_submit_object:2601-2622` にも group 項が無い。
`monitor_job` の group 検査 (`:5059`) は candidate 採択より後段。殺す test: expected-red 2。

**M5 (C1-a の呼出)**: 変更 C-3 の呼出ごと削除し `lookup_hosts` を旧形に戻す。殺す test: expected-red 2。

**M6 (C1-b の中核)**: `group_verified = False` を `True` に変える、または gate を丸ごと削除。
前段の不在根拠: receipt-only resume の経路上、`normalized` に対する group 検査は resume 内に
他に存在しない。殺す test: expected-red 3。

**M7 (C1-b の束縛先)**: gate の `expected_group=policy.account` を `scheduler_user_name()` に差し替える。
殺す test: 更新後の `:2225` / `:2267` / `:2404`。**過剰拒否を検出する正例**。

**過剰拒否検出の正例まとめ**: positive control 1 / 2、更新後の `:2225` `:2267` (gate 通過して
monitor 完走)、`:2404` (gate 通過して qdel 1 回)。

---

## 総括

- C1 / C2 とも欠落は実在し file:line で確定した (`:6577-6592` の 4 項 filter と `:3195-3244` の
  `\S+` 検査)。閉じ方は既存の閉じた対照 (`:4726-4758` と `parse_qstat:3021`) の逐語再利用で足り、
  新概念は不要。
- P1 は採用推奨だが 2 節に分けて実装する必要がある。gate の非可視ケースを hard fail にすると
  liveness 回帰になるため、非可視は通し qdel 2 分岐だけ塞ぐ。
- P2 は `validate_nqsv_accounting` については採用、`validate_final_receipt_object` については
  **不採用を推す**。P3 は両案とも満たす。
- 代償は既存 3 test の script に qstat 1 手を足すこと、および red 3 件と positive 2 件の追加。
- `validate_final_receipt_object:4404` の accounting 経路は現状無被覆で、変異 M3 は殺せない。
  この穴は既知欠落として残し、緑とは主張しない。
