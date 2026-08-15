---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t330-scr-single-process
seq: 1
title: [T-330] の実装形は受入条件が満たせないと実測で確定し、差分ゼロで再裁定へ返す — 敵対 2 レンズが正反対の結論を出し、既に land 済みの床値 claim に新しい穴を 1 件見つけた (docs のみ、branch worktree-dev-wave-t330-scr-single-process)
---

## 本文

- **依頼の前提は半分だけ失効していた。** 依頼は [T-330] (裁定択 (a) = `/scr` fresh namespace と
  `single_process` 強制を、使用権を供給する wrapper の新設とセットで実装する) の実装であり、
  「裁定は 2026-08-03 と古いので現行 main で前提を実測し、失効していたら実装差分ゼロで裁定へ
  返してよい」という条件が付いていた。実測の結果は次のとおりで、**失効と生存が混在した**。
  - 失効: 「使用権を供給する wrapper が存在しない」は**床値経路では失効**している。
    `tools/pegasus/submit_floor.sh` が claims/ を create-only 0700 で事前 provisioning し、
    `tools/pegasus/floor_campaign.sh` が `IZANAGI_RESERVATION_*` 8 値を export する。強制も
    `orchestrator/campaign/s8b_floor_campaign.py` と `s8b_oracle_driver.py` で発火済みである。
  - 生存: D125 決定 (5) の対象は床値ではなく `campaign.loop.run_campaign` であり、そこには
    今も claim 取得・reservation 検査・`allow_resume=False` 拒否のいずれも無い。
  - 失効: ユーザーが疑った「計測経路が dispatch 経由に変わった」は**別の意味で正しかった**。
    dispatch は計測経路ではない (`tests` と `provenance` の 2 task だけ) が、8c live pilot が
    計算ノードで走る現行主経路になっており、そちらが `run_campaign` へ到達する。
- **実装しなかった理由は「不要になったから」ではない。** ユーザーの追加条件
  「caller が実在することをテストで固定してください」が現行 main では満たせないからである。
  `run_campaign` へ到達する compute caller は実在するが、それは repo 外・untracked の wave 専用
  job script (`/work/1/SFC/tanab/dev-wave-jobs/2026-08-15_t1097-s8c-live-abc/live/live.pbs`) で
  あり、tracked なテストで固定できない。tracked 化するには 8c を計算ノードで運転する wrapper を
  新設するしかなく、それは D125 決定 (6) と [T-276] / [T-1097] が所有する境界である。
  段 3 の両レンズが独立に「T-330 が独断で開いてはならない」と判定した。
- **段 3 の敵対 2 レンズが正反対の結論を出した。** レンズ A は「実在する T-1097 PBS 経路が
  X の caller 不在論を崩す」として Y の再設計を要求し、レンズ B は「DW-G04 の成功 artifact が
  無く、8c wrapper は他裁定と衝突する」として Y の land 不可を主張した。親は A の
  「artifact path は成功計測でなくてよい」という DW-G04 解釈を採らなかった — 911106 は
  transport admission で停止し `run_campaign` 到達 0 で、**発火条件を満たしていない**。
  一方 A の「X の成果物影響を certified だけで数えるのは会計の欠落」は採用し、
  記録に exploratory 側の影響を書いた。
- **新しい欠陥を 1 件見つけた ({{F:floor-claim-identity-not-protocol-scoped}})。** 既に land 済みの
  床値 `single_process` 強制は、claim identity が**秒精度の時刻 + protocol hash 先頭 8 桁**で
  あるため、同一 protocol を別の秒に投入した 2 job を排除しない。`campaign_claim.acquire_claim`
  の docstring 自身が「別 out_root を与えた実行同士は排他できない」と明記している。
  これは T-330 の対象外だが、**発火 caller が既に実在する分だけ T-330 本体より優先度が高い**。
- **親 brief の誤りを子が 3 件倒した。** (a) `run_campaign` の caller 列挙が 6 箇所漏れていた
  (`p3_kickoff.py:111,118` / `p3_s4_loop.py:951` / `p3_s4_red.py:165,175` /
  `s8a_trigger_sweep.py:464`。親が実在を確認)。(b) 親が不変条件に書いた D108 決定 (1) は
  **D122 が supersede 済み**で、生きているのは D108 決定 (2)〜(5) の campaign task 凍結と
  D125 決定 (6) だった。(c)「caller は 1 本もない」という絶対表現は偽で、正しくは
  「tracked な sanctioned caller と、gate を通過した成功計測 ID が無い」である。
