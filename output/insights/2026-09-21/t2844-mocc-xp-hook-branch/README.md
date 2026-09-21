# [T-2844] mocc の X/P 計装を e9e477ca の単一の子 commit C として hook 系統 branch に載せた — D1603 材料 3 点 (候補 commit・D297・波及表) と C 上の正例・負例

authority: none
default_effect: no-state-change

- 日付: 2026-09-21
- wave: `dev-wave-t2844-mocc-xp-hook-branch` (branch `worktree-dev-wave-t2844-mocc-xp-hook-branch`)。着手時 local main `36fb14a3d131d516dc57b02ec69f56c711927c2e`
- 起点: ユーザーの `/dev-wave` 引数 (逐語 = `verbatim/request-t2844.md`)。入力 = `output/insights/2026-09-21/mocc-xp-pin-candidate/README.md` §3・§4・§7 と、同 dir の段 2 plan (`verbatim/s2-plan.md`、本 wave で流用)
- 既裁定: D2207、D2150 項 1、D2114 項 3、D1686、D1687、D579、D297、D780、D1603、D16 / D18 / D20、D95、D2153 (逐語は job dir `verbatim/`)
- job dir (親用 script・生 log・codex receipt・bundle): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2844-mocc-xp-hook-branch/`

## 0. 結論

1. **候補 commit C = `68106660686232781bca3be792a750d3e19d7a8a`** (ccbench の local branch `izanagi-mocc-xp-instrumentation`、未 push)。親は e9e477ca ちょうど 1 本、差分は `cc/mocc/transaction.cc` の +64 行だけ (mode 100644 不変)、blob `e393efbfd5fad7bbe05117b43669ccc0f44abb6a` (前 wave §3 の目標と一致)、tree `6dc0883c5bcc854eb6425101508b81a36bd7bf45`。
   中身は T-2294 の X/P 計装から `#include <set>` を足さず、P の snapshot 2 箇所を `std::unordered_multiset<const void*>` にしたもの。旧計装の適用結果との差はこの 3 行だけ (親の独立検算 `verbatim/verify-candidate.log`)。
   自己完結 bundle を job dir に保全し (verify 済み)、主 checkout の submodule git dir (`.git/modules/external/ccbench`) へ branch を非 force で fetch した (`verbatim/fetch-C-to-main.log`)。gitlink と submodule の HEAD は e9e477ca のまま。
2. **D297 (TRACE=0 正規化前処理 + include 活性) は C に対して GCC 11.4 / GCC 12.3 とも pass。** clang 14 は比較前に既知の限界で止まり**比較未完了**。旧計装 patch をそのまま commit した負例対照は同じ検査器が include 契約で拒否した (§3)。
3. **C 上の正例・負例 compute 1 走は all_pass** (Pegasus gen_S request 15646.nqsv、1 node、Elapse 132 秒、旧 driver と同じ 6 走・14 check)。stock 2 走は certified、single の負例 3 本は所定の X / P だけで indeterminate、lockskip-high は cycle を伴う non-serializable (§4)。
4. **波及表:** 現 main で `e9e477c` を含む tracked file 45 件 = 追随 15・据置 29・衝突 1 (`orchestrator/campaign/axis_mocc_temperature.py`)。文字列集合外の依存と、本 wave の追加物の将来の扱いを併記した (§5)。
5. push・gitlink と承認定数 (`CCBENCH_FULL_SHA` / `CURRENT_PIN`) の更新・再承認の提示・探索開始はしていない (依頼どおり scope 外、D16 / D18 / D20)。I 面 ([T-2295]) は不足のまま。

## 1. 依頼の完了条件と状態

| 完了条件 (worklog の [T-2844]) | 状態 |
|---|---|
| C の commit (e9e477ca の単一の子、hook 系統 branch) | **済** — §2 |
| bundle の保全 | **済** — job dir `C.bundle` (3,215,547 byte、sha256 `360805557b5e35abb34b746bcc7bbc7d8db9779e1f5c96244ec96ceff8315de5`、complete history、`git bundle verify` 済み) |
| 主 checkout の submodule git dir への fetch | **済** — 2026-09-21 21:48:29 JST、`refs/heads/izanagi-mocc-xp-instrumentation` = C |
| C 上の正例・負例の compute 1 走 | **済** — all_pass、§4 |
| C に対する D297 (GCC 2 版 + clang) | **GCC 2 版 pass、clang 比較未完了** — §3 |
| 波及表の点検 | **済** — §5 (段 2 plan の分類を現 main へ更新し、段 3 レンズ B と段 6 レビュー B が点検) |
| push・gitlink / 承認定数の更新・再承認の提示・探索開始 | 行っていない (scope 外) |

