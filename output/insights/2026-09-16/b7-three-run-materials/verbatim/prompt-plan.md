単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials

## 必読事項の射影

次の絶対パスだけを読む。**この射影に挙げた file が読めなければ即停止し、その旨を出力に書く。**
停止規則の射程はこの射影 file に限る — 自分で探した path が不在でも、それは停止理由にしない。

1. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/brief.md` (親の段 1 brief)
2. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/verbatim-d1631.md`
3. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/verbatim-d1874.md`
4. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/verbatim-d1986-1to5.md`
5. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/verbatim-d1993.md`
6. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/verbatim-b7-item.md` (版 §8 の B-7 項の逐語)
7. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/README.md`
8. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/results/2026-09-14-b7-all-workload-regression.md`
9. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json`
10. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json`
11. `/work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced/result.json`
12. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-15/t1998-landed-main-recheck/README.md`
13. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-14_t2589-consumer-real-artifact-repair/README.md`

必要なら次も読んでよい (任意、読めなくても停止しない)。

- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-13_t2557-balanced-stock-inline/README.md`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/phase3-main-experiment.md` の「失敗条件」節
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/figures/README.md`
- [T-1998] の走行の同じ dir にある `reservation.json`

## 依頼

親 brief の scope 1 (新しい results 稿) について、**file:line 粒度の起草プラン**を返す。
本文そのものは書かなくてよい。**どの節に、どの一次資料のどの field から、どの値を、どの表記で
置くか**を決めるのが依頼である。

具体的に次を出す。

1. **配置と単位の判断。** 親 brief の (P1)(P2) を検査する。新しい results 稿を足すのが D1631 の
   規則に適合するか、対抗案 (a)(b)(c) のどれかが正しいかを、`verbatim-d1631.md` と
   `docs/paper-story/README.md` の results 系列節の逐語に照らして判定する。**親の案を守らない。**
   採る案と、採らない案それぞれの却下理由を書く。
2. **節構成。** 新稿の節見出しの一覧と、各節が言うこと・言わないこと。既存の 2026-09-14 稿の
   節構成をそのまま写すのか、3 走行になったことで変える必要があるのかを述べる。
3. **値の対応表。** 掲載する各値について `掲載値 | 出所 file | JSON path または節名 | 逐語の表記`
   の 4 列。**[T-1998] の走行は初めて results 系列へ載るので、ここを特に細かく作る。**
   - `result.json` が持つ値と、consumer の判定 (`status` = accepted、`reason`) がどこにあるかを
     区別する。`result.json` のトップレベル `status` は走行の完了状態であって consumer の判定ではない。
     この区別を節の文面でどう出すかを指定する。
4. **3 走行の異質性をどう表に出すか。** protocol・事前登録・attempt・判定式・outer status の
   単位が 3 走行で違う。D1993 項 6 が「1 つの横断実験として集計しない」と定めている。
   **プールした効果・共通 status を作らずに 3 走行を 1 表へ並べる表の形**を具体的に示す。
   列の取り方で集計に見えてしまう形があれば名指しで避ける。
5. **限定の一覧。** 2026-09-14 稿は限定 11 件を持つ。3 走行になったことで足りなくなる限定、
   新しく要る限定 ([T-1998] 固有のもの) を列挙する。**正しさの記録が 3 走行で同じ形かどうかを
   一次資料で確かめる** — [T-1998] の `result.json` に correctness の欄があるか、無ければ
   それをどう書くか。
6. **入口 README の表へ足す 1 行の文面案。** 既存 5 行の書式に合わせる。
7. **親 brief の誤り。** brief の記述・前提・アンカー表・一次資料表に、現物と食い違うものがあれば
   名指しで挙げる。**brief の引用を根拠に一次資料を直さない — 逆向きに、一次資料を根拠に brief を直す。**

## 禁止

- file を書かない・編集しない・commit しない。read-only である。
- 新しい測定を提案しない。既存の凍結物 (版、2026-09-14 稿、figures、事前登録) の bytes を変える案を出さない。
- 3 走行をプールした効果量・共通の outer status・有意差・床値超の判定を作る案を出さない。
- B-7 の充足・不充足を宣告する案を出さない。
- 数値を版 (`docs/paper-story/2026-09-14.md`) や本 prompt の引用から取る案を出さない。出所は一次資料だけとする。
- 書込み可能な tmp は無い。pytest の緑を求めない。静的検査でよい。テストの実測は親が行う。

予算が尽きそうなら、途中結論を下の出力形式どおりに書いて終える。無出力が最悪である。

## 出力形式

次の H2 見出しをこの順で使う。

## 配置と単位の判断
## 節構成
## 値の対応表
## 3 走行の異質性の出し方
## 限定の一覧
## 入口 README の 1 行
## 親 brief の誤り
## 総括
