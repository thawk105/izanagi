---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t657-stage0-fold
seq: 1
title: T-657 段 0 の R1/R2/R3 を設計正本へ畳み込み機械束縛した — 失効 record は下位 §S2-1.10 への conformance と判明、上位 cancellation を R4 として起票 (コード + docs、変異 7/7 KILLED、branch worktree-dev-wave-t657-stage0-fold)
---

## 本文

- **[T-657] 段 0 の続きを実施した。** worklog 415 のユーザー裁定 3 件 (R1 = (a) / R2 = (b) /
  R3 = 分割) を `docs/calibration-freeze-authority-bundle-design.md` §12.3 から §12.1 へ移し、
  規則本文を §7.5 (R1) / §10.2 (R2) / §10 の段 6 行 (R3) へ畳み込んだ。あわせて畳み込んだ内容を
  機械束縛する検証器と契約テストを実装した。逐語・変異台帳は
  `output/insights/2026-08-11_t657-stage0-fold/`。
- **段 3 の敵対 2 レンズが親の裁定を覆した。** 両レンズが独立に「失効 record の 7 key の中身は
  未裁定であり親が選ぶのは越権」と構成し、一次資料として
  `docs/freeze-permanent-design-s2.md` §S2-1.10 を指した。同節には**既に exact 7 fields の失効
  schema が存在し**、R1 (a) が固定した 4 点 (path 形状・key 数 7・束当たり 0/1 件・UTC 秒 int) は
  すべてその逐語と一致していた。**選択肢 (a) は新 schema の発明ではなく、凍結済み下位正本への
  conformance だった。** 親 brief の provisional (P2) と段 2 プランが組み立てた別案は、
  `FREEZE-AX-TOPOLOGY` と同型の不適合を上位に新設するため撤回した。
  **越権の指摘は正しかったが、結論 (ユーザー裁定が要る) は誤りだった** — 7 key は下位正本から
  導出できる。
- **field の表現は下位の逐語でなく上位層自身の慣習に従う。** `revoked_at` は上位承認 A の
  `approved_at` と同じ exact int の UTC 秒 (下位 §S2-1.1 は文字列と定める)、`revoked_by` は
  A の `approver` と同じ制約。段 6 レンズ B はこの差を「conformance 不成立」と blocker にしたが、
  **上位層内で表現を揃える方が正しい**と裁定し、docs に層差として明記した。
- **段 6 は 3 回続けて「直前の fix 自身が作った抜け道」を検出した。** 設計正本を読む
  `_read_design` の fenced code block 除去に、可視部と検査対象を分離する経路が繰り返し残った。
  (i) wave 前 = 除去が無い、(ii) fix 1 巡目後 = tilde と 4 個以上 backtick、
  (iii) fix 2 巡目後 = backtick info string 内の backtick。**いずれも独立の敵対検証子が
  in-memory probe で「正常受理される」ことを実証した。** 4 巡目で opener / closer 判定を
  1 helper へ統合し、**個別の攻撃例を潰す形をやめて CommonMark の条件をまとめて判定する形**に
  した。5 巡目で各条件へ陰性・陽性 node を対で足した。
- **親が変異の帰属を検算して検出漏れを 1 件見つけた。** 敵対レビュー 4 本と焦点再レビュー 2 本の
  いずれも指摘しなかったが、`DW-M01` の単一理由性を検算する過程で、段 6 照合の第 3 選言
  (実行境界文) を単独で殺せる陰性 node が無いと判明した。既存 node は riders を control 文の
  直後へ置くため control 側が先に変わっていた。fix 4 巡目で閉じた。
- **変異は本走 7/7 KILLED、全件が事前登録と一致** (MISMATCH 0 / SURVIVED 0、baseline 緑、
  固定 commit `fe43b92b` の使い捨て worktree)。期待 node は discovery 走で実測してから確定した。
  **erratum**: `failed_nodes` の全件を検出力の証拠に数えてはならない — M1 は 10 node 中 2 件、
  M7 は 37 node 中 31 件が「拒否理由の文字列だけの赤」である (品質点検 3 巡目が指摘)。
  真の KILL は M1 = 8 node、M7 = 6 node。mutant 単位の 7/7 は維持される。
- **再照準 2 件 (DW-M01)。** M3 は当初 段 6 実行境界比較を対象にしたが control 比較が先に殺して
  生存すると判明し、control 比較へ再照準。M5 初稿 (gate 集合 pin) は独立 hash pin との多重防壁で
  診断差にしかならないため削除し、hash pin 単独の変異へ差し替えた。
- **DW-M08 の新旧両走は実施しない。** 本 wave の変異はすべて本 wave が新設した code の逐語を
  anchor にしており、変更前 HEAD に対応 anchor が無いため比較が構造的に退化する。
- **セッション異常 2 件。** (i) 焦点再レビュー 1 巡目は codex rc=0・内容完全だったが launcher が
  `evidence_status=invalid` で不採用にした (stdout/rollout の evidence 検証)。所見は読めたため
  対応し、新 artifact 名で再走して正規の証拠を取り直した。(ii) 焦点再レビュー 3 巡目の初回は
  **上流分類器が prompt を拒否**して rc=1・出力ゼロになった (既知の失敗様態)。防御目的を
  明確にした prompt へ書き直して再投入し成功した。
