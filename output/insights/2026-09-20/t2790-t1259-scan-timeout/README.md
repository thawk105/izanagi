# [T-2790] t1259 受入 fixture の git 走査 timeout — fixture 局所の上限 120 秒 (採用) と、受入並列下の走査所要分布

- 作業日: 2026-09-19 23:30 〜 2026-09-20 (JST)。branch `worktree-dev-wave-t2790-t1259-scan-timeout`、base `8fd1eecf9` (開始時の main tip)。
- 実装 commit: `4208bf332dd999f98737cb468aeec0bf527de9ec` (Codex author trailer)。main 取り込み `ffd379729` (local main `ef897a0cf`)、
  受入前の前方 merge で `78b2c2690` (local main `60bbe8a65`)。
- 裁定の鎖: D1877 (2026-09-09、混雑下の完了時間を測って有界に決める) → D1936 項 43 (2026-09-10、実 repo 走査を module ごと 1 回、
  production timeout 維持) → D2148 項 12 (2026-09-18、受入用走査 fixture の待機上限を局所的に見直す設計。120 秒は候補値で実測で確かめる
  まで確定値にしない。走査対象・拒否能力を維持し production の timeout を一律に変えない)。
- 段構成: 軽量版 (DW-C00)。段 2・3 省略、段 5 Codex author 1 本、段 6 敵対レビュー 2 本 (A 正しさ境界、B 過剰・削除 + 親の実測の一般化)、
  fix 子なし (実装面の must-fix 0、記録の must-fix 6 を親が反映)。逐語は `verbatim/`。

## 0. 結論

1. **採用値 = 120 秒 (git 呼び出しごと、受入 fixture の module snapshot 1 回分にだけ効く)。** production `_run_git` の 30 秒は不変。
   根拠は §6: 接尾あり regime の受入 26 走で fixture を含む testcase time の max 24.5 秒 (本 wave の受入 9.2 秒)、login sampler の呼び出し別
   max 6.3 秒 (合計 max 11.8 秒、他 leader 1〜2 本並走)。120 秒は in-situ max の 4.9 倍、除去済みの前 regime の非打ち切り max 58.9 秒の
   2 倍を覆う。費用は真の hang の検出遅延 +90 秒/呼び出し (fixture は shard で 1 回だけ実行されるので shard 遅延の上限 +360 秒)。
2. **F945 の機序 (裁定時に未見の事実):** 252e24b4f (2026-09-18 23:47 JST、T-2780 wave) より前は t1259 の 51 case が xdist worker へ個別分散し、
   1 shard で module fixture の実走査が走ごと 42〜46 回実行されていた。以後は 1 回。setup error は前 18 走 87 件 → 後 26 走 0 件。
   これは grouping 後の改善の観測であり、時刻・host・共有 FS 負荷との交絡は未分離 (§2.1)。
3. fixture の実走査で検査力を持つのは `head` と `source_sha256` だけ (他 3 field は fixture が模擬値へ上書き)。「走査 argv と取得処理を維持した」
   は成立するが「fixture が実 repo の dirty / untracked を検出する」は成立しない (§3)。

## 1. 何を変えたか (実装、`4208bf332`、`verbatim/author-u1-patch.md`)

