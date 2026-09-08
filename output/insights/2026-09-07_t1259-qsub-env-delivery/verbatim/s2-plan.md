## 方針

実装単位は、計算ノード用 probe 2 本、登録簿同期 3 箇所、単体検査 1 本の計 6 file とする。`submit_floor.sh` と `floor_campaign.sh` は参照だけで変更しない。

承認あり／なしは同じ job 内で環境を書き換えず、別々の `qsub` request にする。これにより、NQSV が各投入時点の環境をどう構成したかを独立に観測できる。

## P1 provisional 裁定

- **P1-a: 支持。** `t2228_driver_gate_liveness_probe.pbs:7-12` は 2 変数を 1 個の `-v` で渡し、同 `:100-115` が 2 本目の evidence path を必須化している。brief が示す実 request でもその先へ evidence が作られているため、2 本目専用の再実測は不要。本 probe は 3 変数をまとめて観測するので、2 本目も副次的に再確認される。
- **P1-b: 支持。** `floor_campaign.sh:267-1215` では repo 内 staging、receipt、allocation、依存 build、protocol 解決を経て初めて `driver_argv` に達する。承認ありの実 argv を観測するためにここを通すと official campaign の前段を起動し、repo へ書くため禁止条件に反する。承認あり側は §8 の分岐射影だけ、承認なし側だけ実 driver の早期拒否を観測する。
- **P1-c: 条件付き支持。** 6 file という変更集合は、後述の self-run harness を新規 test に持たせれば閉じる。ただし brief の行アンカーは不正確。`t1259...` は辞書順で `t139...` より前なので、t2228 行の近傍ではなく、registry は現 `:124` の前、class 辞書は `test_hooks.py:3053` の前、entry 辞書は同 `:3225` の前、runbook は現 `:513` の前へ入れる。
- **P1-d: 支持。** ambient 名は `T1259_NQSV_AMBIENT_SENTINEL` とし、`IZANAGI_` 接頭辞を使わない。repo 全域検索は 0 hit だった。
- **P1-e: 支持。** 実 driver を `-I -B`、承認 flag なしで呼ぶ CLI 経路には永続 state の変更がない。詳細は「P1-e の code path」に示す。なお、承認ありの実 driver は起動しない。

## 変更 file と行アンカー

| file | 位置 | 計画 |
|---|---:|---|
| `tools/pegasus/probes/t1259_qsub_env_delivery_probe.pbs` | 新規、予定 `1-130` | 短時間 PBS job、外部 log 検証、compute-only 検証、driver 起動 |
| `tools/pegasus/probes/t1259_qsub_env_delivery_probe.py` | 新規、予定 `1-300` | env 観測、§8 分岐射影、未承認実 driver の拒否観測、create-only evidence |
| `tools/pegasus/admission_registry.json` | 現 `:124` の直前 | `.pbs` と `.py` を `dispatch-required` として辞書順に追加 |
| `orchestrator/tests/test_hooks.py` | 現 `:3053`、`:3225` の各直前 | `_PEGASUS_EXPECTED_CLASSES` と `_PEGASUS_EXPECTED_ENTRIES` に同じ 2 entry を追加 |
| `docs/pegasus-runbook.md` | 現 `:513` の直前 | §7.0 投影表へ 2 行追加 |
| `orchestrator/tests/test_t1259_qsub_env_delivery_probe.py` | 新規、予定 `1-260` | probe、PBS contract、create-only publish、P1-e command の単体検査 |

## PBS job 本体

`tools/pegasus/probes/t1259_qsub_env_delivery_probe.pbs` は先行 probe の次を踏襲する。

