---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-t139-prereg-freeze
seq: 2
title: [T-139] 本走前置 — paired 例外を roadmap へ限定記録し、事前登録 core を凍結した — 敵対検証が有意水準の事後選択と状態表の穴を land 前に止めた (docs のみ、実装差分なし、branch worktree-dev-wave-t139-prereg-freeze)
---

## 本文

- **裁定の履行。** 2026-08-07 の /rulings で [T-139] の 11 件が全件確定 (最後が κ = 劣化幅 20%) した
  ことを受け、U3 の手続きを実行した。roadmap の測定安定性の節へ paired の限定例外を協議改訂で
  in-place 追記し (版凍結・版上げはしない。`docs/roadmap-history/README.md`)、D19 の適用前提を
  限定する決定 ({{D:t139-paired-prereg-gate}}) と投入順序 gate を同じ wave commit へ置き、
  本走の事前登録 core を凍結した。逐語は `output/insights/2026-08-07_t139-prereg-freeze/`。
- **「同じ変更単位」は最厳格解釈を満たしていない。** D134 決定 (3) は限定を同じ変更単位で行うことを
  要求するが、`docs/spool` 規約は canonical 台帳を wave が直接編集することを禁じており、採番と
  canonical 化は land が lock 内で行う。docs のみで到達できる最も強い形 (同一 wave commit +
  fold 後発効) を採り、**残る差はユーザー裁定へ返す**。決定本文で「変更単位」の定義を書き換えて
  適合を宣言することはしなかった (下位の決定で上位要求の意味を変える読み替えになるため)。
- **敵対検証の規模と成果。** 段 2 起草 1 本・段 3 敵対 2 レンズ・段 6 敵対 2 本・焦点再レビュー 1 本の
  計 6 本 (すべて codex `gpt-5.6-sol` / `reasoning=max` / read-only) が**全本 NO-GO** を返した。
  land 前に止まった主なものは、(a) 候補数上限と累積 spending の締切が「本走 verdict の直前」で、
  本走の生データを見てから判定基準を選べた、(b) gate が承認済み bytes を束縛せず、同じ path を
  後から書き換えた blob を事前登録と申告できた、(c) 「回復は見えたが劣化が閾値に届かない」領域と
  「劣化版の方が速い」領域がどの適格性状態にも正しく入らず、状態表の網羅性が破れていた、
  (d) 待機 0 秒・恒真な環境復帰指標・失敗分類の付け替えで gate を満たしたまま外乱割当てを
  合格にできた、(e) 先行 commit の message と roadmap が D134 の要求を「履行する」と断定していた
  (過大主張)。いずれも real と裁定して閉じた。
- **設計上の転回。** 未確定の量 (時間予算表・待機の数値・臨界値の構成・標本数上限・有意水準) を
  「後で第 2 の完結版を作る」形にすると、第 2 版が κ や受理条件を書き換える経路が開く。これを避けて
  **2 段階事前登録** — 推論の構造を core が凍結し、数値は閉集合 (全件必須・余剰禁止) の追補 A
  (pilot 前) と追補 B (本走投入前) で確定する — に変えた。**core 単独では完結した事前登録ではない。**
- **κ の境界。** 裁定の記録は「劣化幅 20% 未満では回復を主張しない」と書いたが、統計的定式化
  (`E[H_w] > 0`、`H = D − κS`) は狭義の不等号なので、**ちょうど 20% も受理しない**。
  事前登録 core はこの境界で書いた。
- **親自身の誤り 3 件。** (i) brief が `package.md` を「確定済み裁定の正本」と書いたのは不正確
  (同書は裁定前の凍結パッケージで、本文は今も「未裁定」と書いている。確定結果の正本は
  worklog (299)/(300))。(ii) brief が新 D 番号を直書きしたのは race-stale。(iii) **base digest に
  ついて親が「段 2 の値と不一致」と段 3 の両レンズへ伝えたのは親の計算誤りで、`spool_fold` の
  関数で再計算すると一致した。**両レンズはこの誤情報に基づき「値を信用するな」と判定しており、
  その判定理由は誤りである (land 直前に再計算する運用規律自体は正しいので採った)。
- **本 wave が実装していないもの。** 投入 gate の機械配線 (producer の投入前検査、受領証への
  三つ組の必須記録、validator の独立再計算、consumer の受理判定、投入 script) は一切ない。
  **「投入が機械的に阻止されている」と読める記録を作らない。**
- **未解決として残したもの。** 測定 checkout の trust root (解決器を実装するまで文書上の要求に
  とどまる) と、待機秒数の下限 (数値を今ここで発明すると捏造になるため追補 A へ送った)。
- **エージェント工数。** codex 子 6 本 (段 2 × 1、段 3 × 2、段 6 × 3)。すべて read-only、
  `check_codex_output` は 6 本とも rc=0。実装子は起動していない (実装面ゼロのため)。
- **逐語の可逆最小正規化。** codex 出力 3 本が markdown の hard-break (行末 2 空白) を含み
  `git diff --check` に抵触した。可視文字を変えずに行末空白だけを除去し、除去前後の sha256 と
  byte 数を `output/insights/2026-08-07_t139-prereg-freeze/README.md` の erratum 表に記録した。
