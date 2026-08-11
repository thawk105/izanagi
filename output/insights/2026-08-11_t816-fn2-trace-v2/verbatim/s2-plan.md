両正本を読めたため、以下を実装プランとする。推奨は「C 行の arity で v2 を識別し、`E <txid>` を全 X 検査後に置く」「全差分パスを fail-closed に検査する `tools/` checker」である。コード変更は行っていない。

## A. trace v2 の C++ 変更

### 1. 現行 v1 契約

現行形式は [trace.hh:17–23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/include/trace.hh:17) と各 emitter から次のように確定する。

| 種別 | 現行形式 | 実装 |
|---|---|---|
| C | `C <txid> <thid> <epoch> <tid>` | [trace.hh:78–82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/include/trace.hh:78) |
| R | `R <txid> <key_hex> <ver_epoch> <ver_tid>` | [trace.hh:84–89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/include/trace.hh:84) |
| W | `W <txid> <key_hex> <op> <epoch> <tid>` | [trace.hh:91–96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/include/trace.hh:91) |
| X | `X <txid> <key_hex> <reason>` | [trace.hh:113–120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/include/trace.hh:113) |

C/R/W は txn ごとに連続し、C が txn の開始境界である [trace.hh:21–23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/include/trace.hh:21)。

### 2. C 行の v2 化

変更対象は [cc/silo/transaction.cc:584–607](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/silo/transaction.cc:584) のみとする。

1. 現行 `emit_commit` 呼び出し [transaction.cc:594–595](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/silo/transaction.cc:594) を、既存 `izanagi_trace::stream(thid_)` への直接出力に置き換える。
2. v2 C 行を厳密に `C <txid> <thid> <epoch> <tid> <read_count> <write_count>` とする。件数は直後のループと同じ `read_set_.size()` / `write_set_.size()` から取るため、実際に出力予定の R/W 行数と一対一になる [transaction.cc:596–607](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/silo/transaction.cc:596)。
3. 同ブロックのコメントに「Silo v2 の C/E 形式」「`emit_commit` を意図的に使わない理由」「R/W helper は従来どおり」を記録する。`trace.hh` のコメントは SI が使う v1 helper の説明として残す。

直接 `stream()` を使う方式には P 行の実装先例がある [transaction.cc:390–402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/silo/transaction.cc:390)、[transaction.cc:420–433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/silo/transaction.cc:420)。D41 の条件を実装した先例本文も、hook 迂回を退けて同方式を採用している [decisions.md:1305–1315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/docs/decisions.md:1305)。

### 3. 終端マーカーの位置

形式は厳密に `E <txid>` とし、[transaction.cc:684–686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/silo/transaction.cc:684) の既存 `#if TRACE` ブロック内で、`clear_shadow()` の直後に出す。

選択肢の比較は次のとおり。

- R/W ループ直後、すなわち [transaction.cc:601–608](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/silo/transaction.cc:601) に置くと、R/W 尾部欠落は件数と E で検出できる。一方、その後の entry X [transaction.cc:608–623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/silo/transaction.cc:608) や retention X [transaction.cc:635–668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/silo/transaction.cc:635) が末尾切断されても、既に E があるため「完結」と誤認しうる。
- 全 X の後に置けば、後段 verifier は「C の宣言件数どおりの R/W があり、writePhase の全 trace 検査点を通過し、最後に E がある」ことを要求できる。WAL や write loop 中の停止も E 欠落として fail-closed になる [transaction.cc:626–686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/silo/transaction.cc:626)。

したがって後者を推奨する。ただし E が残ったまま中間の X 一行だけが恣意的に除去された場合、X 期待件数を宣言していないため検出できない。R/W 欠落は C の件数で検出できるが、X の中間欠落は残余リスクとして明記する。

### 4. 編集面と `#if TRACE`

`external/ccbench` の許可面は二ファイルだけである [guard_write.py:36–38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/hooks/guard_write.py:36)。本変更ではそのうち `cc/silo/transaction.cc` だけを編集し、以下は一切変更しない。

- `external/ccbench/include/trace.hh`
- `external/ccbench/cc/si/transaction.cc`
- 親 repo の gitlink、`CURRENT_PIN`、`CCBENCH_FULL_SHA`

すべて既存の `#if TRACE` [transaction.cc:584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/silo/transaction.cc:584)、[transaction.cc:684](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/silo/transaction.cc:684) 内に置く。`-DTRACE=0` でも真になる `#ifdef TRACE` は禁止する根拠が D14 にある [decisions.md:198–208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/docs/decisions.md:198)。

