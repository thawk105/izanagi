---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t2293-origin-producer-2
seq: 1
title: [T-2293] 起点試行の証拠の所在と bytes を呼び手申告から producer 導出へ移し、executor の結線障害 6 件を構造化して返した (コード + docs、branch worktree-dev-wave-t2293-origin-producer-2、変異 4/4 KILLED・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「契約側が着地済みの R1 (lifecycle start の起点専用 optional key) と R3
  (execution-provenance/v2) について producer 層を設計・実装する。契約だけ変えても consumer が
  消費しなければ効かないので、実運用 consumer と同じ変更単位で結線する。結線できないなら何を
  結線できなかったかを構造化して返す。規律 2 を緩めない。本題だけ。仮想リスク向けの gate・検査・
  台帳・一般化の追加は scope 外」。
- **brief 前の実測で依頼の前提が覆った。** R1 の producer (envelope の create-only 書き込みと
  lifecycle start への digest 束縛) も R3 の producer (execution-provenance/v2 の書き出し) も
  既に実在していた。欠けていたのは 33 本の物理 campaign run を実行する executor で、
  33 本ぶんの証拠は **test fixture が作り、呼び手が `result_record_bytes` として手渡していた**。
  起点試行の formal terminal は「実行」ではなく「申告」で成立しうる状態だった。
- **段 3 の 2 レンズはいずれも「plan 作り直し」と判定した。** 親が現物で裏取りし、段 4 で
  executor を scope 外に裁定した ({{D:origin-producer-wiring-blocked}})。結線に要る 4 件のうち
  探索 layout の受理追加は未裁定の受理拡大、source entry point の迂回は規律 2 に抵触、
  台帳 FSM と completion / report は依頼の限定範囲を超える。一次資料は
  `output/insights/2026-09-14/t2293-origin-producer/README.md`。
- **実装したのは待ち合わせ点の移動だけ** ({{D:origin-evidence-rendezvous}})。
  閉じたのは supervisor 経由の bytes 注入経路と path 申告で、**唯一 writer 性は運用前提のまま**。
  「実行が書いた証拠だけを受ける」とは名乗らない。formal consumer を直接呼ぶ経路の受理集合も不変。
- **段 6 レビューが恒真化を 1 件見つけた。** 事前登録した 5 変異のうち「件数 33」「ordinal 昇順」
  「path 相異」の 3 つは recovery envelope の member 検査が既に保証しており、後段では必ず真になる。
  DW-M01 / F28 に従い登録から外し実効 gate へ再照準した ({{D:origin-collection-gate-effectiveness}})。
  **本 wave が足した実効的な新設ゲートは「record から再導出した path と member の宣言の一致」1 本だけ**で、
  その変異の観測 node はちょうど 1 件だった。
- **real だが scope 外と裁定した所見:** 導出先に writer のいない名前付きパイプを置かれると
  共有 read helper の open が戻らない。本 wave が触っていない共有 helper の既存性質で、
  証拠置き場へ書ける敵対者を仮定して初めて成立し、その敵対者は本 wave が宣言した運用前提が
  除外している。依頼も仮想リスク向けの gate 追加を scope 外と明示している。nit 3 件
  (symlink 負例が読取り層まで届かない、親 directory 差替えの競合、受入 duration 台帳への
  新規 23 ケース未登録) も同じ扱いとした。
- **親の記述を 5 点訂正した。** 固定名 `reports/execution-provenance.json` は production の配置では
  なく内容アドレスである。物理 root を作るのは共有 fixture builder でなく test 内の materialize
  helper である。brief の行番号 4 件が古かった。issuance context の field は 15 でなく 14。
  「374〜908 秒」「本番 authority 0 件」「発行 3 条件 0/3」は既存記録の引用であって本 wave の実測
  ではなく、「非 test caller 0 件」は静的な直接参照の確認であって全経路の不存在証明ではない。
- **基底 commit が main 上で書き換えられていた事故。** 着手時の local main `d9bbdb6b0` は
  AI-Agent trailer を欠いており、直後に `75bea8e5f` へ差し替えられて main の祖先でなくなった。
  wave をその commit の上に作っていたため全史 provenance 監査が新規違反 1 件を出した
  (自分の commit ではない)。rebase も reset も使わず、現行 main から worktree と branch を作り直し、
  実装 patch を当て直して commit した。最初の worktree `dev-wave-t2293-origin-producer` と
  branch は未着地のまま残してある (撤去はユーザー裁定待ち)。記録は {{F:wave-base-commit-amended-away}}。
- **手順ミス 1 件:** `dev_wave_codex.py` は author 段で `--reasoning` を受け付けない (rc=2) のに
  付けて 1 回空振りした。DW-C01 に明記がある。再投入は `--job-id` と出力 path を変えた (F953 の再発)。
  段 2 を `--reasoning xhigh` で投げたのも DW-S02 の権威 (medium) からの逸脱である。
- **受入全走は 4 回走らせ、赤はすべて非帰属だった (DW-O18 の判定根拠)。**
  1 回目 child-green。2 回目は `test_t1259_qsub_env_delivery_probe.py` 29 件 +
  `test_s8c_preregistration_predicates.py::test_repository_candidate_uses_real_s8c_budget_module`
  1 件の計 30 error。両 file の単独走は 269 passed で緑。3 回目 child-green。
  4 回目は `test_codex_worker_launch.py::test_sigterm_ignoring_child_is_killed` 1 件
  (23336 passed) で、**当該 node 単独では 7.77 秒で緑**だった (負荷 85 下)。F57 (launcher 族の
  負荷依存フレーク、既載 20 回以上) と同型で、本 wave の差分 (`p3_autonomous_workload_trial.py`) は
  どちらの file にも到達しない。hold 登録はしていない — 単独緑が観測できるため決定的赤ではない。
- **land は共有ロックの飢餓に当たった。** local main が 05:43 から 2 時間半動かず、複数 wave が
  同時に land を叩いていた。lock 待ちの上限 180 秒より全史 provenance 監査 (最大 480 秒) が長いため
  誰も通らない。私の land は 15 回で rc=11 が 14 回、rc=29 が 1 回。rc=29 の本文は
  `provenance audit failed: TimeoutExpired after 480 seconds` で `main_before == main_after`、
  **provenance の赤ではない**。他 2 session から同型の実測と「受入 child-green receipt の mtime 昇順で
  1 本ずつ」という提案が届き、自分の観測と一致したので合意して降りた (私の mtime は 06:29:08)。
  rc=29 が残した orphan hold 2 箇所 (`output/pegasus-dispatch/orphan-hold.json` と
  `orphan-holds/*.json`) は、qstat で対象 job の不在を確認したうえで両方外した。
- 工数: codex 子 6 本 (plan 1 = xhigh 537.8 s / 21 call、consult 2 = medium 233.1 s / 9 call と
  155.0 s / 7 call、author 1 = medium 322.7 s / 16 call、review 2 = medium 139.9 s / 6 call と
  197.4 s / 9 call)。fix 子は所見が real かつ scope 内のものが無かったため起動していない。

## 次の一手差分

### 更新

- [T-2293] **P1・実装中 (待ち合わせ点は着地) → ユーザー裁定待ち (Q1〜Q4)**:
  証拠の所在 (root + 33 path) と bytes は producer 導出になった ({{D:origin-evidence-rendezvous}})。
  **33 本を実行する executor は結線できず、障害 6 件を構造化して返した**
  ({{D:origin-producer-wiring-blocked}}、一次資料 `output/insights/2026-09-14/t2293-origin-producer/README.md`)。
  次はユーザー裁定 4 件 — **Q1** 証拠発行器の受理型に探索 layout を加えるか (加えるなら維持する
  拒否述語と負例を同時に確定する。加えないと executor を作っても record が 1 件も発行されない)。
  **Q2** 台帳遷移の責任境界を fixture ledger 上の integration に限定するか、予約から封印までの
  production FSM を作るか。**Q3** q の候補を実 source へ適用する起点専用 entry point を
  既存の検疫・auditor veto を保つ形で作るか (迂回は規律 2 に抵触するので作らない限り executor は
  候補と無関係な binary の結果を材料にしうる)。**Q4** 完了判定を「fixture authority と台帳遷移を
  許し、空の実行 root から production の executor・runner・issuer が 33 本の lock / WAL /
  provenance / record を生成し、supervisor が disk 回収した証拠で formal consumer が
  P6Unavailable へ到達する」限定 integration へ書き換えるか。
  発行 3 条件は 0/3、本番 authority 0 件のままで、certified 選択・材料レポート・試行台帳の
  現在値は変わらない。
  base: f87fddd3284023896de25debf4487f88baca50272570b26d9f4b007f5e2c1516
