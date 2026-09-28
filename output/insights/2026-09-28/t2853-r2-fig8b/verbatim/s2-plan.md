# T-2853 R2 fig8b 実行プラン

対象は **R2 の独立した 2 group、各 3 job**。原 cohort の成果物は読み取り専用とし、R2 の 2 group も互いに合成しない。以下は静的検査に基づく手順であり、この段では checkout 作成、投入、テスト、描画を実行していない。

## 1. 投入前に login で鎖を全部検査する

両 group について、`8737cacb4bd286eb3e0784d16dba6eb85e5d6eab` の **別々の detached submit-tree** を用意する。各 checkout の repo root から投入する。`qsub` の作業 directory が job の `PBS_O_WORKDIR` になるためである（`docs/b10-backoff-static-tail-submission.md:15-17`、`tools/pegasus/b10_backoff_grid.sh:239`）。

| 検査と login 側の操作 | job／driver 側の根拠 |
|---|---|
| 各 checkout の `HEAD` が指定 commit で、tracked tree が clean であることを `git rev-parse HEAD`、`git status --porcelain` で確認する。hydrate が作る ignored staging は別に検査する。job script の working bytes と `HEAD` blob の SHA-256 も照合し、投入後から完走まで checkout を変更しない。 | job script は、投入時に渡された hash、実行中の script、`HEAD` の blob の三者一致を要求する（`b10_backoff_grid.sh:372-397`）。submit 側は script hash を receipt と `qsub -v` に記録する（`submit_b10_backoff_grid.sh:148-152,232-252`）。 |
| 事前登録 commit に **40 桁の `8737cacb4…`** を渡す。checkout に commit が存在し、`HEAD` の祖先であり、作業ツリーの `docs/b10-backoff-static-tail-preregistration.md` がその commit の blob と byte 一致することを `git cat-file`／`git show`／`cmp` で確認する。path の symlink も確認する。 | `b10_backoff_static_tail_formal.py:232-242`。submit 引数の形式は `submit_b10_backoff_grid.sh:60-65`。 |
| checkout **ごと**に repo 外の永続 third-party cache から `fetch_third_party.py hydrate` を行い、出力 JSON の `.source_root` を控える。既定 staging 内の `gflags`／`glog` が real directory、policy の pin と `HEAD` が一致し、`git status --porcelain --untracked-files=all` が空であることを確認する。cache の中身を staging の代わりに渡さない。 | `tools/pegasus/README.md:296-329`、`b10_backoff_grid.sh:499-543`。cohort 2 の初回 3 job は staging 欠落で落ちた（`output/insights/2026-09-19/b10-tail-cohort2/README.md:59-75`）。 |
| `external/ccbench` が real directory で、`git ls-tree HEAD -- external/ccbench` の gitlink が `511c9538…`、submodule の object database に当該 commit があることを `git -C external/ccbench cat-file -e '<hash>^{commit}'` で確認する。 | `b10_backoff_grid.sh:372-386,445-477`。この checkout の gitlink は `511c9538…`。formal driver は `pin.CURRENT_PIN` で stock checkout と patch を作る（`b10_backoff_static_tail_formal.py:751-753`）。 |
| **8737 版 job script の** `EXPECTED_FREEZE_TREES_SHA256=c405c742…` と、`output/s1-freeze`・`output/s8b-freeze` の全 file を path + NUL + bytes で順に hash した値を照合する。追加 file も digest に入る。 | `git show 8737cacb4:tools/pegasus/b10_backoff_grid.sh:22,580-597`。現 checkout の script は `92099c87…` なので、その値を 8737 checkout に流用しない。job は終了時にも照合する（`b10_backoff_grid.sh:643-649`）。 |
| 探索走 campaign は既存、real directory、絶対 path、安全な文字だけ、repo の内外関係と `.git` 祖先条件を満たすことを確認する。候補は cohort 2 が使った `/work/1/SFC/tanab/b10-backoff-grid-t2418-explore/b10-backoff-grid-20260908T193601Z-2540578-balanced/campaigns/t2418-backoff-static-explore-v1-silo-balanced-sweep-783ccbe8`。その campaign が admitted、lock の run kind が `t2418-explore`、`verify_done` の mode が単一であることも事前に read-only で確かめる。 | submit の path gate は `submit_b10_backoff_grid.sh:66-79,114-124`、job gate は `b10_backoff_grid.sh:240-256`、driver の実質検査は `b10_backoff_static_tail_formal.py:351-358`。候補の出所は cohort 2 の記録 `README.md:81-85`。 |
| 共通の出力親 `/work/1/SFC/tanab/b10-backoff-grid-t2853-r2-20260928/` が既存の絶対 directory、symlink でなく、repo の外かつ `.git` 祖先を持たず、安全な文字だけであることを確かめる。既存 receipt・job root・stdout・stderr と衝突しないことも確認する。 | `submit_b10_backoff_grid.sh:85-112,148-164`、job 側 `b10_backoff_grid.sh:258-269`。 |
| login で `python3.10`、`qstat`、`qsub`、`pegasusinfo`、`check_quota`、`sha256sum`、`gen_S` の ENA/ACT を確認する。計算ノードでは Python 3.10、必要 command、bnode と nodefile、予約・単独性などを job が改めて検査する。 | `submit_b10_backoff_grid.sh:126-146`、`b10_backoff_grid.sh:191-225,271-275,287-371`、formal driver `b10_backoff_static_tail_formal.py:734-740`。login では計算ノード固有の検査結果を先取りできないため、異常時は failure receipt で分類する。 |