SI は引き続き v1 helper を使用する [cc/si/transaction.cc:526–554](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/si/transaction.cc:526)。したがって、手順4で protocol 無差別に v1 を拒否する前に、SI の編集面を別裁定で解決する必要がある。

### 5. v1/v2 の判別と現行 verifier

別の `V 2` 行は置かず、C 行そのものの arity を版識別子にする。

- v1 C は全5 token。
- v2 C は全7 token。
- v2 txn はさらに全2 token の `E <txid>` を必須とする。

これなら末尾切断で E が失われても、先頭の C だけで v2 と判定できる。版行を一ファイル一回だけ出すには、本来 stream 初期化点 [trace.hh:49–63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/include/trace.hh:49) を変えるか、transaction 側に追加の thread-local 状態が必要であり、今回の編集面では利点がない。

現行 verifier に v2 を渡すと次の挙動になる。

1. parser は `split()` 後、C を厳密に5変数へ unpack する [parse.py:89–104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/verifier/parse.py:89)。7-token C は `ValueError` となり、`ParseError` に変換される [parse.py:176–178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/verifier/parse.py:176)。
2. 仮に旧 C と E を混在させても、E は未知 tag として `ParseError` になる [parse.py:163–175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/verifier/parse.py:163)。
3. pipeline はこれを `trace-parse-error` で abort し、fitness/certification を付けない [pipeline.py:1023–1030](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/pipeline.py:1023)。

したがって「互換ではないが fail-closed」であり、本 wave で parser を暫定的に緩める必要はない。v2 の厳密な件数・E 検証と v1 拒否は手順4の仕事とする。現行 FN-2 characterization [test_verifier.py:642–657](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_verifier.py:642) はこの wave では変更・反転しない。

## B. TRACE=0 翻訳単位同一 checker

### 1. 配置と予定構造

新規ファイルは `tools/check_trace0_tu_identity.py` とする。予定行構成は次のとおり。

- `tools/check_trace0_tu_identity.py:1–35`（新規予定）: CLI、40-hex 検査、エラー型、結果 schema。
- `tools/check_trace0_tu_identity.py:36–95`（新規予定）: 二 commit の object 解決、祖先関係、NUL-safe raw diff 列挙。
- `tools/check_trace0_tu_identity.py:96–160`（新規予定）: commit ごとの defines、include、条件マクロ、TRACE=0 preprocess。
- `tools/check_trace0_tu_identity.py:161–215`（新規予定）: byte 比較、SHA-256 evidence、決定論的 JSON 出力。
- `tools/check_trace0_tu_identity.py:216–245`（新規予定）: `argparse` と fail-closed `main()`。

`tools/` は enforcement source closure の exact 8 path に含まれない [campaign_lock.py:27–38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/campaign_lock.py:27)。campaign の実行契約を変更せず、承認前の独立 checker として置けるため、この配置に賛成する。

### 2. 既存機構の再利用範囲

再実装せず、checker から以下を直接再利用する。

- `_git_show`: commit blob の fail-closed 取得 [source_digest.py:597–611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:597)
- `_head_defines`: 各 commit の Options/CMake から実 TU define 集合を得る [source_digest.py:632–637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:632)
- `_include_lines`: preprocess が捨てる include 行を順序込みで抽出する [source_digest.py:569–577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:569)
- `_assert_conditional_macros_covered`: 未知マクロと `__has_include` を拒否する [source_digest.py:487–557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:487)
- `_normalize_contexts` → `_cpp_normalize`: context macro の両枝を含む preprocess [source_digest.py:320–373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:320)

一方、次は目的が異なるためそのまま使わない。

- `compute()` は working tree と固定 `EVOLVE_BLOCK_SOURCES` を読むため、二 commit 比較には使えない [source_digest.py:640–651](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:640)。
- `assert_trace_diff_matches_head()` は各 pin 内の TRACE=1/0 差を比較する。pin 自体が前進すると baseline も前進するため、旧 pin 対新 pin の TRACE=0 同一性を保証しない [source_digest.py:699–730](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:699)、[ruling-package.md:45–50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/output/insights/2026-08-11_t756-commit-witness/verbatim/ruling-package.md:45)。
- `_has_trace_symbols` は名前ベースで、strip や無名のデータ構造漏れを完全には証明できない [buildcache.py:1021–1049](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/buildcache.py:1021)。checker には組み込まず、実 perf build の補助防壁として残す。

### 3. 二 commit の検査アルゴリズム

