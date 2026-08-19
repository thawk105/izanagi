[severity: nit] [tools/check_ai_provenance.py:1119] docstring が「導入 commit より前は遡及しない」と記述しており、authoritative の side-branch 適用述語と不一致。→ epoch の祖先は除外し、祖先でない HEAD 到達 commit には適用する旨へ更新する。

[severity: nit] [docs/ai-provenance.md:42] 「導入 commit より後」の表現が、pre-epoch side branch も監査対象となる契約と不一致。→ 統合述語の文言へ統一する。

[severity: nit] [orchestrator/tests/test_check_ai_provenance.py:984] drift テストの偽 audit が findings 空で、HEAD drift 時に rc=2 が rc=1・findings 出力より優先される変異を検出できない。→ synthetic finding を返し、出力されないことも assert する。

`_policy_commit()` の旧・新コマンド結果はともに `50c1ef4e5078...`。述語、ledger 配線、HEAD pin、shallow/graft/replace 検出に機能上の所見はありません。テストは依頼どおり未実行。

## 総括

上記 3 点以外は所見ありません。