| file | 変更 |
|---|---|
| `tools/pegasus/probes/t1259_qsub_env_delivery_probe.py` | `_run_git` / `_repo_is_detached` / `_repo_snapshot` に keyword-only `git_timeout_seconds: float = 30.0` を足し中継。既定 30.0 は現行 literal と同一。走査 argv 4 種 (`rev-parse --verify HEAD` / `status --porcelain=v1 --untracked-files=no --ignore-submodules=none` / `ls-files --others --exclude-standard -z` / `symbolic-ref -q HEAD`)、`GIT_OPTIONAL_LOCKS=0`、`check`、返り値、`ProbeError` 条件、例外型 (`TimeoutExpired` を包まない) は不変。production の呼び出し 2 箇所 (`observe()` 内の `before` / `after`、変更後 684・852 行) は引数なし = 30.0 のまま (レビュー A2 が全 caller を列挙して確認) |
| `orchestrator/tests/t1259_scan_bound.py` (新規) | `FIXTURE_GIT_TIMEOUT_SECONDS: float = 120.0` と `fixture_repo_snapshot(root)` (= `probe._repo_snapshot(root, git_timeout_seconds=120.0)`。例外を捕まえず代替 snapshot を返さない) |
| `orchestrator/tests/test_t1259_qsub_env_delivery_probe.py` | module fixture `_clean_detached_source_snapshot_template` の 1 行を `t1259_scan_bound.fixture_repo_snapshot(REPO_ROOT)` へ (import 1 行追加)。test 関数・parametrize・上書き 3 行・autouse fixture は不変 (real-repo golden・conftest 非接触) |
| `orchestrator/tests/test_t1259_scan_bound.py` (新規) | tmp git repo + `subprocess.run` の spy (本物へ委譲) で、production 既定 30.0 (4 呼び出し) と fixture 経路 120.0 (4 呼び出し) を対で確認する正例 2 本、`TimeoutExpired` の素通し 1 本。自走 harness 付き。新 3 node は実 repo を読まないので real-repo inventory / memo / golden / duration 台帳 (G5 は緑) の更新は不要 |

**変えていないもの (D2148 項 12 の逐語どおり):** production の timeout・走査対象・`observe()` の拒否論理・conftest の memo 配置・
自動再投入 loop・門番条件値・hold 登録・untracked 走査の削減。

## 2. 受入 fixture の走査所要の分布 (一次資料 = 受入 shard の junit)

### 2.1 何を測ったか・限界

- 対象: `/work/1/SFC/tanab/.izanagi-acceptance-shards/<session>/shard-*/junit.xml` のうち session dir mtime ≥ 2026-09-18 20:00 JST で
  t1259 の testcase を含むもの (44 走 = 接尾なし 18 + 接尾あり 26)。session 一覧・走行窓・host・個別所要は `verbatim/survey-final.md`
  (Codex author 作 `junit_scan_survey.py` の出力、抽出 2026-09-20 00:50 JST 頃、script 逐語は `verbatim/junit_scan_survey.md`)。
- 代理値: t1259 の testcase `time` (setup + call + teardown)。module fixture の実走査 (git 4 呼び出し + sha256 3 file) を含む testcase は
  time ≥ 2 秒になる (接尾あり regime で fixture を含まない case の最大は 1.04 秒 — レビュー B6 が原本で確認)。
  **呼び出しごとの所要ではない** (timeout は呼び出しごと。合計が 30 秒を超えても error にならない case が接尾なし regime に 145 件ある)。
- regime: nodeid 末尾 `@real-repo` 接尾の有無。252e24b4f が t1259 の 30 関数を `REAL_REPO_PROCESS_MEMO_NODES`
  (`orchestrator/tests/conftest.py`) へ追加し、conftest の接尾除去 (`_strip_real_repo_loadgroup_suffix`) の例外にした。以前は接尾が
  剥がされ xdist の loadgroup 単位にならず worker へ個別分散していた。
- 「他 session 数」= 走行窓 (shard-0〜2 の和集合) が交差した他 session の数。ピーク同時数でも共有 FS 負荷でもない。
- error 件数は独立した打ち切り走査数ではない: module fixture の例外は pytest が cache して同 worker の後続 case へ再掲するので、error 87 件
  のうち time < 2 秒の 13 件は再掲、time ≥ 30 秒の 74 件が実 timeout (親の検算 `verbatim/error-buckets-parent-check.md`)。
- 交絡: 時刻帯・計算ノード・worktree・他ユーザーの共有 FS 負荷は未調整。**因果の分離ではない** (レビュー B1)。

### 2.2 結果 (`verbatim/survey-final.md` の表を要約)

