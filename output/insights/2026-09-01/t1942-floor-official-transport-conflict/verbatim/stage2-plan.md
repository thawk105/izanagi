## 前提の確認

必読 5 点はすべて読めた。コード変更・ゲート probe・pytest は実施しておらず、緑の主張はしない。

親 brief の前提は次のとおり。

- **(P1-a) は正しい。** v1/v2 は strict な互換形式として意図的に残るため、旧 job 952631 の manifest 再検証は現行 v3 collector の成否を測らない（[s8b_compiler_input.py:11-18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_compiler_input.py:11)、[同:1020-1030](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_compiler_input.py:1020)）。
- **(P1-b) は静的読解として正しい。** v3 は `fetchcontent-masstree` と `dependency-prefix` を持ち（[同:39-45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_compiler_input.py:39)）、collector の分類は [同:1301-1368](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_compiler_input.py:1301)、receipt issuer への current-root 配線は [s8b_floor_campaign.py:4325-4399](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:4325) にある。ただし未実測である。
- **(P1-c) は現行 main では誤り。** `claims/` 36 件と `consumed/` 228 件は fresh reservation の衝突述語から明示的に除外されている（[s8b_holdout_admission.py:1618-1647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:1618)）。現在の衝突対象は measurement generation claim である。
- **(P1-d) は正しい。** ただし後述の staged dependency seam と official の不整合が、現在の scope 内では閉じない。
- **(P1-e) は正しい。** 承認値は submitter・job script・CLI・private core を一続きで通るため、実装は 1 単位で行うべきである。

read-only 観測では共有 root は `/work/1/SFC/tanab/izanagi/.git/izanagi/s8b-holdout-admission-v1` で、旧 `claims=36`、旧 `consumed=228`、R33 `receipts=0` に加え、現行 `measurement-generation-claims=24`、`measurement-generation-consumed=192` だった。

## 対象 1 のプラン

G-A の緑は、leaf validator の単独成功ではなく、次の production 鎖が fresh build で receipt を返すことと定義する。

`build_cells()`（[s8b_floor_campaign.py:4459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:4459)）
→ `buildcache.build_v2()`（[buildcache.py:2857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/buildcache.py:2857)）
→ `_collect_compiler_inputs()`（[同:1395-1452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/buildcache.py:1395)）
→ `collect_compiler_input_manifest()`（[s8b_compiler_input.py:1189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_compiler_input.py:1189)）
→ build 内 live validation（[buildcache.py:2652-2705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/buildcache.py:2652)）
→ `issue_binary_admission_receipt()`（[s8b_floor_campaign.py:4377](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:4377)）
→ issuer 内の完全検証（[s8b_binary_admission.py:231-246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_binary_admission.py:231)）。

実測 probe は repo 外の
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1942-floor-gate-recheck/gate_a_probe.py`
に pytest 形で置き、空の外部 cache/output root を使う。親は次の形で計算ノードへ強制 dispatch する。

```text
python3 tools/run_tests.py --force-dispatch \
  /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1942-floor-gate-recheck/gate_a_probe.py \
  -q -s
