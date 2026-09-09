# [T-2533] 段 1 brief — T-1998 事前登録の実値固定 (A-5 job body digest 更新)

wave: `dev-wave-t2533-t1998-prereg-digest` / branch: `worktree-dev-wave-t2533-t1998-prereg-digest`
worktree (子が読む repo path): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest`
基準 commit: `7f17e1c63`

## 研究前進

論文の「(性能) balanced で fixed 5µs が無 backoff より 11.3% 高い」を、**現行 Pegasus 環境で
prospective に測り直すための最後の未実装部品**が事前登録の実値である。D1874 が正式測定を認可済みで、
実値を固定しない限り 1 本も測れない。完了判定は、事前登録が確定し、consumer がその値を
手写しなしに受け取れること。測定そのものは本 wave では走らせない。

## scope

1. T-1998 (balanced stock-inline 対) の**事前登録を新規に作り、実値を固定する**。
2. consumer 側で、**成果物が記録すべき sha (job body digest = 測定時点の版)** と
   **解析規則の正本文書に要求する sha (現行の版)** を、D1790 に従い**独立した定数**として pin する。
3. 事前登録の値が consumer へ手写しなしに届く最小の経路を置く。

**scope 外:** 正式測定の投入・実行、A-5 の再投入、producer schema の拡張、
仮想リスク向けの gate・検査・台帳・一般化の追加、既存 A-5 投入器/job body/契約テストの変更。

## 確定済みユーザー裁定 (逐語は `verbatim/` にある)

- **D1874 (2026-09-09)**: 事前登録の実値 (期待 commit・gitlink・環境契約 digest・job body script
  digest・arm 別 source digest) を固定したうえで**正式測定を認可する**。2026-09-07 の balanced 生値は
  主張へ転用しない。→ D1267 の「着地後に改めて諮る」は消化済み。
- **D1790 (2026-09-08)**: 測定時点の束縛と現行の解析規則は別々の定数として pin する。
  どちらも「任意の値を受理」「複数版のいずれかを受理」へ緩めない。互換層は作らない。
- **D1244 / D1267**: T-1998 は既存 producer を使う最小 3 部品に閉じる。新しい汎用 driver を作らない。
- **D95**: 実装面 (コード・テスト・実行可能 script・機械設定) は Codex `role=author` が書く。親は書かない。
- **D1525 (2026-09-03)**: **A-5 は Pegasus では充足しない。未充足のまま残す。**

## 依頼文の前提のうち、実測で覆したもの

**依頼文の「旧 digest を指す事前登録のままでは A-5 の別 boot 再取得を開始できない (但し書き 3 が
外れない)」は誤り。** D1525 が A-5 を Pegasus では充足させないと確定し、後続裁定でも「A-5 は再投入
しない」と決まっている。digest を直しても但し書き 3 は外れない。**本 wave の成果物は変わらない** —
本題は D1874 が認可した stock-inline 対の事前登録固定である。子はこの訂正を前提に検査すること。

**「凍結済みの事前登録を erratum で直す」も発火しない。** repo 内に T-1998 の事前登録は存在せず
(`output/insights/2026-09-08_t1998-stock-inline-parts/README.md` §6 が「実値を確定していない」と明記)、
旧 digest `0ef4d41e…` の hit は過去の submit/reservation 記録と insight 逐語だけである。
**訂正すべき凍結 bytes が無いので、新規作成として作る。**

## 親が現物で実測した値 (`artifacts/` に生の JSON)

| 事前登録 field | 実測値 | 取得方法 |
|---|---|---|
| `launcher_script_sha256` | `dff913cb1044858b56f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8` | `sha256sum tools/pegasus/a5_second_boot_backoff_sweep.sh`。作業木と HEAD blob で同値 |
| `ccbench_gitlink_commit` | `511c9538e4e8efa54b45cda62e72389ed3b706ec` | `git submodule status --recursive` |
| `environment_contract_sha256` | `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` | `env_contract.REGISTRY["pegasus"].contract_sha256` |
| baseline `canonical_genome` | `silo\|BACKOFF_FIXED=-1,BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` | `Genome.canonical()`。consumer の定数と一致 |
| baseline `source_bytes_sha256` | `2d691b45afd02a7979b1872eeb0a5c5c58223550892331b31641599aa239a2c6` | `source_digest.resolve_evidence(g, "511c953", cxx="g++")` |
| target `canonical_genome` | `silo\|BACKOFF_FIXED=5,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` | 同上 |
| target `source_bytes_sha256` | `6454d9f34b04fdb148bc3324c5b07786d933dcc1ab0f7267aa0b91d414f70a84` | 同上 |
| `repository_commit` | **未確定** | 本 wave の着地 commit に依存する。下記 (P1-3) |

**DW-G01 の生死確認は済んでいる。** arm 別 source digest は測定を 1 回も走らせずに login node で
計算できた。`cxx="g++-13"` は login に実在せず fails-closed で落ちる。`backoff_sweep` は
Pegasus compute では `compilers_for_current_site()` が `("gcc","g++")` を返すので、
実測に使うのは `g++` 側である (`orchestrator/campaign/buildcache.py:1838-1842`、
`orchestrator/campaign/backoff_sweep.py:283-296`)。
2026-09-07 の A-5 実走 stdout 先頭が `The CXX compiler identification is GNU 11.4.0` で、
この login node の `g++` も 11.4.0 である。**版は一致するが同一 header の証明ではない。**
食い違えば `source-identity-unbound` で fail-closed に落ちるだけで偽の緑にはならない。

## 不変条件

- 規律 2 を緩めない。事前登録は受理集合を**狭める**方向にだけ働き、consumer の既存拒否を 1 つも外さない。
- 規律 3。事前登録は結果を見る前に固定する。2026-09-07 の balanced 生値を主張へ入れない (D1874)。
- 規律 7。歴史成果物の digest (`0ef4d41e…` を含む reservation / submit 記録) を**書き換えない**。
- F36。事前登録文書に自身の hash を書かない (自己参照禁止)。
- 既存 A-5 投入器・job body・契約テスト・登録簿 entry の bytes を変えない。
- 正式測定の人間認可を代行しない。本 wave では qsub を 1 回も打たない。

## 成果物の形

- 事前登録の正本文書 (docs、日本語)。実値と解析規則を固定し、除外規則と推定量の添字域を食い違わせない。
- consumer 側の D1790 準拠の 2 定数と、文書 → `T1998PreregisteredIdentity` の最小 loader。
- 境界テスト (D96): 旧 digest `0ef4d41e…` が `launcher-script-identity-mismatch` で拒否され、
  新 digest が通る正例。arm 別 source digest の正例・負例。
- worklog / decisions の spool fragment、insight。

## (P1) 親の provisional 裁定 — 子はここを攻撃せよ

- **(P1-1) 事前登録は `docs/` の文書 1 本を正本とし、b10 (`docs/b10-backoff-shape-preregistration.md`
  + `b10_backoff_shape_sweep.py:1763 load_preregistration`) と同型の「commit blob と作業木 bytes の
  一致」で束縛する。** 別形式 (JSON 成果物・module 定数直書き) の方が正しいなら、その根拠を出せ。
- **(P1-2) loader を置く。** 文書だけ作って consumer が受け取れない形は D1874 の「実値を固定した
  うえで認可」を満たさない、というのが親の判断。**loader が要求外の純増だという反論があれば出せ。**
- **(P1-3) `repository_commit` は事前登録文書に literal で書けない** (自身が入る commit を
  文書内に書けない、F36)。b10 と同型に `prereg_commit` を実行時引数で受け、HEAD の祖先であることと
  blob 一致を要求し、その commit を `repository_commit` の期待値にする案を親は採る。
  **より単純で束縛の強い形があれば出せ。**
- **(P1-4) D1790 の 2 定数の割り当て:** 成果物側 = `reservation.binding.script_sha256` が持つべき
  job body digest (`dff913cb…`)、解析規則側 = 事前登録文書に要求する sha256。
  **この割り当てが D1790 の意図と食い違うなら指摘せよ。**

## 変更面 (実アンカー)

| path:line | 現状 | 予定 |
|---|---|---|
| `orchestrator/campaign/t1998_stock_inline_pair.py:131-182` | 事前登録 dataclass 3 種。実値なし | 変更なし (型は再利用) |
| `orchestrator/campaign/t1998_stock_inline_pair.py:707-712` | `consume_balanced_stock_inline_pair(root, *, preregistered)` | 変更なし |
| `orchestrator/campaign/t1998_stock_inline_pair.py:915-919` | `launcher-script-identity-mismatch` の exact 比較 | 変更なし |
| `orchestrator/campaign/t1998_stock_inline_pair.py:522-533` | `source-identity-unbound` の arm 別比較 | 変更なし |
| 新規 (docs) | 不在 | 事前登録の正本文書 |
| 新規 (orchestrator/campaign) | 不在 | 2 定数 + loader |
| `orchestrator/tests/test_t1998_stock_inline_pair.py:391-410` | 合成 fixture | 境界テストを追加 (既存は壊さない) |
| `orchestrator/tests/acceptance_duration_ledger.json` | 新 test file を足すなら要登録 | 正本 producer の `--add-only` で登録 |
| `tools/pegasus/a5_second_boot_backoff_sweep.sh` | job body | **触らない** |
| `tools/pegasus/submit_t1998_balanced_stock_inline.sh` | 投入器 | **触らない** |

## 並列分割方針

段 2 は 1 本。段 3 は 2 レンズ並列 (正しさ境界 / 整合・実効性)。段 5 は所有を
「文書 (docs)」と「コード + テスト」に分けず、**受理集合が 1 つなので実装子 1 本**を既定とする。

## 受入・実測環境

Pegasus login node。build・benchmark・正式測定は本 wave では走らせない。受入全走は
`tools/dev_wave_wait.py acceptance --lease-optional` で親が実走する。