## 2. 候補 commit C

| 項目 | 値 |
|---|---|
| OID | `68106660686232781bca3be792a750d3e19d7a8a` |
| 親 | `e9e477ca1b55348ab4530de0b1cf663ce4555290` (1 本) |
| tree | `6dc0883c5bcc854eb6425101508b81a36bd7bf45` |
| raw diff (e9e477ca → C) | `:100644 100644 1f4e9453c39a42451e652b3a28d791b90844f184 e393efbfd5fad7bbe05117b43669ccc0f44abb6a M	cc/mocc/transaction.cc` |
| `cc/mocc/transaction.cc` sha256 | `712e31b5cbf2a3a63df442d50203c5c0787c98c83672d49a20210719bf32ebe4` |
| include 行 | 11 行、e9e477ca と同一 (`<unordered_set>` は同じ `#if TRACE` 枝で include される `include/trace.hh` が供給) |
| `#line` | 7 行 (17 / 990 / 991 / 1158 / 1169 / 1187 / 1195)、T-2294 と同じ |
| commit message | 逐語 = `verbatim/C-commit-message.txt`。trailer は Codex `role=author` (候補 patch の作成)、Codex `role=reviewer` (段 3 レンズ A の独立点検と段 6 レビュー、同一構成)、Claude `role=manager` |

- **作り方:** Codex author A が repo の `patches/instr-mocc-lock-coverage-pin-candidate.patch` (e9e477ca 基準、+64 / −0) を作り、親が wave 木の submodule に job dir 配下の一時 worktree を e9e477ca で切って `git apply --check` → 適用 → blob を目標と照合 → `commit -F` した (witlight の先例 `output/insights/2026-09-19/mocc-witlight-arm-run/README.md` §2・§7 の形、job dir `mk-C-commit.sh`)。
- **初版の置換:** 初版 `1035f1e394b71be2944db969f12dc74882c9d435` は、段 4 裁定で決めた trailer 3 行のうち reviewer 行が抜けていた (親が下書きの message を裁定後に更新し忘れた)。下流 (author B・D297・compute) が参照する前に、同じ tree・同じ親で message だけ直した commit を作り、branch を compare-and-swap で進めた (`verbatim/mk-C-amend.log`)。tree は同一だが commit の時刻 metadata も変わっている。旧 OID の log・bundle は job dir `superseded-1035f1e3/` に保全した。以後の全証拠 (D297・compute・JSON・固定期待値・bundle・fetch) は最終 C に対するもの。
- **patch の位置付け:** `patches/instr-mocc-lock-coverage-pin-candidate.patch` は branch C の可搬な再現資料であり、producer に重ねる第二の正本ではない (C checkout に重ねない)。他 wave の木の submodule は C の object を持つ保証が無い (`tools/dev_waves/git_state.py` の初期化は local・no-fetch) ので、repo の test は e9e477ca + この patch で候補 source を再構成して検査する。旧 `patches/instr-mocc-lock-coverage.patch` (旧命題 e9e477ca + patch の証拠) は bytes 不変。

## 3. D297 検査 (D1603 材料 2)

login `pegasus02`、`tools/check_trace0_preprocess_identity.py` (sha256 `9cf5b84ce30d187ad78afa5fd8111472a790db8a6010a90b44fba091470d8f69`)、`--repo <wave worktree>/external/ccbench --old e9e477ca1b55348ab4530de0b1cf663ce4555290 --new 68106660686232781bca3be792a750d3e19d7a8a --expect-paths cc/mocc/transaction.cc`。2026-09-21 21:17:11〜21:18:20 JST (`verbatim/run-d297.log`)。

