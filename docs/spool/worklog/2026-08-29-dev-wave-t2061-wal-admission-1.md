---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: dev-wave-t2061-wal-admission
seq: 1
title: [T-2061] 保存済み実行記録の判定と受領証を共通 admission helper へ通した (code + tests + insight、branch worktree-dev-wave-t2061-wal-admission)
---

## 本文

- D1246 の実装。実行中の経路は規律 2 を守るが、**保存済み記録を後から読む経路に判定と受領証の
  束縛が無かった**。`artifact_admission.py` に小さい共通 helper を 1 つ置き、実在する
  certified consumer だけをそこへ通した。新 module・新台帳・新署名主体・新 receipt schema は
  作っていない。既存の受領証 validator を再利用した。
- **閉包は 21 module / 30 site。** ユーザー指示のとおり識別子 key と編集面 path の両軸で探した。
  共通入口経由が 16 module / 22 site、lock だけ読む経路が 3 site、
  **識別子検索では出ず編集面 path 検索でだけ出た経路が 4 site**
  (S6/S8A の再開判定、backoff_repro、A-2 の cell 射影)。
  さらに段 6 の敵対レビューが 30 番目 (`p3_s4_loop._resolve_duplicate()`) を見つけた。
  親の段 4 裁定は 29 site で閉じたつもりだったが不足しており、段 3 の 2 本のレンズでも落ちた。
- **述語は段 2 案から 5 つ削った。** `commits > 0`、`aborts >= 0`、commit witness の 3 項目、
  `workload` の exact key 集合、`verify_configs` の一致。段 3 の 2 本が一致して過剰と判定した。
  特に batch 件数 0 の要求は、CCBench が batch commit を独立集計して性能値にも加えるため、
  将来正当に認証できるようになったとき正しい成果物を拒否する。実行側の既存 gate は不変。
- 段 3 レンズ A の (P2) 反証を採用した。**行単位の二重検査は中央関門の後では恒真**なので実装せず、
  代わりに中央関門より前に動く再開経路を結線した。
- 段 6 レビュー A の must-fix 1 件は**不採用**。A-2 の `_classify_verify_repetition()` の
  commit 件数・batch 件数制約は基準 commit に既にあり本 wave の差分ではない。外すと A-2 の
  受理集合が広がる。別裁定の候補として insight に残した。
- **過剰拒否を 20 件出して直した。** helper を「COMMIT が 1 件ある」だけで起動していたため、
  認証対象として適格でない window・旧形式・既に別の理由で拒否済みの行にまで関門が掛かっていた。
  受理集合を縮める wave でも、承認外の方向へ縮めてはならない。
- 変異は 15 件を事前登録した (負例 10 / **過剰拒否を殺す正例 4** / 再開経路 1)。
- **変異走行は未実施。** 計算ノードの待ち上限が固定 900 秒で、変異 harness は dispatch 時に
  `run_tests.py` を介さず `dispatch_compute.py` を直接呼ぶため上書きの環境変数が届かない。
  混雑下で 4 回とも子が起動せず rc=16 で止まった。ローカル走行も harness が
  「dispatch していないこと」を要求するため選べない。
- 非帰属の赤を 3 種計測した。未 commit の enforcement closure member による drift、
  `/tmp/.git` の点滅生成、一時領域を `.git` 祖先のある場所に置いたこと。
- 正式 qsub、正式測定、push、次 wave 起動は行っていない。
- 一次資料は `output/insights/2026-08-29_t2061-persisted-wal-admission/`。

## 次の一手差分

### 更新

- [T-2061] **P1・実装済み・変異走行と受入が未了**:
  helper と 30 site の結線は landed。変異 15 件の事前登録も済み。
  計算ノードの混雑で変異走行と受入全走が未実施。混雑が引いたときに走らせる。
  base: 4d402dfd447462d5715db50db9d796858fff872781400fe219c56859b3cae1fc