1. 必須入力は旧・新の full 40-hex commit。両方を `^{commit}` として解決し、同一 commit、存在しない object、旧が新の祖先でない関係を拒否する。symbolic ref は受けず、実走報告には解決済み OID を出す。
2. `git diff-tree --raw -z --no-renames` 相当で**全差分パス**を取得する。名前に `trace` を含むか等のフィルタはしない。
3. empty diff、追加・削除・rename・copy・type/mode change、regular C/C++ source/header 以外の変更をすべて拒否する。さらに本 wave の契約として、全差分集合が厳密に `{cc/silo/transaction.cc}` であることを要求する [brief.md:37–45](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/brief.md:37)。
4. `genome.SILO_SPACE.enumerate()` の有効8 genome 全件で比較する。この集合は no-wait XOR、BACK_OFF、WAL の実探索面を列挙している [genome.py:34–42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/genome.py:34)、[genome.py:74–85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/genome.py:74)。
5. 各 commit/genome について `_head_defines` を取得した後、必ず `TRACE="0"` で上書きする。実 build も genome define と `CCBENCH_TRACE=<0|1>` を明示している [buildcache.py:840–844](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/buildcache.py:840)。
6. old/new 双方へ条件マクロ検査を掛け、include 行列を完全一致させた後、全 context の正規化出力をUTF-8 bytesとして直接比較する。SHA-256 は比較手段ではなく報告 evidence としてのみ使う。
7. 成功時は full OID、祖先関係、全差分 status/path/mode、compiler path/version、全 genome/context の一致 digest を JSON で stdout へ出す。何らかの取得・decode・preprocess・比較失敗では非0終了し、警告や skip へ落とさない。

### 4. 死角と封鎖

| 死角 | 扱い |
|---|---|
| preprocess が `#include` を削除する | old/new の include 行を順序・表記込みで比較する [source_digest.py:569–577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:569)。header 自体の変更も全差分走査で捕え、本 wave では追加差分として拒否する。 |
| `-D` が外部から供給される | commit ごとの CMake 供給集合を解析し、認証対象の Silo 8 genome を全列挙する [source_digest.py:624–637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:624)。未知条件マクロは拒否する。任意の手動 `-D` は承認 build 面外であり、その実行まで保証したとは報告しない。 |
| `__has_include` | literal と macro 経由の双方を既存ガードで拒否する [source_digest.py:504–510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:504)、[source_digest.py:535–543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:535)。 |
| ファイル追加・削除・rename | 全 raw diff を先に列挙し、M の同一 regular blob pair 以外は比較不能として拒否する。unsupported path を黙って無視しない。 |
| preprocess / git / compiler 失敗 | `_cpp_normalize` と `_git_show` の RuntimeError を CLI 非0へ変換する [source_digest.py:333–351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:333)、[source_digest.py:597–611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:597)。SKIP、空集合成功、部分成功を設けない。 |
| compiler builtin / version差 | 同一 run 内で同じ compiler を使い、compiler identity を evidence に残す。実走は admission build と同じ `g++-13` を要求し、無ければ成功扱いしない [source_digest.py:320–340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:320)。 |

### 5. 合成 fixture の pytest

新規 `orchestrator/tests/test_check_trace0_tu_identity.py` を次の予定行で作る。

- `:1–80`（新規予定）: `tmp_path` 内に最小 CCBench 形の git repo、Options/CMake、old/new commit を作る fixture。new 作成後に old を checkout し、checker が working tree でなく object を読むことも固定する。
- `:81–120`（新規予定）: C 件数と E がともに `#if TRACE` 内にある正例。全8 genomeで成功し、full OID/path/digest を検査する。
- `:121–170`（新規予定）: `izanagi_trace::stream()` が `#if TRACE` 外へ漏れた必須負例、および `#ifdef TRACE` 負例。`TRACE=0` を明示定義するため双方とも必ず不一致になる。
- `:171–225`（新規予定）: include 差、未知外部マクロ、literal/macro 経由 `__has_include`、追加・削除・extra path、mode change をすべて拒否する。
- `:226–270`（新規予定）: malformed preprocessor、存在しない/swapped commit、存在しない compiler、CLI exit code の fail-closed 検査。

実在する新 submodule commit は fixture や期待値に埋め込まない。実 commit 対の検査は pytest 外で一回実走し、その証拠を worklog に記録するという brief の分離に従う [brief.md:42–47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/brief.md:42)。

## C. 実装順序、受入、復元

