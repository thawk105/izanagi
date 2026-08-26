# 裁定パッケージ — CCBench submodule の pin を上げるか

- wave: `dev-wave-ccbench-pin-precheck-20260827`
- 基準: izanagi local main `b7f66232` (作業中に並行 wave の land で `9ebd340b` まで前進)
- 現 pin: `511c9538e4e8efa54b45cda62e72389ed3b706ec`
- **実装差分ゼロ。izanagi の pin は 1 bit も動かしていない。**
  pin を進めた測定はすべて job dir の使い捨て clone の中だけで行った。
- 一次資料: `findings.md` (F1〜F12) / `findings2.md` (G1〜G10) / `findings3.md` (G11〜G17)
- 段 3 敵対検証: read-only codex 2 本 (`consult-sol2.md` / `consult-luna2.md`、どちらも rc=0)。
  **指摘はそのまま採らず、全件を親が実測し直した。**

---

## 0. 依頼の前提のうち、実測で覆ったもの

| 依頼の前提 | 実測 |
|---|---|
| 「上流 master から 3 本ぶん古い」 | **誤り。** pin は master の祖先ではない。分岐点 `7e268f2a`、`511c9538..master` = 16 commit、`master..511c9538` = 8 commit。pin は izanagi 専用 branch `izanagi-trace-pin-t816` の tip |
| 「上げる / 上げない / 条件付きで上げる」の三択 | **「master 直行」は落ちる。** master の `cc/silo/` に "trace" を含む file が 1 件も無く、`include/trace.hh` も無く、`Options.cmake` から `CCBENCH_TRACE` と `TRACE=${CCBENCH_TRACE}` が消える → 絶対規律 1 (D14) と規律 3 の土台を壊す |
| 「SS2PL の YCSB 入口が無い」 | **stock tree では事実。** ただし `patches/ss2pl-lock-protocol-study.patch` が自前で足しており、**現 pin のまま YCSB-A の SS2PL study は 2026-08-25 に完走済み** |
| 「tpcc_ss2pl.exe が 2 スレッド以上で確定的に SIGSEGV」 | **事実。** #122 の commit 本文が機序を明記 (`read()`/`update()` が abort 時も `Status::OK` を返し、呼び手が未初期化の `TupleBody*` を dereference) |

---

## 1. 一行の結論

**pin を上げると、今日緑の経路が 2 本 (本番) + 9 箇所 (検査) 赤くなる。**
**うち 1 本は、修正が設計変更を要する。**
**一方、既存の certified 成果物・campaign が壊れる件数は 0 である。**

そして最も重い構造的事実:

