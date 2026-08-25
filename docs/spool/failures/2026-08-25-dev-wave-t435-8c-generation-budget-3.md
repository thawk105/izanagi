---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t435-8c-generation-budget
seq: 3
---

## 再発

### F39

- **再発: 2026-08-25** — 8c 事前登録の証拠契約を改訂する wave で、親の pin 閉包が
  `consumer_requirement.proof` の逐語だけを検索し、**契約ファイル全体の意味 hash を literal で
  pin するテスト 4 nodeid** を落とした
  (`orchestrator/tests/test_s8c_preregistration_core.py` の
  `test_current_evidence_contract_hash_is_frozen` と
  `test_evidence_contract_hash_accepts_non_path_controls` の 3 parametrize)。
  後者の 3 件は契約ファイルを読んで加工した値を pin するため、契約の path でも proof の語でも
  検索に掛からない。2026-08-17 の再発と同じ subsystem・同じ機序 (key が派生 digest なので
  path 検索に原理的に掛からない) の逐語再現である。検出は段 3 の敵対レンズで、実害なし
  (実装前・commit 0 byte)。恒久対応は F39 から変更しない。運用として、
  凍結成果物の**ファイル全体の hash を pin するテスト**も pin 閉包の既定対象に含める。

### F154

- **再発: 2026-08-25** — 4 例目、新しい所在の変種。親は 8c 事前登録の凍結手続きを §6 本文と
  判定器のコードまで実測し、世代記録の `ruling_reference` が「記録を導入する commit 時点の
  `docs/decisions.md` に見出しが実在すること」を要求する制約
  (`orchestrator/campaign/s8c_preregistration.py` の `_assert_rulings_exist`) を正確に測った。
  しかし**その制約を決めた D439 を引かなかった**ため、D439 が「却下した選択肢」として明記して
  いる回避策 (世代記録の裁定参照に、当該改訂の内容を承認していない決定を代用する) を、
  暫定裁定として据えた。従来の再発は裁定が archive にしか無い型だったが、本件の裁定は
  `docs/decisions.md` の canonical に実在し、機構名 (「世代記録」「裁定参照」) で意味検索すれば
  出た。**コードで制約の振る舞いを測っても、その制約が却下済みとする回避策は見えない。**
  検出は段 3 の敵対レンズ A で、消費は codex 子 3 本 (段 2 プラン 1 + 段 3 敵対 2)。
  実害なし (実装前に wave の形を D439 形 2 へ変更)。恒久対応は F154 から変更しない。運用として、
  brief 前の機構名検索の対象へ、**コードで実測した制約の由来決定**を加える。
