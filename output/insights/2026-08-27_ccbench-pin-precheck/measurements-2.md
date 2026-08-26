# 段 3 敵対検証で判明した追加事実と、親の誤りの訂正 (2026-08-27)

段 3 の read-only codex 2 本 (sol = 正しさ境界と凍結契約、luna = 実効性・運用・裁定の一貫性) が
`findings.md` の F1〜F12 と `brief.md` の (P1)〜(P5) を攻撃した。
**親は指摘をそのまま採らず、全件を自分で実測し直した。** 以下は実測後の確定値である。

---

## G1 (blocker、新規・親の完全な見落とし) — pin 前進には D297 の専用 gate があり、実測で赤

`docs/decisions.md` D297 (2026-08-11) は「CCBench の pin を前進させるとき、旧 pin と新 pin の間で
TRACE=0 の正規化 preprocess 出力と include 活性が一致することを、独立の checker
`tools/check_trace0_preprocess_identity.py` で fail-closed に検査する」と定める。
**親は段 1 でこの gate を閉包に入れていなかった。**

使い捨て clone で `511c9538` に upstream master を merge した commit `4b2a7c94` を作り、
実際に走らせた結果:

```
$ python3 tools/check_trace0_preprocess_identity.py \
    --repo <job>/ccbench-merge-probe \
    --old 511c9538e4e8efa54b45cda62e72389ed3b706ec \
    --new 4b2a7c94656faa9e2fe0f1b7bb0c8639ad296974 --cxx g++
error: … source_digest: ccbench_add_protocol OPTIONS の option token
       '${SS2PL_DLR_MARKER}' が未対応 — 実 TU のマクロ供給を確定できないため
       fails-closed (T-148)
rc=1
```

## G2 (blocker、G1 の真因) — #121 の CMake 変数が izanagi の静的 parser を止める

PR #121 は `cc/ss2pl/CMakeLists.txt` を次のように変えた。

```cmake
+if(CCBENCH_SS2PL_DLR STREQUAL "0")
+  set(SS2PL_DLR_MARKER DLR0)
+elseif(CCBENCH_SS2PL_DLR STREQUAL "1")
+  set(SS2PL_DLR_MARKER DLR1)
+else()
+  message(FATAL_ERROR "CCBENCH_SS2PL_DLR must be 0 or 1")
+endif()
 ccbench_add_protocol(ss2pl
   SOURCES   transaction.cc util.cc
-  WORKLOADS bomb tpcc
+  WORKLOADS ycsb bomb tpcc
   OPTIONS
-    DLR1
+    ${SS2PL_DLR_MARKER}
     KEY_SORT=${CCBENCH_KEY_SORT}
 )
```

`orchestrator/campaign/source_digest.py:695` の `_parse_supplied_macro_details()` は
`ccbench_add_protocol(... OPTIONS ...)` の token を静的に読んで「実 TU へ `-D` されるマクロ集合」を
確定する。literal `DLR1` は読めるが、**変数参照 `${SS2PL_DLR_MARKER}` は解決できず fail-closed** で止まる。

**これは D297 の gate だけの問題ではない。** 同じ走査は本番 campaign 経路からも呼ばれる:
`source_digest.assert_conditional_macros_covered()` (:1746-1755、docstring は「resolve が駆動」)
→ `_assert_proven_repo_absent_macros(sub)` (repo 全体走査)。

**正例つきの実測 (負例だけで結論しない):**

| 対象 tree | `_assert_proven_repo_absent_macros()` |
|---|---|
| 現行 pin (`external/ccbench` の working tree) | **OK** — `frozenset({'MQLOCK'})` |
| master 取り込み後の tree | **RuntimeError** — `'${SS2PL_DLR_MARKER}' が未対応` |

→ **#121 を含むあらゆる pin 前進は、`source_digest` の CMake parser を直すまで
izanagi の campaign resolve 経路を止める。** これが最大かつ最優先の blocker である。

修正が一行で済まない理由: 走査の docstring は「既知の文脈マクロなら `CONTEXT_MACROS` への登録
(= 両文脈 digest 化) が正しい封鎖で、この検査の緩和ではない (規律2)」と書く。ところが
`CONTEXT_MACROS = ("GLOBAL_VALUE_DEFINE",)` は 1 個しかなく、`_merge_defines()` (:1765-1772) は
2 個以上で機械停止する ——「単発文脈列では結合枝 (`#if defined(A) && defined(B)`) を覆えないため」。
DLR0/DLR1 は configure 時に 2 値を取るので、素直に登録すると組合せ文脈への再設計が要る。

