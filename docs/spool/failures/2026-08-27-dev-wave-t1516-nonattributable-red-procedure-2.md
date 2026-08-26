---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1516-nonattributable-red-procedure
seq: 2
---

## 新規

### {{F:doc-obligation-guard-is-bytes-only}}. exact pin された手順書の節は、揃えて書き換えれば機械を素通りする [恒真ゲート] [テスト代表性]

- 事象: `DW-O18` の本文から義務の 1 文を削る変異を回したところ **SURVIVED** した。
  焦点走の `orchestrator/tests/test_check_docs.py` は緑のままだった。
  節全文が exact pin されているので当然赤になると想定していたが、想定が誤りだった。
- 根本原因: 実 repo の本文を exact pin と照合する唯一の test
  (`test_normative_exact_section_pins_accept_real_repo`) が `IZANAGI_GROWTH_HOLD_V1`
  (`hold_axis: docs_bytes`、解除条件はユーザーの明示コマンドのみ、2026-08-12 rulings 第 3 束) で
  既定スイートから外れている。したがって本文側の変異を捕まえる実効 gate は
  test file ではなく `python3 tools/check_docs.py` の直接実行だけである。
  さらに、本文・checker literal・合成 literal・byte 断定を**同じ変更単位で揃えて**書き換えると、
  この直接実行も通る。守られているのは義務の意味ではなく bytes の一致だけである。
- 恒久対応: {{D:nonattributable-red-does-not-stop-the-wave}} の「この保証が届く範囲」節に、
  機械が守るのは bytes だけであること、意味の防壁は敵対レビューが担うことを明記した。
  変異の登録では、意味の防壁の証拠として kill 数を数えない (`DW-M08` の別枠記録)。
- 再発検知: 手順書の節を exact pin する wave は、変異が SURVIVED したときに
  「pin があるから守られている」と結論せず、`DW-M02` に従って実効 gate へ再照準する。
  本 wave では親が `DW-O19` の一時変異で `python3 tools/check_docs.py` を直接測り、
  rc=1・finding 1 件ちょうどを確認した。

### {{F:review-prompt-pointed-at-moved-head}}. レビュー子へ渡した旧 revision 指定が、自分の commit で新本文を指していた [手順漏れ]

- 事象: 段 6 の敵対レビュー prompt に「旧本文は `git show HEAD~1:...` で読める」と書いたが、
  投入時点では統合 commit を 1 つ挟んでいたため `HEAD~1` は既に新本文だった。
  子が自力で `HEAD~2` を使って照合したので成果は失われていない。
- 根本原因: prompt を書いた時点と投入した時点で HEAD が動いていた。相対指定は動く。
- 恒久対応: 子へ旧状態を参照させるときは相対指定 (`HEAD~n`) を使わず、
  wave 開始時の base commit の SHA を絶対に書く。本 wave の段 6 焦点再レビューでは
  `git show dd6621397:...` と固定 SHA で渡し直した。
- 再発検知: prompt に `HEAD~` が現れたら、投入直前に指す先を実測する。
