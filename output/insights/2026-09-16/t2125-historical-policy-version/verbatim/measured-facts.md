# [T-2125] 段 1 で親が実測した事実

すべて 2026-09-16、base commit `d97c423bd` (local main) で測った。
**この節の数値・行番号は親の実測であり、検査対象でもある。食い違ったら報告せよ。**

## M1. 照合は purpose 分岐より手前にある

`orchestrator/campaign/artifact_admission.py` の `_inspect_campaign` 内、1364〜1366 行:

```
    policy = _current_policy()
    if search["build_admission"] != policy.as_preimage():
        raise ArtifactAdmissionError("post-policy campaign lock admission policy differs")
```

`_inspect_campaign` は `purpose` を受け取るが、この比較は purpose で分岐していない。
purpose 別の扱いは `_require_admitted_campaign` の 1491 行以降 (`if purpose is
CampaignReadPurpose.CERTIFIED_ACCEPTANCE:`) で、admission を通った**後**に来る。
したがって `HISTORICAL_RAW` でも同じ例外で落ちる。

直後の 1372 行 `wal._validate_attempt_topology(records, admission_policy=policy, ...)` も
同じ現行 policy を渡している。

## M2. policy 識別子の構成

`orchestrator/campaign/build_admission.py` の `_new_policy()` (456〜466 行) が作る preimage:

```
    {
        "schema": POLICY_SCHEMA,            # "build-admission-policy/v1"
        "repo_stock_pin": CURRENT_PIN,      # orchestrator/campaign/pin.py
        "coder_authority": _AUTHORITY_KIND, # "cli-opt-in"
        "generator_registry": sorted(member.value for member in GeneratorId),
        "review_registry": sorted(member.value for member in ReviewId),
    }
```

`_current_policy()` は `build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP).policy` を返す
(669〜672 行)。`resolve_current_build_admission_policy()` も同じ `_new_policy()` を返す。

**つまり版が上がる事象は 2 つある。** (a) `CURRENT_PIN` の前進、(b) `GeneratorId` または
`ReviewId` への member 追加。

現在の登録簿は `GeneratorId` が 7 member (backoff-overthrottle / backoff-profile / backoff-repro /
backoff-sweep / s1-extime-calibration / s6-sort-sweep / s8a-trigger-sweep)、
`ReviewId` が 3 member (s1-known-axes / s8b-floor / s8b-oracle)。

## M3. 版の前進は実在事象である

- policy 照合の導入: `a21bf413e` (2026-08-03、[T-342/T-343/T-344])。
- `CURRENT_PIN` の前進: `fb5e74a17` (2026-08-12、[T-816] 手順 4)。
  `-CURRENT_PIN = "d706650"` → `+CURRENT_PIN = "511c953"`。
- `pin.py` の docstring が記録する前進の系列は dff0f1e → 028f34d → d706650 → 511c953。
- **照合の導入後に 1 回前進している。**

## M4. 今日の corpus では発火していない (潜在欠陥)

- 外部 official root の v2 lock 20 件 (`/work/1/SFC/tanab/b10-backoff-grid-t2266-formal`、
  `/work/1/SFC/tanab/b10-backoff-grid-t2418-explore`、`/work/1/SFC/tanab/izanagi-measurements`)
  はすべて `repo_stock_pin` に `511c953` = 現行 pin を記録している。
- submodule gitlink は `511c9538e4e8efa54b45cda62e72389ed3b706ec` で `CURRENT_PIN` と一致。
  前進待ちの状態にはない。
- 旧 pin (`d706650`) を記録した tracked 成果物は 2 件だけある:
  `output/insights/2026-08-04_wave-a-campaign-transport-smoke/evidence/campaign-layout/campaigns/p3-t178-ycsb-a-workload-conditioned-autonomous-0a11751c/` と同 `-9785aec6/` の lock。
  **ただしこの 2 件は WAL を持たないため、M1 の比較よりずっと手前の
  `"campaign requires a directory, campaign.lock, and WAL"` で落ちる。**
  `orchestrator/tests/test_artifact_admission.py` の
  `test_existing_evidence_campaign_classification_exact_rejection` がこの拒否文言を固定している。
  よってこの 2 件を「M1 が発火する実例」として使ってはならない。
- `output/campaigns/` 配下の tracked campaign はすべて v1 (build_admission 欄なし) で、
  `historical-pre-admission-schema` として別分岐で扱われる。