| compiler (`--cxx`) | 解決先 | rc | 結果 | 逐語 |
|---|---|---|---|---|
| `/usr/bin/g++-11` | `x86_64-linux-gnu-g++-11` (11.4.0) | 0 | `result: pass`、`files[0].result: match` | `verbatim/d297-gcc11.report.json` |
| `/usr/bin/g++-12` | `x86_64-linux-gnu-g++-12` (12.3.0) | 0 | `result: pass`、`files[0].result: match` | `verbatim/d297-gcc12.report.json` |
| `/usr/bin/clang++` | `/usr/lib/llvm-14/bin/clang` (Ubuntu clang 14.0.0) | 1 | **比較未完了** — stdout 0 byte、stderr「preprocess 出力が空入力の環境 prefix と不一致 — identity を確定できないため fails-closed」(前 wave p6 と同じ既知限界) | `verbatim/d297-clang14.stderr.txt` |
| 負例対照: `/usr/bin/g++-11`、`--new` = scratch の一時 commit `9b3f3013e0c2ce83a616458eb660d98f52cfb652` (e9e477ca + 旧計装 patch そのまま、blob `1ec11e5c12aa7e673a794e744ee9ea0563d9ba66`) | 同上 | 1 | 拒否 — 「include 行文字列（順序込み）が不一致」 | `verbatim/d297-negative-gcc11.stderr.txt` |

- GCC 2 版の report: schema `izanagi-trace0-preprocess-identity/v2`、`old_is_ancestor_of_new: true`、差分 1 path (blob `1f4e9453…` → `e393efbf…`)、include 行 11。各 16 context で正規化前処理出力と include 活性が一致し、include 比較の basis は全件 `exact_identity`。正規化出力の digest は `148e44ea…` × 8 と `4db297ef…` × 8 (前 wave p4 と同じ値)。
- 16 context は report 上 8 genome × 2 overlay で、mocc に投影された define 集合としては各 compiler 4 種類である (段 6 レビュー A の読解)。16 種類の独立した mocc 構成・全 TU・admission toolchain 全体の検査へ一般化しない。
- 負例の一時 commit は job dir の scratch clone (`git clone --shared`) にだけ作り、wave 木の submodule の store に無いことを `git cat-file -e` (rc=1) で確かめた。
- 負例は fail-fast で include 契約により止まった 1 件であり、下流の比較経路の検出力までは示さない。

## 4. C 上の正例・負例 (compute 1 走)

- 実行: `python3 tools/pegasus/dispatch_compute.py --task generic --walltime 00:20:00 -- /usr/bin/python3 orchestrator/campaign/s3_mocc_lock_coverage.py --third-party-cache /work/1/SFC/tanab/izanagi-thirdparty-cache --candidate-oid 68106660686232781bca3be792a750d3e19d7a8a`、wave commit `9427eaad27055c3c575b8606828c7c2403f3019c` (clean tree) から。request 15646.nqsv、gen_S 1 node、21:31:56〜21:34:04 JST、Elapse 132 秒、child rc=0 (`verbatim/compute-1.log`)。
- **計算投入の確認:** 投入前にユーザーへ見積り (1 node × 約 2〜3 分、walltime 上限 20 分) を示し、「投入してよい」の回答を得た (2026-09-21 21:31 前後、ユーザー新指示 = rulings-inbox `2026-09-21-vldb-direction-verdicts.md` 項 4)。
- 結果 JSON: `output/env/pegasus/calibration/s3_mocc_xp_pin_candidate.json` (schema `s3-mocc-xp-pin-candidate/v1`、`all_pass: true`、14 check 全真、`diagnostic_build_admission` = NON_ADMISSIBLE)。

| run | 行列 | verdict / certified | cycle | X | P | reason | other_integrity_clean |
|---|---|---|---:|---:|---:|---|---|
| stock_single | C、patch なし、1 thread | serializable / true | 0 | 0 | 0 | — | true |
| stock_high | C、patch なし、4 thread | serializable / true | 0 | 0 | 0 | — | true |
| lockskip_single | C + lockskip、1 thread | indeterminate / false | 0 | 1,877,661 | 0 | 入口・write 前・publish 前が各 625,887 | true |
| lockskip_high | C + lockskip、4 thread | **non-serializable** / false | **3,525** | 2,363,434 | 0 | 入口 789,663・write 前 786,946・publish 前 786,825 | **false** |
| perm_erase_single | C + permutation-erase、1 thread | indeterminate / false | 0 | 0 | 221,263 | `size-changed` のみ | true |
| early_unlock_single | C + early-unlock、1 thread | indeterminate / false | 0 | 1,368,566 | 0 | write 前・publish 前が各 684,283、入口 0 | true |

