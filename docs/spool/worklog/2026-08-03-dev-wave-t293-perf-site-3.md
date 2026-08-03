---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-03
wave: dev-wave-t293-perf-site
seq: 3
title: "[T-293] perf_candidates は stale ではなかった — 計算ノード実測で 3 因を分離し恒久対応を裁定へ返す (コード + docs、branch worktree-dev-wave-t293-perf-site)"
---

## 本文

- **[T-293] の起票時の前提が実測で覆った。** 「`perf_candidates` が stale で、指す 2 本の perf は
  存在しない」ではなく、**独立した 3 因の重なり**である。値の書き換えでは 1 つも解けない
  - **候補 2 本は計算ノードに実在し、実際に動く** — `perf --version` は
    `perf version 5.15.178` / `5.15.143`、production と同じ smoke argv は **rc=0 で実カウンタ値**を返す
  - **それでも実物の `_executable` は解決に失敗する** (`required executable unavailable: perf`)。
    候補 path は計算ノードでは **symlink** で、`_executable` は symlink を拒むためである。
    shell 側 (`t126_qualification.sh`) は `[[ -x ]]` で通る —
    **同じ設定に 2 つの受理集合がある** ({{F:python-and-shell-executable-acceptance-diverge}})
  - **`prepare_toolchain` は perf に到達しない。** `gcc-13` が両サイトに無く
    **`failure_stage: "cc"`** で落ちる。perf を直しても qualification は動かない
- **ログインノードと計算ノードの linux-tools 版集合は互いに素である** — login (pegasus02) は
  `101/136/173` で候補は不在、計算ノードは `100/135` の 2 つだけ。runbook §1 の「全 node 同構成」
  前提は、この package 集合については成り立たない。`perf_event_paranoid` も login 4 / 計算 0
- **恒久対応は実装せず裁定へ返した。** identity (受理集合) の変更にあたり D96 手続である。
  択一と代償は `output/insights/2026-08-03_t293-perf-site/adjudication-package.md`。
  **親の推奨は (a) 何もしない を既定とし、着手するなら (d) compiler の不在 → (b) symlink 拒否の
  見直し の順**。値を広げる案 (e) は覆った前提の上に立ち、凍結証拠 2 テストを赤にして identity を
  変える代償を払って 3 因のうち 1 つも解けないので推奨しない
- **実損は現時点で 0 である** — `toolchain-manifest.json` / `submission-intent.json` /
  `series-identity.json` は repo 内に 0 件で、この経路は一度も完走した実績がない
- **段 6 は 3 度 NO-GO で fix 4 巡。**敵対レビュー 2 レンズ + 焦点再レビューが所見 14 + 新規 3 を出し、
  親は全件 real と裁定した。当初の変異事前登録 (C1 / M1) は撤回し、同一 run 内の両側 control へ
  差し替えた ({{D:two-sided-control-for-gateless-measurement}})。gate もテストも新設しないため
  **変異 matrix は対象外**であり、代わりに受理述語 5 条件を親が照合した
- **fail-closed が初回の実走でそのまま効いた。** 1 回目 (request `881946`) は計算ノードの既定
  `python3` が oneAPI 版 (3.10 未満) で orchestrator を import できず
  ({{F:compute-node-default-python-is-oneapi}})、`ok:false` / rc=3 で停止した。
  **レビュー A 所見 1 (測定器の故障と正当な否定結果の混同) を直していなければ、この走行は
  `ok:true` かつ `resolved:false` を返し「計算ノードでも候補は使えない」と誤結論していた**
- **投入前に親がログインノードで 1 件潰した。** 正の control に `sys.executable` を使うと必ず失敗する
  — `/usr/bin/python3` は symlink で `_executable` に拒否される。実物の `_executable` で確認して
  `Path(sys.executable).resolve()` へ直した。潰していなければ計算ノードの枠を測定結果なしで消費していた
- 実測は **2 標本** (bnode009 / bnode005) に限定し、gen_S 全 bnode へ一般化しない。probe 自身が
  `sample_scope` に同じ限定を書いている
- エージェント工数: 親 1、子 6 (実装 1 / 敵対レビュー 2 / 焦点再レビュー 1 / fix 4 は 4 回だが
  うち 2 回は 1 点修正)。計算ノード job 3 本 (`881946` probe 1 回目 / `881960` probe 2 回目 /
  `881962` 受入全走)
- 一次資料 = `output/insights/2026-08-03_t293-perf-site/` (README・逐語 10 本・裁定パッケージ)、
  実測 = `output/env/pegasus/t293-perf-site/0_881946.nqsv/` と `0_881960.nqsv/`

- **受入全走の 1 回目で 1 件の赤が出たが、実装差分に帰属しない。**
  `test_pilot_resume_rejects_launch_certificate_contamination[certificate-file]` が
  `repo_before == _real_output_snapshot()` で落ちた。本 wave の差分は
  `tools/pegasus/probes/` の新規 2 file だけで当該テストへ到達しない。**単独再走は 3 passed で緑**
  だったので、DW-O18 に従いフレークとして {{T:output-snapshot-test-flake}} に起票し、
  受入は再走した

## 次の一手差分

### 更新

- [T-293] **P2・本エントリで実測完了 ((本エントリ))**: 「まず計算ノード側の実測を取る」を完了した。
  **起票時の前提 (値が stale) は誤りで、3 因 (login に候補が無い / 候補が symlink で `_executable` が
  拒否する / `gcc-13` 不在で `cc` が先に落ちる) の重なりである。** 恒久対応は D96 手続として
  ユーザー裁定へ返した — 択一と代償は
  `output/insights/2026-08-03_t293-perf-site/adjudication-package.md`。
  **親の推奨は (a) 何もしない を既定とし、着手するなら (d) → (b) の順。(e) 値を広げる案は推奨しない。**
  裁定が出るまで本 ID は開いておく
  base: a176582ac7f3b284813baac3c6372d8793c35dd720f7d88392880a466c9f828f

### 新規

- {{T:output-snapshot-test-flake}} **P3・新規 (本エントリ)**:
  `test_pilot_resume_rejects_launch_certificate_contamination` が実 `output/` ツリーの
  before/after スナップショット一致を検査するため、**全走 (xdist 多並列) では他 worker や
  dispatch harness の書き込みと競合して落ちうる**。2026-08-03 の受入全走 1 回目で実際に落ち、
  単独再走 (3 passed) では再現しなかった。実 `output/` を触る検査を並列全走で安定させる方法
  (専用 tmp ツリーへの隔離、または snapshot 対象の限定) を決める必要がある。
  本 wave では観測のみで手を入れていない
