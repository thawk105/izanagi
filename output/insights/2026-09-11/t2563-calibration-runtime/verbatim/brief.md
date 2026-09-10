# T-2563 段1 brief

- 研究前進: 認定較正を供給するjobの待ちを短縮し、8b/層3の較正取得費用を下げる。完了は同条件の全体所要と処理回数で短縮を示す最小差分、または効果未証明なら差分を残さない報告。
- 正本: D1936項38、archive worklog-phase3-0910-1417のT-2563、certify_calibration.sh、calibration_v1.json、既存job記録。
- 今回ユーザー裁定: 要求時間増加を既定解とする方針を変更。要求時間・各timeout・標本数は固定。
- 不変: 規律2、trace/perf分離、単独測定区間、cold/fresh build契約、pristine検証、各標本の取得とcorrectness/condition gate。
- scope: 認定jobの実時間・待ち・処理回数分析と、既存契約内の最小処理削減または並行化。T-2564・本走範囲拡大・汎用cache/scheduler/計測基盤・仮想防壁は除外。
- 実測環境: Pegasus計算ノード、既存sanctioned submit経路。テストはrun_tests.py経由、正式受入は共通acceptance。
- 既存成功例989271.nqsv: mocc rr50 t48 bnode020、scheduler Elapse302s。started_epoch1788976387からcompleted_epoch1788976685までは298s。queue作成から開始12s。
- ログ内epoch: static6392→pre6422は30s (build・コピー・検証・toolchain・probeを含む)。pre6422→post6685は263s (cooldown・較正・publishを含む)。各値の178897接頭を省略。
- 保存fileのmtimeは取り込み時刻で揃っており工程計時に使えない。上限式6610/6910/7870は実所要と無関係。
- 既存標本: sweep3点×3rep、noise10rep、scale not-measured。walltime_sは各点代表値で全rep合計とみなさない。
- 処理回数: gflags configure/build/install各1、glog各1、CCBench configure/build各1、3依存copy各1・pristine検証1。gflagsは同じ3ソースをthreads/nothreadsの2targetでcompile。
- (P1) 親暫定: 未使用gflags_nothreadsの生成停止は小さい候補だが、全体への効果は未証明。並行copyの費用はprepare30s内の一部であり85sのlogin→NFS実測をcompute→/scrへ流用しない。
- (P2) 親暫定: 最大時間式の整合と7200s維持は同時に成立しない可能性がある。必要上限>枠なら正しさ検査を緩めず、不整合を隠さず説明する。
- 成果物: 短いanalysis/裁定/同条件効果表、採用時だけjobと必要consumer testの最小差分、phase完了記録、spool記録。改善候補はhandoffにのみ記録。
- 分割: plan read-only→異なる2レンズconsult→親裁定→採用候補だけ別worktreeのD95 author。親は実装・実行scriptを書かない。
- 所有: T-2515 recoveryはland済み。旧branch/merge途中worktreeは非接触。今回wave専用worktreeをmain d85bbb211から作成中。
- DW-O08: proof/receipt境界に関係するためsubmodule初期化を実施してからplanへ。既存凍結成果物bytesは変更しない。新規gateはscope外。
- DW-G05: 検証済み較正の値・受理集合を変えず、生成待ち時間だけが変わることを確認する。