**言えること・言えないこと:**
- single の負例 3 本は、公開された直交違反数 (X 負例の P = 0、P 負例の X = 0)・cycle 0・`other_integrity_clean` の範囲で、所定の X / P に限った拒否である。**lockskip_high は cycle と他の integrity 異常を併発した non-serializable で、単一理由の負例ではない** (旧 check が要求するのは X > 0 なので all_pass と矛盾しない)。`other_integrity_clean` は driver が列挙する integrity field の集約で、`Integrity.clean()` 全体 (proof surface・commit witness を含む) とは同義でない。
- stock 正例が certified であることは、verifier の `certified` が `Integrity.clean()` 経由で proof-surface gate (`certification_gate_satisfied`) を含むので、C の source root について gate が真であることを含意する (driver が build した source を `--ccbench-root` に渡すことは routing test で検査)。gate は X / P の emitter の存在であり、I 被覆・全経路の実行・将来の全 run の certified を意味しない。
- P の動的証拠は perm-erase の size 違反までである。同サイズの pointer 置換・多重度変更は、source 契約 test (旧計装からの 3 箇所変換との byte 一致) で静的に固定した。hot 経路 (hot-update-unlock) は C 上で再立証していない (T-2757 の命題であり本 wave の対象外)。
- TRACE=0: e9e477ca と C を等長 build dir (`trace0-pin0` / `trace0-cand`) で build し、nm の `izanagi` 0 件、strings の `izanagi_trace` / `IZANAGI_` 0 件、正規化逆アセンブル (行頭アドレスを除いた `objdump -d --no-show-raw-insn`) の一致 (差 0 行)。binary 全体の sha256 は異なる。**`.text` の bytes 一致は測っておらず主張しない** (段 4 裁定)。完全除去の十分条件でもない (D780)。

## 5. 波及表 (D1603 材料 3) — 将来 pin を C へ進める場合の扱い

母集合: 現 main (`36fb14a3d`) で `e9e477c` を含む tracked file のうち、docs の 3 台帳・`docs/archive/`・`docs/spool/`・`output/insights/` を除く **45 件** (前 wave 段 2 plan §6 の 43 件 + 日付版の論文ストーリー 2 件)。
分類は **追随 15・据置 29・衝突 1**。段 2 plan (Codex read-only) の起草を段 3 レンズ B と段 6 レビュー B が点検し、主分類の逆転は無い。親は件数と path 集合の一致を確認した。
**本表は文字列を含む file の分類であり、将来変更する file の完全一覧ではない** (集合外依存を併せて読む)。追随 = pin を C へ進める同じ変更単位で新しい値へ更新する。据置 = 歴史記録・旧命題の証拠・独立 source pin として値を保つ。衝突 = そのままでは C 系列へ接続できない。

