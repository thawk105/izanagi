---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-t189-stage2-plan-replayer
seq: 1
title: '[T-1434] T-189 stage2-plan-replayer registration機構を実装した (コード+テスト、branch worktree-dev-wave-t189-stage2-plan-replayer、変異matrix = baseline PASSED・M1-M11 11/11 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- model-routing事前登録の未解決点(5) (stage2/stage5 downstream replayerの実装) のうち、
  stage2-plan-replayerだけをnarrowに実装した。stage5-author-replayerは別waveへ送る
  ({{T:t189-stage5-author-replayer}} 参照)。D603の前例に倣うnarrow化。
- `tools/codex_reasoning_ab.py`に、plan入力hash・固定downstream model/effort pin・
  fix pass上限・acceptance判定条件・出力hashの5点セットをrun-root配下へcreate-onlyで
  freezeし、apparatus (snapshot/config/auth/binary) もhash込みで必須pinする機構を追加した。
  Wave D所有関数 (`_validate_schedule`等) は一切呼ばない・参照しない独立機構とした。
- 段3敵対相談 (2レンズ) が「親自身のbrief記載 (fixed-model起動は生死確認済み) は
  dry_run=True限定の検証で実bwrap経路は未検証」という事実で親の一般化を反証した。
  段5実装子が実際にsmoke gateで`_bwrap_exec_argv`経由のreal codex execを試み、
  実ネットワーク到達不可 (120秒timeout・exit -15) を実測した。親が直接調査し、
  `codex_worker_launch.py` (動作実績あり) との比較から真因を特定: ambient環境の縮小
  (`_clean_environment`のENV_ALLOWLIST) が問題であり、bwrapの有無は本質ではなかった。
  詳細は {{D:stage2-direct-launch-recipe}} 参照。
- 段6敵対レビュー2本が独立に「apparatus pin任意でTOCTOU残存」「非有限timeout許容」
  「認証情報cleanup無し」「変異キル力不足のtest」を収束指摘、NO-GO判定。fix 3巡
  (DW-O16上限) を経て347 passed・0 failedを親が独立実走で確認。詳細は
  {{F:stage2-launch-test-representativeness-gap}} 参照。
- 変異matrix (M1-M11) は親自身が11件の意味的記述からCodex子へspec化させ (機械設定は
  実装面のためCodex role=author契約)、`tools/mutation_harness.py --runner-mode dispatch
  --detached`で実走した。baseline PASSED (347 passed)、M1-M11 **11/11 KILLED**・
  SURVIVED 0・MISMATCH 0。
- acceptance判定条件はtask-specific oracle manifest (§5.3列挙の別項目、scope外) が
  無いため、`task_acceptance_status`を常に`"unbound"`とし、`accepted`相当のboolフィールドを
  一切出さない設計にした ({{D:stage2-unbound-acceptance-status}})。段3・段6のレビューが
  独立に「genericなacceptedフィールドは将来task correctnessの証拠と誤読される」と
  指摘したことを受けた裁定。
- 受入投入は本fragment commit後に行う (記録を後から足すとland rc=23になるため、
  受入より先に記録commitを完了させる契約 — 詳細な経緯は past T-1434 waveの実測に基づく)。

## 次の一手差分

### 更新

- [T-1434] **P1・7論点中 (4)完了・(5)のうちstage2側も完了、stage5側+他4論点は引き続き未着手**:
  `tools/codex_reasoning_ab.py`のmodel軸拡張 (4) はWave A-Dで既完了。今回はさらに
  (5) stage2/stage5 downstream replayer実装のうちstage2側を実装した。stage5側
  ({{T:t189-stage5-author-replayer}})、および (1)power simulation・(2)独立custodian実現方式・
  (3)provider cache制御実測・(6)task catalog実データ+独立分類者確保・(7)price snapshot
  実データ取得の計5論点は引き続き未着手。T-189のrouting_evidence_status
  (preregistration §12.1) はこれらが埋まるまでinconclusiveで確定する。
  base: 03ecf05a476c7101c19522226cf1771d84ab0b066757ecc5e95bd266ac5a4300

### 新規

- {{T:t189-stage5-author-replayer}} **P2・T-189設計 §5.3参照**: stage5-author-replayer
  (固定plan入力hash、author出力の適用先、固定downstream model/effort pin、receipt検証手順、
  fix pass上限、acceptance判定条件、出力hashの登録機構) を実装する。stage2-plan-replayer
  ({{D:stage2-direct-launch-recipe}}の起動recipeを再利用可) との共通harness再利用は妨げないが、
  入出力契約とdownstream model/effort pinはstage毎に別々に固定する
  (preregistration §5.3の既定)。
