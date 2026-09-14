# [T-2557] balanced stock-inline 正式対比較 — 投入・回収・解析

D1874 が認可し D1938 が AI 担当へ移した balanced の stock-inline 対 (無 backoff 対 静的 fixed 5 µs) を、
事前登録 `docs/t1998-balanced-stock-inline-preregistration.md` v1 の下で正式に投入し、回収し、
既存 consumer `orchestrator/campaign/t1998_stock_inline_pair.py` へ通した記録である。

**結論を先に書く。測定は完走した。しかし consumer は拒否を返した。**
拒否の原因は測定側ではなく consumer 側にあり、**実成果物では原理的に成立しない検査が 2 系統ある。**
是正のうち 1 系統は既裁定 (D924) だが、もう 1 系統は設計択一を含むためユーザー裁定へ返す。

## 1. 実行したこと

| 項目 | 値 |
|---|---|
| 投入器 | `tools/pegasus/submit_t1998_balanced_stock_inline.sh` (1 回だけ、fan-out なし) |
| 投入元 | 記録を書かない専用 detached worktree (repo 外、worktree lock 済み) |
| 投入時刻 | 2026-09-13 13:27:23Z |
| job | `995755.nqsv` (gen_S)。13:27:36Z 開始、13:39:23Z 終了、Elapse 712 秒 |
| repository_commit | `a551cdd3014708993475108f014aacbf32c21137` |
| 成果物 root (repo 外) | `/work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced` |
| submit receipt | 同 parent の `t1998-balanced-stock-inline-20260913T132723Z-548740.submit.jsonl` |

投入器の receipt が記録した digest は事前登録 §4 と一致した。

- `job_script_sha256` = `dff913cb1044858b56f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8`
  (事前登録 §4 の `launcher_script_sha256` と同値。§4.1 の撤去後の値であって旧値ではない)
- `submitter_sha256` = `dff1f9d0662a519e8427f6aa7571998ea8ba08f70d98931e960aec4f7813add8`

`load_preregistration` が投入時 HEAD から組み立てた identity も事前登録 §4 の表と 5 値すべて一致した。
gitlink `511c9538e4e8efa54b45cda62e72389ed3b706ec` /
環境契約 `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` /
launcher `dff913cb…` / baseline source `2d691b45afd02a7979b1872eeb0a5c5c58223550892331b31641599aa239a2c6` /
target source `678b7203aa1f9fdca4c35f9b3219d0b9662b60b22331484027adfc6c34580b12`。
事前登録 blob の sha256 は作業木・当該 commit とも
`464e3af59a1ef0f776cad022a52ab87e1fdf2709abfc2062c058203bc813719c` で、consumer の
成果物側・解析規則側の 2 定数の両方と一致した。

**producer は完走している。** WAL は 8 genome それぞれについて
`build_start` / `build_done` / `bench_done` / `verify_done` / `commit` を各 8 件持ち、abort は 0 件である。
`.failure.json` は生成されていない。

## 2. consumer の判定 (事前登録 §8 が要求する報告)

**判定: 拒否。**

| 項目 | 値 |
|---|---|
| code | `performance-build-not-trace-disabled` |
| field | `wal.bench_done.run_cmd.executable` |
| arm | baseline |
| 期待値 | `<build_dir>/cc/silo/ycsb_silo.exe` |
| 実際の値 | 同じ実行ファイル path に workload flag が続く run_cmd 全体 |

`<build_dir>` は
`/scr/0_995755.nqsv-a5-second-boot-balanced/job-repo/external/ccbench/build-variants/contracts/e576e9cd…/263ed3a3…`
である。**実行ファイル自体は期待値と一致している。** 拒否の原因は次節の 2 系統目の理由による。

## 3. 診断 — 実成果物では成立しない検査が 2 系統ある

### 3.1 numactl 前置を literal で固定している

`t1998_stock_inline_pair.py` は
`_KNOWN_BENCH_WRAPPER_PREFIX = ("numactl", "--interleave=all")` を持ち、
`_bench_execution_target` は run_cmd の先頭 2 語がこの literal であることを要求し、
一致しなければ `None` を返して拒否させる。

