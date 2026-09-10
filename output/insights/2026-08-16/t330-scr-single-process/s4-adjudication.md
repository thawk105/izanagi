# 段 4 裁定 — [T-330] `/scr` fresh namespace と `single_process` 強制

wave: `dev-wave-t330-scr-single-process` / 2026-08-16 / branch
`worktree-dev-wave-t330-scr-single-process` / 基準 commit `330f67d0`

## 裁定: (X) 実装差分ゼロで裁定へ返す

**理由は「もう要らないから」ではない。裁定 (a) が指定した実装の形が、現行 main では
実行不能な受入条件を持つからである。** 強制の対象欠陥そのものは生きており、むしろ
本 wave は同族の欠陥を新たに 2 件見つけた。したがって「解決済みとして閉じる」のではなく、
**形を変えて再裁定へ返す**。

段 3 の敵対 2 レンズは**正反対の結論**を出した (レンズ A: X を退け Y を再設計せよ /
レンズ B: Y は land 不可)。親は両者の real 指摘を個別に裏取りし、下記のとおり採否を決めた。

## 決定 1 — 裁定 (a) の受入条件が満たせない

ユーザーの追加指示は「実装する場合は wrapper と強制を同一 wave で入れ、**caller が実在することを
テストで固定**してください」であった。これは現行 main では満たせない。

- `campaign.loop.run_campaign` へ到達する compute caller は**実在する**が、それは
  `/work/1/SFC/tanab/dev-wave-jobs/2026-08-15_t1097-s8c-live-abc/live/live.pbs:145-154`
  という **repo 外・untracked・wave 専用の job script** である (親が実在を確認、6,999 bytes、
  2026-08-15 07:48)。tracked なテストはこれを固定できない。
- tracked 側の caller は 12 file 15 call で閉じており (`orchestrator/tests/test_campaign.py:4720-4740`)、
  そのいずれも PBS job script から起動されない。tracked な PBS job script 7 本が計算ノードで
  起動する python は `s8b_floor_campaign.py` (別実装の `run_campaign`)、`orchestrator/calibrate.py`、
  `pegasus_floor_scoping.py`、`silo_ladder_rung1.py`、`run_probe.py`、`t126_driver.py` と
  inline profiler だけである。
- したがって「caller をテストで固定する」には、8c を計算ノードで運転する wrapper を **tracked
  として新設する**しかない。それは D125 決定 (6)・[T-276]・[T-1097]・D108 決定 (2)〜(5) の
  campaign task 凍結が所有する境界であり、**T-330 が独断で開いてはならない**
  (段 3 の両レンズが独立に同じ結論)。

## 決定 2 — S4 (`/scr` へ cache_root の fresh namespace) は現行の正しい設計ではない

- **床値経路は既に実質 job ごとに cold である。** `tools/pegasus/floor_campaign.sh:97-101` が
  `/scr/${PBS_JOBID}` を create-only で作り、`:810-923` が gflags/glog をそこへ build・install し、
  `:923` が `CMAKE_PREFIX_PATH` をその 2 path へ export する。v2 build identity は dependency
  prefix を **path 要素の配列**として pre-image に束縛する (D125 決定 (3)、
  `orchestrator/campaign/buildcache.py:750-770,1043-1066,1307-1347`)。job ID が変われば prefix が
  変わり digest が変わるので、跨ジョブ cache hit は構造的に起きない。
  よって「`s8b_floor_campaign.py:1953` の cache root が永続領域にある」ことだけを根拠に
  既存床値を汚染済みとは言えない (レンズ A・B・段 2 が独立に同結論)。
- **S4 は F319 を閉じない。** F319 の汚染対象は third-party source cache (masstree の
  ignored 生成物 71 件、`config.h` 10,448 bytes) であり、S4 が動かす build-variants
  `cache_root` ではない (`docs/failures.md:7705-7725` と `s8b_floor_campaign.py:1941-1954` /
  `:1582-1603` は別の root)。F319 の恒久対応は [T-1094] / [T-1095] / [T-1128] / [T-1129] が
  所有しており、T-330 が横取りしてはならない。
- **コストは現行予算に直結する。** 床値は 1 cell あたり build cap 900 秒を要求する
  (`s8b_floor_campaign.py:250-259,844-881`)。一律 cold 化は walltime envelope を圧迫する。

**ただし S4 の懸念は 8c 経路では生きている** — 8c は共有 checkout の
`build-variants` を cache root にし (`p3_autonomous_workload_trial.py:3277-3278`)、
`TMPDIR` 未設定なら checkout は `/tmp` を使う (`patchharness.py:345-364`)。
対象を取り違えていたのであって、懸念自体が消えたのではない。

## 決定 3 — 強制側の欠陥は生きており、新たに 2 件見つかった

(X) を選ぶが、次の 3 点は**未解決のまま残る事実**として台帳へ記録する。

1. **`loop.run_campaign` は宣言だけで強制しない。** `loop.py:61-89 _authorize_measurement` は
   D125 決定 (4) のとおり required attestation を発火させるが、claim 取得も reservation 検査も
   `allow_resume=False` の拒否も行わない。pegasus 契約は `single_process=True /
   allow_resume=False` を宣言する (`env_contract.py:245-253`)。**[T-1097] の transport 欠陥が
   直った瞬間、この sink は単独性が未検査のまま exploratory WAL・report・binary を受理し始める。**
