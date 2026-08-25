---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t525-holdout-binding
seq: 1
title: [T-525] holdout の完全条件を実行引数と報告側で束縛した (コード + テスト、branch worktree-dev-wave-t525-holdout-binding、変異 matrix = baseline PASSED・12/12 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **段 4 の親裁定は誤っていた。** 親は「実行 argv の値を完全条件と照合すれば穴は閉じる」と
  裁定したが、段 6 の敵対レビュー A が値照合だけでは閉じない経路を 2 本出し、親が原典で裏取りした。
  (1) gflags は flag 名の `-` を `_` へ置換して再探索する
  (`FlagRegistry::FindFlagLocked` の実装コメントに明記)。完全一致 argv の後ろへ
  `--ycsb-rmw=1` を足すと関門は別 key として無視し CCBench は `ycsb_rmw=1` で走る。
  保護 5 field すべてで成立する。(2) `TotalThreadNum = FLAGS_thread_num + FLAGS_batch_th_num`
  (`external/ccbench/cc/silo/util.cc:35`) のため `--batch_th_num=48` を足すと
  凍結 threads=48 のまま実 worker は 96 になる。敵対レビューを省いていれば
  「塞いだつもりの関門」を land させていた。
- 潰し方を個別対応から構造対応へ変えた。CCBench の direct flag を棚卸しすると条件を変えうるものは
  `batch_ratio` / `batch_tuples` / `ronly_ratio` / `ycsb_max_ope` など他にもあり、1 件ずつ拒否を足す
  設計は保たない。分類前の gflags 同等の名前正規化と、保護 run の **閉じた allowlist** の 2 段にした。
  allowlist は `clocks_per_us` と `extime` の 2 要素だけで、各要素に根拠コメントを付けた。
- 過剰拒否の不在は親が実測した。`ycsb_max_ope` が拒否対象に入るため確認したところ、
  `p3_autonomous_workload_trial._perf_for` は freeze の 3 key しか `PerfConfig.workload` へ渡さず、
  正式 holdout の argv は 7 本で `ycsb_max_ope` を含まない (あれは rr50 の正しさ検証経路で
  非保護 ratio のため allowlist の対象外)。
- **変異 matrix だけが中心シナリオの穴を掘り当てた** ({{F:mutation-only-central-scenario-gap}})。
  焦点走 1670 件緑と敵対レビュー 2 本が揃って見落とした。当初は単独変異の生存を
  masking と疑ったが、両層同時変異でも生存したためテスト集合の穴と確定した。
- **親が F540 の明文に違反した** ({{F:not-accepted-artifact-adopted-on-content-check}})。
  段 2 の不採用成果物を内容検査の緑だけで採用し、逸脱を自分で handoff へ書きながら先へ進んだ。
  F540 の手当て (別 `--job-id` で 1 回再投入) を実施して正規成果物へ差し替えた。
  段 3・4 の所見は成果物本文でなくソースへ当てて独立に裏取りしていたため裁定の根拠は変わらない。
- `evidence_status=invalid` の 3 つ目の型を診断し F540 へ supersede した。
  読取禁止行域を prompt へ書く回避で以後の子 6 本は全て正規採用された。
- 段 3 レビュー B は「値を名前付き定数へ分割する方式は形式上は検出器回避である」と指摘した。
  裁定が明示した方式であり freeze との exact 比較が補うが、評価はそのまま残す。
- 段 3 の両レンズが独立に「保存形式を変えるなら schema 世代交代が要り、旧 artifact を失効させるか
  二世代 reader を持つかの裁定が要る」と指摘したため、保存形式・schema 版・exact key 集合・
  canonical preimage を一切変えない範囲へ scope を確定し、残りを裁定パッケージへ回した。
- 子の工数: codex 12 本 (plan 2・consult 2・author 2・review 2・fix 3・再投入 1)。
  段 2 の 1 本目は不採用 (750 秒・model call 52)。他は全て `launcher_rc=0`。
- 変異 matrix は harness の dispatch 経路で M07 が 2 回連続で出力を取れず停止した。
  手元で同じ変異を当てると毎回きれいに 2 node 落ちたため、変異でなく捕捉側の失敗と判定した。
  local runner mode へ切り替えると今度は harness の node 列挙が通らず、dispatch へ戻した。
  最終巡は 12 件すべて実測の完全 node 集合で登録し KILLED になった。

## 次の一手差分

### 完了

- [T-525] holdout 束縛を完全条件へ広げ、実行 argv 側の関門と報告側 exact 述語を実装した。
  gflags 名前正規化と閉じた allowlist で別条件実行の経路を塞ぎ、
  中心シナリオの直接テストを追加した。受入 receipt の freeze 再錨付け・schema 世代交代・
  正式起動配線・C01 述語は scope 外として裁定パッケージへ回した。
  remaining: none
  base: 8c17e0f9966477006f502c32ceab08aaf95a7c428b9aab25cf24ce664aeee53b

### 新規

- {{T:holdout-receipt-freeze-anchor}} **P2・新規 (段 6 レビュー A/B blocker、ユーザー裁定待ち)**:
  `orchestrator/campaign/s8c_acceptance_receipt.py` は freeze を一切読まない。
  nested condition と cell と descriptor を同じ誤値で自己整合させた receipt を
  H1 として検証済みに出来る。standalone verifier を構造 verifier のまま置くか、
  ratified legacy freeze を再導出する条件 verifier へ昇格するかを裁定する。
  昇格するなら {{T:holdout-schema-generation-cutover}} が前提になる。
- {{T:holdout-schema-generation-cutover}} **P2・新規 (段 6 レビュー A/B must-fix、ユーザー裁定待ち)**:
  serialized binding へ freeze SHA と完全条件を載せるには report / run-start / receipt を
  v4 へ上げる必要がある。旧 artifact を legacy として読み続けるか明示的に失効させるかは
  ユーザー裁定事項。[T-525] は保存形式を一切変えない範囲で着地させた。
- {{T:formal-launch-admission-wiring}} **P2・新規 (段 6 レビュー A must-fix)**:
  `p3_autonomous_workload_trial._preflight_workload_profile` が正式起動を無条件拒否し、
  かつ `orchestrator/campaign/loop.py` に `holdout_observation_admission` が 0 件のため
  (`pipeline.py` には 7 件)、拒否を外しても token が `pipeline.evaluate` へ届かない。
  binding / report / 受入層の関門は production で現在発火しない。[T-527] と歩調を合わせる。
- {{T:c01-scale-literal-predicate}} **P3・新規 (段 3 レビュー B must-fix)**:
  `s8c_preregistration_evidence.py` の C01 は p3 の 3 関数の AST に整数リテラル
  `1_000_000` と `48` が直接現れることを要求する。二重の真実を消す素直な改善が
  この述語を落とす。リテラルを残し続けるか、shared condition constructor の
  到達性検査へ更新するかを裁定する。[T-525] はリテラルを残した。
- {{T:dw-o01-launcher-rc-budget}} **P3・新規 (段 8 で予算に阻まれた、ユーザー裁定待ち)**:
  `DW-O01` の「採用は `check_codex_output.py` の rc=0」は一文だけ読むと十分条件に読め、
  本 wave の親はそれで launcher の赤を迂回した。`launcher_rc=0` も必須と追記したいが
  `docs/dev-wave/**` の L1.5 予算が満杯で、この 1 文だけで 9653 bytes > 予算 9566 になる。
  安全義務を削って空きを作ることは自己改善契約が禁じる。予算値を上げるか、
  同 L1.5 集合の別箇所を意味等価に縮約して空きを作るかを裁定する。
- {{T:jsonl-splitlines-u2028-hardening}} **P3・新規**:
  `tools/codex_worker_launch.py` は JSONL を `str.splitlines()` で切る (6 箇所) ため、
  子が読んだ行に生の U+2028 / U+2029 があると event 行が割れて成果物が全損する
  (F540 supersede)。分割を `split("\n")` へ変えれば現在の 5 file と将来の混入を一度に閉じる。
  tool の出力契約に触れるため独立審査とする。