- **`/scr` fresh namespace は T-330 から切り離した ({{D:t330-return-zero-diff}})。** 対象を
  取り違えていた。床値 wrapper は依存を `/scr/${PBS_JOBID}` へ build して `CMAKE_PREFIX_PATH` へ
  export し、v2 build identity が dependency prefix を path 要素として束縛するため、床値経路は
  durable cache root でも実質 job ごとに cold である。加えて S4 は F319 (third-party source cache
  の ignored 生成物 71 件) を閉じない — root が違う。懸念自体は 8c 経路 (共有 checkout の
  `build-variants` と `/tmp` checkout) で生きており、そちらは F319 の恒久対応と同じ層である。
- **本 wave は計測ジョブを 1 本も投入していない。** 静的検査と repo 内テスト 2 node の実走
  (`test_s8c_preregistration_predicates.py` の `zero_satisfied` / `gap_reason_snapshot`) だけである。
  8c 事前登録 C12 の機械評価器は `machine_checkable` が false のため休眠しており、契約が名指しする
  `reservation.single_process_required` という関数は実在しない (現行名は `is_reservation_required`)。
- **実装差分ゼロのため変異 matrix は対象外 (`DW-S04`)。受入全走は免除せず実施した。**
  1 走目 (request 912424、計算ノード 48 worker、11,224 items、152.97 秒) は
  `attributable-red` (rc=70) で 3 node が赤だったが、**3 件とも本 wave の差分が到達しえない**
  (差分は spool fragment 3 件と `output/insights/` のみ)。計算ノードでの単独再走
  (request 912438) が **3 passed / 3.27 秒**で緑になり、非帰属と判定した。
  内訳は F57 の再発 2 件 (`test_codex_worker_launch.py` の fake wall 上限 3 秒) と
  F306 の再発 1 件 (`test_dev_wave_wait.py` の signal 復元系) で、いずれも新しい F は採らず
  既存エントリへ再発として追記した。**待ち手の非帰属 checker は docs-only の差分でも
  3 件すべてを `attributable` と分類しており、この経路は今回も塞がれていない。**
- 材料の正本 = `output/insights/2026-08-16_t330-scr-single-process/`
  (段 4 裁定と、段 2 プラン・段 3 敵対 2 レンズの逐語)。

## 次の一手差分

### 更新

- [T-330] **P1・ユーザー裁定待ち (再裁定)**: 実装差分ゼロで返す。裁定 (a) の受入条件
  「caller が実在することをテストで固定」が満たせない — 実在する caller は repo 外・untracked の
  8c job script であり、tracked 化は D125 決定 (6) / [T-276] / [T-1097] の所有境界を開く。
  `/scr` fresh namespace は対象取り違えのため本タスクから切り離した ({{D:t330-return-zero-diff}})。
  択一は (a) 強制のみ先行 (2026-08-03 の「部分実装は採らない」を明示解除する裁定が要る) /
  (b) [T-1097] / [T-276] へ合流 / (c) 発火 caller が既に実在する床値側の穴
  ({{F:floor-claim-identity-not-protocol-scoped}}) を先に直す / (d) 現状維持。
  親の推奨は (c) → (a) の順。材料 = `output/insights/2026-08-16_t330-scr-single-process/`。
  base: 9deb00ba4f0fac86cfac4b2fc503f866231850e6374b57698f72c108619f9a9b

### 新規

- {{T:floor-claim-protocol-scope}} **P1・新規**: 床値 campaign の claim identity を protocol 単位の
  排他にする。現行は秒精度 run ID + protocol hash 先頭 8 桁のため、同一 protocol を別の秒に
  投入した 2 job が同時に走れる ({{F:floor-claim-identity-not-protocol-scoped}})。
  発火 caller (床値 campaign) は既に実在するので DW-G04 を満たす。
  あわせて reservation が現在 hostname・実行 script SHA・submission nonce を照合しない点を
  同じ層で扱うか、別タスクへ分けるかを裁定する。
