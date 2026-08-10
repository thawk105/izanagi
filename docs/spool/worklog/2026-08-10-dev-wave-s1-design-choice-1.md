---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-s1-design-choice
seq: 1
title: 段 7 前提 S1 の設計択一パッケージを返した — 2 案は同じ目標の代替でなく、案 A には登録済み負債 4 件が束ねられていた (docs のみ、実装差分ゼロ、branch worktree-dev-wave-s1-design-choice)
---

## 本文

- **起票根拠 = スコープ B 部分再開裁定 Q2 = (a) の W2** (2026-08-10、一次控え rulings-inbox
  `2026-08-10-scope-b-reopen.md`)。本 wave は docs のみで本番コードを編集しない (ユーザー明示)。
  並走ガード 3 条件 (Q3 = (a)) — (i) 計算ノード未使用、(ii) [T-139] job 走行中のため
  キュー投入なし (wave 開始時 qstat: 900495 RUN / 900512 PRR)、(iii) 裁定帯域は A 優先。
  裁定パッケージの正本 = `dev-wave-jobs/dev-wave-s1-design-choice/ruling-package.md`。

- **択一の形が依頼時の想定と違った。** 「案 A (別 protocol への trace-hook 移植) と
  案 B (stock 専用計測経路) の 2 案を 3 軸で比較する」依頼だったが、**2 案は同じ目標に対する
  代替ではない**と判明した。案 A だけが段 7 の certified cross-protocol 比較を成立させ、
  案 B はどれだけ隔離を厳しくしても比較を作れない (作れるのは正しさ未検証の性能観測で、
  それを比較表・順位・headline の片側に置いた時点で規律 2 違反)。敵対レンズ 1 が blocker 認定。
  よって裁定 3 問は「A か B か」ではなく「段 7 を certified 比較として成立させるために
  判明した本当のコストを払うか」を問う形にした。

- **親の provisional 裁定 2 件が敵対レンズに倒された (real 認定)。**
  - (P1)「si に trace-hook がある以上、案 A は 2 本目の展開で安い」→ **一部誤り**。hook の
    構文は安いが、certified 比較の成立には登録済み負債 4 件が束で要る (下記)。
    si の hook が「安かった」証拠にはならず、si 固有の先例を移植先一般へ一般化していた。
  - (P2)「stock を certified の外に出すと明示宣言できれば規律 2 と整合する」→ **誤り**。
    宣言は防壁ではない。整合するのは公式受理集合・順位・headline から**機械隔離**した
    場合だけで、そのとき案 B は段 7 の成果物ではなく別の偵察成果物になる。

- **案 A に束ねられている負債 4 件 (いずれも本 wave で実在を確認)。**
  1. **trace 形式 v2 化** — `orchestrator/tests/test_verifier.py:601`–`638` に、現行 verifier が
     部分履歴を certified にすることを意図的に assert する characterization が 2 本あり、
     コメントが「恒久対応は … S1 移植と同時に行う」と宣言している (2026-07-02 洗練検査の
     [HIGH] finding、`docs/archive/worklog-phase3-0702-0713.md:52`)。
     **この偽陰性は移植先だけの問題ではなく、現行 silo の certified 結果も同じ verifier に乗る。**
     現行「次の一手」から見えなかったので {{T:trace-completeness-v2}} として起票する
  2. **observer 防壁の protocol 対応** — diff-of-diffs の対象が silo 固定
     (`source_digest.py:79`/`:82`)。全 protocol の単純 union は別 protocol の dirty source を
     digest 外で許すため不可。加えて、汚染された新 pin を baseline にすると diff-of-diffs 自体が
     素通りするため、旧 pin 対新 pin の TRACE=0 翻訳単位同一検査が最後の防壁として要る
  3. **遺伝子空間・較正・floor** — `genome.py:88` の `SPACES` は silo のみ、
     `between_run_floor.py:52` の baseline も silo 固定で測定点 3。3 protocol で floor は 9 セル。
     段 6 前提タスク台帳 (b) と同じもの
  4. **公式成果物への接続** — `layer3_report.py:345` の floor 照合が protocol をキーにせず
     複数一致で停止、`layer3_schema.json:5` は `additionalProperties: false`、
     `layer3_report.py:544` は certified-selection consumer 不在を自認。敵対レンズ 2 が
     最重要 blocker と判定

