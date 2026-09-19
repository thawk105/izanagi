# [T-2629] 旧 build 分岐の compiler 非対称 — 到達条件と既存の拒否の実測

`authority: none` / `default_effect: no-state-change` — これは**実測記録と裁定の材料**である。可変状態の正本
(worklog 末尾・現行 phase doc) ではなく、checker・build・gate の受理集合も変えていない。

- 実測日: 2026-09-20 (JST)
- 実測機: login node `pegasus02` (07:41 JST)、計算ノード `bnode020` (NQSV request `11860.nqsv`、07:42 JST =
  `2026-09-19T22:42:17Z`)
- 基準 commit: `b7f970dfa` (local main、wave branch `worktree-dev-wave-t2629-legacy-compiler-reach`)、
  CCBench submodule `511c9538e4e8` (= `pin.CURRENT_PIN` `511c953`)
- 起点: 台帳 entry 1498 (`docs/archive/worklog-phase3-0914-1498.md`) の T-2629 本文、T-1643 insight
  (`output/insights/2026-09-14/t1643-has-include-real-pair/README.md` §9 R-1)、裁定 D2044 項 24
- 依頼: 「旧分岐の compiler 非対称 (静的に確認済み、発生記録なし) の到達条件と既存の拒否を実測してから修正の要否を
  決める。限界として閉じる場合は、確認した呼び手の範囲を明記する。新 gate・台帳・一般化の追加は scope 外。」

---

## 1. 何が非対称か

`orchestrator/campaign/pipeline.py` の `_prepare_evaluation_core` は build の前に source identity (`SourceEvidence`) を
確定する (`:1788〜1812`)。このとき preprocess に使う compiler は `buildcache.compilers_for_current_site()` が選ぶ
(`:1790`)。一方 build は `env_contract` の有無で 2 経路に分かれる (`:1935〜2012`):

| 経路 | 条件 | build 関数 | compiler |
|---|---|---|---|
| v2 | `env_contract is not None` (`common` を作る) | `buildcache.build_v2(genome, trace, **common)` | `common["cc"/"cxx"]` = site 解決 (evidence と同じ値) |
| 旧分岐 (v1) | `env_contract is None` (`common is None`) | `buildcache.build(genome, commit, trace=..., ...)` を **cc/cxx 無し**で呼ぶ | 既定 `DEFAULT_CC/DEFAULT_CXX = gcc-13/g++-13` (`buildcache.py:622`) |

`compilers_for_current_site()` (`buildcache.py:1863`) は **実 site が `PEGASUS_COMPUTE` のときだけ `("gcc","g++")`** を
返し、それ以外の site では既定 (`gcc-13`/`g++-13`) を返す。したがって evidence と build の compiler **名**が食い違うのは

> **(A) `env_contract is None` (旧分岐) ∧ (B) `site_policy.current_site() == PEGASUS_COMPUTE`**

の積のときだけである。(B) 以外の site では旧分岐でも両者が既定で一致する (対称)。

前提: (A)(B) は「通常の未注入経路 (site / contract の注入なし)、site 観測中の hostname が安定、
`expected_toolchain_manifest` 無し」における記述である。manifest は `pipeline.py:1661` / `:2640` で `env_contract` 無しとの
併用を拒否する。`site_policy.classify_site` (`site_policy.py:30〜46`) は hostname `bnode[0-9]+` を環境値に依らず
compute に分類する (計算ノードの probe は clean env で `NQSV` 系の環境変数が無かったが、site は `PEGASUS_COMPUTE` と判定された)。

---

## 2. 到達条件 — 呼び手の閉包

### 2.1 certified 入口 3 API (`loop.run_campaign` / `pipeline.evaluate` / `pipeline._prepare_evaluation`)

`orchestrator/` + `tools/` の非 test を AST で走査 (import 解決つき、原本は job dir の `verbatim/callers-ast.txt`)。
呼び出し箇所は **28** = 中継 3 (`loop.py:768/782`、`screening_driver.py:641`) + 外側 25 (うち手動 test 1)。外側 25 の分類:

