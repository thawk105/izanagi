実装の受理条件に直接の誤りは見つかりませんでした。must-fix は proof-chain の検出力不足2件です。

### must-fix

1. post-provenance の D987 再照合をテストが時系列で証明していません。

   実装は初回 preflight 後と再 preflight 後に検査していますが、テストは同じ引数で2回呼ばれたことしか確認していません。[test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:7018) は「初回に2回呼び、[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:5066) の再検査を削除」という変異でも通ります。rc=16 の負例は初回検査だけを証明しています。[test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:1566)

   初回 D987 は通過し、provenance と第2 preflight の後だけ D987 を拒否させ、呼出し順も確認する負例が必要です。

   未修正時: 「TOCTOU 後に D987 を再照合する」という proof 参照を、このテスト群からは主張できません。

2. active fold 中の D987 拒否について、lease 保持分類が未固定です。

   実装は `active_plan is None` を早期に保存し、最終 catch で permanent rejection を release-safe にするか決めており、現在の配線自体は正しいです。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:4977) [dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:5574)

   しかし active forward fold のテストは成功経路だけです。[test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:7692) active plan と final-main runner mismatch を重ね、`release_safe=False`、`retryable_same_request=False`、provenance 非実行、main 非変更を固定する負例が必要です。

   未修正時: active fold の D987 拒否が lease を保持するという proof 参照を置けず、分類退行により処理中 transaction の lease が解放される実装も検出できません。

### nit

- D987 の final-main 側欠落、tree、非blobは実装上 permanent rejection になりますが、専用テストは mismatch と Git lookup failure だけです。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:851) main/tip の同型テストで下位 helper は確認されていますが、D987 固有理由への直接帰属もあると明瞭です。

### refuted

- exact 2述語以外の解除は確認できません。launcher は tested-tip の読取りを残して等値拒否だけを外し、land は両 entry の存在、blob、SHA 検査を残して blob ID 等値だけを外しています。[acceptance_launcher.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:566) [dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1091)

- tested-main bytes 実行、実行後再読、binding report、receipt digest は維持されています。[acceptance_launcher.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:582) [acceptance_launcher.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:595) [acceptance_launcher.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:614)

- land の receipt digest は tested-main content のままです。waiter は tested-tip、checker は main/tip blob 等値に引き続き束縛されています。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1110) [dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1118)

- D987 は区間ごとの any 差ではなく、最後の `incorporated_main_sha` と tested-main の net blob 差を比較しています。復元正例と最終段変更負例も分離されています。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:860) [test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:7050)

- D987 mismatch は provenance より前に permanent、release-safe として拒否され、Git lookup failure は retryable です。通常の main-tip divergence 後に checker lookup failureへ到達する ordering も維持されています。

- schema、非dispatch receipt、Git mode、waiter/checker production、既定 shard 数への変更はありません。

## 総括

実装ロジックは裁定どおりで、受理集合を誤って広げる production bug は確認できませんでした。ただし、D987 の再 preflight 後再照合と active fold 時の release-safe 分類は、現在のテストでは退行を検出できません。この2点を proof-chain の must-fix とします。

read-only 指示に従い、テストは実行していません。