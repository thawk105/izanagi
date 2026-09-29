# 方策 loop を Pegasus で job をまたいで複数 iteration 回せるようにした — pair を iteration ごとの計測 campaign で測り、本番入口の pair job 2 本を同じ系列で連続して通した (2026-09-28〜29、[T-2871])

- 位置づけ: [T-2865] (`output/insights/2026-09-27/t2865-silo-policy-iter2/README.md` §3.4、D2274) で、Pegasus の one-shot claim のために方策 loop の 2 本目の pair job が build 前に `ClaimError` で止まった問題を、claim leaf と one-shot 性を変えずに driver 側で解いた記録。手順の正本は `docs/phase3-silo-policy-runbook.md`、設計判断は同じ wave の decisions fragment。可変状態の正本 (worklog 末尾) にはしない。
- wave: branch `worktree-dev-wave-t2871-policy-loop-iter`、起点 local main `51f896352` (開始 gate rc=0、2026-09-28 07:58 JST)。Pegasus の保守 (9/28 09:00〜21:00) で段 6 の途中から中断し、9/29 02:27 JST に再開した (resume gate rc=0)。
- 逐語 (`verbatim/`): 依頼 `request.md`、段 1 brief `s1-brief.md`、段 2 plan `codex-plan-a.md`・`codex-plan-b.md`、段 3 相談 `codex-consult-a.md`・`codex-consult-b.md`、段 4 裁定 `s4-ruling.md`、段 5 実装子 `codex-author.md`、段 6 のレビュー `codex-review-a.md`・`codex-review-b.md`・焦点再レビュー `codex-rereview.md`、段 6 裁定 `s6-ruling-1.md`〜`s6-ruling-6.md`、fix 子 `codex-fix1.md`〜`codex-fix5.md`、生死確認の形の相談 `liveness-decision-context.md`・`codex-decide-a.md`・`codex-decide-b.md`・裁定 `liveness-decision.md`。変異の spec と結果は `mutation/`。codex の prompt と受領証は wave の job dir (repo 外、`/work/SFC/tanab/tmp/t2871-policy-loop-iter-20260928/`)、生死確認の script と evidence は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2871-policy-loop-iter/`。

## 0. 要約

1. **段 1 の新事実:** claim を解くだけでは足りない。同じ campaign の WAL で終端済みの variant は次の run で skip される (retryable abort を除く、`loop.py` のリカバリ skip) ので、2 本目の pair を同じ loop campaign で測ると、stock (variant `db4764543546` は毎回同じ) が skip されて同じ job の対照が付かない。
2. **先例の実測:** backoff 軸の K2 (T-2795) は job ごとに新しい空の submit checkout (= 別 out_root) で同じ identity を通していた (`dev-wave-t2795-k2-pair-resubmit/setup-submit-trees.sh:5`「out_root を分けるのは同 identity の one-shot claim と同 campaign の stock skip を避けるため」)。各 tree の loop_state は iteration=1 のままで、確認した K2・B-5 (T-2797)・T-2849・T-2850・方策系列 A/B はいずれも loop 状態を job をまたいで継続していない。B-5 系は `b5_slot` で「1 identity = 1 測定点」。
3. **設計 (段 2 の 2 plan が独立に収束、段 3 の 2 レンズで点検):** 系列 (loop) の campaign dir には `loop_state.json`・`policy_history.jsonl`・critic digest だけを置き、pair の候補と stock は系列の identity に `policy_iteration` (系列の次の番号、driver が loop_state から決める) を足した**計測 campaign** で測る。claim は iteration ごとに 1 本で one-shot のまま、同じ計測 identity の再使用は従来どおり `ClaimError`。stock skip も同時に解ける。counter は計測より前に保存し、claim 取得後の強制終了は欠番になる (次の job は次の番号で進み、系列が claim に止められ続けない)。履歴行と stdout に `measurement_campaign_id`。
4. **結合検査:** driver `main` を別 process で直列に起動し、実 `_authorize_measurement`・実 `acquire_claim`・実 `check_reservation`・実 `authorization_session`・実 admission・実 auditor gate を通す 3 本 (2 本連続・強制終了・同じ identity の再使用)。焦点走 6 回目 (計算ノード `33701.nqsv`) で 393 passed。
5. **変異:** 5 / 5 KILLED (dispatch final、baseline PASSED)。
6. **計算ノードの生死確認 (本番入口 = job body):** 新しい submit checkout で t2865 の auditor 通過済み proposal 2 本を pair job として直列に流し、2 本とも候補 certified・同じ job の stock `certified-stock`・別の claim・系列 iteration 1 → 2 を確かめた。

## 1. 依頼と裁定

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = `verbatim/request.md`): claim leaf と one-shot 性を変えず、claim を手で退避する運用も採らず、driver 側で解く。段 2・3 は 2 レンズ。段 1 で backoff 軸 loop の Pegasus 系列を実測して先例にする。結合検査は実 `_authorize_measurement`・実 `acquire_claim` を 2 process で通す形を含める。計算ノードの生死確認の形は段 1 で決める。実装は Codex author、正しさゲートは緩めない。検査込み 2 node 時間以上ならユーザー確認。仮想リスク向けの gate・検査・台帳・一般化は scope 外。
- 段 4 の主な裁定 (`verbatim/s4-ruling.md`): 上の §0 項 3 の設計。K2 型 (job ごとに別 out_root) は系列状態の出所が tree をまたぐため、B-5 型は pair を 1 測定点と定義すれば同型になるため退けた。critic digest の材料は当該 iteration の計測 campaign の admitted WAL (候補の評価後・stock の前) になり、過去の iteration と login の record-reject は digest に入らない (系列全体は coder が `self_history` で見る)。これは受け入れて runbook §1(g) に明記した。
- 受理単位の変更: Pegasus の one-shot claim の単位が「loop 系列に 1 本」から「系列の iteration に 1 本」へ移る。claim leaf (`campaign_claim.py`) の bytes と同じ path の `O_EXCL` 拒否は不変。

## 2. 実装 (commit)

| commit | 内容 | 作者 |
|---|---|---|
| `14beca40c` | pair の計測 cfg / layout の分離、counter の計測前保存、`measurement_campaign_id`、結合検査 T1〜T3 | Codex author (段 5) |
| `b6c824675` | runbook §1(0)(f)(g)・§3 | 親 (docs) |
| `571dadd4b` | fix-1: T1 の digest を stock 前の時点で検査、`stopped-before` の stdout に計測 id を載せない (段 6 レビュー A・B) | Codex fix |
| `d95c893ce` | runbook: 系列 dir の中身、digest と checkpoint の置き場、欠番の数え方 (段 6 レビュー B) | 親 (docs) |
| `40b3d09fd` | fix-2: 結合検査の子 process に `orchestrator/tests` を通す、layout 作成箇所を既存 helper に寄せる (namespace inventory の pin は不変) | Codex fix |
| `13d0e0913` | fix-3: 結合検査の代役を方策 driver の 1 checkout の流れに合わせる | Codex fix |
| `d7161a2a1` | fix-4: 代役を評価ごとの模擬 pipeline・process ごとの新 checkout・patch の巻き戻しに合わせる | Codex fix |
| `9c6e34c80` | fix-5: 結合検査の子 Python process を `-B` で起動する (受入 1 回目の赤) | Codex fix |

run_campaign の呼出しは 2 本のまま (test_campaign.py の棚卸し pin)。loop.py・campaign_claim.py・p3_s4_loop.py・job body は不変 (前 3 つは contract loader 閉包の member)。

## 3. 段 6 の経過

- レビュー A (正しさ) は重大な不一致なし・should 3 件、B (過剰・削除) は must-fix 1 件 (T1 の digest 期待値を stock 後の view から作っていた) と runbook の誤り。fix-1 と親の docs で閉じた。コンパイラ不在時の skip (A should) は同じ file の既存 test 9 箇所と同じ慣習なので変えず、焦点走の skip 内訳で T1〜T3 が実行されたことを確かめた (skip 0)。
- 焦点走の赤 (すべて本 wave の test の代役・配線に帰属、正しさ判定の赤ではない):
  - 3 回目 (`33653.nqsv`): 子 process が `skiputil` を import できない (pytest 下でだけ import 経路に入る)、namespace inventory の `exploration_campaign_layout` 呼出し箇所 pin 2 → 3。→ fix-2。
  - 4 回目 (`33662.nqsv`): stock の評価が `admission-error (source evidence は stock/review/generator/coder のどれも支持しない)`。方策 driver は 1 つの checkout で候補 → stock を評価するが、代役は backoff の 2 checkout 手本を写し、root で STOCK を判定していた。**実 admission は正しく拒否していた。** → fix-3。
  - 5 回目 (`33689.nqsv`): 同じ checkout の 2 評価目で模擬 bench の台本が尽きる、強制終了した候補の書込みが残り 2 本目で**実 auditor gate が digest 不一致を正しく拒否**。production の `patchharness.checkout` は process ごとに新しい隔離 worktree、`applied` は抜けるときに source を戻す。→ fix-4。
  - 6 回目 (`33701.nqsv`): 393 passed。
- 焦点再レビュー (`verbatim/codex-rereview.md`): R1〜R14 は不採用の 2 件を除き closed、代役は実物の機構を通る。新所見「T1 は系列 digest が 2 本目の計測 WAL 由来か 1 本目由来かを弁別できない」は、digest の材料が同じ pair の `evaluation_layout` から来て前 iteration を読む経路が無いため、仮想欠陥として scope 外 (`verbatim/s6-ruling-5.md`)。
- 1 回目・2 回目の焦点走 (`32588`・`32592`) は保守前後の待ち行列で queue-wait の打ち切り (rc=16、child 未起動)。

## 4. 変異 matrix (段 4 の事前登録、M5 は段 6 裁定 1 R7 で赤の理由を再照準)

| id | 壊す箇所 (`p3_s4_loop_policy.py`) | 赤になった node (final) | final |
|---|---|---|---|
| M1 | pair の計測 cfg に `policy_iteration` を足さない | T1・T2・T3 と既存 pair test 2 本 (5 node) | KILLED |
| M2 | counter の計測前保存を外す | T2 (強制終了) だけ (1 node) | KILLED |
| M3 | `_stock_result` に系列 layout を渡す | T1・T2・T3 (3 node) | KILLED |
| M4 | 成功時の履歴を計測 layout に書く | T1・T2 (2 node) | KILLED |
| M5 | critic digest の admitted view を系列 layout にする | T1・T2・T3 (3 node) | KILLED |

- 判定は `tools/mutation_worktree.py` の dispatch final だけ (`mutation/final-results.json`、summary KILLED 5 / matching 5、baseline PASSED)。source は wave tip の独立 clone (`d7161a2a1`)。
- **手順の逸脱 (記録):** 期待 node の収集 (probe) は、dispatch probe が混雑で 2 回とも中止した (1 回目は baseline が queue-wait 3,600 s で rc=16 → PARSE_ERROR、`--resume` は baseline を再走しないので回復不能。2 回目は runner の dispatch 強制を外しても harness が collection を dispatch へ回し 900 s で打ち切り) ため、login で実 pytest (`tools/run_tests.py` の自動判定) を使い、clone に 1 本ずつ注入 → 走行 → 元 bytes へ戻して sha256 と `git status` 空を照合する使い捨て script (repo 外、sha256 `f4ce394f…`) で行った (`mutation/login-probe-results.json`)。DW-M08 の login 自走は pytest fixture 依存の file を除外するが、これは実 pytest なので fixture 依存の問題は無い。KILLED の判定手順は変えていない。
- login の実 pytest は、`/tmp` の他ユーザーの空 `.git` のために `/tmp` 下の tmp_path が「repository 内」と判定され、結合検査 3 本が偽赤になった (F763 と同型)。`--basetemp` を job dir 下に置いて解いた。

## 5. 計算ノードの生死確認 (liveness 専用系列)

- submit checkout `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2871-policy-loop-iter/trees/live` (HEAD `d7161a2a1`、骨格 patch SHA-256 `9cb545520fe6d27a852ccb406f321924ee61d17ff86bf1b74eeafc54b9db2904` = 系列 B と同じ、locked)。段 4 §6 は「受入済みの tip から」だったが、受入は記録 commit 後の最終 tip で行う決まり (DW-O12) なので、実装が確定した `d7161a2a1` (以後は docs だけ) から作った。
- proposal: t2865 の `verbatim/llm/prop-2.json` (系列 B の iteration 2 の候補) と `prop-3.json` (critic の推奨 A の切り分け候補)。bytes は insight の原本と sha256 一致。login の preview で digest が auditor の審査対象と一致 (`b0171a7d…`・`37a17d1d…`)。LLM は呼んでいない。**研究系列ではなく、値は系列 A・B と合算しない。**
- 投入: 1 本目 `33730.nqsv` (prop-2)、2 本目 `33800.nqsv` (prop-3) は `qsub --after 33730.nqsv` で直列を scheduler に保証させた。待ち行列が混んでいた (実行中 23・待ち 67) ため、系列の walltime 予算 (3,600 s、待ちを含む) で 2 本目が `stopped-before` になる見込みがあり、生死確認の形を codex の 2 立場で相談して A (本番入口の 2 job を待つ) を採った (`verbatim/liveness-decision.md`、ユーザー就寝中のためマネージャー指示に従い codex と決定)。手当てとして 2 本の要求 walltime を 1,800 s に下げ、2 本目の優先度を `qalter -p 10` で上げた。
- 結果 (現物で突き合わせた):

| job | 開始 | Elapse | 系列 iteration | 計測 campaign | 候補 | 同じ job の stock | claim |
|---|---|---|---|---|---|---|---|
| `33730.nqsv` | 05:51:20 | 793 s | 1 | `…-c4efe427` | `145e3d73315a` certified、中央値 4,396,363 txn/s、abort 18.53% | `db4764543546` certified-stock、1,361,537 txn/s、abort 12.15% | bnode026 |
| `33800.nqsv` | 06:27:06 | 741 s | 2 | `…-4e8009c5` | `ae2c702b179e` certified、中央値 1,931,227 txn/s、abort 55.41% | `db4764543546` certified-stock、1,371,084 txn/s、abort 12.61% | bnode081 |

  - 系列 dir (`…-877344a7`): `loop_state.json` の iteration = 2 (系列開始 05:51:47)、`policy_history.jsonl` 2 行で各行の `measurement_campaign_id` が上の計測 campaign と一致。claim は `output/env/pegasus/claims/` に別名の 2 file。各計測 dir の WAL に候補 (非 STOCK の src_token) と stock (`src_token = stock`) の BUILD_START と BENCH_DONE。
  - 2 本目は系列開始から約 36 分後に始まり、予算内だった。
- 観測 (1 回ずつ、性能主張ではない): prop-2 の同じ job の比 3.23 は系列 B の 3.19 に近い。prop-3 (critic の推奨 A「abort 後の待ちを 0 に」) は比 1.41 で abort 率 55% に上がり、critic の第一仮説「待ちが短いことが効いた」とは逆向きの観測になった。
- trace 保全先 `/work/1/SFC/tanab/izanagi-repro-archive/t2871-liveness-20260929/`。

## 6. 計算ノードの使用 (job Elapse / runner の報告)

| 用途 | request | 所要 |
|---|---|---|
| 焦点走 3〜6 回目 | 33653・33662・33689・33701 | 44・42・43・40 s |
| 焦点走 1・2 回目 | 32588・32592 | child 未起動 (queue-wait 打ち切り) |
| 変異 final (baseline + 5 本) | dispatch | 68 + 33 + 152 + 33 + 55 + 38 s (harness の各走行の報告、待ち行列込み) |
| 変異 probe 1・2 回目 | dispatch | 未起動で中止 |
| pair 2 本 | 33730・33800 | 793・741 s |

受入を除く合計は約 2,080 s (約 0.58 node 時間)。段 1 の見積り (約 1.03 node 時間) の内側で、2 node 時間の線を下回る。受入は §7。

## 7. 受入

- 1 回目 (tip `71f249116`、post-claim merge `8a54cbd27` で local main `f6772df03` を取り込み): `1 failed, 27899 passed, 74 skipped`。赤は `orchestrator/tests/test_check_subprocess_bytecode_guard.py::test_real_repo_clean` の 1 件で、repo 全体の bytecode guard 検査器 (`tools/check_subprocess_bytecode_guard.py`) が本 wave の結合検査の子 process 起動 (`test_p3_s4_loop_policy.py:822`、`-B` も env の guard も無い) を検出した。**本 wave に帰属** (login で検査器を直接走らせて同じ指摘 1 件を再現)。fix-5 (`9c6e34c80`) で `-B` を付け、検査器 rc=0、焦点 2 file 40 passed を login で確かめた (`verbatim/s6-ruling-6.md`)。変異の置換対象は production file だけなので、final の KILLED はこの変更の影響を受けない。
- 2 回目: 記録時点では未実施 (fix-5 と本記録を含む tip で投入する)。

## 8. scope 外と次の一手

- **系列の walltime 予算が待ち行列の時間を含む:** `MAX_WALLTIME_S = 3600` は loop_state の作成 (1 本目の job の driver 起動) から数えるので、混雑した Pegasus では driver が claim を解いても 2 本目以降が予算で `stopped-before` になりうる。本 wave は `qsub --after` と優先度の引き上げで 36 分以内に 2 本目を始められたが、保証ではない。予算の数え方は D2256 項 3 に関わるので別 task として起票する。
- 研究系列 (LLM の coder・auditor・critic を回す新系列) を複数 iteration 回すことが次の研究前進。単価は pair 741〜793 s。
- critic digest が 1 本目・2 本目の計測 WAL を弁別できない検査の弱さ (段 6 裁定 5) は、コード経路が無い仮想欠陥として実装していない。
- 同じ系列への並行投入 (番号予約)・強制終了した番号の再測定契約・系列全体の admitted digest の再構成・生成器対照の系列制御は、段 4 で scope 外とした。