| 分類 | 件数 | 呼び手 (file:line) | (A) の成否 |
|---|---|---|---|
| `env_contract` を常に渡す | 11 | b10_backoff_shape_sweep:4470、b10_backoff_static_tail_formal:761、backoff_extended_sweep:1446、backoff_sweep:484 (+ screening 339/364)、p2_2:376、paper_story_a1_paired:7178/7428、paper_story_a2_certification:3803、t126_driver:623、s8b_oracle_driver:1781、manual_probes/test_t2397_a1_source:96 (monkeypatch を伴う手動 test) | (A) 偽 |
| site 条件付き | 2 | p3_s4_loop:2012、p3_s4_loop_trigger_gating:811 — `resolved_site == PEGASUS_COMPUTE` のとき contract を渡す (`p3_s4_loop.py:1996〜1998`、`p3_s4_loop_trigger_gating.py:802〜804`) | (B) のとき (A) 偽 |
| 渡さない (旧分岐) | 12 | backoff_repro:172、demo:57/67、p3_kickoff:152/159、p3_s4_loop_sort:413、p3_s4_red:207/217、s6_sort_sweep:413 (+ screening 321/421)、s8a_trigger_sweep:515 (+ screening 421/523)、sanity_silo:59、s1_direct_comparison:1281 | (A) 真。**ENV_TAG は全て `linux-baremetal`** |

**pegasus 契約で `env_contract` を省く呼び手は 0。** (A)∧(B) へ到達しうるのは、`linux-baremetal` の 12 呼び手を
計算ノードで起動した場合だけで、それは §3 (R-a) が evidence・build より前に拒否する。

### 2.2 pipeline を経ない legacy `buildcache.build()` の直接呼び手

直接 API には `env_contract` 引数が無いので、条件は「evidence 側と build 側の compiler が異なるか」で個別に見る。

| 呼び手 | evidence 側 compiler | build 側 compiler | 対称性 |
|---|---|---|---|
| s1_verify_extime_calibration:382/390 | 既定 (`resolve_evidence` に cxx 無し) | 既定 (`build` に cxx 無し) | 対称 |
| s2_verify_calibration:352/356-357 | 既定 | 既定 | 対称 |
| s3_lock_coverage:257/258 | 既定 | 既定 | 対称 |
| s5_permutation_coverage:292/293 | 既定 | 既定 | 対称 |
| between_run_floor:327〜340 | Pegasus なら site 解決、他は既定 | 同じ値を `build_kwargs` で渡す | 対称 |
| backoff_profile:847/857 | `runtime.cxx` | `runtime.cxx` | 対称 |
| pegasus_floor_scoping:214〜224 | site 解決 | 同じ値 | 対称 |

直接 legacy `build()` は **7 file・8 呼び出し箇所** (s2_verify_calibration が 2 箇所)。manual_probes / tools/pegasus/probes の
5 箇所 (legacy `build` 4: test_t2000_legacy_build_probe:1876、t1683_rr5_cost_probe:248、t2187_adaptive_const_probe:3941/4334;
`build_v2` 1: test_t2000_legacy_build_probe:1855) は compiler を明示する。**直接経路で同じ非対称は発見しなかった。**

閉包の限界: 上は静的閉包であり、任意の動的呼び出し (getattr / partial / shell) の不可能性の証明ではない。
対象 3 API への別名 import・関数参照代入は再走査して追加を発見しなかった (段 3 相談 A1)。

---

## 3. 既存の拒否 — 実測

probe (`t2629_legacy_compiler_reach_probe.py`、Codex `role=author` 作、147 行) は production の関数を stub 無しでそのまま
呼び、返り値と例外を JSON に記録する。共有 build cache には触れず、`cache_root` は job dir の専用空 dir。
呼び出し形は `pipeline.py:1738` (認可)、`:1809` (evidence)、`:1847〜1857` (admission 導出)、`:2002〜2008` (旧分岐 build) と同じ。

### 3.1 環境

| 項目 | login `pegasus02` | compute `bnode020` |
|---|---|---|
| `site_policy.current_site()` | `PEGASUS_LOGIN` | `PEGASUS_COMPUTE` |
| `compilers_for_current_site()` | `('gcc-13', 'g++-13')` (= 既定、対称) | `('gcc', 'g++')` (≠ 既定、**非対称**) |
| `which g++` → realpath | `/usr/bin/x86_64-linux-gnu-g++-11` (11.4.0) | 同じ (11.4.0) |
| `which g++-13` / `gcc-13` | **不在** | **不在** |
| `which cmake` | `/usr/bin/cmake` | `/usr/bin/cmake` |

