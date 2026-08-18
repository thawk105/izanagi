## 敵対レビュー所見

**A-01 / 正式 workload は selector を省略すると既存 registered 経路を通過する**

- 根拠: `s4-adjudication.md:141-149` は「正式 selector を渡した経路は fail-closed」「正式 campaign identity を一度も発行しない」と裁定している。一方 `orchestrator/campaign/p3_autonomous_workload_trial.py:3427-3429` は `workload_profile: str = EXPLORATORY_WORKLOAD_PROFILE` とし、`:853-854` は探索 selector なら即 `return` する。`orchestrator/tests/test_p3_autonomous_workload_trial.py:5579-5594` の `_t325_run` は `workloads=["rr80"]` のまま `workload_profile` を渡さず、`:5843-5845` は逐語で `report = _t325_run(...)`、`assert report["status"] == "complete"`。
- 深刻度: **must-fix**
- 成果物影響: issued capability が存在すれば rr80/rr20 の正式 run が探索 selector のまま complete となり、report、lifecycle、trial ledger の正式 workload 受理集合が裁定外に拡大する。

**A-02 / 正式 Layer-3 受理枝を汎用枝へ混入し、探索 identity で正式 artifact を受理する**

- 根拠: `orchestrator/campaign/p3_autonomous_workload_trial.py:226-232` は `HOLDOUTS` を `WORKLOADS` へ追加し、`:1039-1081` の `_prepare_manifest_campaign_identity` が正式 workload の campaign identity を発行する。一方 `_campaign_for` は `:702` の `"pilot_scope": "exploratory-ycsb-abc"` と `:716-720` の exploratory `spec_content` を固定する。consumer も `orchestrator/campaign/autonomous_trial_completeness.py:2962-2963` の `workload in producer.WORKLOADS` で rr80/rr20 を受け、`:588` と `:609` で探索 pilot/spec を要求する。これは裁定 `s4-adjudication.md:127-149` の「正式 Layer-3 受理枝を実装しない」「正式 campaign identity を一度も発行しない」と矛盾する。
- 深刻度: **must-fix**
- 成果物影響: rr80/rr20 の campaign lock、Layer-3 report、campaign ID が正式 provenance なしに exploratory artifact として受理され、レポート参照と受理集合が混線する。

**A-03 / legacy provenance の独立再導出は正式 consumer に接続されていない**

- 根拠: 裁定 `s4-adjudication.md:111-113` は「consumer が `load_legacy_freeze` を独立に呼び直す」ことを要求する。実装の consumer 呼出しは `orchestrator/campaign/p3_autonomous_workload_trial.py:855-862` の preflight 内だけで、直後に必ず `raise AutonomousTrialError(...)` する。対して registered completeness は `orchestrator/campaign/autonomous_trial_completeness.py:846-851` で `producer.WORKLOADS` を読むだけである。同ファイル `:735-738` 自身も逐語で「Do not use the exploratory producer's WORKLOADS table for registered holdouts.」と警告している。
- 深刻度: **must-fix**
- 成果物影響: A-01 の経路では source record、legacy path/hash、四 key の独立再導出なしに正式 report と台帳行が complete になり、legacy-v1 参照が成果物から欠落する。

**A-04 / mutable alias により module、producer、arm resolver の独立性が崩れている**

- 根拠: `orchestrator/campaign/p3_autonomous_workload_trial.py:227-231` は逐語で `ycsb=_formal_authority["ycsb"]` とし、producer entry と `HOLDOUTS` に同じ可変 dict を共有させる。producer-module 比較は `:790-795` だが、arm resolver も `orchestrator/campaign/s8c_arm_inputs.py:186-195` と `:409-421` で同じ `HOLDOUTS` を読む。裁定 `s4-adjudication.md:91-93` は object identity を要求せず canonical bytes で束縛するとしている。
- 深刻度: **must-fix**
- 成果物影響: `WORKLOADS["rr80"]["ycsb"]` の一変更が module 表、producer、arm descriptor を同時に変え、四 key と digest の検査を通ったまま report の workload flags と台帳 binding を偽値へ移せる。

**A-05 / 3 sink の正式 scale「照合」は結果を捨てる無効比較**

- 根拠: 裁定 `s4-adjudication.md:95-99` は literal を「entry 由来の値が正式 profile の期待値と一致するか」の照合に使うとする。しかし `orchestrator/campaign/p3_autonomous_workload_trial.py:685-690`、`:734-738`、`:748-752` はいずれも逐語で `_ = (records, threads) == (1_000_000, 48)` とし、結果を一切消費しない。C01 は `orchestrator/campaign/s8c_preregistration_evidence.py:1420-1424` で関数内に整数 token があるかだけを見る。
- 深刻度: **must-fix**
- 成果物影響: C01 report は実効照合なしに `workload-projection-mismatch` を脱し、将来 ratified 参照だけが解けた際の preregistration 受理集合を誤って広げうる。

