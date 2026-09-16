単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results

## 必読事項の射影

これは自分たちの論文材料 (統制稿) の主張範囲レビューである。次の絶対パスだけを読む。**この射影に挙げた
file が読めなければ即停止し、その旨を出力に書く。** 停止規則の射程はこの射影 file に限る — 自分で探した path が
不在でも、それは停止理由にしない。差分は commit 前の作業ツリー (untracked の新 file 1 本 + README の 1 行追加)
であり、親が起草した。数値の検算は別のレビュー子が担当するので、ここでは行わない。

**レビュー対象 (これが本題)**

1. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md`
2. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/docs/paper-story/README.md` の
   「results 系列（`results/` サブディレクトリ）」節 (2026-09-16 の `b10-static-tail-not-observed` の行が今回の追加)
   と、同 README の「最新スナップショット以後に確定したこと」節の項目 3

**依頼の原文 (親が受けた scope と裁定。逐語)**

> [T-2647] B-10 静的 backoff 右 tail 本走 (2026-09-15 完走、group `b10-backoff-grid-20260915T061814Z-545445`、
> 集団判定 `not-observed-in-any-workload`) の results 稿を `docs/paper-story/results/` へ起草する。A-2 / B-7 の
> 既存稿 (`2026-09-07-a2-certification-observed-positive.md`、`2026-09-16-b7-three-run-materials.md`) と同型の
> 日付付き凍結物として置く。言い方は `docs/b10-backoff-static-tail-preregistration.md` §4.5 が固定する
> 「登録した述語では、表現可能域 9999 µs までに飽和を観測しなかった」に限り、「飽和しない」「飽和点が存在しない」
> とは書かない。性能値は未認証 (`performance_certified: false`) のままで採用根拠にしない (規律 2)。論文図は作らない
> (`output/insights/2026-09-16/t2647-b10-tail-downstream.md` §4 の 3 条件が未充足)。2 本目 cohort の地位 (D2050)
> には触れない。正本 = 同 insight §1・§3・§4、`output/insights/2026-09-15/t2266-tail-band/README.md`、
> `output/insights/2026-09-16/b10-tail-formal-submit/README.md`、`docs/paper-story/README.md`
> 「最新版以後に確定したこと」項目 3。着手直前の local main から fresh worktree。docs のみ。本題の results 稿だけ。
> 仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。

**照合に使う正本**

3. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/docs/b10-backoff-static-tail-preregistration.md`
   (§0、§1、§3、§4.4、§4.5、§4.6、§7、§9 を主に使う)
4. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/output/insights/2026-09-16/t2647-b10-tail-downstream.md`
5. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/output/insights/2026-09-16/b10-tail-formal-submit/README.md`
6. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/output/insights/2026-09-15/t2266-tail-band/README.md`
7. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/docs/paper-story/results/2026-09-07-a2-certification-observed-positive.md`
   (同型の枠の先例)
8. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/docs/paper-story/results/2026-09-16-b7-three-run-materials.md`
   の §0 と §3 (同型の枠の先例。限定の書き方)
9. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/CLAUDE.md` の「絶対規律」節
   (規律 1・2・3・7)

## レンズ

**主張の範囲と言い方の固定。** 稿が (a) 事前登録が固定した言い方を超えていないか、(b) 一次資料が支持しない
主張・含意を持ち込んでいないか、(c) 書くべき限定が欠けていないか、(d) 依頼の scope (本題の results 稿だけ・
D2050 に触れない・図を作らない・性能値を採用根拠にしない) を逸脱していないか、を点検する。
数値の一致は別の子が担当する。

## やること

1. **言い方の固定の点検。** 稿の全文から、「飽和しない」「飽和点が存在しない」「飽和は無い」と読める文、
   9999 マイクロ秒より右を含意する文、機序を含意する文 (「〜だから下がる」「〜が原因」) を探す。
   事前登録 §3・§4.5・§9 の固定表現と照らし、**超えている文を逐語で名指しする。**
   「読めること」「観測できること」と書かれた段落も対象にする — 記述のつもりで因果や一般化を
   滑り込ませていないか。
2. **protocol 出力と研究宣告の区別 (D12)。** `not-observed-in-any-workload` / `declining` / `certified` を
   成功・失敗・完了のラベルへ読み替えている文が無いか。B-10 や [T-2647] を閉じたと読める文が無いか。
3. **性能値の扱い (絶対規律 2)。** §2.3 の throughput 表と「過抑制の費用」の文が、variant の採用・不採用の
   根拠として読める形になっていないか。「望ましい」「合理的」「最適」等の評価語が入っていないか。
4. **正しさの記述 (絶対規律 1・2)。** §1.4 と限定 6 が、trace 有効ビルドの別走行の結果を性能測定条件そのものの
   直列性保証へ広げていないか。逆に、成果物が記録している事実 (120 記録 certified、anomaly 0) を過小に
   書いていないか。`legacy` mode の条件差の書き方が成果物の field (`correctness_flags`) に忠実か。
5. **監査限界の引継ぎ。** insight 5 の §0・§4 が書く「当時の実行全体の独立監査は未実施」「再導出が示すのは
   現行 loader が受理し同じ judgement を出したことまで」「探索走 argv 未保存」が、稿の限定に**弱められずに**
   入っているか。逆に insight が言っていない監査結果を稿が主張していないか。
6. **限定の欠落。** 先例 7・8 の限定と事前登録 §3・§9 を照らし、稿の §3 (14 件) に**欠けている限定**が
   あれば具体的に書く。逆に、一次資料に根拠の無い限定 (自作の懸念) が混じっていないか。
7. **scope の点検。** 稿と README 行に、依頼が外したもの — 2 本目 cohort の地位 (D2050) についての判断や記述、
   論文図の作成・昇格、gate・検査・台帳の新設や提案、事前登録・版・既存稿の改訂 — が入っていないか。
   §0.3 の「D2050 が持つ」という 1 文が「触れない」の範囲に収まるかも判断する。
8. **README 項目 3 との整合。** README の項目 3 (2026-09-16 追記) と稿の記述が矛盾していないか。項目 3 が
   「古くなっていない」とした 4 点を稿が古くしていないか。
9. **同型性。** 稿の枠 (冒頭の但し書き、§0 位置づけ、§1 条件、§2 結果、§3 限定、§4 一次資料) が先例 7・8 と
   同型か。系列の規則 (README「results 系列」節: append-only、1 file = 1 結果、数値の出所は一次資料だけ、
   転記元 SHA-256、protocol status を宣告へ拡張しない) に反する箇所が無いか。

## 禁止

- file を書かない・編集しない・commit しない。read-only である。
- 新しい測定・図・gate・検査を提案しない。既存の凍結物の bytes を変える案を出さない。
- 「飽和しない」と書く方向へ緩める提案をしない。事前登録の固定表現は動かない前提で点検する。
- 所見が無いなら「無い」と根拠つきで書く。点検したことを書かずに「問題なし」とだけ返さない。
- 書込み可能な tmp は無い。pytest の緑を求めない。静的検査でよい。テストの実測は親が行う。

予算が尽きそうなら、途中結論を下の出力形式どおりに書いて終える。無出力が最悪である。

## 出力形式

次の H2 見出しをこの順で使う。各所見には `重大度: must-fix | should-fix | nit` と、
**放置したとき成果物 (統制稿・入口の表・下流の執筆) の値・受理集合・参照がどう変わるか**を 1 行で書く。
所見ごとに、稿の該当箇所を逐語 (1 文以内) で引く。
最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。

## 言い方の固定
## protocol 出力と研究宣告
## 性能値と正しさの扱い
## 監査限界の引継ぎ
## 限定の欠落と過剰
## scope と README 項目 3 との整合
## 同型性と系列の規則
## 総括
