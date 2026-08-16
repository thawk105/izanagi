## 1. 所見対応表 (closed / partial / regressed)

| レビュー A の所見 | 判定 | 根拠 |
|---|---|---|
| 所見 1: M1〜M4 が fixture の `FileNotFoundError` で偽の赤になる | `closed` | 独立 literal 12 path は `orchestrator/tests/test_artifact_admission.py:44`、fixture 作成と `git add` は同 `:331`〜`:339`、期待 epoch は同 `:349`〜`:359` から導出される。対象 verifier file は production tuple から削除しても存在し、対象 node は同 `:1152` の certified gate 呼出しまで到達する。 |

pytest は未実走であり、緑とは数えていない。これは構造上の root cause に対する `closed` 判定である。

## 2. fix が作った新欠陥の有無

fixture 自体に新しい内容不整合はない。

- production tuple、fix の `_EXPECTED_E1_CLOSURE_PATHS`、既存の `_EXPECTED_ENFORCEMENT_SOURCE_PATHS` は、いずれも順序込みで同じ exact 12 件だった。根拠は `campaign_lock.py:29`〜`:42`、`test_artifact_admission.py:44`〜`:57`、`test_t671_source_binding.py:22`〜`:35`。
- 各 file の内容は `epoch closure fixture <index>\n` で、index は 1 始まりの tuple 順である。fixture 作成は `test_artifact_admission.py:331`〜`:336`、期待 payload は同 `:350`〜`:358` で同じ文字列を SHA-256 化している。
- 静的に再計算した期待値は `E1:6b5bb921e7dcf2eace9292f9d3a14becef7e0b2f500df9f10e432ef493c9ea6d`。
- 現行 tuple が同一なので、fix 前後で fixture の file bytes、commit 対象、期待 epoch の値は変わらない。既存の直接 consumer 7 function、parametrize 展開後 10 node に静的な破壊は見つからなかった。
- `git diff --check 518a87e1..999357c5` は成功した。

ただし、変異検査面には後述の帰属不成立が残る。これは fixture 不在という所見 1 の再発ではなく、独立 oracle 化によって可視化された多重赤と、従来からの M5/M6 の分類誤りである。

## 3. production 無変更の確認

fix commit による production 緩和はない。

- `git diff --quiet b20c5459..999357c5 -- orchestrator/campaign/ orchestrator/verifier/` は `rc=0`。
- fix commit `999357c5` の変更は `orchestrator/tests/test_artifact_admission.py` だけ。
- wave 全体でも `orchestrator/verifier/**` は `518a87e1..999357c5` で差分ゼロ。
- wave 全体の `orchestrator/campaign/**` には、実装 commit `b20c5459` による exact 12 化が存在する。したがって「全 range で campaign 差分ゼロ」とは主張せず、「fix が production を変更していない」と限定する。
- `git status --short` は出力ゼロで、作業木は clean。

## 4. 変異 M1〜M7 の帰属判定と期待 node 集合

以下の略記を使う。

- `P12` = `{env_contract.py, env_contract_activation.py, execution_guard.py, loop.py, pipeline.py, wal.py, ident.py, artifact_admission.py, core.py, dsg.py, model.py, parse.py}`
- `V4` = `{core.py, dsg.py, model.py, parse.py}`
- `v(M1)=core.py`、`v(M2)=dsg.py`、`v(M3)=model.py`、`v(M4)=parse.py`

### M1〜M4

判定は各変異とも、対象 drift 入力に対する production 層の mask はないが、runner 全体の赤理由は一つに絞れず、帰属は `partial`。

対象 verifier path を tuple から削ると、未 commit drift も commit 済み drift も `capture_contract_loader_binding()` と map 比較から消えるため、同じ入力を前後で拒否する production 層はない。対象 node は fixture file を読めて `test_artifact_admission.py:1152` に到達し、`pytest.raises` が発火しないことで赤になる。ここはレビュー A の問題を正しく解消している。

一方、静的に予想される完全な失敗集合は各変異 47 node で、次のとおり。

- `orchestrator/tests/test_t671_source_binding.py::test_enforcement_source_closure_is_the_independent_exact_twelve_paths`
- 次の3 familyについて、それぞれ `[p]`、`p ∈ P12` の全12 node、計36 node。
  - `::test_loader_drift_rejected_before_campaign_lock_or_wal_bytes[p]`
  - `::test_live_verification_rejects_each_dirty_enforcement_source[p]`
  - `::test_admission_rejects_contract_loader_blob_mismatch_at_recorded_commit[p]`
