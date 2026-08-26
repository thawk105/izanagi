# CCBench pin bump — 影響範囲の実測 (dev-wave ccbench-pin-precheck-20260827)

基準: izanagi local main `b7f66232` / pin `511c9538e4e8efa54b45cda62e72389ed3b706ec`
上流 clone: `<job>/ccbench-upstream.git` (https://github.com/thawk105/ccbench, 2026-08-27 取得)
実験用 clone: `<job>/izanagi-probe` (sparse, 使い捨て) / `<job>/ccbench-merge-probe` (使い捨て)

**izanagi 側の pin は 1 bit も動かしていない。** pin を進めた測定はすべて job dir の
使い捨て clone の中だけで行った。

---

## F1. pin は master の祖先ではない (依頼の前提を覆す)

- `merge-base 511c9538 master` = `7e268f2a`。`merge-base --is-ancestor` は rc=1 (祖先でない)
- `511c9538` は upstream branch `izanagi-trace-pin-t816` と `izanagi-trace-t816-fn2` の tip
  (2 本とも同一 SHA)。`master` には含まれない
- `511c9538..master` = **16 commit** (#115〜#122)。依頼の「3 本ぶん古い」は誤り
- `master..511c9538` = **8 commit**:
  - `8b82d3e` Silo に `#if TRACE` の検証用トレース口を追加 (izanagi verifier 入力)
  - `fee622f` si (Snapshot Isolation) に検証用トレース口を追加
  - `977e194` トレース口の clang-format 修正
  - `028f34d` write_set lock-coverage assert (izanagi 後続段 3, D38)
  - `d706650` write_set permutation-preservation assert (izanagi 段 5, D41)
  - `511c9538` trace v2 — C 行に read/write 件数、txn 終端に E 行 (T-816, FN-2)
  - `6656e93` WAL preallocation 修正 (上流 `b8f09aa` と同内容の別 commit)
  - `dff0f1e` ODR 違反修正 (上流 `ad33940` と同内容の別 commit)
- **master の `cc/silo/` には "trace" を含む file が 1 件も無い**
  (`git grep -il trace master -- cc/silo/` = 空。pin 側は `cc/silo/transaction.cc` が hit)
- master に `include/trace.hh` が存在しない (pin 側にはある)

→ 「pin を master へ動かす」を素直に実行すると verifier の入力である TRACE 計装が全部消え、
   絶対規律 1 (観測者効果の分離) と規律 3 (正しさシグナル) の土台が失われる。

## F2. `CCBENCH_TRACE` が master の Options.cmake から消えている

`git diff 511c9538 master -- cmake/Options.cmake`:
- **master 側に無い**: `set(CCBENCH_TRACE 0 CACHE STRING "izanagi correctness trace (0=off, perf)")`
  と直上の izanagi 向けコメント 4 行 (D14 / 絶対規律 1 を明記した block)、および
  `ccbench_universal_definitions()` 内の `TRACE=${CCBENCH_TRACE}`
- **master 側で追加**: `set(CCBENCH_SS2PL_DLR 1 CACHE STRING "ss2pl: 0=timeout, 1=no-wait")` (#121)

→ D14 のビルド時完全除去契約が乗っている knob そのものが master には無い。

## F3. 取り込み (merge) なら TRACE は残り、凍結行のずれは 5 行中 1 行だけ

使い捨て clone で `511c9538` に `origin/master` を merge した実測:
- **競合ゼロ** (`Auto-merging cmake/Options.cmake` / `Automatic merge went well`)
- merge 後の Options.cmake: `CCBENCH_TRACE` は 19 行目に**残る**、
  `TRACE=${CCBENCH_TRACE}` は 68 行目に**残る**、`CCBENCH_SS2PL_DLR` が 50 行目に入る
- `include/trace.hh` も残る (master が消したのではなく元々持っていないだけ)

## F4. s1_known_axes_freeze の凍結 bytes への影響 (経路で大きく違う)

`orchestrator/campaign/s1_known_axes_freeze.py`
- `OPTIONS_REL` (:69) = `external/ccbench/cmake/Options.cmake`
- `SILO_CMAKE_REL` (:70) = `external/ccbench/cc/silo/CMakeLists.txt`
- `_stock_common()` (:641-676) が `_unique_cmake_line()` で一意行を取り、
  **`f"{line_no}: {line}"`** の形で `sources[].lines` に凍結する
- golden は `orchestrator/tests/s1_expected_goldens.py:461` の `EXPECTED_SOURCE_LINES`。
  自身のコメントに「固定 ccbench pin (d706650) に対する値で、**pin bump 時だけ裁定つきで更新する**」
  と書いてある。`test_s1_known_axes_freeze.py::test_generate_selects_registered_expected_points`
  が live の working tree を読む `M.build_document()` の結果と照合する

**実 bytes を実コード `_stock_common()` に通した実測** (`K.ROOT` を差し替えて入力だけ入替):

| 凍結行 | 現行 pin (= golden) | master 直行 | master 取り込み |
|---|---|---|---|
| `CCBENCH_BACK_OFF` default | 20 | **15** | 20 |
| `CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION` default | 27 | **22** | 27 |
| `CCBENCH_NO_WAIT_OF_TICTOC` default | 28 | **23** | 28 |
| `CCBENCH_WAL` default | 47 | **42** | 47 |
| `BACK_OFF=${CCBENCH_BACK_OFF}` universal mapping | 63 | **59** | **64** |
| silo CMakeLists 3 行 | 5 / 6 / 10 | 5 / 6 / 10 | 5 / 6 / 10 |
| `flags` 値 (BACK_OFF/NWLIV/NWOT/WAL) | 1/1/0/0 | 1/1/0/0 | 1/1/0/0 |

- **golden と食い違う行数: master 直行 = 5 行、master 取り込み = 1 行。**
- どちらの経路でも `_unique_cmake_line` の一意性は保たれる (`FreezeError` にはならず、
  値が変わる形で影響する)。行本文と flag 値は全経路で不変
- 現行 working tree の Options.cmake は 20/27/28/47/63 で golden と完全一致 (= 今は緑)

→ 更新が要るのは `EXPECTED_SOURCE_LINES` の Options.cmake 側だけ。silo 側 3 行は触らなくてよい。
   decisions.md:3552 が「lines は literal — pin bump 時のみ裁定つき更新」と定めているので、
   **これはユーザー裁定を要する編集**である。

## F5. s8b_holdout_freeze の凍結 bytes は実質影響なし

- `enumerate_repository_files()` (:369-383) が `external/ccbench/` 配下の tracked regular file
  を全部集める。凍結されるのは `search.file_count` (整数)・軸別一致 file 数・`conjunction_hits`。
  **path の全列挙そのものは凍結されない**
- ccbench tracked regular file 数: pin **404** / master **404** / 取り込み **405**
  - master 直行: `-cc/ss2pl/ss2pl.cc`, `-include/trace.hh`, `+cc/ss2pl/include/dlr0_timeout.hh`,
    `+cc/ss2pl/ycsb_ss2pl.cc` (±2 で相殺)
  - 取り込み: `-cc/ss2pl/ss2pl.cc`, `+dlr0_timeout.hh`, `+ycsb_ss2pl.cc` (`trace.hh` は残る)
- 三軸 literal は `git diff 511c9538 master` の追加行・削除行に **1 件も現れない** (rc=1)。
  追加/削除された file の全行も diff に出るので、これで新規 file 側も否定できている
  → 軸別 count・`conjunction_hits` は不変
- 記録済み `holdout_freeze.json` の `search.file_count` = **1197**、
  live 実測 = **15,236** (うち ccbench 404)。**既に 13 倍ずれている**
  (`s8b-holdout.frozen-head-current-head` の保留下)。ccbench の ±1 は識別不能

補足: `s8b_ratified_freeze._enumeration_digest()` (:1437) は path 名集合の sha256 なので
名前が変われば動くが、走査前後の TOCTOU 比較 (:3446/:3454) にしか使わず凍結 doc へ持続化しない。

## F6. 床値 protocol の解決が pin bump で確定的に落ちる (最大の影響、実測済み)

`orchestrator/campaign/s8b_floor_campaign.py::resolve_current_floor_protocol` (:1017-1060)、
契約の正本は **D491** (2026-08-17):
1. 現行 env 契約と `contract_sha256` が一致する候補集合 `C` を作る
2. `len(C)==0` → fail-closed
3. `len(C)==1` → **gitlink を読まずに**返す
4. `len(C)>=2` → HEAD gitlink と一致する部分集合 `E` を作り、`len(E)==1` のときだけ返す。
   それ以外は `current_count` / `head_exact_count` を添えて fail-closed

現状の索引 (実測、どちらも contract `e576e9cd…` / env_tag `pegasus`):

| record | ccbench_pin |
|---|---|
| `output/s8b-freeze/floor_protocol.json` (legacy anchor) | `d706650c…` (= PREVIOUS_PIN) |
| `output/s8b-freeze/floor-protocols/e576e9cd…--511c9538….json` | `511c9538…` (= CURRENT_PIN) |

**使い捨て clone で実際に gitlink を `b28f96b6` (master) へ進めて resolver を走らせた実測:**

```
BASELINE resolved: output/s8b-freeze/floor-protocols/e576e9cd…--511c9538….json
AFTER BUMP FAILED: FloorCampaignError
現行 env 契約の floor protocol を一意に解決できない: current_count=2 head_exact_count=0
```

→ `C=2` なので pin が現に効いている。pin を動かした瞬間 `E=0` になり床値 admission が止まる。
   これは fail-closed の設計どおりの挙動であって、静かに値が壊れる型ではない。
   consumer は `s8b_holdout_admission.py:679` と `certified_writer_admission.py:201`。

**D491 は `E` 判定の導入時に「発行後は候補が 2 件になる」ことを前提にしており、
3 件目の発行 (= 同一 contract・新 pin) で `E=1` に戻る設計である。**

## F7. 復旧手順は既に裁定済み (D444 / D471 / D491)

- **D444** (2026-08-16): 床値 protocol のうち AI が更新してよいのは
  `contract_sha256` と `ccbench_pin` の 2 field だけ。残る 16 field は先行 protocol から
  **byte-exact に継承**する。格納 path は組から一意導出。issuer の公開 API は**零引数**
  (`s8b_floor_campaign.reseal_protocol()` :1237)
- **D471** (2026-08-17): 契約単位の封鎖を撤去し、同一 `contract_sha256` のまま
  `ccbench_pin` だけを進めた 2 件目の発行を許した。
  「**contract 据え置き・pin 前進**」が採られた案の唯一の実行形
- **D491** (2026-08-17): D460 の「選択条件に ccbench pin を入れてはならない」を
  この範囲で狭く撤回し、現行の `C`/`E` 契約を確定した

→ **床値の再取得 (再計測) は要らない。** 16 field を byte-exact 継承する再発行だけで済む。

ただし `reseal_protocol()` は発行前に **live gitlink と `s8b_approved.CCBENCH_FULL_SHA` の
一致を要求**する (`s8b_floor_campaign.py:1280-1285`「現在値の追認を拒否」)。
発行される document の `ccbench_pin` もこの承認定数から焼く (:1297)。
よって pin bump では `s8b_approved.py:67` の承認定数の更新が**先に**要る。

## F8. E1-stale は 1 件も起きない

- E1 epoch は `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` の **exact 25 path の blob sha256**
  だけから導出される (`artifact_admission._recorded_campaign_verifier_epoch` :784-822)
- 25 path は env_contract / env_contract_activation / execution_guard / loop / pipeline / wal /
  ident / artifact_admission / verifier 6 file / s8c 3 file / campaign_lock /
  contract_loader_binding / enforcement_source_ratification / guided / replay /
  qualification/artifacts / qualification/t126_driver / commit_receipt
- **`external/ccbench` 配下も `pin.py` も `s1_known_axes_freeze.py` も `s8b_approved.py` も
  `s8b_floor_campaign.py` も 1 件も含まれない**

→ **pin bump 単独では既存 campaign は 1 件も E1-stale にならない。**

gitlink 消費点の挙動:
- `orchestrator/qualification/identity.py:124-127` — 記録済み superproject commit から gitlink を
  再導出して pre-image と照合。過去の記録は自分の commit を指すので成立し続ける
- `orchestrator/campaign/certified_writer_admission.py:363-369` — 記録行の `source_commit` の
  gitlink を照合。同上、既存行は無傷
- `orchestrator/qualification/t126_driver.py:403` — `HEAD:external/ccbench` を実測。literal なし。
  **新規 series の identity だけが動く**
- `orchestrator/campaign/ident.py:168` — `ccbench_commit` が campaign-id の pre-image に入る。
  pin 前進後に作る campaign は campaign-id が変わる (`pin.py` docstring が
  「既知・正直な content-addressed 挙動、バグではない」と明記)。既存 campaign-id は動かない

## F9. 凍結検証の保留 (HELD) が pin ドリフトを既に吸収している

`orchestrator/campaign/freeze_verification_hold.py`: **`HELD = True`**、
裁定 `rulings-4th-batch-2026-08-12` (2026-08-12 ユーザー裁定)、
解除条件は `explicit-user-command-only` (ユーザーの明示命令のみ)。

保留中の check は 21 件。うち **pin 照合そのものが 9 件**:
`s1-known-axes.ccbench-submodule-head-pin` / `s1-measurement.recorded-pin-current-pin` /
`s8b-floor.protocol-bytes-expected-pin` / `s8b-floor.sealed-protocol-ccbench-pin-current-head` /
`s8b-oracle.known-axes-recorded-pin` / `t080.draft-known-axes-ccbench-current-pin` /
`t080.live-known-axes-ccbench-current-pin` / `t080.static-known-axes-ccbench-current-pin` /
`t080.static-known-axes-recorded-pin`

裏づけ: canonical `output/s1-freeze/known_axes_freeze.json` の `ccbench_pin` は
**`d706650c…`** (現行 pin ではない)。**izanagi は既に一度 pin を前進させ (d706650 → 511c9538)、
その差を保留で持ち越している。**

→ pin 照合系への追加コストは、保留が続く限り**ゼロ**。ただし**負債は 1 段深くなる**
   (解除時に再凍結すべき距離が伸びる)。
   一方 **F4 の golden と F6 の resolver は保留の対象外**で、どちらも保留に守られない。

## F10. pin literal の全在庫と、bump で赤になる箇所

`git grep -l 511c9538 -- . ':(exclude)external/ccbench'` = **119 file**。

**bump で更新が要る live な束縛 (7 件):**

| path | 形 | 備考 |
|---|---|---|
| `orchestrator/campaign/pin.py:28` | `CURRENT_PIN = "511c953"` (7 char) | 正本。参照 driver 14 本が自動追随 |
| `orchestrator/campaign/s8b_approved.py:67` | `CCBENCH_FULL_SHA` (40 char) | **承認定数**。`test_s8b_approved.py:60` が live gitlink と照合 → bump で即赤 |
| `orchestrator/campaign/silo_ladder_rung1.py:57` | `PIN` | |
| `orchestrator/campaign/silo_ladder_rung1_contract.py:543` | `"base_commit"` | |
| `tools/pegasus/mocc_trace_v1_policy.json:16` | `mocc_trace.base_oid` | **F11 参照** |
| `orchestrator/tests/test_mocc_trace_job_contract.py:29` | `BASE_OID` | |
| `orchestrator/tests/test_mocc_trace_pair.py:17` | `BASE_OID` | |

**golden・台帳 (裁定つき更新が要る):**
`orchestrator/tests/s1_expected_goldens.py:461` の `EXPECTED_SOURCE_LINES` (F4)、
`output/s8b-freeze/floor-protocols/…--511c9538….json` (file 名に pin。追加のみ・上書き禁止)。

**触らないもの:** `docs/archive/worklog-*.md` 21 件、`output/insights/**` 多数、
`patches/ledger.json`、`tools/known_violations/*.json` 4 件、`docs/decisions.md`、
`docs/failures.md`、`docs/paper-story/claim-evidence/2026-08-26.md`、
`docs/phase3-8b-restart-runbook.md`、`output/env/pegasus/calibration/*.json` 2 件 —
いずれも歴史記録であり、当時の pin を指したままが正しい。

**影響を受けない driver 群:** `pin.CURRENT_PIN` を参照する 14 本 (`s1_verify_extime_calibration`,
`s8a_trigger_coverage`, `axis_trigger_gating`, `s5_permutation_coverage`, `backoff_sweep`,
`s6_sort_sweep`, `paper_story_a1_paired`, `s3_lock_coverage`, `s1_measurement_freeze`,
`pegasus_floor_scoping`, `between_run_floor`, `p3_s4_loop_sort`,
`autonomous_trial_completeness`, `paper_story_a2_certification`) は literal を持たず自動追随。
歴史的 driver (`p3_kickoff` / `p3_s4_red` / `p2_2` / `backoff_repro` / `sanity_silo` / `demo` /
`s2_verify_calibration`) は `KICKOFF_PIN = dff0f1e` を保持し無関係 (`pin.py` の IDENT-1/IDENT-3)。

## F11. 稼働中の MOCC trace branch が pin の上に乗っている

ローカル module に `refs/izanagi/ccbench/t1506/mocc-trace-include` = `058d0c4e` があり、
系譜は `511c9538` → `ef9328a3` (feat(mocc): correctness trace v2 hook) → `058d0c4e`。
upstream には無い (未 push)。`tools/pegasus/mocc_trace_v1_policy.json` が
`base_oid = 511c9538` / `new_oid = 058d0c4e` の対で参照する。

worktree 一覧に `dev-wave-t1506-mocc-trace0` が稼働中。
→ pin を動かすと、この branch も base ごと動かす必要が出る。**進行中 wave との調整が要る。**

## F12. 取り込みの便益 (依頼の前提のうち正しい部分)

- `cc/ss2pl/ycsb_ss2pl.cc` は pin 側に無く master にある → **SS2PL の YCSB 入口が無いのは事実**
- #122 (`df47e3a`) の commit 本文が SIGSEGV の機序を明記:
  `TxExecutor::read()` / `update()` が lock を取れないとき `status_ = aborted` にしながら
  `Status::OK` を返すため、呼び手が `TupleBody*` を無関係な `read_set_` entry
  (read set が空なら未初期化) のまま dereference する。TPC-C Payment が全 trx で
  Warehouse 行を更新するので 2 スレッド以上で数秒以内に確定的に落ちる
  → **`tpcc_ss2pl.exe` の確定的 SIGSEGV は事実で、#122 が直している**
- #121 (`ff291e4`) は DLR0 timeout を実装し `CCBENCH_SS2PL_DLR` を追加。
  configure 時に `-DCCBENCH_SS2PL_DLR=0` を選んだときだけ `-ss2pl_dlr0_timeout_us` が効く。
  既定は `1` (no-wait) で従来挙動
