R2 と R10 を修正しました。静的判定は両方 `closed` です。

### 実装

[p3_b4_closed_critic.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/orchestrator/campaign/p3_b4_closed_critic.py:944)

- certified 経路から次の注入口を除去しました。
  - `_CERTIFIED_RUNNER`
  - `_CERTIFIED_WHICH`
  - `runner` 引数
  - `executable` 引数
  - runner・executable・evidence class を受ける共通 factory helper
- certified factory 内で `shutil.which("claude")` と `subprocess.run` を直接使用します。
- test-only 入口の signature は次のとおりです。

```python
create_b4_closed_critic_pair_for_test(
    *,
    on_cfg: CampaignConfig,
    off_cfg: CampaignConfig,
    artifact_root: Path,
    executable: str | os.PathLike[str],
    runner: Callable[..., Any],
    repository_root: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> B4ClosedCriticPair
```

- test-only receipt は `evidence_class="test-only"` 固定です。
- `assert_b4_arm_pair` は certified/test-only の両方を構造検査し、異なる evidence class の混成を拒否します。
- same-process Python 書換えと PATH binary 非認証の非保証記述は、今回の保証境界と一致していたため維持しました。

### テスト変更

[test_p3_b4_closed_critic.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/orchestrator/tests/test_p3_b4_closed_critic.py:466)

変更した nodeid は以下です。新規 nodeid はありません。

- 変更・改名: `::test_m5_certified_factory_has_no_runner_seam_and_binds_subprocess_run`
- 変更: `::test_unregistered_pair_control_rejects_reused_session_after_byte_recheck`
- 変更: `::test_unregistered_pair_control_rejects_reused_provider_identity`
- 変更: `::test_r10_payload_field_values_have_exact_one_field_positive_negative_pairs`
- 変更・改名: `::test_p4_test_only_pair_reports_precursor_differences_without_rejecting_them`
- 変更: `::test_r1_terminal_pair_revalidation_rejects_status_and_payload_byte_tamper`
- 変更: `::test_m16_sent_on_off_payload_bytes_match_independent_admitted_view_digests`
- 変更: `::test_m17_pair_id_accepts_one_factory_and_rejects_mixed_factories_only`
- 変更・改名: `::test_m18_certified_factory_has_no_executable_seam_and_resolves_fixed_claude`
- 変更: `::test_m19_pair_gate_accepts_terminal_paths_and_rejects_promoted_dataclasses`
- 不変: 上記以外の既存 nodeid

M5/M18 は fake runner で certified receipt を作らず、certified API に注入口がないことと直接束縛を検査します。R1・R3・R5・M16〜M20 の構造・byte-level 検査は test-only pair 上で維持しています。

R10 には `{"projected_digest": 1, "result": "rejected"}` を追加し、exact reason は `projected_digest must be a non-empty exact str` です。

## 総括

- R2: `closed`。certified seam を除去し、test-only との混成・昇格負例を固定。
- R10: `closed`。truthy な非 str digest の負例を追加。
- 構文解析: OK。
- 差分 whitespace 検査: OK。
- pytest・変異試験: 指示どおり未実走。実装済み・未実走であり、緑とは報告しません。
- 編集は指定された 2 ファイルだけです。commit、add、stash、branch 操作は行っていません。