`g++-13` 不在は、この 2 node・各観測日時・各 JSON の `results.env.observed.PATH` に限定した観測である (PATH は両 node で異なる:
login は `/home/SFC/tanab/.local/bin` で始まり、compute は `/usr/bin:/bin:…:/opt/nec/nqsv/bin:/opt/memverge/bin`)。
T-1643 (2026-09-14、`bnode009`) と合わせて計算ノード 2 台で不在を観測したが、全 node・将来の PATH へは一般化しない。

### 3.2 拒否の 3 層 (計算ノード `bnode020` の実測値)

| 層 | 呼び出し | 結果 (例外本文は JSON の逐語。configure 診断だけは改行を空白化し末尾を省略、全文は `probe-compute.json`) |
|---|---|---|
| **(R-a) 認可** `execution_guard.require_certified_writer_authorization(authorize('linux-baremetal'), env_tag='linux-baremetal', clocks_per_us=<登録値>, numactl=<登録値>, env_contract=None)` | `loop.py:177` / `pipeline.py:1738` と同形 | `CertifiedWriterAuthorizationError` (stage `guard`): `Pegasus compute では receipt state 内で一意な required authorization_contract だけを受理する` |
| 同上、`'pegasus'` | 同上 | 通過 (返り値 env_tag `pegasus`、attestation_mode `required`)。認可関数の通過であり full attestation の成功ではない |
| **evidence (site cxx)** `resolve_evidence(STOCK_G, '511c953', ccbench_dir=<sub>, cxx='g++')` | `pipeline.py:1809` と同形 | 成功: `src_token='stock'`、`tracked_clean=True`、`ccbench_commit='511c953'` |
| **evidence (既定 cxx)** 同上 `cxx='g++-13'` | cache-hit 側 `_recheck_source_evidence` (`buildcache.py:3491`) が呼ぶのと同じ関数・同じ compiler | `RuntimeError`: `source_digest: マクロ定義状態の照会を起動できない (g++-13: [Errno 2] No such file or directory: 'g++-13') — 文脈ガードを確定できないため fails-closed で停止 (D23)` |
| **(R-b) 旧分岐 build** `buildcache.build(STOCK_G, '511c953', trace=True, cache_root=<空 dir>, ccbench_dir=<sub>, src_token='stock', admission=<stock admission>, build_context=<BACKOFF_SWEEP>, source_evidence=<site evidence>)` **cc/cxx 無し** | `pipeline.py:2002〜2008` と同形。`build_run_context` → `derive_build_admission` → `require_build_admission` の 3 段は通過 | `RuntimeError` (stage `build`): `configure failed (rc=1): CMake Error at CMakeLists.txt:3 (project): The CMAKE_CXX_COMPILER: g++-13 is not a full path and was not found in the PATH. …` |

login では site compiler が既定 `g++-13` なので evidence が同じ RuntimeError で失敗し、build は `SkippedNoEvidence`
(login は heavy-work gate の外側で止まるため、R-b の configure 実測には数えない)。login でも認可は両 tag とも通過する
(compute 限定の規則 `execution_guard.py:137〜161` が発火しないため)。

### 3.3 拒否の順序 (静的読取、pipeline 経由の場合)

| 段階 | 旧分岐 × 計算ノードで起きること | pipeline の変換 |
|---|---|---|
| 認可 (`pipeline.py:1738`、`loop.py:177`) | `linux-baremetal` は `CertifiedWriterAuthorizationError` | evidence・build・WAL より前に例外 (loop では `_authorize_measurement` が最初の書込みより前) |
| 事前 evidence (`:1790〜1809`) | site compiler `g++` で成功 (stock なら `stock`) | — |
| fresh build: `_run(staging_cfg, "configure")` (`buildcache.py:3540〜3545`、`:3791〜3821`) | heavy-work site gate → `subprocess.run(cmake …)` → rc=1 → `RuntimeError("configure failed …")` | `pipeline.py:2024` の `except (RuntimeError, SubprocessError)` → `build-error` abort (非 retryable、`model.py:207〜214`) |
| 同上、cmake 自体が起動できない場合 | `_run` は `OSError` を捕捉しない → `FileNotFoundError` が素通り | `pipeline.py:2024` には入らず、`loop.py:795` 以降の `Exception` 隔離で `eval-exception` abort。直接 evaluate の呼び手には同じ隔離が無い (今回は cmake が在るので未到達) |
| cache hit: `_recheck_source_evidence(cxx='g++-13')` (`:3491`、`:3625〜3665`) | sidecar 検証を通った後、`resolve_evidence(cxx='g++-13')` が上表と同じ `RuntimeError` | 同じ except → `build-error` abort |