| 分類 | file | pin 前進時の扱い |
|---|---|---|
| 据置 | `.claude/agents/auditor.md` | BASE の行位置を明示した proof 契約。C 向けの改訂は関連 hash 束縛を伴う別作業 |
| 据置 | `.codex/role-adapters/auditor.json` | 上記本文の休眠 adapter。pin だけで再生成・起動しない |
| 据置 | `docs/paper-story/2026-09-19.md`、`2026-09-20.md`、`2026-09-20b.md`、`2026-09-21.md`、`2026-09-21b.md`、`2026-09-21c.md` (新規) | 日付版の主張・取得事実 |
| 据置 | `docs/paper-story/README.md` | 既存結果の索引説明は保つ。新成果は新項目 |
| 据置 | `docs/paper-story/claim-evidence/2026-09-20.md`、`2026-09-21.md`、`2026-09-21b.md` (新規) | 日付版の証拠対応・主張境界 |
| 据置 | `docs/paper-story/results/2026-09-20-mocc-g2-observation-conditions.md`、`2026-09-20-mocc-witlight-four-arm.md`、`2026-09-21-b8-final-candidate-longrun-verify.md` | producer OID の実測記録・BASE に束縛された正式結果 |
| 追随 | `docs/phase3-8b-restart-runbook.md` | 現行 gitlink の期待値 (旧 floor の説明は保つ) |
| 据置 | `docs/related-work/cc-candidates-2026-09-17.md`、`docs/related-work/claim-survey/2026-09-18b-axis1-search-execution.md` | 調査時点の差分量・凍結済み裁定の引用 |
| **衝突** | `orchestrator/campaign/axis_mocc_temperature.py` | `PIN` は `CURRENT_PIN` に追随するが、`PROOF_PIN`・template・proof の束縛は BASE 固定。C 系列へそのまま接続できない (旧 proof の遡及取消しではない) |
| 据置 | `orchestrator/campaign/buildcache.py` | BASE の生成物形を再実測した履歴。C では生成物形の再確認が要る (本 wave の compute build は代用しない) |
| 追随 | `orchestrator/campaign/pin.py` | `CURRENT_PIN` (歴史定数は保つ) |
| 据置 | `orchestrator/campaign/s3_mocc_lock_coverage.py` | legacy `PIN` は BASE 固定。候補 mode とは分離 |
| 据置 | `orchestrator/campaign/s3_mocc_template_proof.py` | BASE 固定の template proof / control |
| 追随 | `orchestrator/campaign/s8b_approved.py` | `CCBENCH_FULL_SHA` (承認後に gitlink・`CURRENT_PIN` と同一 commit) |
| 据置 | `orchestrator/tests/acceptance_duration_ledger.json` | 旧 node 名と実測所要時間 |
| 据置 | `orchestrator/tests/test_between_run_floor.py` | BASE で R/W hook が入った履歴 (C でも事実は成立) |
| 追随 | `orchestrator/tests/test_dynamic_backoff_transitions.py`、`test_t2187_adaptive_const_probe.py` | 実 checkout の HEAD と照合する `PIN_FULL` |
| 据置 | `orchestrator/tests/test_mocc_mutation_proof.py`、`test_mocc_proof_surface.py`、`test_mocc_trace_job_contract.py` | BASE + 旧計装の proof、旧 pilot policy / receipt の契約 |
| 追随 | `orchestrator/tests/test_p3_build_authority_cli.py` | 現行 `repo_stock_pin` の独立期待値 |
| 追随 | `orchestrator/tests/test_p3_s4_loop.py`、`test_p3_s4_loop_sort.py`、`test_p3_s4_loop_trigger_gating.py` | policy preimage の現行 epoch・`CURRENT_PIN` alias の期待値 |
| 追随 | `orchestrator/tests/test_s6_sort_sweep.py`、`test_s8a_trigger_sweep.py`、`test_s8b_protocol_builder.py`、`test_t126_qualification_driver.py` | 現行 pin・characterization / policy・承認定数に束縛された golden (歴史 epoch は保つ) |
| 据置 | `output/env/pegasus/calibration/s3_mocc_lock_coverage.json`、`s3_mocc_mutation_proof.json`、`s3_mocc_template_proof.json` | 旧実測 bytes と hash 鎖 |
| 追随 | `patches/README.md` | C の採用状態・適用条件を追記 (旧 preimage の記録は書き換えない) |
| 据置 | `tools/pegasus/mocc_trace_v1_policy.json` | 511c → BASE の比較契約。C 向けは別契約 |
| 追随 | `tools/pegasus/probes/t2187_adaptive_const_probe.py` | `CURRENT_PIN` との一致を自ら要求する probe |

**本 wave の追加物 (上の 45 件には含まない。land 後は `e9e477c` を含むので母集合が増える):**

| 追加物 | 将来 pin を C へ進めるときの扱い |
|---|---|
| `patches/instr-mocc-lock-coverage-pin-candidate.patch` | 据置 — e9e477ca → C の固定再現資料。C に再適用しない |
| `orchestrator/tests/test_mocc_xp_pin_candidate.py` | 据置 — e9e477ca / C の OID・tree・blob の固定期待値 |
| `output/env/pegasus/calibration/s3_mocc_xp_pin_candidate.json` | 据置 — C で取得した診断記録として bytes を保つ |
| driver の候補 mode (`--candidate-oid`) | 据置 — e9e477ca の単一の子を検査する診断契約 |
| `patches/README.md` の候補 patch 節 | 追随 — 承認・採用状態だけを実際の進捗に合わせて追記 |

**文字列集合外の依存:**

