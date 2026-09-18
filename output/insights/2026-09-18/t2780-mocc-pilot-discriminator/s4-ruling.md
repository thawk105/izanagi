# 段 4 裁定 — [T-2780] (親、2026-09-18 15:31 JST — mtime 実測)

裁定 inbox 再走査: 本 wave に関わる新規項目なし (最新は 14:33 の受入門番契約 = 段 6 で使う)。

## 1. 所見の裁定 (real / refuted、採否、scope)

| # | 出所 | 所見 | 裁定 | 採否 | scope |
|---|---|---|---|---|---|
| P-1 | plan 異議 | verifier `--ccbench-root "$CCBENCH_BASE"` (2231) は pin 511c9538 の未計装 checkout を読む。patch を当てても verifier の proof-surface (X/P evidence) は absent のまま → T1943 mode は `BUILD_SOURCE` を渡す | **real** (親が `model.py:130,174〜177` で検算。source 本文を読む) | 採用 | 内 (本題 2 を verifier に届けるのに必要。配線修正であり受理集合は不変、A 判定と一致) |
| A-S1 | レンズ A | receipt の `patched_source_sha256` は build 入力の証明ではなく記録。`trace0_built_from_patched_source` / `trace0_identity_witness` は receipt から省き insight に書く。witness test の保証範囲は「include 除去後の前処理比較」に限定 | real | 採用 (B-S3 も同時に閉じる: test 識別子は receipt に載せない) | 内 |
| A-S2 | レンズ A | patch marker の BEGIN/END count==1 と順序を patch 契約 test に入れる (既存 marker 列挙 test は固定 tuple) | real | 採用 | 内 |
| A-N1 | レンズ A | version 変異の限界の書き方 (「比較除去」は殺す、「文字列を残した恒真化」は保証外) | real | 採用 (insight の記述) | 内 |
| A-N2 | レンズ A | 旧候補の hydrate 拒否 stub はケース (a) 限定 (b では python3 が成功候補) | real | 採用 | 内 |
| A-N3 | レンズ A | hydrate 実行失敗 (非 0) の stage は既存 ERR trap の `shell`、新 test の被覆外と明記 | real | 採用 (記述のみ) | 内 |
| A-N4 | レンズ A | 全候補不在時 `rejected: none` は既存 gate と同じ | real | 不採用 (変更なし、既存挙動) | — |
| A-N5 | レンズ A | decisions fragment は削除可 / receipt writer と job-result writer の検査の役割分担 | 一部 | decisions fragment は **1 件出す** (receipt schema の interface 変更は routing 2 に該当、短く)。検査の分担は A 案を採用 (receipt writer = 実 bytes/sidecar 照合、job-result writer = v2 の必須 field・型) | 内 |
| B-MF1 | レンズ B | qsub の request ID `N.nqsv` と実行環境 `$PBS_JOBID` = `0:N.nqsv` は別。done file は `job-staging/0:N.nqsv/job-result.json` | **real** (T-2774 の done file 実績と pilot 57/76 行で検算) | 採用 (親の待ち手・判定 script) | 内 |
| B-MF2 | レンズ B | `dev_wave_wait.py compute` は done 非空 **または** accounting 終端で success を返し JSON の意味を見ない → 親の判定 script で終端・`failure.json` 不在・schema・digest 鎖・conclusion を評価 | **real** | 採用 (判定 script `judge_liveness.py` を job dir に置く。条件式は §4) | 内 |
| B-S1 | レンズ B | cache 5 dir の存在は hydrate 契約適合を覆わない → 投入前に `fetch_third_party.py verify` | real | 採用 (親が実施済み: rc=0、`thirdparty-verify.json`、5 source とも pin=HEAD) | 内 |
| B-S2 | レンズ B | receipt の 3 引数は全 mode で渡し、T1943 は非空必須、general は空で binding も artifact も出さない | real | 採用 | 内 |
| B-S3 | レンズ B | test 識別子を receipt に載せると実行したように読める | real | A-S1 で閉じる (載せない) | 内 |
| B-S4 | レンズ B | job-staging は worktree 内 (gitignore 外) に残る。land 前の扱いを決める | real | 採用: land は main 側衝突 untracked しか見ない (dev_wave_land.py 2050〜) ので障害でない。**job 終了後に attempt dir を job dir `attempts/job-staging-copy/` へ退避し insight は両 path を書く** (T-1878 の raw 喪失の再発防止) | 内 |
| B-N1 | レンズ B | 失敗途中 artifact の二重赤は起きない | real | 変更なし | — |
| B-N2 | レンズ B | 空 stdout artifact の意味 | real | 5 artifact を維持、manifest reason に「通常空」と書く | 内 |
| B-N3 | レンズ B | general-mode 漏れ検査への 5 file 追加は既存方式の追随 | real | 採用 | 内 |
| B-N4 | レンズ B | fetch / parse / general mode へ広げない | real | 採用 | 内 |
| B-N5 | レンズ B | author 1 本は妥当、作業順 hydrate → patch/source → receipt/schema | real | 採用 (`--max-model-calls 400`) | 内 |

