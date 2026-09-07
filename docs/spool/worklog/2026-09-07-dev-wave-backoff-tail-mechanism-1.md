---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-backoff-tail-mechanism
seq: 1
title: 静的 backoff の tail 応答の機序を書いた — 待ちが集約時間の 7〜9 割で指数減衰ではないことを、記録済み測定だけで示した (docs + 図の生成器 + テスト、branch worktree-dev-wave-backoff-tail-mechanism、変異 matrix = baseline PASSED・KILLED 10・SURVIVED 0・MISMATCH 0・期待 node 完全一致)
---

## 本文

- **新しい測定は 1 件も行っていない** (規律 7)。材料は [T-2320] wave が 2026-09-07 に投入した
  job 979843 / 979844 / 979845 の report と、[T-2313] の 13 点較正である。
  すべて非認証 (trace-disabled、直列性の検査を通していない)。
- **図の設計を段 4 で変えた。** 段 2 のプランは 13 点の集約値を唯一の入力にしていて、
  作図規約 §1 (その場で再計算・孫引きしない) と §2 (反復があれば信頼区間) を満たせなかった。
  tail 6 点は rep 生値が repo 内にあるので、図をそこへ寄せた。
  `b ≤ 100 µs` の旧 7 点は rep 生値が repo に無く測り直さないので図の測定系列から外し、
  本文の解析にだけ使う。判断は {{D:tail-figure-uses-repo-rep-values-only}}。
- **主張の格を 2 段階弱めた。** 書けるのは記述的な会計までで、
  「機序を確定した」「B-10 を閉じた」「既存 7 点だけで tail が決まっていた」
  「別の劣化は現れない」は書かない。判断は {{D:backoff-tail-accounting-claim-scope}}。
- **段 3 の敵対相談 2 本が、親 brief の数値を 5 件訂正した。** 指数外挿との最大乖離は
  43 倍でなく balanced の 44.20 倍。待ちの占有率は「tail で 81〜92%」でなく b ≥ 150 全体で
  68.8〜93.4%。out-of-sample は測定 abort 率を条件に与えた再構成であって予測ではない。
  `representative_latency_ns` は `48e9/median_tps` の導出値なので並列度の独立な裏づけにならない。
  閉包候補は `α/f` の定数性が write-heavy の tail で 21% 破れている。
- **段 6 の敵対レビュー 2 本がどちらも NO-GO を返し、6 件の real 所見を出した。全件直した。**
  最も重いのは、**図の caption (非認証の 3 値と 6 つの但し書き) が PNG / PDF に 1 文字も
  描画されていなかった**こと。文字列は定義されていたが実 artist として足されておらず、
  さらにそれを検査する test が matplotlib の private 属性を見ていたため、
  **描画されていなくても通る恒真な検査**になっていた。
  **これは変異 matrix の外にあった偽の正例である** — 事前登録した 10 変異はすべて
  意図した test に殺されており、変異だけでは見つからなかった。
  残りは scope 外の workload 順序拒否 2 箇所 (削除)、作図規約 §5 の未展開略語 (展開)、
  in-sample の当てはめ値の `predicted_` という名前 (改名)、信頼区間の中心のずれ (非対称区間へ)。
- **親自身の裁定にも誤りが 1 件あった。** 段 4 に書いた「誤差 0.06% 以内」は
  balanced 500 µs が 0.0633% なので厳密には不成立で、`0.064% 以内` へ訂正した。
  レビュー A の独立検算が指摘したものである。
- **段 5 の実装子用に `.codex/worktrees/` へ別 worktree を作ったが、使えなかった。**
  背景 job の worktree 隔離が、そこへの一切の command (cd も pwd も) を拒否する。
  しかも一度 cd すると永続 shell がそこに取り残され、`EnterWorktree --path` で
  入り直すまで全 command が落ちた。単一実装単位だったので wave worktree で直接作業させた。
  作った worktree (branch `impl-dev-wave-backoff-tail-mechanism`、commit ゼロ、locked) は
  未使用のまま残っている。
- 受入は 2 回投入した。1 回目は入れ子 submodule (googletest) の未初期化で
  `preflight-submodule-ready` rc=2。規定の再帰初期化を通してから再投入した。

## 次の一手差分

### 新規

- {{T:backoff-abort-rate-power-law-mechanism}} **P2・新規**: 静的 backoff の tail で
  abort 率が冪則 (指数 −0.44〜−0.52) に従う理由は未確定である。
  走行密度への比例を仮定すると指数 −1/2 と山の位置が同時に出るが、
  `α/f` の定数性は write-heavy の tail で 21% 破れており、正確な比例則としては成立しない。
  切り分けには in-flight トランザクション数の直接観測が要り、診断ビルドが要る。
  新しい実行体を要するので同じ wave では走らせられない (F660)。
