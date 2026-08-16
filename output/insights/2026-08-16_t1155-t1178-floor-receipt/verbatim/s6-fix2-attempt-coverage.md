## 1. ticket が実際に消費される条件

消費は次の条件をすべて満たした場合だけ発生します。

- [s8b_floor_campaign.py:4094](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:4094) で `session-start` を durable に記録する。
- [s8b_floor_campaign.py:4107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:4107) の binary 再 hash が一致する。
- [s8b_floor_campaign.py:4115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:4115) の pre-probe が成功し、`probe_before["competing"] is False` である。
- [s8b_floor_campaign.py:4133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:4133) から wrapper を呼び、[同:3883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:3883) で measure より先に `consume_attempt_ticket` を呼ぶ。
- [s8b_holdout_admission.py:1394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1394) で admission が生存し、attempt が frozen ticket 集合内である。
- [同:1349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1349) の journal 認可を満たす。planned は schedule/cell/round/trigger が一致し、retry は同一 cell の invalid planned trigger が一意に存在する。
- [同:1414](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1414) で未使用 marker を `O_EXCL` 作成し、attempt ledger へ追記する。

したがって `session-start` は認可であり、消費そのものではありません。consume 後に measure が crash すると、marker・ledger・`session-start` は残りますが completed `session` は残りません。

## 2. 現行導出がずれる経路

- `test_resume_reuses_manifest_perf_preflight_without_reprobing`
  - 2 回目の measure callback が consume 後に crash。旧導出は completed session が無いため、前 run の消費行を期待集合から落としていました。
- `test_resume_rejects_tampered_binary_but_succeeds_when_untampered`
  - seq3 の consume 後 crash 行が残ります。binary 復旧後もこの行は forward-only で再実行されず、旧期待集合だけが欠落します。
- `test_resume_forward_only_skips_completed_and_crashed_seqs`
  - 名指しの seq3 が `session-start + marker + ledger` のみとなります。resume は seq3 を skip するため、completed session 由来の旧導出では永久に拾えません。
- `test_resume_under_unchanged_current_contract_generation_completes`
  - 2 回目の measure で同じ consume 後 crash。contract 世代は原因ではなく、前 run の orphan consumption が原因です。
- `test_resume_does_not_reissue_retry_slot_after_retry_start_crash`
  - retry1 は認可・consume 後に crash。resume は ordinal 1 を再発行せず ordinal 2 を使うため、retry1 の ledger 行だけが completed session 射影から脱落します。
- `test_official_resume_validates_certificate_and_completes`
  - official の証明書検査後も、4 回目の consume 後 crash 行が残ります。pilot/official の差ではなく同じ orphan consumption です。
- `test_deterministic_artifacts_across_roots_and_subprocess_environments`
  - deliberate crash の無い fresh 経路です。session の結果射影を消費事実の正本としていた非 resume 側を通ります。新導出では root/process 非依存の frozen marker と lifecycle を使用します。
- `test_generation_two_rejected_before_artifact_io`
  - generation-scope を強制的に 1 にした後の full validation が live admission consumer へ到達します。ratified consumer は検証済み full journal を持ちながら completed sessions だけを渡していたため、認可 lifecycle を失っていました。

## 3. 直した内容

- [s8b_holdout_admission.py:1764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1764)
  - `session-start` と completed `session` を分離。
  - planned/retry の認可を `consume_attempt_ticket` と同じ条件で再検査。
  - 全 frozen attempt の marker path を有限列挙し、durable marker が存在する認可済み attempt を期待集合に採用。
  - consume 後 crash は marker/ledger があれば受理し、consume 前 crash は両方無ければ受理。
  - completed non-competing の marker 欠落と、completed competing の marker 存在を拒否。
- [s8b_floor_campaign.py:4407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:4407)
  - `runner.records` から `session-start` と `session` だけを射影する `_attempt_lifecycle_records` を追加。
  - campaign/round/terminal 等は inspector へ渡しません。
- [s8b_floor_campaign.py:4484](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:4484)、[同:4510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:4510)
  - finalize と live self-check の双方へ lifecycle 射影を渡すよう変更。
- [s8b_ratified_freeze.py:3065](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_ratified_freeze.py:3065)
  - 検証済み journal から attempt lifecycle を渡すよう変更。
- [s8b_holdout_freeze.py:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_freeze.py:225)、[同:1431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_freeze.py:1431)
  - sibling journal を strict JSONL として読み、journal の starts と result の completed sessions を consumer 検査へ渡すよう波及修正。

## 4. coverage 検査を緩めていない根拠

- [s8b_holdout_admission.py:1889](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1889) で、認可 `session-start` の無い marker を拒否します。
- [同:1904](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1904) で、non-competing の marker 欠落と competing の余分 marker を拒否します。
- [同:1933](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1933) の検査は、引き続き `set(actual_attempt_rows) != set(expected_attempt_rows)` という双方向の完全一致です。
- 余分 ledger 行は actual 側だけに存在して拒否され、欠落行は marker 由来 expected 側だけに存在して拒否されます。
- [同:1937](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1937) では各行の全 field 完全一致も維持しています。

片方向包含、余分行の無視、resume skip、fail-open は導入していません。

## 5. 追加した positive control

すべて未実走です。

- `orchestrator/tests/test_s8b_holdout_admission.py::test_inspection_resume_accepts_prior_run_crashed_consumption_exact_coverage`
- `orchestrator/tests/test_s8b_holdout_admission.py::test_inspection_resume_rejects_extra_attempt_ledger_row`
- `orchestrator/tests/test_s8b_holdout_admission.py::test_inspection_resume_rejects_missing_attempt_ledger_row`

既存テストの期待値、skip、xfail、assertion は変更していません。

静的確認のみ実施しました。

- 対象 5 ファイルの `ast.parse`: 成功
- NFC 正規化検査: 成功
- pytest・`tools/run_tests.py`: 指示どおり未実走

## 6. 所有外への波及

live admission consumer である `s8b_ratified_freeze.py` と `s8b_holdout_freeze.py` まで lifecycle 射影を伝播しました。公開 verifier/inspector の関数シグネチャは変更していません。

docs、`freeze_verification_hold.py`、`output/` は編集していません。git 操作、commit、Web 検索も行っていません。

## 総括

特定した消費条件: canonical `session-start` 認可と binary/pre-probe 検査を通り、competing が false の場合だけ、measure 直前に marker と attempt ledger が作られます。

直した導出: completed session ではなく、認可済み lifecycle と frozen attempt の durable marker から実消費集合を導出します。consume 後 crash も正確に復元します。

緩めていない根拠: actual/expected の双方向完全一致と全 field 一致を維持し、余分 marker・余分 ledger 行・欠落 ledger 行をすべて拒否します。