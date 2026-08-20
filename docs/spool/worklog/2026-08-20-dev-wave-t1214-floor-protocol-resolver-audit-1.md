---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1214-floor-protocol-resolver-audit
seq: 1
title: "[T-1214] 床値 protocol path 固定読取り consumer 6 件を監査し、3件 resolver 化済み・2件歴史錨定維持・1件は別チケット休眠中と確定した (docsのみ、branch worktree-dev-wave-t1214-floor-protocol-resolver-audit、段2 codex plan + 段3敵対相談2レンズ、計7件real所見を反映)"
---

## 本文

- **command 引数の前提が段1 brief 前の実測で覆った。** 引数は「5件確認済み・6件目を grep で
  確定」としていたが、実測すると 6件中3件は既に別 wave (2026-08-16 の D460、2026-08-17 の
  worklog entry636) で resolver 化済みだった。DW-S01 の「brief 前に承認済み裁定と引数の前提を
  実測する」指示どおりに動いて捕まえた。
- **codex 工数**: 段2 プラン (read-only, reasoning=max) 1本、段3 敵対相談 (sol/luna,
  reasoning=max) 2本。全3本 rc=0、`check_codex_output.py` OK。
- **段3 の2レンズはいずれも「実装なし」という結論自体への直接反証は返さなかったが、
  計7件の real 所見を検出した。** 棄却 (refuted) 所見なし — 全件を採用し、3件は
  {{D:floor-protocol-consumer-audit}} の本文・理由・残る限界節へ、2件は次の一手の
  [T-1215]/[T-1216] 更新へ、1件は下記の再起票へ反映した (もう1件は方法論上の精度指摘で
  記録の書き方にだけ反映、carry には現れない)。
- **セッション異常・ユーザー裁定待ちの発生: なし。** 親の provisional 裁定 (P1) は
  段2 プラン + 段3 2レンズの独立検証だけで確定でき、ユーザーへの確認は不要だった。
- **発見: worklog carry から [T-1218] (2026-08-16 origin entry589) が、解決記録なく
  脱落していた。** `docs/worklog.md`・`docs/decisions.md` を独立に grep して脱落を確認した
  (archive には多数残るが現行 carry・decisions のいずれにも存在しない)。下記「新規」で
  旧番号を明記した上で再起票する。

## 次の一手差分

### 完了

- [T-1214] 固定 path を読む consumer 6件を監査した。3件
  (`certified_writer_admission.py`・`s8b_holdout_admission.py._authority()`・
  `tools/pegasus/floor_campaign.sh`) は既に resolver 化済み、2件
  (`s8b_prediction_runner.py`・`s8b_ratified_freeze.py`) は歴史 commit
  (`pre_oracle_head`、seal 時点の HEAD 一致検査で拘束) の証明鎖再検証でありliteral path
  維持が正しい、1件 (`s8b_holdout_freeze.py:1362-1365`) は current literal read だが
  別チケットが発火条件 (承認 artifact・SHA pin・official result の3条件) 不成立で休眠中と
  確認した。resolver 化の追加実装はない。詳細は {{D:floor-protocol-consumer-audit}}。
  remaining: none
  base: 6fc313be7b5edfc07fba91e7353fe0f9accb4dc4efe3229d503a69bb58958910

### 更新

- [T-1216] **P2・裁定パッケージ**: ratified document 内の `floor_protocol.path` dynamic
  pointer が canonical 相対 POSIX path であること以外の namespace 制約を持たず、literal
  `_SELECTOR_PROTOCOL_PATH` (別途 resolver 化監査済み) とは独立でクロスチェックもされない
  ことを file:line 単位で再確認した (`s8b_ratified_freeze.py` の該当箇所、詳細は
  {{D:floor-protocol-consumer-audit}} の「残る限界」節)。pointer を sanctioned namespace へ
  束縛するかを裁定して実装する、という原文の課題設定は変わらない。
  base: 26ff6bcc655778dc1a0073e577e320dfdad5399b1f2fbdbe7bce1b6d5b04c085

- [T-1215] **P2・新規 (継続)**: `source_digest._sanitized_git_env` に加え、
  `s8b_prediction_runner._git_bytes`・`s8b_floor_campaign._pre_oracle_blob`・
  `s8b_ratified_freeze` の Git 読取りでも ambient `GIT_DIR` 等の除去が不統一という、族一般化
  (`DW-G03`) の独立2例目になりうる候補証跡を得た (file:line 詳細は
  {{D:floor-protocol-consumer-audit}} の「残る限界」節)。次に触る wave がこれを2例目として
  認めるか確認し、族一般化の要否を裁定する。
  base: df910b31fcb9ce8a5ec852777ab6c8693cf8b61090834a41c243038c02814381

### 新規

- {{T:floor-protocol-authority-open-questions}} **P1・ユーザー裁定待ち** (旧 T-1218、
  origin entry589・2026-08-16、worklog carry から記録なく脱落していたのを2026-08-20に発見・
  同一内容で再起票): 案3の射程 (pin を進めれば新しい組で測り直せるか)、「環境契約1世代につき
  床値1件」の妥当性、ratified pointer の束縛 (上記 [T-1216] と論点が重なる可能性あり、次に
  触る wave で整理すること)、versioned artifact を `FROZEN_MANIFEST` へ載せるか、run 層の
  測り直し (旧 T-1140 問1) との関係。裁定パッケージは
  `output/insights/2026-08-16_floor-reseal-authority/README.md` の「残る限界」節。
