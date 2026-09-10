## 総括

**GO（静的レビュー）**。must-fixは0件です。許可集合、条件関門、T-2535のoffline供給、receipt束縛に実害のある退行は見つかりませんでした。

ただしpytestと変異は未実走なので、親の実走完了までは「緑」とは判定しません。

## 所見

- **refuted: 受理集合の過剰拡張**
  - submit/jobともexact `{5,20,50,80,95}`です。[submit_certify.sh:40](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/submit_certify.sh:40)、[certify_calibration.sh:154](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:154)
  - `+5`、`05`、空白付き、全角、`51`は通りません。receipt用の整数化はexact関門後なので、受理集合も広がりません。[submit_certify.sh:159](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/submit_certify.sh:159)

- **refuted: 条件関門の弱化**
  - `BACKOFF_FIXED`、requested value `-1`、stock comparison、meaning case、use class、timeout 300秒は維持されています。[certify_calibration.sh:430](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:430)
  - 呼出条件もsiloのみのままです。[certify_calibration.sh:688](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:688)

- **refuted: T-2535のoffline供給または独立verifier喪失**
  - 3依存のjob-private copyと独立した`THIRD_PARTY_VERIFY_PYTHON`選定を保持しています。[certify_calibration.sh:576](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:576)
  - 5個のFetchContent引数もconfigureと条件関門に保持されています。[certify_calibration.sh:676](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:676)

- **refuted: receiptと実行workloadの分断**
  - submit receipt、job側再照合、calibrator argv、job resultまで同じrratioが束縛されています。[certify_calibration.sh:214](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:214)、[certify_calibration.sh:928](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:928)、[certify_calibration.sh:958](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:958)

- **real、受入前の非コード条件: M8 node集合の再probeが必要**
  - 旧specは1 nodeだけですが、bare `python3`をexit 97にするproduction harnessにより、silo経路を使う複数nodeへ失敗が広がります。[reference-mutation-spec.json:125](/work/1/SFC/tanab/dev-wave-jobs/t2515-recovery-20260910/reference-mutation-spec.json:125)、[test_pegasus_calibration_workload.py:593](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:593)
  - 最小対応は予定どおり、全件SURVIVED指定のprobeから観測node完全集合を機械生成することです。手作業で旧1 nodeを流用してはいけません。

- **real、nitのみ**
  - [certify_calibration.sh:691](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:691) の「pending a separate user ruling」は裁定済みの現状と不一致です。実行値や受理集合への影響はありません。直すなら「本waveでは保持し、撤去は別変更単位」とする1行訂正で十分です。
  - [certify_calibration.sh:922](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:922) は直後の代入で上書きされる冗長行ですが、挙動への影響はありません。

失敗insightはaccepted未取得と過去実測を明確に区別しており、回収した7 evidence fileも`ec17af5dc`上のblobと全件一致しました。[insight README:15](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/output/insights/2026-09-10_t2515-rr95-rr5-calibration/README.md:15)

静的確認として`bash -n`、`git diff --check`、U+0300〜U+036F走査は成功しています。pytest、変異、測定は実行していません。