- `orchestrator/tests/test_t671_source_binding.py::test_shared_v2_fixture_default_uses_recorded_blobs_when_disk_is_dirty[v(Mx)]`
- `orchestrator/tests/test_artifact_admission.py::test_valid_v2_campaign_is_admitted`
- `orchestrator/tests/test_artifact_admission.py::test_certified_acceptance_admits_exact_e1_fixture`
- `orchestrator/tests/test_artifact_admission.py::test_certified_acceptance_rejects_e1_stale_exact_map_mismatch`
- `orchestrator/tests/test_artifact_admission.py::test_certified_acceptance_rejects_each_verifier_drift_fail_closed[p]` の `p ∈ V4`、全4 node
- `orchestrator/tests/test_artifact_admission.py::test_historical_epoch_display_is_independent_of_live_closure_bytes`
- `orchestrator/tests/test_artifact_admission.py::test_lock_only_epoch_api_does_not_read_wal`

赤理由は少なくとも、exact tuple 不一致、map key 集合不一致、欠落 key 参照、固定12件数不一致、独立12-path epoch と production 11-path epoch の不一致、対象 drift の過少拒否、の複数に分かれる。さらに drift test は最初の未 commit 検査で停止するため、M1〜M4 の本走だけでは対象 path の commit 済み drift 段階まで到達しない。

`test_campaign_lock_codec.py:166`〜`:179` の missing-key parametrize は production tuple 由来なので、削除対象 `[v(Mx)]` node 自体が collection から消える。これは失敗 node には含まれないが、完全 node 集合の解釈上は記録が必要である。

### M5

帰属は「診断感度として成立、negative KILL として不成立」。

期待失敗 node は次の1件だけ。

- `orchestrator/tests/test_artifact_admission.py::test_real_e0_is_rejected_only_by_certified_epoch_gate`

`test_artifact_admission.py:953`〜`:956` の exact `identity_scope` assert が赤になる。受理集合や fail-closed 挙動は変わらず、同じ入力を拒否する層の有無という問題も発生しない。`DW-M03` に従えば `KILLED` ではなく diagnostic sensitivity pin である。

### M6

M5と同様に、診断感度としては成立するが negative KILL としては不成立。

期待失敗 nodeは次の1件だけ。

- `orchestrator/tests/test_artifact_admission.py::test_real_e0_is_rejected_only_by_certified_epoch_gate`

赤になるのは `test_artifact_admission.py:957`〜`:960` の exact `excluded_scope` assert。受理集合は不変なので、これも diagnostic sensitivity pin として扱う必要がある。

### M7

帰属は成立する。期待失敗 node は次の2件。

- `orchestrator/tests/test_artifact_admission.py::test_certified_acceptance_admits_exact_e1_fixture`
- `orchestrator/tests/test_artifact_admission.py::test_lock_only_epoch_api_does_not_read_wal`

いずれも clean E1 正例で、記録 map と現在 map は本来一致する。`artifact_admission.py:737` の記録済み binding 検証を通過した後、同 `:791`〜`:797` の比較を常時不一致にすることだけで過剰拒否になる。前段で同じ clean 入力を拒否する層はなく、後段へは到達しない。2 node は別 API consumerだが、赤理由は同じ `CampaignVerifierEpochRejected` に一意化できる。

## 5. 過大主張の有無

指定された未閉鎖面を閉じたと読める過大主張は、コード、docstring、対象 commit message から検出しなかった。

- `artifact_admission.py:722`〜`:725` と `:806`〜`:809` は exact 12 の対象を限定し、`__init__.py`、`__main__.py`、`cli.py`、`report.py` を明示的に除外している。
- `b20c5459` の commit message は、再 export、report、CLI、in-process 改変、未束縛 bootstrap、推移依存、弱化 bytes を先に commit して fresh lock を作る経路が開いたままと明記している。
- `999357c5` は fixture と変異証拠の修正に限定し、production を閉じたとは主張していない。
- full range に含まれる docs 2件は介在した別 task の commit で、T-1143 の閉鎖範囲を広げる記述ではない。

## 総括

NO-GO。レビュー A の所見 1そのものは `closed` であり、fixture 不在による偽の `FileNotFoundError` は解消している。  
fix は production を変更せず、独立 literal、fixture bytes、期待 epoch payload は現行 exact 12 と整合している。  
しかし M1〜M4 は各47 nodeが複数理由で赤になり、対象 verifier drift の commit 済み段階まで到達しないため、変異全体の単一理由性は成立しない。  
さらに M5/M6 は受理集合を変えない診断文字列変異であり、`KILLED` ではなく diagnostic sensitivity pin として扱う必要がある。  
M7 は clean E1 正例2 nodeで過剰拒否を一意に検出でき、前後の拒否 mask も見つからない。  
成果物影響は、現状のままでは変異 matrix が certified gate の検出力を実際以上に主張できる点であり、期待 node と分類の再登録なしには段 6 を閉じられない。