submit script 自体には clean-tree gate と staging gate がない。従って、上の login 検査を省略すると qsub 成功後に job が失敗しうる。formal driver は測定前に探索 mode、単独性、site calibration、予約、stock pin、全 build の条件 gate を通す（`b10_backoff_static_tail_formal.py:732-761`）。正しさは trace 有効の別走で、計測は trace 無効の反復である（生成器の検査と caption、`plot_b10_static_tail_formal.py:122-151,299-307`）。

## 2. 2 group の投入と衝突回避

各 submit-tree で hydrate を完了してから、それぞれの repo root で次を **1 回ずつ**実行する（`docs/b10-backoff-static-tail-submission.md:35-53`）。

```bash
tools/pegasus/submit_b10_backoff_grid.sh \
  --run-kind t2500-tail-formal \
  --preregistration-commit 8737cacb4bd286eb3e0784d16dba6eb85e5d6eab \
  --explore-campaign /work/1/SFC/tanab/b10-backoff-grid-t2418-explore/b10-backoff-grid-20260908T193601Z-2540578-balanced/campaigns/t2418-backoff-static-explore-v1-silo-balanced-sweep-783ccbe8 \
  --output-parent /work/1/SFC/tanab/b10-backoff-grid-t2853-r2-20260928
```

**同じ checkout を 2 group で共有しない。** job ごとの `/scr` cache と CCBench worktree は `PBS_JOBID`／workload で分かれる（`b10_backoff_grid.sh:278-285,445-459`）が、checkout 側の staging、submodule の worktree 管理、作業ツリーの bytes は共有される。2 本の submit-tree にすれば group 間の変更・cleanup の干渉を避けられる。repo 外の永続 third-party **cache は read-only の hydrate 元として共有可**だが、hydrate 後の staging は checkout ごとに持つ（`tools/pegasus/README.md:298-325`）。探索 campaign は読み取り元として共通でよい。

各実行が作る `<group id>.submit.jsonl` の manifest、3 件の submitted event、nonce、request ID を保存する。submit は group ID と nonce を毎回生成し、3 job を逐次 qsub するため、一部だけ提出された場合もありうる（`submit_b10_backoff_grid.sh:148-153,166-265`）。投入直後に job root がないことだけでは失敗と判定しない（手順書 `:50-53`）。

## 3. 待機、完走、集団報告

receipt の **6 request ID** を `qstat` で追い、各 group の 3 root それぞれについて scheduler stdout／stderr、`*.failure.json`、`reservation.json`、`completion.json` を照合する。`completion.json` は 8 genome の commit と execution report が揃った後にだけ作られる（`b10_backoff_grid.sh:695-729`、手順書 `:55-64`）。3 root の `completion.json` が `status: complete` で、`run_kind`、workload、request ID、source commit、nonce が receipt と一致することを確かめる。campaign path は各 root の `campaigns/` 配下から **1 本ずつ明示**して選ぶ。

