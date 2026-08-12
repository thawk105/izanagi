---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-l2-route
seq: 1
title: dev-wave の L2 経路を成立させ、裁定済み保留 11 項を収容した (docs + 契約、branch worktree-dev-wave-l2-route)
---

## 本文

- **L2 経路は「新規 L2 節を作る」ではなく「毎 wave 読むわけではない既存節を段 dispatch の
  U 行から外す」で成立した。** 層は入口の dispatch 表から機械導出され、U 行に一度も出ない
  登録済み節が L2 になる。`DW-O03` (防護パスを含む prompt)、`DW-O13` (gate 入力の実在)、
  `DW-M07` (fix 後 anchor) の 3 節は、本文の適用条件が既存の条件行 03 / 13 / 15 と一致し、
  条件が成立しない wave では読む必要がない。U 行から外すだけで L2 になり、L1.5 が 650 bytes 空いた。
  新規節も新規条件行も作らないため D271 の admission 3 条件は発火しない ({{D:l2-route-by-demotion}})。
- **収容できなかった項はゼロ。** 収容した 11 項は T-916 (c) = `DW-S01`、T-925 (2)(3) と
  T-911 (i) = `DW-O01`、T-934 (a) = 入口の読み込み契約、T-911 (ii) = `DW-O19`、
  T-139 Q5 の 3 件 = `DW-O01` / `DW-O02` / `DW-O05`、a12 控えの候補 1 = `DW-O02`、候補 2 = `DW-S04`。
- **T-139 Q5 は「既収容の項に包含される」という親 brief の前提が誤りだった。** 段 3 の敵対 2
  レンズが独立に指摘し、親が一次資料 (`dev-wave-jobs/handoff/dev-wave-t139-manifest-land2-s2.md` の
  「dev-wave 改善候補」1・2・5) に当たって独立 3 件と確定した。scope を 9 項から 11 項へ広げた。
  a12 控えの候補 3 (NFC 救済経路) は 2026-08-13 の rulings 第 7 束が「作らない」と裁定済みのため
  収容対象外とし、記録だけ残す。
- **親の docs 圧縮は 4 回 exact 契約を壊した。** 入口の `入力と開始` 節全体 pin、9 段状態機械
  項 9 の waiter consumer 行 pin、`CODEX_AUTHORING_STRUCTURE` の regex (行折り返しで
  `Codex \`role=author\`` が分断された)、`DW-S09` の helper 唯一経路 literal。いずれも
  `check_docs` が捕捉し、圧縮を撤回して別の原資へ差し替えた。**入口と core の圧縮は
  「意味等価」だけでなく「exact pin を跨がないか」を先に確認する必要がある。**
- **段 6 レビューは blocker 1 件を捕まえた。** T-911 (ii) を `DW-M07` へ置いたが、その読了 gate
  である条件 15 は「fix 後に変異を走らせる直前」だけで発火する。期待 node を直しての再走は
  fix を伴わないことがあり、その場合は一度も読まれない。条件 19「tracked file を一時変異する
  直前」で読む `DW-O19` へ移した。**義務の射程と、それを読ませる条件の射程は別に検証する。**
- レビューはほかに、圧縮による義務の弱化 2 件 (`DW-G05` の「放置した場合」欠落、
  `DW-S07` と入口の完了後条件が「行う」へ後退) を real と判定し、いずれも復元した。
- **L2 の節別余白の合算値 (6,765 bytes) は収容原資として扱わない。** L2 は節ごと 1,000 bytes の
  独立上限であり合計上限を持たない。両レンズが独立にこれを指摘した。
- **変異 matrix は 3/3 KILLED、SURVIVED 0、MISMATCH 0** (spec sha `3bedc861…`、
  tip `b70c7c09`、runner = `test_check_docs.py -rf -k "dev_wave_layer_budget or
  command_docs_guard_positive_controls or real_repo_clean or command_guard_case_registration"`)。
  1 走目 (spec sha `95596744…`) は 3 件とも MISMATCH = 超過検出で、観測集合は期待の真上位集合
  だった。`DW-M08` に従い初回を probe とし、完全集合 (4 node) を再導出して別 `--out` で再走した。
  probe の spec と結果は `/work/1/SFC/tanab/dev-wave-jobs/mut-out-l2route/` に保全した。
- **変異 harness の起動罠を 4 件実測した** — `--wrapper-attempt` は path でなく int (`--attempt-out`
  と対)、runner argv に `-rf` が無いと起動前 abort、起動前 abort でも使い捨て container が
  worktree 登録に残り次走の共有木事後検査を落とす、`--out` が `--scratch-root` と別 filesystem だと
  dispatch evidence の rename が cross-device で失敗する (結果 JSON は生成済みでも rc≠0)。