## G3 (親の誤りの訂正) — reseal は承認定数を照合しない

`findings.md` F7 の末尾で親は「`reseal_protocol()` は発行前に live gitlink と
`s8b_approved.CCBENCH_FULL_SHA` の一致を要求する」と書いたが、**誤り**である。

- `_reseal_protocol_at_root()` (`s8b_floor_campaign.py:1095-1145`) は
  `target_pin = _ccbench_gitlink(root, head_commit)` を使い、承認定数を一切見ない。
  legacy anchor を `copy.deepcopy` して `contract_sha256` と `ccbench_pin` の 2 field だけ差し替える。
- 承認定数の照合 (`actual_link != s8b_approved.CCBENCH_FULL_SHA` →「現在値の追認を拒否」) は
  **別 API** の `build_protocol_document()` (:1280-1285) にしかない。
- 親が読み違えた行 (:1281/:1297) は後者である。

**訂正後の結論:** reseal の順序に承認定数の前提は無い。D444 の byte-exact 継承により
**床値の再計測が不要**という F7 の中核は変わらない (子 2 本とも支持)。
ただし承認定数 `s8b_approved.CCBENCH_FULL_SHA` の更新自体は別途必要で、
`test_s8b_approved.py:60` が live gitlink と照合するため bump 直後に赤になる。

補足: reseal が deepcopy するのは **legacy anchor** (pin `d706650c…` の
`output/s8b-freeze/floor_protocol.json`) であり、現行 versioned protocol ではない。
したがって新 protocol の 16 field は anchor 由来のまま引き継がれる。

## G4 (親の閉包の穴) — 7 桁 pin を検索していなかった

親は `git grep -l "511c9538"` (40 桁) で 119 file を数えたが、
**正本の `pin.CURRENT_PIN` は 7 桁 `"511c953"`** であり、この検索では 7 桁だけを持つ file を落とす。

実測: `git grep -l "511c953"` = **142 file**。差集合 (7 桁のみ) = **23 file**。

そのうち **pin bump で赤になる独立 golden が 6 file・7 箇所**:

| path:line | 形 |
|---|---|
| `orchestrator/tests/test_s6_sort_sweep.py:370` | `expected_pin = "511c953"  # repo policy から逆算しない独立 pin` |
| `orchestrator/tests/test_s8a_trigger_sweep.py:79` | `_CHARACTERIZATION_PIN = "511c953"` |
| `orchestrator/tests/test_s8a_trigger_sweep.py:456` | `expected_pin = "511c953"` |
| `orchestrator/tests/test_p3_build_authority_cli.py:175` | `_EXPECTED_REPO_STOCK_PIN = "511c953"` |
| `orchestrator/tests/test_p3_s4_loop_sort.py:680` | `assert cfg.ccbench_commit == S.PIN == "511c953"` |
| `orchestrator/tests/test_p3_s4_loop_trigger_gating.py:2025` | `assert cfg.ccbench_commit == T.PIN == "511c953"` |
| `orchestrator/tests/test_t126_qualification_driver.py:399` | 引数 literal `"511c953"` |

本番 side の 7 桁出現 (`axis_trigger_gating`, `backoff_sweep`, `p3_s4_loop_sort`,
`p3_s4_loop_trigger_gating`, `s5_permutation_coverage`, `s6_sort_sweep`) は
**すべて `pin.CURRENT_PIN` の隣に置かれたコメント**であり、実行に効かない (実測確認)。
残りは `docs/archive` 2 件と `output/insights` 6 件の歴史記録。

## G5 (新規) — E1 とは別に `repo_stock_pin` が受理条件に入る。ただし live campaign は 0 件

`orchestrator/campaign/build_admission.py:458-466` の `_new_policy()` は
preimage に `"repo_stock_pin": CURRENT_PIN` を含める。
`artifact_admission.py:1044-1046` は記録済み campaign lock の `build_admission` を
現行 policy の preimage と **exact 比較**し、違えば
`post-policy campaign lock admission policy differs` で拒否する。
`pin.py` も `build_admission.py` も E1 の 25 path には入っていないので、
これは E1-stale とは別経路である。

