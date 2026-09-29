# silo-function-policy 軸の研究系列 C — LLM の coder・auditor・critic を回し、評価済み 3 iteration (すべて certified) と拒否 1 件で walltime 予算まで走った (2026-09-29、[T-2865])

- 位置づけ: [T-2865] の研究系列 (軸 silo-function-policy、D2214、段階 F = D2270)。[T-2871] (D2281、`output/insights/2026-09-29/t2871-policy-loop-iter/README.md`) で pair を iteration ごとの計測 campaign で測れるようになった後、LLM を回す研究系列として初めて評価済み iteration を複数得た記録。系列 A・B (`output/insights/2026-09-27/t2865-silo-policy-iter2/README.md`) と T-2871 の liveness 専用系列は別系列で、値を合算しない。手順の正本は `docs/phase3-silo-policy-runbook.md`。可変状態の正本 (worklog 末尾) にはしない。
- wave: branch `dev-wave-t2865-series-c`、起点 local main `1887f56e4` (開始 gate rc=0、`--mode fresh --external-handoff`)。コード変更なし (段 4 で「実装しない」、4→7→8→9)。
- 逐語 (`verbatim/`): 依頼 `request.md`、段 1 brief `s1-brief.md`、段 3 相談の prompt `s3-consult-prompt.md` と出力 `s3-consult.md`、段 4 裁定 `s4-ruling.md`、job の状態遷移 `qstate.log`、停止判定 `stop-check.log`、記録時に読み取り専用で再実行した系列の照合 `verify-series.log` と auditor gate の読み直し `auditor-gate-recheck.log`。記録の read-only review `s7-review.md` (NO-GO、must-fix 3) と焦点再レビュー `s7-focus-1.md`・`s7-focus-2.md` (2 巡目で残った「`--after` を渡した」という断定 1 点は、上限 3 巡に達したので親が real と裁定し、断定を削って閉じた)。LLM の入出力は `verbatim/llm/` (coder 入力 `coder-input-N.json` = driver の emit 出力そのもの、coder 返却 `coder-N.raw.json`、preview `preview-N.json`、拒否記録 `record-reject-1.json`、auditor prompt `auditor-prompt-N.md` と返却 `auditor-output-N.json`、確定 proposal `prop-N.json`、critic prompt `critic-prompt-N.md` と返却 `critic-output-N.md` (行頭の 2 字下げを外したもの))。
- 親専用の運用 script と job の evidence は repo 外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-series-c/` (`make-submit-tree.sh`・`submit-policy.sh`・`release-policy.sh`・`login-driver.sh`・`make-auditor-prompt.py`・`make-critic-prompt.py`・`verify-series.py`・`stop-check.py`・`qstate-log.sh`・`wait-job.sh`、`evidence/<attempt>/`)。trace 保全先 `/work/1/SFC/tanab/izanagi-repro-archive/t2865-series-c-20260929/` (stock 344 MB、pair 947 MB・925 MB・1.1 GB)。

## 0. 要約

1. 新しい submit checkout で bootstrap stock を測り、系列 C を 4 iteration 回した: iteration 1 は preview の文法拒否、iteration 2・3・4 は候補 certified (serializable)・同じ job の stock `certified-stock`。4 本目の pair を始める前に walltime 予算 (3,600 秒) に達した (`budget-walltime`)。
2. LLM の閉ループが働いた: coder は self_history の拒否 (`decl.local`) を読んで iteration 2 で書き方を直し、iteration 3・4 は直前の critic の推奨 (「一度に 1 要素だけ変える」) をそれぞれ 1 要素の変更として採った。
3. 同じ job の比 (候補 ÷ stock、5 rep 中央値) は 2.17 → 1.86 → 2.64。1 候補 1 観測で、性能主張ではない。
4. 正しさ gate: 評価した 7 attempt (bootstrap stock 1、pair 3 本 × 候補・stock) の legacy verify 1 回と性能構成 verify 5 回がすべて serializable・anomaly 0 件。auditor は 3 回とも pass (違反 0)。
5. 運用: 2 本目以降の pair は前の pair の終了前に保留 (`qsub -h`) で投入し、proposal を確定・照合してから `qrls` した。保留を外してから開始までは 37 秒・22 秒だった。`--after <前>` の指定は投入記録に残っていない (§3)。
6. 計算: job Elapse 合計 2,517 秒 (約 0.70 node 時間)。2 node 時間の線の下なので確認なしで投入した (段 1 見積り 約 0.97 node 時間)。

## 1. 依頼と裁定

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = `verbatim/request.md`): 新しい系列を 1 本起こして coder・auditor・critic を回し、複数 iteration を Pegasus で実走する。着手直前の local main から新しい detached submit checkout を作り bootstrap stock から始め、2 本目以降の pair は `qsub --after` で先に待ち行列へ入れる。auditor の出力形は runbook §1(d) の prompt 明記。iteration ごとの certified / reject・anomaly の分類・stock 比を残す。コード変更は想定しない。規律 2 は緩めない。仮想リスク向けの追加は scope 外。
- 段 3 (read-only codex 1 本、2 レンズ、`verbatim/s3-consult.md`): real 5・要実測 1。段 4 裁定 (`verbatim/s4-ruling.md`) で次を採った。
  - 停止判定は driver の開始前と結果記録後に掛かる (brief の「起動時だけ」を訂正)。起動済みの pair は最後まで評価される。
  - 保留解除の前に、preview の `passed=true`・proposal の auditor `diff_digest` と preview の digest の一致・proposal の coder と preview に掛けた coder の一致を確かめる (repo 外の親専用 script `release-policy.sh`、repo の gate ではない)。qsub / qrls の失敗で script を非 0 にする。
  - pair の成立は計測 dir の WAL・stdout の stock outcome・系列の loop_state と履歴行で確かめる (§2.3)。
  - 分類は preview 拒否 / auditor veto / AuditorGateFailure / verifier anomaly / eval-exception / stopped-before / 欠番 / certified を分ける (§2.2)。
  - 保留投入の scheduling 効果は前提にせず実測する (§3)。

## 2. 系列 C の実走

submit checkout `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-series-c/trees/c` (HEAD `1887f56e4`、CCBench `6810666` = `axis_silo_function_policy.PIN`、tracked clean、骨格 patch SHA-256 `9cb545520fe6d27a852ccb406f321924ee61d17ff86bf1b74eeafc54b9db2904` = 系列 B・liveness と同じ、locked、third-party は hydrate 済み)。形は C++ (`--form cpp`)。系列 dir `p3-silo-policy-loop-silo-policy-autonomous-877344a7`、bootstrap campaign `…-a84dd632`、計測 campaign は iteration 2・3・4 がそれぞれ `…-4e8009c5`・`…-f6ac2c7c`・`…-8a9c885c`。いずれも系列 B・liveness と同じ ID を別 checkout の別 dir に持ちうるので、ID 単独で系列を結合しない (runbook §3)。全操作をこの checkout で直列に行った。

### 2.1 経過

| iteration | 段 | 結果 |
|---|---|---|
| (0) | bootstrap stock `34230.nqsv` (Elapse 308 秒) | `certified-stock`、variant `db4764543546`、5 rep 中央値 1,368,676 txn/s、abort 12.23% |
| 1 | coder (`coder-1.raw.json`) → preview | `passed=false`、policy-grammar / `decl.local` (`LockResponse give_up{...}` の波括弧初期化の局所宣言)。auditor は呼ばず `--record-reject` (loop_state がここで作られ、予算の起点 = 10:09:25 JST) |
| 2 | coder (self_history に拒否 1 行) → preview (digest `cf34b7ab…`) → auditor pass → pair `34246.nqsv` (Elapse 706 秒) | coder は「前回は decl.local で落ちた、原因は `T name{...}` の形」と推定し、局所宣言を `T name = T{...};` に揃え、abort 後の待ち窓の上限を 31 → 15 に下げた。候補 `3e0b518a3b4e` certified |
| (g) | critic (`critic-prompt-2.md` → `critic-output-2.md`) | 帰属は「abort 後の待ちと施錠競合時の方策が同時に入っていて分離できない」。推奨 1 = 施錠競合時を即 abort に戻す切り分け、推奨 2 = 待ち窓の上限を 1 方向だけ動かす |
| 3 | coder (`--critic-output` 付き) → preview (`46ec8fdc…`) → auditor pass → pair `34247.nqsv` (Elapse 696 秒) | coder は推奨 2 を採り、待ち窓の上限だけを 15 → 7 に下げた (他は iteration 2 と同じ bytes)。候補 `c107a40f0486` certified |
| (g) | critic (`critic-output-3.md`) | 推奨 1 = 2 つの関数を分けて測る (a: 施錠競合時を即 abort、b: abort 後の待ちを stock 相当)。待ち窓の上限を超える死んだ枝だけを変える変異は避けよ |
| 4 | coder → preview (`90fa584c…`) → auditor pass → pair `34356.nqsv` (Elapse 807 秒) | coder は推奨 1(a) を採り、abort 後の待ちは iteration 3 のまま、施錠競合時の方策を常に `{abort, 0}` に戻した。候補 `7e475c2c6607` certified |
| 停止 | 読み取り専用で `check_stop` を評価 (`verbatim/stop-check.log`) | 11:10:54 JST に経過 3,689 秒 ≥ 3,600 秒で `budget-walltime`。4 本目の pair は投入していない (runbook §1(f)「残りが足りなければ投入せず、予算停止として記録する」)。critic も呼んでいない (runbook §1(g)) |

pair job の終了時の stdout の `stop_reason` は 3 本とも `continue`。driver は候補の評価直後 (同じ job の stock の前) に停止判定を掛けるので、iteration 4 の判定時刻は予算の手前だった。

### 2.2 分類 (iteration ごと)

| iteration | 分類 | 根拠 |
|---|---|---|
| 1 | preview 拒否 (policy-grammar / `decl.local`) | `record-reject-1.json`、履歴行 `outcome=rejected` |
| 2 | certified | 履歴行、stdout の `candidate.verifier_digest` (`certified: true`)、legacy verify 1 回・性能構成 verify 5 回とも serializable・anomaly 0 |
| 3 | certified | 同上 |
| 4 | certified | 同上 |

0 件だった分類: auditor veto (3 回とも pass、違反 0)、AuditorGateFailure (driver の run で拒否なし = 履歴 3 行とも certified。proposal 確定時にも同じ parser で読んだが出力は残しておらず、記録時に読み直した結果が `verbatim/auditor-gate-recheck.log`: 3 件とも pass・違反 0)、verifier anomaly、eval-exception、stopped-before (予算停止は投入前の判定で、driver の `stopped-before` 行は無い)、欠番 (系列 iteration 1〜4 に対し履歴 4 行)。stock 4 attempt (bootstrap + pair 3 本) は `certified-stock`。

### 2.3 成立の照合

親専用の `verify-series.py` (記録時の再実行の出力 = `verbatim/verify-series.log`) で、系列 dir の `loop_state.json` の iteration = 4、`policy_history.jsonl` 4 行 (iteration 1 = rejected、2〜4 = certified、pair の 3 行の `measurement_campaign_id` は上の計測 campaign と一致)、claim file 4 つ (bootstrap 1 + 計測 campaign 3、各 job の job_id と一致)、各計測 dir の WAL に候補と stock の `BENCH_DONE` があることを確かめた。

### 2.4 値 (5 rep、txn/s)

| attempt | job | 中央値 | 5 rep | abort 率 |
|---|---|---|---|---|
| stock (bootstrap) | 34230 | 1,368,676 | 1,365,562・1,368,676・1,382,571・1,370,177・1,359,726 (bootstrap campaign の WAL) | 12.23% |
| 候補 iteration 2 `3e0b518a3b4e` | 34246 | 2,988,984 | 3,054,179・2,911,232・3,025,398・2,988,984・2,963,971 | 37.72% |
| stock (同じ job) | 34246 | 1,376,465 | 1,341,828・1,376,465・1,327,499・1,378,426・1,390,370 | 12.44% |
| 候補 iteration 3 `c107a40f0486` | 34247 | 2,556,839 | 2,556,839・2,486,447・2,593,303・2,610,591・2,513,484 | 41.62% |
| stock (同じ job) | 34247 | 1,371,220 | 1,371,220・1,379,178・1,357,005・1,362,911・1,381,786 | 12.65% |
| 候補 iteration 4 `7e475c2c6607` | 34356 | 3,614,547 | 3,686,626・3,555,573・3,649,007・3,614,547・3,455,402 | 60.26% |
| stock (同じ job) | 34356 | 1,368,428 | 1,368,428・1,378,974・1,346,381・1,372,031・1,338,597 | 12.55% |

- 同じ job の比 (候補 ÷ stock の 5 rep 中央値): iteration 2 = 2.17、iteration 3 = 1.86、iteration 4 = 2.64。**1 候補 1 観測であり、性能主張ではない。** 同じ候補の再測定は無い。
- 候補の verify (legacy) の abort 率: iteration 2 = 25.42%、3 = 25.41%、4 = 26.88% (234,438 / (234,438 + 637,629))。stock の legacy verify の率は 2.67〜3.42% (bootstrap と各 pair job の stderr の legacy 行、4 回)。
- 観測の並び (1 回ずつ): abort 後の待ち窓を短くした iteration 3 は iteration 2 より低い比、施錠競合時の retry をやめた iteration 4 は iteration 3 より高い比。critic が挙げた「施錠競合時の retry が効いている」仮説とは逆向きの観測で、施錠競合時の方策が verify・bench 中に発火した証拠 (hook の計数) は v1 に無い (runbook §4)。再測定なしに帰属を断定しない。

## 3. 運用 — 保留投入と解除

- LLM を回す系列では、次の pair の proposal (coder → preview → auditor) は前の pair の critic の後にしか作れない。前の pair の終了から次の proposal の確定まで 7〜9 分かかったので (下表)、`--after` だけで先に入れると、前の pair の終了後に proposal の確定を待たず job が始まりうる (保留しない形は試していない)。そこで保留状態 (`qsub -h`) で入れ、proposal を照合してから `qrls` した (段 4 裁定 3)。`--after <前>` の指定は投入記録に残っていない: 投入 log (`submit-pair-c3.log`・`submit-pair-c4.log`) には request ID と rc だけが残り argv は無く、job 実行時の `qstat -f` (`evidence/<attempt>/allocation-qstat.stdout`) にも依存関係の欄は無い。保留と解除は解除 log (`release-pair-c3.log`・`release-pair-c4.log` の `qrls ok` 時刻と解除直後の QUE) と `verbatim/qstate.log` で確認できる (qstate.log は 10:37:35 に記録を始めたので、HLD → RUN を直接読めるのは 34356 だけで、34247 は解除後の PRR → RUN が残る)。
- 実測 (`qstate.log`、各 job の stderr の Created/Started/Ended):

| job | 投入 | 前の job の終了 | 保留解除 | 開始 | 終了 |
|---|---|---|---|---|---|
| 34246 (保留なし) | 10:16:04 | — | — | 10:16:12 | 10:27:54 |
| 34247 (保留投入) | 10:16:27 | 10:27:54 | 10:37:00 | 10:37:37 | 10:49:09 |
| 34356 (保留投入) | 10:37:23 | 10:49:09 | 10:56:15 | 10:56:37 | 11:10:00 |

- 待ち行列は gen_S で、`qstat -Q` を 2 回見た時点 (09:5x と 10:29 頃) で実行中 34・55、待ち 21・6。保留解除から開始まで 37 秒・22 秒で、この時間帯では待ち行列の待ちはほぼ無かった。保留が scheduling 上の利得 (待ち行列での順番) を生んだかは、この混み具合では弁別できない。
- 予算: 起点 10:09:25 (iteration 1 の record-reject)。iteration 1 が preview で落ちたため、最初の pair の driver 起動 (10:16 台) の前に約 7 分を消費した。評価済み 3 本目の終了は起点から約 3,635 秒。

## 4. 計算ノードの使用 (job Elapse)

| 用途 | request | Elapse |
|---|---|---|
| bootstrap stock | 34230 | 308 秒 |
| pair iteration 2 | 34246 | 706 秒 |
| pair iteration 3 | 34247 | 696 秒 |
| pair iteration 4 | 34356 | 807 秒 |

合計 2,517 秒 (約 0.70 node 時間)。段 1 の見積り (bootstrap 309 秒 + pair 最大 4 本 × 793 秒 ≈ 0.97 node 時間) の内側で、ユーザー確認の線 (2 node 時間) を下回るので確認なしで投入した。受入は本記録の commit 後に行う (未実施の欄を先に作らない)。LLM (Claude 子の wall): coder 4 回 約 113・90・75・45 秒、auditor 3 回 約 167・154・105 秒、critic 2 回 約 72・81 秒。codex: 段 3 相談 1 本、記録 review 1 本、焦点再レビュー 2 本 (いずれも gpt-6-sol・medium)。

## 5. scope 外と次の一手

- 同じ候補の再測定 (R2、runbook §3.1) をしていないので、比の並び (2.17・1.86・2.64) は候補間の差として読めない。次に系列の値を論文の主張へ使うなら、候補ごとの R2 再測定が要る。
- critic が 2 回とも「計測側への要望」として挙げた、施錠競合時の方策の発火回数・abort 要因別の件数・llc_miss_rate / ipc は取っていない (v1 に無い、runbook §4)。本 wave では実装していない。
- LLM 対 非 LLM の対照は [T-2867]、coder の固定文面 (`leakproof_context` が backoff 軸用の旧文書のまま) の改訂は [T-2870]、予算の数え方 (待ち行列を含む) は [T-2881] で、いずれも本 wave の scope 外。本系列では iteration 1 の preview 拒否で予算の時計が最初の pair の前に始まった。

## 所在の移動・撤去 (2026-09-30 追記)

本 insight が投入元として名指す `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-series-c/trees/c` は、2026-09-30 の掃除 wave で回収せずに撤去する。次の一手 (R2 再測定・新系列) は proposal file と新しい checkout を入力に取るので、この木を使わない。候補・値・ログは本文と verbatim に転記済み。
判定の根拠・木ごとの退避の所在・残る写しの一覧は `output/insights/2026-09-30/cleanup-originals-migration/README.md` を正本とする。上の本文は当時の事実として書き換えない (記録された測定・判定は撤去を理由に無効にならない、規律 7)。撤去は同 wave の land の後に行う。
