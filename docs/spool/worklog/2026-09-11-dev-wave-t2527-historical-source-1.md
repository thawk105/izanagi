---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-11
wave: dev-wave-t2527-historical-source
seq: 1
title: [T-2527] 旧known-axesの歴史閲覧と現行意味照合を限定改訂する
---

## 本文

- D1936項22の限定改訂として実施し、旧artifactのbytesと当時判定を保持した。
- 起動時候補のS1/floor関連file重複は0。最終scopeの20worktree再照合ではT-2515とテスト登録2fileが重なり、本体コードとdirty差分の重複は0だった。未landの他wave差分は採用していない。
- 独立相談2本で、旧識別子改変の拒否と入力SHA検査の検出帰属、oracle adapter経路のmaskを分けた。
- 独立レビュー2本が同じ不要live readを検出。別authorの局所fix後、焦点再レビューは追加must-fixなし。
- 親のconsumer検査で、旧source差拒否を期待する既存oracle testが1件赤になった。D1936に反するその期待だけを改め、generator改竄・pin・floor/budget・sentinelのexact検査を保持した。
- author/fix計3走のテストはqstat preflightで子未起動。親が実走し、子の未実走を緑に数えなかった。
- 変異は8/8 KILLED・期待node完全集合一致。oracle/generatorの2件は最終可否反転でなく診断感度として分けた。
- 診断初回は検出できたが共有木postcheckでrc125。変更元は断定せず、記録を保持して同条件で再走し、外側照合までrc0を確認した。
- 段6全走は23098 passed / 68 skipped、child-green。記録 = `output/insights/2026-09-11/t2527-historical-source/README.md`。
- 工数: Codex 9走（plan1・consult2・author1・review2・fix2・focus1）、全走accepted。改善候補はhandoffへ記録し、本waveでは実装しない。

## 次の一手差分

### 完了

- [T-2527] D1936項22に沿う限定改訂と独立検証を完了。旧bytes・判定を保持し、入力束縛と現行意味照合を維持。
  remaining: none
  base: bddd3eb306c3160d3da7414b17eceb5223946fcefea28011631252c8da4b7641