**A-06 / Layer-3 scale テストは既存 digest gate に過剰決定され、受理集合を反証しない**

- 根拠: `orchestrator/tests/test_autonomous_trial_completeness.py:2986-2989` は descriptor scale と `descriptor_binding.output_sha256` だけを変更し、campaign lock 内の `descriptor_sha256` は更新しない。新 scale gate を除去しても、`orchestrator/campaign/autonomous_trial_completeness.py:583-601` の既存 search-config digest 比較が後段で拒否する。新テストは期待診断文字列だけを変えるため、`DW-M03` 上の受理集合 kill ではない。
- 深刻度: **must-fix**
- 成果物影響: descriptor、binding、campaign lock を自己整合させつつ producer entry だけと違える artifact の受理をテストできず、accepted campaign の descriptor scale と benchmark scale の分離が再発しうる。

**A-07 / producer 側の四 key と descriptor digest guard は削除変異を殺せない**

- 根拠: 実効 guard は `orchestrator/campaign/p3_autonomous_workload_trial.py:790-813`。しかし `orchestrator/tests/test_p3_autonomous_workload_trial.py:423-455` は正常値を再計算して `descriptor == arm_descriptor` と既知 digest を比較するだけで、guard の入力を不一致にしない。consumer 側の tamper test `orchestrator/tests/test_autonomous_trial_completeness.py:3041-3055` は別関数 `C.assert_legacy_workload_profile_source` だけを攻撃する。したがって事前登録 M8/M9 の producer guard 削除は生存する。
- 深刻度: **must-fix**
- 成果物影響: producer の runtime 束縛を削除しても検査が緑になり、formal campaign ID、descriptor digest、arm binding の不一致を台帳へ流せる。

**A-08 / 既存テスト 5 件が既知のまま赤になる状態で引き渡されている**

- 根拠: `s5-author.md:27-35` は 5 件の衝突を明記する。実際に `orchestrator/tests/test_p3_autonomous_workload_trial.py:5747` と `:5818` は flat flags と構造化 `WORKLOADS["rr80"]` を比較し、`:6121` と `:6154` は逐語で `assert "rr80" not in A.WORKLOADS`。さらに `orchestrator/tests/test_s8c_preregistration_predicates.py:151` は C01 reason を `"workload-projection-mismatch"` に固定したままである。
- 深刻度: **must-fix**
- 成果物影響: 現状は受入不能であり、赤を無視して land すれば formal workload の supported set、report shape、C01 台帳 reason が既存契約から無審査で変わる。

**A-09 / source path/hash の一部 assert は同じ loader を二度呼ぶだけ**

- 根拠: `orchestrator/tests/test_p3_autonomous_workload_trial.py:428-431` は `_formal_profile_source_record()` の直後に同じ `load_legacy_freeze()` を呼び、`source_record["sha256"] == legacy.sha256` を比較する。producer helper 自身も `orchestrator/campaign/p3_autonomous_workload_trial.py:816-846` で同じ loader の `sha256` をそのまま source record に入れる。
- 深刻度: **nit**
- 成果物影響: 受理集合は変わらないが、この assert 単体には独立 provenance の検出力がない。

## 確認済みの非違反

- `holdout_conjunction_hits` を変更 6 file へ個別適用し、rr80/rr20 とも全 file で 0 hit。repo scan invariant の現時点の直接違反はない。
- `output/s8b-freeze/holdout_freeze.json` は HEAD と同じ SHA-256 `315b1eb8...688`。`V1_FREEZE_SHA256`、`s8b_holdout_freeze.HOLDOUTS`、`trial_registry.HOLDOUT_BINDINGS` の staged diff もない。
- R-02 の run-root/exemption、R-03 の oracle driver は変更されていない。
- baseline hash は指定 `m3-baseline.json` と一致し、skip、xfail、削除、揮発 payload の新規焼き込みは見つからない。
- pytest は実走していない。静的検査結果のみである。

**全体判定: NO-GO**

## 総括

最大の穴は、formal selector だけを止め、rr80/rr20 と default exploratory selector の組合せを止めていないこと。
実装自身の registered fixture が、その別経路で正式 run を complete にできると証明している。
その経路では legacy provenance の独立再導出も通らず、Layer-3 は正式 artifact を探索 identity として受理する。
さらに mutable alias と無効比較が canonical 束縛を弱めているため、land 前の修正が必須である。