| regime | 走 | fixture 走査 / 走 (≥2 秒 case 数) | n (非 error) | p50 (層別) | p90 | p99 | max | setup error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 接尾なし (worker ごと) | 18 | 42〜46 | 713 | 18.6〜32.2 | 27.3〜41.9 | 32.1〜57.7 | 58.9 | 87 (実 timeout 74 + 再掲 13) |
| 接尾あり (1 work unit) | 26 | 1 | 26 | 8.6〜9.0 | 8.9〜18.5 | 9.0〜23.9 | 24.5 | 0 |

- 接尾ありの 26 走は他 session 0〜2 本の重なりを含む (0 本: 5 走、1 本: 18 走、2 本: 3 走)。max 24.494 秒は 09-19 00:43 の走
  (他 session 重なり 0、bnode113)。本 wave の受入 (00:40 投入、他 leader 2、bnode009) は 9.20 秒。
- 読み: 接尾なしでは module fixture が走ごと 42〜46 回実行され (同時数は junit から復元できない)、所要は接尾ありの 1 回より系統的に長く、
  30 秒超の実 timeout は接尾なし 18 走に 74 件、接尾あり 26 走に 0 件。grouping 後の改善を観測し、shard 内の重複走査の削減が寄与した
  ことを示唆する。主因の分離・ピーク同時走査数・将来の裾は確定していない。n=26 の p99 は上位 2 点の補間で、件数・中央値・最大値・
  error 件数を主とする。
- 段 1 の親の使い捨て集計 (14 走 / 567 / 59、`brief.md`) は top-level junit の存在で母集団を絞っていたため権威にしない (レビュー B2)。

## 3. 変異 matrix (`mutation-spec.json`、`mutation-results.json`、`mutation-results.json.wrapper-receipt.json`)

独立 clone (D1009、`main=4208bf332`) の linked worktree、`tools/mutation_worktree.py --runner-mode dispatch`、runner 対象は
`orchestrator/tests/test_t1259_scan_bound.py` のみ (t1259 module は parametrize id に改行を含み node の完全一致に使えない)。

| id | category | 変異 | 期待 | 結果 | 失敗 node |
|---|---|---|---|---|---|
| m0-equivalent-import-comment | positive (等価) | import 行末に comment | SURVIVED | SURVIVED | — |
| m1-fixture-bound-zero | negative | `FIXTURE_GIT_TIMEOUT_SECONDS` 120.0 → 0.0 | KILLED | KILLED | `test_fixture_snapshot_uses_local_candidate_bound` |
| m2-fixture-skips-scan | negative | `fixture_repo_snapshot` が固定 dict を返す (走査省略) | KILLED | KILLED | 上 + `test_fixture_snapshot_propagates_timeout` |

baseline PASSED、summary KILLED 2 / SURVIVED 1 / MISMATCH 0 (期待集合と完全一致)、wrapper `shared_snapshot_matches=true`、child rc 0。
M1 の kill は定数の literal assertion (と 0 秒 timeout での `TimeoutExpired`) による — 実 git の時間切れ発生を証明しない。M2 は呼出し数 0 と
例外不伝播の 2 理由 (変異原因は 1 つ、レビュー A1 で期待集合を訂正)。

**補助 (DW-O19、harness 外、`verbatim/focus-runs.md`):** 統合 commit 後の clean tree で helper を M2 形へ一時変異し t1259 module を
焦点走 → **16 failed / 35 passed** (`test_submission_source_digests_are_bound_to_runtime_bytes` 3、manifest / projection / main 系 13)。
復元後の sha256 は HEAD と一致。module fixture は `detached` / `tracked_status` / `untracked_paths` を模擬値へ上書きするので、fixture の
実走査で検査力を持つのは `head` と `source_sha256` だけである。既存負例 `test_job_start_requires_manifest_head_detached_and_clean_repository
[untracked_paths-…]` は注入した snapshot に対する `observe()` の拒否を検査しており、本 wave で不変 (焦点走・受入で緑)。

