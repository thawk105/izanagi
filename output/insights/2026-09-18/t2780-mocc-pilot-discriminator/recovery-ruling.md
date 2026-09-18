# T-2780 引継ぎ時の限定裁定

既存実装の骨格と段2/3成果物を維持し、段6の再監査へ進む。

- B-MF1: Ended Request Time を含む 5905.nqsv の accounting と qstat 不在を親が読んだ後に receipt 判定を実行した。今回の完走確認を閉じる。judge の file exists 判定だけで終端とする手順を再利用しない。新しい恒久 gate を足さない。
- M8: 同じ binding 欠落を後段 job-result writer が拒否する。正式走の期待 node は既存 probe の node と同じだが、実効理由は writer の binding 欠落拒否。後段 field assertion に到達した証明とはしない。検査を削って単一理由を作らない。
- M2/M3: harness の status が KILLED でも、字句条件と診断文への sensitivity pin として別枠記録する。correctness の受理集合変化の証拠に数えない。
- M1/M4/M5/M6/M7/M8: 振舞いを変える負例6件。M0 はコメントのみの等価対照。baseline および general v4 正例を維持する。
- 旧 local probe の結果は期待 node の発見資料としてのみ利用。正式実績にはしない。旧実行が run_tests.py を通していない逸脱も記録する。
- 正式 spec: recovery-mutation-spec.json、SHA256=328f57828efecfc16910294b8396014048341fd35133cbf1f93bd2e7114dcb89。anchor は固定 f93281e55 に全件一意。
- runbook §7.0 の mutation task を使い計算ノードの1 jobへ束ねる。対象は pilot だけで runner 実行経路を含まない。内側 local runner は計算ノードで tools/run_tests.py を通す。所要の事前見積は旧 probe より240秒、job walltime は3600秒。queue 待ちは実走所要に含めない。
- 重複 marker の削除 nit は性能・正しさ・成果物を変えないため採用せず、既存 test 期待の削除はしない。hydrate の実 PYTHONPATH 全被覆を主張しない。
- 実装修正が必要になった場合は隔離 Codex author のみが編集する。
