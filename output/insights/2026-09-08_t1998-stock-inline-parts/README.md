# [T-1998] balanced stock-inline 対照の最小 3 部品 — 到達性監査と、実装した launcher / consumer

- 日付: 2026-09-08
- wave: `worktree-dev-wave-t1998-stock-inline-parts`
- 基準 commit: `c5754d1f4b3d915f2e55615e69674190f48c69a8` (着手直前の local main)
- authority: none — 本書は到達性監査の結論と設計判断の索引であって、性能の測定原典ではない。
  **本 wave で測定は 1 回も走らせていない。性能値は他所の一次資料から引用した分だけを含む。**
- 一次資料: `docs/decisions.md` の D1244 / D20 / D1137、
  `docs/handoff/2026-08-28-t1998-balanced-stock-inline-precheck.md` の段 4 裁定、
  `output/insights/2026-09-07_t2320-backoff-sweep-gate-layer2/README.md` (A-5 経路の実測)、
  `docs/failures.md` の F251。

## 0. 何を求められていたか、何をしたか

D1244 (2026-08-28 ユーザー裁定) が T-1998 を最小 3 部品に限定した。

1. producer evidence の read-only 到達性監査
2. 既存 backoff sweep を呼ぶ薄い sanctioned launcher
3. 事前登録で固定した 2 点だけを読む consumer

新しい汎用 driver は作らない。3 部品の land 後に prospective 事前登録と正式測定認可は人間手番へ返す。

**本 wave はこの 3 部品を land した。測定は走らせていない。**

## 1. 第 1 部品 — producer evidence の read-only 到達性監査

対照 consumer が再検証する必要のある evidence が、producer の成果物のどの field から取れるかの対応表。
**結論: producer schema は拡張しない。ただし事前登録が arm 別の期待 source digest と
期待 job body script digest を持つことが前提である。**

| evidence | producer 成果物と field | consumer 側の再検証 |
|---|---|---|
| repository commit | `result.json.repository_commit`、`reservation.json.source_binding.repository_commit`、`campaign.lock` の `authority.contract_loader_commit` | 3 者と事前登録値の一致 |
| CCBench gitlink | `result.json.ccbench_commit` と reservation は 40 桁、`campaign.lock` と WAL は `pin.CURRENT_PIN` の 7 桁 | 40 桁は exact、短縮形は接頭辞。**接頭辞一致は full identity ではない** |
| CCBench source | WAL `build_start.payload.build_admission.source` の `genome_sha256` / `src_token` / `source_bytes_sha256` | **arm ごとに異なるのが正常。** 事前登録の arm 別期待値と照合する |
| 環境契約 digest | `campaign.lock` の `authority.environment_contract_sha256` と各 COMMIT の `payload.contract_sha256` | **`result.json` にも `reservation.json` にも無い。** lock と WAL から取る |
| trace-disabled 性能 build | WAL `build_done.payload.perf_configure_cmd` / `perf_build_cmd` / `perf_bin_sha256`、`bench_done.payload.run_cmd` | configure の `-B` と build の `--build` の directory 一致、既知 wrapper 列の後の実行対象が当該 build directory の実行体であること |
| 診断 knob `BACKOFF_NOINLINE` | **単一 field として存在しない** | 事前登録の arm 別 source digest との一致で束縛する。genome と configure の明示値検査は補助 |
| toolchain manifest | WAL `build_done.payload.toolchain` と `toolchain_record_sha256`、`result.json.toolchain` | manifest の canonical digest を再計算して記録値と照合し、その後 arm 間一致と result 投影を見る |
| verifier receipt | WAL COMMIT の `payload.commit_verification_receipt` | `require_admitted_campaign(...CERTIFIED_ACCEPTANCE)` が全 COMMIT を検証済み |
| 投入器の同一性 | `reservation.json.binding.script_sha256` は **job body 自身の digest** | **どの投入器から出したかは成果物から復元できない。** consumer が束縛できるのは job body まで |

### 到達性の限界 (主張しないこと)

- full な `--version` 本文は公式 output に残らない。残るのは短い manifest と record digest だけで、
  2 arm の identity 一致には足りるが、full 本文の後日再ハッシュはできない。
