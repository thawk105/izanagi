# 段 3 第 2 巡 (rc=0 成果物) 後の追加実測と、live 束縛の確定在庫 (2026-08-27)

第 1 巡は親の prompt の見出し階層 (`###`) が `check_codex_output.py` の
`^## 総括` 要求に合わず `f43_fragment` で不採用になった (親の作成ミス)。
出力自体は完成していたため保全し、prompt を直して第 2 巡を投げ直した。
第 2 巡 (`consult-sol2.md` / `consult-luna2.md`) は 2 本とも rc=0 で採用。
以下は**親が全件を実測し直した**確定値である。

---

## G11 (blocker、本 wave 最大の構造的発見) — SS2PL の SIGSEGV 修正と blocker A は切り離せない

「必要な commit だけ選択的に取り込めば blocker A (`${SS2PL_DLR_MARKER}`) を回避できる」
という案を実測した。**成立しない。**

使い捨て clone (`ccbench-backport-probe`) を `511c9538` に checkout して cherry-pick:

| commit | 結果 |
|---|---|
| `b629dc1` (#120 YCSB 入口) | **成功** (競合なし) |
| `df47e3a` (#122 lock 失敗報告) を続けて | **CONFLICT** — `cc/ss2pl/transaction.cc` |

理由は `df47e3a` の中身にある。この commit は**行を足すのではなく `#if defined(DLR0)` の
guard を外すだけ**である:

```diff
-#if defined(DLR0)
   if (this->status_ == TransactionStatus::aborted) {
     return Status::ERROR_LOCK_FAILED;
   }
-#endif
```

その `if` ブロック自体は `ff291e4` (#121) が入れたもので、現 pin には存在しない
(実測: `git grep -n ERROR_LOCK_FAILED` は pin の `cc/ss2pl/` で 3 件、master で 5 件。
差の 2 件が `read()` と `update()` の早期 return = SIGSEGV を直している箇所)。

→ **SIGSEGV を直すには `ff291e4` が要る。`ff291e4` は `cmake/Options.cmake` と
`cc/ss2pl/CMakeLists.txt` を変え、`${SS2PL_DLR_MARKER}` を持ち込む = blocker A を必ず踏む。**
`ff291e4` が触る file は 9 件 (`cc/ss2pl/CMakeLists.txt`, `README.md`, `include/common.hh`,
`include/dlr0_timeout.hh`, `transaction.cc`, `util.cc`, `cmake/Options.cmake`,
`docs/runtime-args_{en,ja}.md`)。

唯一の逃げ道は「#121 の C++ 側だけを手で port し、CMake 側の変数化は採らない」。
その場合 `DLR0` マクロの供給形を izanagi 側で決める必要があり、上流との差分が恒久化する。

## G12 (親の在庫表の矛盾を訂正) — silo ladder の 3 箇所は「歴史的 base」で一体

sol2 が親の F10 の内部矛盾を突いた。実測で確認:

- `orchestrator/campaign/silo_ladder_rung1.py:57` `PIN = "511c9538…"`
- `orchestrator/campaign/silo_ladder_rung1_contract.py:543` `"base_commit": "511c9538…"`
- `patches/ledger.json` entry `silo_ladder_rung1` の `base_commit`

contract は `expected_scalars` として ledger entry の全 field を **exact 比較**する
(`_strict_equal`、:562-564)。3 者は相互に束縛されている。
親は F10 で前 2 者を「更新対象」、ledger を「触らない」に分類しており矛盾していた。

さらに `silo_ladder_rung1.py` の `PIN` の使われ方を実測すると、
`git show {PIN}:{relative}` (:1894, :3665, :4079) と
`patchharness.checkout(PIN, base)` (:3791) — **その commit の source を materialize する**
用途であり、live gitlink とは比較しない。

→ **MOCC pair と同じ「歴史的実験 base」であり、pin bump で更新してはならない。3 者とも据え置く。**

## G13 — campaign-id は pin bump で二重に動く

`orchestrator/campaign/ident.py:166-172` の `canonical_preimage()` は
`ccbench_commit` と `search_config` 全体を覆う。`search_config` には
`build_admission` policy が必須 (:157-161) で、その preimage は
`build_admission.py:461` の `"repo_stock_pin": CURRENT_PIN` を含む。

→ pin を上げると campaign-id hash は **`ccbench_commit` 経由と `repo_stock_pin` 経由の
2 経路で**動く。campaign-id を literal 固定している test はすべて張り替えになる。

## G14 — 触ってはならないものの確定

| path | 理由 |
|---|---|
| `tools/pegasus/mocc_trace_v1_policy.json` の `base_oid`/`new_oid` | 実験 pair の identity (G7) |
| `orchestrator/tests/test_mocc_trace_job_contract.py:29`、`test_mocc_trace_pair.py:17` | 同上 |
| `orchestrator/campaign/silo_ladder_rung1.py:57`、`silo_ladder_rung1_contract.py:543`、`patches/ledger.json` | 歴史的 base、3 者一体 (G12) |
| `output/env/pegasus/calibration/a2_perf_verify_cost_*.json` の `ccbench_head` | 計測時点の evidence 記録 |
| `orchestrator/submission_gate/_semantic_validator.py:69` `_CCBENCH_PIN` | **既に `d706650…`** (a08 承認 pin)。現 pin ですら一致しない固定承認値 |
| `tools/known_violations/*.json` (4)、`docs/archive/**`、`output/insights/**`、`docs/decisions.md`、`docs/failures.md` | 歴史記録 |

## G15 — live 束縛の確定在庫 (pin bump で必ず触る / 必ず赤になる)

**必ず更新するもの (3):**

| # | path:line | 内容 |
|---|---|---|
| 1 | `orchestrator/campaign/pin.py:28` | `CURRENT_PIN` (7 桁)。正本。参照 driver 15 本が自動追随 |
| 2 | `orchestrator/campaign/s8b_approved.py:67` | `CCBENCH_FULL_SHA` (40 桁)。**承認定数 = 人間手番** |
| 3 | `output/s8b-freeze/floor-protocols/<contract>--<新 pin>.json` | **追加のみ**。`reseal_protocol()` (零引数) が発行。既存 bytes は上書きしない |

**bump で赤になる検査 (裁定・張り替えが要る):**

| # | path:line | 種別 |
|---|---|---|
| 4 | `orchestrator/tests/s1_expected_goldens.py:461` `EXPECTED_SOURCE_LINES` | 取り込み経路なら Options.cmake 側 **1 行**。**裁定つき更新** (decisions.md:3552) |
| 5 | `orchestrator/tests/test_s8b_approved.py:60` | live gitlink vs 承認定数。#2 を直せば追随 |
| 6 | `orchestrator/tests/test_s6_sort_sweep.py:370` | 7 桁 pin の独立 golden |
| 7 | `orchestrator/tests/test_s8a_trigger_sweep.py:79, :456` | 同上 (2 箇所) + policy SHA golden (:80-82) |
| 8 | `orchestrator/tests/test_p3_build_authority_cli.py:175` | `_EXPECTED_REPO_STOCK_PIN` |
| 9 | `orchestrator/tests/test_p3_s4_loop_sort.py:680` (+ campaign-id literal :867-869) | 7 桁 pin と派生 campaign-id |
| 10 | `orchestrator/tests/test_p3_s4_loop_trigger_gating.py:2025` (+ :797-820) | 同上 |
| 11 | `orchestrator/tests/test_t126_qualification_driver.py:399` | 7 桁 pin 引数 |
| 12 | `orchestrator/tests/test_s8b_protocol_builder.py` の canonical bytes / `_GOLDEN_SHA` / 承認 protocol SHA | #2 の更新で 3 者とも動く |

**本番経路で赤になるもの (test ではない):**

| # | 対象 | 実測 |
|---|---|---|
| 13 | `source_digest._assert_proven_repo_absent_macros()` | 現 pin OK / 取り込み後 RuntimeError (G1/G2) |
| 14 | `s8b_floor_campaign.resolve_current_floor_protocol()` | 現 pin OK / bump 後 `current_count=2 head_exact_count=0` (F6) |

`pin.CURRENT_PIN` の consumer は親が F10 で 14 本と書いたが、
`orchestrator/campaign/b10_backoff_shape_sweep.py:79` を落としていた (sol2 指摘、実体確認)。**15 本**が正しい。

## G16 (測定条件の訂正)

親は findings.md の基準を `b7f66232` と書いたが、
resolver probe の clone (`izanagi-probe`) の親 commit は `0d3d80e1` だった
(clone 作成時に local main が既に前進していたため)。

- `git merge-base --is-ancestor b7f66232 0d3d80e1` → rc=0 (基準を含む前進)
- `git diff --stat b7f66232 0d3d80e1 -- orchestrator/campaign/s8b_floor_campaign.py output/s8b-freeze orchestrator/campaign/pin.py orchestrator/campaign/source_digest.py` → **空**

→ 関連 file に差が無いので結論は変わらないが、記載を訂正する。
  **F6 の resolver 実測の基準 commit は `0d3d80e1`、probe commit は `567871ae`。**

なお本 wave の作業中に local main は `b7f66232` → `9ebd340b` へ前進した (並行 wave の land)。

## G17 (訂正) — 進行中作業は T-1506 ではなく mocc-g2

親は F11 で `dev-wave-t1506-mocc-trace0` を稼働中とした。**誤り。**

- `git merge-base --is-ancestor 2caec363 main` → rc=0 → **T-1506 は着地済み** (worktree の残骸のみ)
- `worktree-dev-wave-mocc-g2-repro-20260826` (`abf2bde0`) は main の祖先でない → **未着地**
- 同 branch が変更する file に
  `orchestrator/tests/test_mocc_trace_job_contract.py` と
  `orchestrator/tests/test_mocc_trace_pair.py` が含まれる (実測)

→ pin bump とこの branch の関係は「base を動かす」ことではなく、
  **同じ 2 つの test file を編集面として奪い合うこと**である。
  G14 のとおりその 2 file の pin literal は触らないので実害は小さいが、
  pin 作業を始めるなら mocc-g2 の land 後にするのが安全。
