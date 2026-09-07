# [T-2232 後続] 段 4 loop Pegasus job body の初回投入

着地済みの `tools/pegasus/p3_s4_loop_pegasus.sh` を **Pegasus 計算ノードへ初めて実際に投入した**
wave の一次資料。job body・登録簿・手順書は変更していない (実装面の差分ゼロ)。

## この wave が立った経緯

依頼は「[T-2199] の残件 [T-2232] を実装する」だったが、[T-2232] の実装は
**2026-09-07 03:19 に main へ着地済み**だった。依頼本文は land 自身の fold が書いた持ち越しである。

| 照合対象 | 値 |
|---|---|
| land 受領証 | `status=landed`、`main_after=1a820a913`、`tested_tip=e59d8e4c3` |
| ancestry | `git merge-base --is-ancestor 1a820a913 HEAD` = 0 |
| worklog | entry (1286)、`docs/archive/worklog-phase3-0907-1285-1286.md` |
| 一次資料 | `output/insights/2026-09-05_t2232-s4-loop-pegasus-job-script/README.md` |
| 変異 | 16/16 KILLED、期待 node 完全一致 |

同 entry が残件として名指ししていたのは「初回投入と reservation / attestation の実効確認は
後続 wave」であり、後続 wave は本 wave まで存在しなかった。`DW-S01` / F35 の
「stale なら依存項目を繰り上げる」に従い、初回投入を本 wave の scope とした。

## 投入した job

| 項目 | 値 |
|---|---|
| Request ID | `981655.nqsv` (name `izs4loop`、queue `gen_S`) |
| 実行 host | `bnode116` |
| Created / Started / Ended | 21:58:51 / 22:30:06 / 22:30:11 (JST、2026-09-07) |
| Elapse | 9S (要求 10800S) |
| `driver_rc` | 1 |
| REPO_ROOT | 固定 SHA `542bfadb8` の detached checkout (job dir 配下、AI worktree container 外) |
| EVIDENCE_ROOT | 全 repository の外 (job dir 配下) |
| 投入形 | `tools/pegasus/README.md` §7 の tagged qsub command のまま (`submit-attempt-0001.sh`) |

fixture 経路 (`--value` 側、`IZANAGI_S4_PROPOSAL_PATH` 無指定) で 1 本だけ投入した。

実際に実行した投入は次のとおり (逐語)。`REPO_ROOT` の submodule は所見 1 のため PIN へ
checkout してある。実行可能 file を repo へ入れないため、script ではなく本文へ記録する。

```text
cd <REPO_ROOT>
qsub \
  -v IZANAGI_S4_REPO_ROOT=<REPO_ROOT>,IZANAGI_S4_EXPECTED_HEAD=542bfadb86b14625a99cca1bdef3583ea09a95ca,IZANAGI_S4_EVIDENCE_ROOT=<EVIDENCE_ROOT>,IZANAGI_S4_THIRDPARTY_SOURCE_ROOT=<REPO_ROOT>/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src \
  -o <EVIDENCE_ROOT>/job.stdout \
  -e <EVIDENCE_ROOT>/job.stderr \
  tools/pegasus/p3_s4_loop_pegasus.sh
```

`THIRDPARTY_SOURCE_ROOT` は `fetch_third_party.py hydrate` が出力した `.source_root` そのものである。

## 初回投入で実機確認できた層

`README.md` の保証範囲が「初回投入で割れうる」と挙げていた項目のうち、次は**通った**。

| 層 | 根拠 |
|---|---|
| host gate (`bnode[0-9]+`) | `IZANAGI_RESERVATION_HOST=bnode116` |
| 環境 sanitize と PATH 固定 | 後段まで到達している |
| 計算ノードの `python3.10` 実在と shim | `python_realpath=/usr/bin/python3.10`、sha256 を `compute-result.json` に記録 |
| expected HEAD / superproject tracked clean | 後段まで到達している |
| CCBench `p3_s4_loop.PIN` の exact 照合 | 所見 1 の前提充足後に通過 |
| `/scr/$USER` の scratch と shim dir | shim 検査を通過している |
| **`qstat -f` からの reservation 束縛** | `reservation.json` に 8 変数すべて。`REQUESTED_S=10800`、`SCHEDULER_STARTED_EPOCH=1788787806`、`DEADLINE_EPOCH=1788798606`、`BOOT_ID`、`SCRIPT_SHA256` |
| **claim root の provisioning** | `<REPO_ROOT>/output/env/pegasus/claims` が 0700 で存在 |
| third-party 3 本の scratch 複製 | prebuild へ到達している |

reservation 束縛と claim root は、依頼本文が「未実測の障害として出うる」と名指ししていた 2 件である。
**どちらも実機で通った。**

## 止まった層

masstree の FetchContent 事前構築が configure で失敗した。

```
MasstreeFetchContentError: masstree FetchContent configure 失敗:
configure failed (rc=1): CMake Error at FindPackageHandleStandardArgs.cmake:230 (message):
  Could NOT find gflags (missing: gflags_LIBRARY_FILE gflags_INCLUDE_DIR)
Call Stack (most recent call first):
  cmake/Findgflags.cmake:9 (find_package_handle_standard_args)
  CMakeLists.txt:33 (find_package)
```