**実測した在庫:**
- `output/` 配下の `campaign.lock` = **32 件**
- そのうち `repo_stock_pin` を持つ (= post-policy 世代) = **2 件**
- その 2 件の記録値 = `"d706650"` (= PREVIOUS_PIN)。
  → **現行 pin `511c953` の下で既に不一致であり、pin bump で新たに壊れるものは無い。**
  2 件はいずれも `output/insights/2026-08-04_wave-a-campaign-transport-smoke/evidence/` 配下の
  歴史 evidence であって live campaign ではない。

→ 依頼の問い (4)「既存 campaign が E1-stale になるか、なるなら何件か」への確定回答:
  **E1-stale = 0 件。`repo_stock_pin` 経路でも新規に壊れる live campaign = 0 件。**

## G6 (訂正) — canonical s1 凍結の source SHA も動くが、その関数は**既に赤**

luna は「merge で Options.cmake の source SHA が変わり、`verify_document()` が
HELD 外の source-sha 検査で落ちる」を blocker として挙げた。前半は正しい:

| | Options.cmake の sha256 |
|---|---|
| `known_axes_freeze.json` の記録値 | `7f8656c1…` |
| 現行 working tree (= 現 pin) | `7f8656c1…` **一致** |
| master 取り込み後 | `038b560a…` **不一致** |

`s1_known_axes_freeze.py:845-858` の source-sha 検査は `HELD_CHECK_IDS` に無い。

**ただし親の実測では、この検査へ到達しない。** `K.verify()` は同関数のより手前
(:839-842) で既に落ちている:

```
verify() FAILED: FreezeError
generator sha256 不一致: recorded=1d4d45a3… actual=a9edc1dc…
```

これは pin とは無関係な既存のドリフトで、原因は generator 自身の後続改変
(`135836be feat(freeze): 凍結チェーンの同一性検証を保留する (D328 / [T-917])` ほか)。
`orchestrator/tests/test_s1_known_axes_freeze.py` は `verify()` を **1 度も呼ばない**
(実測: grep で 0 件)。受入経路は `M.build_document()` + 独立 golden を使う。

→ **訂正後の位置づけ:** source-sha 不一致は「今日緑の経路を新たに赤にする」ものではなく、
  「既に赤い未使用関数に赤をもう 1 つ足す」ものである。blocker から **major (負債の深化)** へ格下げする。
  今日緑で bump により新たに赤くなるのは G1/G2 (source_digest)、F4 (`EXPECTED_SOURCE_LINES`)、
  F6 (床値 resolver)、G4 (7 桁 golden 7 箇所)、`test_s8b_approved.py:60` である。

## G7 (親の過大評価の訂正) — MOCC の pin は「動かす対象」ではない

親は F11 で「pin を動かすと T-1506 の MOCC branch も base ごと動かす必要がある」と書いたが、**過大**。

`tools/pegasus/mocc_trace_pilot.sh:640-648` は `new_oid` の実在と
「`base_oid` が `new_oid` の祖先であること」を検査するだけで、**現行 gitlink とは比較しない**。
`:657` は `new_oid` の detached worktree を作る。receipt も `outer_gitlink_advanced: false` を記録する。

→ `tools/pegasus/mocc_trace_v1_policy.json` の `base_oid`/`new_oid` と、
  `test_mocc_trace_job_contract.py:29` / `test_mocc_trace_pair.py:17` の literal は
  **実験 pair の identity** であって live な pin 束縛ではない。**更新してはならない** (更新すると
  既存証拠の identity を壊す)。F10 の「live 7 件」からこの 3 件を除く → **live 4 件**。

必要なのは「動かすこと」ではなく「**壊さないこと**」:
ローカル専用 ref `refs/izanagi/ccbench/t1506/mocc-trace-include` (`058d0c4e`) と
その object を削除しないこと。名前つき ref なので自動 prune の対象外である。

## G8 (親の誤りの訂正) — 「上げないと SS2PL が着手できない」は事実に反する

`brief.md` の成果物影響 (a) で親は「SS2PL を使う materials campaign が着手できない」と書いたが、**誤り**。

