単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials

## 必読事項の射影

次の絶対パスだけを読む。**この射影に挙げた file が読めなければ即停止し、その旨を出力に書く。**
停止規則の射程はこの射影 file に限る — 自分で探した path が不在でも、それは停止理由にしない。

1. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/results/2026-09-16-b7-three-run-materials.md` (再レビュー対象)
2. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/focus-out.md` (前巡の所見)
3. `/work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced/result.json`
4. 同 root の `reservation.json`
5. 同 root の campaign `backoff-sweep-silo-balanced-sweep-0dd37c05` の `runs/wal.jsonl`
6. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-15/t1998-landed-main-recheck/README.md`
7. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-14_t2589-consumer-real-artifact-repair/README.md`
8. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-13_t2557-balanced-stock-inline/README.md`
9. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/t1998-balanced-stock-inline-preregistration.md`
10. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-07_t2364-paper-story-a2-certification/raw-manifest.json`
11. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-08_t2411-paper-story-a6-certification/raw-manifest.json`
12. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/README.md` の
    「results 系列（`results/` サブディレクトリ）」節の表

## 依頼

**前巡 (`focus-out.md`) が出した 3 件を親が直した。閉じたかを判定する。それ以外は見なくてよい。**

対象は次の 3 件である。

1. **partial だった「事前登録 §8 の identity 実値」** — 親は §1.2 の末尾に identity の表を足し、
   job body script digest と、事前登録 sha が成果物側・解析規則側の 2 定数として束縛されている旨を
   書いた。**表の 7 行の値をすべて一次資料で照合する。** 2 定数の説明が資料の書きぶりに
   収まっているかも見る。
2. **should-fix「§1.4 の field 不存在が直後の説明と矛盾」** — 親は「走行成果物の側に無い」と
   限定し、`payload.src_token` が WAL に実在することを明記した。**矛盾が解けたか。**
3. **should-fix「§4.2 の hash 照合範囲が §4.3 より広い」** — 親は照合先を走行ごとに分け、
   [T-1998] には raw manifest が無く WAL の照合先は走行成果物の `wal_sha256` であると書いた。
   **この記述が現物と合うか。** [T-1998] の成果物 root に raw manifest が本当に無いかも確かめる。

加えて、**この 3 つの修正で新しく壊れた箇所 (regressed) が無いか**だけを見る。重複、矛盾、
消し残し、番号のずれ、限定の件数 (本文は 20 件、入口の行も 20 件と書く) を確かめる。

**前巡で closed と判定した 9 件は再監査しなくてよい。**

## 禁止

- file を書かない・編集しない・commit しない。read-only である。
- 新しい測定を提案しない。既存の凍結物の bytes を変える案を出さない。
- B-7 の充足・不充足を宣告する案を出さない。
- 数値を版や既存稿から取らない。出所は一次資料だけとする。
- 所見が無いなら「無い」と根拠つきで書く。照合したことを書かずに「問題なし」とだけ返さない。
- 書込み可能な tmp は無い。pytest の緑を求めない。静的検査でよい。テストの実測は親が行う。

予算が尽きそうなら、途中結論を下の出力形式どおりに書いて終える。無出力が最悪である。

## 出力形式

次の H2 見出しをこの順で使う。各所見には `重大度: must-fix | should-fix | nit` と、
**放置したとき成果物の値・受理集合・参照がどう変わるか**を 1 行で書く。

## 3 件の対応表
## identity 表の照合
## 新しく壊れた箇所
## 総括
