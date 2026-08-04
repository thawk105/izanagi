---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: wave-a-transport-smoke
seq: 3
title: 壁 1 の生死確認 — build 未到達で止まったが、塞いでいるのが実行時 attestation の自己不整合だと特定した (コード + docs、branch worktree-wave-a-transport-smoke、実測 = Pegasus gen_S request 882490 / bnode002、変異 matrix = 対象外)
---

## 本文

- **壁 1 は越えられていない。build に一度も到達しなかった。** ただし**塞いでいる原因を特定した**。
  詳細と択一は {{D:pegasus-attestation-blocks-wall1}}、事故の型は
  {{F:pegasus-attestation-self-rejecting}}。逐語は
  `output/insights/2026-08-04_wave-a-campaign-transport-smoke/`
- **原因は transport でも LLM 分割線でもなかった。** Pegasus 契約は `attestation_mode="required"`
  であり、campaign の全実行が `execution_guard` の実行時 attestation を通る。
  そこで `effective_clock.samples_mhz` が不合格になり、2 脚とも build 前に停止した
- **登録済み較正は自分自身の判定を通らない。** 述語は「期待列の中央値を中心に観測列の全要素が
  ±2% に入ること」で、許容帯は [2058.98, 2143.02]。ところが較正自身の期待列が index 40 に
  3080.935 を持つ。**参照データを観測値として与えると落ちる。** 実行時も
  「48 コアのうち 1 つでもブーストしていれば不合格」になり、今回は index 34 が 3076.13 だった。
  どのコアがいつブーストするかは再現性のある機器特性ではない
- **裁定へ返す理由:** 述語と凍結較正のどちらを正とするかは正しさ防壁と凍結 bytes に同時に触る。
  推奨は「述語を正とし、較正を取り直す + 取得時に全要素が帯内であることの受入検査を同時に入れる」
  だが、再登録は proof chain の参照を動かすためユーザー裁定事項である
- **scope に書かれた機序は現ドライバでは成立しないことが brief 前実測で判明した。**
  8c CLI は `--provider fixture` と実 build が排他 (`p3_autonomous_workload_trial.py`)、
  かつ計算ノードの build opt-in は `claude-headless` provider 専用で LLM transport receipt を要求する。
  そのため fixture をコードとして再利用し、素の proposal を受ける `drive_iteration` を直接呼ぶ
  使い捨て driver に切り替えた。**LLM は経路に一切現れない**ので、稼働中の
  [T-276] / D122 の再裁定がどちらに転んでも本 wave の結果は成立する
- **投入前レビューで blocker を 2 件捕捉し、実走前に閉じた。** (i) job script が
  sanctioned な `qsub -v` を写さず位置引数を発明していた ({{F:qsub-positional-args-invented}})。
  (ii) `legacy+s2` は Pegasus 契約の空 numactl により build 前に落ちる (静的確認)。
  後者は gate を緩めず 2 脚構成にして両方を証拠化する形へ変えた
- **副次的に環境事実を 3 件確定した** ({{D:pegasus-numactl-single-node}})。計算ノードは
  単一 NUMA ノード (48 CPU / node 0 / 127476 MB)、`numactl` は計算ノードに在りログインノードに無い、
  pin 済み gflags/glog の build+install は計算ノードで 11 秒で通る (D87 決定 4 の形がそのまま動く)
- **D131 の共通前提のうち 2 件は既に閉じていた** (`total_deadline` の rebase、走行中 qdel の禁止)。
  一方 **D117 決定 (4)(b) は未解消** — `_job_run` は `os.environ.copy()` を継承し、
  `env_allowlist` を子側で強制していない
- **背景 job セッションからの qsub は F49 (ii) の 3 検査をすべて満たした。**
  計算ノード自身が書いた marker (`bnode002`)、`qstat` 可視 (STT=PRR)、
  NQSV 会計サマリ (Elapse 20S) のいずれも実在する
- **`qsub` には `--accept-sigterm` と `--warning-signal=elapstim:signal` がある。**
  「NQSV は walltime 超過で SIGKILL を直送し finally は走らない」(149) に対する既存の対抗手段。
  本 wave では使っていない (scope 外) が、恒久実装の設計材料として記録する
