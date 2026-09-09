---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2265-cohort2-perf6
seq: 1
title: [T-2265] cohort 2 の図に要る観測長 6 秒の performance 成果物 7 本を測った — 測定は完了、図は生成器の layout 検査が実データで落ちて未公開 (実測 + docs、branch worktree-dev-wave-t2265-cohort2-perf6)
---

## 本文

- **測定は完了し、図は出なかった。** 観測長 6 秒・schema v3・legacy 7 腕 x 3 workload x
  8 スレッドの performance 成果物を 7 本測り、7 本すべてが図の生成器の受理条件
  (168 点の完全格子・15 個の identity field が cohort 2 診断と一致) を満たすことを親が実測した。
  生成器の `load_inputs` も 7 本 + 診断を受理した。**しかし layout 検査が落ちた。**
  はみ出しは 1 ラベルだけで **5.85 px** (図幅 1452 px の 0.40%)、右下パネルの
  `cw-as-dyn-c2-p2` である。3 図のうち thread-axis と contrasts は通る。
  裁定が結果を見る前に固定した停止規則どおり、生成器を触らずに止めた。裁定は insight §5。
- **当初の provisional 裁定を段 4 で取り下げた。** 「companion 用の新規事前登録文書を投入前に
  commit する」を予定していたが、段 3 の 2 レンズが独立に「作っても成果物へ束縛できない」を
  示した。成果物の `prereg_sha256` は driver が常に既存の事前登録文書から作り、図の provenance も
  その値しか出さない。**発火しない保証を置くのは実装したふり**なので、insight の一部を
  前倒しで commit する形へ縮めた。束縛が外付けであることは insight に明記した。
- **段 3 の最重要所見: 測る 7 腕は cohort 2 の腕ではない。** legacy の `cw-as-dyn` は時間 cap が
  10240 µs、cohort 2 の 3 腕は 9223372036854775807 µs で、別の並行性制御設定である。
  この測定値を cohort 2 の局所 ITT の主判定の性能側の裏づけとして読んではならない。
- **段 6 の fix 3 巡はすべて scheduler が NQSV であることに由来した。**
  (1) `qstat -f` は `Request ID:` / `Current State` を返し PBS Pro の `job_state =` を出さない。
  終了 job は rc=0 のまま "does not exist" を返し一覧から消える。
  (2) `qsub` は素の job ID でなく `Request <id> submitted to queue: <q>.` を返す。
  最初の投入はこれで止まり、**job が queue に入ったのに台帳へ記録されなかった** (警告が発火し
  `qdel` で取り消せた。実害なし)。
  (3) 投入側の RequestID には `0:` 接頭辞が付かないが job 内の `PBS_JOBID` には付くので、
  期待 file 名がずれる (既存成果物 20 件で実測)。
  (4) NQSV の state 語彙検査が `qstat` の全行に掛かり、無関係な別 session の job が未知 state に
  なると監視が死ぬ。
  **子は 4 件すべてを偽 `qstat` / 偽 `qsub` で緑にしていた。** 実機の書式は親が測るまで
  誰も知らなかった。親は fix 後の待ち手を実機の `qstat` で 1 回走らせて確かめた。
- **生成器の test に穴がある。** cohort 2 の test は `make_diagnostic_figure` を実際に呼んで
  軸ラベルまで確認するが、**本物の `check_figure_layout` を 1 度も通していない**
  (同 file で `check_figure_layout` が現れるのは monkeypatch で差し替える test だけ)。
  実データで初めて出た。
- 親の手順ミス 1 件: 段 7 の base digest 取得のために main の作業木へ `cd` し、
  session の cwd が worktree の外へ移った。以後の git は `git -C` で木を明示して戻した。
- 工数: codex 子 9 本 (plan 1 / consult 2 / author 1 / review 2 / fix 3)。author 1 本は
  `f43_fragment` で不受理となり報告が途中で切れたが、実装 file 2 本は残っていたので親が
  現物を読んで段 6 のレビューへ回した。

## 次の一手差分

### 更新

- [T-2265] **P1**: 観測長 6 秒の performance 成果物 7 本を測り終えた
  (`986850`〜`986855`、`986857`、7 ノードに分散、wall 1218.6〜1222.4 秒)。
  7 本とも 168 点の完全格子で、15 個の identity field が cohort 2 診断と一致する。
  **残るのは図である。** 生成器の layout 検査が実データで落ちる —
  `make_diagnostic_figure` の右端ラベル `cw-as-dyn-c2-p2` が図の右端を 5.85 px はみ出す。
  3 図のうち thread-axis と contrasts は通る。**測定はやり直さなくてよい。**
  裁定は 2 択で、(A) `subplots_adjust` の `right` を下げ cohort 2 の layout 検査を test へ足す
  (既発表図の再生成結果が変わることを承知のうえで)、(B) 同 file を保持する T-2417 の wave の
  所有として直す。詳細は `output/insights/2026-09-09_t2265-cohort2-figures/README.md` §5。
  (a) 12 seed 別実行体と 24 スレッド条件の認証 (312 job) と
  (c) 解析器の限界の明示 (ring 容量 65,536 到達時に seq と summary の契約が壊れるが fail-closed)
  は変わらず残る。D1515 の再訪条件はなお未充足。
  base: 3fec8f4745d05019fda039a79774c31cb0fbbc0a4c3ea1492e977210ea3f125e
