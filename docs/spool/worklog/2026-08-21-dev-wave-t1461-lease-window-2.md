---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t1461-lease-window
seq: 2
title: '受入lease(D239)の排他区間短縮を分析・検討し、D270が既に却下済みの同型設計だと判明したため実装しない (docsのみ、branch worktree-dev-wave-t1461-lease-window)'
---

## 本文

- 依頼: 受入lease (D239) の排他区間 (claim〜land) を縮める設計の分析・検討。実装可否は段4裁定に
  委ねる形で開始した。段2-3の敵対レビューは省略しないという明示指示どおり実施した。
- 段1 brief 執筆時、依頼が引用した動機数値 (受入投入〜land完了7時間中、実テスト8分44秒・残り
  98%超) を裏取りしたところ、引用元とされた `output/insights/2026-08-20_t870-congestion-nproc/
  README.md` に該当する文字列が存在しないことを段3レンズ (luna) が発見し、親が grep で追認した。
  問題自体 (lease順番待ちが実テスト時間を大きく上回る) は別の一次資料
  (`output/insights/2026-08-20_t870-acceptance-lease-timing/README.md`、3件の実landed waveの
  事後解析、lease待ち32〜74分 vs 実テスト207〜283秒) が独立に支持するが、具体的な数値は再確認が
  要る。
- 段2 codex plan (read-only, reasoning=max) は brief のfile:line引用を独立検証し (receipt schema
  は26でなく27 fieldと訂正)、2つの再設計案 (leaseを残し保持区間だけ短縮 / lease撤去しD128+D254
  一般化のみ) を対比し、前者を推奨した。
- 段3 敵対相談2レンズ (正しさ境界=sol、整合性・実効性・scope=luna、いずれもreasoning=max) が
  独立に計15件のreal所見を検出した。luna は特に、D270 (2026-08-10) が「main取り込みを待ち手の
  事前作業にする」設計を既に検討し、飽和下での恒常的な陳腐化 (24分待って15commit遅れ、4回空振り)
  を理由に却下していたことを発見した。親がD270・D432の決定原文を直接照合し、この所見と
  D432の「監査lock待機化はprovenance監査の同時流入を増幅しうる」という既知未解決の残余リスクを
  追認した。
- 段4裁定: 実装しない (`4→7→8→9`)。設計提案として {{D:lease-window-shrink-not-implemented}}
  を記録し、詳細分析は `output/insights/2026-08-21_t1461-lease-window-design/README.md`
  (段1-3の逐語を含む) へ保存した。
- wave開始中、ユーザーから別軸の追加依頼 (自wave起因でないテスト失敗でwaveを失敗させない件) が
  届いた。現物コード調査 (`tools/check_acceptance_reds.py`, `tools/dev_wave_wait.py`) では
  分類ロジック自体は「waveのせいでない赤は通す」設計になっており、過去実在した schema不一致拒否
  バグ (2026-08-17以前) も commit `4906e063` で解消済みと確認した。再発の原因はcheckerの起動
  不安定性か運用徹底不足のいずれかと推定するに留め、本waveへ混ぜず次の一手として登録した。

## 次の一手差分

### 新規

- {{T:acceptance-nonattributable-discipline}} **P1・ユーザー依頼**: 自waveが原因でないテスト
  失敗でwaveを失敗させない件。`tools/check_acceptance_reds.py`/`tools/dev_wave_wait.py`の
  非帰属赤分類ロジック自体は機能する設計 (2026-08-21実測、`tools/dev_wave_land.py:716-786`の
  receipt verifierは`non-attributable`/`flake`いずれの形も正しく受理する) が、ユーザーは
  「何度も言っているのに起きる」と繰り返し訴えている。checker起動自体の安定性
  (probe worktree dispatchのorphan-hold実績が過去handoffにあり) と、「赤が出たら必ずcheckerを
  経由する」運用がdev-wave手順側で徹底されているかを調査すること。正しさゲートの中核のため
  専用のbrief→plan→敵対相談を経ること。
- {{T:lease-window-empirical-restaleness}} **P2・新規**: 「claim前にmerge・受入テストを済ませて
  いたら実際にどれくらいの頻度でmain advanceにより無駄になっていたか」を、既存のland/acceptance
  receiptとworklog着地時刻から事後解析で定量化する (新規production変更ゼロ、
  `output/insights/2026-08-20_t870-acceptance-lease-timing/README.md`と同じ手法)。
  {{D:lease-window-shrink-not-implemented}}が実装を見送った根拠 (D270の陳腐化率が現在の
  並行度15+でどの程度か不明) を埋める。この実測が「陳腐化率は十分低い」と示した場合のみ、
  次の設計waveでD270のsupersedeをユーザーへ諮る。
