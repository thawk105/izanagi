# [T-2354] A-5 job 本体の共有 gitdir prune を撤去した

- 日付: 2026-09-09
- branch: `worktree-dev-wave-t2354-a5-prune-removal`
- 着手時 main: `cbcdb6c91bd2eced76bd6a82650204c357c1b299`、取り込んだ main: `5aa71fc930728d66e0bee292763585885e9d8a17`
- wave tip: `99f36357154415ca484d9d4f94fa52f12b56279b`
- 正本裁定: D1700 (2026-09-07 ユーザー裁定)、事故は F251 の 2026-09-07 再発

## 1. 何を直したか

A-5 job 本体 (`tools/pegasus/a5_second_boot_backoff_sweep.sh`) の終了処理は、自 path の
worktree を remove した後に、投入元 checkout の submodule gitdir へ
`git worktree prune --expire now` を打っていた。各 job の ccbench worktree は計算ノード
ローカルの `/scr/<jobid>-…/` にあるため、別ノードから見ると他 job の path は存在しない。
prune はそれを「消えた worktree」として登録ごと削除し、以後その job の git 呼び出しは
`fatal: not a git repository` になる。A-5 投入器は同じ checkout から 2 job を出すので、
**後に終わる job が必ずこの経路で落ちる構造**だった。2026-09-07 の実測では A-5 balanced が
8 genome を commit した後、T-2266 が 8 点中 6 / 6 / 4 点を commit した後に落ちている。

D1700 に従い、prune ブロックを撤去して自 path 2 つへの `worktree remove --force` だけに限った。
remove が失敗した path は receipt へ明示し、後続の安全な掃除へ回す。
投入器を workload ごとの checkout に分ける案は D1700 が却下済みで、本 wave では採らない。

## 2. 変更面

| path | 変更 |
|---|---|
| `tools/pegasus/a5_second_boot_backoff_sweep.sh` | `remove_worktrees()` から prune ブロック・`prune_rc`・`remove_rc` を撤去。receipt を新書式へ |
| `orchestrator/tests/test_a5_second_boot_job_contract.py` | prune 正例 2 assert を「実行可能な prune の不在」1 assert へ。実 git fixture の runtime test 2 本を追加 |
| `orchestrator/tests/acceptance_duration_ledger.json` | 追加 2 node を正本 producer の `--add-only` で登録 (F902) |

job body の sha256 は `0ef4d41ee1ddf8ecd7a86a32a3b9dbaf128279125ef4820c54421973ee281d84` から
`dff913cb1044858b56f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8` へ変わった。

### receipt の新書式

正常時は B-10 job 本体と同じ裸の cleanup rc 1 行。remove が成功しなかった path だけが続く。

```
0
```

```
<非 0 の cleanup rc>
remaining_ccbench_path=<path>
remaining_repo_path=<path>
```

`remaining_*` は remove 成功時に空へ更新される変数をそのまま書くので、「実際に残った path」
だけが現れる。案として挙がった「1 行 rc + stderr 任せ」は、cleanup の締切が尽きた経路では
git 自体を起動せず stderr に path が出ないため採らなかった。

## 3. 親が実測した機序 (使い捨て git repository)

負例が実際に発火することを、段 4 の裁定前に親が確かめた。

| 操作 | 結果 |
|---|---|
| `worktree lock` した自 path への `worktree remove --force` | rc=128 (`cannot remove a locked working tree`)、登録も directory も残る |
| directory だけ消した兄弟登録に対する自 path の `remove --force` | 兄弟登録は**残る** |
| 同じ兄弟登録に対する `worktree prune --expire now` | 兄弟登録は**消える** |

前者は「remove 失敗時に本当に残置が起きる」fixture の作り方、後者 2 つは「prune を戻すと
兄弟登録が消える」負例の発火根拠である。

## 4. 受理形をどう分けたか

契約テストが静的に固定するのは**実行可能な `worktree prune` の不在**だけにした。
remove が実際に起きること・receipt の中身・rc 伝播は、job 本体から `remove_worktrees` と
`cleanup_worktrees` を抽出して実 git repository 上で走らせる runtime test 2 本が固定する。
段 2 plan が提案していた remove 逐語の `count(...) == 1` pin は、`--` の追加や wrapper 化のような
D1700 を満たす等価実装まで拒否するので採らなかった (段 3 レンズ A の指摘、段 4 で採用)。
設計判断は decisions 台帳へ記録した。

### 限界 (主張せず明記する)

静的層は literal の `worktree prune` しか見ず、runtime 層は cleanup の 2 関数しか実行しない。
したがって**その外側に置いた難読化 prune** は両層を通過する。これは変異 M5 として事前登録し、
期待どおり SURVIVED することを実測した (下表)。ここへ bash token 解析の allowlist gate は
足さない — 依頼の scope 外であり、D387 のとおり gate と検査を同じ主体が変更できる限り、
repo 内の挙動検査は意図的な弱体化への完全な防壁にはならない。塞ぐべきは literal の
再導入という退行で、それは静的層が捕まえる。

## 5. 変異 matrix

spec `mutation/mutation-spec.json` (sha256 `faa3a51d41c1d8d2f133f8cdbaaa73567132540975043238464aec4fdb5e8fd9`)、
report `mutation/mutation-report.json`。baseline PASSED、`repo_head=99f36357154415ca484d9d4f94fa52f12b56279b`、
summary は `KILLED=5 / SURVIVED=1 / MISMATCH=0 / matching=6`。期待 node と失敗 node は全件完全一致。

