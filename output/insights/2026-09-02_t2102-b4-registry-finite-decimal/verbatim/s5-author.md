## 変更した file と行

- [p3_b4_analysis_ledgers.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2102-author/orchestrator/campaign/p3_b4_analysis_ledgers.py:344)
  - `reference is not None` の guard 内で既約分母から 2 と 5 を除去。
  - 残りが 1 でなければ指定 message で拒否。

- [test_p3_b4_analysis_ledgers.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2102-author/orchestrator/tests/test_p3_b4_analysis_ledgers.py:158)
  - `(1, 10)` と `None` の seal 正例。
  - `(1, 3)` と `(1, 30)` の hash 層での拒否。
  - `_ratio_from_payload` の canonical control と exact error signature を固定。

- [test_p3_b4_raw_record_producer.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2102-author/orchestrator/tests/test_p3_b4_raw_record_producer.py:1138)
  - M12 の node 名を維持。
  - 実 `_fraction_token((1, 3))` と production catch の全 issue fields を検査。

## 現行と変更後の受理・拒否

- 現行は `None` とすべての正の exact rational を受理し、`(1, 3)`・`(1, 30)` も受理。
- 変更後も `None`、`(1, 10)`、整数比を受理。
- `(1, 3)`・`(1, 30)` は `reference_tps has no finite decimal expansion` で拒否。
- 型不正・非正値は従来の検査と message が先に発火。
- manifest-only codec の `[1, 3]` 受理は意図どおり変更なし。

## 実走した検査

- `git diff --check`: 緑。
- ledger file 全体: runner rc=16。`qstat -Q preflight rc=1`、`child_started=false` のため実走 nodeid は 0。
- 新設 ledger node だけの再試行も同じ infrastructure failure で未実走。
- raw producer file 全体: 同じ rc=16 で未実走。
- M12、M13、`test_mutation_node_mapping_is_complete_and_one_to_one` は実装済み・未実走。
- runner が作った今回分の診断 directory 3 個は削除し、`output/` に差分を残していません。

## 波及可能性

- `p3_b4_prerun_issuer.py`: 新規 issuance の scheduled hash、seal、manifest generation、publication reload。
- `p3_b4_analysis_path.py`: registry load と completeness 検査。
- `p3_b4_analysis_prereg_consumer.py`: 整数 reference の自己検査は維持される一方、ledger member と closure receipt の digest は変化。
- 共有 fixture: `test_p3_b4_analysis_path.py`、`test_p3_b4_prerun_issuer.py`、raw producer fixture は分母 1・2・10 のため静的には影響なし。
- consumer test: analysis path、prereg consumer、prerun issuer、raw producer の各 test file が間接的な回帰確認対象。
- repository 外に非有限十進 registry があれば、新 loader では拒否される。

## 残る不確実性

- Pegasus の dispatch infrastructure failure により、指定された pytest 範囲は未実走。
- 変更後の source-closure digest の具体値は実走で未確認。
- repository 外に保存された closure receipt や独自 caller が存在する可能性は静的検索では否定不能。

## 総括

親裁定のプラン v2 を指定の 3 file に実装しました。
`None` の正当な受理を維持し、非有限十進だけを registry lifecycle で拒否します。
差分検査は緑ですが、pytest は dispatch infrastructure failure により未実走です。
docs、production producer、output の最終状態、git staging・commit には触れていません。