- 診断 knob の実効値はどこにも単一 field として記録されない。commit 束縛の source bytes からしか導けない。
- 投入器の provenance は新 submitter が書く submit receipt に残るだけで、`result.json` へは入らない。

### 2026-09-07 の実測との関係

A-5 経路は 2026-09-07 に balanced の対を実測している (無 backoff 3,803,883 tps / fixed 5 µs 4,294,095 tps。
原典は `output/insights/2026-09-07_t2320-backoff-sweep-gate-layer2/README.md` §4.1)。
**この root は本 wave の consumer では受理されない。** balanced job は 8 genome を commit した後、
finalizer の前に rc=1 で落ちており `result.json` が無いので `producer-artifact-missing` になる。
加えて commit `0ade09d5e` に束縛されており、3 部品 land 後の prospective 事前登録より前の測定である。
**数値が実在することと T-1998 の主張へ適格であることは別である。**

## 2. 第 2 部品 — 薄い sanctioned launcher

`tools/pegasus/submit_t1998_balanced_stock_inline.sh` (新規)。

- balanced 1 workload だけを 1 回 `qsub` する。fan-out しない。
- job body は既存 `tools/pegasus/a5_second_boot_backoff_sweep.sh` を **1 byte も変えずに再利用**する。
- 既存 A-5 の投入器・job body・契約テスト・登録簿 entry は変更していない。base と HEAD の blob は同一。
- 既存投入器の投入前検査を 1 つも落としていない (`git` と `python3.10` の実在検査を足した)。
- `tools/pegasus/admission_registry.json`、`orchestrator/tests/test_hooks.py`、
  `docs/pegasus-runbook.md` へ同じ変更単位で登録した。

### なぜ純増ありと裁定したか

段 2 のプランは「既存 A-5 経路で足りるので純増ゼロ」と起草した。段 3 の敵対相談が、
既存 A-5 投入器は同じ checkout から 2 job を出し、先に終わった job の終了処理が打つ
global `git worktree prune --expire now` が共有 submodule gitdir 上の他 job の worktree 登録を消す
**構造**であることを突き止めた。F251 の 2026-09-07 再発記録が同じ結論を書いており、
実測でも balanced job が 8 genome 計測後に落ちている。1 job だけを出す投入器なら
同一 invocation 内にこの経路が成立しない。

### 残る限界 (裁定パッケージ)

**別 invocation どうし、あるいは既存 A-5 job と同時に走る場合は、再利用している job body の
global prune 経路が残る。** 恒久対応は job body の shared gitdir ownership の変更であり、
F251 として既にユーザー裁定待ちなので本 wave では触れていない。
実装 commit `0df429a21` の message は「構造的に成立しない」と書いたが、
正しくは「同一 invocation 内では成立しない」であり、後続 commit `4a5f2cae5` の message で訂正した。

## 3. 第 3 部品 — 事前登録固定 2 点だけを読む consumer

`orchestrator/campaign/t1998_stock_inline_pair.py` (新規)。

- balanced の `BACK_OFF=0, BACKOFF_FIXED=-1` と `BACK_OFF=1, BACKOFF_FIXED=5` を
  module 内 immutable 定数に固定する。`backoff_sweep` から import しない。**argmax を使わない。**
- 事前登録 identity を共通 (repository commit / gitlink / 環境契約 digest / job body script digest) と
  arm 固有 (canonical genome / 期待 source digest) に型で分ける。**本 wave では実値を確定しない。**
- 拒否は code だけでなく `field` / `expected` / `actual` / 対象 arm を持つ。
- 片方でも `unstable` なら例外ではなく inconclusive を返し、ratio と improvement を `None` にする。

### 冗長 gate として明記したもの (単独では発火しない)

`pair-cardinality`、`producer-rejected-variant` の receipt 欠損 / abort / stage 欠損部分、
WAL gitlink の一致、COMMIT の environment contract digest、
`admission.lock_sha256` / `admission.wal_sha256` の TOCTOU guard。
いずれも上流の finalizer か `require_admitted_campaign` が先に同じ入力を拒否する。
source に明記し、変異の証拠から外した。

## 4. 敵対レビューが構成した 9 件の入力

親の実走 (consumer 16 / launcher 6 / official perf 7 / hooks 474) はすべて緑だったが、
段 6 の敵対レビュー 2 本は**その緑が通っていない入力**を現物で構成した。重いものは 3 件。

