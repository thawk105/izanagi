---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-22
wave: dev-wave-t1462-t1464-checkpoint-integrity
seq: 1
---

## {{D:t1462-project-whiteboard-value-domains}}. project_whiteboard()の値域検査はD607と同じ共有validatorで閉じる

**決定:** `orchestrator/campaign/p3_s4_loop.py`の`project_whiteboard()`に、`state_from_dict`/
`layer3_report.build_report`が既に使う共有validator `assert_whiteboard_value_domains()`を
そのまま呼ぶ形で値域検査を追加した。`WhiteboardEntry`構築・`state.whiteboard.append()`より
前に検査し、新規例外クラスは作らず既存`ValueError`をそのまま伝播させる。

**理由:**
- D607は`state_from_dict`と`layer3_report`独立readerの2境界を共有validatorで閉じたが、
  producer側 (in-memory射影経路、`project_whiteboard()`) を明示的にscope外とし独立の
  ユーザー裁定を要すると記していた。本決定はその残余を閉じる直接の続きである。
- 敵対相談・敵対レビューが独立に検証した結果、この新設gateが実際に無効値を止めるのは
  core/sort driverのhuman-supervised経路 (`load_proposal_file()`) に限られると判明した
  (trigger driverは`_assert_trigger_proposal_contract()`で、8c自動経路は`parse_planner()`で
  それぞれ別の防壁が先に発火するため)。それでも3 driver共有の単一関数を直す設計は
  defense-in-depthとして妥当であり、個別driverへ検査を複製する案より変更面が小さい。
- 変異事前登録 (MUT-1、validator呼出しをbypassする変異) の本走で baseline PASSED
  (120件緑)・MUT-1 KILLED (期待node3件と完全一致、他への副作用なし) を実測確認した。

**却下した選択肢:**
- 3 driverの`load_proposal_file()`各々に検査を置く案 (adjudication package §1択a) —
  同じ検査ロジックが3箇所に分散し、D607が確立したDRYな設計と非整合。

## {{D:t1464-redaction-mechanism-deviation}}. checkpoint起源未信頼値のredactionはrepr()でなく制御文字除去+length-capにする

**決定:** `_redacted_transport_error()`の拡張で、未信頼値を無条件`repr()`する案 (command引数の
原文が示す「length-cap付きrepr」) は採用せず、制御文字・Unicode行/段落区切り文字の除去と
500文字capのみを実装した。

**理由:**
- 段2プランと段3敵対相談 (両レンズ独立) が、無条件`repr()`は既存exact-match test 3件
  (`test_p3_autonomous_workload_trial.py`の複数箇所) と衝突し、かつ`:2237`→`:4627`の
  二重処理経路で非冪等になることを実測で確認した。
- 制御文字除去+length-capは既存exact-match testを壊さず (短い定型メッセージには影響しない)、
  かつ冪等である。目的 (未信頼値の運搬量上限化・保存形式衛生化) は`repr()`案と同値である。
- 敵対レビューが独立に指摘した限界: 制御文字除去+length-capは規律6が理想とする
  「prompt-injection遮断」までは達成しない (通常ASCII文字だけの注入文言は素通しする)。
  達成できるのは保存形式の構造衛生 (ログ行分割・端末制御・JSON破壊の防止) と運搬量の上限化
  であり、この区別を worklog に正直に記録する。

**却下した選択肢:**
- 無条件`repr()` (command引数原文) — 上記の理由により技術的に不採用。
- 診断側 (state_from_dict自身) でredactする案 (adjudication package §4択a) — 既存test
  `test_state_from_dict_rejects_unknown_top_level_field`の期待値変更を要するため不採用
  (adjudication packageの時点で既に不採用と裁定済み)。
