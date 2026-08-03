# 段 1 brief — [T-342]+[T-343]+[T-344] を一体で塞ぐ

## scope と確定済みユーザー裁定

3 件一体。分割すると片方が迂回路になる (ユーザー明示)。

- **T-342 = (a)**: build provenance を source 由来の capability へ移す (source digest / clean 検査 /
  generator identity / review receipt)。**CLI authority も同時に移す** (部分実装は採らない)。
- **T-343 = (a)**: admission を cache / replay identity へ束縛する (legacy cache key・v2 preimage・
  completion manifest・campaign preimage)。**receipt 欠落の旧 entry は拒否し、明示 migration はしない。**
- **T-344 = (a)**: 段 5 / 段 8a の旧成果物は overlay で既定除外。**凍結 bytes は触らない。**

本 wave は正しさ防壁 (受理集合) を変えるため軽量版にしない (`DW-C00`)。段 2・3 と段 6 の敵対レビュー 2 本を行う。

## 不変条件 (段 1 で実測済み)

1. **`orchestrator/campaign/s1_known_axes_freeze.py` は編集禁止。** 実測: 同ファイルの sha256
   `1d4d45a3de4926c6aae76906f7b4b72d3fead51e9cdf62ff03f80a0379c364e0` が 3 箇所に pin される —
   凍結 `output/s1-freeze/known_axes_freeze.json` の `/generator/sha256`、
   `orchestrator/campaign/t080_freeze_migration.py:110-115` の `METADATA_SPECS` 定数、
   `orchestrator/tests/test_s8b_oracle_driver.py:95`。1 byte でも変えると赤。
2. **`FROZEN_MANIFEST` (`orchestrator/tests/test_frozen_artifacts.py:38`) の 23 件は bytes 不変。**
   overlay 台帳は凍結集合の外に新規ファイルとして置く。
3. **既存 drift は直さない (段 1 で判明した新事実)。** clean tree・main HEAD で
   `s1_known_axes_freeze.verify_document(凍結 doc)` は**既に FAIL する**。凍結 doc が pin する 63 source の
   うち `s8a_trigger_sweep.py` / `s6_sort_sweep.py` / `p3_s4_loop_sort.py` / `backoff_sweep.py` の 4 本が
   T-316 の編集で drift 済み。本 wave がこの 4 本を再度編集しても**新規の赤は生まない**が、
   drift を直す (= 凍結 JSON の再生成) は凍結 bytes 改変なので**やらない**。
4. **凍結 doc が pin する source 集合に、T-342/T-343 の中核編集面は含まれない。** 含まれないと実測したのは
   `buildcache.py` / `build_admission.py` / `pipeline.py` / `loop.py` / `ident.py`。
5. **`docs/` の 3 runbook (`phase3-s4b` / `phase3-s5-sort` / `phase3-s8a-trigger`) は親が直す。**
   実装子は docs を編集しない (凍結境界)。

## 発火 path の実在 (`DW-G04` / `DW-O13`)

- **T-344 の overlay 対象 (実測)**: `output/campaigns/` 配下の 3 loop campaign で
  `build_start` に receipt が 1 件も無い —
  `p3-s4-loop-s4-autonomous-0b53a387` (build_start=3, receipt=0)、
  `p3-s5-sort-loop-s5-sort-autonomous-3be89e0d` (1, 0)、
  `p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5` (2, 0)。
- **capability の材料は実在 (`DW-O13`)**:
  `source_digest.src_token()` (`source_digest.py:650`、HEAD と同一なら `STOCK`)、
  `source_digest.assert_worktree_within_allowlist()` (`source_digest.py:662`、tracked 改変の allowlist 検査)、
  `source_digest.resolve()` (`source_digest.py:701`、identity 単一窓口)、
  `orchestrator/codex_roles/review_ledger.py` (role review pin)。
- **CLI authority の現況**: `--allow-coder-derived-build` は 5 driver にあり
  (`p3_kickoff.py:89` / `p3_s4_red.py:130` / `p3_s4_loop.py:801` / `p3_s4_loop_sort.py:366` /
  `p3_s4_loop_trigger_gating.py:687`)、いずれも plain bool を `BuildAdmission` へ渡している。

## 成果物影響 (`DW-G05`)

- **T-342 を実装しないと**: 同一 `CODER_DERIVED` bytes を `STOCK_OR_PINNED` と自己申告するだけで
  certified 受理集合へ入り、`median_tps` と certified 選択の provenance が偽装できる。
- **T-343 を実装しないと**: cache hit と WAL replay が class を跨ぐため、別 class の run で作られた
  binary・`median_tps`・certified terminal を現在の run の provenance へ付け替えられる。
- **T-344 を実装しないと**: receipt を持たない旧 loop 成果物が admission-aware な選択と
  材料レポートへ既定で流入し、proof chain が「T-316 containment 下で admission された測定」を
  証明できないまま certified 扱いになる。

## 親の provisional 裁定 (すべて攻撃対象)

- **(P1)** class は caller が選ぶ値でなく evidence から導出する。caller が class を宣言する場合は
  evidence と exact 一致しなければ拒否する。`src_token == STOCK` かつ tracked-clean なら
  `STOCK_OR_PINNED`、以外は evidence 次第。
- **(P2)** CLI authority は plain bool を廃し、CLI parser だけが発行する run-scoped token にする。
  in-process の `True` は受理しない。
- **(P3)** legacy `cache_key()` は class が `STOCK_OR_PINNED` 以外のときだけ `|adm=` 相当を足し、
  旧 stock key を温存する (`src_token` / toolchain と同型の後方互換規則)。
- **(P4)** v2 は `_v2_identity` の preimage と completion manifest の両方に admission を入れる。
  manifest の field 集合は exact 検査なので、receipt を持たない旧 entry は拒否側に倒れる。
- **(P5)** campaign 側は campaign id (`ident.canonical_preimage`) を変えず、`campaign.lock` へ
  admission policy を焼き込み、`ident._verify_screening_policy` と同型の lock 照合を足す。
  さらに resume 時に既存 `build_start` receipt を現在の admission と exact 照合する。
  **この形なら旧 3 campaign の resume で実発火する** (id を変えると旧 dir が沈黙 orphan になり発火しない)。
- **(P6)** T-344 の overlay は `output/` 配下の新規 JSON 台帳 + 共有 reader モジュールとし、
  campaign id と WAL sha256 を鍵に `legacy-unclassified` を宣言する。admission-aware な選択・
  材料レポートは既定で除外する。凍結 bytes と `s1_known_axes_freeze.py` は触らない。

## 成果物の形と分割方針

- コード: `orchestrator/campaign/build_admission.py` (capability 発行)、`buildcache.py` (legacy key /
  v2 preimage / completion manifest)、`ident.py` + `loop.py` (campaign lock と replay 照合)、
  新規 overlay モジュール + 台帳、全 caller の配線更新、テスト。
- docs: 親が 3 runbook・decisions・worklog fragment を書く。
- 分割は段 4 で確定する。候補は A=capability + CLI authority、B=cache/replay identity、
  C=overlay + consumer。B は A の公開 API に依存するため直列化するか、A の API を段 4 で先に凍結する。

## 受入・実測環境

`tools/run_tests.py` 経由で Pegasus 計算ノードへ dispatch する。login ノードでの pytest 直起動は
hook が機械拒否する (段 1 で実測)。所在は worklog、機体固有情報は環境 runbook を正本とする。