**結論: 本件は [T-2483] と同型の「影響は潜在」である。次の版上げの時点で発火する。**

## M5. 編集面の重複 (依頼が段 1 で実測せよと指示した項目)

- **[T-2117]**: 対象は `tools/codex_reasoning_ab.py:196-208` の pin 可用性判定。**重複なし**。
- **[T-2483]**: 対象は exact-62 の歴史 grammar = `orchestrator/campaign/campaign_lock.py`。
  本件は `artifact_admission.py` の policy 照合であり、**module も関数も別**。
  ただし両方とも「歴史閲覧を通す」主題なので、概念の衝突は段 4 で再確認する。
- 両 branch (`worktree-dev-wave-t2117-legacy-bytes-removal`、
  `worktree-dev-wave-t2483-exact62-historical-grammar`) は `git rev-list --left-right --count`
  が `0 0` = main と同一で、commit はまだ 1 つも無い。作業ツリーは稼働中で読み取れなかった
  (`git status` が timeout / degraded)。**したがって未 commit の編集面は測れていない。**

## M6. 既存被覆の検索結果 (純増の確認)

decisions.md を post-policy / admission policy / repo_stock_pin / policy_sha256 / 歴史閲覧 /
HISTORICAL_RAW / downgrade で走査した。

- **活動ごと止める裁定は見つからなかった。**
- policy 層にはまだ歴史閲覧の分岐が無い。decoder 層 (D1653/D1770) と認証 attempt 層 (D1841) には
  既に「記録どおりに読む」機構がある。

## M7. 同型の先例が既に repo 内にある — ただし向きが逆の警告つき

`orchestrator/campaign/s8b_binary_admission.py:324-338` の
`validate_portable_binary_record(record, *, expected_policy: BuildAdmissionPolicy | None, ...)` は
docstring でこう定めている (逐語):

```
    ``expected_policy=None`` は historical reverify 専用で、artifact 内 policy を期待値へ
    流用しない。live consumer は公開 resolver 由来の policy を必ず渡す。
```

**つまり同じ問題に対して、既存の兄弟実装は「歴史再検証では policy 照合を外す」を選び、
かつ「artifact 内 policy を期待値へ流用しない」と明記している。**
`orchestrator/campaign/b4_binary_record.py:149` が実際に `expected_policy=None` で呼んでいる。

これは親の (P1) 裁定 (記録 policy を照合先にする) と**向きが逆の先例**である。段 4 で裁定する。
**両レンズはこの先例を踏まえて (P1) を攻撃せよ。**

## M8. 記録 policy を照合先にすると何が残るか

`wal.py:2155-2160` は build_start の receipt を
`validate_build_admission_receipt(receipt, expected_policy=admission_policy)` へ通し、
`build_admission.py:687` が `body["policy_sha256"] != expected_policy.sha256` を見る。

したがって照合先を記録 policy に替えると、この検査は
**「WAL の receipt 群が、その lock が記録した policy と同じ policy に束縛されている」**
という lock↔WAL の内的整合検査になる。恒真にはならない (receipt が別 policy 由来なら赤)。
ただし lock と WAL の両方を書ける偽造者には満たせる。**この差が「歴史閲覧」の意味そのものであり、
別識別子と `current_verifier_conformance = unknown` が要る理由である。**

## M9. `wal._replay` の 2 つ目の照合は production の歴史経路から到達しない (親の独立実測)

`wal.py:2767-2779` の `"campaign.lock の build admission_policy が現行 policy と不一致"` は
`admission_policy is None` のときだけ発火する。`_replay` を呼ぶ公開 API は `replay` と
`replay_a1_non_certifying` の 2 本 (`wal.py:2821-2839`)。production の呼び手は
`loop.py:579,800`・`s6_sort_sweep.py:432`・`backoff_sweep.py:541`・
`b10_backoff_shape_sweep.py:3562`・`s8a_trigger_sweep.py:534`・
`screening_driver.py:592,649` で、**すべて `admission_policy=<build_context.policy>` を渡している**。
`orchestrator/campaign/replay.py` (歴史閲覧の consumer) は `wal.replay` を呼んでいない
(同 file の `wal` 参照は 143 行の path 存在検査 1 箇所だけ)。
**よって None 分岐は test からしか到達しないと親は読んだ。段 3 レンズ B に裏取りさせる。**