親 brief の訂正: (i)「nm/strings」→「TRACE=0 binary の bytes 読取り + 同 fd への `nm -a` + T1943 既定 token/symbol の不在検査」、(ii)「discriminator mode は indeterminate しか出せない」→「verifier rc=3 で pilot が停止する」、(iii) 現行 general mode も verifier source は 511c9538 checkout を読む (本 wave は general mode を変えない。この不一致は insight §限界に記録、起票はしない)。

## 2. plan v2 (段 2 plan からの差分だけ。それ以外は plan の逐語を正とする)

1. receipt `t1943_g2_discriminator.instrumentation_patch` = `{repo_path, sha256, touched_paths, patched_source_sha256, trace0_built_from_patched_source: true}` の 5 field。test 識別子は載せない。
2. patch 契約 test に `# BEGIN/END T2780 INSTRUMENTATION PATCH` の count==1 と順序 (BEGIN < END < `build_mode() {`) を入れる。hydrate 契約 test も同様 (plan どおり)。
3. hydrate 契約 test の「旧候補の hydrate 拒否」は (a) の fake python3 だけ。
4. receipt 組み立て python の 3 引数 (`"${PATCH_PATH:-}" "${PATCH_SHA:-}" "${PATCHED_SOURCE_SHA:-}"`) は全 mode で渡す。T1943 は非空 + 64 hex + 実 bytes/sidecar 一致を必須、general は空を要求し binding・追加 artifact を出さない。
5. verifier 起動 (2226〜2232): `VERIFIER_SOURCE_ROOT="$CCBENCH_BASE"`、T1943 なら `"$BUILD_SOURCE"`。`--ccbench-root "$VERIFIER_SOURCE_ROOT"`。`CCBENCH_BASE` 自体は変えない。契約 test は mode=1/0 で `--ccbench-root` の値を fake verifier の argv で検査。
6. manifest の 5 artifact: `instr-patch.sha256` / `instr-patch.numstat` / `instr-patch-source.sha256` = `correctness_evidence`、`instr-patch-apply.stdout` / `.stderr` = `operational_diagnostic` (reason に「通常は空」)。T1943 専用 pattern として general-mode 漏れ検査 (622〜631) に 5 exact filename を追加。
7. schema: writer 3164 → `mocc-trace-pilot-receipt/t1943-g2-v2`、admitted set 3346 は v1 を v2 に置換、3349 の分岐も v2。job contract test 4576 の期待を v2 に。v2→v1 改変 + sidecar 再計算で job-result が作られないケースを追加。v4 正例・v3 拒否は維持。
8. decisions fragment 1 件 (receipt schema の t1943-g2-v2 置換: 理由 = patch 有無で source 命題が異なる、旧 v1 非受理、general v4 不変、verifier 判定不変)。
9. 生死確認: done file = `<wave worktree>/output/env/pegasus/mocc-trace/job-staging/0:<N>.nqsv/job-result.json`。投入直後に `job-staging/` を list して dir 名を実測してから待ち手を張る。待ち上限 21600 s (queue 込み)。完了後に `judge_liveness.py` (§4) → attempt dir を job dir へ退避。
10. 編集 file (author 1 本の所有): `tools/pegasus/mocc_trace_pilot.sh`、`orchestrator/tests/test_mocc_trace_job_contract.py`、`orchestrator/tests/test_pegasus_tools.py`。触らない: `fetch_third_party.py`、`orchestrator/verifier/**`、`patches/**`、`test_ccbench_spawn_sites.py`、docs 全般。

## 3. 変異の事前登録 (DW-M01、実装前)

すべて位置は plan v2 の挿入後の pilot、赤理由は 1 つに絞る (同じ入力を拒否する層が前後に無いことを実装後に author に確認させる)。

