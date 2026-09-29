---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-vhash-eval-prereg
seq: 1
title: VHash 論文の評価計画を事前登録の草稿として置く (docs のみ、VHash 並行 wave md_12、branch dev-wave-vhash-eval-prereg)
---

## 本文

- **依頼 (ユーザー依頼により親セッションが作成した並行 wave の投げ文 md_12):** 計測を本格的に始める前に、仮説 H1〜H6 ごとに何と何を比べ、何が出たら何と言うかを
  結果を見る前に固め、正しさの門・統計・計算時間の見積り・「読み取りの後に待つ tx には効かない」限界の示し方を書く。docs だけで計測はしない。
  投げ文の本体は repo の外 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_12.txt`、job dir に逐語の写し)。
- **成果:** `docs/vhash-evaluation-preregistration-draft.md` (草稿 v0、未発効) と `docs/README.md` の地図の 1 行。置き場と主な設計は {{D:vhash-eval-prereg-draft}}。
  構成を 3 因子 (配置・発火したときの行動・GC への反映) で定義し、F と G を論理 K 境界の上と hot の上の 2 通りにした。主要な判定 20 個、1 job 内の
  対の round n = 14、順序統計量の区間、Bonferroni。試算は合計 12.76 node 時間 (1 走行 5 秒・build 60 秒の仮定) から 52.47 node 時間 (30 秒・180 秒の仮定)
  で、S1 探索・S1 確認・S3 はどちらの仮定でも単独で 2 node 時間を超える。発効の前に md_11 の実測単価で計算し直し、段ごとにユーザー確認を取る。
- **起草時に分かった事実 (pin C `68106660` の checkout を見た範囲):** Cicada の `batch_*` 引数は表示・thread 数の合計・結果表示への受け渡しにしか現れず、
  長い tx を生成する処理を確認できなかった。読み取り後の待機は compile 時のマクロ `WORKER1_INSERT_DELAY_RPHASE` (thread 1、commit の冒頭) だけで、
  遅延量のマクロ `WORKER1_INSERT_DELAY_RPHASE_US` の定義は木に見当たらない (build はしていない)。長い tx の生成器は評価の前提 (草稿 §11 の P5) になる。
  md_11 の投げ文も長い tx の 2 型を較正の対象に挙げているので、同じ前提に当たる。
- **段 6 の read-only レビュー (codex gpt-6-sol、13 call・約 204 秒):** NO-GO、must-fix 7・nit 4。親は全件 real と裁定して改めた。主なもの:
  探索段 (n = 3) に 95% 区間を主張していた (最も広い区間でも被覆 0.75)、H5 の「両単独構成を上回る」を相乗効果の判定にしていた (A=100・B=110・C=110・D=115 が反例)、
  W-wait で「待ちの間の試行 0 なら保持は減らない」と予測していた (待ちに入る前の前進で E は保持を減らしうる)、門の走行数 (120 組) を見積りが 50 と数えていた、
  H6 の E 対 A が「1 因子だけ違う」の約束と矛盾していた、x_L が未定義だった、`batch_max_ope` の用途を狭く書いていた。
  焦点再レビュー (6 call・約 118 秒) は GO で、全所見 closed、派生値の再計算一致。残った nit 2 件 (表の見出しの重複、撤回済みの述語への参照) も直した。
  レビューの原文は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-eval-prereg/` の `s6-review.md`・`s6-focus.md`。
- **統計の文の反例 (起草時に自分で作って書かなかった文):** 「2 node の両方で同じ向きなら共通の偶然に強い」「A_best を最大の中央値で選ぶのは E に不利な向きにしか偏らない」など。草稿 §8.8 に残した。
- **wave の運用:** EnterWorktree は name 形が filter driver のエラー、path 形が worktree 一覧の 10 秒 timeout で失敗し、手動の `git worktree add` (混雑で約 21 分) と
  絶対 path の作業で進めた。submodule 初期化は 1 回目が一過性の I/O 失敗 (rc=1)、同じ引数の再実行で rc=0。開始 gate は fresh で rc=0。
  段 2・3 は軽量版の既定で省いた。実装面の差分が無いので変異 matrix は免除 (DW-S04)。
- **受入 1 回目 (tested main `3bf2d0a16`、post-claim merge 後の tip `f8593c7a3`) は rc=70、赤 11 件で、すべて `orchestrator/tests/test_dev_wave_cleanup.py` の
  remove-child 系だった。** 9 件は本文が `occupancy result is indeterminate or inconsistent; attempts=3 retry_count=2` で、issue は
  `{"error":"missing","source":"cwd"}` (走査中に cwd を読めなかった pid)。残る 2 件は `assert [] == [True]` (部分撤去の記録が空) で、本文だけでは同じ原因と言い切れない。
  failures 台帳の occupancy 走査の不定 (docs のみの wave でも走ごとに別 node で落ちる) と同じ型と判断した。本 wave の差分は docs と `docs/spool/**` だけで、
  `tools/dev_wave_cleanup.py` と占有検査に届く経路は無い (非帰属)。同じ tip でその file を単独再走したら 201 passed / rc=0 で非再現だったので、
  受入を 1 回だけやり直す (DW-O18)。受入 2 回目はこの追記の commit の後に行う (記録の時点では未実施)。
- 親は計算ノードを使っていない (計測なし)。

## 次の一手差分

### 新規

- {{T:vhash-eval-prereg-activate}} **P2・新規**: VHash 論文の評価計画 (`docs/vhash-evaluation-preregistration-draft.md`、草稿) を発効させる。
  草稿 §11 の前提 (md_11 の調整済み Cicada・between-run floor・1 走行と build の実測単価、構成 B〜G の inert patch と門、新しい経路ごとの壊した variant、
  長い tx の生成器、計器、E の GC 安全の根拠、基盤の欠陥の有無、pin) が揃ってから、実測単価で段ごとの node 時間を計算し直し、段ごとにユーザーの確認を得て
  日付付きの決定で発効させる。発効までは本計画の計測・計算投入をしない。設計の根拠は {{D:vhash-eval-prereg-draft}}。