- 予定 `:1-7`: `t2228...pbs:1-6` と同じ `#!/bin/bash`、`-A SFC`、`-q gen_S`、`-b 1` を使う。job 名だけ `izanagi-t1259` にする。
- `elapstim_req` は `03:00:00` から `00:10:00` へ短縮する。T-2228 の 3 時間は `:145-304` の gflags/glog build、3 repo clone、複数 driver 実行用だった。本 probe は環境の読み取り、短い Python import、CLI 早期拒否だけで、build、clone、benchmark、campaign は一切ない。10 分は起動と import に十分な余裕を持ちつつ観測 job を短くする。
- 予定 `:10-20`: `set -Eeuo pipefail`、`umask 077`、`GIT_DIR` などの Git selector unset を `t2228...pbs:14-21` から踏襲する。
- 予定 `:21-45`: `PBS_JOBID`、`PBS_O_WORKDIR`、`bnode[0-9]+`、canonical repo root の検証を同 `:23-42` から踏襲する。
- 予定 `:46-80`: `/proc/$$/fd/1` と `/proc/$$/fd/2` を使う外部 scheduler log 検証を同 `:44-71` から踏襲する。両 log が同じ repo 外 directory にあることを要求し、その親を evidence directory とする。これにより、観測対象である `IZANAGI_FLOOR_JOB_EVIDENCE_ROOT` が落ちても result を残せる。
- 予定 `:81-100`: evidence directory の `expected-head.txt` と実 HEAD を照合し、tracked-clean を要求する。probe `.pbs`、`.py`、実 driver が regular・非 symlink・tracked であることも確認する。
- 予定 `:101-118`: `/scr/${PBS_JOBID//:/_}-t1259-qsub-env-delivery` を mode 0700 で create-only 作成し、EXIT trap でその exact directory だけ削除する。Python 3.10 以上の選択と `PYTHONPATH/PYTHONHOME/PYTHONSTARTUP` の unset は `t2228...pbs:117-143` を踏襲する。
- 予定 `:119-130`: Python driver へ `--repo-root`、`--evidence-dir`、`--scratch-dir`、`--pbs-job-id` を渡す。env 値そのものを argv に写さず、driver が `os.environ` から直接観測する。

T-2228 の dependency policy 読み込み、gflags/glog build、CCBench clone、3 driver cloneである `t2228...pbs:145-308` は全削除する。今回の estimand に不要で、walltime を延ばすだけだからである。

## 計算ノード側 driver

`tools/pegasus/probes/t1259_qsub_env_delivery_probe.py` は以下の構造とする。

- 予定 `:1-35`: schema、対象 env 名、32 桁 lowercase hex regex、ambient の固定期待値を定義する。全環境を dump せず、対象 4 変数だけを記録する。
- 予定 `:36-85`: canonical repo、external evidence、compute hostname、expected HEAD を検証する。Git 読み取りは `GIT_OPTIONAL_LOCKS=0` で行う。
- 予定 `:86-125`: env を unset／set-empty／set-nonempty の三値で観測する。条件は次の排他的な形から自動判定する。

  - 承認あり: `IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN` が存在し、`T1259_QSUB_SECOND_HEX` は不在。
  - 承認なし: 承認変数が不在で、`T1259_QSUB_SECOND_HEX` が存在。
  - 両方存在または両方不在: invalid observation。

- 予定 `:126-160`: 明示 3 変数を順序付きで記録し、全てが存在すること、nonce 2 本が 32 桁 hex であること、evidence root が scheduler log から独立導出した directory と一致することを検査する。承認ありでは approval と submission nonce の exact 一致も要求する。
- 予定 `:161-185`: `T1259_NQSV_AMBIENT_SENTINEL` の存在、値、固定期待値との一致を記録する。unset と期待値どおりの present はどちらも正常な観測結果とし、別値だけを異常にする。したがって「継承しなかった」ことを失敗扱いしない。
- 予定 `:186-215`: `floor_campaign.sh:547-566` と同じ四分岐を純粋関数として射影する。

  - unset: `OFFICIAL_APPROVAL_BOUND=0`、driver flag なし。
  - set-empty: submit-binding で拒否。
  - nonce 不一致: submit-binding で拒否。
  - nonce exact 一致: `OFFICIAL_APPROVAL_BOUND=1`。

  さらに `floor_campaign.sh:1216-1225` に従い、bound=1 のときだけ `--confirm-official-floor-run` が 1 個追加されると記録する。

