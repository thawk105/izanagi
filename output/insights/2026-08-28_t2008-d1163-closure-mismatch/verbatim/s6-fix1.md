修正は完了し、すべて unstaged 差分として追加しました。段 5 の index は pre-fix snapshot と完全一致し、stage/commit は行っていません。

| 所見 | 状態 | 閉じ方 |
|---|---|---|
| P2-2 / LB-01 | closed | `write_summary()` が各行の `HISTORICAL_RAW` と exact marker を検査・表示。生成本文の正例、marker 欠落・purpose 不一致負例を追加 |
| LB-02 | closed | fig2b/fig4 は generation-time 固定 SHA で検証。記録 SHA 改竄は拒否し、新 producer の current SHA は独立テストで検査 |
| S1 / LB-03 | closed | production `load_campaign()` → 一時 PNG/PDF → `build_provenance()` を通し、全 campaign input の marker を検査 |
| WorkloadDigest / LB-04 | closed | `fastest` を従来の第7 positional 位置に戻し、新 field を後置。historical marker/certified `None` を維持 |
| 回帰 | なし | 入力/output bytes 改竄、合成 generator bytes 改竄負例を維持 |

受理の含意: 過去 fig2b/fig4 は記録された生成時 SHA が固定値と一致すれば、現行 generator bytes が異なることだけでは無効になりません。
拒否の含意: 記録 generator digest、入力 bytes、出力 bytes、合成 fixture の generator bytes の不一致は引き続き拒否されます。

編集 path:

- [p2_2_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-author/orchestrator/campaign/p2_2_report.py:249)
- [digest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-author/orchestrator/critic/digest.py:101)
- [test_bench_first_real_wal.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-author/orchestrator/tests/test_bench_first_real_wal.py:376)
- [test_critic.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-author/orchestrator/tests/test_critic.py:649)
- [test_backoff_figure_provenance.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-author/orchestrator/tests/test_backoff_figure_provenance.py:354)
- [test_plot_backoff_ci.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-author/orchestrator/tests/test_plot_backoff_ci.py:348)
- [test_s1_9pair_figure_provenance.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-author/orchestrator/tests/test_s1_9pair_figure_provenance.py:1032)

通る正例として追加・強化した node は P2 summary 本文、fig2b/fig4 historical provenance、両 production producer の current SHA、S1 最終 provenance、`WorkloadDigest` positional 互換です。

実走は `python3 tools/run_tests.py` で次の10 nodeを指定しました。

- P2 summary
- critic positional / historical marker
- fig2b real provenance、input・generator・PNG改竄
- backoff current producer SHA
- fig4 real provenance
- S1 final provenance marker

結果は `child_started=false`, rc=16 でした。Pegasus の `qstat -Q` preflight rc=1により全 node未起動で、緑とは報告しません。生成された dispatch receipt は除去済みです。

静的検査は成功しています。

- 変更7 Python fileの `py_compile`: rc=0
- `git diff --check`: rc=0
- staged diff と `s6-pre-fix-snapshot.patch` の完全比較: rc=0
- fig2b/fig4の記録 SHAと固定値の一致、および現行 SHAとの差を確認
- S1 self-run exact set 27件の整合を確認

未実走範囲は上記10 node、変更test module全走、保持負例全走、変異検査、親受入全走です。波及候補は、旧marker無し backoff provenance と新producer出力を区別するversion境界、external official campaignの親環境実測、および既裁定の `current-closure-unavailable`・persisted WAL共通gateです。

docs、output、凍結artifact、campaign、PNG/PDF/provenance bytesは編集していません。

## 総括

4件の must-fix はコードとテスト境界上で closed です。段5差分はstagedのまま完全保持し、fixだけを許可された7 pathのunstaged差分として追加しました。残件はPegasus infrastructure failureにより未実走のpytest検証だけです。