| ID | 変異 (位置) | 殺す test / ケース | 単一理由 |
|---|---|---|---|
| M1 | hydrate 呼出の `"$HYDRATE_PY"` → `python3` (旧 1534 行) | hydrate test (a): hydrate の interpreter identity ≠ 選択 path、(a) の fake python3 が hydrate argv で rc≠0 | 選択結果が hydrate に配線されない |
| M2 | probe の `sys.version_info >= (3, 10)` 条件除去 (`raise SystemExit(0)`) | hydrate test (d): probe argv の文字列検査 | version 条件の不在 |
| M3 | `hydrate_py_rejected+=` 行の除去 | hydrate test (c): message / stderr に 4 候補が並ばない | rejected 記録の欠落 |
| M4 | `git -C "$BUILD_SOURCE" apply "$PATCH_PATH"` 行の除去 | patch test 正例: source が preimage のまま、apply 呼出記録なし | patch 未適用 |
| M5 | numstat の awk 検査除去 | patch test: 2 file の numstat で rc=0 / apply 到達 | touch set 未検査 |
| M6 | `if [[ "$T1943_G2" -eq 1 ]]` guard 除去 (常時適用) | patch test mode=0: git 呼出 0・source 不変・5 artifact 不在 | general mode への漏れ |
| M7 | verifier の `--ccbench-root` を `"$CCBENCH_BASE"` に戻す (T1943) | verifier 配線 test mode=1: argv の `--ccbench-root` ≠ `BUILD_SOURCE` | source 配線の欠落 |
| M8 | receipt の `instrumentation_patch` binding 除去 | receipt test: field 不在 / digest 不一致 | 束縛の欠落 |
| 正例 P1 | 変異なし | hydrate (a)(b) rc=0・hydrate 到達 | — |
| 正例 P2 | 変異なし | patch 正例: postimage・digest・artifact・呼出順 | — |
| 正例 P3 | 変異なし | general v4 receipt 正例 (既存 4562) 不変 | — |

M1〜M3 が依頼の負例 3。M4〜M8 は plan 由来。変異走行は段 6 で `DW-M07` を読んでから (spec/out は checkout 外、走行中は worktree に書かない)。

## 4. 生死確認の成功判定 (親の `judge_liveness.py`、job dir)

```
success = pbs-job.stderr が存在 (終端)
      and attempt_dir/failure.json が不在
      and attempt_dir/job-result.json が存在し schema == "mocc-trace-pilot-job-result/v2" (現物で確認)
      and receipt.schema_version == "mocc-trace-pilot-receipt/t1943-g2-v2" and receipt.status == "completed"
      and sha256(receipt bytes) == sidecar == job-result.receipt_sha256
      and receipt.t1943_g2_discriminator.instrumentation_patch.sha256 == sha256(patches/instr-mocc-lock-coverage.patch @ 投入 commit) == instr-patch.sha256
      and instr-patch-source.sha256 == receipt ... patched_source_sha256
      and instr-patch.numstat の path == ["cc/mocc/transaction.cc"]
      and receipt.gates.trace0_preprocess_identity_rc == 0 and workload_rc == 0 and verifier_rc in {0,1} and discriminator_rc == 0
      and sha256(discriminator.json) == receipt の discriminator 束縛
      and discriminator.conclusion in {"no-g2","supported","contradicted"}
```
queue timeout は「未完了」(成功にも欠陥にも数えない)。verifier rc=1 経路は実走しなければ「fixture の被覆のみ」と記す。

## 5. 段 5 / 6 の構成

- 段 5: author 1 本 (`.codex/worktrees/t2780-author`、branch `impl-dev-wave-t2780-mocc-pilot-discriminator-author`、base = wave HEAD c8e8dc06f)、`--max-model-calls 400`。
- 段 6: レビュー A (正しさと契約: 規律 2、hydrate 選択と実 argv、patch 適用順、verifier source、marker 一意性、schema 置換、変異の検出条件) / レビュー B (実行と artifact: 5 artifact 分類・general 漏れ・receipt と実 bytes・投入形・完了判定・insight 引用)。fix は同 author 契約。変異 matrix (M1〜M8 + P1〜P3)。受入全走は門番 script 経由。
- 生死確認は実装 commit 後、**専用 detached worktree** (`.codex/worktrees/t2780-compute`、実装 commit に固定、submodule 初期化、lock) から投入する (T-2774 の node worktree と同型)。理由: pilot の判定時 source 捕捉 (pre/post) は投入元 worktree の `git status` を見るので、受入・変異・fix と同じ wave worktree から投入すると untracked 混入で `post_judgment_source` rc=2 になりうる。done file はその compute worktree の `output/env/pegasus/mocc-trace/job-staging/0:<N>.nqsv/job-result.json`。job 終了後に attempt dir を job dir へ退避してから段 9 で worktree を撤去する。wave worktree では受入・変異を並行して進める。
