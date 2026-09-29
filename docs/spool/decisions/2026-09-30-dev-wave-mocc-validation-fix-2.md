---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-30
wave: dev-wave-mocc-validation-fix
seq: 2
---

## {{D:mocc-validation-recheck-fix}}. MOCC の validation の修理は lock 状態の読みの後に版を読み直す形 (案 A) で F の子の 1 commit にし、D297 は「意図した修理差分による不合格」として記録して pin 前進での扱いを別に裁定する

対象: T-2872。資料: D2277 項 1・2、D2293、D297 / D2255 / D2275、insight `output/insights/2026-09-29/mocc-validation-fix/README.md` (§1・§3・§4)、段 4 裁定 `verbatim/s4-ruling.md`、段 6 裁定 `verbatim/s6-ruling.md`、一次資料 `output/insights/2026-09-29/t2872-mocc-g2-split/README.md` §7。

**決定:**

1. **修理の形:** CCBench の F `25898d00` の直接の子 X `f4a5169e` (branch `izanagi-mocc-validation-fix`) で、`cc/mocc/transaction.cc` の validation の read set 走査だけを変える。既存の版比較と writer lock の検査は残し、その後ろで版を acquire で読み直し、(epoch, tid) が検査した版と違えば既存の版不一致と同じ状態・計数で abort する。`max_rset_` は 3 回目の load でなく検査した版から取る。既存の `#line` の値は据え置き、新たな `#line` は足さない。作成は Codex author、commit は親 (trailer = Codex author・reviewer・Claude manager)。
2. **検証の型:** 同じ job の中で修正前 F と修正後 X を交互に走らせ、事前登録の判定 (判定不能 0・修正後の trace build の G2 0/112・修正後の commit 側 class A 0) を runner の集計が機械的に出す。修正前 F の G2 と class A は同時刻の対照として報告し、完了判定に入れない。修正後の class A = 0 は修理から構造上導かれるので、修理の効き目の独立の観測として再読の不一致による abort 件数を数える。結果は成功 (G2 0/112、class A 0、対照は G2 8/56・class A 1,415、再読 abort 6,368)。
3. **D297:** F → X の検査は GCC 11.4・12.3 とも TRACE=0 正規化 preprocess 出力の不一致で rc=1 になり、差分は `cc/mocc/transaction.cc` の 1 hunk・header 0 だった。これを「D297 不合格 (意図した修理差分)」と記録し、合格・include 活性の合格は名乗らない。gitlink を X を含む tip へ進めるときの D297 の扱い (C → F の合格と F → X の意図した差分の審査を分けて受け入れる等) は、gitlink 前進 wave で裁定する。
4. **push と gitlink:** X の branch の push は人間の手番 (D16)。gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN`・patches は本決定では変えない。

**理由:**
- 案 A は既存条件への条件追加なので、同じ観測列で元のコードが拒否した取引を新たに受理しない (依頼の「受理集合を縮める方向だけ」を字義で満たす)。版が前進する範囲では、通過した取引は lock を読んだ瞬間に「読んだ版のまま・他者の writer lock なし」を満たし、Silo の 1 word 検査 (`cc/silo/transaction.cc` の read set 検査) に対応する。
- `#line` を据え置くと差分が修理の hunk に閉じ、`ERR` の `__LINE__` (後段の `#line 1187` の後) も patch の context も動かない。修理の行は実際に有効な C++ 文なので、論理行番号が進むのは実態どおりである。
- D297 は trace hook の変更が TRACE=0 を変えないことを検査する最後の防壁で、本物の修正はそれを構造上通らない。検査器を変えずに「意図した差分による不合格」と名付け、差分が修理の hunk だけであることを併記すれば、規律 1 の防壁を緩めずに事実を残せる。

**却下した選択肢:**
- 案 B (lock を先に読み、版は 1 回だけ読む) — Silo の考え方には対応するが、lock を読んだ後に他者が施錠してまだ公開していない実行を受理しうるので、元のコードに対して受理集合を縮める方向だけとは言えない。
- 修理より後ろの既存 `#line` の値を +15 する — trace 区間を除いた行番号の意味は保てるが、修理と無関係な `ERR` の `__LINE__` と D297 の差分と patch の context を広げる。
- D297 の検査器に「意図した差分」を受理する例外を足す — 正しさ防壁の緩和になり、依頼の scope 外 (gate・検査の追加をしない)。
