---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1814-shard-time-balance
seq: 2
title: 受入分割の時間不均衡を測り、duration 重み割付を実装しないと裁定した — 完璧な予言者でも利得 0.0 秒 (docs のみ、branch worktree-dev-wave-t1814-shard-time-balance、実装差分ゼロのため変異 matrix は DW-S04 で免除)
---

## 本文

- 依頼は「受入分割 (K=2) の時間不均衡を直す」。(i) 同一 tip で K=1 と既定 K=2 を並べて測り
  4 層を D713 どおり分けて記録する、(ii) junit の duration を重みにした割付の実装可否まで
  判断する、の 2 点。適応 K ([T-1589]) は scope 外と明示された。控えは
  `2026-08-24-shard-allocation-balances-count-not-time.md` で、裁定不要・起票して判断してよいとされた。
- **結論は「実装しない」。** 設計判断は {{D:shard-duration-weight-refused}} と
  {{D:shard-chain-bound-trigger}}。実装差分ゼロで閉じた。
- **控えが名指しした機序は確認された。** `allocate()` は要素数だけで詰める。同一 tip の
  K=2 走で選択 node 数は 8580/8580 と完全に均等なのに、直列総仕事量は 8981.5 対 5880.5 秒
  (34% 偏り) だった。参照走 (2026-08-24) の 12.8% より偏りは拡大している。
- **しかし偏りは wall を決めていない。** shard-0 では `real-repo` の排他 group が 1 worker を
  222.7 秒 / 76 件 占有し、残り 47 worker は 185.7〜191.4 秒に密集していた。鎖が単独で最遅である。
- **完璧な予言者でも利得は 0.0 秒だった。** その走自身の実測 duration を重みにした割付は
  仕事量を 5283.4 / 5283.4 秒 (1 worker あたり 110.1 秒) まで均衡させるが、鎖はそのまま残る。
  独立 2 走で再現した。
- **親の事前予測は 2 つとも外れた。** (a)「K=2 が K=1 より速い」— 4 走では K=2 が 307.29 と
  275.02 秒、K=1 が 261.45 と 275.05 秒で、K=2 が速いとは言えなかった。
  (b)「duration 重み割付の期待利得は 0〜17 秒」— 上限の導出が誤りで、実測は 0.0 秒だった。
- **親 brief に算術の誤りがあった。** `W/(48K)` の分母から K を落とし、参照走で
  `7472.5/48 = 155.7` と書いた。正しくは `7472.5/96 = 77.84`。段 2 plan と段 3 の 2 レンズが
  独立に指摘し、段 4 で訂正した。結論 (鎖律速) は変わらない。
- **親の「分割は worker 準備費を倍払わせる」という推論は撤回した。** 1 走目の総仕事量 14862.6 秒と
  K=1 の wall からの逆算 (約 9000 秒) を比べて立てた仮説だったが、同一 tip の 2 走目で
  総仕事量が 10585.7 秒 (1.40 倍差) になり、差はノードの違いで説明できた。sol レンズが
  「因果でなく仮説」と正しく指摘していた。
- **同じ理由で「テストの仕事量が 2 日で倍増した」も訂正した。** 1 走目は台帳比 1.64 倍
  (中央値 1.01、95 パーセンタイル 4.75) だったが、2 走目は 1.18 倍 (中央値 0.90、
  95 パーセンタイル 2.24) で、参照走の分布 (0.91 / 2.12) とほぼ同じだった。
  1 走目は bnode009 + bnode001、2 走目は bnode016 + bnode017 に載っている。
  実際の 2 日ぶんの増加は共通テストで 1.24 倍、新規 2323 件を含めた総量で 1.42 倍である。
- **段 3 の 2 レンズは独立に同じ最重要所見を返した。** 「所要台帳は 15,909 nodeid、受入集合は
  17,160 node なので、plan の全件 fallback 設計は毎走必ず発火し、duration 割付は実環境で
  一度も動かない」。段 2 plan 自身の総括も「実装しない」を推奨していた。
  親は 15 件の所見をすべて real と裁定し、不採用はゼロだった。
- **計測は受入ではなく計測として投入した。** land 用受領証を作る `dev_wave_wait.py acceptance`
  経路は claim 時に main を merge するため tip が走ごとに動く。同一 tip を保つ必要があったので、
  worktree の tip を `9463bcbc` に固定したまま `IZANAGI_ACCEPTANCE_SHARDS` を 2/1/1/2 と
  切り替えて 4 走した。受入全走は最終 tip で別に投入している。
- **4 走目が 1 件赤で戻ったが非帰属である。** 本 wave の実装差分はゼロ (tip = main)。
  `test_t810_coordinator.py::test_authorized_production_core_uses_same_validator_twice_and_dormant_prereg`
  が、走行中に別セッションが `dev-wave-8b-b2-precheck` の worktree 登録を撤去したことで落ちた。
  この test は生きた worktree 登録を読む。1 走目・K=1 の 2 走では緑だった。
- **受入全走の 1 走目は非帰属の赤 1 件で戻った。**
  `test_dev_wave_cleanup.py::test_forward_merged_landing_tip_is_used_for_cleanup[asserted]` が
  `status=rejected phase=occupancy reason=occupancy result is indeterminate or inconsistent` で
  落ちた。本 wave の差分は docs のみで、cleanup の占有検査へ到達しえない。同 file を単独走した
  ところ 94 passed で非再現だったので、DW-O18 に従い受入を 1 回だけ再走した。
  占有検査が全走の負荷下で不定になる型は既知である。
