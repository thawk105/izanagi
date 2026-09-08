---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2418-static-backoff-explore
seq: 1
title: [T-2418] 静的 backoff の右側 3 点を探索走 t2418-explore として測れるようにし、3 workload へ投入した — 凍結格子には触れず、先例と同じ強さの正しさ検査を付けた (コード + テスト + 投入 + insight、branch worktree-dev-wave-t2418-static-backoff-explore、変異 14/15 KILLED + 等価変異 1 件 SURVIVED・期待 node 完全一致)
---

## 本文

- **依頼が名指しした機構の所在は正確でなかった。** 引数は機構を `orchestrator/campaign/backoff_sweep.py`
  と書いていたが、同 file の格子は生の `BACKOFF_FIXED` を渡すため 1000 以上を表現できない。
  1000 超の符号化と拡張格子は `orchestrator/campaign/backoff_extended_sweep.py` にある。
  実装はこちらへ入れた。凍結格子 `EXTENDED_SWEEP_US` には触れていない。
- **裁定の土台にしたのは先例 `t2266-tail` の実走記録である** (`output/insights/2026-09-07_t2266-tail-measurement/`)。
  そこから (a) 符号化の高域枝は認証済み格子の上端 1000 が既に発火させている、(b) 関門の既知欠陥は
  修正済み、(c) 恒真テストのせいで report 段が 3 job とも止まった事故、(d) 8 genome で 11 分という
  時間実績、の 4 点を取った。(c) は変異 m13 として再発検査に入れた。
- **敵対レビューの must-fix 2 件はどちらも real で採用した。** 1 件は事前登録した変異 m12 が
  生存していたこと (成果物 stem の照合が無い)、もう 1 件は裁定した meaning witness の限定が
  成果物側に載っていなかったこと。fix 後の変異本走でどちらも KILLED を確認した。
- **不採用にした nit は 3 件。** m13 の登録位置 (親が変異 spec 側で再照準した)、positive assert の
  冗長、共有 helper の例外文言。焦点再レビューで「親裁定どおり未変更」を確認した。
- **受入は 4 回目で緑になった。** 1 回目は受入所要時間台帳の網羅率が 89.979689% で閾値 90% を割り、
  本 wave 帰属と算術で確かめた (F902 へ再発として記録)。
  2 回目は台帳を正本 producer で更新した直後に**別 wave が同一更新を main へ着地させ**、
  merge guard が `owned-path-overlap` で正しく止めた。3 回目は取り込み直後に main が 11 commit
  進む競走で `postcheck` 停止。4 回目が `child-green` (22116 passed / 68 skipped)。
- **台帳 commit は取り下げた。** main 側の台帳が 22123 node へ更新されて網羅率が約 99.9% になり、
  本 wave の 8 node が未登録でも閾値を大きく上回る。一方、自分の更新を残したまま main を
  取り込むと 3-way merge で 56 か所衝突する (`git merge-file` で実測)。閾値は下げていない。
- **手順違反を 1 件やった。** 段 5/6 の子を投入する直前の起動 gate が「submodule 未初期化」で
  非 0 を返したのに、同じコマンドで子を起動してしまった。子は即座に停止し、初期化して gate を
  通してから別 job-id で投入し直した。gate の判定と投入は必ず別の tool call に分ける。
- **背景の待ち手がこの環境で複数回空振りした。** `until` ループも `tail --pid` も、対象が生きて
  いるのに即座に戻った回がある。生存は毎回 `ps` で実測して判断した。
- **段 8 は文書変更なしで閉じた。** 候補は「起動時の編集面重複検査が実用にならない」1 件。
  worktree 全数 (202 本) の `git status` は実測 65 分かかり起動を実質止める。対象 file 名指しの
  blob 照合は古い commit に固定された submit-tree が大量に偽陽性になる (実測 639 件中、真の
  稼働中衝突はゼロ)。routing 先の `DW-O20` は 989 / 1000 bytes で余地が 11 bytes しかなく、
  安全義務を削らずには収容できないため D782 の手順で閉じた。予算引き上げには至っていない。
- エージェント工数: Codex 子 9 本 (plan 1・consult 2・author 1・review 2・fix 1・focus 1・
  ledger author 1)、model call 計 165、wall-clock 合計約 5773 秒。すべて `gpt-5.6-sol` @ `xhigh`。
- **探索の結果、9999 マイクロ秒までの範囲に飽和は現れなかった。** 3 workload すべてで abort 率が
  単調に下がり続け (2000→9999 でおおむね 2.3〜2.8 倍の低下)、同じ区間で throughput も
  0.49〜0.58 倍へ落ちる。この領域では abort 抑制の追加分を throughput の低下がそのまま買っている。
  変動係数は全点 0.7% 未満。値は insight §12。D1813 の第 2 段はこの事実を踏まえて事前登録する。
- 設計判断は {{D:t2418-explore-run-kind}}。一次資料は
  `output/insights/2026-09-09_t2418-backoff-static-explore/`。

## 次の一手差分

### 完了

- [T-2418] 探索走 `t2418-explore` を実装し、固定 SHA
  `c49cdca1d40454ad006a6b583c61703b14dedd56` の detached submit-tree から 3 workload へ投入し、
  3 本とも `status=complete` で完走した (request 986597 / 986598 / 986599、出力親
  `/work/1/SFC/tanab/b10-backoff-grid-t2418-explore/`)。abort 率は 3 workload すべてで
  9999 マイクロ秒まで単調に下がり続け、**飽和は現れなかった**。値と observation は
  `output/insights/2026-09-09_t2418-backoff-static-explore/` §12。本格格子と停止基準は
  D1813 のとおり本 wave では凍結しておらず、{{T:t2418-formal-grid-preregistration}} が持つ。
  remaining: none
  base: cf61353f3b3dceb6530ff4cc9e54c9c4328b50096fa1fb3adef628d169898591

### 新規

- {{T:t2418-formal-grid-preregistration}} **P1・新規**: D1813 第 2 段。探索走の結果を見た後・
  本格 cohort の投入前に、静的 backoff 右側の本格格子と停止基準 (飽和判定) を事前登録して凍結する。
  探索値は正式標本へ混ぜない。
- {{T:b10-explore-scope-boundary-rulings}} **P2・ユーザー裁定待ち**: [T-2418] が scope 外として
  返した 4 件。(1) 正値 `BACKOFF_FIXED` の pointwise meaning witness を確立する gate の新設
  (現状は探索走に限らず既存 sweep 全体が `unestablished`)、(2) B-10 job 本体へ driver・patch・
  `pin.py`・condition gate の working bytes を HEAD へ拘束する検査の追加 (現状は job script の
  sha256 だけ)、(3) 既存の正式 consumer へ `completion["run_kind"] == "extended"` を必須化する案、
  (4) runbook の `IZANAGI_EXPLORATION_OUTPUT_ROOT` が指す「exploration campaign」と D1813 の
  「探索」が別語であることの整理。いずれも既存の正式系列と共通の性質で、探索走に固有の弱体化ではない。