- 使った計算資源は 1 ジョブ・Elapse 20 秒。規模は膨らませていない (workload 1 本、
  records=100,000、threads=4、extime=1、reps=2 = 8c の 1 cell と同値)
- `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-03-task-def-rulings.md` の 3 件は
  **本 wave では台帳化しない**。[T-276] が D122 と逆方向であることが同ファイルに追記され、
  ユーザー再裁定待ちになったためである。争点のある裁定を確定として台帳へ書かない
- **受入全走 = 5430 passed / 19 skipped / 1 failed** (Pegasus gen_S request 882661、270.26s)。
  **赤 1 件は本 wave の差分に由来しない。** `test_ruleops.py::
  test_real_checkout_independent_maximum_package_and_runner_preflight` が
  `tools/ruleops.py inventory` の rc=2 で落ちる。原因は既に land 済みの別 wave の成果物
  `output/insights/2026-08-03_t361-t362-cluster-probes/` 配下にある**非 UTF-8 の probe raw file**で、
  inventory がこれを拒否する。**wave 差分なしの main (846d5a1) 単体で同一メッセージが再現する**ことを
  実測して帰属を確定した ({{T:ruleops-nonutf8-artifact}} を起票)。本 wave は回帰を持ち込んでいない

- **段 9 の land が防壁の交差で止まった** ({{F:campaign-run-blocks-wave-land}})。campaign を 1 回
  起動した結果 wave worktree に `output/exploration/` が生成され、`dev_wave_land.py` の
  「完全に clean」要求を満たせない。しかし `hooks/guard_bash.py` は
  `namespace.json` (exact path) と `campaign.lock` (末端) の削除・移動を拒否する。
  **迂回しないことを選び、land せずに停止した。** 成果は branch `worktree-wave-a-transport-smoke`
  に全て commit 済みである。人間が worktree の `output/exploration/` を除去すれば
  そのまま land できる

## 次の一手差分

### 新規

- {{T:pegasus-attestation-ruling}} **P1・ユーザー裁定待ち**: 実行時 attestation の
  `effective_clock` 述語と登録済み較正のどちらを正とするか裁定する。
  推奨は「述語を正とし較正を取り直す + 取得時受入検査を同時に入れる」。
  これが決まるまで Pegasus 上の campaign 実行は全面的に塞がれたままである。
- {{T:wall1-transport-recheck}} **P2・新規**: attestation の裁定が付いた後、
  `output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/` の使い捨て driver を
  そのまま再走させ、build → verify → bench が計算ノードで 1 周通るかを確かめる。
  追加実装は要らない。通れば壁 1 の生死確認が初めて完了する。
- {{T:pegasus-s2-numactl-proxy}} **P3・新規**: `pipeline.py` の「numactl prefix が非空か」という
  代理条件を、単一 NUMA ノードでも意図どおり働く判定へ置き換えるかを検討する。
  attestation の裁定後、実機で発火を確認してから着手する。
- {{T:wave-land-vs-campaign-guard}} **P1・ユーザー裁定待ち**: campaign を実走した wave が
  正規経路で land できない ({{F:campaign-run-blocks-wave-land}})。
  推奨は「campaign の実行先を使い捨て worktree の外へ出す」= 防壁を 1 つも緩めない案。
  放置すると、計算ノードで campaign を回す wave はすべて段 9 で止まる。
- {{T:ruleops-nonutf8-artifact}} **P1・新規**: **現在 main の受入全走が赤である。**
  `output/insights/2026-08-03_t361-t362-cluster-probes/` 配下の非 UTF-8 probe raw file を
  `tools/ruleops.py inventory` が拒否し、`test_ruleops.py` の real-repo 検査が落ちる。
  凍結済み成果物の再エンコード・削除と、inventory 側で binary 成果物を許容する案の択一になる。
  どちらも凍結 bytes か受理集合に触れるため裁定を要する。放置すると全 wave の受入が赤のままになる。