- 予定 `:216-255`: 承認なし job だけ実 driver を次の exact argv で subprocess 起動する。

  ```text
  <python3.10+> -I -B <repo>/orchestrator/campaign/s8b_floor_campaign.py \
    --mode official \
    --protocol <scratch>/protocol-loader-must-not-run.json
  ```

  protocol file は事前・事後とも不存在とする。`capture_output=True` で stdout/stderr を pipe に保持し、rc=2、単一 JSON、`status="refused"`、承認 flag 要求文、stderr 空を要求する。承認あり job ではこの subprocess を起動せず、`executed=false` と scope 上の理由を記録する。

- 予定 `:256-285`: subprocess 前後で repo の tracked-clean 状態と scratch の entry 集合が変わらないことを確認する。
- 予定 `:286-300`: T-2228 driver `:108-145` と同じ temp＋hard-link publish を使い、`result.json` を create-only、fsync 付きで公開する。既存 target は上書きしない。

result の主な field は `condition`、`explicit_env_order`、各 env の三値観測、`ambient`、`floor_section8_projection`、`unapproved_driver_cli`、`repo_head`、`repo_state_before/after`、`hostname`、`pbs_job_id`、`ok` とする。

## 投入 command 全文

以下は実装後に親が実行する command であり、本段では実行しない。2 request とも `-v` はちょうど 3 変数である。

```bash
set -Eeuo pipefail
umask 077

cd /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1259-qsub-env-delivery

T1259_ATTEMPT=$(date -u +%Y%m%dT%H%M%SZ)-$$
T1259_ROOT=/work/1/SFC/tanab/izanagi-job-evidence/t1259/"$T1259_ATTEMPT"
T1259_WITH_DIR="$T1259_ROOT/with-approval"
T1259_WITHOUT_DIR="$T1259_ROOT/without-approval"
T1259_REPO_HEAD=$(git rev-parse --verify HEAD)
T1259_WITH_NONCE=$(python3.10 -I -B -c 'import secrets; print(secrets.token_hex(16))')
T1259_WITHOUT_NONCE=$(python3.10 -I -B -c 'import secrets; print(secrets.token_hex(16))')
T1259_WITHOUT_SECOND=$(python3.10 -I -B -c 'import secrets; print(secrets.token_hex(16))')

test ! -e "$T1259_ROOT"
mkdir -p -m 700 "$T1259_WITH_DIR" "$T1259_WITHOUT_DIR"
(
  set -o noclobber
  printf '%s\n' "$T1259_REPO_HEAD" >"$T1259_WITH_DIR/expected-head.txt"
  printf '%s\n' "$T1259_REPO_HEAD" >"$T1259_WITHOUT_DIR/expected-head.txt"
)

(
  unset IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN T1259_QSUB_SECOND_HEX
  export T1259_NQSV_AMBIENT_SENTINEL=t1259-ambient-sentinel-v1
  qsub \
    -o "$T1259_WITH_DIR/pbs.stdout" \
    -e "$T1259_WITH_DIR/pbs.stderr" \
    -v "IZANAGI_SUBMISSION_NONCE=$T1259_WITH_NONCE,IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN=$T1259_WITH_NONCE,IZANAGI_FLOOR_JOB_EVIDENCE_ROOT=$T1259_WITH_DIR" \
    tools/pegasus/probes/t1259_qsub_env_delivery_probe.pbs \
    >"$T1259_WITH_DIR/qsub.stdout" \
    2>"$T1259_WITH_DIR/qsub.stderr"
)

(
  unset IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN T1259_QSUB_SECOND_HEX
  export T1259_NQSV_AMBIENT_SENTINEL=t1259-ambient-sentinel-v1
  qsub \
    -o "$T1259_WITHOUT_DIR/pbs.stdout" \
    -e "$T1259_WITHOUT_DIR/pbs.stderr" \
    -v "IZANAGI_SUBMISSION_NONCE=$T1259_WITHOUT_NONCE,T1259_QSUB_SECOND_HEX=$T1259_WITHOUT_SECOND,IZANAGI_FLOOR_JOB_EVIDENCE_ROOT=$T1259_WITHOUT_DIR" \
    tools/pegasus/probes/t1259_qsub_env_delivery_probe.pbs \
    >"$T1259_WITHOUT_DIR/qsub.stdout" \
    2>"$T1259_WITHOUT_DIR/qsub.stderr"
)
```