各 group について、その group の submit-tree の repo root で、手順書 §4 と同じ argv を使う（`docs/b10-backoff-static-tail-submission.md:66-85`、CLI 定義 `b10_backoff_static_tail_formal.py:777-803`）。

```bash
python3.10 -I -B orchestrator/campaign/b10_backoff_static_tail_formal.py \
  --preregistration-commit 8737cacb4bd286eb3e0784d16dba6eb85e5d6eab \
  report \
  '<そのgroupのwrite-heavy root>/campaigns/<campaign>' \
  '<そのgroupのbalanced root>/campaigns/<campaign>' \
  '<そのgroupのread-heavy root>/campaigns/<campaign>' \
  --explore-campaign /work/1/SFC/tanab/b10-backoff-grid-t2418-explore/b10-backoff-grid-20260908T193601Z-2540578-balanced/campaigns/t2418-backoff-static-explore-v1-silo-balanced-sweep-783ccbe8 \
  --output-root /work/1/SFC/tanab/b10-backoff-grid-t2853-r2-20260928/group-report-<group-id>
```

出力先は group ごとに固有とする。`t2500-backoff-static-tail-formal.json`、`.dat`、`-complete.json` は create-only で、既存 file があると拒否される（手順書 `:79-85`、driver `:645-660`）。終了コード 0 と report の `verdict`／`failures` を確認する。**invalid でも report は作られ、rc=1** なので、file の存在を合格と扱わない。

## 4. R2 の描画と対照表

生成器の bytes を保ったまま描くには、repo 外 wrapper が実行時に module を import し、少なくとも次を R2 用に差し替える必要がある。

| 差し替え対象 | 根拠と理由 |
|---|---|
| `COHORTS[1]`／`[2]` の `role`、`group_id`、`completed_jst`、`report_dir`、3 file の `pinned_sha256`、`results_document`。`GROUP_ID`、`DEFAULT_ROOT`、`REPORT_JSON`／`DAT`／`COMPLETE_JSON`、`PINNED_SHA256` も元 cohort に固定されている。 | `plot_b10_static_tail_formal.py:25-51,185-197`。両 R2 group の report を、wrapper が使う同一 measurement root の下に異なる report directory 名で参照できるようにする。 |
| `CLAIM_BOUNDARY_V2` を **COHORTS 差し替え後に再構成**し、2 group ID を合わせる。provenance の role と group ID closure もこれを検査する。 | `:66-69,525-557`。定数は import 時に元 `COHORTS` から作られるため、`COHORTS` だけを後から変えても一致しない。 |
| `_caption_v2` と `make_figure_v2` の役割表示。必要なら `NO_REREAD_WORDING`、`NOT_POOLED_WORDING` も R2 の「別 attempt、原 cohort とプールしない」に合う文言へ置換する。caption の再計算を行う closure 関数も同じ表示を参照させる。 | `:70-72,314-345,439-460,565-566`。現状は「primary result」と「independent reproduction」、cohort 1／2 と記す。R2 を原 cohort 1／2 の置換として表示してはならない。 |
| `DEFAULT_ROOT` または wrapper の明示 root、出力 prefix と provenance の再現 argv。`main` は `--reproduction-cohort 2` のとき 2 block を読む。 | `:648-678`。`build_provenance_v2` は generator path/hash と再現 command を記録する（`:525-536`）。wrapper の実際の呼び方を別途記録し、元 CLI を実行したように見せない。 |
| **固定検査の扱い**。`EXPECTED_VERDICT` と `repo_stock_pin == "511c953"` はそれぞれ `:29,204,229,555`。group 束縛は `:221,550,572-576`。R2 が想定外 verdict なら検査値を緩めて図を出さず、表に結果と拒否理由を記す。pin が異なれば P2 checkout／入力を調べ直す。 | `load_measurements` は SHA、verdict、source identity、全点・DAT・正しさを検査する（`:185-278`）。wrapper は受け入れた事実のラベルだけを変え、結果の gate は維持する。 |

wrapper の陽性対照として、元 metadata と元 3 file のままで既存 fig8b の `artist_series` が一致することを確認する。その後 R2 metadata で 2 block を描き、PNG、PDF、provenance、caption、wrapper の bytes/hash と入力 6 file の SHA-256 を insight に記録する。`_publish_outputs` は 3 出力を publish し、layout 検査を通す（`:614-645`）。固定の `SCHEMA_V2` や `GENERATOR_PATH` は元生成器の provenance として残るため、**差し替えた wrapper の内容と実行 argv も別に開示**する。

