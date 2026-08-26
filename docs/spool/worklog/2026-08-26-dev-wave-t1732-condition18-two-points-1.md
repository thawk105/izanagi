---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1732-condition18-two-points
seq: 1
title: [T-1732] 条件 18 の発火点を投入前と赤処理前の 2 点にした (コード + テスト + docs、branch worktree-dev-wave-t1732-condition18-two-points、変異 matrix = baseline PASSED・3/3 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

D907 (ユーザー裁定) の実装。設計判断は裁定済みのため、残るのは実装と検査だった。

**trigger 逐語を一次資料から確定した。** 親は段 1 で「D907 が根拠にした 3 byte 短い案は
『テスト』を落とした案だろう、落とすと焦点走の発火点が消える」と provisional 裁定 (P1) したが、
`docs/archive/worklog-phase3-0825-949.md` に提案文言そのもの (`親のテスト・受入前と赤処理前`) が
残っており、**「テスト」を落としていなかった。P1 は refuted。** 裁定が実測した文字列をそのまま採り、
裁定が見ていない新しい文字列を発明しない方針とした。42 byte で現行より 3 byte 短い。

**入口の byte 予算は 0 だった。** `.claude/commands/dev-wave.md` は 9520 byte で `COMMAND_LIMITS` の
上限ちょうど。さらに段 6 レンズ B が、上限ではなく**現物 9520 byte を固定する assertion** を
見つけた。親が段 1 brief に書いた「現行以下なら検査は赤にならない」という一般化は誤りで、
期待値を実測値 9517 へ更新した。予算値そのものは変えていない (独立審査対象のため)。

**恒真化を避ける設計。** 条件 dispatch の既存検査は「入口の trigger 文 == 契約 dict の値」の
等値比較だけで、両方を同時に 1 点へ戻すと全 gate が緑になる (親が反実仮想で実測)。そこで契約 dict から
導出しない手書き逐語 2 本を置き、入口から抽出した実 trigger が両方を含むことを本番検査経路
(`_main` → `_check_command_docs_guard`) で要求する形にした。判断の記録は {{D:condition-18-two-point-gate-scope}}。

**変異 matrix (repo_head=a349c991、`tools/mutation_worktree.py` の使い捨て worktree 経路)。**
probe を全件 SURVIVED 期待で回して観測 node を集め、それを完全集合として本走を組んだ。
2 点性の証拠は M01/M02 が担う — 新設検査の連言から走行点側だけを外すと走行点欠落の負例だけが、
赤処理点側だけを外すと赤処理点欠落の負例だけが落ちた (**各 1 node**)。M03 (解決器が状況を無視) は
別 context 検査だけを落とした。実ツリーの入口 trigger と契約 dict を同時に単点化する変異
(probe の M04/M05) は**各 329 node** を巻き込む過剰決定だったため、`DW-M03` に従い単独変異の
証拠から外し、冗長 gate として記録した。

**段 6 の敵対レビュー 2 本と焦点再レビュー。** must-fix 5 件のうち、採用 2 件 (赤処理側 subprocess の
標準入力が非伝達検査の穴になっていた / timeout の根拠が別 node の所要の流用だった)、
親の実測で解消 1 件 (finding 件数が推測値という指摘 — 焦点走の緑がそのまま件数の実測だった)、
scope 外 2 件。焦点再レビューは残る must-fix ゼロで閉じた。

**refuted。** (a) 鏡像 `.agents/skills/dev-wave/SKILL.md` の追随が要るという指摘 — 逐語 0 件を実測。
(b) 広げた変異の finding が 3 件になるという指摘 — 合成 fixture では byte 予算に当たらないため
成立せず、実ツリー変異にのみ当てはまる (そちらは登録しない裁定にした)。

**scope 外として裁定パッケージへ返すもの。** 実運用の manager / 赤処理経路から
`resolve_condition_sections` を呼ぶ配線は未実装であり、**「実運用で必ず 2 点発火する」ことは
本 wave では担保していない**。関門 (2 点性の検査) は本番経路に配線済みで、未配線なのは解決器の方である
(F559 の型との切り分け)。もう 1 件、共有ヘルパ `_run_check` に時間上限が無い件は既存の族全体の
性質であり、`DW-G03` に従い 1 例で制度化しなかった。

**親の手落ち 1 件。** 校正用の単発走行が計算ノードで実行中に焦点走を投入し、同一 worktree の
並行 dispatch で orphan hold を踏んだ ({{F:probe-run-serialization-parent-side}})。
hold は先行走行の自然終了で撤去され、`qdel` はしていない。

**段 8 で回帰を出し、逐語 pin の閉包が 4 層あることを実測した。** `DW-O26` の 1 行を改める
自己改善で、docs 本文と production の exact literal を揃えたところ焦点走が 326 failed になった。
残っていたのは (3) 合成 repo を書く元の写しと、(4) 節の byte 数を独立した数値で固定する pin である。
(3) は旧文のままだと合成 repo を使う全テストに違反が 1 件ずつ増え、(4) は数値だけなので逐語検索で
見つからない。**親が編集を始める前に閉包を数えなかったことが原因**で、実装子は pytest を実走できない
ため実 repo の検査 (期待どおり 1 件) しか見えず、親の焦点走が唯一の検出点だった。
なお (4) の検査は「production 定数と合成 fixture の共謀的な縮小を独立 literal で拒否する」もので、
狙いどおり働いた結果の赤である。

**エージェント工数。** codex 子 12 本 (plan 1 / consult 2 / author 1 / review 3 / fix 5)、
すべて model=gpt-5.6-sol・effort=xhigh・rc=0。段 5 実装子は 1064 秒・57 model call。
**子は sandbox の制約で pytest を一度も実走できず**、実測はすべて親が行った (受領証と報告に明記)。
親の argv 誤り 1 件 (review 段で `--reasoning` を指定して rc=2、子は未起動) は
`DW-C01` に既記載の制約であり、文書の欠落ではなく適用漏れだった。

## 次の一手差分

### 完了

- [T-1732] 条件 18 の発火点を投入前と赤処理前の 2 点にし、両点が独立に発火することを
  変異で裏取りした。実運用 adapter への配線は {{D:condition-18-two-point-gate-scope}} で
  scope 外と裁定し、下の新規項目へ分離した。
  remaining: none
  base: 447e43144ffd93f95022fe84a2e809d6a993a980615f4184863075bf90dfe2df

### 新規

- {{T:condition-18-production-adapter}} **P2・裁定待ち**: 条件 18 の 2 点発火を実運用で
  担保するなら、manager の赤処理経路を観測可能な adapter にして
  `resolve_condition_sections` を呼ぶ設計が要る。現状は入口の文書契約と解決器の検査までしか
  担保していない。段 6 の敵対レビュー 2 本が独立に指摘し、いずれも別タスクと判定した。
- {{T:run-check-shared-timeout}} **P3・新規**: `orchestrator/tests/test_check_docs.py` の
  共有ヘルパ `_run_check` は `timeout=None` で、command guard の全負例が共有する。
  変異後の checker が停止すると bounded time で赤が確定しない。既存の族全体の性質のため
  `DW-G03` に従い単発では制度化せず、独立 2 例が出るか族全体の migration として扱う。
