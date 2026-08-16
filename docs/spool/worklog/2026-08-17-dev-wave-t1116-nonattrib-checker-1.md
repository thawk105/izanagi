---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t1116-nonattrib-checker
seq: 1
title: 非帰属 checker の修正は checker 層だけで止まり消費層が取り残されていた — 実装せず裁定パッケージへ返す (docs のみ、branch worktree-dev-wave-t1116-nonattrib-checker、実装差分ゼロにより変異 matrix 免除)
---

## 本文

依頼は「commit 8a2b735b が [T-1116] 裁定 (択 2) とユーザー裁定 R2 をどこまで果たしたかを
実測で確定し、残る穴を閉じる」だった。**checker 層だけを果たし、end-to-end では果たしていない。**

- **実測 (本 wave の一次資料)**: 2026-08-15 に旧 checker が `attributable` と判定して受入全走
  1 本を捨てた**実履歴の log** を現 main の checker へかけ直すと `classification=flake`、rc=0 に
  なる。しかし `tools/dev_wave_wait.py` の node exact 検査が全 node に 3 field かつ
  `classification == "non-attributable"` を要求するため、**受領証は発行されない**。
  文字列 `flake` の出現数は待ち手・land とその test 4 file すべてで 0。
  8a2b735b が触ったのは checker とその test の 2 file だけだった。
  → **ユーザー裁定 R2 は一度も発効していない。** 8a2b735b の commit body は「既存の呼び手は
  壊れない」を root field と flag だけで確認しており、node 形の検査を見落としていた。
  規律 6 が監査発火条件に挙げる consumer 取り残しの型である。
- **裁定 (親)**: 穴を閉じる = 受理集合を広げることであり、段 3 の独立 2 レンズが**別々の根拠で**
  NO-GO に到達した。実 scope も親見積り (4 file) の倍以上だった。`DW-S04` に従い実装せず、
  4 択の裁定パッケージをユーザーへ返す。**実装差分ゼロ。**
- **新規に判明した重大事実**: [T-1131] は checker だけを tested main へ束縛しており、
  待ち手 (`running bytes == tip blob` のみ) と runner (tip での存在確認のみ) は束縛されていない。
  wave は待ち手か runner を書き換えるだけで実 child rc=1 を child-green として land できる。
  {{D:touch-not-sufficient-for-non-attribution}} と併せて {{T:acceptance-evidence-self-certified}} へ起票した。
- **親自身の誤りを 2 件撤回した**。(a) brief (P2)「残る穴は flake の過剰受理」は向きが逆で、
  正しくは**過少受理**だった (段 2 プランが指摘)。(b)「過去 89 赤のうち接触は 4 件なので R2 の
  救済の 95.5% が残る」は無根拠だった — 分母が旧 checker の分類で wave 単独 rc を 1 件も
  測っていない (段 3 レンズ A が指摘)。支持されるのは上界「最大 4 件にしか作用しない」だけ。
- **peer セッションの誤りを 1 件訂正した**。`/next-tasks` 側が「非帰属経路が実運用で初めて発火
  した」と報告した受領証の分類は `non-attributable` であり、これは 8a2b735b より前から存在した
  分岐である。新 field を持つ受領証は 45 件中 0 件のままだった。
- 段 3 = 2 レンズ、所見 15 件 = real 14 / nit 1 / refuted 0。
- 段 8 = 候補 1 件を採用。「呼び手を確認した」を root field と flag の照合だけで閉じ、入れ子の
  exact 検査を見落として修正が end-to-end で発効しなかった型を
  {{F:consumer-partial-predicate-check}} へ登録した。機械化は本件の受理集合裁定に従属するため、
  暫定の恒久対応は memory `consumer-exact-predicates-must-all-be-checked` を実体とする。
  dev-wave docs は変更していない (独立 2 例が揃っていないため `DW-G03` により一般化しない)。
- 一次資料: `output/insights/2026-08-17_t1116-nonattrib-checker/`
  (`README.md`、`ruling-package.md`、`probe2-receipt.json`、`verbatim/` に brief・段 2・段 3 両
  レンズ・段 4 裁定の全文)。

## 次の一手差分

### 更新

- [T-1116] **P1・ユーザー裁定待ち (実測により前提が変わった)**: 8a2b735b は非帰属 checker の
  checker 層だけを直し、`tools/dev_wave_wait.py` の消費層を取り残していた。したがって
  ユーザー裁定 R2 は一度も発効しておらず、フレーク 1 件で受入全走 1 本が捨てられる構造は
  変わっていない。択 (2) 相当の分類は 8a2b735b より前から live probe として実装済みで、
  registry は不要になっている。残るのは (i) 本項を終端してよいか、(ii) R2 を実効化するか
  (実効化には production / conftest / fixture / plugin 経由の全走限定赤が通る残余の明示受容と、
  待ち手・outer receipt schema・land・3 test file・runbook / D371 / D389 の同時改訂が要る) の
  2 点である。4 択の全文は `output/insights/2026-08-17_t1116-nonattrib-checker/ruling-package.md`。
  成果物影響 = 未裁定のままだと受入窓が捨てられ続け、かつ [T-1055] の可否も決まらない。
  base: 3ab8946f7a3888214875b451105624fc91d45b3c483b98ad3a24800ad9b3d316

### 新規

- {{T:acceptance-evidence-self-certified}} **P1・新規・要裁定**: 受入証拠の連鎖は checker 以外
  すべて wave tip の自己証明である。[T-1131] は `tools/check_acceptance_reds.py` だけを
  tested main の blob へ束縛したが、`tools/dev_wave_wait.py` は running bytes と tip blob の
  一致しか検査されず、`tools/run_tests.py` は tip での存在しか検査されない。したがって wave は
  待ち手か runner を書き換えるだけで、実 child rc=1 を `child_rc=0 / verdict=child-green` として
  land できる。**[T-1131] が塞いだ穴と同型が隣接 2 層で開いたままである。**
  択は (a) 待ち手と runner も main 側 blob と照合する / (b) tested main 固定の外側 launcher を
  設ける / (c) 現状維持。親の推奨は (a) — 代償は [T-1131] で既に受容済みの型である。
  成果物影響 = 未対処だと acceptance receipt が wave tip の自己証明になり、実際は赤でも
  child-green として台帳に残り、certified 成果物の land 根拠が失われる。
- {{T:waiter-rc-value-pin}} **P2・新規**: `tools/dev_wave_wait.py` の受領証 node 検査は
  `non-attributable` の `rerun_rc` について型しか見ないため、構成上必ず 1 になるはずの値が
  0 / 2 / -1 でも通る。純粋な縮小で安全だが、{{T:acceptance-evidence-self-certified}} が
  開いている間は防御深度に留まるので同一 wave で直すのが安い。
  成果物影響 = 単独では受理集合の穴が 1 つ残るだけで、成果物の値は変わらない。