- **段 0 の status は `incomplete` のまま維持した** (R2 = (b) の正直な表示)。他者手番 gate 2 件
  (`FREEZE-CONFORMANCE-LITERAL` / `FREEZE-AX-TOPOLOGY`) の owner・status、fixture 10 件、
  row 10 件、裁定 profile 12 件も不変。`required_gates` は 8 → 13 件、blocking gate は 3 → 5 件。

## 次の一手差分

### 完了

- [T-794] R2 = (b) を §10.2 へ畳み込み、gate `CFAB-R2-STAGE0-COMPLETION` を resolved で登録した。
  段 0 の `incomplete` が意図した正直な表示であることを本文に明記した。
  remaining: none
  base: 7cbcd19feba9923e5f55de7a1e5cc627b543e47319c92d7fe1994579c1657bd1

- [T-795] R1 = (a) を §7.5 へ畳み込み、exact 7 key と 4 意味規則を確定した。下位 §S2-1.10 への
  conformance であることが段 3 で判明し、親の別案は撤回した。設計本文と検証器定数の drift を
  行全体で束縛した。
  remaining: none
  base: 4ee96e29e28404d7cc997f1cf749a49d07ad26f7b83c745cefcf7806dc324a76

- [T-796] R3 = 分割を §10 の段 6 行へ畳み込んだ。構造部分 (i)〜(v) を段 0 で固定し、policy 依存
  部分を `CFAB-STAGE6-POLICY-PREDICATE` (unresolved) として残した。parent は「その時点の
  live tip X」に限り世代は A と一致し非 genesis では真に大きい、を §7.2 / §5.1 から導出した。
  remaining: none
  base: 102a3b7af19c12dda6a95dbe9cb34e5d8e1661b3ba94c459144659ecdcd69969

### 更新

- [T-657] **P1・段 0 の R1〜R3 は畳み込み済み。新たに R4 が残った (B 系)**: R1/R2/R3 は
  §12.1 へ移し、規則本文を §7.5 / §10.2 / §10 段 6 行へ畳み込んで機械束縛した。
  段 0 status は `incomplete` のまま (R2 = (b))。他者手番 gate 2 件は不変。
  **残るユーザー裁定は {{T:upper-cancellation-record}} (R4) の 1 件。**
  段 0 を止めているのは 3 軸 = fixture `pending` 5 件 / applicable な `unresolved` 2 件 (S・B) /
  blocking gate 5 件。正本 = `docs/calibration-freeze-authority-bundle-design.md` §12
  base: 19a4d3f6f46a31dceab71f7ac948f0a137fbef12339ed7412643f81eae3f69b8

### 新規

- {{T:upper-cancellation-record}} **P1・ユーザー裁定待ち (R4、B 系)**: 上位 pointer X が fork
  したときの敗者をどう扱うか。下位 §S2-1.11 は fork cancellation を
  `active-cancellations/<pointer_sha256>.json`・exact 6 fields で定めるが、R1 が裁定したのは
  失効 record であり cancellation は範囲外だった。**上位が専用 record を持つべきかどうか自体が
  未裁定。** 候補 = (a) 下位 §S2-1.11 と同型を 1 層上へ写す / (b) 上位は cancellation を持たず
  fork の回復も補償世代 (Q3 (i)) だけで行うと明示禁止する / (c) 先送り確定項目として §12.2 へ移す。
  **親の推奨は (a)** — Q3 (i) の補償世代は「祖先へ戻さず前進する」規則であって、同一世代内で
  2 本目の X が置かれた fork の敗者を無効化する手段ではない。(b) では敗者が解決不能のまま残り
  §7.2 の「live tip を一意に解決する」義務と衝突する。(c) は cancellation が封印 S・副作用境界 B
  に依存しないため先送り箱へ入れる理由が無い。
  gate = `CFAB-R4-CANCELLATION-RECORD` (owner = user, status = unresolved) を登録済み。
  正本 = `docs/calibration-freeze-authority-bundle-design.md` §12.3 R4

- {{T:cfab-hash-pin-detection-gap}} **P2・新規**: `_EXPECTED_FIXTURE_ENTRIES_SHA256` と
  `_EXPECTED_ROW_IDS_SHA256` の 2 つの独立 hash pin に、**それぞれを単独で到達・殺す陰性 node が
  無い** (品質点検 3 巡目 S6F-03)。required-gates pin には単独の reorder node があるのと対照的。
  どちらか一方の比較だけを無効化しても、現行 fixture は canonical のままなので既存負例が前段で
  落ち、pin の欠落を示す node が赤にならない。**本 wave 以前から存在する pin であり、本 wave が
  作った欠陥ではない。** 対応 = 単独陰性 node を足すか、他の raw pin と冗長ならその事実を明記して
  単独変異証拠から外す。§10 の「manifest literal・実体・独立期待値の三者比較」の一部が静的読解
  だけに依存している状態。

- {{T:check-docs-fence-scanner-column}} **P2・新規**: `tools/check_docs.py` の fence scanner が
  indent を**表示 column ではなく文字数**で数えており、行頭 tab を「indent 1」と扱う
  (焦点再レビュー 2 巡目が指摘、`check_docs.py:3281` / `:3288`)。CommonMark では tab は
  tab stop 4 の column 送りなので indent 4 以上 = fence ではない。本 wave は
  `orchestrator/tests/calibration_freeze_authority_contract.py` 側の同型欠陥だけを直し、
  `tools/**` は scope 外として触っていない。**独立 2 例目の producer** であり、族一般化の条件
  (DW-G03) を満たす。