承認あり側は `submit_floor.sh:632-638` が最大構成で作る exact 3 名、すなわち 32 桁 nonce、同じ 32 桁 approval nonce、絶対 evidence path である。

承認なし側は approval を本当に unset にしたまま 3-field delivery を測るため、2 本目を衝突しない probe 専用の `T1259_QSUB_SECOND_HEX` に置き換える。値の形は同じく 32 桁 hex 2 本＋絶対 path 1 本である。

## ambient 継承の観測

使用名は `T1259_NQSV_AMBIENT_SENTINEL`、値は `t1259-ambient-sentinel-v1` とする。各 `qsub` を subshell に閉じ、そこでだけ export する。`-v` には載せないため、job 側に存在すれば NQSV または job 起動環境が ambient を継承した直接証拠になる。

実施した検索は次のとおり。

```bash
rg -n --hidden -g '!.git/**' -F 'T1259_NQSV_AMBIENT_SENTINEL' . \
  | awk 'BEGIN{n=0} {print; n++} END{print "HIT_COUNT=" n}'
```

結果は `HIT_COUNT=0`。同様に承認なし側の明示 control 名も検索した。

```bash
rg -n --hidden -g '!.git/**' -F 'T1259_QSUB_SECOND_HEX' . \
  | awk 'BEGIN{n=0} {print; n++} END{print "HIT_COUNT=" n}'
```

こちらも `HIT_COUNT=0`。既存 consumer、fixture、文書上の既存契約との衝突はない。

2 result の ambient 判定は次のように読む。

- 両方 absent: 当該 2 request では ambient 継承なし。
- 両方 expected value: 当該 2 request では ambient 継承あり。
- 一方だけ present、または別値: 条件依存または汚染として一般化せず indeterminate。

## floor_campaign §8 への対応

| job | 実測する env | `floor_campaign.sh:552-566` の射影 | `:1216-1225` の argv 射影 |
|---|---|---|---|
| 承認あり | nonce、approval、evidence の 3 本 | exact 一致なら `OFFICIAL_APPROVAL_BOUND=1` | approval flag を 1 個 append |
| 承認なし | nonce、control hex、evidence の 3 本。approval は unset | `OFFICIAL_APPROVAL_BOUND=0` のまま通過 | approval flag を append しない |
| ambient | 独自 sentinel の present／absent | §8 自体は読まない | ambient が一般継承されるなら、投入 shell に残した承認 env も届きうるという運用上の反例になる |

これは §8 の shell 本体を実行した観測ではない。実測 env に対する現行 source の分岐射影である。この非対称を result と最終報告に明記する。

## P1-e の code path

未承認の実 driver CLI は安全に使える。

1. direct CLI 起動時の `sys.path` と `__package__` の変更は `s8b_floor_campaign.py:81-88` の process memory 内だけ。
2. `_parser()` の `--protocol` は `Path` への変換だけで、file を開かない (`:8396-8413`)。
3. `main()` は parse 後、`args.mode == "official"` かつ approval flag がない場合に `:8608-8615` で rc=2 を返す。
4. protocol path の絶対化は `:8617-8619`、loader は `:8622` なので、どちらも拒否後で未到達。
5. freeze loader、`repo_output_root()`、`run_campaign()` は `:8629-8638` で、すべて未到達。
6. state を変更する可能性が指摘されていた `take_checkpoint_environment()` は private core `:7259-7261` にしかなく、その実体の `floor_job_checkpoint.py:474-490` にある `os.environ.pop` も未到達。
7. public wrapper の承認 gateも `_run_campaign_core` より前にある (`s8b_floor_campaign.py:7174-7215`)。
8. subprocess は `-B` と `PYTHONDONTWRITEBYTECODE=1` を使うため import 時の `__pycache__` 作成もない。stdout/stderr は pipe に捕獲する。

既存テストも `test_s8b_floor_campaign.py:7394-7407` で protocol loader が未呼出しであることを固定している。したがって、未承認 CLI は filesystem を変更せず拒否するという P1-e を採用する。実 probe では nonexistent protocol、repo clean 前後比較、scratch entry 前後比較を追加して実 bytes でも再確認する。