**(R-c) evidence の exact 一致 (`_recheck_source_evidence`、`buildcache.py:3656〜3665`):** build compiler で再計算した
`SourceEvidence` 全体 (`src_token`、`source_bytes_sha256`、proof snapshot、verification_variant) が事前 evidence と
異なれば `TOCTOU 検知` の `RuntimeError` で拒否する。これは「compiler 差を全て拒否する」ではない — `SourceEvidence` に
compiler 名は無く、同じ evidence を返す 2 compiler は通る (source identity の意味では正しい)。`g++-13` が在る機体で
この層が何を通すかは本 wave では実測していない (§6)。

---

## 4. 発生記録の検索

- worklog / failures: 旧分岐 × 計算ノードの発生記録なし (T-2629 本文も「静的に確認済み、発生記録なし」)。
- repo 内 (tracked) の campaign WAL 30 本 (`output/campaigns/*/runs/wal.jsonl`、JSON として厳密に集計): 3086 record は
  全部 `linux-baremetal`。`stage=abort` ∧ `payload.reason=build-error` は **12 件** (内訳 = compile error
  `build failed (rc=2)` 9、`ccbench_commit 不一致` 1、error 本文なし 2)。別に同じ reason を参照する `stage=s1-session`
  の記録 (再試行分類) が 18 件ある。記録された error 本文に compiler 不在型の診断 (`not found` /
  `CMAKE_CXX_COMPILER`) は発見しなかった。診断本文のない 2 件は原因を判定できない。`g++-13` を含む 463 record は全て
  `build_done` の `perf_configure_cmd` (`CMAKE_CXX_COMPILER=g++-13`) に現れる。
- 未検索: Pegasus の durable output root 配下の WAL、job の stdout/stderr。

---

## 5. 裁定 — 修正しない (限界として閉じる)

D2044 項 24 の形で閉じる。設計判断は decisions (本 wave の fragment) を正本とする。要点:

1. **到達不能:** pegasus 契約で `env_contract` を省く production 呼び手は 0 (§2.1)。`env_contract` を省く 12 呼び手は
   全て `linux-baremetal` で、計算ノードでは (R-a) が evidence・build より前に拒否する (§3.2 実測)。直接 build の
   7 呼び手は対称 (§2.2)。
2. **到達しても fails-closed:** 観測した計算ノード `bnode020` では `g++-13` 不在で、旧分岐 `buildcache.build()` の cmake configure が
   失敗する `RuntimeError` を直接呼び出しで実測した (§3.2)。pipeline 経由でそれが `build-error` abort へ変換されること、
   cache-hit 側で先行検査の後に既定 compiler の evidence 再計算が同じ `RuntimeError` で止まることは静的確認 (§3.3。
   同じ関数・同じ compiler の cell は §3.2 で実測)。
3. **修正候補を採らない理由:**
   - (i) 旧分岐へ site compiler を渡す — `g++-13` 固定は D293 が「現に効いている fail-closed 障壁」と位置づけたもので、
     床値 campaign では calibration 由来の toolchain 束縛検査と同じ commit でしか入れられない。加えて本 wave で
     必要性 (到達する呼び手) を確認できない。
   - (ii) 事前 evidence を旧分岐では既定 compiler にして対称化する — 失敗段階が build から evidence へ移り、WAL の
     abort reason が `build-error` (非 retryable) から `identity-error` (retryable、`model.py:207〜214`) へ変わる。
     再試行・集計の分類を変える変更であり「成果物不変」ではない。必要性も未確認。
   - (iii) 計算ノードでの旧分岐を明示拒否する新 gate — 依頼が scope 外と明示。
4. **実装面の差分ゼロ** (probe は repo に残さない) → 変異 matrix は免除。受入全走は land 前に 1 回行い、結果と log の所在は
   worklog (本 wave の fragment) と job dir の受領証 `acceptance-receipt-*.json` を正本とする。

---

## 6. 限界 (主張しないこと)