```

probe は次を行う。

1. clean HEAD、current protocol resolver、verified freeze、active Pegasus contract/calibration、CCBench gitlink を固定・記録する。
2. 現行 freeze の `sort_best` 1 cell を選ぶ。この 1 cell で masstree 31 件と gflags/glog dependency-prefix 7 件の両クラスを通す。
3. job script と同じ pinned gflags/glog source を job-local prefix へ install し、同じ `CMAKE_PREFIX_PATH` を設定する。第三者 payload は current policy pin と Git HEAD/clean を production helper で検証し、ダミー header は使わない。
4. `prepare_fn is prepare_cell`、`build_fn is buildcache.build_v2` のまま `build_cells()` を呼ぶ。issuer の spy や validator の置換はしない。
5. 空 cache からの fresh build が返った後、receipt 内 manifest が v3、`fetchcontent-masstree=31`、`dependency-prefix=7` で、消える `.staging-*` や `/scr/0_<jobid>` の絶対 path を保存していないことを確認する。receipt の発行成功そのものを主要判定とする。
6. 同一 cache に対する 2 回目も通せるなら cache-hit 再束縛を副判定として記録するが、fresh 成功を cache-hit で代用しない。

模擬との差は明記する。

- 12 cell 全体ではなく `sort_best` 1 cell。
- cache/output、PBS job ID、gflags/glog install root は probe 固有。
- submission receipt、reservation、holdout claim、測定、result publish は通さない。
- source snapshot、CCBench pin、expected-materialization hash、third-party Git pin、compiler input bytesは実物を使う。これらの自己 hash・参照・pin を temp copy や手製 header で代用して判定してはならない。
- `build_cells` から issuer までを通すので leaf-only ではないが、`_run_campaign_core()` 全体の official 到達性を証明する probe ではない。

Pegasus calibration と job-local dependency build が必要なので login node ではなく計算ノードを使う。目安は fresh 20～45 分、cache-hit 5～15 分。floor 性能測定は行わない。

赤または検証不能なら、HEAD、protocol/freeze/contract/CCBench hash、probe bytes hash、node/job/time、選択 cell、fresh/cache-hit、manifest schema/hash/root 別件数、origin/current root、例外 chain、phase marker、CMake prefix、build completion の有無を create-only の外部記録へ残し、D926 実装・qsub・迂回を停止する。

## 対象 2 のプラン

6 項目の claim key は [s8b_holdout_admission.py:753-771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:753) の次の集合である。

- `freeze_sha256`
- `freeze_holdout_key`
- `configuration_id`
- `ccbench_pin`
- `env_tag`
- `observation_role`

`mode` と `protocol_sha256` は入らない。6 項目の canonical JSON hash が `cell_effect_digest` になる（[同:774-779](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:774)）。

旧 marker と現行 marker は分ける。

- 旧 marker は `consumed/<cell_effect_digest>-sha256(attempt_id).json`（[同:4492-4516](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:4492)、[同:4541-4546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:4541)）。
- 現行 marker は `measurement-generation-consumed/<measurement_generation_claim_digest>-sha256(attempt_id).json`（[同:4435-4489](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:4435)、[同:4531-4540](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:4531)）。
- `measurement_generation_digest` は `observation_role + campaign_run_id` から導出され（[同:782-802](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:782)）、generation claim digest はそれと cell effect digest の hash（[同:805-815](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:805)）である。

repo 外 `gate_b_probe.py` は login node 上の read-only、通常 5 秒未満でよい。`provision_shared_admission_root()` は呼ばず、既存 root を shared lock（[同:611-638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:611)）下で読む。

手順は次のとおり。

1. current protocol/freeze から production と同じ 12 cell と schedule を導出する（[s8b_floor_campaign.py:7165-7177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:7165)）。
2. prospective fresh `campaign_run_id` を `_fresh_run_id()` の書式で置き（[同:7800-7801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:7800)）、12 個の six-field key、cell effect digest、generation digest、generation claim digest、予定 claim path を再導出する。
3. `measurement-generation-claims/` の予定 12 path がすべて不存在であることを確認する。fresh の実際の衝突述語は、その path の `O_EXCL` 失敗だけである（[s8b_holdout_admission.py:1636-1647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:1636)）。
4. planned 96 attempt と retry 枠 24、計 120 marker path も candidate generation では不存在か確認する。
5. `ledger.jsonl`、`attempt-ledger.jsonl`、既存 measurement-generation claim、refreeze-disqualification marker を canonical parser で全件検査する。候補 run ID の既存 resume markerも拒否する（[同:1612-1634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:1612)）。
6. 同時稼働 floor job が無いことを `qstat` で記録し、lock 解放後の TOCTOU を残余として明記する。

旧 `claims=36` と `consumed=228` は production fresh reservation が参照しないため衝突しない。`receipts=0` は R33 用 directory（[同:114-116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_holdout_admission.py:114)）で、floor claim の可否には使われない。現行 24 claim は 2 個の pilot generation に分かれており、fresh official が異なる `campaign_run_id` を持てば同じ six-field cell effectでも claim digest は異なる。

衝突・破損時は、12 cell の digest 表、衝突 path、既存 document の schema/mode/run ID、関連 marker、ledger parse/shape エラー、共有 root の device/inode、全 directory 件数、同時 job を記録する。削除・名前変更・既存 generation の再利用・qsub は行わず、D811 どおりユーザーへ返す。

## 対象 3 のプラン

実装順は「G-A 実測 → G-B 実測 → 後述の dependency transport 衝突の解決 → D926 の 1 単位実装 → targeted tests → 親による docs」とする。

推奨する新しい名前は、zero-arity CLI を `--confirm-official-floor`、nonce env を `IZANAGI_CONFIRM_OFFICIAL_FLOOR` とする。削除済み pilot 系の `--confirm-irreversible-pilot-holdout` / `IZANAGI_CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT` は復活させない。

- [submit_floor.sh:7-69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/tools/pegasus/submit_floor.sh:7): usage、bool 初期値、引数 parser に `--confirm-official-floor` を追加する。値を取る形や mode 引数は作らない。
- [submit_floor.sh:299-315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/tools/pegasus/submit_floor.sh:299): 既存 submission nonce をそのまま承認値に使う。
- [submit_floor.sh:621-635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/tools/pegasus/submit_floor.sh:621): 通常の `IZANAGI_SUBMISSION_NONCE` に加え、確認引数がある場合だけ `IZANAGI_CONFIRM_OFFICIAL_FLOOR=$NONCE` を `qsub -v` に append する。receipt key は増やさない。
- [floor_campaign.sh:545-695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/tools/pegasus/floor_campaign.sh:545): `submit_binding` 段で、承認 env が設定済みなら非空・32 lowercase hex・submission nonce exact 一致を要求する。不一致・空文字は `write_failure(..., submit_binding, ...)` で gflags/glog build と driver より前に停止する。一致時だけ approval argv 配列へ flag を exact 1 個追加する。
- [floor_campaign.sh:1224-1234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/tools/pegasus/floor_campaign.sh:1224): base argv を `--mode official --protocol <resolved>` 固定へ変え、承認照合済みの場合だけ末尾に `--confirm-official-floor` を追加する。環境変数から mode を読む処理、wrapper argv の mode、`eval` は作らない。
- [floor_campaign.sh:1352-1405](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/tools/pegasus/floor_campaign.sh:1352): metrics guard を “official floor result”、job-result の `mode` を `"official"`、driver 非 0 の失敗文言を “official floor driver returned nonzero” へ変える。job-result schema/key 集合は据え置く。
- [s8b_floor_campaign.py:453-463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:453): `_assert_official_permitted` を exact bool の `confirm_official_floor` を要求する guard にする。official+false を拒否し、pilot+true も拒否する。
- [同:6962-7014](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:6962) と [同:7017-7092](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:7017): public wrapper と private core の双方へ default `False` の control 引数を通し、両境界で拒否する。これは測定 seam ではないため `_nondefault_campaign_seams()` へ入れない。
- [同:8177-8190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:8177) と [同:8383-8414](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:8383): parser に zero-arity flag を追加し、CLI の無条件拒否を「official は flag 必須、pilot は flag 禁止」へ置換する。確認値を `run_campaign()` へ明示転送する。

テストは次を同じ変更単位で直す。

- [test_s8b_floor_campaign.py:6148-6367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/tests/test_s8b_floor_campaign.py:6148): 無条件拒否テストを、CLI/public/core 各々の missing approval、wrong-mode approval、exact-bool、承認ありの gate 通過へ置換する。承認あり正例は後段を mock し、測定しない。
- 同ファイルの `_assert_official_permitted` monkeypatch 箇所は新署名へ追随させるか、可能なら明示 control 引数へ置換する。
- [同:6615-6640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/tests/test_s8b_floor_campaign.py:6615): control 引数を classifier の除外集合へ加える一方、18 名集合は exact 不変とする。
- [test_pegasus_floor_tools.py:2108-2150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/tests/test_pegasus_floor_tools.py:2108): fixed official argv、mode token exact 1、mode env/argv/eval 不在、承認 flag exact 0/1 を固定する。
- [同:2162-2171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/tests/test_pegasus_floor_tools.py:2162): confirm 無しでは新 env を export せず、confirm 有りだけ nonce exact 一致を export する。
- [同:3890-3994](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/tests/test_pegasus_floor_tools.py:3890): job-result、metrics guard、failure 文言を official へ更新する。
- 承認 env の unset・空・不一致・ambient stale 値は build/driver sentinel が発火しない負例を置く。一致だけ driver argv に flag 1 個を運ぶ。
- [test_floor_submit_receipt.py:208-244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/tests/test_floor_submit_receipt.py:208)、[certified_writer_fixtures.py:86-150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/tests/certified_writer_fixtures.py:86)、`test_campaign.py` の `floor` admission 正例は、schema/key 不変と新 script hash の動的再導出を確認するため実走対象に含める。原則としてファイル内容は変更しない。
- [test_hooks.py:2698-2702](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/tests/test_hooks.py:2698) は `floor_campaign.sh=dispatch-required`、[同:2920-2924](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/tests/test_hooks.py:2920) は `submit_floor.sh=local-ok` のまま通す。blob approval の trust root には数えない。

D926 が変更禁止とした面は次で機械確認する。

- `floor_submit_receipt.py` と `s8b_holdout_admission.py` は base-to-tip の file diff を 0 にする。
- 18 名集合の実体は [s8b_floor_contract.py:40-50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_contract.py:40)。既存 exact-set test を維持し、承認 control が集合へ混入しないことを追加 assertion にする。
- 判定式は [s8b_floor_campaign.py:6906-6919](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:6906)。AST で `official && fresh && nondefault_seams empty` の式が不変であることを固定する。
- pilot は flag 未指定の従来 call と argv が同じ結果へ進み、新 official flag・env は pilot で拒否する。この正負対で pilot の受理集合が 1 bit も広がっていないことを示す。

docs は実装子が触らず、親が [phase3-8b-restart-runbook.md:163-197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/docs/phase3-8b-restart-runbook.md:163) の「固定 pilot」「official 無条件拒否」を、固定 official・明示 confirm・nonce 束縛・raw qsub 非保証へ更新する。`docs/pegasus-runbook.md` の execution class 表は変更不要である。

## pin 閉包

現行 HEAD `08a17b3b3271dc6e0db575a7c15afbbbb91f6328` における `floor_campaign.sh` は、Git blob OID `b214e9f0e2f69ee41328f68fb38d8e4c946b7704`、blob bytes SHA-256 `f49a44e8fdd1cceb91c1a36c590f3f587cd0985edc1737fa89e28a09d343f555`。full/short OID・SHA の repo 内 literal pin は無い。

閉包は固定 digest 台帳ではなく動的束縛である。

- submitter が source commit の blob を hash し、working tree bytes と比較する（[submit_floor.sh:250-273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/tools/pegasus/submit_floor.sh:250)）。
- `pre-submit.json` と `submit-receipt.json` が `job_script_path` / `job_script_sha256` を記録する（[同:348-388](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/tools/pegasus/submit_floor.sh:348)、[同:679-708](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/tools/pegasus/submit_floor.sh:679)）。
- job script が executing bytes、receipt hash、source commit blob の三者を比較する（[floor_campaign.sh:723-785](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/tools/pegasus/floor_campaign.sh:723)）。
- static admission の operation key は `floor`（[certified_writer_preflight.py:136-176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/certified_writer_preflight.py:136)）。`_admit_floor()` が receipt の commit/path/hash から blob bytes を再取得する（[certified_writer_admission.py:178-224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/certified_writer_admission.py:178)）。
- job は同じ hash を `IZANAGI_RESERVATION_SCRIPT_SHA256` と reservation record へ運び（[floor_campaign.sh:956-985](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/tools/pegasus/floor_campaign.sh:956)）、driver が reservation binding と submit receipt を再照合する（[s8b_floor_campaign.py:7195-7233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:7195)）。
- job-result にも記録する（[floor_campaign.sh:1361-1398](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/tools/pegasus/floor_campaign.sh:1361)）。
- 挙動 pin は [test_pegasus_floor_tools.py:893-1005](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/tests/test_pegasus_floor_tools.py:893)、[同:2230-2260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/tests/test_pegasus_floor_tools.py:2230)、[test_floor_submit_receipt.py:109-118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/tests/test_floor_submit_receipt.py:109)、[certified_writer_fixtures.py:93-150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/tests/certified_writer_fixtures.py:93)、`test_campaign.py` の `floor` admission 正例である。
- `tools/pegasus/admission_registry.json` と `test_hooks.py` は実行場所の class pin であり、script blob の trust root ではない。

したがって D926 編集後に必要なのは、新 commit の新 blob hashを submitterが動的に記録・照合することの再実測である。固定 SHA 台帳、receipt schema、独立 trust root の更新はない。これが D323 の「別 source commit と別 script blob hash」を満たす。

## 未解決・親の裁定が要る点

- **実在する blocker:** 現行 job は staged payload を `--fetchcontent-base-dir` で渡す（[floor_campaign.sh:697-721](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/tools/pegasus/floor_campaign.sh:697)、[同:1226-1231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/tools/pegasus/floor_campaign.sh:1226)）。しかし同引数は 18 名集合の不適格 seam で（[s8b_floor_campaign.py:6891-6894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:6891)）、public official は承認 gate より先に拒否する（[同:6990-6996](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:6990)）。
- 引数を単に外すと default は `TMPDIR` に新しい base を作り（[同:2997-3048](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:2997)）、staged payload を使わない legacy transportへ入る（[同:3202-3247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1942-floor-gate-recheck/orchestrator/campaign/s8b_floor_campaign.py:3202)）。計算ノードの offline 条件では通る根拠がない。
- 18 名集合・判定式を変えず、D926 名指し面以外を変更しないという今回の制約下では、この transport 不整合を解く変更は書けない。親は「default legacy transport が実機で通ることを先に実測して argv から staged seam を外す」か、「固定 staged transport を production default とする追加変更を別途裁定する」かをユーザーへ返す必要がある。推奨は前者を実測し、赤なら scope 拡張を裁定すること。
- CLI/env の具体名は D926 逐語では未指定。本プランは `--confirm-official-floor` / `IZANAGI_CONFIRM_OFFICIAL_FLOOR` を推奨するが、親が別名を選ぶなら段 5 開始前に固定する。

## 総括

G-A は real `build_cells → build_v2 → receipt issuer` の one-cell 計算ノード probe、G-B は measurement-generation digest による read-only 衝突判定とする。  
(P1-c) は現行 main で誤りで、旧 36/228 件は fresh claim を塞がない。  
D926 自体の実装面は確定できるが、staged dependency seam と official eligibility の実在衝突は親の裁定なしに閉じない。