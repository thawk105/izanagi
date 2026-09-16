---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t1232-rootless-failure-report
seq: 3
---

## 再発

### F29

- **再発: 2026-09-16** — [T-1232] wave。段 1 brief で 2 つの前提を、命題と違う対象から導いた。
  (1) producer が failure-only report を実際に publish する例として
  `orchestrator/tests/test_p3_autonomous_workload_trial.py` の
  `test_registered_formal_noncertifying_build_crash_is_indeterminate` を挙げたが、このテストは
  `assert_autonomous_trial_completeness`・`assert_autonomous_trial_execution_digest_chain`・
  `layer3_report.render` (admitted を返す fake)・`assert_campaign_layer3_chain` をすべて monkeypatch で
  無効化しており、**実出力の証人にならなかった**。(2)「root を省くと失われるのは path identity 束縛だけ」と
  結論したが、読んだのは `assert_campaign_layer3_chain` の失敗 cell 区間だけで、その手前で走る
  `verify_s8c_cross_binding` の build population 要件を含めていなかった。実際には campaign identity を持つ
  失敗 cell は **root を与えても** cross-binding が落とす。いずれも読解自体は正確で、
  **読解対象が命題と違っていた。** 検出は段 2 の codex plan で、段 3 の敵対レンズ 2 本も独立に同じ 2 点を
  指摘し、親が現物で裏取りして段 4 裁定で訂正した。brief は実測 1〜6 を「source 読解であって実走ではない」と
  明記していたが、**テストを証拠に挙げるときにその検証機構が無効化されていないかを確かめる手順**は
  書いていなかった。恒久対応は既存のまま (再発検知行どおりレンズに攻めさせる経路が機能した)。
  逐語は `output/insights/2026-09-16/t1232-rootless-failure-report/verbatim/s4-ruling.md` §2。

### F30

- **再発: 2026-09-16** — [T-1232] wave。実装子が新しい test helper `_failure_only_producer` の中で、
  coder build authority の低レベル発行 helper `add_coder_build_authority_argument` を直接呼んだ。
  `orchestrator/tests/test_p3_build_authority_cli.py` の
  `test_tracked_python_coder_authority_ast_closure_is_exact` は、この helper の呼び出し箇所を
  **tracked な Python 全体の AST で数え、許可台帳 `_LOW_LEVEL_ISSUER_ALLOWLIST` と完全一致を要求する**。
  台帳に無い呼び出し箇所が 1 つ増えたので、**受入全走で初めて赤になった** (1 failed / 24109 passed)。
  **pin の key は file path ではなく呼び先の helper 名であり、しかも走査範囲は repo 全体である。**
  段 1 の pin 閉包は編集面の path (`autonomous_trial_completeness.py`) で引いたので hit しなかった。
  段 6 の焦点走は `DW-O26` どおり変更した production symbol を参照する consumer test を集めたが、
  この検査は本 wave の symbol を参照せず**呼び先 helper 名で全域を走査する**ので consumer 集合に入らなかった。
  段 6 レビュー 2 本も実装子の報告も拾わなかった。今回の新しい角度は、**wave が変える path や symbol ではなく、
  wave が新たに呼ぶ callee の名前を key にする全数 pin** であること。直し方は許可台帳へ行を足さず
  (authority 発行箇所の許可集合を増やさない)、既に台帳に載っている
  `test_p3_autonomous_workload_trial._coder_authority()` の流用へ置き換えた。恒久対応は既存のまま
  (`DW-O09` の「path 以外を key にする pin も key 側で検索」に、新たに足した呼び出しの callee 名も含まれる)。
  逐語は `output/insights/2026-09-16/t1232-rootless-failure-report/README.md` §9。