原 cohort 1／2 と R2 group 1／2 の対照表には、少なくとも以下を各 attempt・各 workload ごとに載せる。数値の出所は元および R2 の group report 3 file と job root とし、原値を R2 に混ぜない。

- group ID、日付、3 request ID、source commit、事前登録 commit／blob SHA／spec SHA、report 3 file の SHA、verdict、failures、`performance_certified`（生成器 `:198-235,273-278,314-341`）。
- 8 x 値（1000 µs の境界参照、1250～9999 µs の 7 tail 点）、各点の **5 反復**の throughput、abort／commit 整数、abort rate、平均、標本 SD、95% CI、CV（`:52-58,122-171,245-271,299-304,361-372`）。図の artist series は workload × 指標 × tail／境界参照の `x`、`y`、`ci95_half`（`:361-372`）。
- 各 workload の 6 区間の `state`、`qhat`、`qL`、`qU`、`L`、`U`、`U_flat`、declining 数と `min L`、全 18 区間の L の範囲、1250→9999 µs の throughput 比、correctness certified 件数と anomaly 件数（`:252-271,314-328,353-358`）。
- 図の条件と限定：48 thread、100 万 record、Zipf 0.9、3 秒、5 反復、CCBench pin、trace 無効計測と trace 有効正しさ検査、workload／cohort ごとに独立した y 軸、プールなし（`:330-344,376-421`）。

## 5. 失敗時の記録と再投入

失敗を **投入前 gate／qsub 部分失敗／job 起動前条件／dependency・freeze／予約・単独性／build・正しさ・CV／deadline／集団 identity・report／描画固定検査** に分け、receipt、stdout／stderr、`*.failure.json` の `stage`・`line`・最後の WAL commit、job `completion.json` の有無、group report の `failures` を保存する（`submit_b10_backoff_grid.sh:166-265`、`b10_backoff_grid.sh:32-151`、`b10_backoff_static_tail_formal.py:571-661`）。

再投入は **新しい submit 実行による新 group ID・nonce・request ID** で行い、元 request ID と失敗理由を insight に残す。元の receipt、job root、report を上書き・再利用しない。partial qsub の場合も提出済み request を特定して待機・分類する。成功した request を取消しや別 group に混ぜず、集団報告には同一 group の 3 campaign だけを渡す（submit receipt `:148-164,232-265`、driver の同一性検査 `b10_backoff_static_tail_formal.py:571-579`）。再走で総見積りが 2 node 時間以上になる場合は、brief の裁定条件に従い次の投入前に見積りを提示する。

## 総括

- P1：正しい投入経路は `submit_b10_backoff_grid.sh --run-kind t2500-tail-formal`。手順書 `docs/b10-backoff-static-tail-submission.md:35-48` と一致する。
- P2：8737 checkout は妥当な候補。`8737` の job body の freeze pin は **`c405c742…`**、現 checkout は `92099c87…`（各 script `:22`）。ただし、新しい detached checkout 2 本の staging・submodule object・freeze 実値はこの段で未確認。
- P3：submit の `qsub -v` 列挙に `IZANAGI_TRACE_ARCHIVE_ROOT` は無い（`submit_b10_backoff_grid.sh:239-252`）。この経路で trace 保全 opt-in を有効にするという前提は成立しない。
- **P4 は一部誤り。** 元生成器の `make_figure_v2`／`_caption_v2` は 2 block を「primary result／independent reproduction」、cohort 1／2 と固定表示する（`plot_b10_static_tail_formal.py:314-345,439-460`）。`COHORTS` 定数と図中の役割表示だけでなく、import 時に作る `CLAIM_BOUNDARY_V2`、caption と provenance の closure まで整合させる必要がある。`EXPECTED_VERDICT` が違う R2 結果は、brief どおり図を描かず表だけ記録する。
- P5：結果前の「別 attempt、原 cohort を置換せず、合成しない」という地位の記録は必要。投入前 commit とその時刻を receipt より前に確定し、R2 の 2 group も別々に記録する。