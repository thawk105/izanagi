# [T-2127] 段 6 fix 裁定

段 6 レビュー 2 本と親の実測を突き合わせ、fix 子へ渡す所見を確定した。

## 採用する所見 (real・must-fix)

### P-01 (親の実測) — `_certifying_campaign` の commit が環境契約と env_tag 不一致

**5 つのテストが赤である。**実装 commit `107fc0b98` 後の焦点走で測った
(`test_artifact_admission.py` + `test_layer3_report.py` + `test_bench_first_real_wal.py`
+ `test_t1286_commit_receipt.py` を走らせ 5 failed / 347 passed)。

- `test_layer3_report.py::test_accepted_report_requires_e1_and_records_epoch`
- `test_layer3_report.py::test_certified_report_omits_current_verifier_conformance`
- `test_layer3_report.py::test_render_accepted_persists_certifying_report`
- `test_layer3_report.py::test_render_and_render_accepted_race_rejects_second_writer[render]`
- `test_layer3_report.py::test_render_and_render_accepted_race_rejects_second_writer[render_accepted]`

赤の本文はすべて同一である。
`AttemptTopologyError: commit: env_tag が environment contract と不一致`

**親が測った原因 (子の推測に任せない):**
- `orchestrator/tests/test_layer3_report.py:534` の `_record()` は `env_tag="test-env"` を書く。
- 同 file の `_campaign()` は `build_v2_campaign_lock(identity_preimage)` を authorization
  無しで呼ぶ。`orchestrator/tests/campaign_lock_test_support.py:29-30` の既定は
  `env_contract.authorize("linux-baremetal")` である。
- `orchestrator/campaign/wal.py:1511-1513` は commit record の `env_tag` が
  解決済み contract の `env_tag` と一致することを要求する。
- `_certifying_campaign` (`test_layer3_report.py:245-297`) は commit を
  `start.env_tag` (= `"test-env"`) で書くため不一致になる。

**注意:** 実装 commit 前の走行では 6 件赤だったが、6 件目
(`test_accepted_report_rejects_no_commit_campaign`) は
`artifact_admission.py` が未 commit だったことによる contract-loader drift
(`state=E1-stale reason=current-closure-unavailable`) であり、実装の回帰ではない。
commit 後の走行で緑になっている。**この node を「直す」対象にしてはならない。**

### RA-01 (レンズ A・real) — M4 変異の kill node が単一理由でない

`orchestrator/tests/test_artifact_admission.py:1740-1742` は
`(True, IntSubclass(0))` を 1 つの loop で順に検査する。
exact int 検査を削除すると、最初の `True` は snapshot 件数 0 との不一致で
`ValueError` になり、そこで test が終わる。実際に exact 型検査だけが拒否する
`IntSubclass(0)` へ到達しない。

変異事前登録 (`DW-M01`) は「無効化時の赤理由が一つに絞れること」を要求する。
**この形では M4 の赤を exact 型境界の検査と評価できない。**

### RB-01 (レンズ B・real) — 件数の非保証が docstring に無い

段 4 裁定の節 5 は「件数 field は共通入口の投影であって検証の証拠ではない」ことを
docstring へ明記せよと定めた。実装は「view 自体は commit の存在を保証しない」までは
書いたが、**件数が検証通過を証明しないことを書いていない**。
`require_certified_commit_evidence` の docstring も "admitted COMMIT" と書いており、
独立した検証証拠のように読める。

**code を強化しない。token 強化も新 gate も足さない。契約記述だけを裁定へ合わせる。**

## 採用するが fix 子へ渡さない所見

### RB-02 (レンズ B・real) — acceptance ledger の新規 7 node

duration は親が実測して `tools/update_acceptance_duration_ledger.py` で add-only 追加する。
fix 子は推定値を書いてはならない。fix 完了後、親が受入全走の JUnit から入れる。

対象 node (レンズ B の列挙、親が実走後に確定する):
- `test_certified_commit_evidence_rejects_no_commit_campaign`
- `test_certified_view_checks_every_commit[both-commits-valid]`
- `test_certified_view_rejects_commit_count_snapshot_mismatch`
- `test_certified_view_rejects_negative_commit_count`
- `test_certified_view_rejects_non_exact_commit_count`
- `test_real_wal_replay_landscape_rejects_e1_without_commit`
- `test_accepted_report_rejects_no_commit_campaign`

## refuted / 不採用

- **レビュー B の「後続 commit の実行主体は git metadata だけでは確定できない」** —
  情報として正しいが所見ではない。実装 commit `107fc0b98` は親が
  Codex author + Claude manager の trailer 付きで作った。provenance 監査 rc=0。
- **自己 SHA の変化 (`artifact_admission.py` `fb3e695a` → `994d3f4b`、
  `replay.py` `b5ed150e` → `6110b424`、`layer3_report.py` `362fb98f` → `920a247a`)** —
  段 4 節 7 のとおり既存の設計性質であり、本 wave の blocker にしない。
  親が値を記録する (レンズ B が測った上記を採用)。
- **受理集合の拡大** — 両レンズとも「見つからない」で一致。親の読解とも一致。所見なし。

## 段 6 の焦点走 (親の実測、実装 commit 107fc0b98 時点)

| 走行 | 結果 |
|---|---|
| `test_artifact_admission` + `test_layer3_report` + `test_bench_first_real_wal` + `test_t1286_commit_receipt` | **5 failed / 347 passed** (P-01) |
| `test_critic` + `test_backoff_consumers` + `test_autonomous_trial_completeness` + `test_layer3_admission_diagnosis` | 434 passed |
| `test_p3_s4_loop` + `test_p3_b4_closed_critic` + `test_s6_sort_sweep` + `test_s8a_trigger_sweep` + `test_p3_b4_wiring_probe` | 541 passed |