**この literal は `linux-baremetal` 契約の値である。**
`orchestrator/campaign/env_contract.py` の登録簿では
`linux-baremetal` が `numactl=("numactl", "--interleave=all")`、
`pegasus` が `numactl=()` であり、同 file は空 tuple を
「解決済みで launch prefix なし」として正当と明記している。
D144 は bnode002 が単一 NUMA ノードであることを実測し、Pegasus 契約の空 numactl に根拠があると裁定した。
同 D は「numactl を偽装して verify を通す」ことを規律 2 違反として却下している。

したがって、事前登録 §4 が `pegasus` 契約を pin している以上、
**この検査を満たす成果物は原理的に作れない。**

**是正方向は既裁定である。** D924 の却下した選択肢に逐語でこうある —
「env contract の値を計測側へ literal で写す — 写した時点で contract の変更に追随しなくなる。
`env_contract.lookup()` から引く。」
consumer は成果物と照合済みの `environment_contract_sha256` を既に保持しているので、
`env_contract.resolve_by_contract_sha256(...)` で契約を hash 束縛のまま解決し、
その `numactl` を要求 prefix にすればよい。

**これは検査を緩めない。** prefix を契約由来にしても、その後段の
「実行対象が configure が指定した build dir の `cc/silo/ycsb_silo.exe` と一致すること」は
そのまま発火する。`linux-baremetal` の成果物に対する挙動は 1 bit も変わらない。

### 3.2 toolchain digest を再導出できる前提になっている

consumer は `wal.build_done.toolchain` を canonical JSON 化して sha256 を取り、
`wal.build_done.toolchain_record_sha256` と一致することを要求する。

**producer はその 2 つを別の対象から作っている。**
`orchestrator/campaign/buildcache.py` の `_toolchain_manifest` は
`requested` / `realpath` / `version_first_line` の 3 key だけを持つ **identity 射影**を返す。
一方 `_tool_version_full` は `--version` の stdout + stderr 全文を `version` として別に観測し、
`_split_expected_toolchain_manifest` が両者を分けている。
`orchestrator/campaign/pipeline.py` は `toolchain_record_sha256` に
「buildcache の pre-image hash とは異なる、**full version を含む** campaign 実行証跡用 hash」を入れる、と
コメントで明示している。`orchestrator/tests/test_campaign.py` の assertion も、
`payload["toolchain"]` が 3 key であるのに対し digest は `version` を含む manifest から取ることを示している。

実成果物で裏を取った。今回の WAL の `toolchain` は
`{"requested","realpath","version_first_line"}` の 3 key だけを持ち、
`version` という key は成果物全体で **0 件**である。`result.json` にも同じ 3 key の射影しか無く、
`toolchain_record_sha256` そのものは記録されていない。

したがって **この digest は成果物からは再導出できない。** 環境に依らず、どの実成果物でも成立しない。

観測値は次のとおり。WAL 記録値 `61f756352ad21e05f3fc52d94f3249db25f23cf43ca43248a64f405183c48fbd`、
consumer の再計算値 `b3b636dcdce493f0ecb9aa343915d01c7e5f223275af16e25a66e4f6ea3446d7`。

### 3.3 欠陥境界の確定 — 腕間比較は健全である

同じ code (`toolchain-identity-mismatch`) を持つ検査のうち、
**腕間比較** (`target.wal.build_done.toolchain_record_sha256`、baseline と target の記録値が等しいこと) は
実成果物で**通る**。これは実効のある検査であり、欠陥ではない。
欠陥は腕内の再導出 (`wal.build_done.toolchain_record_sha256`) だけである。

この境界は、腕内の再導出だけを無効化した偵察で確定した (腕間比較は生かしたまま受理に到達した)。

### 3.4 根本原因は F622 と同型である

2 系統とも、述語を合成 fixture に対してだけ検証し、守る現物と接続しなかったことによる。
`orchestrator/tests/test_t1998_stock_inline_pair.py` の fixture は
`run_cmd = ["numactl", "--interleave=all", …]` を合成し、toolchain digest も自己整合に作る。
実 producer の成果物へ通した試行は、本 wave が初めてである。

F622 との違いは**恒真の向き**だけである。F622 は「決して赤にならない gate」、本件は
「決して緑にならない gate」である。後者は、実データが手に入るまで露見せず、
露見したときには測定を 1 本消費し終えている。

## 4. 偵察の結果 (これは成果物ではない)