## 4. login sampler (Codex author 作 `scan_sampler.py`、逐語 `verbatim/scan_sampler.md`、生データ `sampler-meas-1.jsonl`)

- 何か: login node から wave worktree に対し production と同じ 4 git 呼び出し (`git_timeout_seconds=600`) と sha256 3 file を順に呼び、
  呼び出しごとの wall・`/proc/loadavg`・受入 leader 数 (`dev_wave_wait.py acceptance` の process、**自 wave の leader を含む**)・
  `run_tests.py` process 数を 60 秒周期で記録する能動測定。受入計測走 (00:38:46〜00:49:41) と並走、11 sample。
- 限界: 別 host (login) からの測定で、計算ノード上の shard の fixture 所要を代替しない。自走査が共有 FS を叩く (60 秒周期で走査 5〜12 秒 →
  8〜20% を追加走査に使う)。leader / worker 数は login の process で、計算ノードの xdist worker 数ではない。cache warming は未評価。
- 結果 (login load1 5.7〜13.7、leader 2〜3 本 = 自 1 + 他 1〜2): git 合計 p50 5.0 / p90 8.3 / max 11.8 秒。呼び出し別 max: `status` 5.5、
  `ls-files --others` 6.3、`rev-parse` 0.03、`symbolic-ref` 0.02 秒。sha256 3 file の合計 < 0.01 秒。leader 2 本 (n=6) max 8.3、
  3 本 (n=5) max 11.8。試走 2 sample (00:14、load 15、leader 2、worker 12) は合計 6.8 / 10.8 秒。

## 5. in-situ (本 wave の受入計測走、`verbatim/focus-runs.md`)

25,327 passed / 69 skipped / 赤 0、child-green。shard-0 (bnode009) の t1259: fixture を含む case 1 件 = 9.20 秒、他 50 case < 2 秒、error 0。
他 session の受入 leader は投入時 2 本。この走は §2 の接尾あり 26 走に含まれる。

## 6. 採用値の判定

測定単位を分ける: (a) in-situ = 受入 shard-0 junit の t1259 の fixture を含む testcase time (4 呼び出し + hash + test 本体の上限、呼び出し別
ではない)、(b) sampler = login からの呼び出し別 wall。候補 120 秒は各 git 呼び出しの上限なので、(a) は上限側 (4 呼び出しの和 ≥ 最大の 1 呼び出し)、
(b) は直接の単位である。

| 呼び出し上限 | in-situ max 24.5 秒に対する余裕 | 除去済み前 regime の非打ち切り max 58.9 秒に対する余裕 | 真の hang の検出待ち (1 呼び出し) | 4 呼び出しの待機予算の和 | 評価 |
|---:|---:|---:|---:|---:|---|
| 60 | 2.4 倍 | 1.0 倍 (覆わない) | 60 秒 | 240 秒 | memo 配置が退行した場合を覆わない |
| 90 | 3.7 倍 | 1.5 倍 | 90 秒 | 360 秒 | 覆うが余裕 1.5 倍 |
| **120** | **4.9 倍** | **2.0 倍** | **120 秒** | **480 秒** | **採用。D2148 項 12 の候補値。退行時も 2 倍の余裕、検出遅延は +90 秒/呼び出し** |
| 180 | 7.3 倍 | 3.1 倍 | 180 秒 | 720 秒 | 今回の分布から追加費用を正当化する証拠なし |

- **採用値 120 秒。** 観測条件: 接尾あり regime の受入 26 走 (他 session 0〜2 本、bnode009〜140、2026-09-19 00:36〜2026-09-20 00:50)、
  login sampler 11 sample (load1 5.7〜13.7、leader 2〜3 本)。この条件で 1 呼び出しが 120 秒に近づいた観測は無い (最大でも合計 24.5 秒)。
  **未観測の条件 (他 session ≥ 3 本の並走、login load1 > 60、共有 FS の他ユーザー負荷の突発) では候補のまま**であり、超過が出たら値を上げず
  F945 へ再発追記して再検討する。