- **閉包は静的** (§2.2 末尾)。
- **`g++-13` 不在は観測事実。** `pegasus02` / `bnode009` (T-1643) / `bnode020` の 3 node、2026-09-14 と 2026-09-20 の PATH での
  不在である。`g++-13` が解決可能になった場合、現行呼び手への (R-a) は変わらないが、仮想的な旧分岐到達後の
  「不在による拒否」は消え、残る検査は (R-c) の evidence 一致だけになる。そのとき同一 identity・異なる toolchain の
  binary が v1 経路で作られうることは、本 wave では観測も否定もしていない (v1 に toolchain 束縛は無い。D293 の領域)。
- **(R-c) は「evidence の一致」であって「compiler の一致」ではない** (§3.3)。2 compiler 間の evidence 不一致の実測は
  していない (`g++-13` が無く pair を作れない。T-1643 §2 は `g++`/`g++-11`/`g++-12` の 3 名称で checker の対照表が
  完全に一致したことを別に記録している)。論文へ移せるのは「確認済み呼び手では当該非対称に到達せず、再照合は evidence の
  一致を要求する」という限定された主張であり、「compiler 差は fails-closed」を一般命題として採らない。
- **probe が測っていないもの:** pipeline の WAL abort 変換 (静的読取のみ、§3.3)、cache-hit 経路の実走、
  `pegasus` 契約の full attestation。認可通過は関数の通過であって attestation 成功ではない。
- **発生記録の未検索範囲** は §4 末尾。

---

## 7. 一次資料の所在

job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2629-legacy-compiler-reach/` に保全した。

| file | 中身 |
|---|---|
| `probe-login-parent.json` | login `pegasus02` の親実走 (4.6 KB) |
| `probe-compute.json` | compute `bnode020` の実走 (4.6 KB、NQSV `11860.nqsv`)、`probe-compute.log` は dispatch の log |
| `codex/t2629_legacy_compiler_reach_probe.py` | probe 本体 (147 行、Codex `role=author` が作成、repo へは残さない。unit branch `dev-wave-t2629-unit-probe` の終端 commit `39585d2fc` にも同一内容) |
| `verbatim/callers-ast.txt` | §2.1 の AST 走査結果 |
| `s1-brief.md` / `codex/s3-consult.md` / `s4-ruling.md` / `codex/s5-author.md` / `codex/s6-review.md` | 段 1〜6 |

子の逐語は本 dir の `verbatim/` にも複製した。**`verbatim/` は可逆最小正規化を施してある** (`DW-S07`): `s3-consult.md` (10 行) と `s6-review.md` (2 行) の Markdown 強制改行に使われていた**行末空白だけ** を `sed -i 's/[ \t]*$//'` で除去した (可視文字は不変)。原文は job dir 側にあり、下表の SHA-256 と byte 数で同定できる。

| verbatim/ の file | 原文 (job dir) | 原文の SHA-256 | 原文の bytes |
|---|---|---|---|
| `s1-brief.md` | `s1-brief.md` | `475b5f4d89fc9195c53a815ca79b90e1b1098e044952be3f9b96abcf10ed22d7` | 6998 |
| `s3-consult.md` | `codex/s3-consult.md` | `5a186b62733a22ec1a99c5f5a4cb3cca12dcf05354d890e874953415a2513871` | 16298 |
| `s4-ruling.md` | `s4-ruling.md` | `3161c4513499695b304b5fd51f9fc71a6e6dadc17c16b57c70288549fad78cfa` | 8561 |
| `s5-author.md` | `codex/s5-author.md` | `be2fd1fe1a5fdff02aebcaa4ea6412382fc92daa4adf99d99dd0750edc3bc658` | 2005 |
| `s6-review.md` | `codex/s6-review.md` | `4c759fed3fb307bc969104656ba8199174f3f9af3625b6bebaf00c6006c6059d` | 8005 |
| `probe-compute.json` | `probe-compute.json` | `720dd0cce02b57d332c23a29a39e213ae4ce81160ee3ef1b42ad9f730eec6308` | 4559 |
| `probe-login-parent.json` | `probe-login-parent.json` | `7cadf6ad8816ceead6d014bc4b4c7913c349c90a4e5c2feaf098782c0fd479e1` | 3823 |

compute 実測の再現 (wave worktree の root で、probe を `tools/` に置いて):

```
python3 tools/pegasus/dispatch_compute.py --task generic \
  --queue-wait-timeout 3600 --overall-grace 3000 --walltime 00:15:00 \
  -- python3 -B tools/t2629_legacy_compiler_reach_probe.py --output <出力先>.json --cache-root <専用の空 dir>
```
