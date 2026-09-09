---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-t2535-certify-offline-fetch
seq: 1
title: [T-2535] 認定較正 job へ offline の FetchContent 供給を配線した — 非 silo の較正 record が初めて 1 件出た (コード + 実測 + docs、branch worktree-dev-wave-t2535-certify-offline-fetch、変異 9/9 KILLED・期待 node 完全一致)
---

## 本文

- **較正 record は出た。** request `989271.nqsv` (host `bnode020`、Elapse 302 秒、`calibrate_rc=0`)。
  protocol `mocc`、quality `accepted`、`calibration-449d0ad22f13e366.json` として publish 済み。
  詳細と一次資料は `output/insights/2026-09-10_t2535-certify-offline-fetch/`。
- 設計判断は {{D:certify-offline-fetchcontent-supply}}。
- **段 1 brief の前提が 1 つ実測で覆った。** 「永続 cache は `fetch_third_party.py verify` が
  rc=0 だから pristine」は成り立たない。同 verify は既定で ignored artifact を検査せず、
  実際に cache の masstree には ignored な生成物が 71 件あった。hydrate 済み staging は 0 件。
  段 2 と段 3 が独立に指摘し、親が実測して撤回した。
- **段 3 レンズ A が段 2 案の負例の設計欠陥を出した。** 複製先を `<FETCHCONTENT_BASE_DIR>/<name>-src`
  に置くと、`SOURCE_DIR` override を 1 つ落としても CMake の既定命名が複製を拾って configure が通る。
  「override が効いている」ことを示す負例が baseline から緑になる。複製先 root と base dir を
  分ける形へ裁定で変更し、分離した実装と結合した対照を実 CMake で両方走らせて差を示した。
- **段 6 レンズ B が投入前に blocker を出した。** 新設の verifier 呼出しが裸の `python3` で、
  計算ノードの既定 3.9 では import 自体が落ちる構成だった。F500 の再発として記録した。
- **段 6 レンズ A が「テストが production の関数を実行していない」を出した。** 条件関門への転送検査が
  テスト側の写しを観測しており、production の slice 幅を変える変異を検出できなかった。
  production の関数本体と configure 起動行を実際に走らせる形へ直した。
- **1 回目の投入 (`989232.nqsv`) は親の操作ミスで止まった。** 投入後に `docs/spool/` の fragment を
  書いたため、job 冒頭の clean 再照合が `source_identity` で拒否した。job の検査は `output/` を
  除外するので、投入中に書いてよいのは `output/` 配下だけである。実装の問題ではない。
- **親が provenance の全史監査に 300 秒の timeout を掛けて orphan hold を作った。** 監査は計算ノードへ
  dispatch するため 300 秒では足りない。hold は 2 箇所にあり、`qstat` の行頭照合で終端を確認してから
  両方を消した。以後この監査には長い timeout を掛ける。
- **背景 job の完了通知が、実際には走行中の command について複数回先行して出た。** 待ち手・成果物・
  process の現物で毎回検算したため誤って先へ進むことはなかったが、通知だけを完了判定にしてはならない。
- 段 2 プラン 1 本、段 3 敵対相談 2 本、段 5 実装子 1 本、段 6 敵対レビュー 2 本、段 6 fix 子 1 本を使った。
  段 5 の初回投入は `--reasoning` が段 5 / 6 で指定できないため argv 拒否で子が起動せず、
  `.done` を再利用せずに再投入した。以後 `dev_wave_codex.py` は投入前に必ず `--dry-run` する。
- 子は pytest を実走できない。テストの実走と計算ノードへの投入はすべて親が行った。

## 次の一手差分

### 完了

- [T-2535] 認定経路へ offline の FetchContent 供給を配線し、計算ノードで較正 record を 1 件生産した
  (request 989271.nqsv、mocc、quality accepted)。silo の認定が条件関門で止まる件は [T-2534] の所有で、
  本項の射程外である。
  remaining: none
  base: c5ef85812c24054a9736134e81bc9e789547b3eb117d5594380f62a4bf895139

### 新規

- {{T:certify-walltime-formula-refreeze}} **P2・新規**: 認定 job の walltime 式を再凍結する。
  現在 3 通り食い違う — job 冒頭 comment は条件関門込みで 6910、receipt の `frozen_required_s` は
  関門抜きで 6610、各 command の `timeout` の直列和は mocc で 7870。PBS 要求は 7200 秒である。
  本 wave はこの不整合を作っていないので式を 1 byte も変えなかったが、
  copy と pristine 検査の上限 480 秒がその上に乗った。式・`calibration_v1.json` の
  `certify_walltime_s`・PBS directive・凍結式を検査するテストを同じ wave で動かす必要がある。
- {{T:certify-receipt-third-party-provenance}} **P2・新規**: 認定 receipt が第三者依存の pin を
  記録しない。`ccbench.build_argv` に入るのは job 終了後に消える一時 path だけで、
  masstree / mimalloc / googletest の commit は 1 つも残らない。`pinned_clean=True` が
  CCBench checkout だけを指すのか compiler 入力全体を指すのかも未定義である。
  どちらの意味を採るか決め、採った意味に合う field を receipt schema へ足すかを裁定する。
- {{T:certify-repo-root-pbs-binding}} **P2・新規**: `submit_certify.sh` の `--repo-root` と
  job 側の `PBS_O_WORKDIR` が束縛されていない。repo 外の cwd から投入すると、submit が検査した木と
  job が実行する木が別になりうる。本 wave は運用前提 (repo root から投入する) で凌いだ。
