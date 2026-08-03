# land の fold 署名判定を trusted main cutoff の外側へ限定する — dev-wave 逐語 (2026-08-03)

`authority: none` / `default_effect: no-state-change`

相談・敵対レビュー・fix・変異の逐語。正本は `docs/decisions.md` の該当 D と
`docs/worklog.md` の該当エントリで、本ディレクトリは一次資料を凍結するだけである。

| ファイル | 段 | 内容 |
|---|---|---|
| `s1-brief.md` | 1 | 親 brief。前提実測と provisional 裁定 (P1)〜(P4) |
| `s2-plan.md` | 2 | codex プラン起草。親案を棄却し三 tree 免除を提案 |
| `s3-lens-a-spec-conformance.md` | 3 | 敵対レンズ A — 仕様適合と痕跡集合の十分性 (NO-GO) |
| `s3-lens-b-regression-closure.md` | 3 | 敵対レンズ B — 回帰・consumer 閉包 (NO-GO) |
| `s4-ruling.md` | 4 | 親の裁定。plan v2 と変異事前登録 |
| `s5-author-report.md` | 5 | 実装子の完了報告 |
| `s6-review-1-teeth.md` | 6 | 敵対レビュー 1 — 歯があるか (NO-GO) |
| `s6-review-2-regression.md` | 6 | 敵対レビュー 2 — 回帰・テストの誠実性 (NO-GO) |
| `s6-fix1-report.md` | 6 | fix round 1 — subprocess 削減・量化の固定・land 配線 E2E |
| `s6-fix2-report.md` | 6 | fix round 2 — 新設 E2E の receipt fixture を実 planner 準拠へ |
| `s6-fix3-report.md` | 6 | fix round 3 — 変異が暴いた量化の穴を負例 2 本で塞ぐ |
| `s4-ruling-addendum.md` | 4 | 裁定 補遺 (改訂 2)。全 parent が trusted な merge の扱い |
| `s6-fix4-stop-report.md` | 6 | 補遺 初版に対する実装子の**停止報告**。既存テストとの矛盾を指摘 |
| `s6-fix5-report.md` | 6 | 補遺 改訂 2 の実装 |
| `mutation-spec.json` / `mutation-ledger-run1.json` | 6 | 変異本走 1 回目 (8 件)。**erratum を含む初回結果** |
| `mutation-spec-2.json` / `mutation-ledger-2.json` | 6 | fix3 後の M03 / M04 再走 |
| `mutation-spec-3.json` / `mutation-ledger-3.json` | 6 | 補遺 実装後の M09〜M12

## 何が壊れていて、何を直したか

`verify_declared_fold_commit` の fold 署名検査が `git diff-tree -m` で親ごとの差分を見ていたため、
`DW-O23` が指示する「land 前の wave 側 main 取り込み merge」は、wave 側の親との差分に
main が既に取り込み済みの fold 署名 (`M docs/spool/FOLDED.md`) を必ず含み、常に拒否された。
fold は 2026-08-02 以降すべての land が `FOLDED.md` を触るため、main が動いた後に取り込みが
要る wave は正規手段では land 不能だった (rebase / cherry-pick は `DW-STOP` が禁じる迂回)。

規則を「その commit が **trusted main cutoff の外側で加えた変更**だけを署名判定にかける」へ変えた。
parent が 2 以上の commit では、tested main の祖先である parent がちょうど 1 つのときだけ
その親との差分を見る。0 個または 2 個以上、および cutoff 未指定の呼び出しでは全 parent を
走査して現行の強さを保つ。ff-only で main に載るのは wave が trusted main の上に加えたものだけ
なので、この定義では main 自身の履歴が再び現れることは原理的に起きない。

## 段 3 / 段 6 が潰した案

- **累積差分 (親の当初案)**: `landed_main_sha` は post-fold HEAD で範囲端が誤り。
  正しい端に直しても、hidden fold の後に protected tree を base へ戻す履歴を見逃す。
- **三 tree 免除 (段 2 案)**: 免除が **path 単位**なので、protected 2 path を main 親から、
  canonical 台帳を wave 親から採る merge が通る (fold は transaction である)。
  加えて commit × parent × key × 候補で git subprocess が増え、共有 deadline で
  正規履歴を timeout 拒否しうる。

## 変異 matrix の結論

初回 8 件は KILLED 4 / MISMATCH 3 / SURVIVED 1。**SURVIVED 1 件 (M03) は実物の穴**で、
trusted parent が複数の octopus において「信頼できない parent も走査する」ことをテストが
固定していなかった。M04 も同型で、cutoff 未指定時の全 parent 走査が固定されていなかった。
fix3 で「走査から落とされる側の parent からしか署名が見えない」負例 2 本を新設し、
再走で M03 / M04 とも期待 node ちょうどで KILLED。
M06 / M07 は kill されたが期待より多くの node が赤で、**冗長 gate** として記録する
(単独変異の証拠からは外す)。初回台帳は `DW-M02` に従い消さずに残す。

## 禁止集合の置き所を 4 回言い当てられた

本 wave は防壁の判定領域を 4 回書き直した。いずれも独立の検証が突いた。

1. 親の当初案「累積差分」→ 段 2 プランが棄却 (tree 復元を見逃す)。
2. 段 2 案「三 tree 免除」→ 段 3 レンズ B が棄却 (免除が path 単位で transaction を分割できる)。
3. 採用案「trusted がちょうど 1 つ」→ **本 wave 自身の land が実測で棄却**。
   worktree を main から切った直後に main を取り込むと両 parent が trusted になり、
   「main に追いついてから作業を始める」という正規形が禁止される (F82 の 4 度目)。
4. 補遺 初版「極大 trusted parent を無条件に選ぶ」→ **実装子が契約どおり停止して棄却**。
   fix round 3 で新設した octopus 負例と矛盾する。

最終形は「全 parent が trusted のときだけ極大 trusted parent を選ぶ」で、
untrusted parent を含む merge の判定は一切変えていない。

## この wave が閉じていないこと (ユーザー裁定へ)

1. **署名 2 条件は lock 外 fold の十分条件ではない。** canonical 台帳だけを書き換える履歴、
   `T` (gitlink) を経由する復元、同一 commit 内の A→D は今日も受理される。
   閉じるには fold transaction の意味検証 (FoldPlan delta の保存または決定的 replay) が要り、
   「legacy wave が canonical を直接編集する」現行契約 (F82 が記録) と衝突する。
   **本 wave はこの穴を広げも狭めもしていない。**
2. **supervised runner (checker / daemon) は直っていない。** receipt の初期 `base_main_sha` に
   束縛されており cutoff の意味が違うため、正規 main merge を拒否したままである。
   直すには receipt schema へ tested main cutoff を別 field で永続化・binding する必要がある。
