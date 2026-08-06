---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-t454-testification
seq: 1
title: [T-454] テスト化 pass は変異 kill 判定の 7 vector を固定しただけの部分実施 — 予算回収は 0 bytes で、需要 1,356 に対し不足 1,136 と実測した (テストのみ、受入 6781 passed / 20 skipped、変異 16/16 一致、branch worktree-dev-wave-t454-testification)
---

## 本文

- **実装差分は `orchestrator/tests/test_mutation_harness.py` の 3 node (parametrize 4 case 込みで
  実 7 vector)・78 行だけ**である。commit は `a8a055a2` / `198b246d` / `b3dc8deb` の 3 本と
  取り込み merge 1 本。**production、`docs/dev-wave/**`、受理集合はいずれも不変。**
- **`docs/dev-wave/**` の回収実績は 0 bytes。** 合計は取り込み前後とも 25,187 / 25,200 のままで、
  **予算問題は解けていない。** 採録待ち 4 件は本 wave 後も本文へ入らない。
- **S1 (子起動 tool) と S2 (harness 生死 probe) は実装しないと裁定した。** 段 3 の 2 レンズが
  独立に同じ blocker へ到達したためである — 新 tool を足しても現行 `DW-O01` が raw 経路を
  正規手順として残すので受理集合は `旧経路 ∪ 新経路` のまま縮まらず、prose を pointer へ畳む
  根拠が立たない。権威経路化には `DW-O01` 本文の置換と長期 interface の新 D が要り、
  **それはユーザーが本 wave で明示的にまとめ裁定へ留保したものそのもの**である。
  加えて既存 `tools/codex_worker_launch.py` (2,591 行) の二重投資であり、D100 / [T-184] と所有が衝突する。
  **「任意 helper として作る」案も採らない** — その場合は機械化・byte 回収を一切主張できない。
- **親の段 1 実測が誤っていた。** 「(217) 候補 (c) は既に機械強制 + テスト済みで純増検出力ゼロ」と
  書いたが、既存テストは**互いに素な集合しか試していない**。段 2 プランと段 3 レンズ A が
  `failed_keys == expected_keys` → `expected_keys <= failed_keys` の弱化変異で反証した。
  誤りの型は「既存実装 + 既存テストがある」を「その性質が固定されている」と読み替えたことで、
  `DW-S01` の「機構名でなく性質で検索する」義務への直接違反である。
- **固定できたのは 7 vector。** 集合関係 3 象限 (期待の真上位集合 / 真部分集合 / 等集合の正例) と、
  node key の正規化衝突 4 種 (basename のみ / 末尾 2 component / 大小文字同一視 /
  class namespace 除去)。**未固定の弱化変異が他に無いことは示していない。**
- **段 3 で 20 件、段 6 で 15 件の所見が出て、すべて real と裁定した (refuted 0)。**
  段 6 は 2 レンズとも NO-GO、焦点再レビューも NO-GO で、fix は 2 巡した。
  段 4 裁定には**訂正 3 件**を入れた — (1) P1 / N1 を二軸へ分解 (「docs を触らない」のは
  ユーザー命令ではなく親の wave-local 選択である)、(2) `DW-G05` +274 bytes の脱落と
  142 bytes の符号誤り (削減ではなく追記)、(3) 「20 件すべて real」だけでは `DW-S04` の
  採否・scope の三軸要求を満たしていなかった点。
- **`DW-M07` の最終 anchor 再検証が実際に効いた。** fix 2 巡目で parametrize case が増えたため、
  MU-4 の実赤集合が初回登録 (1 node) の**真上位集合 (4 node)** になることを走行前に予測できた。
  最終 commit で登録し直して 4 node で確定し、3 件は冗長 gate と明記した (`DW-M03`)。
  この再検証が無ければ MISMATCH で 1 走無駄にしていた。
- **変異は 6 走・16 変異。** 新側 8 KILLED / 旧 HEAD 側 (`616ef5db` の clone) 7 SURVIVED /
  正例 1 KILLED で、**事前登録と実測は 16/16 一致・MISMATCH 0**。erratum なし。
  旧側の collection は 57 node、新側は 64 node で、差は追加した node だけである
  (旧側だけにある node はゼロ)。したがって「旧では生存し、新では対応 node だけが殺した」と
  限定でき、**一般的な検出力を示すものではない。**
- **受入全走は 2 回。** (1) 実装 3 commit + main 取り込み時点の tip `4607d112` で
  6781 passed / 20 skipped / 0 failed (request `892711.nqsv`)、(2) 記録 commit 後の land 直前再走でも
  **6781 passed / 20 skipped / 0 failed** (request `892724.nqsv`、確定値)。
  (2) の走行 tip と land tip の差は本 fragment のこの段落だけで、コード・テストの差はない。
  受入直前に local main `23cc93d6` を取り込んだ (15 commit、競合なし)。
