---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-a6-read-heavy-cert
seq: 3
title: A-6 read-heavy certification を実走し indeterminate で記録した (コード + 実走、branch worktree-dev-wave-a6-read-heavy-cert)
---

## 本文

- ユーザー指示は「read-heavy (ycsb_rratio=95、fixed 2us) について A-2 と同じ正式 certification
  protocol を 1 workload 分だけ回す」。出所は `docs/paper-story/2026-09-02.md` §8 の A-6 (台帳 ID 未起票)。
- **投入は行い、判定は `indeterminate` で確定した。** attempt `a6-20260902a`、request
  `967525.nqsv`、Elapse 20S、driver_rc=2。read-heavy の correctness も performance も取れていない。
  論文 §8 の但し書き 2 は外れていない。一次資料は
  `output/insights/2026-09-02_paper-story-a6-certification/`。
- 止まった理由は {{F:a2-cert-online-fetchcontent}}。条件 gate の cmake configure が CCBench の
  `FetchContent_Populate(masstree)` で git clone を要し、計算ノードは直結の外部 network 不可
  (実測: `git ls-remote` rc=128、`Could not resolve host: github.com`)。同じ configure は
  ログインノードでは成功する。`docs/pegasus-runbook.md` は 2026-08-01 の実測でこの事実と
  「依存ソースはログインノードで pinned staging し `FETCHCONTENT_SOURCE_DIR_*` で渡す」運用を
  既に定めているが、A-2 / A-6 の certification 経路はこれに従っていない。
- 条件 gate は A-2 の実走 (2026-08-28、commit `639c1dba`) より後に driver 全体へ義務化されたもの
  (T-1999 / D1198) であり、**A-6 固有ではなく A-2 経路そのものが今日は計算ノードで走らない**。
  規律 2 により gate を緩めて通すことはしていない。
- 機構側で実装したのは {{D:a6-study-shape-map}} と {{D:a6-walltime-twelve-hours}}。
  段 3 の独立 2 レンズが「任意 N への一般化は A-6 という名前だけの別 policy を正式 proof chain へ
  通す」と挙げたため、study→shape の exact map と canonical 2 path の closed set に閉じた。
- 実走前に恒真だった防壁を 1 件閉じた ({{F:qstat-reqname-truncation-inert-guard}})。
  投入器の重複検出は A-2 導入時から一度も発火していなかった。
- 段 6 のレビュー 2 本が挙げた must-fix は、harness の `load_policy` 差し替えが `path` 引数を
  無視して `--policy` 伝播欠落を隠す件と、queue 状態検査が対象 queue の行に束縛されていない件。
  親の焦点走 (初回 6 failed / 150 passed) が test harness の `exit 96` 落下、実 `qstat` fixture の
  手書き置換、合成 `Args` の `policy` 欠落を出した。fix は 2 巡で閉じた。
- 変異 matrix: baseline PASSED、M1〜M6 が 6/6 KILLED、SURVIVED 0 / MISMATCH 0 / TIMEOUT 0。
  事前登録の訂正 2 件を erratum として残した。M3 は workload 数検査と cell 数検査が相互に支配して
  単独帰属が成立しないため両層同時変異へ再照準。M7 は対応する production 変異位置が存在せず
  (凍結値との比較が production に無い)、変異としては撤回し golden 回帰テストとして残した。
- 変異 probe 走では `tools/mutation_worktree.py` の共有木事後検査が rc=125 で失敗した。ledger 自体は
  完走しており、本 wave 中に local main へ 23 commit が着地している以上、他 session の churn に
  帰属する。本走は `tools/mutation_harness.py` を自 worktree に対して回した。
- 工数: codex 子 8 本 (plan 1、consult 2、author 1、review 2、fix 2)。model は全て `gpt-5.6-sol`、
  reasoning は `xhigh`。model call は plan 以降で合計 200 前後、実装子の wall は 1221 秒。
- 実装しなかった real 所見 4 件 (事前登録 policy SHA の proof chain 束縛、full v3 materializer の
  report 再導出、投入の永続 claim、PID 可視性 canary) は成果物の主張上限として insight に明記した。
  いずれも A-2 にも等しく存在する性質である。

## 次の一手差分

### 新規

- {{T:a2-cert-offline-dependency}} **P1・ユーザー裁定待ち**: A-2 / A-6 certification 経路の build を
  オフライン依存へ配線し直すか決める。永続 cache `/work/1/SFC/tanab/izanagi-thirdparty-cache` と
  helper `tools/pegasus/fetch_third_party.py` は既に在り `mocc_trace_pilot` / `silo_ladder_rung1` が
  使っているが、certification 経路は `run_campaign` 経由でビルドし、`run_campaign` は FetchContent の
  source dir 引数を持たない (`buildcache` 側には在る)。配線は共有 measurement pipeline
  (`run_campaign` → `pipeline.evaluate` → `buildcache`) への横断変更になり、全 driver の測定ビルドの
  configure argv を変える。これが決まるまで read-heavy の実測は取れない ({{F:a2-cert-online-fetchcontent}})。
