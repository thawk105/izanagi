単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- **作業 root (書込み可。ここだけを編集する)**: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix1`
- **親の段 4 裁定 (§2 の 4 箇所目が本 fix の権威)**: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/s4-adjudication.md`
- 契約の追記訂正 2 の草稿 (束縛の理由): `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/contract-v3.1-erratum-2.md`
- 先行子 A1 の報告: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s5-a1.md`
- 先行子 A2 の報告: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s5-a2.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix1/CLAUDE.md`

# 段 6 fix 1 — launcher test の planned helper を訂正済み ordinal 束縛へ合わせる

## 所有 path (これ以外を 1 行も変えない)

- `orchestrator/tests/test_s8b_floor_attempt_launcher.py`

**production code は変更しない。docs は編集しない。commit しない。`git add` もしない。**

## 親が実測した赤 (12 件、原因は 1 つ)

親が統合 tip `6a8223dd0` で実走した結果は
`test_s8b_floor_attempt_launcher.py` の **12 failed / 287 passed** で、
12 件すべてが同じ理由である。

```
orchestrator.campaign.s8b_terminal_evidence.TerminalEvidenceError:
[s8b-terminal-evidence] campaign_record.retry_ordinal differs from durable identity
```

赤になった nodeid:

```
test_certified_pre_probe_competing_branch_publishes_sealed_terminal
test_test_seam_forwarding_registry_lacks_launcher_origin_capability
test_v2_protocol_snapshot_precedes_builder_mutation
test_v2_profile_reaches_draft_but_fake_cannot_issue_capability
test_v2_builder_receives_detached_sources_not_private_snapshot[repetition-terminal.observation_sha256 differs]
test_v2_builder_receives_detached_sources_not_private_snapshot[probe-campaign_record.probe_before differs]
test_v2_capture_subclasses_reach_a_sealed_draft[failure0-OSError]
test_v2_capture_subclasses_reach_a_sealed_draft[failure1-OSError]
test_v2_capture_subclasses_reach_a_sealed_draft[failure2-RuntimeError]
test_v2_perf_receipt_snapshot_precedes_builder_mutation
test_launch_probed_competing_skips_capture_and_matches_existing_terminal
test_launch_probed_clean_matches_existing_terminal_and_classification
```

**原因**: この file の helper (`_v2_terminal_from_opened()` 付近、旧 `:1490` 相当) が planned の
`campaign_record` に `retry_ordinal=reservation.slot_id[4]` (= 0) を入れている。
訂正後の束縛では **planned は `None`**、retry は `measurement_ordinal` である。

## 直す内容

- helper が planned の `campaign_record` へ渡す `retry_ordinal` を `None` にする。
  retry を作る helper があれば `measurement_ordinal` を渡す。
- **強度を落とさないこと。** 訂正後もこの file の中で次が成り立たなければならない。
  - planned なのに `retry_ordinal` が非 null なら terminal 発行が拒否される (負例を 1 つ置く)
  - retry の `retry_ordinal` を `attempt_ordinal` (recovery 軸) へ差し替えたら拒否される
    (この file に既に等価な負例があるなら新設せず、その nodeid を報告する)
- `measurement_ordinal` と `attempt_ordinal` を**異なる値**にできる箇所では異なる値にし、
  どちらへ束縛されているかが判別できる形にする。

## 禁止

- production code (`orchestrator/campaign/**`) を 1 行も変えない。
- 赤を **skip・xfail・deselect・assert 緩和・期待値反転**で消さない。
  実装が誤りだと判断したら**直さず報告して止まる**。
- 所有外の test file を変えない。
- 期待値へ揮発 payload を焼き込まない。
- 出力へ結合文字 U+0300〜U+036F を使わない。

## 検査 (自分で実走する)

**`tools/run_tests.py` は sandbox では rc=16 になるので使わない。** 自走 harness を使う。

```
cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix1
PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_attempt_launcher.py
PYTHONPATH=. python3 orchestrator/tests/test_s8b_terminal_evidence.py
PYTHONPATH=. python3 orchestrator/tests/test_s8b_attempt_registry.py
```

3 file すべての passed/failed の実数を報告する。走らせていないものを緑と書かない。

## 出力形式

```
## 総括
(3-5 行)

## 直した helper と理由 (file:line)

## 強度の対照 (負例 2 種の nodeid と、新設か既存かの区別)

## 実走結果 (command と passed/failed の実数)

## 残った懸念
```
