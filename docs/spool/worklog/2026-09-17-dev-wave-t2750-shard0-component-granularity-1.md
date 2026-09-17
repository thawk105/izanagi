---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2750-shard0-component-granularity
seq: 1
title: [T-2273][T-2750] 受入 shard-0 の連結成分粒度 (file → node) は実装せず閉じた — 台帳 refresh 後の受入 20 走 (同時刻対照) で shard の wall は「最長 node + 相方 約 20 秒 + 固定費 66 秒」で決まり、案 (a) の offline 割付は負荷を均等化しても最遅 shard の予測 306.1 秒を動かさず、素直な案は real-repo の跨ホスト排他を外す (docs のみ、branch worktree-dev-wave-t2750-shard0-component-granularity、変異 matrix = 実装面差分ゼロにつき免除)
---

## 本文

- ユーザー依頼は「受入の最新律速 = shard-0 の連結成分 (`campaign-repository-scan` / `real-repo` / `s8c-predicate-snapshot` /
  `s8c-preregistration-candidate` の 4 xdist group が 1 成分、`conftest.py` の `REAL_REPO_RESOURCE_NODES` が `real-repo` を動的付与、
  台帳予測 7502 秒 / 実測 8569 秒 / 均等なら 6053 秒) を `tools/acceptance_shards.py` の `allocate` で解く — 案 (a) 成分単位を
  file から node へ (順序依存の検査が先)、案 (b) 大 file の real-repo node を別 file へ分離。D358 と受理集合は変えない。採用条件 =
  検出力維持と D104 の効果実証 (同時刻対照つき、n=1 の前後比較で主張しない)。実装面は Codex author、変異事前登録要。本題の
  分割改善だけ、追加 gate・検査・台帳は scope 外」。
- **閉じた (実装せず)。** 一次資料は `output/insights/2026-09-17/t2750-component-granularity/README.md`。設計判断は
  {{D:shard0-component-granularity-no-wall-gain}}。実装 commit なし (docs-only)。
- **段 1 の前提実測が起票の前提を覆した。** 台帳 refresh 後の受入 20 走 (2026-09-17 09:34〜12:26、他 wave の受入 = 同時刻対照) で
  shard-0 の最忙 worker は 20 走すべてで item 2 個 (最長 node `test_s8b_oracle_driver.py::…_b5[ccbench-current…]` 225〜500 秒
  + 相方、相方は 17 走で 19.8〜20.1 秒)。最大 worker 占有 − 最長 node = 中央値 19.9 秒、wall − 最大占有 = 中央値 66.1 秒、
  平均 worker 負荷 (直列和 ÷ 48) = 161〜417 秒で 20 走すべてで最長 node より小さい。99 session の最遅 shard は shard-0 が 94、
  shard-2 が 4、shard-1 が 1 (最遅 shard wall 中央値 359.1、shard-0 wall 中央値 352.9、300 秒以下は 3 走)。
- **生死実験 (DW-G01) = 案 (a) の offline 割付 simulation。** collect-only 24660 node + 現行台帳で、現行 7523 / 5372 / 5372 秒 →
  案 (a) 6089 秒 × 3 に均等化されるが、D1019 の makespan 式 max(最長 node, 負荷/48) + 66.1 では最遅 shard の予測が 3 通りとも
  306.1 秒で同値。予測 wall の合計は 690 → 748〜838 秒へ増える。衝突成分は 3929 node / 7523 秒 → 188 node / 1612 秒。
- **段 2 plan と段 3 の 2 レンズ (正しさ境界 / 実効性) が独立に「実装しない」を支持し、親の言い方を 3 点訂正した。** (a) 素直な
  案 (a) は `test_s8c_preregistration_predicates.py` の候補 commit 生成 fixture の consumer (group 無し・inventory 外、function
  fixture が実 object store へ書く) の跨ホスト排他を外す — file 閉包だけが同 host に留めている (fixture-owned golden に明記、親が
  code で確認)。(b) 「期待利得 0 を実証」「一次資料の床の主張は偽」は飛躍で、正しくは「固定 duration model では最遅 shard の
  下限不変、実 wall 改善は未実証、採用条件不成立」。(c) brief の誤記 2 点 (平均負荷 161〜221 → 161〜417、tail 19.9 秒は 20/20 でなく
  17/20) と D358 要約 (D1618 の runtime 分割を反映)。規律 2 の射程判定は (c) 一部だけ射程内。
- **親の追加実測 2 点。** 相方は xdist 初期配布 (各 worker に 2 unit) の構造で、session `5141225c` では
  `test_codex_reasoning_ab.py::test_m3_ignored_extra_and_missing` (台帳 22 秒) と同定 (順位説明は G11 により一般化しない)。
  最長 node の所要は同 shard の他 worker 占有と r=0.993、別ノードの shard とは r=0.07 だが、同一割付内では仕事量が一定なので
  ノード状態で説明でき、「仕事量を減らせば速くなる」の証拠にはならない。
