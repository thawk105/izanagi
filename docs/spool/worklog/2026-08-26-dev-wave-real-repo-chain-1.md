---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-real-repo-chain
seq: 1
title: 受入全走の律速だった real-repo 排他鎖を資源別 RW lock へ細分化した (コード + テスト、branch worktree-dev-wave-real-repo-chain、変異 matrix = baseline PASSED・9/9 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 依頼は「受入全走のボトルネック改善。並列化・計算ノード分散ジョブ化・マシンアーキテクチャを
  効率よく使った形などで改善する」。
- **実測の結論は「律速は計算資源でも分割数でもなく 1 本の排他鎖である」だった。**
  73 node を単一 loadgroup へ閉じ込める全対全排他が台帳 239.1 秒 / 前 wave 実測 210.5 秒あり、
  shard-0 の pytest wall 266.89 秒のほぼ全部を占めていた。鎖の 84% は 1 file の 21 node。
  一方この排他が守っている writer は 4 件・**合計 0.19 秒**しかなく、残りは全部 reader だった。
  設計は {{D:real-repo-resource-rw-lock}}。
- **依頼が挙げた 3 手のうち「分散を増やす」は本 wave では採らなかった。**
  work / (48K) は約 77.8 秒で、鎖 210.5 秒がその上にある間はどの並列化も鎖に隠れる。
  本 wave の値打ちは鎖を仕事量の下へ落として**初めて並列化が効く領域へ入れる**ことにある。
- **生死実験 (DW-G01) で筋を先に確かめた。** 同じ 21 node を計算ノードで直列 145.79 秒 /
  21 並列 54.83 秒。結果集合は `21 passed, 2 skipped` で完全一致し 2.66 倍速い。
  並列は login node の反復 3 走を含め 4 走すべて直列と同一結果。
  並列 54.83 秒の内訳は単独 fixture setup 11.80 秒 + 最長 call 43.22 秒 = 55.02 秒とほぼ一致した。
- **段 3 の 2 レンズは親の見積りを 2 つとも独立に訂正してきた。** 「writer は 4 件」
  (親が実装を読んで訂正した数と一致) と「改善後は 56.4 + 149.4 = 205.8 秒であり
  150〜170 秒はこの式から導けない」。**親は当初 149.4 秒の項を落としていた。**
  加えて「function fixture では module fixture の setup を守れない」という、
  親が気づいていなかった機構上の罠を出した。
- **段 3 の最大の所見は plan の共有 cache 機構への攻撃で、親はこれを修理せず削除した。**
  `verify_snapshot` が共有 tree へ `git status` を撃って index refresh lock を踏む経路
  (正しさ) と、cache hit 検証が排他 lock 下で直列化する経路 (性能) の 2 本が挙がった。
  **削除の根拠は議論ではなく実測である** — 生死実験の並列 54.83 秒は
  `21 workers [23 items]` / `--dist load` / **cache 無し**で得た値であり、
  共有 cache は利得に寄与しないことが header から確認できた。
  同じログが「collected instance は 22 でなく 23」という段 3 の指摘も裏付けた。
- **段 6 の正しさレビューは「実装を壊しても赤にならない検査」を 3 件見つけた。**
  (a) 資源 stamp の欠落・不一致で lock を 1 本も取らず黙って続行する経路、
  (b) lock identity 検査が弱く digest に session 固有値を混ぜる変異を通す、
  (c) strip → reorder の順序検査が実行順でなく source 文字列出現順を見ている。
  いずれも事前登録した変異の的であり、放置すれば変異が生き残る形だった。
- **fix は 4 巡かかった。** 1 巡目は赤 2 件が閉じず、2 巡目で原因が確定した
  (memo node は 4/4 件すべて suffix が剥がれていた。assert が 1 件目で止まるので
  1 件に見えていた)。3 巡目は前巡が新設した検査の作り物 config に production が読む
  `args` が無いという検査側の不備で、1 行で閉じた。4 巡目は変異が見つけた穴 (下記)。
  **どの巡でも既存テストの期待値は 1 つも変えていない。**
- **変異が、敵対レビュー 2 本が見逃した検出力の穴を掘り当てた。**
  9 件中 M07 (`stripped = current[:-len(suffix)]` → `stripped = current`) だけが SURVIVED した。
  原因は観測文脈で、札の除去を見る検査は素の collection subprocess の報告を使うため
  **その文脈では xdist が札を付けず、非 memo node は「札が無ければ即 return」で
  変異行に到達しない**。memo へ札を足す側は同文脈で観測できるので M08 / M10 は KILLED だった。
  つまり「実際に札が付いた nodeid から札を剥がす」動作を確かめる検査が 1 本も無く、
  **この経路が壊れると 71 node が 1 work unit のまま走って利得が丸ごと消えるのに全部緑**になる。
  DW-M02 に従い実効 gate へ再照準し、検査だけを足して閉じた (production 挙動は無変更)。
  fix 子は一時変異を実注入して新検査が赤になることを確かめ、復元後の SHA-256 一致まで照合した。
- **変異本走は baseline PASSED・9/9 KILLED・SURVIVED 0・MISMATCH 0** で、
  期待 node は全件が完全集合で一致した (`repo_head` `09a314a8`、spec sha256 `999fa804...`)。
  事前登録 10 件のうち M04 (deadline 撤去 = hang しうる) は裁定どおり dispatch 本走から隔離した。
- **変異 harness は 3 回落ちてから走った。** (1) baseline 赤 — 後述の環境依存テスト。
  (2) 親が失敗した container を `rm -rf` した結果、git に「登録済みだが実体が無い」worktree が
  残り `rc=125`。`git worktree prune` で 1 件除去して復旧した。正しい手順は tool が出す
  `--resume` を使うことだった。(3) `M05` の変異が import 時の整合チェックに当たって rc=4 になり
  失敗 node を抽出できず、かつ**走行中に main が 25 commit 進んで**共有木の事後検査が赤になった。
  前者は DW-M01 / F28 に従い実効 gate へ再照準し、後者は {{D:mutation-source-repo-independent-clone}}
  で構造的に断った。
- **環境依存テストで 2 回止まった。** `output/runs/` が新しい worktree に存在しないため
  `test_t080_output_snapshot_excludes_git_ignored_real_output_changes` が落ちる
  ({{F:ambient-output-dir-red-in-fresh-worktree}})。焦点走 1 回目と変異 baseline の 2 回踏んだ。
  本 wave では環境側で dir を作り、変異 baseline では DW-C01 に従って当該 1 node を
  `--deselect` した。**どちらもテストを直していないので次の wave も踏む。**
- **待ち手の誤報が 3 件あった。** `dev_wave_wait.py producer`、background sleep、Monitor が
  それぞれ「完了」を通知したが `.done` は不在で producer は生存中だった。
  `DW-O01` の「完了は `.done` と exit code だけで判定し通知を判定にしない」を守ったので事故なし。
- **計算ノードへの分散について、親は一度誤読して訂正した。** 引数なしの `qstat` は自分の job しか
  出さないので「同時実行枠が 1」と読みかけたが、`qstat -Q` の実測では `gen_S` 全体で
  RUN 31 / QUE 16 だった。**枠の問題ではなく混雑である。** 本 wave の probe は ARM1 だけで
  外側 wall 677 秒に対し job Elapse 152 秒、差の約 525 秒が queue 待ちだった。
- **本 wave が確かめていないこと:** 受入全走の前後比較はまだ取っていない。
  205.8 秒という値は計測前の仮説であり、D713 に従って certified な利得としては扱わない。
  段 7 の記録 commit 後の受入全走が唯一の実測になる。

## 次の一手差分

### 新規

- {{T:s8c-exclusive-chain-split}} **P1・新規**: `s8c-preregistration-candidate` (台帳 97.1 秒) と
  `s8c-predicate-snapshot` (同 99.7 秒) の 2 鎖に同じ手を当てる。本 wave が real-repo を落とすと
  次の律速はここになる。最長単体は 34.0 / 33.0 秒なので、ほどければ「鎖以外の最遅 worker
  149.4 秒」の項が下がる。中身も同型 (重い共通の下準備 + それを待つ reader 群) であることを
  台帳で確認済み。
- {{T:acceptance-fixed-cost-breakdown}} **P2・新規**: 受入の固定費 56.4 秒の内訳が未分解。
  本 wave 後は wall の約 27% を占める。D532 が認める 3 手のうち (c) に当たる。
- {{T:patchharness-guard-thread-subprocess-escape}} **P2・新規**: `patchharness` の共有 checkout
  guard は `ContextVar` を読むので、別 thread と subprocess は stamp を継承せず guard を抜ける。
  本 wave で `ccbench == "write"` 要求へ強化したが、この抜け道は現行も同じで閉じていない。
- {{T:nproc-study-chain-metric-meaning}} **P2・新規**: `tools/pegasus/run_acceptance_nproc_study.py`
  の `real_repo_exclusive_chain_s` は、本 wave の land 後に「71 node の排他鎖」ではなく
  memo 4 件の残余になる。**旧意味で使ってはならない。** 同 file は
  `dev-wave-t1719-nproc-parity` 所有のため本 wave では触っていない。同 wave の land 後に追随する。
- {{T:ambient-output-runs-test-fix}} **P2・新規**: {{F:ambient-output-dir-red-in-fresh-worktree}}
  の恒久対応。fresh worktree を作る全 wave が踏む。対処案は (a) テストが必要な ignored dir を
  自分で作る、(b) 判定器を `git check-ignore` 基準へ変える、(c) 前提未充足なら明示 skip。
  **ユーザー裁定を仰ぐ** — 環境依存の赤を独断で恒久 skip へ落とさない。
- {{T:gen-s-queue-congestion}} **P3・新規**: `gen_S` の混雑 (実測 RUN 31 / QUE 16) により、
  受入や焦点走を計算ノードへ分散すると外側 wall が queue 待ちで伸びる。
  分散を増やす設計は混雑を測ってからでないと成立しない。
- {{T:dev-wave-mutation-doc-budget}} **P2・ユーザー裁定待ち**: 段 8 の自己改善が
  `docs/dev-wave/**` の byte 予算に阻まれた。`DW-M05` へ 2 文
  (「失敗 run の container を消さず `--resume` を使う。消すと git 登録だけ残り次の add が rc=125」
  「`--source-repo` は稼働 worktree でなく当該 commit を `main` に固定した独立 clone にする」)
  を足したところ **L1.5 が 9,858 bytes となり予算 9,566 bytes を 292 bytes 超過**した。
  予算の残余は実質ゼロである。**予算値の変更は自己改善の範囲外 (独立審査)** と契約が定めるため
  編集を戻した。**採るなら予算の再裁定が要る。**
  なお内容自体は失われていない — 独立 clone の判断は
  {{D:mutation-source-repo-independent-clone}} に、`--resume` の教訓は本エントリ本文に残した。
  前 wave (980) も同じ理由で `DW-M06` への追記を断念しており、**同じ壁に 2 回連続で当たっている。**