## repo 外 write の閉包

probe が書く可能性のある path は次だけとする。

- login 側:

  - `$T1259_WITH_DIR/expected-head.txt`
  - `$T1259_WITHOUT_DIR/expected-head.txt`
  - 各 directory の `qsub.stdout`
  - 各 directory の `qsub.stderr`

- NQSV scheduler:

  - 各 directory の `pbs.stdout`
  - 各 directory の `pbs.stderr`

- compute job:

  - `/scr/${PBS_JOBID//:/_}-t1259-qsub-env-delivery/`
  - 各 evidence directory 内の `.result.json.<random>.tmp`
  - 各 evidence directory内の `result.json`

一時 JSON は final hard-link publish 後に unlink し、scratch は EXIT trap で exact directory だけ削除する。

永続 path の根は `/work/1/SFC/tanab/izanagi-job-evidence/t1259/...` であり、repo root `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1259-qsub-env-delivery` の外である。PBS job は両者を canonicalize して containment を拒否する。`protocol-loader-must-not-run.json` は不存在確認に使うだけで作成しない。repo 内 `output/`、`.git/`、probe source directoryには書かない。

## 登録簿の閉包検索

先行 probe 名を repo 全域で検索した結果は 251 line hit だった。

```bash
rg -n --hidden -g '!.git/**' -F 't2228_driver_gate_liveness_probe' . \
  | awk 'BEGIN{n=0} {print; n++} END{print "HIT_COUNT=" n}'
```

大半は過去 insight、mutation ledger、実 evidence であり、現行 gate ではない。live 登録候補 7 file に絞った同検索は 10 hitで、実際の登録箇所は次の 3 fileだけだった。

- `tools/pegasus/admission_registry.json:190-200`
- `orchestrator/tests/test_hooks.py:3064-3065,3291-3301`
- `docs/pegasus-runbook.md:524-525`

構造 marker の repo 全域検索では 126 line／93 file hitだった。履歴・evidence を除いた live surface では20 hitだった。

```bash
rg -n --hidden -g '!.git/**' \
  -e '_PEGASUS_EXPECTED_CLASSES' \
  -e '_PEGASUS_EXPECTED_ENTRIES' \
  -e 'test_bash_pegasus_execution_inventory_is_synchronized' \
  -e '_ADMISSION_PROJECTION_HEADER' \
  -e '_check_admission_projection' \
  -e 'PYTEST_ONLY_ALLOWLIST' \
  -e 'test_every_test_file_is_self_runnable_or_allowlisted' . \
  | awk 'BEGIN{n=0} {print; n++} END{print "HIT_COUNT=" n}'
```

赤になる閉包は以下で尽きる。

- `test_hooks.py:4360-4386`: `tools/pegasus/` を再帰 walkし、`.py/.sh/.pbs` 等と registry key の集合完全一致を要求する。新規 probe だけ足すと最初にここが赤。
- `test_hooks.py:3032-3103,3104-3525` と `:3926-3937`: registry を追加すると、class 辞書と entry×4-field golden の両方が赤になる。
- `docs/pegasus-runbook.md:489-560` と `tools/check_docs.py:4404-4438,4541-4587`: registry の `(path,class,evidence)` と投影表の集合完全一致。runbook に2行必要。
- `tools/pegasus_admission_registry.py:113-135`: JSON path順、field順、2-space indent、末尾 LF を canonical bytes として要求する。実装変更は不要だが、新 entry は `t139...` より前へ置く。
- `test_plain_runner_coverage.py:44-86`: 新規 `test_*.py` に自走 harness も allowlist もなければ赤になる。

更新不要と判定した箇所は次のとおり。

- `tools/pegasus/README.md`: `tools/check_docs.py:4682-4802` の宣言表は registry 全件表ではなく、README 本文が言及する実行体だけの部分表。本 probe をREADME手順へ追加しないため更新不要。
- `hooks/guard_bash.py`: registry を動的 loadするため literal entry 追加不要。
- `orchestrator/tests/test_check_docs.py`: synthetic fixture であり実 registry 全件の複製ではない。
- `orchestrator/tests/acceptance_duration_ledger.json`: 新規 node の閉集合登録を要求しない。