- 実走 (login node、bounded local、記録 commit 前): 三軸語走査 `s8b_holdout_freeze search` rc=0 (hit 0、本 wave の file を含む)。
  `test_s8b_repo_scan_invariant.py` + `test_real_repo_serialization.py` の焦点走は **105 passed / 2 failed / 2 skipped / 62 秒**。
  赤 2 件は差分到達不能と判定した (DW-O18): `test_t080_import_temp_environment_fails_closed_for_foreign_module` は fresh worktree の
  初回走で並行 worker が `output/insights/2026-08-05_t471-restore-bound/driver/__pycache__` を作り output/ の snapshot が変わったもので、
  単独再走で緑 (非再現)。`test_real_repo_writers_do_not_materialize_oracle_environment_candidates` は `p3_s4_loop._admit_env_contract`
  の site guard (`site='PEGASUS_LOGIN' では生成できない`) で login venue では決定的赤、単独再走でも赤、受入 venue (計算ノード) の
  直近 main 受入 `5141225c` では両 node とも passed。本 wave の差分は docs のみ (`output/insights/` と `docs/spool/`) で両経路に触れない。
  受入全走は記録 commit 後の最終 tip に対し land 前に 1 回 (結果は land の受領証)。
- 工数: codex 子 3 本 (plan 1、consult 2、全部 `gpt-6-astra` / `medium` / read-only、accepted 3/3)。author / review / fix は
  起動していない。親の実測は解析 script 8 本 (repo 外、sha256 は insight)、collect-only 1 走、焦点走 1 本、受入 1 走 (land 前)。

## 次の一手差分

### 完了

- [T-2750] 成分粒度 (file → node) は実装せず閉じた。48 worker では shard の wall は最長 node + 相方 + 固定費で決まり、案 (a) の
  offline 割付は負荷を均等化しても最遅 shard の予測 306.1 秒を動かさず、素直な案は real-repo の跨ホスト排他を外す。詳細は
  `output/insights/2026-09-17/t2750-component-granularity/README.md` と {{D:shard0-component-granularity-no-wall-gain}}。
  remaining: none
  base: 6fc2828990efb600afc4922e482309086686ebb8cb5e3fedd600237c46530698

### 更新

- [T-2273] **P1・律速を再同定、300 秒目標は割付では届かない**: 受入の最遅 shard (99 session 中 94 で shard-0) の wall = 最長 node
  (t080 e2e b5 群 5 本、225〜500 秒) + 相方 約 20 秒 + 固定費 約 66 秒 ≈ 311 秒 (最良時)。負荷の均等化 (成分粒度) では動かない
  ({{D:shard0-component-granularity-no-wall-gain}})。次の候補は {{T:reorder-pairing-longest-unit}} (上限 5.8%)、
  {{T:node-granularity-paired-trial}} (期待値未数値化)、b5 群の単体所要 (D2068 が fixture 側 3 案を却下済み、e2e の分割・parametrize の
  縮約は受理集合に触れるため別裁定)。次も実測で律速を選び、効果を先に測ってから実装する。
  base: 937e28ecf14fc0755ce7fc3210ef5f73845089ad2c4e995381f759b5dfd9d305

### 新規

- {{T:reorder-pairing-longest-unit}} **P3・新規**: 受入 shard 内の cost 順 reorder で、最長 unit を持つ worker の 2 個目の初期 unit
  (xdist の #277 heuristic、現状は cost 順で約 20 秒の test) を最小 unit にする pairing。台帳 refresh 後の 20 走で最忙 worker の
  tail は 17 走で 19.8〜20.1 秒 (最遅 shard wall 中央値 347.7 秒の 5.8% = D357 の「変化なし」域)。実 scheduler の配布順
  (`test_acceptance_schedule_order.py` の G11: collection 順と dequeue 順は一致しない) の確認が先。採用は同時刻対照つきの
  効果実証 (D104) を条件とし、効果が示せなければ land しない。Codex author。
- {{T:node-granularity-paired-trial}} **P3・新規**: 成分粒度 (file → node) の安全な試作と paired 測定。前提 = 明示 affinity の補完
  (`ItemRecord` / record parser / `assignment_closure_gate`、file 閉包に依存する fixture-owned consumer を衝突成分へ束縛)、
  D711 gate 4 の裁定改訂、衝突閉包 (resource node + fixture-owned consumer + 明示 affinity) の独立 literal 検査。測定 = 同一 tip・
  同一 collection・同一台帳で旧/新割付を交互 n≥3 (A-B / B-A) の `max(shard wall)` + 機構発火の直接観測 (別 shard へ出た node 数・
  file 数・各 affinity が同一 host に残った事実)。期待値は未数値化 (経路は同 host 競合の低減だけ)、費用 ≈ Codex author + 変異 +
  受入 ≥6 走。一次資料は `output/insights/2026-09-17/t2750-component-granularity/README.md`。