- 120 秒は各 git 呼び出しの上限で snapshot 全体の上限ではない (和は 480 秒 + hash)。real-repo lock の 245 秒は lock 取得待ちの期限であり、
  取得後の snapshot を打ち切らない。受入 5 分上限への収まりを保証しない (fixture は shard で 1 回だけなので hang 時の shard 遅延は最大 +360 秒)。
- 段 4 で事前に置いた規則「(a)(b) の max ≤ 60 秒なら 120 を採用」は満たした (24.5 / 11.8)。この規則は 120 を一意に導くものではなく
  (レビュー B5)、採用の根拠は上の表の余裕と費用である。

## 7. 主張の限界 (レビュー A/B から採った記録)

- production の git timeout は各呼び出し 30 秒を維持した。fixture の 120 秒は各呼び出しの上限で、snapshot 全体の上限ではない。
- 既存負例は注入した untracked snapshot の拒否を検査する。実 repo の cleanliness 出力は fixture が上書きするため、その実出力から拒否までの
  一貫した検証ではない。
- M1 の kill は候補値の literal assertion によるもので、実 git の時間切れ発生を証明しない。M2 は呼出し数検査と例外伝播検査の双方で kill。
- 部分走査省略の等価性は変異位置と観測 test に依存する。M2 の結果だけで全走査項目の必要性を実証したとは主張しない。
- tmp repo の正例と例外注入は値の中継・snapshot 内容・伝播を確認する。混雑下の採用値の妥当性は §6 の観測条件の範囲でだけ言える。
- grouping 前後の改善は観測上の関連であり、時刻・負荷・host 差を分離した因果推定ではない。「≥2 秒 case の件数」は fixture 実行回数の
  補助指標であり、再発時の原因二分に使わない (接尾・worker 配置・traceback・`TimeoutExpired` の値 30.0 / 120.0 で経路を確認する)。
- error 件数 87 は独立した打ち切り走査数ではない (fixture 例外 cache の再掲 13 件を含む)。独立の実 timeout は time ≥ 30 秒の 74 件。
- 接尾あり regime n=26 の p99 は上位 2 点の補間で、裾の安定推定ではない。
- 焦点走 2 の赤 1 件 (`test_p3_s4_loop.py::test_drive_iteration_checkpoint_survives_across_calls` の lock identity preimage 不一致、
  `test_real_repo_serialization.py` からの直接呼び出し) は本 wave の差分に到達せず単独再走で緑 = 非帰属。原因は未同定。

## 8. 受入・land

- 計測走 meas-1: child-green (§5)。最終走 (記録 commit 後、TAG final) と land の結果は worklog fragment に書く。

## 9. 次の一手の候補 (本 wave では実装しない)

- fixture 固有の所要 (呼び出し別) と実行識別 (worker、host) を junit に残す記録。現状は testcase time の代理に依存する
  (worklog fragment の新規 T)。
- 採用値を変えるときの手順: `orchestrator/tests/t1259_scan_bound.py` の定数と `test_t1259_scan_bound.py` の literal assertion を同時に
  変え、本 insight §2 と同じ集計器で再測定し、F945 へ追補する。

## 10. 逐語 (`verbatim/`)

`brief.md` / `adjudication.md` (段 4 §1〜§4、段 6 §5) / `rulings-verbatim.md` / `prompt-author-u1.md` / `author-u1-out.md` /
`author-u1-patch.md` / `prompt-review-a.md` / `review-a-out.md` / `prompt-review-b.md` / `review-b-out.md` / `survey-final.md` /
`junit_scan_survey.md` / `scan_sampler.md` / `error-buckets-parent-check.md` / `sampler-summary-parent-check.md` / `focus-runs.md`。
codex 子の receipt は job dir `artifacts/` (author: model_calls 11、cli_reported 61,660 token、wall 414.5 秒、accepted)。