2. **床値の claim は protocol 単位の排他ではない (新発見)。** claim identity は
   `_fresh_run_id(protocol_sha256, started_at)` = **秒精度の時刻 + protocol hash 先頭 8 桁**
   (`s8b_floor_campaign.py:4235-4239`, `:4618-4619`)。`O_EXCL` が排他するのは同一 identity の
   ファイルだけであり、`campaign_claim.acquire_claim` の docstring 自身が
   「clone ごとに別 out_root を与えた実行同士はこの leaf では排他できない」と明記する
   (`campaign_claim.py:167-174`)。**同一 protocol を別の秒に投入した 2 job は別 claim を取り、
   同時に走れる。** 既に land 済みの `single_process` 強制は、名前が示すほど強くない。
3. **reservation は caller の自己申告である。** `reservation.py:218-270` が照合するのは
   現在の `PBS_JOBID`、boot ID、時刻、残容量だけで、現在 hostname・実行 script SHA・
   submission nonce は照合しない。claim には未検証の `binding.host` が転記される
   (`s8b_floor_campaign.py:4253-4262`)。ただし binding を無変更で別ノードへ複製するだけなら
   boot ID 検査で落ちるため、「host 未照合だけで全入力が恒真」ではない (レンズ A の但し書きを採用)。

## 親 brief の誤り (子が倒した。訂正して記録する)

- **caller 在庫の 6 箇所漏れ**: `p3_kickoff.py:111,118` / `p3_s4_loop.py:951` /
  `p3_s4_red.py:165,175` / `s8a_trigger_sweep.py:464`。親が実在を確認した。
- **D108 決定 (1) を生きた禁止として不変条件に書いた**のは誤り。`docs/decisions.md:4983-4987` が
  D122 による supersede を明記している。生きているのは D108 決定 (2)〜(5) の campaign task 凍結と
  D125 決定 (6) の scope 境界である。
- **「caller は 1 本もない」という絶対表現**も誤り。repo 外に実在する (決定 1)。
  正しくは「tracked な sanctioned caller と、gate を通過した成功計測 ID が無い」。

## 採らなかったレンズ A の主張

- レンズ A は「repo が sanctioned と記録した T-1097 PBS は DW-G04 の artifact path に数えられる」
  として Y の再設計を求めた。親は採らない。DW-G04 は「**発火条件を満たす**既存 artifact path か
  計測 ID」を要求する (`docs/dev-wave/core.md:60-63`)。request 911106 は D122 transport admission
  で停止し role attempt 0、`run_campaign` 到達 0 である。**発火条件を満たしていない。**
  加えて、その artifact は untracked の wave 専用 job script であり、ユーザーが指定した
  「caller が実在することをテストで固定」を満たせない (決定 1)。
- ただしレンズ A の「X の成果物影響を certified だけで数えるのは会計の欠落」は**採用**した。
  下記の成果物影響はその指摘を反映している。

## 成果物影響 (DW-G05)

- **certified 選択・材料レポート・proof chain・凍結 bytes・受理集合は本 wave では 1 bit も変わらない**
  (実装差分ゼロ)。
- **実装しないことの影響**: [T-1097] の transport 欠陥が直ると、8c exploratory の WAL・report・
  binary SHA・throughput が、`single_process=True` を宣言しながら単独性を一度も検査していない
  経路から台帳へ入り始める。これは「謳うだけで発火しない gate」の受理であり、規律 3 の
  「正しさシグナルを後付けにしない」に抵触する。**再裁定はこの点を止めるためのものである。**
- **決定 3-2 の影響**: 現行の床値 `single_process` は同一 protocol の二重投入を排除しない。
  ただし本 wave は既存の床値値を疑わしいとは主張しない — 二重投入が実際に起きた記録は無い。

## 再裁定へ返す択一 (ユーザー手番)

- **(a) 強制のみを先に入れる** — `loop.py:61-89` に、`contract.isolation_policy.single_process is
  True` のときだけ発火する sink-local な claim 取得と reservation 検査を置く。caller は当面
  repo 外の 8c job script のままとし、tracked wrapper は [T-1097] / [T-276] 側で作る。
  *長所*: 発火した瞬間に fail-closed になり、未検査の値が台帳へ入らない。
  *短所*: 2026-08-03 の裁定が明示的に禁じた「発火 caller を持たない強制だけの部分実装」に当たる。
  採るなら**その禁止を明示的に解除する裁定**が要る。OTHER (linux-baremetal,
  `single_process=False`) を 1 bit も変えないことが必須条件。
- **(b) [T-1097] / [T-276] へ合流させる** — 8c compute wrapper を tracked 化する作業と同一 wave で
  強制と使用権供給を入れる。T-330 は独立タスクを解体し、その wave の受入条件に吸収する。
  *長所*: 裁定 (a) の「セットで」を字義どおり満たす。*短所*: T-330 単独では着手できない。
- **(c) 強制の対象を先に直す** — 決定 3-2 (claim identity が protocol 単位でない) と
  3-3 (reservation が自己申告) を、既に発火している床値経路に対する独立タスクとして先に直す。
  *長所*: 発火 caller が既に存在するので DW-G04 を確実に満たす。
  *短所*: T-330 の字面 (`/scr` と 8c) からは外れる。
- **(d) 現状維持** — 8c live が exploratory 値を出し始めるまで何もしない。
  *長所*: 予算ゼロ。*短所*: 上記の受理が既成事実になる。

親の推奨は **(c) → (a)** の順である。(c) は発火 caller が実在し (床値 campaign)、
成果物影響が certified 側に直接効く。(a) はその後に、2026-08-03 の禁止の明示解除とセットで行う。

## S4 の扱い

`/scr` fresh namespace は **T-330 から切り離す**。対象を取り違えていたためである。
8c 経路の共有 checkout build cache (`p3_autonomous_workload_trial.py:3277-3278`) と
`/tmp` checkout (`patchharness.py:345-364`) の job-local 化は、F319 の恒久対応
([T-1094] / [T-1095] / [T-1128] / [T-1129]) と同じ層の問題として、そちらの所有者へ返す。