| ID | 変異 | 期待 | 実測 |
|---|---|---|---|
| m1 | literal の prune を cleanup 内へ戻す | KILLED (静的 + 兄弟保存の 2 node) | KILLED、2 node 一致 |
| m1b | 難読化 prune を cleanup 内へ入れる (静的 regex を通過) | KILLED (兄弟保存 node のみ) | KILLED、1 node 一致 |
| m2 | `return "$cleanup_rc"` を `return 0` にする | KILLED (失敗 node) | KILLED、1 node 一致 |
| m3 | remove 失敗でも `JOB_CCBENCH` を空にする | KILLED (失敗 node) | KILLED、1 node 一致 |
| m4 | 元 job rc の優先を落とす | KILLED (失敗 node) | KILLED、1 node 一致 |
| m5 | 難読化 prune を cleanup の**外**へ置く | **SURVIVED** (検出漏れ probe として事前登録) | SURVIVED、node 0 件 |

m1 は静的層と runtime 層に同時に殺されるので冗長 gate であり、単独 gate の証拠には使わない。
runtime gate 単独の検出力は m1b が示す。m5 は §4 の限界を実測に変えたもので、
等価変異ではない (mutated 側は本当に共有 gitdir を prune する)。

## 6. 実測した検査

親が login 経由の dispatch で実走した (子 sandbox では `run_tests.py` が rc=16 になり走らない)。

| 走行 | 結果 |
|---|---|
| `test_a5_second_boot_job_contract` + `test_t1998_launcher_contract` + `test_official_perf_closure` | rc=0 |
| `test_hooks` + `test_backoff_extended_sweep` + `test_t1998_stock_inline_pair` | 551 passed, 1 skipped |
| `test_acceptance_schedule_order` | 79 passed (**台帳登録前から緑**) |
| `test_a5_second_boot_job_contract` 単独 (JUnit 取得) | 9 passed |
| `check_ai_provenance` 全史 | 9202 件、新規違反なし |

## 7. 閉包と波及

- **凍結 pin なし。** 旧 sha256 の hit は過去 submit 記録・reservation・T-1998 裁定逐語という
  歴史記録だけで、live な golden / `FROZEN_MANIFEST` / generator hash pin は無い。
- **登録簿は変更不要。** `tools/pegasus/admission_registry.json` は path を key にし、
  loader (`tools/pegasus_admission_registry.py`) に sha256 の参照は 0 件。hook も target path と
  class だけで判定する。既存登録済み実行体の本文編集なので F660 は発火しない。
- **receipt の runtime consumer は今回追加した test が最初。** 既存の
  `test_backoff_extended_sweep.py:1785` は B-10 の同名 file を読む別 producer の consumer。
- **T-1998 への波及 (コード変更なし)。** T-1998 launcher は同じ job body を再利用し、
  submitter が実 file を hash して reservation の `script_sha256` に運ぶ。consumer
  (`orchestrator/campaign/t1998_stock_inline_pair.py`) は事前登録の `launcher_script_sha256` と
  exact 比較するので、**新しい T-1998 の事前登録は着地後の新 digest で作り直す必要がある**。
  旧 digest を持つ live な事前登録は repo 内に無く、T-1998 の正式測定は未実施なので、
  既存の適格成果物は壊れない。歴史成果物の digest は書き換えない。
- **F902 の状態更新。** 「main 側の余裕は 1 node 未満」は現在は解消しており、
  node を 2 件足した状態でも被覆 gate は登録前から緑だった。登録自体は恒久対応どおり
  正本 producer で行った。

## 8. 却下・不採用にした所見

| 所見 | 判定 | 理由 |
|---|---|---|
| receipt 書き込み失敗の `\|\| true` を cleanup rc へ合成せよ (段 3 レンズ A) | real・不採用 | `\|\| true` は現行コードに既に在り本 wave の退行ではない。合成すると依頼が求めていない新しい失敗経路を job rc へ足す。限界として §4 と同様に記録する |
| remove 逐語の count pin・語彙禁止 assert を足せ (段 2 plan) | 一部不採用 | 等価実装まで拒否し受理集合を余分に狭める (§4) |
| 難読化 prune 検出のため bash token allowlist gate を足せ (段 6 レンズ A) | real・不採用 | 仮想リスク向けの gate 追加で scope 外。m5 で限界を実測に変えて明記する方を採った |
| `collect_receipt.py` や外部 collector が prune artifact を要求している可能性 | refuted | A-5 からの callsite が無く、repo 内に根拠なし |

## 9. 資料

- `verbatim/s1-brief.md` — 段 1 brief
- `verbatim/s2-plan.md` — 段 2 plan
- `verbatim/s3-consult-lensA.md` / `verbatim/s3-consult-lensB.md` — 段 3 敵対相談
- `verbatim/s4-adjudication.md` — 段 4 裁定 (変異事前登録を含む)
- `verbatim/s5-author.md` — 段 5 実装子報告
- `verbatim/s6-review-lensA.md` / `verbatim/s6-review-lensB.md` — 段 6 敵対レビュー
- `verbatim/s6-ledger-author.md` — 受入所要台帳の登録子報告
- `mutation/mutation-spec.json` / `mutation/mutation-report.json`