1. 親 gitlink、submodule HEAD、双方の clean 状態が d706650 で一致することを先に確認する。固定値は [pin.py:26–33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/pin.py:26)、[s8b_approved.py:65–67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/s8b_approved.py:65)。
2. A は submodule 内で d706650 から名前付き local branch を作り、`cc/silo/transaction.cc` だけを commit する。親 repo では `external/ccbench` を stage/commit せず、push もしない [brief.md:49–58](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/brief.md:49)。
3. B は独立して checker と合成 pytest を完成させる。A の full SHA が出たところで合流し、旧 d706650 対新 SHAを実走する。全差分集合、TRACE=0 bytes、include、8 genome がすべて緑でなければ A に戻る。
4. 新 HEAD を checkout 中に、既存の real-build controlを `tools/run_tests.py` 経由で実行し、TRACE=0/1 の二 build が成立することを確認する。このテストは submodule の実 HEAD を pin として使い [test_s8b_oracle_driver.py:4163–4177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_s8b_oracle_driver.py:4163)、両 build を要求する [test_s8b_oracle_driver.py:4222–4227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_s8b_oracle_driver.py:4222)。SKIP は成功証拠に数えない。perf 側では既存 nm guard も通る [buildcache.py:744–755](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/buildcache.py:744)。
5. 復元前に、名前付き submodule branch を repo 外の一意名 bundleへ保存し、`git bundle verify`、bundle heads、新 SHA、bundle SHA-256を確認する。推奨先は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/izanagi-trace-t816-<newsha>.bundle`。submodule の gitdir はこの worktree 固有領域にあるため [external/ccbench/.git:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/.git:1)、local branch だけでは worktree 撤去後の保存保証にならない。
6. bundle 検証後、submodule を `d706650cdb31e442bef45b9b4216951d4fb40969` の detached HEAD へ戻す。local branch は削除しない。submodule clean、親 `git status` clean、親 `git ls-tree HEAD external/ccbench` が同 SHAであることを再確認する。
7. その後に親 repo の受入を行う。`test_s8b_approved.py` は working tree の submodule HEADではなく committed gitlinkを読むため [test_s8b_approved.py:34–46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_s8b_approved.py:34)、gitlinkを動かさない限り新 HEAD checkout中も緑のはずである [test_s8b_approved.py:58–64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_s8b_approved.py:58)。
8. 実際に赤くなる経路は、旧 pin を宣言したまま実 submodule HEAD を照合する箇所である。floor E2E helper は HEAD が d706650 か直接 assert する [test_s8b_floor_campaign.py:471–492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_s8b_floor_campaign.py:471)、呼出側も d706650 を固定する [test_s8b_floor_campaign.py:3242–3258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_s8b_floor_campaign.py:3242)。通常 build も宣言 pin と実 HEAD の不一致を拒否する [buildcache.py:653–656](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/buildcache.py:653)、[buildcache.py:1071–1094](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/buildcache.py:1071)。また dev-wave clean scan は submodule commit dirt を別枠で検出する [git_state.py:300–318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/dev_waves/git_state.py:300)。
9. 復元後、新 checker pytest、関連 verifier characterization、pin/g​​itlink gate、全受入を `python3 tools/run_tests.py ...` 経由で実行する。`CURRENT_PIN`、`CCBENCH_FULL_SHA`、FN-2 characterization は不変である。親 commit 後は通常の docs／Codex-agent／provenance 検査まで行うが、push はしない。

## 総括

- **推奨する設計択一:** `E <txid>` は全 X と `clear_shadow()` 後、v1/v2 は C の5/7-token arityで判別する。checker は `tools/` に置き、`source_digest` の blob取得・define・include・macro guard・normalizeを再利用する。
- **(P1)(P2):** P1 に賛成。許可面内の直接 `stream()` は既存先例と一致する [decisions.md:1305–1315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/docs/decisions.md:1305)。P2 は本 wave に限り賛成するが、SI v1のまま手順4を全 protocolへ適用してはならない。
- **実装単位:** A は `external/ccbench/cc/silo/transaction.cc` と submodule commit/bundleだけ、B は `tools/check_trace0_tu_identity.py` と `orchestrator/tests/test_check_trace0_tu_identity.py` だけを所有し、ファイル集合を交差させない。
- **残るリスク:** SI未移行は将来の SI certified 行を拒否しうる。TRACE=0漏れは throughput/fitness と certified 選択を変え、中間X欠落はレポートの violation 件数と台帳の閉鎖判断を誤らせうるが、gitlink不変の本 wave 自体は既存成果物の値を変えない。