`output/insights/2026-08-25_ss2pl-lock-protocol-study/report.md` は
「CCBench commit: `511c9538…` **+ 本 study の out-of-tree patch**」で
YCSB-A / 1M records の SS2PL ロック規律 study (phase1〜4) を **2026-08-25 に完走**している。
`patches/ss2pl-lock-protocol-study.patch` が YCSB entrypoint を自前で足しており、
**現 pin のままで SS2PL YCSB は測れる。**

D790 (2026-08-25) はまさにこの形を裁定している —「改変は submodule へ commit せず
out-of-tree patch に置く (D16 第 4 類 / D18)」。却下理由に
「**submodule へ commit する:** gitlink 前進は承認定数の再承認と freeze の再凍結を確定的に
発生させる。価値が未確定の探索 variant にその費用を払わない」と明記されている。
**親が実測した費用は、D790 が既に言語化していた費用そのものである。**

→ 「上げない」の正しい費用は次のとおり。
  - 直近の探索は止まらない (study は完走済み、現行 critical path は Silo 系の B-4)
  - ただし当該 study は `pipeline.evaluate()` を通らない **descriptive / non-certified** であり、
    report 自身が「後続で正式採択するなら再測定が要る」と書いている
  - `tpcc_ss2pl.exe` は現 pin では 2 スレッド以上で確定的に落ちたままになる
  - upstream の修正が stock source の既定に入らないため、将来の正式採択時に
    overlay 維持か再統合の費用を払う

## G9 (新規、latent) — `.gitmodules` の宣言 branch は既に現 pin を指していない

`.gitmodules` は `branch = izanagi-trace` を宣言するが、
upstream の `izanagi-trace` は `d706650c…` (= PREVIOUS_PIN) であり、
現 gitlink `511c9538…` は `izanagi-trace-pin-t816` / `izanagi-trace-t816-fn2` の側にある。

→ `git submodule update --remote` を実行すると **pin が 1 世代巻き戻る**。
  pin を動かす動かさないに関わらず、この宣言の不整合は独立の是正候補である。

## G10 (新規) — SS2PL study patch は取り込み後の tree に当たらない

正例つき実測:

| 対象 | `git apply --check patches/ss2pl-lock-protocol-study.patch` |
|---|---|
| 現行 pin の tree | **OK** (エラーなし) |
| master 取り込み後の tree | **失敗 6 件** |

失敗の内訳: `cc/ss2pl/CMakeLists.txt`, `cc/ss2pl/include/common.hh`,
`cc/ss2pl/transaction.cc`, `cc/ss2pl/util.cc`, `cmake/Options.cmake` が
`patch does not apply`、および `cc/ss2pl/ycsb_ss2pl.cc: already exists in working directory`。

最後の 1 件が本質である。**izanagi の study patch が自前で足していた YCSB entrypoint を、
上流 #120 が別実装で入れた。** 取り込むなら重複の統合と、D790 が要求する
「既定 `IMPL=0, KIND=1, DLR=1` は stock 逐語 = patch は既定で inert」の再証明が要る。

---

## 子の指摘のうち採らなかったもの

| 指摘 | 判定 | 理由 |
|---|---|---|
| sol #1「D297 は diff status A/D/header で拒否するので merge は通らない」 | **部分的に real** | 結論 (gate が赤) は正しいが、機序が違う。実走すると `_validate_diff` (:669) の手前、`_assert_proven_repo_absent_macros` (:659-663) で落ちる。親は実測した機序 (G1/G2) を採り、予測された機序は採らない |
| sol #2「`.gitmodules` の `izanagi-trace` を merge 基点にすると T-816 が入らない」 | **real だが scope 外** | 基点の取り違えは実在の危険 (G9 で独立に記録)。ただし親は最初から `511c9538` を基点に測っており、この wave の測定は汚れていない |
| sol #5「pin 照合は 9 件でなく直接比較 6 件」 | **real、採用** | 親の F9 は「pin 照合そのもの」を粗く数えていた。ただし本 wave の結論 (保留下では追加コストが出ない) は変わらない |
| luna #2「source SHA 不一致は blocker」 | **real だが格下げ** | G6 のとおり、到達しない既存赤に隠れている |
| luna「(A) 上げない を推奨」 | **採用しない (親の裁定は択一をユーザーへ返すこと)** | 推奨の根拠 (SS2PL study 完走済み、critical path は Silo 系) は実測で裏づいたので裁定パッケージへ反映する。ただし本 wave の scope は択一の提示であり、親が決めることではない |