- **段 2 のプラン子は 1 本目を model call 上限 100 で失った** (1,035 秒・出力 0 bytes)。
  `tools/check_docs.py` を「関数名で探して読め」と書いたのが原因で、行番号表と実測値表を
  親が digest にして先渡しし、上限を 250 へ上げた 2 本目は完走した。本 wave が収容した
  T-925 (3) / T-139 Q5-a (`--max-*` は caller が上げてよい) と同型の事故である。
- **受入全走 (1 走目、tip `a7289002`) は 2 failed / 10297 passed / 65 skipped / 114.10 秒。**
  赤 2 件はいずれも本 wave の差分から到達しないファイルで、独立に外部由来と実測した。
  (1) `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
  は main 由来の既知赤。`validate_condition_freeze_at` の直呼びで `d1de13ad` 自身・`main`・本 wave
  `HEAD` の 3 点とも `[octopus-merge] d1de13ad` で RED と実測した (pytest 不要)。
  2026-08-13 01:05 JST のユーザー裁定により既知赤として land 可。
  (2) `test_codex_worker_launch.py::test_parallel_jobs_preserve_both_manifest_entries` は [T-1005] の
  非決定赤 (`codex_exit_code=-9`)。同 file の単独再走は **114 passed / rc=0** で再現しない。
  `DW-O18` に従い本 wave の差分へ帰属させない。
  なお単独再走の 1 回目は `--force-dispatch` 無しで rc=16 (bounded local scope の attest 不能) となり、
  テスト結果を得られなかった。親の焦点走にも dispatch 明示が要る。
- 親の実測 (rc は単独取得): `python3 tools/check_docs.py` rc=0、全史 provenance rc=0、
  focal 9 passed、command guard positive control 88 passed。
  変更後の予算は L1 = 10,615 / 10,625、L1.5 = 9,546 / 9,566、入口 = 9,498 / 9,500 (最長行 134 / 140)、
  `DW-O19` = 984 / 1,000。予算上限は 1 つも引き上げていない。入口 `:116-117` は byte 不変。

## 次の一手差分

### 完了

- [T-911] dev-wave の手順欠落 2 件を収容した。`--artifact-root` の事前作成は `DW-O01`、
  変異再走の `--out` 別 path は `DW-O19` へ置いた。親推奨 (c) の不採用どおり docs へ収容した。
  remaining: none
  base: f767c13a9a97cfc2467ff6f6b21a2a3298161bf45c2474e5459d6cba8b720d62
- [T-916] 裁定 (c) どおり分類文と実アンカー表の二重管理禁止を `DW-S01` へ収容した。
  remaining: none
  base: c4de878675d854ca661bc2e7ca2259354c8f11f40fccc5585e7cc6443b6a645b
- [T-925] 塞がっていた候補 (2)(3) を `DW-O01` へ収容した。個別承認は不要のまま終えた。
  remaining: none
  base: 12a38a31e66861c22d5270d3a9e724f6cabb91b253511992e15d9a7dd1ccfa8a
- [T-934] 裁定 (a) の流用条件を入口の読み込み契約へ収容した。原資は入口プローズの圧縮で作り、
  `:116-117` は削除していない。
  remaining: none
  base: 700ac44be7e1b124a2082e6ddc9d6a0c3399ffae11ee712e10bdd532f3537048
- [T-946] L2 空き枠経路で収容し、収容できなかった項はゼロ件だった。入口 `:116-117` の削除は
  再審査しない。
  remaining: none
  base: 71e2439b36bc81a81628a14d3392676bd57be66b7ef65daf3629b69ce9b85c6b

### 新規

- {{T:dev-wave-compression-pin-guard}} **P3・新規**: `docs/dev-wave/**` と入口の圧縮が exact pin を
  跨いだかを、圧縮前に機械で洗い出す手段がない。本 wave は 4 回踏んで `check_docs` の赤で気づいた。
  pin 一覧 (節全体 exact、literal、regex 構造) を 1 コマンドで列挙できれば圧縮の試行回数が減る。
  成果物影響 = 放置すると docs 予算の遣り繰りのたびに数回の赤と撤回が発生し、
  意味等価な圧縮まで巻き戻す判断ミスを誘う。
- {{T:mutation-harness-argv-preflight}} **P3・新規**: 変異 harness の起動前 abort 4 型
  (`--wrapper-attempt` の型、`-rf` 必須、container 残骸、`--out` と `--scratch-root` の
  filesystem 一致) はすべて起動後に判明する。`--plan-only` を argv 検証だけで通せるようにするか、
  4 条件を 1 箇所へまとめて事前検査したい。成果物影響 = 放置すると変異 1 巡ごとに
  数回の空投入が続き、受入 lease の窓を圧迫する。