- **親の実測 (すべて本 wave の worktree、login node)。** `tools/check_docs.py` rc=0、
  `tools/spool_fold.py --dry-run` rc=0 (`status: planned`)、`tools/check_ai_provenance.py` rc=0
  (1723 件、新規違反なし)、受入全走 `tools/run_tests.py` **rc=0 (7177 passed / 20 skipped、
  1081.53s、Pegasus request `895477.nqsv`)**。実装差分がゼロのため変異 matrix は射程外である。
- **受入 rc の誤報と訂正 (F152 の再発)。** 先行の 2 走では `tools/run_tests.py` の出力を
  `| tail` へ通しており、親が「rc=0」と報告・記録したのは **`tail` の rc** だった。
  `run_tests.py` 自身の rc は検証されていなかった。**同じ wave の段 8 で F157 の再発を制度化した
  直後に、別の既知失敗型を親が再発させた。**pipe を通さず rc をファイルへ書き出す走行で
  取り直し、上記が実測値である。段 8 の core.md 変更後の走行として有効なのはこの 1 走だけであり、
  先行 2 走の rc は記録から落とす (テスト結果 7177 passed は 3 走とも同じだが、
  run_tests の事前・事後検査を含む rc は検証されていなかった)。

- **段 8 (自己改善)。** 候補 2 件。(1) 親の base digest 誤計算は **F157 と同型の再発**であり、
  これで独立 2 例が揃ったため `DW-G03` に従い族の制度化へ上げ、`DW-S01` の一次資料規律へ
  「値の定義元 tool から取り、手計算で代用しない」を統合した (+62 bytes)。**`docs/dev-wave/**` の
  合計は 25196 / 上限 25200 となり、残余は 4 bytes である。**次の自己改善は縮約か予算の独立審査なしに
  入らない。(2) 実装差分ゼロ wave における受入全走の射程は裁定境界の変更なので実装せず、
  次の一手へ裁定候補として起票した。

## 次の一手差分

### 更新

- [T-139] **P1・roadmap 限定例外と事前登録 core が land 済み。次は追補 A → producer 実装 → pilot**:
  paired の限定例外 (roadmap 測定安定性の節)、D19 の適用前提を限定する決定、投入順序 gate、
  本走の事前登録 core を land した。**事前登録は 2 段階**であり、core 単独では完結しない —
  数値は閉集合の追補 A (pilot 投入より前) と追補 B (本走投入より前) で確定する。
  追補 A が確定すべきもの: 1 割当ての時間予算表・待機秒数・環境復帰の指標と許容範囲・
  失敗の写像先・割当て外 build の binary 束縛・要求 walltime・workload の driver 引数一式・
  3 arm の build identity・実行順の事前 seed と許容 schedule 集合・`J_max` と割当て内訳と
  `J` の導出手続き・同時信頼領域と臨界値 `q` の構成・weak null 較正 simulation の仕様・
  primary 系列の有意水準。追補 B: 候補数上限・個別公表系列の spending・累積台帳の正規の根。
  **pilot は投入不可** — 追補 A が無く、producer も未実装である。
  gate の機械配線 (producer の投入前検査・受領証・validator・consumer・投入 script) は
  すべて producer 実装 wave の責務であり、本 wave はコードを 1 行も足していない。
  κ の境界は狭義 — ちょうど劣化幅 20% は受理しない。
  正本 = `output/insights/2026-08-07_t139-mainrun-design/preregistration.md` (core)、
  逐語 = `output/insights/2026-08-07_t139-prereg-freeze/`、設計判断 = {{D:t139-paired-prereg-gate}}
  base: dc41c0b8608b77ee70ac33a9637df5f56f224f23a6524f14c23da034013e2343

### 新規

- {{T:t139-samechange-residual}} **P2・ユーザー裁定待ち**: D134 決定 (3) の「同じ変更単位」について、
  `docs/spool` 方式の下で canonical 台帳と roadmap を同一 Git commit に載せることは不可能である。
  本 wave は同一 wave commit + fold 後発効で無害化したが、要求そのものを緩めたと読むこともできる。
  (α) fragment が wave commit 時点の署名決定であり fold は採番だけ、と認めるか、
  (β) 認めないなら別の充足形を定めるか、を裁定する。
- {{T:devwave-zero-diff-acceptance-scope}} **P3・ユーザー裁定待ち (dev-wave 契約)**:
  `DW-S04` は実装差分ゼロの wave について「変異 matrix と**受入全走**が対象外だと射程を明記する」と
  定めるが、docs のみの wave でも `test_check_docs` / `test_spool_fold` は実 repo を読むため
  受入全走に実質的な検出力がある (本 wave も実走して rc=0 を得た)。契約どおり省くと docs 起因の
  赤を見逃し、走らせると契約と食い違う。射程を「変異 matrix だけ対象外。実 repo を読むテストが
  あるなら受入全走は走らせる」に改めるかを裁定する。裁定境界の変更なので本 wave では実装しない。
- {{T:t139-producer-preconditions}} **P1・ユーザー裁定待ち (producer 実装 wave の前提)**:
  (i) producer と投入 script のどちらを第一の admission boundary にするか。
  (ii) 測定 checkout の trust root — 解決器が実 checkout から導出することを、どこまで機械保証にするか
  (現状は文書上の要求にとどまり、別 checkout で測って整合する受領証を作る偽造を検出できない)。
  受領証の三つ組の必須記録と validator / consumer の権威境界は本 wave の決定と D162 が既に
  制約しているので、再択一にはしない。