- **受入全走は 2 走とも同じ理由で赤になり、land せずに停止した。** 2 走目は
  `test_reentry_states_run_only_remaining_cleanup[b]` で、本文は 1 走目と逐語一致の
  `phase=occupancy reason=occupancy result is indeterminate or inconsistent` (rc=22) だった。
  **落ちる node が走ごとに動く**ため node 単位の hold では塞がらない。F489 の再発として
  台帳へ記録した。除外の再投入・class 単位の hold・占有検査の作り替えはいずれも受理集合を
  変える判断なので、ユーザー裁定へ返して停止した。本 wave の成果は branch 上にある。
- **codex 子の工数**: plan 902.8 秒 / 22 model call、sol 830.4 秒 / 17 call、
  luna 458.2 秒 / 18 call。3 本とも accepted、失敗ゼロ。
- 一次資料は `dev-wave-jobs/dev-wave-t1814-shard-time-balance/` の `arm-*.log`・`arm-*.meta`・
  `extract_layers.py`・`counterfactual.py`・`ledger_ratio.py`・`compare_runs.py`・
  `probe_alloc.py`、および `.izanagi-acceptance-shards/` の 3 session。逐語は
  `output/insights/2026-08-26_t1814-shard-time-balance/`。

## 次の一手差分

### 更新

- [T-1589] **P3・更新**: 負荷に応じて K を動的に選ぶ案。**K を増やす方向は当面効かないことが
  実測で分かった。** {{D:shard-chain-bound-trigger}} の引き金 `最長排他鎖 > 総仕事量/(48K)` が
  観測 3 走すべてで成立しており、K=3 では `10585.7/144 = 73.5 秒` に対し鎖が 206.1 秒で
  差はさらに開く。telemetry を貯める前に、鎖の短縮 (D532 (a)(b)) が先である。
  base: 530bfd17d1050783b0c4a22e96f7c0958dc69fb49b44ed3732d980ca27564362

### 新規

- {{T:real-repo-chain-is-acceptance-floor}} **P1・新規**: 受入 wall の床は `real-repo` 排他鎖である。
  実測は 2026-08-24 の走で 210.5 秒 / 72 件、2026-08-26 の 2 走で 222.7 秒 / 76 件と 206.1 秒。
  内訳の上位は `test_codex_reasoning_ab` 群で、単体最大 42.77 秒、上位 10 件で 155.3 秒
  (鎖全体の 70%) を占める。5 分に安定して収めるには D532 (a) 鎖の短縮か (b) 排他閉包の
  細分化が要る。どちらを採るかを決める。
- {{T:default-k-two-not-reproduced-as-faster}} **P2・新規**: D724 の既定 K=2 は「速い」を
  再現しなかった。同一 tip 4 走で K=2 が 307.29 / 275.02 秒、K=1 が 261.45 / 275.05 秒。
  各 2 走では勝敗を宣言できない (走間ばらつき 32 秒) が、K=2 は PBS request と故障面を
  2 倍にする。ノードで block した対測定を組むか、D724 を再裁定するかを決める。
- {{T:duration-ledger-has-no-provenance}} **P3・新規**: 所要台帳
  `orchestrator/tests/acceptance_duration_ledger.json` に provenance が無い。
  現物 schema は `schema_version` / `unit` / `nodeid_count` / `duration_seconds_by_nodeid` だけで、
  いつ・どの K・どの scheduler・worker 何本・どの junit から採ったかを持たない。被覆も
  15,909 / 17,160 = 92.5% にとどまる。台帳を重みに使う機構を将来作るなら、provenance、
  部分被覆の裁定、走行証拠への `allocation_mode` と台帳 digest、controller 間の同一 snapshot の
  機械証明、bin 加算の有限性検査の 5 点が前提になる。
- {{T:live-worktree-registration-read-is-racy}} **P2・新規**: `test_t810_coordinator.py` が
  生きた worktree 登録 (`.git/worktrees/<name>/gitdir`) を読むため、別セッションの worktree 撤去と
  競合して落ちる。2026-08-26 の計測 4 走目で実際に落ちた (実装差分ゼロの走)。
  並行 wave が常時 20 本以上ある環境では再発する。fixture 側で固定するか、
  既知の非帰属赤として扱うかを決める。
- {{T:stage9-release-tool-name-is-wrong-but-pinned}} **P2・新規**: 入口 command の 9 段状態機械の
  項 9 が「受入・land の終端で必ず `tools/dev_wave_wait.py acceptance` で `release` し、
  land 成功時だけ `message` を送る」と書くが、**`dev_wave_wait.py` に `release` も `message` も
  無い。** `_parse_cli` が受けるのは `producer` と `acceptance` だけである。実在するのは
  `tools/wave_land_window.py` の `claim` / `release` / `status` / `message` である。
  是正は byte を減らす方向だが、`tools/check_docs.py` の
  `DEV_WAVE_STAGE9_WAITER_CONSUMER_LINES` がこの 3 行を逐語で pin しており、
  文言を直すと機械防壁の pin 自体を変えることになる。段 8 の契約は防壁の変更を
  裁定パッケージへ送れと定めるため、本 wave では実装しない。
  pin の意図 (項 9 で waiter consumer を名指しさせる) を保ったまま道具名を正す形を裁定する。
- {{T:same-tip-run-variance-breaks-timing-claims}} **P2・新規**: 同一 tip・同一選択・同一割付の
  受入走で、直列総仕事量が 10585.7 対 14862.6 秒 (1.40 倍)、pytest wall が 275.02 対 307.29 秒
  動いた。原因は割り当てられた計算ノードの違いである。**今後の所要主張はノードで block した
  対測定でなければ成立しない。** 所要の目標値・上限を裁定に書くときの前提として明文化する。
