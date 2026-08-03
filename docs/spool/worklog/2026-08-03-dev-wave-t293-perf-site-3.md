---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-03
wave: dev-wave-t293-perf-site
seq: 3
title: [T-293] perf_candidates は stale ではなかった — 計算ノード実測で 3 因を分離し恒久対応を裁定へ返す (コード + docs、branch worktree-dev-wave-t293-perf-site、受入全走 = Pegasus gen_S 計算ノード request 882024 で 5385 passed / 19 skipped、実装差分は probe 2 file のため変異 matrix は対象外)
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
- **段 8 自己改善: 候補 1 件を [T-328] の外出し枠へ相乗りさせる ([T-359] の既裁定に従う)。**
  **受入全走は統合 commit 後の clean tree で走らせる** — 未 commit の docs を載せたまま投げると、
  計算ノードは投入時点の worktree bytes を読むため、直後に直した版とずれて赤になる。本 wave で
  実際に 1 job (`881967`) を無駄にした。DW-O18 は cwd の規定しか持たず、この点を書いていない。
  **dev-wave docs は予算のため編集しない** (memory の既裁定どおり dev-wave 系へは移らない)
- 一次資料 = `output/insights/2026-08-03_t293-perf-site/` (README・逐語 10 本・裁定パッケージ)、
  実測 = `output/env/pegasus/t293-perf-site/0_881946.nqsv/` と `0_881960.nqsv/`

- **受入全走は 3 回走らせ、3 回目が緑である (`5263 passed / 19 skipped`、rc=0、request `881995`)。**
  1 回目 (`881962`) は `test_pilot_resume_rejects_launch_certificate_contamination[certificate-file]`
  が `repo_before == _real_output_snapshot()` で落ちた。本 wave の差分は `tools/pegasus/probes/` の
  新規 2 file だけで当該テストへ到達せず、**単独再走は 3 passed で緑**だったので、DW-O18 に従い
  フレークとして {{T:output-snapshot-test-flake}} に起票した。
  **2 回目 (`881967`) の赤は親の手順ミスである** — fragment の action 節順序を直す直前に投入したため、
  計算ノードが修正前の版を読んで `check_docs` の `worklog-action-order` に当たった。
  **未 commit の docs を載せたまま受入を走らせたのが原因**で、3 回目は commit 後の clean tree で走らせた

- **land は 5 度追い越された。** 1 度目は `dev_wave_land.py` が
  `rejected / tested main is not an ancestor of tested wave tip` を返した (受入全走の最中に
  main が `57f65b5` → `24a9478` へ進んだ)。DW-O23 に従い同 wave 内で巻き戻さず fresh context で
  再開し、既存 branch を再利用して `4c5e97c` を取り込んだが、**受入を投入し終える前に**
  23:15:59 の land で main が `055081e` へ進み、投入済みの走行 (request `882014`) は land に
  使えなくなった。`055081e` へ付け直した走行 (request `882015`、`5385 passed / 19 skipped`、
  rc=0、統合 commit `729728a`) は green だったが、その 5 分の最中の 23:30:25 に 3 度目の land が
  入った。`7ac6b2c` へ付け直した走行 (request `882020`、同じく `5385 passed / 19 skipped`、rc=0、
  統合 commit `65687c2`) も、その投入 3 秒前の 23:37:13 に 4 度目の land を受けた。
  `1348a66` へ付け直した走行 (request `882024`、同じく `5385 passed / 19 skipped`、rc=0、
  統合 commit `77d8aee`) も green だったが、実測を記録する commit を作っている最中の 23:47:47 に
  5 度目の land が入った
- **`882014` の打ち切りはログイン側の dispatch だけを止めたので、計算ノードの request は孤児になった。**
  ちょうど取り込んだ裁定 [T-367] が「走行中のジョブは殺さない」を採っており、`qdel` も
  auto mode の分類器が拒否したため実行していない。孤児は walltime で自然終了する
- **local main の land 間隔は実測で 6〜16 分である** (fold の commit 時刻 = 22:45:58 / 22:59:31 /
  23:09:34 / 23:15:59 / 23:30:25 / 23:37:13 / 23:47:47)。受入全走が約 5 分かかるため、並行 wave が
  4 本とユーザーの裁定セッションが同時に走る間は追い越しが常態化する
  ({{T:land-window-vs-acceptance}})

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

- {{T:land-window-vs-acceptance}} **P3・新規 (本エントリ)**:
  land は「main 取り込み → 受入全走 → `dev_wave_land.py`」を要求するが、受入全走は約 5 分かかり、
  2026-08-03 実測の local main の land 間隔は 6〜16 分である。並行 wave が 4 本走る間は追い越しが
  常態化し、本 wave は計 5 回やり直した (1 度は `rejected`、4 度は走行結果を捨てた)。
  直列化の方法 (land 待ち行列、lock 内での main 取り込み、受入の増分化) は防壁と裁定境界に
  触るため実装せず裁定へ返す。最も安い緩和 (受入投入の直前に main HEAD を再確認する) すら
  `docs/dev-wave/operations.md` が 8354/8400 bytes で余裕 46 bytes しかなく DW-O23 へ書けない
  ([T-313] の合計上限撤廃が実装されれば前提が変わる)