- 型付き CMake define (`-DCCBENCH_BACKOFF_NOINLINE:STRING=1`) が診断 build 検査を素通りする。D20 に直結する。
- bench executable の検査が argv 内に期待 path が 1 回現れるだけで通り、`/bin/true <path>` を受理する。
  **レビュー 2 本が独立に指摘した。**
- attempt に属さない `verify_done` (anomalies=1) が素通りする。**規律 2 の迂回である。**

他に、正例 fixture 自身が不整合な root だった (toolchain manifest の canonical digest は
`fb534797fa4eaa063c95c782900b817701208d1954ba13c1e7cae8124a453c59` なのに `"3" * 64` を記録して
accepted を期待していた)、`verify_done` だけ env tag 一致検査から漏れていた、
診断 knob を持つ off-pair genome を受理していた、admission 失敗の arm を一律 `baseline` に帰属させていた、
submit receipt の schema literal が未固定だった、恒偽の分岐が 1 つあった。**9 件すべてを閉じた。**

## 5. 変異 matrix

事前登録 16 件。spec と report は本 directory に置いた。

| 走行 | spec | report | 結果 |
|---|---|---|---|
| probe 1 回目 | `mutation-probe-spec.json` | `mutation-probe-report.json` | MISMATCH 14 / **SURVIVED 2** |
| probe 2 回目 | 同上 | `mutation-probe2-report.json` | MISMATCH 16 / SURVIVED 0 |
| 本走 | `mutation-main-spec.json` | `mutation-main-report.json` | **baseline PASSED / KILLED 16 / SURVIVED 0 / MISMATCH 0** |

probe は観測 node を集めるため全件 SURVIVED 期待で登録する。MISMATCH は probe としては正常な結果である。

### probe 1 回目に生き残った 2 件 (erratum として残す)

- **M12 は他層の mask だった。** toolchain の canonical digest 再計算を消しても、既存負例は
  target だけ digest を変えるため arm 間比較が代わりに赤にする。両 arm が同じ非 canonical digest を
  持つ負例を足して、再計算層だけが単独で拒否する形にした。
- **M9 は文字列存在検査の素通りだった。** 述語を `if False and (...)` へ倒しても部分文字列は残るので
  テストは緑のままだった。python 断片を実行する挙動検査へ変えた。

いずれも実装の欠陥ではなくテストの穴であり、実装は変えていない。詳細は failures 台帳に記録した。

## 6. 確定していないこと・限界

- **prospective 事前登録の実値を確定していない。** 期待 commit / gitlink / 環境契約 digest /
  job body script digest / arm 別 source digest はすべて型と seam だけを land した。
- **正式測定の認可を代行していない。** D1244 のとおり人間手番である。
- **balanced の complete な producer root は実環境にまだ存在しない。** complete な
  `a5-second-boot-result/v1` は write-heavy が 1 件あるだけで、consumer の正例は実環境で
  到達していない。テストの正例は合成 root である。
- **投入器の同一性は成果物から復元できない。** 束縛できるのは job body までである。
- **3 つの Pegasus 投入器に共通する queue preflight の欠陥が残る。** `gen_S` / `ENA` / `ACT` を
  `qstat -Q` の出力全体で独立検索するため、`gen_S DIS INA` と `gen_L ENA ACT` が並ぶ出力を
  成功と誤判定する。誤った成果物は生まれない (qsub が失敗する) ので must-fix にしていない。

## 7. 裁定パッケージ (ユーザーへ返す。本 wave では実装しない)

1. **A-5 job body の global prune と投入器の 2 job fan-out。** F251 として既にユーザー裁定待ち。
   本 wave の第 2 部品は 1 job だけを投入する新しい投入器を足すだけで、A-5 側の構造は直していない。
2. **3 投入器に共通する queue preflight の行単位検査。** 上記の限界。
3. **事前登録の実値の固定と正式測定の認可。** D1244 のとおり人間手番。
4. **2026-09-07 に取れた balanced の生値の扱い。** 実在するが、`result.json` が無く、
   3 部品 land 後の prospective 事前登録より前の測定である。T-1998 の主張へ転用してよいかは人間手番。
