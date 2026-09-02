---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2187-tuned-adaptive-baseline
seq: 1
title: 既定 adaptive を単独基準線に使っている箇所を差し替えた — 変異が「閉じたつもりの pin」を 1 件暴いた (コード + テスト + docs + insight、branch worktree-dev-wave-t2187-tuned-adaptive-baseline、変異 5/5 KILLED)
---

## 本文

- **ユーザー指示:** D1475 に従い、既存の比較・図・論文ストーリーのうち既定 adaptive を
  単独基準線に使っている箇所を洗い出して差し替える。差し替えた各箇所について旧基準線で書いた
  結論が変わるか変わらないかを 1 行ずつ明記する。**本題の差し替えだけで、仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外。**
- **着手後に前提が 2 つ変わった。** (a) 引数が指した D1475 は既に `D1505` / `D1506` が
  実質更新済みで、**新しい D を作る必要が無かった** (段 2 の子が指摘、親が現物で確認)。
  調整済みの正式値は D1506 の**刻み 1 µs / 更新間隔 2560 µs / 上限 1000 µs** であり、
  親 brief が書いた「上限 50 µs」は誤りだった (50 µs は上限 sweep の最良セルだが差は CI 内で、
  D1505 が上限を調整軸に数えないと決めている)。(b) 段 5 の直前に main が 10 commit 進み、
  **T-2187 の図 3 枚が着地していた**。その凍結図と生成器は label `stock adaptive` を使うので、
  計画していた `default adaptive` への改名を撤回した — 改名すると着地したばかりの凍結図が
  作図規約に反する状態になり、凍結物の bytes は直せない。
- **洗い出しは 5 件から 10 編集単位へ増えた。** 段 2 の plan が 3 件、段 3 の敵対 2 レーンが
  さらに 2 件を足した。差し替えの中心は生成器の**既定基準線を無 backoff 1 本へ狭める**ことで、
  呼称の変更だけでは D1506 を満たさない (「呼称を変えても既定 baseline のまま残る」と
  2 レーンが独立に指摘)。`stock-adaptive` は明示指定で今も描ける — D1506 は既定 adaptive を
  測ること自体を禁じていない。
- **段 2 が出した最大の提案を不採用にした。** 図 provenance の genome から label への対応は
  3 定数を開く patch の下で既定と調整済みを区別できない。plan はこれを 5 値同定へ広げる案を
  出したが、**その形の producer が実在しない** (既存 3 campaign の WAL に `BACKOFF_INCR_MILLI` は
  grep 実測 0 件) 上に、要求すると既定作図が全 campaign で止まるだけで調整済みの対照は
  1 本も増えない。ユーザーが scope 外とした仮想リスク向け gate に当たるので採らず、
  **限界として insight に記録した** — 将来この生成器へ調整済みの系列を流すなら、
  描く前に対応表を拡張しなければ `fig2_backoff_mechanism.png` と同じ誤 label 事故になる。
- **変異が「閉じたつもりの pin」を 1 件暴いた。** 敵対レビューは静的に
  「判定閾値を 3% から 20% 未満へ動かせばテストは同じ分岐のまま通る」と指摘し、
  1 回目の fix は `assert BETWEEN_RUN_CV == 0.03` という**定数の値の pin**で閉じたつもりになった。
  probe 走で `nf = BETWEEN_RUN_CV` を `nf = 0.19` に置き換える変異が**生存**した —
  fixture の +20% / +2% / -20% はいずれも 0.03 と 0.19 で同じ分岐へ落ちるからである。
  **定数の値を固定しても、その定数が判定に使われていることは固定されない。**
  2 回目の fix で 0.03 と 0.19 の間に落ちる +5% のケースを足し、本走で KILLED になった。
  実装・数式・定数の値・分岐条件は 1 行も変えていない。
- **変異走の経路を途中で変えた。** `tools/mutation_worktree.py` は rc=125
  「共有木の事後検査に失敗」で落ちた。真因は自分の編集ではなく、同ツールが
  **共有 primary worktree も観測対象**にしていることである。この計算機では他 wave が
  claude 81 / codex 40 プロセス動いており、6 分間 primary が静止する窓は取れない。
  DW-M05 が正本として指す `tools/mutation_harness.py` を隔離 worktree へ直接適用して通した。
- **子の実走はすべて rc=16 (dispatch infra) で、緑は親が実測した。** 実装子も fix 子 2 本も
  「実装済み・未実走」と正しく申告し、緑を偽らなかった。親の実測は変更前 baseline 87 件、
  変更したテスト 2 file の単独走 17 + 18、consumer 9 file の焦点走 181 passed / 9 skipped。
- **凍結物は 1 byte も変えていない。** `docs/paper-story` の各版、figures の png/pdf/provenance、
  `docs/phase3-main-experiment.md` (3 台帳が sha256 で pin)、b10 事前登録、s1-freeze。
  凍結スナップショットの訂正は、腐らない入口である `docs/paper-story/README.md` の
  stale 注記が担う。**その注記の対象は 2 箇所ではなく、fig2c の一般化が §2・§4・§6・§8 の
  4 箇所にあった** (敵対レビュー B の指摘、親が行番号で実測して節名へ直した)。
- 詳細は `output/insights/2026-09-02_default-adaptive-baseline-replacement.md`。
  変異台帳は同名 `-mutation/` に置いた。

## 次の一手差分

### 新規

- {{T:tuned-adaptive-as-drawn-control}} **P2・新規**: 調整済み adaptive を「呼称の限定」でなく
  **実際の対照として同じ図に並べる**。本 wave が達成したのは「既定 adaptive を単独の適応基準線として
  使わせない」ところまでで、旧 `linux-baremetal` の campaign 3 件には調整済みのセルが無く、
  Pegasus で測った値を旧環境の図へ混ぜてはならない (環境だけでなく CCBench の版・patch の有無・
  反復設計・集約方法も違う)。したがって新規計測が要る。
  **着手の前提条件が 2 つある。** (1) `orchestrator/tests/test_backoff_figure_provenance.py` の
  genome から label への対応 `("1","-1") → ("stock-adaptive","stock adaptive")` を、
  調整済みの系列を描く**前に**拡張すること — 拡張前に描くと調整済みの線に `stock adaptive` の
  label が付き、`fig2_backoff_mechanism.png` と同型の誤 label 事故になる。
  (2) 調整済みの値は trace-disabled のみで直列性の検査を通していないので、
  性能主張へ使うには [T-2189] の correctness 検査が要る (絶対規律 2)。