- **既存 docs の誤りを 3 件見つけた (訂正は scope 外、{{T:ccbench-anatomy-corrections}} で起票)。**
  - `docs/ccbench-anatomy.md:211` の ermia `cstamp<<1` 警告は **dormant な `ssn_commit()` の話**。
    現行 active な `ssn_parallel_commit()` は raw cstamp を格納する
    (`cc/ermia/transaction.cc:765`、`commit()` は `:905` で parallel だけを呼ぶ)。
    **S1 着手時の「必須知識」として書かれているため、従うと誤った写像を実装する。**
    ermia の真の難所は別で、成功した read の一部が `read_set_` に入らない分岐 (`:160`–`:174`)
  - `docs/ccbench-anatomy.md:126` の「mocc 2^4」— 変数化された軸は
    `TEMPERATURE_RESET_OPT` と `KEY_SORT` の 2 つ、`RWLOCK` は固定 define
    (`cc/mocc/CMakeLists.txt:5`–`9`)
  - `docs/phase3.md:269` の must 表 S1 行「silo 内に閉じる」— si に trace-hook が既にある事実
    (`cc/si/transaction.cc:526`–`553`) を落としている
  - なお親 brief 自身の「silo に 13 箇所」も誤りで、実際の `#if TRACE` は 10 箇所だった
    (grep のヒット数をコメント込みで数えた)。敵対レンズ 2 が指摘

- **wave 構成。** 設計択一が割れる案件のため軽量版を採らず、段 2 (codex `gpt-5.6-sol`/max) +
  段 3 敵対 2 本 (`gpt-5.6-sol` / `gpt-5.6-luna`、正しさ境界レンズと実効性レンズ) を回した。
  実装差分ゼロのため段 5・6 を飛ばし `4→7→8→9`。変異 matrix は `DW-S04` の免除
  (実装差分ゼロの「実装しない」裁定) に該当。段 2 の待ち手を 1 度張り替えた
  (最初の上限 30 分が短く、codex は生存していた)。

## 次の一手差分

### 新規

- {{T:s1-design-choice-ruling}} **P1・ユーザー裁定待ち**: 段 7 前提 S1 の設計択一 3 問。
  Q1 = 段 7 cross-protocol の成立方法 (推奨 (a) = trace v2 化を単独 wave で先に land し、
  protocol 移植は別 wave)、Q2 = 移植先の初手 (推奨 (a) = mocc。版 ID が silo と同型で
  補助 buffer 不要)、Q3 = 案 B の偵察解禁 (推奨 (a) = 解禁しない。3〜5 人日で得られるのは
  移植先の選定材料だけだが、その判断は本 wave の静的読解で既に付いた)。
  正本 = `dev-wave-jobs/dev-wave-s1-design-choice/ruling-package.md`
- {{T:trace-completeness-v2}} **P1**: trace 形式 v2 化 (C 行に R/W 件数、txn 終端マーカー) と
  verifier 側の完全性検査。`test_verifier.py:601`–`638` の characterization 2 本を反転する。
  2026-07-02 洗練検査の [HIGH] finding が archive にしか無く現行台帳から見えなかったため起票。
  単独 wave にするか S1 移植へ束ねるかは {{T:s1-design-choice-ruling}} の Q1 で決まる
- {{T:ccbench-anatomy-corrections}} **P2**: 既存 docs の誤り 3 件の訂正 —
  `ccbench-anatomy.md:211` (ermia active は raw cstamp)、同 `:126` (mocc の自由軸は 2 つ)、
  `phase3.md:269` (si の trace-hook 既存)。1 件目は S1 着手時の必須知識として書かれており、
  従うと誤実装するため優先する