- **policy epoch:** `build_admission` の policy preimage が `repo_stock_pin = CURRENT_PIN` を含むので、pin 前進で policy sha が動く。T-2304 (511c → e9e4) では SHA 文字列を含まない golden と live consumer に波及した: `test_autonomous_trial_completeness.py`、`test_campaign.py`、`test_p3_autonomous_workload_trial.py`、`test_p3_b4_closed_critic.py`、`test_s8b_materialization.py`、`test_s8b_floor_campaign.py` (preflight fixture) など (T-2304 の焦点走で 104 failed / 75 errors、受入でさらに 24 件、`output/insights/2026-09-20/t2304-pin-advance/README.md` §3)。旧証拠の保持と、新 main での旧 policy 成果物の live 消費 (`s8b_binary_admission`・`s8b_ratified_freeze`・`s8b_floor_campaign`・`ident`・`p3_s4_loop`・`paper_story_a1_paired`) は別であり、後者は新 main から消費できなくなる (D2184)。
- **floor protocol:** `resolve_current_floor_protocol()` は現行 env 契約の候補が 1 件ならそれを返し、複数なら gitlink と pin が一致する 1 件を選ぶ (`orchestrator/campaign/s8b_floor_campaign.py`)。候補が 2 件 (anchor d706650 / versioned 511c9538) ある現状では、C の gitlink と一致する successor protocol が無いと fail-closed になる。
- **patch の preimage:** (a) 旧計装 `instr-mocc-lock-coverage.patch` を C に再適用すると二重計装になる。(b) 温度述語 template `mocc-temperature-predicate-variant.patch` 単体は X/P を足さず、C への移植は template 自身の適用可否と `#line` の相互作用の確認が要る。(c) 計装 template 版 `instr-mocc-lock-coverage-temperature.patch` の preimage は e9e477ca + template で、C 系列では X/P が既に C にあるので、template を C へ移したうえでの計装の差し直し (または不要化) が別途要る。
- **mocc trace pilot / D2153 receipt v2:** `tools/pegasus/mocc_trace_pilot.sh` は旧 X/P patch の path / hash・適用後 source hash・TRACE=0 build 配線を束縛する。new_oid だけ C に置き換えると二重適用・命題不一致になる。本 wave の候補 JSON は receipt v2 の代用品ではない。
- **生成物形:** `buildcache.py` が要求する CMakeCache / DependInfo の形は pin ごとに再実測する (T-2304 §2 の先例)。
- **自前 PIN・fixture・事前登録・較正・凍結:** 旧 source pin を保つ driver (`p3_s4_loop.py:PIN`、backoff 解析の `CCBENCH_PIN` など) と現行 policy に依存する部分を分ける。C の取得値と主張する新系列だけ再取得・新登録する。
- **auditor 本文の hash consumer:** 本文を C 向けに改めるなら adapter・review ledger・関連 test の hash 同期も要る。

## 6. 実装・検査・レビューの経過

| 段 | 内容 | 結果 |
|---|---|---|
| 段 1 | 開始 gate (fresh、乖離 0)、brief (`verbatim/s1-brief.md`、provisional (P1)〜(P9)、条件表 08 / 09 / 10 / 13)。Codex 利用枠は他 wave の codex 子 (20:27〜20:43、rc=0) で復帰を実測 | — |
| 段 2 | 前 wave の plan を流用 | — |
| 段 3 | 相談 A (正しさ・観測者効果、20:57:12〜21:03:44) / B (過剰・削除・pin 材料、20:59:13〜21:04:44)。B の初回は親の prompt の path 誤りで子が fail-closed 停止し (36 秒)、資料を job dir へ写して再投入 | A: must-fix 2 (単一理由性、`.text` bytes の説明)、B: must-fix 1 (C の OID 変更時の証拠更新順) ほか should |
| 段 4 | 裁定 (`verbatim/s4-ruling.md`) | 候補固有 check key 0 本 (識別 2 条件 + blob 束縛は build 前の fail-closed 停止)、check は旧 14 key、`.text` bytes は測らず主張を縮小、hot 2 走は不採用、P9 (事前 build) は compute 本走の最初の build で代替、変異 15 件を登録 |
| 段 5 | author A (21:10:34〜21:13:38、候補 patch 1 file) → 親が独立検算・統合 commit `6c0f6af81` → 親が C を commit・置換 → author B (21:17:46〜21:29:08、driver +157 行・新 test 330 行 5 node・README +21 行) → 統合 commit `9427eaad2` | 両 author の自走検査は緑 (B の node 5 は候補 JSON 不在で期待どおり赤) |
| compute / D297 | §3・§4 | 候補 JSON commit `6fa89b563`、新 test 5/5 緑 |
| 焦点走 | 新 test・旧 mocc test 3 本・spawn inventory・build authority・inventory 4 群・目録 meta 3 本・patches 走査 node・materializer 登録簿 node (request 15671.nqsv、1 node、Elapse 136 秒) | **787 passed / 5 skipped / 0 failed** (`verbatim/focus-1.log`) |
| 段 6 | レビュー A (正しさ・証拠の解釈、21:37:25〜21:42:49) / B (過剰・削除に固定、21:37:27〜21:42:32) | **両方 GO、must-fix 0**。should は記録の訂正 (負例 verdict を run 別に書く、floor resolver の選択規則、template 系 preimage の区別、本 wave 追加物の扱い、MP3 / MP4 の kill の帰属) で本 README に反映。nit 1 (新 test の routing fixture のコメント「Clone only BASE history」は実装 (通常の local clone) より強い) は成果物に影響しないので直していない。fix 子は起動していない |

