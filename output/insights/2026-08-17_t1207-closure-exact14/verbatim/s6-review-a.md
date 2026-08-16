### L-A-01 / must-fix

- **主張:** A-01 と A-05 の記録実装が未完であり、現状のまま land すると exact 12 と撤回済みの受理集合主張が正本に残る。
- **根拠:** 裁定は新 D と worklog で主張を限定すると要求する (`/home/SFC/tanab/.claude/jobs/f3762925/tmp/wave/ruling-v2.md:7-18`, `:26-28`, `:204-208`)。実装報告も未 land と明記する (`/home/SFC/tanab/.claude/jobs/f3762925/tmp/wave/s5.md:85-88`)。現在の正本はなお「exact 12」とし、未実証の「anomaly を含む run が certified 集合へ入りうる」と記す (`docs/decisions.md:18501-18522`)。
- **反例または検算:** 段 7 で裁定 §4 の限定逐語を持つ新 D、M2/M3 主張の撤回を持つ worklog、D442 の限定 supersede が追加されれば本所見は落ちる。
- **成果物影響:** certified 選択の実コードは変わらなくても、レポートと台帳の proof reference が古い exact 12 と過大な受理集合主張を正本として参照する。

### L-A-02 / nit

- **主張:** 恒真な test node はゼロだが、新設 node 内に production-only mutation では発火しない冗長 assert が 6 個ある。
- **根拠:** 対照 node の `mutated != original` と復元後の equality (`orchestrator/tests/test_t671_source_binding.py:219`, `:239-242`)、clean node の set 比較 (`:278-283`)、census の literal 件数・disjoint 3 個 (`:297-314`) は、同じ node 内の先行条件または固定 literal から導かれる。一方、各 node の実効 assert は対象 path を含む capture/live drift (`:244-256`)、独立 `git cat-file` digest (`:284-291`)、実 package 集合 (`:306-315`) なので node 全体は恒真ではない。
- **反例または検算:** test source を固定したまま production だけを変えて、挙げた assert のいずれかが先行 assert より先に独立して赤になれば本分類は落ちる。
- **成果物影響:** 冗長 assert を残しても受理集合・レポート・台帳値は変わらず、保守上の雑音だけなので nit とする。

## 静的検算

- 対照テストは `campaign_lock` ではなく direct-import 後の module global を差し替える (`contract_loader_binding.py:15`, `test_t671_source_binding.py:222-231`)。capture/live はその global を実参照する (`contract_loader_binding.py:329`, `:348`)。復元は保存した production object へ戻り (`test_t671_source_binding.py:203`, `:233-242`)、capture と live の双方で例外型、`contract-loader-drift`、対象 path を検査する (`:244-256`)。
- clean node は fixture が返す期待 hash を使わず、独立 `git cat-file` と SHA-256 を照合する (`test_t671_source_binding.py:264-290`)。
- census は実 checkout の `orchestrator/verifier/` 直下を走査する (`test_t671_source_binding.py:294-315`)。`.pyc` と `__pycache__` は suffix/file 条件で除外され、新しい直下 `.py` と有効な `.py` symlink は集合差で赤になる。editable install は走査先を変えない。
- scope と excluded scope は裁定逐語と連結後も完全一致する (`artifact_admission.py:65-72`, `test_artifact_admission.py:993-1001`)。余分な空白・欠落はない。
- 削除された assert、skip、xfail、期待値緩和はゼロ。旧 exact-12 tuple assert は exact-14 nodeへ保持され (`test_t671_source_binding.py:166-175`)、件数 assert は 12 から 14 へ強化された (`test_artifact_admission.py:1118`)。
- A-02 は実装済み。A-06 は復元・対照・旧 wire 拒否まで実装済みで、変異実測は親担当。A-07 は Git config 隔離済み (`test_t671_source_binding.py:60-99`)。A-03/A-04/A-08/A-09 は裁定どおり scope 外。A-01/A-05 は L-A-01 の段 7 記録待ち。
- pytest、build、変異、file-addition probe は実行しておらず、緑とは判定していない。

## 総括

コード・テスト差分に実効性を失う must-fix は見つからなかった。  
恒真な test node はゼロで、冗長 assert は 6 個あるが検出本体は独立している。  
唯一の land blocker は、A-01/A-05 の新 D・worklog 記録がまだ存在しないこと。  
静的レビューのみであり、実測結果は親の段 6 に委ねる。