> **SS2PL の SIGSEGV 修正と、その blocker は切り離せない。**
> 修正 (#122) は #121 が入れた `#if defined(DLR0)` guard を外すだけの commit で、
> #121 抜きでは cherry-pick が競合する (実測)。そして #121 こそが blocker を持ち込む。

---

## 2. blocker — `${SS2PL_DLR_MARKER}` が izanagi の静的 CMake parser を止める

PR #121 が `cc/ss2pl/CMakeLists.txt` の option を literal から CMake 変数へ変えた。

```cmake
-  WORKLOADS bomb tpcc
+  WORKLOADS ycsb bomb tpcc
   OPTIONS
-    DLR1
+    ${SS2PL_DLR_MARKER}
```

`${SS2PL_DLR_MARKER}` は同 file 内の `if/elseif` が `CCBENCH_SS2PL_DLR` の値で
`DLR0` / `DLR1` に決める。`orchestrator/campaign/source_digest.py` は
この CMake を静的に読んで「実 TU へ実際に `-D` されるマクロ集合」を確定するが、
**変数参照を解決できず fail-closed で止まる。**

**正例つきの実測** (負例だけでは結論しない):

| 対象 tree | `source_digest._assert_proven_repo_absent_macros()` |
|---|---|
| 現行 pin | **OK** — `frozenset({'MQLOCK'})` |
| master 取り込み後 | **RuntimeError** — `'${SS2PL_DLR_MARKER}' が未対応 … (T-148)` |

影響は D297 の pin 前進 gate だけではない。

- `tools/check_trace0_preprocess_identity.py` (D297) — 実走で **rc=1**
- **本番 campaign 経路**: `source_digest.assert_conditional_macros_covered()`
  (docstring は「resolve が駆動」) → `_assert_proven_repo_absent_macros()`

**一行で直せない理由。** 走査自身の docstring が
「既知の文脈マクロなら `CONTEXT_MACROS` への登録 (= 両文脈 digest 化) が正しい封鎖で、
**この検査の緩和ではない (規律2)**」と定める。ところが `CONTEXT_MACROS` は現在 1 個
(`GLOBAL_VALUE_DEFINE`) しかなく、`_merge_defines()` は 2 個以上で機械停止する
——「単発文脈列では結合枝 (`#if defined(A) && defined(B)`) を覆えないため」。
DLR0/DLR1 は configure 時に 2 値を取るので、素直に登録すると**組合せ文脈への再設計**が要る。

検査を緩めて通す道は**採ってはならない**。緩和は偽 cache hit の運び屋になり、
規律 2 (正しさゲートを緩める変異を許さない) に正面から反する。

---

## 3. 選択的 backport が成立しないことの実測

「blocker を持ち込む #121 を避け、必要な commit だけ取る」を実際に試した。

使い捨て clone を `511c9538` に checkout して cherry-pick:

| commit | 結果 |
|---|---|
| `b629dc1` (#120 YCSB 入口) | **成功** |
| 続けて `df47e3a` (#122 lock 失敗報告) | **CONFLICT** (`cc/ss2pl/transaction.cc`) |

`df47e3a` は行を足すのではなく `#if defined(DLR0)` の guard を**外すだけ**である。
その `if` ブロックを入れたのは `ff291e4` (#121) で、現 pin には存在しない
(実測: `ERROR_LOCK_FAILED` は pin の `cc/ss2pl/` に 3 件、master に 5 件。
差の 2 件が `read()` と `update()` の早期 return = SIGSEGV を直している箇所)。

→ **SIGSEGV を直したいなら #121 が要る。#121 を入れるなら blocker を踏む。**
唯一の逃げ道は「#121 の C++ 側だけ手で port し、CMake の変数化は採らない」で、
その場合 `DLR0` の供給形を izanagi 側で決めることになり、上流との差分が恒久化する。

---

## 4. 取り込み経路そのものは安い

`511c9538` に upstream master を merge した実測:

- **競合ゼロ** (`Automatic merge went well`)
- `CCBENCH_TRACE` (19 行目)、`TRACE=${CCBENCH_TRACE}` (68 行目)、`include/trace.hh` は**すべて残る**
- 凍結行のずれは **5 行中 1 行だけ** (master 直行なら 5 行すべてずれる)

| 凍結行 | 現 pin (= golden) | master 直行 | master 取り込み |
|---|---|---|---|
| `CCBENCH_BACK_OFF` default | 20 | **15** | 20 |
| `CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION` | 27 | **22** | 27 |
| `CCBENCH_NO_WAIT_OF_TICTOC` | 28 | **23** | 28 |
| `CCBENCH_WAL` | 47 | **42** | 47 |
| `BACK_OFF=${CCBENCH_BACK_OFF}` universal mapping | 63 | **59** | **64** |
| silo CMakeLists 3 行 | 5/6/10 | 5/6/10 | 5/6/10 |
| flag の値 4 つ | 1/1/0/0 | 1/1/0/0 | 1/1/0/0 |

**高いのは取り込みそのものではなく、その周りである。**

---

## 5. 壊れないもの (依頼の問い (4) への回答)

| 問い | 実測 |
|---|---|
| 既存 campaign が E1-stale になるか | **0 件。** E1 epoch は `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` の exact 25 path の blob hash だけで決まる。25 path に `external/ccbench` も `pin.py` も `s8b_approved.py` も `s1_known_axes_freeze.py` も `build_admission.py` も含まれない |
| E1 とは別経路 (`repo_stock_pin`) では | **新規に壊れる live campaign 0 件。** `build_admission._new_policy()` の preimage に `repo_stock_pin: CURRENT_PIN` が入り、`artifact_admission.py:1044` が記録 lock と exact 比較する。実測: `output/` 配下の `campaign.lock` 32 件のうち `repo_stock_pin` を持つのは 2 件、その 2 件の記録値は既に `d706650` (旧 pin) で**現行 pin の下でも既に不一致**。いずれも `output/insights/2026-08-04_…/evidence/` 配下の歴史 evidence (走査範囲: tracked `output/` 配下) |
| 過去の記録 series / certified writer 行 | **無傷。** `qualification/identity.py:124` も `certified_writer_admission.py:363` も**記録済み commit の gitlink**を再導出して照合する |
| `s8b_holdout_freeze` の凍結 bytes | **不変。** ccbench の tracked file 数 404 (取り込み後 405)、三軸 literal は pin→master の diff の追加行・削除行に 1 件も無い → 軸別 count・conjunction も不変。なお記録済み `file_count` は 1197、live は 15,236 で既に 13 倍ずれている (保留下) |
| 床値の測定値 | **再計測不要。** D444 が不変 16 field の byte-exact 継承を定め、`reseal_protocol()` は legacy anchor を deepcopy して 2 field だけ差し替える |

---

## 6. 赤になるものの確定在庫

**必ず更新する (3):**

| # | path:line | 内容 |
|---|---|---|
| 1 | `orchestrator/campaign/pin.py:28` | `CURRENT_PIN` (7 桁)。正本。参照 driver 15 本が自動追随 |
| 2 | `orchestrator/campaign/s8b_approved.py:67` | `CCBENCH_FULL_SHA` (40 桁)。**承認定数 = 人間手番** |
| 3 | `output/s8b-freeze/floor-protocols/<contract>--<新 pin>.json` | **追加のみ**。`reseal_protocol()` (零引数) が発行。既存 bytes は上書きしない |

**本番経路で赤になる (2):**

| # | 対象 | 実測 |
|---|---|---|
| 4 | `source_digest._assert_proven_repo_absent_macros()` | 現 pin OK / 取り込み後 RuntimeError (§2) |
| 5 | `s8b_floor_campaign.resolve_current_floor_protocol()` | 現 pin OK / bump 後 `FloorCampaignError: current_count=2 head_exact_count=0` (実測)。 D491 の設計どおりの fail-closed。#3 を発行すれば `E=1` に戻る |

**検査が赤になる (9 箇所):**

| # | path:line | 種別 |
|---|---|---|
| 6 | `orchestrator/tests/s1_expected_goldens.py:461` `EXPECTED_SOURCE_LINES` | 取り込み経路なら **1 行**。**裁定つき更新**が要る (decisions.md:3552 が「pin bump 時のみ裁定つき更新」と定める) |
| 7 | `orchestrator/tests/test_s8b_approved.py:60` | live gitlink vs 承認定数。#2 で追随 |
| 8 | `orchestrator/tests/test_s6_sort_sweep.py:370` | 7 桁 pin の独立 golden |
| 9 | `orchestrator/tests/test_s8a_trigger_sweep.py:79, :456` (+ policy SHA golden :80-82) | 同上 |
| 10 | `orchestrator/tests/test_p3_build_authority_cli.py:175` | `_EXPECTED_REPO_STOCK_PIN` |
| 11 | `orchestrator/tests/test_p3_s4_loop_sort.py:680` (+ campaign-id literal :867-869) | 7 桁 pin と派生 campaign-id |
| 12 | `orchestrator/tests/test_p3_s4_loop_trigger_gating.py:2025` (+ :797-820) | 同上 |
| 13 | `orchestrator/tests/test_t126_qualification_driver.py:399` | 7 桁 pin 引数 |
| 14 | `orchestrator/tests/test_s8b_protocol_builder.py` の canonical bytes / `_GOLDEN_SHA` / 承認 protocol SHA | #2 の更新で 3 者とも動く |

campaign-id が動く理由: `ident.canonical_preimage()` は `ccbench_commit` と
`search_config` 全体を覆い、`search_config` には `build_admission` policy
(= `repo_stock_pin`) が必須である。**pin bump は campaign-id を 2 経路で動かす。**

**触ってはならないもの** (更新すると既存証拠の identity を壊す):

| path | 理由 |
|---|---|
| `tools/pegasus/mocc_trace_v1_policy.json` の `base_oid`/`new_oid`、`test_mocc_trace_job_contract.py:29`、`test_mocc_trace_pair.py:17` | 実験 pair の identity。pilot は `new_oid` の実在と ancestry だけ検査し、現行 gitlink とは比較しない (receipt も `outer_gitlink_advanced: false`) |
| `silo_ladder_rung1.py:57`、`silo_ladder_rung1_contract.py:543`、`patches/ledger.json` の `base_commit` | 歴史的 ability-probe base。3 者は contract の `expected_scalars` exact 比較で一体。driver は `git show {PIN}:…` で source を materialize する用途 |
| `output/env/pegasus/calibration/a2_perf_verify_cost_*.json` の `ccbench_head` | 計測時点の evidence 記録 |
| `orchestrator/submission_gate/_semantic_validator.py:69` `_CCBENCH_PIN` | **既に `d706650…`** (a08 承認 pin)。現 pin ですら一致しない固定承認値 |
| `docs/archive/**`、`output/insights/**`、`tools/known_violations/*.json`、`docs/decisions.md`、`docs/failures.md` | 歴史記録 |

**保留 (`freeze_verification_hold.HELD = True`) の扱い:**
裁定 `rulings-4th-batch-2026-08-12`、解除条件は `explicit-user-command-only`。
保留中の 21 件のうち **CCBench の current pin を直接比較する production check は 5 件**
(`s1-known-axes.ccbench-submodule-head-pin`, `s1-measurement.recorded-pin-current-pin`,
`t080.{draft,live,static}-known-axes-ccbench-current-pin`)。
1 件はテスト helper のみ、残る 15 件は artifact bytes / 別 SHA の pin で bump と無関係。
→ **即時の追加赤はゼロ。ただし解除時に説明すべき差分が 1 世代深くなる** (延期負債の増加)。

参考: canonical `output/s1-freeze/known_axes_freeze.json` は `ccbench_pin: d706650…` を
記録しており、**izanagi は既に一度 pin を前進させてその差を保留で持ち越している。**
また `K.verify()` は pin と無関係な generator sha drift で**今日すでに赤**であり、
受入経路は `build_document()` + 独立 golden を使う (test は `verify()` を 1 度も呼ばない)。

---

## 7. 択一

### 案 A — pin を据え置く

- **やること:** 何もしない。SS2PL は既存 out-of-tree patch で扱い続ける
- **費用:** 0。凍結 bytes・承認定数・golden・床値・campaign-id・人間 push のいずれも動かない
- **失うもの:**
  - `tpcc_ss2pl.exe` は 2 スレッド以上で確定的 SIGSEGV のまま
  - 上流の SS2PL 修正 3 本が stock source の既定に入らない
  - SS2PL を **certified** 経路へ載せる日が来たら、その時点で取り込みか overlay 維持の費用を払う
    (現 study は `pipeline.evaluate()` を通らない descriptive で、report 自身が
     「正式採択するなら再測定が要る」と書いている)
- **整合する既裁定:** **D790 (2026-08-25) がこの形を選んでいる。**
  却下理由に「submodule へ commit する: gitlink 前進は承認定数の再承認と freeze の再凍結を
  確定的に発生させる。価値が未確定の探索 variant にその費用を払わない」と明記。
  **本 wave の実測は、その費用が実在することを裏づけた。既裁定を覆す新事実は見つからなかった。**

### 案 B — SS2PL の修正だけを izanagi 側へ持つ (global pin 据え置き)

- **やること:** #121 の C++ 側 (`transaction.cc` の `ERROR_LOCK_FAILED` 早期 return、
  `dlr0_timeout.hh`、`common.hh`、`util.cc`) と #120 の YCSB 入口を、
  既存 study patch に統合する。**CMake の `${SS2PL_DLR_MARKER}` 変数化は採らない**
- **費用:** patch の統合。既存 study patch が自前で足している `ycsb_ss2pl.cc` と
  上流 #120 の実装が重複するので、どちらを採るか決める。
  D790 が要求する「既定 `IMPL=0, KIND=1, DLR=1` は stock 逐語 = patch は既定で inert」の再証明
- **失うもの:** stock source の既定にはならない。上流との差分が恒久化する
- **blocker を踏むか:** **踏まない** (global tree に変数が入らない)

### 案 C — 条件を満たしてから取り込む (master を izanagi-trace branch へ merge して re-pin)

前提条件:

| 前提 | 内容 |
|---|---|
| C-1 | **blocker の解消。** `source_digest` が `${SS2PL_DLR_MARKER}` を扱えるようにする。`CONTEXT_MACROS` の 1 個制限に触るため、組合せ文脈への再設計かユーザー裁定が要る |
| C-2 | D297 gate を新旧 pin 間で緑にする (C-1 後に再評価) |
| C-3 | 承認定数 `s8b_approved.CCBENCH_FULL_SHA` の再承認 (人間手番) |
| C-4 | `EXPECTED_SOURCE_LINES` 1 行の**裁定つき**更新 |
| C-5 | §6 の検査 9 箇所の張り替え (campaign-id 派生を含む) |
| C-6 | 床値 protocol を (同一 contract, 新 pin) で 1 件発行 (**再計測不要**)。 gitlink・定数・golden を同一 commit にし、その HEAD に対して `reseal_protocol()` を走らせる (2 commit に割ると resolver が `E=0` の一時停止になる) |
| C-7 | SS2PL study patch の rebase と、D790 の inert 再証明。上流 #120 との重複統合 |
| C-8 | 新 ccbench commit の**人間 push** (D16)。push と remote 到達確認の前に superproject の pin を land しない |
| C-9 | `refs/izanagi/ccbench/t1506/mocc-trace-include` (`058d0c4e`) と object を保存する。 **MOCC / silo ladder の pin literal は触らない** |
| C-10 | 未着地の `worktree-dev-wave-mocc-g2-repro-20260826` の land 後に着手する (同じ 2 つの MOCC test file を編集面として奪い合うため) |

- **失うもの:** 新 pin 以後に作る campaign の campaign-id が動く
  (既知・正直な content-addressed 挙動。既存 campaign-id は不動)。保留負債が 1 段深くなる

---

## 8. 親の推奨

**案 A (据え置き) を既定とし、案 C は blocker (C-1) を独立の wave で解いてから再提起する。**

1. blocker は pin とは独立に価値がある。`source_digest` の CMake parser が変数参照を扱えないのは
   上流がいつ変えても踏む脆さで、いま直せば将来の取り込みが安くなる
2. 現行 critical path は Silo 系 (worklog 末尾の「次の一手」は B-4) であり、SS2PL ではない。
   SS2PL の探索は現 pin + patch で現に回っている
3. D790 が同じ費用を根拠に同じ選択をしており、本 wave はその費用が実在することを実測で裏づけた

案 B は「SS2PL の SIGSEGV を今すぐ直したい」場合の最小手である。

pin の可否と独立に、次の 1 件は是正を推奨する。

- **`.gitmodules` の `branch = izanagi-trace` は upstream で `d706650` (旧 pin) を指している。**
  `git submodule update --remote` を実行すると **pin が 1 世代巻き戻る。**
  宣言を実際の tip (`izanagi-trace-t816-fn2`) へ揃えるべき。

---

## 9. ユーザーに決めていただきたいこと

1. **案 A / B / C のどれを採るか。** (親の推奨は A、C は blocker 解消後に再提起)
2. 案 C を選ぶ場合、**C-1 の `CONTEXT_MACROS` 組合せ文脈への再設計**を認めるか。
   認めない場合の代替は「上流 `cc/ss2pl/CMakeLists.txt` を literal option へ戻す PR を出す」。
3. **`.gitmodules` の branch 宣言の是正**を、この裁定と切り離して先に進めてよいか。
4. **`docs/dev-wave/operations.md` の `DW-O09` の byte 予算 (1 節 1000 byte) を上げてよいか。**
   本 wave は閉包の検索軸を 2 つ落とした (§6 の 7 桁 pin と §2 の D297 gate)。恒久対応は
   `DW-O09` へ書くのが筋だが、同節は **997/1000 byte** で余地が 3 byte しかなく、
   既存の安全義務を削らずには入らない。自己改善契約は
   「予算のために安全義務を削除・弱化してはならない」「予算値を上げる変更は
   通常の自己改善に含めず、理由付きの独立審査対象にする」と定めるため、
   本 wave では編集せず memory `pin-closure-search-two-missing-axes` に置いた。
   択一は (i) 予算を上げて `DW-O09` へ入れる、(ii) memory のまま運用する、
   (iii) `DW-O09` を 2 節に割る、のいずれか。