- 新 test (`orchestrator/tests/test_mocc_xp_pin_candidate.py`) の 5 node: `test_candidate_source_contract` (旧計装からの 3 箇所変換との byte 一致・include・X/P 構造・固定 blob / sha256・負例 3 本の厳密適用)、`test_candidate_trace0_logical_rows`、`test_candidate_identity_checks` (4 条件の正例と 1 条件ずつの拒否)、`test_candidate_mode_source_routing` (BASE だけから作る使い捨て repo に BASE の子 commit を作り、識別・checkout・patch 適用・verifier root・旧 JSON path 拒否・blob 不一致で build 前停止を実物で通す。build・実行・verifier subprocess・依存物準備だけを差し替え)、`test_candidate_json_is_bound` (候補 JSON を親の固定期待値と e9e477ca + 候補 patch の再構成に照合、1 文字改変の拒否対照を含む)。
- 登録簿 (materializer・spawn inventory・build authority・condition gate) は変えていない (新しい `"--build"` 関数・subprocess 呼び出し箇所・macro なし)。legacy mode の既存処理・定数・出力 schema / path は不変 (help 表示には新 option が増える)。

## 7. 計算量

2026-09-21 21:1x のユーザー指示 (実験の計算投入は見積りを示して確認)、続く 21:3x の追補 (1 タスクの job 合計が 2 node 時間以上なら事前確認、受入・焦点走・変異も数える) に従った (rulings-inbox `2026-09-21-vldb-direction-verdicts.md` 項 4)。
本 wave の計算ノード使用 (記録 commit 時点): compute 1 走 Elapse 132 秒、焦点走 Elapse 136 秒、変異本走 16 run の runner wall 合計 約 1,524 秒 (dispatch の待ち列を含む上限値。1 run だけ待ち列込みで 1,072 秒、他は 27〜38 秒)。合計は多くても約 0.5 node 時間。受入全走は記録 commit を含む tip で行い、合計が 2 node 時間に届かない見込み (直近 wave の受入は 3 shard、test 実行区間 343 / 188 / 137 秒)。

## 8. 変異 matrix

段 4 裁定 §4 で事前登録した 15 件を、独立 clone (D1009、main = `6fa89b563f27e8e99186cfe27113115cf721f780`) の固定 commit で `tools/mutation_worktree.py --runner-mode dispatch` により走らせた。
runner = `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_mocc_xp_pin_candidate.py -q -rf` (login 自走 probe と同じ file 集合)。spec sha256 `fcb35c25bf5edffe73a0f5202b532ad7e3a27e3c37e2625abe545ab3ab6e4478` (`verbatim/mutation-spec-final.json`)。
期待 node は login 自走 probe (`verbatim/probe-1.json`、baseline 0 失敗、15 件すべて失敗 node あり、各件の復元を sha256 と `git status --porcelain` 空で照合) から登録した (DW-M08)。

**結果: baseline PASSED、15 / 15 KILLED、期待 node との完全一致 15 / 15** (`verbatim/mutation-final-results.json`)。

| id | 変異 | 失敗 node (test_mocc_xp_pin_candidate.py) |
|---|---|---|
| MP1 | 候補 patch: P snapshot 宣言 1 箇所を `unordered_set` に | source_contract、mode_source_routing、json_is_bound |
| MP2 | 候補 patch: `#line 17` → `#line 18` | trace0_logical_rows、source_contract、mode_source_routing、json_is_bound |
| MP3 | 候補 patch: P の比較 `if (post != pre)` を `if (false)` に | source_contract、mode_source_routing、json_is_bound |
| MP4 | 候補 patch: X 入口検査の条件を恒偽に | source_contract、mode_source_routing、json_is_bound |
| MD1 | driver: 親列検査を「PIN を含む」に緩める | identity_checks |
| MD2 | driver: raw diff 検査を先頭行だけに緩める | identity_checks |
| MD3 | driver: 新 mode を 100644 以外も受理 | identity_checks |
| MD4 | driver: blob 束縛の停止を外す | identity_checks、mode_source_routing |
| MD5 | driver: 候補 mode で旧計装 patch を C に重ねる | mode_source_routing |
| MD6 | driver: 候補 mode の負例で broken patch を当てない | mode_source_routing |
| MD7 | driver: TRACE=0 の比較相手を PIN でなく C に | mode_source_routing |
| MD8 | driver: verifier root を build した source 以外に | mode_source_routing |
| MD9 | driver: 旧 JSON path の拒否を外す | mode_source_routing |
| MJ1 | 候補 JSON: `ccbench_commit` を 1 文字変える | json_is_bound |
| MJ2 | 候補 JSON: `candidate.reconstructed_blob` を 1 文字変える | json_is_bound |