- **byte 会計は 3 回訂正した。** 初稿の見積り → 第 1 次実測 → 焦点再レビューの独立検算で
  B-4 が強調記号 4 bytes 分の数え落としと判明。**既知需要 1,356 bytes に対し、
  回収見込みは A-1 (`DW-O01` pointer 化) −159 + A-2 (`DW-M05` pgrep pointer 化) −48 = −207 のみ**で、
  適用後の余白 220 でも **1,136 bytes 不足**する。回収は既知需要の 15% にしか届かない。
  さらに F112 / F124 の追記文案は未起草・未計測である。
- **L2 削除候補は 3 度目もゼロ**であり、これは「見送り」ではなく**削除不適格**である
  ([T-160] 2026-07-28、[T-291] 2026-08-01 に続く 3 度目)。唯一「発火実績なし」だった
  `DW-O10` も 2026-08-06 の [T-419] で実発火した。
- **削除実施なし・新 D 発効なし・decisions fragment なし。** [T-505] 恒久 3 機構の規範文 (435 bytes)
  と新 D は draft のみを裁定パッケージに置き、発効していない。
- 逐語 (brief / 追補 / plan / 段 3 敵対 2 本 / 段 4 裁定 / 実装報告 / 段 6 レビュー 2 本 /
  fix 2 巡 / 焦点再レビュー / 段 6 fix 裁定 / 裁定パッケージ draft / 変異 spec・台帳 6 本) は
  `output/insights/2026-08-06_t454-testification/` に凍結した。
- **段 8 の改善候補 2 件はいずれも byte 予算に阻まれ、reference を変更しない。**
  (a) `DW-M05` の pgrep 照合規律を「親が張る全ての子 process 待ち手」へ射程拡張する
  (+112 bytes、親自身が本 wave で踏んだ。新規 F を採らず F104 の再発として記録した)、
  (b) `DW-S04` に「一部だけ実装しないと裁定した場合の worklog 射程の書き方」を足す
  (本 wave が現に該当し、全部実装しない場合の規定しか無い)。
  **安全義務を削って捻出せず、予算引き上げも提案しない。** 実体は本エントリと裁定パッケージに残る。

## 次の一手差分

### 更新

- [T-454] **P2・部分実施 → 予算裁定と R1 待ち**: 変異 kill 判定の 7 vector をテストで固定した
  ((217) 候補 (c) は docs 追記不要と確定)。**回収は 0 bytes で予算問題は未解決。**
  裁定パッケージ R1〜R9 と、見送り 11 件・削除不適格 1 件を
  `output/insights/2026-08-06_t454-testification/` に置いた。次は
  (i) R1 (子起動を単一経路にするか、既存 launcher を拡張するか、現状維持か。[T-184] / D100 と調停)、
  (ii) 既知需要 1,356 に対する採録優先順位、の 2 点がユーザー裁定待ちである。
  F112 / F124 の追記文案と `DW-S01` / `DW-S02` の逐語は未起草で、起草しないと入否を判定できない
  base: 90f9727fd5ba603014ce9e4ea5ec21e81bf101f1540123991738864c4a9871b3

### 新規

- {{T:dev-wave-single-launch-route}} **P2・ユーザー裁定待ち**: dev-wave の子起動を
  単一経路へ結線するか。択一は (a) 新 tool を権威化、(b) 既存 `tools/codex_worker_launch.py` を
  拡張して `DW-O01` へ結線 ([T-184] 所有)、(c) 現状の二経路を受容し機械化を主張しない。
  (a)(b) には startup 前死亡の終端化、job-dir の所有・mode・shared FS での flock 権威性、
  論理 condition key と generation nonce の分離、`launch.json` / `.done` の namespace 衝突回避、
  output checker 採用までの E2E 結線が前提になる
- {{T:dev-wave-budget-priority}} **P2・ユーザー裁定待ち**: `docs/dev-wave/**` の
  既知需要 1,356 bytes に対し回収見込みは 207 bytes しかない。何を採録し何を見送るかの
  優先順位を決める。上限は上げない (既裁定)
- {{T:mutation-key-remaining-vectors}} **P3・新規**: 変異 kill 判定で未固定の弱化変異が
  他に無いかを、集合関係と正規化以外の軸 (rc 分類、timeout、artifact error) でも棚卸しする
- {{T:dev-wave-l2-delta-audit}} **P3・新規**: L2 削除候補の棚卸しを全件方式から
  「前回 anchor 以後の delta 監査」へ変える。3 度とも候補ゼロで、変わるのは membership の増減・
  発火実績の増分・機械化の変更だけだと実測した