呼出しは `buildcache.py:2069` の `_run(configure, ...)` ← `prepare_masstree_fetchcontent`。
全文は `evidence/job.stderr`。

attestation の exact 照合 (`env_attestation.load_verified_calibration`) には**到達していない**。
driver は起動していないので、この層は本 wave でも未実測のままである。

## 所見 1 — README §7 の手順どおりに投入すると必ず rc=2 になる

job body は CCBench の working tree が `p3_s4_loop.PIN` に exact 一致することを要求し、
driver も `patchharness.assert_pinned_clean(fixed_sub, PIN)` で同じことを要求する。
しかし main の submodule gitlink は pin と一致しない。

| 対象 | 値 |
|---|---|
| main の gitlink (`git ls-tree HEAD external/ccbench`) | `511c9538e4e8efa54b45cda62e72389ed3b706ec` |
| `p3_s4_loop.PIN` | `028f34d` (= `028f34db5fd7bb257a48b1dd1e2f011d295d40d1`) |
| 関係 | `028f34d` は `511c9538e` の**祖先** |

`README.md` §7 の手順は「固定 SHA の専用 checkout」としか書いておらず、
**submodule を PIN へ checkout する手順が無い**。gitlink は [T-2232] の実装 commit `11a7af4b4`
の時点から `511c9538e` のままなので、この欠落は着地時から在った。

本 wave は迂回ではなく前提の充足として、submit-tree の submodule だけを PIN へ checkout した
(submodule の git dir は `.git/worktrees/<name>/modules/...` で checkout 専用であり、
他 worktree の submodule には影響しない)。

## 所見 2 — job body に gflags/glog の供給経路が無い

計算ノードには gflags が無い。これは環境の偶発ではなく、job body の欠落である。

- 兄弟 job body は自前で建てている。`tools/pegasus/floor_scoping.sh` の gflags/glog prologue は
  policy の pin から両者を `$TMPDIR` へ configure / build / install し、
  `export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"` してから CCBench を configure する。
  同 script は出典を `floor_campaign.sh` の同型 prologue と記している。
- `p3_s4_loop_pegasus.sh` は環境 sanitize で `CMAKE_PREFIX_PATH` を `unset` するだけで、
  gflags/glog を建てず、prefix path も与えない。
- 供給元は実在する。`tools/pegasus/policy.json` の
  `gflags_source_path` / `glog_source_path` が指す 2 つの source について、
  **HEAD が policy の pin (`e171aa2d15ed9eb17054558e0b3a6a413bb01067` /
  `8f9ccfe770add9e4c64e9b25c102658e3c763b73`) と exact 一致し、tracked / untracked とも clean である**
  ことを本 wave で実測した。
- `fetch_third_party.py` の cache root には gflags/glog が無い (masstree / mimalloc / googletest のみ)。
  したがって hydrate 経路の拡張ではなく、floor 系と同じ policy 経由の prologue が対応する形である。

## 本 wave で実装しなかった理由

段 1 brief の scope で「job body の機能追加」を scope 外として凍結しており、`DW-O12` により
凍結は自分が直前に書いたものでも拘束する。加えて純粋な移植ではなく設計択一が残る。

- prologue が `policy.json` を読むなら、この job body に policy 依存が新設される (現在は非依存)
- floor 系は provenance file 群を記録する。s4 でも記録するか
- 契約テスト `orchestrator/tests/test_p3_s4_loop_job_contract.py` (44 node) と
  `tools/pegasus/admission_registry.json` の同時更新が要る
- `-j` と timeout の値、`CMAKE_PREFIX_PATH` を driver 本走まで持たせるかの束縛

裁定は `s4-adjudication-supplement.md` の D1〜D3。

## 構成

- `s1-brief.md` — 段 1 brief (親)。割れうる前提 P1〜P7
- `s4-adjudication.md` — 段 4 裁定 (親)。C1〜C5、plan v2
- `s4-adjudication-supplement.md` — 実測後の再裁定 (親)。D1〜D3
- `evidence/compute-result.json` — job body の終端記録
- `evidence/reservation.json` — reservation 束縛 8 変数と qstat 証跡の hash
- `evidence/allocation-qstat.stdout` — 計算ノードから見た `qstat -f` の全文
- `evidence/job.stderr` — 失敗の全文 traceback

`job.stdout` は 0 byte だったため収録していない。

## 保証範囲 (主張の限界)

- 通ったと書いた層は **1 回の投入 (bnode116、2026-09-07) で通った**という意味であり、
  他の配分・他の host で常に通ることを主張しない。
- attestation の exact 照合、driver 本走、build の成否は依然として未実測である。
- 所見 2 の対応案 (floor 系 prologue の移植) は**実装も実測もしていない**。
  移植すれば gflags で止まらなくなることは推測であって、本 wave の実測ではない。
