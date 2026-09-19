# [T-2790] 段 4 裁定と plan v2 (親、2026-09-19 23:55 JST)

対象 worktree (wave): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2790-t1259-scan-timeout` (branch `worktree-dev-wave-t2790-t1259-scan-timeout`、base `8fd1eecf9` = main tip)。
brief と前提実測は `/home/SFC/tanab/.claude/jobs/0a534e2c/tmp/brief.md`。裁定・規律の逐語は同 dir の `rulings-verbatim.md`。

## §1 段構成の裁定

- 軽量版 (DW-C00)。段 2 (plan) と段 3 (consult) は省く。理由: D2148 項 12 が設計方向 (fixture 局所の待機上限、production 不変、
  走査対象・拒否能力維持、120 秒は候補で実測確認) まで裁定済みで、変更面は production 1 file の keyword 引数追加 + test 側 3 file、
  親が段 1 で file:line を確定した。独立の敵対検証は段 6 のレビュー 2 本 (DW-S06-A、レンズ A = 正しさ境界・整合・実効性、
  レンズ B = 過剰・削除 + 親の実測値とその一般化 = P1 の交絡) で行う。
- (P1) real (provisional、段 6 レンズ B の攻撃対象)。F945 の主因 = 非 group 化された t1259 が xdist worker ごとに module fixture を
  再実行し同一 worktree を 42〜46 本同時走査していたこと。252e24b4f (2026-09-18 23:47 JST) 以後は 1 走査/shard・error 0/19。
  時刻・負荷との交絡は未分離と明記して記録する。
- (P2) 採用。timeout は git 呼び出しごと (production と同じ構造)。合計予算は設けない。
- (P3) 採用。fixture 定数は候補値 120.0 秒で実装する。採用値の確定は段 6 の実測 (本 wave の受入 shard-0 junit の in-situ 値 + login
  sampler の分布) で max ≤ 60 秒なら 120 秒を採用値として記録。超えたら値を変えず、分布を添えて裁定パッケージへ。
- 新 test は t1259 の test module に足さない (autouse fixture の consumer になり conftest の real-repo 2 集合・serialization golden
  3 表の更新が要る)。fixture 定数とヘルパは新しい非 test module に置き、正例 test は新 test file に置く。conftest は非接触。

## §2 実装 (Codex author、単位 U1、所有 path は §2.1)

### §2.1 所有 path (これ以外を編集しない)
1. `tools/pegasus/probes/t1259_qsub_env_delivery_probe.py` (production probe)
2. `orchestrator/tests/t1259_scan_bound.py` (新規、非 test の helper module)
3. `orchestrator/tests/test_t1259_qsub_env_delivery_probe.py` (module fixture 1 箇所だけ)
4. `orchestrator/tests/test_t1259_scan_bound.py` (新規 test file)
5. `output/scratch-t2790/scan_sampler.py` と `output/scratch-t2790/junit_scan_survey.py` (計測 script 2 本、untracked。親が実行前に
   repo 外へ退避する。commit しない)

### §2.2 production probe (`tools/pegasus/probes/t1259_qsub_env_delivery_probe.py`)
- `_run_git(repo_root, *args)` (133〜144 行) に keyword-only 引数 `git_timeout_seconds: float = 30.0` を足し、`subprocess.run(...,
  timeout=git_timeout_seconds)` にする。既定値 30.0 は現行の literal と同一 (production 不変)。
- `_repo_is_detached(repo_root)` (147〜160 行) にも同名 keyword-only 引数 (既定 30.0) を足す。
- `_repo_snapshot(repo_root)` (163〜190 行) を `_repo_snapshot(repo_root, *, git_timeout_seconds=30.0)` にし、内部の 3 回の `_run_git`
  と `_repo_is_detached` へ中継する。走査対象の argv 4 種 (`rev-parse --verify HEAD` / `status --porcelain=v1 --untracked-files=no
  --ignore-submodules=none` / `ls-files --others --exclude-standard -z` / `symbolic-ref -q HEAD`)、`GIT_OPTIONAL_LOCKS=0`、
  返り値の dict の key と値、`ProbeError` の条件、`check=True` は 1 byte も変えない。`subprocess.TimeoutExpired` を捕まえて包まない
  (junit に残る F945 署名 = 生の TimeoutExpired + git argv を維持する)。
- production の呼び出し (671 行 `before = _repo_snapshot(repository)`、839 行 `after = _repo_snapshot(repository)`) は引数を足さない =
  30.0 のまま。他の呼び出し・`DRIVER_TIMEOUT_SECONDS`・`observe()` の拒否論理は触らない。
- module 定数 `GIT_TIMEOUT_SECONDS = 30.0` を production 側に導入するかは author の裁量 (導入するなら既定値をそれで書き、literal を
  1 箇所にする)。導入しなくてもよい。

### §2.3 helper module (`orchestrator/tests/t1259_scan_bound.py`、新規)
- `FIXTURE_GIT_TIMEOUT_SECONDS: float = 120.0` (候補値。docstring に D2148 項 12 と F945 を 1 行で引き、「production の 30.0 は
  不変、この値は受入 fixture の module snapshot 1 回分にだけ効く」と書く)。
- `def fixture_repo_snapshot(repo_root: Path) -> dict[str, Any]:` = `probe._repo_snapshot(repo_root, git_timeout_seconds=
  FIXTURE_GIT_TIMEOUT_SECONDS)` を返すだけ。例外を捕まえない (fail-closed。timeout 時に代替 snapshot を返さない)。
- import は `from tools.pegasus.probes import t1259_qsub_env_delivery_probe as probe` (test module と同じ形)。
- pytest が test として拾わない名前 (`test_` で始めない)。既存の非 test helper (`orchestrator/tests/s8b_v2_freeze_fixture.py` 等) の
  先例に合わせる。

### §2.4 module fixture (`orchestrator/tests/test_t1259_qsub_env_delivery_probe.py` 73〜80 行)
- `_clean_detached_source_snapshot_template` 内の `snapshot = probe._repo_snapshot(REPO_ROOT)` (76 行) を
  `snapshot = t1259_scan_bound.fixture_repo_snapshot(REPO_ROOT)` に置き換える (import を 1 行足す)。**それ以外の行 (77〜79 の上書き、
  autouse fixture 83〜97、全 test) は 1 byte も変えない。** test 関数の追加・改名・parametrize 変更をしない (real-repo golden に
  当たる)。

### §2.5 正例 test (`orchestrator/tests/test_t1259_scan_bound.py`、新規)
- tmp git repo (`tmp_path` に `git init` + user.name/email を `-c` で与えて 1 commit、untracked 1 file) を作る。実 repo
  (`REPO_ROOT`) は読まない (real-repo inventory 登録を不要にするため)。
- spy: `probe.subprocess.run` を、kwargs を記録してから本物の `subprocess.run` へ委譲する wrapper に `monkeypatch` する (stub にしない、
  F649)。
- test 1 (production 既定): `probe._repo_snapshot(tmp_repo)` を呼び、記録された全 git 呼び出し (4 件) の `timeout` が 30.0 で、
  snapshot の `head` が tmp repo の HEAD、`untracked_paths` が作った 1 file を含むことを assert。
- test 2 (fixture 経路): `t1259_scan_bound.fixture_repo_snapshot(tmp_repo)` を呼び、4 件の `timeout` がすべて
  `FIXTURE_GIT_TIMEOUT_SECONDS` (120.0) で、production 既定と異なる (`!= 30.0`) こと、snapshot の内容が test 1 と同じ形であることを
  assert。
- test 3 (fail-closed): `probe.subprocess.run` を `subprocess.TimeoutExpired(cmd=[...], timeout=FIXTURE_GIT_TIMEOUT_SECONDS)` を
  raise する代役に差し替え、`fixture_repo_snapshot(tmp_repo)` が同じ例外型をそのまま伝播させる (包まない・代替 snapshot を返さない)
  ことを `pytest.raises(subprocess.TimeoutExpired)` で assert。
- 自走 harness: 既存 test file と同じ `_run()` / `if __name__ == "__main__":` 形式を付ける (`test_plain_runner_coverage.py::
  test_every_test_file_is_self_runnable_or_allowlisted` の判定条件 `_self_runnable()` を読んで合わせる。allowlist へ逃がさない)。
- 新 nodeid は受入 duration 台帳 (`acceptance_duration_ledger.json`) に無いと `test_acceptance_schedule_order.py::test_g5_...` が
  赤になる。台帳は親が junit を取った後に別 step (Codex fix 子が `tools/update_acceptance_duration_ledger.py --add-only <junit>`) で
  足す。author は台帳を手で編集しない。

### §2.6 計測 script 2 本 (`output/scratch-t2790/`、untracked、親が実行)
1. `scan_sampler.py` — 引数 `--worktree <abs>` `--out <jsonl>` `--interval-seconds N` `--max-samples N` `--stop-file <path>`
   `--self-tag <str>`。1 sample ごとに: ISO 時刻、`/proc/loadavg` の 3 値、leader 数 (`/proc/*/cmdline` に `dev_wave_wait.py` と
   ` acceptance` を両方含み `--self-tag` を含まない process 数)、worker 数 (`run_tests.py` を含む process 数)、そして
   `probe._run_git(worktree, ...)` を production と同じ 4 argv で順に呼び `git_timeout_seconds=600.0` で各呼び出しの wall 秒を
   `time.monotonic()` で測り、合計も記録する (`_repo_is_detached` は同じ引数で呼ぶ)。sha256 3 file の所要も別に測る。
   worktree へは 1 byte も書かない (`GIT_OPTIONAL_LOCKS=0` は probe 側が設定する)。1 行 1 JSON で追記し、`--stop-file` が現れたら終える。
2. `junit_scan_survey.py` — 引数 `--shards-root /work/1/SFC/tanab/.izanagi-acceptance-shards` `--since 'YYYY-MM-DD HH:MM'`
   `--out <md>`。各 session の `shard-*/junit.xml` から t1259 (classname に `test_t1259_qsub_env_delivery_probe`) の testcase を集め、
   regime (nodeid 末尾 `@real-repo` の有無)、走査回数の代理 (time ≥ 2.0 秒の test 数)、各走査所要 (同 time)、error 数 (右打ち切り
   30 秒) を出す。testsuite の `timestamp` と `time` で各 session の走行窓を作り、同時に走っていた他 session 数 (窓の重なり) を層に
   して p50/p90/p95/p99/max を regime 別・重なり数別に表にする。hostname も列に出す。
- どちらも標準 library だけ。実行は親。author は走らせない (sandbox は socket 不可、pytest 不可)。

## §3 変異事前登録 (DW-M01、親が段 6 で実走)

- M1 「上限を 0 にする」: `orchestrator/tests/t1259_scan_bound.py` の `FIXTURE_GIT_TIMEOUT_SECONDS = 120.0` → `0.0`。
  期待 kill: `test_t1259_scan_bound.py` の test 2 (120.0 を assert) が赤。加えて t1259 module の module fixture が
  `subprocess.TimeoutExpired` で error (焦点走で確認するが kill の権威は test 2)。赤理由は 1 つ (timeout 値)。
- M2 「走査を省く」: `fixture_repo_snapshot` が `probe._repo_snapshot` を呼ばず固定 dict (`head="0"*40`, `detached=True`,
  `tracked_status=""`, `untracked_paths=[]`, `source_sha256={}`) を返す。期待 kill: test 2 (git 呼び出し 0 件 / head 不一致) が赤、
  および t1259 module の `test_submission_source_digests_are_bound_to_runtime_bytes` 等 (source_sha256 の実 bytes 束縛) が赤。
  注: module fixture は `tracked_status`/`untracked_paths` を上書きして捨てるので、untracked 走査だけを省く変異は fixture 側では
  等価変異 (検出不能) になる。走査対象の維持は D2148 項 12 の裁定で守り、検出は `head`/`source_sha256` 経由で行う — この限界を
  insight に明記する。
- 正例 (通る側): test 1 と test 2 が緑、t1259 51 case が緑、負例 `test_job_start_requires_manifest_head_detached_and_clean_repository
  [untracked_paths-bad_value3]` が緑 (拒否能力不変)。

## §4 段 6 の実測計画 (親)

1. 焦点走: `test_t1259_scan_bound.py`、`test_t1259_qsub_env_delivery_probe.py`、`test_plain_runner_coverage.py`、
   `test_acceptance_schedule_order.py`、`test_real_repo_serialization.py` (consumer、DW-O26)。
2. 変異 M1・M2 (`tools/mutation_worktree.py --commit <統合 commit>`、spec/out は checkout 外)。
3. `junit_scan_survey.py` を 9/18 20:00 以降で実行 → 表を insight へ。
4. `scan_sampler.py` を login で wave worktree に対し 20 秒間隔で起動 → 受入投入 → 受入終了で stop → 分布。
5. 受入 1 回 (記録 commit を全部積んでから)。shard-0 junit の t1259 の in-situ 値を survey に含める。
6. 採用値の判定 (§1 P3) → insight・F945 追補 fragment に記録。

## §5 段 6 レビュー裁定 (親、2026-09-20 00:30 JST)

レビュー A (`review-a-out.md`、正しさ境界) と B (`review-b-out.md`、過剰・削除 + 親の実測の一般化) を読み、所見ごとに裁定した。
実装面 (production probe・helper・fixture・新 test) への must-fix は 0 件。fix 子は起動しない。訂正はすべて親所有の登録・記録・主張。

| # | 所見 | 裁定 | 処置 |
|---|---|---|---|
| A1 | M2 の期待 KILLED 集合は test 2 だけでなく test 3 (`pytest.raises` が DID NOT RAISE) も含む | real / must-fix | §3 を訂正: M2 = test 2 + test 3。M1 = test 2 のみ (test 3 は代役が同じ例外を送出するので生存)。赤理由は M2 で 2 つ (呼出し数 0、例外不伝播) — 変異原因は 1 つ (走査省略) と記録 |
| A2, A4, A5 | production 不変・spy 妥当・inventory 不要 | refuted (親の主張を支持) | 記録のみ |
| A3, B8 | 「拒否能力維持」は実 repo の dirty 検出の実証ではない。fixture は `detached`・`tracked_status`・`untracked_paths` を上書きし、実値が残るのは `head` と `source_sha256` | real / should | insight と F945 追補に限界として明記。「走査 argv と取得処理を維持」とだけ主張する |
| A6 | G5 (90% 被覆) は新 3 node 未登録でも赤と断定できない | real / should | 焦点走 2 で `test_acceptance_schedule_order.py` は緑 = 台帳登録は不要と実測で確定。adjudication §2.5 の「無いと赤」を撤回 |
| A7, B4 | 120 秒は呼び出しごとの上限で snapshot 全体の上限ではない (和は 480 秒 + hash)。245 秒は lock 取得待ちの期限で snapshot を打ち切る期限ではない | real / must-fix (記録) | brief の「120 < 245」比較と「1 走査が採用値を超えれば再発」を撤回。insight は呼び出し単位と全体所要を分けて書く |
| B1 | P1 は機序の支持から因果の確定へ飛躍。「42〜46 本同時」「主因を分離した」は未証明 | real / must-fix (記録) | 主張を「grouping 後の改善を観測し、shard 内の重複走査 (≥2 秒の testcase 42〜46 件 = fixture 実行 42〜46 回) の削減が寄与したと示唆」に限定。同時数・時刻・host・共有 FS 負荷の交絡は未分離と書く |
| B2 | 母集団の不一致 (親の前提実測 14 走/567/59 と集計器の 18 走/713/87)。後 regime max 24.494 秒の session は overlap=0 | real / must-fix (記録) | 権威は Codex 作 `junit_scan_survey.py` の出力 (対象 session 一覧・抽出時点を insight に固定)。親の前提実測は「段 1 の使い捨て集計 (top-level junit の存在で絞った 14 走)」と注記し、値を主張に使わない。「前 regime 並走時」の説明を撤回 |
| B3 | error 件数を独立の右打ち切り走査と数えるのは誤り (fixture 例外 cache の再掲 13 件が 2 秒未満) | real / must-fix (記録) | 「setup error 件数」と書き、独立した打ち切り走査数は「time ≥ 30 秒の error 件数」を別に数えて示す (集計器の再走で確認) |
| B5 | P3 の規則 (max ≤ 60 → 120) は 120 を一意に導かない | real / must-fix (記録) | 採用値は D2148 項 12 の候補 120 を「観測した呼び出し別 max の 2 倍以上の余裕 + 真の hang の検出遅延 (+90 秒/呼び出し) を受け入れる設計判断」として記録し、60/90/120/180 の比較表を添える。測定単位を明記: (a) in-situ = 受入 shard-0 junit の t1259 の最大 testcase time (4 呼び出し + hash + test 本体の上限)、(b) sampler = login からの呼び出し別 wall。混雑条件を捉えていなければ候補のままとする |
| B6 | 「≥2 秒 = fixture 実行回数」を再発判定へ昇格させない | real / should | F945 追補から二分判定を削除。補助指標 (接尾・worker 配置・traceback) と併記 |
| B7 | sampler は別 host の能動測定。20 秒周期では自走査が 34〜54% を占める | real / should | 間隔を 60 秒へ。sampler の値は計算ノード側へ外挿しない・自走査の競合と cache warming は未評価と明記 |
| B9 | helper + 新 test file は過剰 | refuted | 維持 |
| B 不足 | fixture 固有の所要・実行識別の記録が無い | real / nit | 本 wave は実装しない (scope)。「実行回数・呼出し別所要は in-situ では未計測、testcase time を代理」と明記し、次の一手候補として insight に置く |

### §5.1 変異事前登録 (訂正版、DW-M01)
- runner 対象 = `orchestrator/tests/test_t1259_scan_bound.py` のみ (t1259 module は parametrize id に改行を含み node 一致が壊れるため harness 対象にしない)。
- M0 (positive、等価): helper の docstring 末尾の句点位置を変える → SURVIVED、expected_nodes 空。harness の正例。
- M1 (negative): `FIXTURE_GIT_TIMEOUT_SECONDS: float = 120.0` → `0.0` → KILLED、expected = `test_fixture_snapshot_uses_local_candidate_bound` のみ。
- M2 (negative): `fixture_repo_snapshot` が固定 dict を返す → KILLED、expected = `test_fixture_snapshot_uses_local_candidate_bound` + `test_fixture_snapshot_propagates_timeout`。
- 補助 (DW-O19、harness 外): 統合 commit 後の clean tree で helper を M2 形へ一時変異し、t1259 module の焦点走で赤になる node を観測して復元する。fixture の実走査が `head` / `source_sha256` 経由で検査力を持つことの実測。expected は事前に固定せず「観測」として記録する (完全集合を事前確定できないため kill には数えない)。
