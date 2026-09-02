---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2199-s4-loop-pegasus-build
seq: 1
title: [T-2199] 段 4 loop を Pegasus で build へ到達させる道は認可 gate で塞がっていた — 実行場所は Pegasus で決着し、配線は p3 所有 wave へ渡す (docs のみ、branch worktree-dev-wave-t2199-s4-loop-pegasus-build、実装面の差分 0)
---

## 本文

- **本 wave は実装しないと裁定した (段 4 裁定 C2)。** 目的 (Pegasus 計算ノードで段 4 loop を
  build へ到達させる) が、ユーザーの指定した編集面 (`tools/pegasus/` と job script 側) では
  到達不能だったためである。停止点は `execution_guard.py:136-159` の認可検査で、直すには
  `p3_s4_loop.py` の 5 か所を site-aware にする必要がある。同 file は稼働中の t2145 wave の所有で、
  ユーザーは「触る必要が出たら止めて報告する」と定めていた。
- **親はこの到達不能をコードの実見で確定した。** 段 2 の主張をそのまま採らず、
  `p3_s4_loop.py:111,1428-1433` → `loop.py` の `_authorize_measurement` →
  `execution_guard.py:136-159` → `env_contract.py:292-311` の 4 点を自分で読み、
  `linux-baremetal` の `attestation_mode` が `"none"`、`pegasus` が `"required"` であるため
  Pegasus compute では拒否されることを確かめた。
- **編集面の内側に残った唯一の案 (PATH の CMake wrapper) も採らなかった。** 段 3 レンズ A が
  real 所見として、gate は wrapper を CMake 実体として実行するのに green record が
  CMake path も wrapper hash も実効 configure argv も保存しないと指摘した。
  `condition_meaning_gate.py` を 1 byte も変えなくても受理集合の変更になる。詳細は {{F:path-wrapper-changes-acceptance-set}}。
- **実行場所の択一は Pegasus で決着した ({{D:s4-loop-stays-on-pegasus}})。** 段 2 の起草子は
  cygnus を推奨したが、比較の cygnus 側が過去の成功 4 iteration、Pegasus 側が目的の異なる 6 投入で、
  沈んだ費用を将来費用として読んでいた。段 2 自身が現在の cygnus 到達性を未確認と書いており、
  親の実測でもこの session の ssh 設定に cygnus の entry は無い。段 3 の両レンズが独立に
  Pegasus 継続を支持した。**「cygnus では不可能」とは言っていない — 費用の項が欠けていると言った。**
- **brief の前提 2 件が段 3 で反証され、親が撤回した。** (P1)「Pegasus の env 契約が登録済みだから
  正式採用の 4 前提は充足済み」は、登録の層では正しいが対象 job の層では誤りだった
  (D59 条件 3 は計測ごとに再成立させる義務、条件 4 はこの job について未実装)。
  (P4)「env_tag と物理環境の不一致は block 理由にしない」は現行 guard と正面衝突する。
  **ラベルの不一致で作業を止めない一般則と、現に効いている防壁を迂回しないことは別である。**
- **preprocess 失敗の診断は確度が上がったが確定していない。** 段 2 の `config.h` 仮説
  (確信度 0.85) を、親が前 wave の残存 configure 木を実見して裏取りした
  (`FETCHCONTENT_SOURCE_DIR_MASSTREE` 空、`_deps/masstree-src` は clean clone、`config.h` 皆無)。
  ただし前 wave は stderr を保存しておらず、同じ reason code へ落ちる条件は 7 つある。
  literal な原因の確定には至っていない。
- **配線の先例が repo 内にある。** `p3_s4_loop_trigger_gating.py` は既に site-aware で、
  site を契約へ写像し (未知 site は fail-closed)、`authorize(contract.env_tag)` を渡している。
  p3 所有 wave はこの兄弟 file の形を写せばよい。新設ではなく移植である。
- 段 3 が scope 外の real 所見を 3 件返した (PATH wrapper 経由の trace + strip 同時注入で
  `nm -C` 検査を抜ける経路、p3 CLI が aborted でも rc=0 を返し condition の canonical record を
  保存しない、p3 経路の単独性確認が canary 付き probe でなく plain `pgrep`)。いずれも編集面の外。
- 実装面の差分がゼロのため変異 matrix を免除した (`DW-S04`)。受入全走は実施した。
- 子の工数: 段 2 プラン 52 call / 1404 秒、段 3 レンズ A 45 call / 1052 秒、
  レンズ B 35 call / 823 秒。3 本とも `accepted`。

## 次の一手差分

### 更新

- [T-2199] **P1・部分完了**: 実行場所の択一は Pegasus で決着した (D59 の 4 前提を
  この job について満たす方向)。残るのは段 4 loop の環境契約配線で、これは
  `orchestrator/campaign/p3_s4_loop.py` を所有する wave が行う。preprocess の
  `config.h` 不在は job script 側で解けるが、PATH wrapper で解いてはならない。
  base: 3d4fd2fd8d2cae4ca5825b2cbf783173b9898816e2d7161d55ab8c5e67aef467
- [T-2182] **P1・部分完了**: K2 入力経路の生死確認は済んだ。評価経路の実行場所は
  Pegasus で決着したので、残りは配線待ちである。受領証・campaign 識別子・role 入出力の逐語は
  保存済みなので、評価経路が通った時点で残り 3 条件だけを確かめればよい。
  base: e60387a77d61a9c0b3069c58f246122795d9121baeb8232543c10aa769dd8910

### 新規

- {{T:s4-loop-site-aware-contract}} **P1・新規**: 段 4 loop へ site-aware な環境契約配線を移植する。
  `p3_s4_loop_trigger_gating.py` の `_site_admits_measurement` / `_admit_env_contract` /
  `_campaign_cfg_for_site` と `authorize(contract.env_tag)` の形を、`p3_s4_loop.py` の
  `ENV_TAG` 固定箇所と `run_campaign` 呼出しへ写す。**新設ではなく移植である。**
  着地すれば Pegasus 計算ノードで build へ到達しうる。次に出る障害 (attestation の exact 照合、
  reservation と claim root の束縛) は未実測の予測である。
- {{T:s4-loop-pegasus-job-script}} **P2・新規**: 上の配線が着地した後に、段 4 loop 用の
  Pegasus job script を作る。**PATH の CMake wrapper で third-party を注入してはならない**
  ({{F:path-wrapper-changes-acceptance-set}})。masstree の `config.h` を事前に建てる経路と、
  計算ノードでの `python3` 3.10 shim、raw qsub の `-o` / `-e` の repo 外転送、
  admission registry と手順書投影と README の tagged qsub command の同時同期が要る。