- **帰属:** MP1〜MP4 の source_contract の赤は、旧計装からの 3 箇所変換との **bytes 一致の assert** が最初に落ちたもので、後続の X/P 構造 helper が単独で殺したことは示していない (段 6 レビュー A / B)。mode_source_routing と json_is_bound の併発赤は、変異した patch から作る候補 source の blob が固定期待値と違うことによる (冗長な束縛 gate)。MP2 だけは TRACE=0 論理行列の検査 (trace0_logical_rows) も落ちた。
- MD1〜MD9 と MJ1・MJ2 は、それぞれ 1 条件だけを壊す拒否対照・配線検査・consumer の固定期待値で落ちた (MD4 は識別の純関数と実 git の配線の 2 node)。
- hot 経路・21 key・`.text` bytes の変異は登録していない (実装しない検査)。

## 9. 主張しないこと

- pin を C へ進めてよいこと (再承認は D2114 項 3 の見送り台帳経路で別途、人間手番)。C が GitHub の ccbench に存在すること (未 push)。
- clang での同一性。D297 の合格が規律 1 の十分条件であること (必要条件の一つ、D780)。16 context が mocc の実効構成を 16 種覆うこと。
- TRACE=0 の `.text` bytes 一致。TRACE=1 の観測負荷が T-2294 と同一であること (容器が違うので同一でない)。
- hot 経路の C 上での再立証、同サイズの pointer 置換の動的立証、I 被覆 ([T-2295])。
- lockskip_high が単一理由の負例であること。

## 10. 再現資料

- 逐語 (`verbatim/`): `request-t2844.md`、`s1-brief.md`、`s4-ruling.md`、`s3-consult-A.md`、`s3-consult-B2.md`、`s5-author-A.md`、`s5-author-B.md`、`s6-review-A.md`、`s6-review-B.md`、`verify-candidate.log`、`mk-C-commit.log` (初版、置換済み)、`mk-C-amend.log` (最終 C)、`C-commit-message.txt`、`fetch-C-to-main.log`、`run-d297.log`、`d297-gcc11.report.json`、`d297-gcc12.report.json`、`d297-clang14.stderr.txt`、`d297-negative-gcc11.stderr.txt`、`compute-1.log`、`focus-1.log`、`probe-1.json` (変異の login 自走 probe)、`mutation-spec-final.json`、`mutation-final-results.json`。
  うち `compute-1.log`・`focus-1.log`・`mk-C-amend.log`・`mk-C-commit.log`・`verify-candidate.log` の 5 file は `git diff --check` のため行末空白だけを除去した (可視文字不変)。原文の sha256・byte 数・除去した行と文字列 = `verbatim/NORMALIZATION.md` (DW-S07 の可逆最小正規化、正規化 script `normalize_verbatim.py` は job dir)。
- 親用 script (repo に入れない、job dir、sha256 先頭 8 桁): `mk-C-commit.sh` 38f9c956、`mk-C-amend.sh` a12c5241、`fetch-C-to-main.sh` a4599cea、`run-d297.sh` 62a89b2c、`run-compute.sh` c2c1336f、`run-focus.sh` 59ec4f4c、`verify_candidate.py` 1d28072f、`make_mutation_spec.py` f71c5809、`mutation_probe.py` dd1fce9f、`run-mutation.sh` 3f57a574、`make-mutation-source.sh` a0d62047、`extract_verbatim.py` 832b07f2。
- bundle: job dir `C.bundle` (sha256 `360805557b5e35abb34b746bcc7bbc7d8db9779e1f5c96244ec96ceff8315de5`)。置換前の bundle は `superseded-1035f1e3/C.bundle`。
