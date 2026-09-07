---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t583-qsub-oe
seq: 1
title: [T-583] qsub の scheduler 出力を repo 外へ向けた — 封じ込め gate は作らず argv 実走検査の負例で守る (コード + テスト + insight、branch worktree-dev-wave-t583-qsub-oe、変異 6/6 KILLED)
---

## 本文

D1291 の実装。`tools/pegasus/submit_certify.sh` の qsub 引数へ `-o` / `-e` を足し、返り先を
共有 git dir の 2 つ上に置いた `izanagi-job-evidence/calibration-certify` 配下の nonce 付き
file path にした。追加は 6 行で、同 script の他の挙動は変えていない。一次資料は
`output/insights/2026-09-08_t583-qsub-scheduler-output/README.md`。

**段 2 と段 3 レンズ B が提案した封じ込め gate (返り先が repo 内なら rc=2) を、親が不採用に
裁定した。** 理由は 3 つ。(1) D1291 の「引数 1 箇所」と依頼引数の「仮想リスク向け gate は
scope 外」に抵触する。(2) レンズ B が「負例は恒真でない」と示した根拠の変異 2 件は、その
gate が在って初めて存在する変異であり、gate を足し gate を撃つ負例を足しその負例が gate を
守るから gate が要る、という循環になっていた。(3) gate が守る状態が実環境で到達不能である。
段 3 レンズ A が到達経路として submodule を挙げたが、`--repo-root` に submodule を指す走行は
policy 検査で rc=2 になり導出へ到達しないことを親が実測した。残る経路は
`git init --separate-git-dir` の配置だけで、izanagi はそれを採っていない。

**段 3 の両レンズが独立に、親 brief の誤りを 1 件突いた。**brief は「submit directory =
qsub 実行時の cwd = repo root」と書いていたが、`submit_certify.sh` は qsub の前に `REPO_ROOT` へ
`cd` しない (`submit_floor.sh:664` はする)。返り先は呼出し元の cwd であり、記録済み運用が
repo root から投げていたので結果が一致していただけだった。親が両 script を直接読んで確認し、
insight §2 で訂正した。brief の逐語は訂正前のまま `verbatim/` に残してある。

段 3 はほかに、brief の「pin 閉包は不在」「触っている稼働 wave は無い」が探索範囲を超えた
全称否定であることも突いた。親は探索範囲を広げて (`*.sh` 集合 glob、admission registry loader の
読解) 追加実測したうえで、書き方を「この探索範囲で発見せず」へ狭めた。

段 6 の must-fix は 2 件。レンズ B が「m1/m2 は `.index()` の `ValueError` で落ちており契約を
assert で検査していない」を出し、レンズ A の nit「テストが `mkdir -p` の存在を検査しておらず、
その行を消しても dry-run では緑のまま通る」を親が must-fix へ昇格した。後者は今回届ける機構
そのものが未検査だったためで、修正後の `expected_root.is_dir()` が変異 m6 を KILLED にしている。

**負例に独自の検出力が無いことを、実測のうえ記録する。** この fixture では git common repo が
fixture repo と一致するので、正例の「親が期待 root と一致」から負例の containment は論理的に
導ける。変異走でも負例だけが赤になる件は 1 件も無かった。負例は依頼が要求した「返り先が
repo 外であることの検査」を直接表現する可読性のために残すが、独自に守っているとは主張しない。

変異は 6 件を probe で観測 node を集めてから本走し、6/6 KILLED・期待 node 完全一致。runner argv に
`orchestrator/tests/test_pegasus_tools.py` も入れたが 1 件も落ちず、冗長 gate が無いことを実測した。
`DW-M08` の新旧両走は、変異対象行が変更前 HEAD に存在しないため旧走が空である。

セッション異常: 待ち手が 2 度早戻りした。1 度目は `dev_wave_wait.py producer` が pid-only へ
縮退したもの (既知の型)、2 度目は自前の until ループが `kill -0` で setsid 済み process を
見失ったもの。いずれも producer は生存しており実害はなく、生死判定を成果物の実在へ寄せて
張り直した。`tools/dev_wave_submodule_init.py` が新規 worktree に対し 1 度だけ
`runtime-io-failure: update-no-fetch` で rc=1 になり、同じ worktree で
`git submodule update --init --recursive --no-fetch` を手で通した後の再実行で rc=0 になった。
原因は特定できていない。

## 次の一手差分

### 完了

- [T-583] `submit_certify.sh` の qsub 引数へ repo 外の `-o` / `-e` を足し、返り先が repo の
  内側でないことを argv 実走検査の負例で守った。変異 6/6 KILLED。
  remaining: none
  base: cda602a6d0f81b826118ba529cd89a74c089a9f238fe11fc4ed4249ce1c58763
