---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-t1462-t1464-checkpoint-integrity
seq: 1
title: '[T-1462]+[T-1464] checkpoint値チャネルの整合性を修正した (コード+テスト、branch worktree-dev-wave-t1462-t1464-checkpoint-integrity、変異matrix = baseline PASSED・MUT-1 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

裁定根拠は2026-08-21ユーザー裁定「推奨通りで」、一次資料は
`output/insights/2026-08-04_t287-checkpoint-values/adjudication-package.md` §1・§4。

- [T-1462] (§1択b): `orchestrator/campaign/p3_s4_loop.py` の `project_whiteboard()` に、
  `state_from_dict`/`layer3_report.build_report`が既に使う共有validator
  `assert_whiteboard_value_domains()`をそのまま呼ぶ形で値域検査を追加した ({{D:t1462-project-whiteboard-value-domains}})。
  D607がproducer側 (in-memory射影経路) を明示的にscope外とした残余を閉じる続き。
  3 driver共有の単一関数のため12呼出し全てを一度に閉じる。docstring5箇所を実態に合わせて更新。
- [T-1464] (§4択c): `_redacted_transport_error()`の早期return (transport_receipt is None時に
  secret置換より前に即returnしていた) を除去し、secret置換の後に制御文字除去+500文字cap
  (truncation marker付き) を両分岐共通で適用した ({{D:t1464-redaction-mechanism-deviation}})。
  9呼出し全てがこの一箇所の拡張で保護される。

command引数原文の「length-cap付きrepr」からの逸脱: 段2プラン・段3敵対相談 (両レンズ独立) が、
無条件`repr()`は既存exact-match test 3件と衝突し`:2237`→`:4627`の二重処理経路で非冪等になると
実測確認したため、制御文字除去+length-capへ変更した。詳細と却下理由は
{{D:t1464-redaction-mechanism-deviation}}参照。目的 (未信頼値の運搬量上限化・保存形式衛生化)
は原案と同値だが、規律6が理想とする「prompt-injection遮断」までは達成しないと敵対レビューが
指摘した — この区別を正直に記録する (達成できるのは保存形式の構造衛生と運搬量の上限化)。

段3敵対相談2レンズが、trigger driver (`_assert_trigger_proposal_contract()`) と8c自動経路
(`parse_planner()`) は既存の別防壁で既に無効値を止めており、T-1462の新設gateが実際に
無効値を止めるのはcore/sort driverのhuman-supervised経路に限ることを実測で検出した。

段6敵対レビュー2本がreal所見2件を検出 (docstring1箇所の記述残存、T-1464新設テストの
境界値(500/501文字)不足) し、fix1巡で両方closedにした。fix子の投入前に統合snapshot patchを
job dirへ退避した (DW-S06-B)。

段5実装子・段6レビュー2本・fix1本の計4回、`evidence_status=invalid`/`launcher_rc=1`で
`-o`成果物が書かれない事象に当たった。`codex_exit_code=0`で内容は健全
(`check_codex_output.py` rc=0) であり、`attempt-0001.output.md`から復旧して採用した。
原因はF217 (web_search重複key) でもF223 (非NFC行) でもない新しい変種と判明し
{{F:codex-jsonl-backslash-unterminated-string}}として登録した。

実装commit (`b66cca12`) は AI-Agent trailer 3行 (researcher/reviewer/author、いずれも
`product=codex; model=gpt-5.6-luna; reasoning=max`) + manager (`product=claude;
model=claude-sonnet-5; reasoning=default`) で記録した。

親の焦点走 (`test_p3_s4_loop.py`+`test_p3_autonomous_workload_trial.py`+
`test_p3_s4_loop_trigger_gating.py`、459件) は緑 (52.68秒、失敗0件)。変異事前登録MUT-1
(project_whiteboard内のvalidator呼出しbypass) はbaseline PASSED (120件緑)・MUT-1 KILLED
(期待node3件 `test_project_whiteboard_rejects_invalid_{direction,magnitude,result}` と
完全一致、他への副作用なし)。

Pegasus計算ノードのqueue混雑 (待ち70件超まで悪化した時間帯があった) により、親の焦点走・
変異matrix・provenance監査のdispatchが複数回queue-wait-timeoutで失敗し、都度
`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE`で猶予を延ばして再試行した (最終的に
queue改善後に成功)。混雑対応中に「lease coordination compute saturation」
セッションから2点の重要な共有を受けた: (1) 自分のPBS job (qdel実施状況) の実態確認要請へ
receipt.json全件を突き合わせて回答し、孤児0件・並行dispatch2本を確認して以後逐次化した、
(2) `dev_wave_wait.py acceptance`の`preclaim-history-provenance`段が固定300秒timeoutで
`check_ai_provenance.py`のPBS jobをqdelせず孤児化するバグが見つかり、修正が入るまで
**受入の新規投入を一時停止**するよう要請された。本waveはまだ受入段階に達していなかったため
直接の影響はないが、段9のland前に解除確認が必須。プレーンな`run_tests.py`直接呼出しは
この制約の対象外。

## 次の一手差分

### 完了

- [T-1462] project_whiteboard()にvalidatorを追加し値域検査を閉じた。
  remaining: none
  base: 99ebd1fa142d971b9be33a4b929c821b8e61eee93617622cd96bdaf421874e19
- [T-1464] _redacted_transport_error()を早期return除去+制御文字除去+length-capへ拡張した。
  remaining: none
  base: f2a7a02d207327c732b8f2d97e75005533415259f403c9d021940a558caca544
