---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t989-realrepo-worker-diag
seq: 1
title: '[T-989] worker_id/nodeid/start/finish 一時診断を実装・検証しrevertした (コード実装は変異matrix 4/4 KILLED で完走、測定基盤のdispatch env allowlistが閉じた集合でありworker spanが因果的指標でもないため、branch worktree-dev-wave-t989-realrepo-worker-diag)'
---

## 本文

- [T-989] real-repo グループ部分除外 NO-GO (2026-08-19、worklog entry 686) の
  insight package が示した次の一手 (worker_id/nodeid/start/finish の一時診断) を、
  ユーザーが留保 (投資対効果不明) を読んだ上で明示的に指示した。
- 段2 codex plan → 段3 敵対相談2レンズ (正しさ境界・実効性/一般化) → 段4 親裁定
  → 段5 実装 → 段6 敵対レビュー2レンズ (mutation-kill力不足7件を独立発見) →
  fix2回 → 焦点再レビュー → 変異matrix (baseline PASSED 15/15、登録4件全て
  KILLED、期待node完全一致、SURVIVED 0・MISMATCH 0) の全段を完走した。統合commit
  `0296a5f92373f76f510a3ccb7adea622a1647cb0`。
- 段6測定手順どおり全テストスイート実測 (`tools/run_tests.py --force-dispatch`、
  13,881 items) を実行したが、診断出力ファイルが作成されなかった。原因は
  `tools/pegasus/dispatch_compute.py` の `"tests"` task env_allowlist (89-103行)
  が閉じた集合であり (D103 決定5)、新規env varがdispatchされるqsub jobへ伝播
  しないため。20以上の並行稼働セッションが共有するdispatchのセキュリティ境界を
  一時診断のためだけに拡張するのは不釣り合いと判断した。
- 段3レンズBが既に「worker span (occupied interval union) は除外時のwall短縮量
  を意味する因果的指標ではない」と指摘しており、測定に成功していてもD358
  (排他機構の変更では受入は速くならない) を覆す根拠にはなり得なかった
  (レンズB提示の決定表: 5行中4行がrevertへ帰着)。
- 二重の理由 (測定基盤の壁・worker spanの非因果性) により、規律5に従い診断
  コードをrevertした (revert commit、amendでtrailer訂正はユーザー明示許可済み)。
  詳細は {{D:t989-worker-span-diagnostic-closed}}。
- **セッション異常: revert commitのtrailerで、実際にはCodex fix子が2回投入して
  ファイル編集したにもかかわらず、親(Claude)自身のrole=manager行だけを書き
  product=codex; role=author行を書き忘れた。** `check_ai_provenance.py`が新規
  違反 (missing-codex-author) として検出。是正方法としてPR-C01型forward
  correctionとknown-violation台帳追記の2案を検討したが、どちらも
  `tools/check_ai_provenance.py`自体へのハードコード追加(小規模dev-wave相当)を
  要し、かつ既存entryは全て2026-08-07の/rulings裁定に遡ることが判明した。
  未push・私用wave branch上のtrailer誤記1件の是正としては著しく不釣り合いと
  判断し、ユーザーに確認の上この場に限りamendを許可された (2回目のask)。
  次セッションへの教訓: Codex子にファイル編集をさせた場合、commit文の
  AI-Agent trailerには必ずproduct=codex; role=author行を(親自身のmanager行と
  併記して)含めることを、commit-message作成の最初のチェック項目にする。
- **セッション異常: 段5/段6/段7 revertを通じて、codex完了報告の
  `check_codex_output.py`不採用 (`## 総括`見出し欠落 or 500 bytes下限未満) が
  計4回発生した (段5×1、段6-fix×1、段6-fix2は問題なし、段7-revert×1回目は
  総括はあったが500 bytes未満)。実装自体は毎回正しく、報告のみの軽量再投入
  (max-model-calls低め) で解消した。** 段8自己改善候補: stage=author/fix/focus
  向けpromptに`## 総括`必須+目安bytes数(500以上)を、stage=plan/consultと同様
  テンプレート化して漏れを防ぐべき。
- 実測: `python3 tools/run_tests.py orchestrator/tests/test_real_repo_serialization.py
  -q --force-dispatch` (統合commit時点) = 44 passed, 1 skipped (既知、T-989無関係),
  0 failed。変異matrix: baseline PASSED 15/15、4/4 KILLED。
  `python3 tools/check_ai_provenance.py` = rc=0、新規違反なし (amend後)。
- codex工数: 段2 plan 1本、段3 consult 2本、段5 author 2attempt、段6 review 2本+
  focus 1本+fix 3attempt (2回目のfix2は1attempt)、段7 revert 2attempt、
  計12回のcodex呼び出し。うち4回が報告形式不備での再投入。

## 次の一手差分

### 完了

- [T-989] real-repo グループへの受入 wall 帰属調査 (worker_id/nodeid/start/finish
  一時診断の実装・検証・revert) を完了し、これ以上の再訪を推奨しない。今後
  再訪する場合の前提条件 (dispatch env allowlist 拡張の別途正当化・worker span
  から因果効果を推定する方法論の確立) は insight package に記録した。
  remaining: none
  base: 8e37bef7f01934cffd775b843e2a9fbca30255bfd17f8e01be54b15d45e05658