したがって brief の6 fileは過剰ではない。一方、brief は `test_plain_runner_coverage.py` という赤の経路を列挙していなかった。新規 test 末尾に、先行 test `test_t2228_driver_gate_liveness_probe.py:444-445` と同じ `pytest.main([__file__])` の self-run harness を置くことで、README allowlist という7本目の編集を避ける。

## 登録内容

`tools/pegasus/admission_registry.json`、`test_hooks.py` の2辞書、runbook投影表には次の分類を同値で入れる。

- `.pbs`

  - class: `dispatch-required`
  - reason: `PBS T-1259 qsub environment delivery observation job body`
  - primary gate: `PBS allocation and job-body compute-host, repository, log-path, and evidence-path validation`
  - evidence: `static job-body classification`

- `.py`

  - class: `dispatch-required`
  - reason: `compute-side T-1259 qsub environment delivery and official CLI refusal observer`
  - primary gate: `compute allocation owned by t1259_qsub_env_delivery_probe.pbs`
  - evidence: `static compute-side call-site classification`

## 単体検査

新規 `orchestrator/tests/test_t1259_qsub_env_delivery_probe.py` は、既存 `test_t2228_driver_gate_liveness_probe.py` の隣に置き、同じ import と self-run 形式を使う。

予定する検査は次のとおり。

- 3-field の承認あり／なしを合成 env で与え、順序、存在、32 hex、absolute path、approval exact-match を検証。
- A、B、C を1本ずつ欠落させ、result は公開できるが `ok=false` になることを検証。
- ambient の absent と expected-present の双方が有効な観測、set-empty／別値が異常になることを検証。
- §8 射影の unset、empty、mismatch、exact-match の4分岐と、approval flag の0個／1個を固定。
- 承認なしだけが実 driver helper を呼び、argv に `-I -B`、`--mode official`、不存在 protocol があり、承認 flag がないことを検証。
- 承認ありでは実 driver subprocess が呼ばれないことを検証。
- result の create-only publishが既存 file を上書きせず、tempを残さないことを検証。
- evidence pathが repo内、symlink、非 canonicalなら拒否することを検証。
- PBS sourceに `gen_S`、`-b 1`、`00:10:00`、compute hostname gate、外部 fd検証、Git env unset、scratch cleanupが存在することを静的に固定。
- 新規 test自身が `pytest.main([__file__])` を持つことを確認し、`test_plain_runner_coverage.py:60-86` を緑に保つ。

実装後に親が行う焦点検査は次の組とする。

```text
python3 tools/run_tests.py \
  orchestrator/tests/test_t1259_qsub_env_delivery_probe.py \
  orchestrator/tests/test_hooks.py::test_bash_pegasus_registry_schema_and_fixed_classes \
  orchestrator/tests/test_hooks.py::test_bash_pegasus_execution_inventory_is_synchronized \
  orchestrator/tests/test_plain_runner_coverage.py \
  -q -rf
python3 tools/check_docs.py
```

本段では filesystem が read-onlyであり、依頼も plan のみに限定されるため、test、`qsub`、official mode は実行していない。

## 総括

- 10分・gen_S・1 node の軽量 probeを、承認あり／なしの2 requestとして投入する計画。
- 各 `qsub -v` はちょうど3変数。承認ありは production exact names、承認なしはapprovalをunsetにして固有control hexへ置換する。
- ambient sentinelは `-v` に載せず、repo全域検索0 hitを確認済み。
- §8は実測envから射影し、承認ありの実 driverは起動しない。未承認の実 driverだけ、protocol loaderより前のrc=2拒否を観測する。
- 永続writeはすべて `/work/1/SFC/tanab/izanagi-job-evidence/t1259/...`、一時writeはjob専用 `/scr/...` に限定し、repo内writeは0。
- 変更集合はbriefの6 fileで閉じる。ただし辞書順アンカーはt2228近傍ではなくt139直前へ修正する。
- 未解決なのはNQSVのambient継承結果そのものだけであり、2 jobの実走後に確定する。