上記 2 系統だけを無効化すると、consumer は
`accepted` / reason `preregistered-balanced-stock-inline-pair` に到達し、
両 arm とも sample 数 5、`unstable` は両 arm とも false、`ratio` は非 null となった。
残る検査に追加の欠陥は無い。

**この偵察は repo 外の使い捨て driver で行っており、成果物でも認証結果でもない。**
認証された値は、正規に是正・レビュー・変異検査された consumer からしか出さない。

**効果量 (両 arm の sample・median・ratio・improvement_percent) は本 wave では読んでいない。**
生成した偵察 driver は、これらを出力しないよう意図的に作ってある。
未決の設計裁定 (§5) を、効果量を知らないまま下せる状態に保つためである。
生値は上記の成果物 root に保全してあり、失われていない。

## 5. ユーザー裁定へ返すもの

§3.1 の是正は D924 が既に方向を定めているので、単独で実装できる。
しかし §3.2 の是正には設計択一があり、親は裁定しない。

- **案 A: 腕内の再導出を撤去し、保証しない範囲として明記する。**
  腕間比較と `result.toolchain` との一致検査は残す。producer を変えないので今回の成果物が使える。
  同型の決着として D1876 (実害が観測されない再受理検査を exact 化せず非保証として明記) がある。
  失うのは「digest と manifest が互いに束縛されている」という保証である。
- **案 B: producer に full version manifest も記録させ、digest を検証可能にする。**
  束縛は保たれるが `pipeline.py` を変えるため全 campaign の WAL bytes が動き、
  今回の成果物は要件を満たさなくなるので**再測定が要る**。
- **案 C: producer が hash する対象を identity 射影へ揃える。**
  同じく producer 変更と再測定が要る。加えて pipeline のコメントが意図的だと述べている
  「full version を含む証跡用 hash」という区別を失う。

親の推奨は **案 A** である。撤去対象は実成果物で一度も成立したことがない述語であり、
事前登録 §6 が列挙する判定規則 (workload、2 点だけを読むこと、sample 5、median、
`ratio`、`unstable` なら `inconclusive`、事後 argmax の禁止) のいずれにも属さない。
つまり**事前登録された受理条件は 1 つも動かない。**

**それでも親は実装しない。** 検査を 1 行外せば自分の計測が読めるようになる、という圧力が
現に掛かっている場面であり、絶対規律 2 が想定しているのはまさにこの状況である。
受理集合を変える判断は、圧力の外にいる主体が下すべきものと判断した。

## 6. 本記録が閉じないもの

- **balanced の対の効果量。** 認証経路からはまだ 1 つも出ていない。§5 の裁定待ちである。
- **事前登録の版。** 本 wave は事前登録の bytes を 1 byte も変えていない。
  consumer を是正しても 2 つの sha 定数は動かないので、v1 のままで有効である。
- **2026-09-07 の生値。** D1874 に従い主張へ転用していない。本記録にも数値を書いていない。
- **compiler の同一性。** 事前登録 §9 の但し書きはそのまま残る。
  今回は `source-identity-unbound` に落ちていないので、計算ノードの `g++` が
  事前登録の arm 別 source digest を再現したことは実測されたが、これは 1 回の観測である。
- **write-heavy と read-heavy。** 事前登録の対象外であり、本 wave も測っていない。

## 7. 追補 (2026-09-14、[T-2589] の敵対レビューによる訂正)

本文の記述 2 箇所が言い過ぎだった。**削除せず、ここで訂正する。**

- **§3.2 の「全文は成果物に無い」の射程。** `orchestrator/campaign/buildcache.py` の
  completion manifest は `complete_toolchain_manifest` とその sha256 を実際に保存している。
  持たないのは **T-1998 consumer が読む回収済み成果物**
  (result.json、reservation.json、campaign の lock と WAL) の側だけである。
  親が実測で確認した — 回収成果物 23 file に `complete_toolchain_manifest` は 0 件。
  したがって「この consumer は digest を再導出できない」という結論は変わらないが、
  「全文はどこにも無い」と読める書き方は誤りだった。
- **§4 の「残る検査に追加の欠陥は無い」。** 1 成果物の受理からは導けない。
  言えるのは**この成果物では追加の拒否に遭遇しなかった**ことだけである。

是正の実施と認証された結果は
`output/insights/2026-09-14_t2589-consumer-real-artifact-repair/README.md` にある。
