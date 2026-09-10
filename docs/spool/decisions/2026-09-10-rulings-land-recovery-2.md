---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-10
wave: rulings-land-recovery
seq: 2
---

## {{D:rulings-land-terminal}}. rulings の裁定記録は受入・land・foldとcanonical反映までを終端とする

**決定 (ユーザーの復旧・自己改善依頼):** rulingsの記録は専用branchのfragmentとして作り、
既存の受入・local main land・同lock内のfoldを完了してから完了報告する。
mainへの直接commitで代用せず、landの成功応答とcanonicalへの反映を実体で確かめる。
read-onlyの索引・説明だけの場合は従来どおり編集・commit・受入を行わない。

**理由:** {{F:rulings-commit-before-land}} で、裁定記録をmainへ置くだけでは他waveが読む
正本へ届かないことが実際に起きた。必要な仕組みは既存のland operationにある。
短い導線を共通commandの冒頭へ統合すれば、ClaudeとCodexの両入口が継承する。

**却下した選択肢:**
- spoolへのcommitで終了し次のwaveにfoldを委ねる — 共有mainに未完の作業を残す。
- canonicalを手で追記する、wave側でfoldする、履歴を巻き戻す — 既存のlock・採番・履歴境界を破る。
- 新しいhookや検査基盤を作る — 既存経路の未使用が原因であり、新機構は不要。
- docs-onlyやskill記録を着地手順の例外にする — 今回の誤った読みを残す。

**修正範囲:** `.claude/commands/rulings.md` の冒頭と意味を保った短縮だけ。
byte予算は変更せず、Codex側Skillのdispatchも変更しない。
