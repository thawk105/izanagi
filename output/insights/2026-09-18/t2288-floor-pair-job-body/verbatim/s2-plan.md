## plan v1

以下の行番号は読んだ現物のもの。新規３ファイルにはまだ行番号がないため、追加する関数・段名と、その根拠となる既存 `file:line` を示す。`V/` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-pair-job-body/verbatim/` を指す。本段では書き込み・テスト実行とも行っていない。

1. **job body `tools/pegasus/floor_pair_window.sh` の段構成**

   PBS header は `-A SFC`、`-q gen_S`、`-b 1`、`--accept-sigterm=yes`。`elapstim_req` は submitter の `qsub -l` で指定し、header には重複記載しない。既存型は `tools/pegasus/floor_campaign.sh:1–19`。

   エラーは固定 token の一行 JSON、例えば `{"gate":"site","reason":"compute_node_required"}` を stderr に出す。bootstrap 前でも使える Bash `fail()` とし、任意の未検証文字列を JSON に直接埋めない。終了コードは入力不正 `2`、前段検査拒否 `4`、receipt 書込み失敗 `5`、driver は取得した rc を保存・伝播する。

   | 段 | 実装内容 | 拒否時 |
   |---|---|---|
   | bootstrap | `PBS_JOBID`、`PBS_O_WORKDIR` と下記 `FP_*` を要求。job ID は既存許容 regex、nonce は lowercase 32 hex、HEAD は40 hex、sha は64 hex。mode は `window/finalize` のみ | rc=2、`bootstrap/missing_binding`、`invalid_binding` |
   | environment | PATH を `/usr/bin:/bin:/opt/nec/nqsv/bin:/system/tool/bin` に固定。`PYTHONPATH/PYTHONHOME/PYTHONSTARTUP`、`LD_PRELOAD/LD_LIBRARY_PATH`、継承 `GIT_*` を除去。PBS 変数は保持 | rc=2、`environment/cleanup_failed` |
   | interpreter | `python3.10` を優先し、既存型で realpath・実行可能・version ≥3.10 を確認。候補は `python3.10 python3.11 python3.12 python3` | rc=2、`interpreter/python_unavailable` |
   | commands | `git pgrep sha256sum hostname date realpath mkdir env`、後述の shim 用 `ln` を確認。`realpath` は interpreter 解決前にも必要なので先に存在確認 | rc=2、`commands/required_command_missing` |
   | checkout | `PBS_O_WORKDIR` の realpath と `git rev-parse --show-toplevel` を照合。`HEAD^{commit}` と `FP_EXPECTED_HEAD` を照合 | rc=4、`checkout/root_mismatch`、`head_mismatch` |
   | input preflight | spec の実 bytes を `FP_SPEC_SHA256` と照合。spec は閉集合の relpath。`artifacts[]` の binary 全件について実在・実行可能・sha 一致を確認 | rc=4、`spec/hash_mismatch`、`binary/missing_or_mismatch` |
   | site | `hostname` の出力を `require_compute_hostname()` に渡す。第一 label を lowercase 化し `^bnode[0-9]+$` と照合 | rc=4、`site/compute_node_required` |
   | time | window mode のみ、選択した窓に対し後述の時刻 gate を再検査 | rc=4、`window/before_window`、`insufficient_remaining_time` |
   | scratch | `TMPDIR=/scr/${PBS_JOBID}` を `mkdir -m 0700` 一回で作成。既存なら拒否。必要な `python3` shim を配下に置き PATH 先頭へ追加 | rc=4、`scratch/create_failed` |
   | driver | stdout/stderr を別ファイルへ create-only 保存し、CLI を一回起動。retry・出力削除なし | driver rc を保持 |
   | result | `job-result.json` を Python `open(...,"x")` で作成。stdout sha256 と実際の driver rc を記録 | driver 非0を優先、driver=0なら receipt 失敗で5 |

   束縛 env は次の８個とする。

   ```text
   FP_NONCE
   FP_EXPECTED_HEAD
   FP_SPEC_RELPATH
   FP_SPEC_SHA256
   FP_MODE
   FP_WINDOW_ID
   FP_EVIDENCE_DIR
   FP_ELAPSTIM_REQ
   ```

   `FP_WINDOW_ID` は window mode では `rr95-w1` 等、finalize mode では literal `none`。receipt では finalize の `window_id` を JSON `null` にする。env 名は PBS が自動設定する名前と衝突させない。

   **driver 起動は P5 の `-I -m` を修正する。** isolated mode のまま checkout を明示的に import path へ置き、既存 `main()` を呼ぶ。既存の明示 import 方式は `floor_campaign.sh:196–210`、CLI 契約は `floor_pair_driver.py:3113–3144`。

   ```bash
   DRIVER_BOOTSTRAP='import sys; sys.path.insert(0, sys.argv.pop(1)); from orchestrator.campaign.floor_pair_driver import main; raise SystemExit(main())'

   driver_argv=(
     "$PY" -I -B -c "$DRIVER_BOOTSTRAP" "$REPO_ROOT"
     --repo-root "$REPO_ROOT"
     --spec "$FP_SPEC_RELPATH"
     --expected-sha256 "$FP_SPEC_SHA256"
   )
   case "$FP_MODE" in
     window) driver_argv+=(--execute-window "$FP_WINDOW_ID") ;;
     finalize) driver_argv+=(--finalize) ;;
   esac
   ```

   cwd は `$REPO_ROOT`。`driver.stdout` / `driver.stderr` は `$FP_EVIDENCE_DIR` 直下で、`noclobber` を使う。stdout は driver の JSON result、測定 JSONL・summary は凍結 spec が指定する repo 内 path のまま。

   `job-result.json` の最小 schema は以下。

   ```text
   schema_version = "pegasus-floor-pair-job-result/v1"
   pbs_jobid, hostname, nonce, expected_head
   spec_relpath, spec_sha256, mode, window_id
   driver_rc, driver_stdout_sha256
   started_epoch, completed_epoch
   job_rc, gate, reason
   ```

   開始 epoch は job 本体開始、終了 epoch は receipt 作成直前。driver 未起動なら `driver_rc` と `driver_stdout_sha256` は `null`。bootstrap のように evidence directory をまだ信頼できない段では stderr のみとし、receipt の存在を保証しない。

   trap は `floor_campaign.sh:441–462` の ERR・signal 分類を継承するが、checkpoint 書込みは継承しない。driver を background child として待つ場合は、TERM/HUP/INT で signal を記録し、`wait` の中断を driver 終了と取り違えず終了を回収する。shell から driver に追加の `kill` は送らない。signal 終了は `128+signal`、不明の driver rc を捏造しない。scheduler の SIGKILL まで receipt を保証する設計ではない。

   継承／非継承は次のとおり。

   - **継承**：PBS/nonce bootstrap、interpreter 選択、ERR/signal の区別、create-only job-result。根拠は `floor_campaign.sh:22–45,169–184,421–462,1352–1397`。
   - **非継承**：gflags/glog build と protocol-resolution。今回は凍結 binary と spec が入力であり、build・protocol 選定をやり直さない。
   - **非継承**：allocation-reservation の qstat 照合、checkpoint、`certified_writer_preflight`。別 campaign の予約・復旧・書込み契約を移植せず、この driver の既存契約を通す。
   - **非継承**：A-5 の worktree 作成・build proxy・cleanup。測定 checkout H を３段で維持する。

   shell の HEAD/hash/binary 確認は早期拒否のための前段であり、driver の検証実装はコピーしない。`load_frozen_spec()` の sha・HEAD blob・参照束縛は `floor_pair_driver.py:1230–1292`、live site と runtime HEAD は `:2228–2236`、成果物の exclusive create は `:1685–1691,2273,3083–3087` に残す。site env の偽装、validator の差替え、出力の事前作成は行わない。

2. **窓の時刻 gate と walltime の一元化**

   入力 field は実在する。３ spec とも `windows` は109行、`not_after/not_before` は113–114行と124–125行、`window_id` は119行と130行。`--workload rr95 --window w1` を `rr95-w1` に変換し、`windows[].window_id` の exact 一致で引く。配列の先頭／末尾で選ばない。

   `date -u +%s` で実時計の epoch を得る。spec の ISO 値は選択済み Python の `datetime.fromisoformat(value.replace("Z","+00:00")).timestamp()` で epoch 秒へ変換する。未来時刻の注入は CLI に持たせず、純粋関数の引数だけに設ける。

   ```bash
   window_gate() {
     local now=$1 not_before=$2 not_after=$3 duration=$4
     (( now >= not_before )) || {
       fail 4 window before_window
     }
     (( now + duration <= not_after )) || {
       fail 4 window insufficient_remaining_time
     }
   }
   ```

   `duration > 0` と時刻・duration の整数化は呼出し前に検査する。`now=not_before` と `now=not_after-duration` は通り、それぞれ１秒外側は拒否する。正の duration により、許可される開始時刻は必ず半開区間内になる。

   `elapstim_req` の literal は **submitter の mode 分岐一箇所**に置く。

   ```bash
   case "$MODE" in
     window) ELAPSTIM_REQ=10:00:00 ;;
     finalize) ELAPSTIM_REQ=00:30:00 ;;
   esac
   ```

   同じ変数を `qsub -l "elapstim_req=$ELAPSTIM_REQ"` と `FP_ELAPSTIM_REQ` に渡す。秒数はこの値から導出し、36000/1800 の運用定数を別に置かない。job body は受領値を秒に変換する。PBS header の walltime 検査は「literal が存在する」から「重複せず、qsub と伝播値が同じ変数に束縛される」へ変更する。

   queue 待ちで窓の残時間が不足した job は、driver 起動前に拒否する。守るのは**測定成果物の path を未作成で残すこと**であり、submit evidence が存在しないという意味ではない。scratch 準備後、driver 直前にも実時計を取り直して同じ関数を呼べば、準備時間による境界越えも拒否できる。

   DW-O13 の具体例は全６窓について実 field を読み、以下を検査する。

   - `2026-09-18T01:47:00Z`：w1 前、拒否。
   - 各窓の `not_before`：許可。
   - `not_after−10h`：許可。
   - `not_before−1s`、`not_after−10h+1s`、`not_after`：拒否。

   凍結窓は session 開始帯であり、全 session 完了や実 campaign 間24時間分離の保証ではない。根拠は `V/D2138.md:16–20`、`V/t2288-a5-freeze-handover.md:10–15`。

3. **submitter `tools/pegasus/submit_floor_pair.sh`**

   引数は `--workload {rr95,rr50,rr5}`、排他的な `--window {w1,w2}` / `--finalize`、任意の `--dry-run`、`-h/--help` に限る。重複指定・不足値・未知引数は rc=2。任意 spec、HEAD、evidence root、job script、walltime を指定する引数は足さない。`--assume-now` は採らない。

   pin 表は workload の **case 文**で、次の完全な relpath と sha256 を返す。省略形を runtime で扱わない。

   ```text
   output/env/pegasus/floor-pair/t2288-f1/spec__env-pegasus__protocol-silo__threads-48__workload-rr95-s0.9-rmw0__campaign-t2288-f1-rr95-c1c2.json
   990e3a6feb176ccf863315fde6e2afce43b7fc16053f50a1080641dde2570619

   output/env/pegasus/floor-pair/t2288-f1/spec__env-pegasus__protocol-silo__threads-48__workload-rr50-s0.9-rmw0__campaign-t2288-f1-rr50-c1c2.json
   b582d20c37268f491e4c47bb7436731197c18e737cdcca43694c64fa3e0d5e37

   output/env/pegasus/floor-pair/t2288-f1/spec__env-pegasus__protocol-silo__threads-48__workload-rr5-s0.9-rmw0__campaign-t2288-f1-rr5-c1c2.json
   d13c384473a5d24170e929f7e17aad9cc24479a5487ed0da21d06bc45430d8c4
   ```

   根拠は `V/D2138.md:7–11,33–42`、tracked 正本は `docs/decisions.md:66903–66907,66929–66938`。job 側は submitter が渡した pin と実 bytes を照合し、別の hash 表を持たない。

   checkout は script 所在地から canonical root を導出し、次を明示的に rc 確認する。

   ```bash
   git -C "$REPO_ROOT" rev-parse --show-toplevel
   git -C "$REPO_ROOT" rev-parse --verify HEAD^{commit}
   git -C "$REPO_ROOT" symbolic-ref -q HEAD
   git -C "$REPO_ROOT" status --porcelain --untracked-files=no
   sha256sum -- "$REPO_ROOT/$SPEC_RELPATH"
   git -C "$REPO_ROOT" show "HEAD:$SPEC_RELPATH" | sha256sum
   ```

   `symbolic-ref` は rc=1を detached として受理し、rc=0は拒否、その他は観測失敗として拒否する。`status` の失敗を「出力が空なので clean」としない。実 file sha と HEAD blob の **SHA-256** の両方を pin と照合する。blob OID と比較しない。型の根拠は `submit_t2417_backoff_policy_performance.sh:6–25`。

   binary は spec の `artifacts[].binary_relpath/binary_sha256` 全件を使う。３ spec の5–6行と15–16行はいずれも同一 binary。`-f/-x` と sha を確認し、配置は事前の `b4_binary_record place` に任せる。policy 検査を移植・緩和しない（`V/D2069.md:8–22`）。

   window は時刻 gate、finalize は `outputs.summary_relpath` の不在を確認する。不在判定は dangling symlink も既存扱いにする。finalize に窓時刻 gate は課さず、両窓の完全性・同一HEADは driver に任せる。

   evidence base は `/work/1/SFC/tanab/izanagi-job-evidence/floor-pair`。base の準備と nonce leaf 作成を区別し、leaf は `mkdir -m 0700 "$EVIDENCE_DIR"` 一回だけ。失敗を「既存または作成不能」として拒否し、同じ nonce で retry しない。既存型は `submit_floor.sh:310–333`。

   **P6 の所有記述を修正**し、同じ leaf 内の所有ファイルを分ける。

   | 所有者 | ファイル |
   |---|---|
   | submitter | `pre-submit.json`、`qsub.stdout`、`qsub.stderr`、`submit-receipt.json` |
   | scheduler | `scheduler.stdout`、`scheduler.stderr` |
   | job body | `driver.stdout`、`driver.stderr`、`job-result.json` |

   qsub は repo root へ移動して、一回だけ次の argv で呼ぶ。

   ```bash
   qsub_cmd=(
     qsub
     -l "elapstim_req=$ELAPSTIM_REQ"
     -N "$JOB_NAME"
     -v "$EXPORT_SPEC"
     -o "$EVIDENCE_DIR/scheduler.stdout"
     -e "$EVIDENCE_DIR/scheduler.stderr"
     tools/pegasus/floor_pair_window.sh
   )
   ```

   `JOB_NAME` は `fp-rr95-w1` / `fp-rr95-fin` 型。`EXPORT_SPEC` は項1の８変数を明示的な `NAME=value` 列で渡す。`-V` は使わない。path は固定 root と安全な nonce による絶対 path、spec は固定 relpathなので comma/newline を含まない。

   `pre-submit.json` は qsub 前に create-only。submit receipt は以下を持つ。

   ```text
   schema_version = "pegasus-floor-pair-submit-receipt/v1"
   nonce, expected_head, repo_root, spec_relpath, spec_sha256
   mode, window_id, evidence_dir
   request = {project:"SFC", queue:"gen_S", nodes:1, elapstim_req, elapstim_req_s}
   qsub_argv, dry_run, qsub_rc, pbs_jobid
   status, prepared_epoch, completed_epoch
   ```

   dry-run は `status="dry_run"`、`qsub_rc=null`、`pbs_jobid=null`。実 qsub 非0は `failed`、rc=0でも ID を読めなければ `indeterminate`。自動再投入しない。ID parsing は `submit_floor.sh:672–690` の NQSV 表示／単一 token の型を継承する。

   `--dry-run` は全入力・時刻 gate を通し、通過後は evidence leaf と投入予定記録を作るが qsub は呼ばない。driver・scratch・測定成果物は作らない。窓前拒否は evidence 作成前なので副作用なし。現時刻での正例は不要で、未来時刻の正例は snippet テストに限定する。

4. **登録簿の閉包**

   `tools/pegasus/admission_registry.json:70–81` と `:340–350` の位置関係に、ソート順で次の２ entry を追加する。

   ```json
   "tools/pegasus/floor_pair_window.sh": {
     "class": "dispatch-required",
     "reason": "PBS floor-pair window and finalize job body",
     "primary_gate": "PBS allocation and job-body site preflight",
     "evidence": "static job-body classification"
   },
   "tools/pegasus/submit_floor_pair.sh": {
     "class": "local-ok",
     "reason": "login-side PBS floor-pair submitter",
     "primary_gate": "qsub submission; compute work stays in job body",
     "evidence": "static login-side submitter classification"
   }
   ```

   field 順と canonical bytes は `tools/pegasus_admission_registry.py:20,98–115,128–135` に従う。

   親は `docs/pegasus-runbook.md:502–577` の投影表へ以下を追加する。

   ```markdown
   | `tools/pegasus/floor_pair_window.sh` | `dispatch-required` | `static job-body classification` |
   | `tools/pegasus/submit_floor_pair.sh` | `local-ok` | `static login-side submitter classification` |
   ```

   §7.8 には同一 detached H、checkout ごとの place、６ window job＋３ finalize job、窓前／末端拒否、成果物を途中 commit しないことを書く。§7.7 の fan-out/barrier は別 driver の契約なので継承しない（`docs/pegasus-runbook.md:1614–1633`）。

   関係する閉包は以下。

   | 検査／実装 | 本差分への影響 |
   |---|---|
   | `test_hooks.py:4523–4549` | `.sh`、shebang、実行 bit 等の再帰 inventory と registry が完全一致。２ entry 必須 |
   | `test_hooks.py:4580–4589`、`hooks/guard_bash.py:285–307` | sanctioned paths は registry から導出。手書き追加不要 |
   | `test_hooks.py:4467–4472` | fallback 投影は **非Pegasus** path 用。本件で変更不要 |
   | `test_ccbench_spawn_sites.py:847–899` | shell sink は `cmake --build`＋`--target`＋`ycsb_*`。今回 build しないので新 sink なし |
   | `test_codex_worker_launch.py:3747–3756` | registry bytes を HEAD blob に束縛。段6の子起動前に registry を commit |
   | `tools/check_codex_hooks.py:33–46` | registry/loader がコピー・pin 対象。script の個数表ではない |
   | `tools/check_docs.py:4489–4499,4602–4648` | runbook 投影集合一致。親の２行が必要 |

   `tools/pegasus/README.md` は `:22–26` の宣言表、`:42–54` の literal path／site tag 契約を持つ。本件を本文に追加しないため更新不要。変更ゼロとする。

   materializer を新設・呼出ししないので `materializer_admission.py` も変更不要。t2772 の２編集面と本計画の差分は重ならない。ただし親／author は着手直前の実編集面を再照合し、共有ファイルの変更が必要になった時点で先行可能という前提を取り下げる。

5. **契約 test `orchestrator/tests/test_floor_pair_job_contract.py`**

   fixture 不要の stdlib テストとし、`test_a5_second_boot_job_contract.py:593–612` 型の `_run()` / `__main__` を持たせる。全 `test_*` を列挙実行し、失敗は非0。allowlist は変更しない。要件は `test_plain_runner_coverage.py:25–41,60–86`、allowlist 正本は `orchestrator/tests/README.md:129–188`。

   | test 関数名 | 検査対象・殺す変異 |
   |---|---|
   | `test_registry_entries` | ２ entry の全field一致。class反転・登録漏れ |
   | `test_frozen_spec_pins` | submitter case、D2138 項7、実file SHA-256の三者一致。pin一桁変更 |
   | `test_pbs_and_walltime_binding` | PBS queue/project/nodes/signal、walltime一箇所、qsubとenvの同値伝播。時間の二重化・伝播漏れ |
   | `test_submitter_argument_set` | workload/mode/引数の閉集合、重複・不足・未知引数拒否。任意spec・時刻override追加 |
   | `test_window_id_and_fields` | workload＋窓から実在IDへ対応、`windows[].window_id` で選択。`w1`直渡し・別field参照 |
   | `test_window_gate_boundaries` | 項2の正例／負例を全窓で Bash snippet 実行。不等号反転・境界誤り |
   | `test_hostname_gate` | `bnode009`、FQDN正例、`pegasus02`、`bnode009evil` 負例。regex除去・prefix-only化 |
   | `test_gate_order_and_calls` | hostnameと時刻関数が定義だけでなくdriver前に呼ばれること。gate呼出し削除 |
   | `test_checkout_and_input_binding` | canonical root、detached、tracked-clean、HEAD、実file/HEAD blob SHA、binary確認。OID取り違え・検査脱落 |
   | `test_driver_argv` | isolated bootstrapと両mode argv、`--validate-only` 不在。測定mode差替え |
   | `test_evidence_and_receipts` | repo外root、leaf mkdir、noclobber/open-x、schema必須field、driver rc保存。truncate・偽rc |
   | `test_dry_run_has_no_execution` | dry-run分岐がqsubを呼ばず、driverを呼ぶ経路もない。dry-runから実投入 |
   | `test_no_build_or_output_replacement` | build、測定出力削除、retryが存在しない。既存campaign段の誤移植 |

   `_shell_function()` は `test_a5_second_boot_job_contract.py:59–62` の型を使う。実関数の文字列を切り出し、`bash -c` の位置引数で `now/not_before/not_after/duration` または hostname を渡す。実 qsub・実 driver・hostnameコマンドの偽装はしない。関数の正常／異常 rc と JSON `gate/reason` を検査する。

   driver argv は静的文字列の存在確認だけでなく、argv 構築部分を snippet で評価して配列要素を比較する。配列の読取りは `_shell_array()` の型（同 `:106–125`）を参考にする。isolated bootstrap は AST で `sys.path` 挿入→正規moduleの `main()` 呼出しを確認する。

   D2138 は repo 外の親job directoryへ依存せず、tracked `docs/decisions.md` の D2138 節から項7を抽出する。省略 `…` は同節の明示展開に従う。テストの期待値を submitter 自身からだけ生成しない。

6. **変異事前登録 M0〜M6**

   新規ファイルの行番号は author 後に確定する。事前登録では次の関数／literal を一意の変更対象とし、段4で exact diff に固定する。各変異は単独で適用・復元し、baseline成功を先に確認する。

   | ID | file・old → new | 殺す node／実行 | 期待 |
   |---|---|---|---|
   | M0 | `floor_pair_window.sh` の説明コメント `# Window admission` → `# Window admission gate` | 新規契約test全体 | **SURVIVED** |
   | M1 | registry の job entry `"class": "dispatch-required"` → `"class": "local-ok"` | `test_floor_pair_job_contract.py::test_registry_entries` | **KILLED** |
   | M2 | submitter rr95 pin の先頭 `990e…` → `890e…`（残りは同一） | `::test_frozen_spec_pins` | **KILLED** |
   | M3 | job `window_gate` の `now + duration <= not_after` → `now + duration < not_after` | `::test_window_gate_boundaries` の `now=not_after−duration` | **KILLED** |
   | M4 | job hostname関数の regex 判定を `:` に置換し、拒否側は残す | `::test_hostname_gate` の login／紛らわしいhostname負例 | **KILLED** |
   | M5 | job の `driver_argv+=(--execute-window "$FP_WINDOW_ID")` → `driver_argv+=(--validate-only "$FP_WINDOW_ID")` | `::test_driver_argv` | **KILLED** |
   | M6 | runbook §7.0 の新job body投影行 → 行削除 | 契約pytest層、その後 `python3.10 -B tools/check_docs.py` | pytest層 **SURVIVED**、直接checker **KILLED** |

   M3 は弱化だけでなく受理すべき境界を狭める変異を殺す。下限側は `not_before−1s/not_before` の両方をテストに残す。

   M6 は pytestが緑でも完了としない。`check_docs.py:4493–4499` の `registry_only` finding を、CLI直接実行の非0と併せて保存する。これは予測であり、本段での観測結果ではない。

7. **login 起動確認の手順**

   親が author差分・docs・registry を commit した後、その commit H の detached checkout を別途作る。これは本実装wave用fresh worktreeとは別の起動確認checkoutである。

   ```bash
   git worktree add --detach /work/1/SFC/tanab/izanagi-floor-pair-smoke HEAD
   cd /work/1/SFC/tanab/izanagi-floor-pair-smoke

   python3.10 -B -m orchestrator.campaign.b4_binary_record place \
     --record output/insights/2026-09-16/t2636-b4-binary-record/records/rr20--stock_common.json \
     --source-root /work/1/SFC/tanab/izanagi-b4-floor-binaries \
     --env-tag pegasus

   bash -n tools/pegasus/floor_pair_window.sh
   bash -n tools/pegasus/submit_floor_pair.sh

   bash tools/pegasus/submit_floor_pair.sh \
     --workload rr95 --window w1 --dry-run
   ```

   `bash -n` は各 rc=0。2026-09-18T01:47Z 相当なら dry-run は rc=4、`window/before_window`、qsub未実行。実行日が変われば現在時刻と期待判定を更新し、「今日は窓前」を恒久条件にしない。

   job body負対照は、新しい nonce と evidence leaf を作り、次の形で呼ぶ。`FP_EVIDENCE_DIR` は項3のbase直下、同じnonceの leafとする。

   ```bash
   FP_NONCE=$(python3.10 -I -B -c 'import secrets; print(secrets.token_hex(16))')
   FP_EXPECTED_HEAD=$(git rev-parse --verify HEAD^{commit})
   FP_EVIDENCE_DIR="/work/1/SFC/tanab/izanagi-job-evidence/floor-pair/$FP_NONCE"
   mkdir -p /work/1/SFC/tanab/izanagi-job-evidence/floor-pair
   mkdir -m 0700 "$FP_EVIDENCE_DIR"

   export FP_NONCE FP_EXPECTED_HEAD FP_EVIDENCE_DIR
   export FP_SPEC_RELPATH=output/env/pegasus/floor-pair/t2288-f1/spec__env-pegasus__protocol-silo__threads-48__workload-rr95-s0.9-rmw0__campaign-t2288-f1-rr95-c1c2.json
   export FP_SPEC_SHA256=990e3a6feb176ccf863315fde6e2afce43b7fc16053f50a1080641dde2570619
   export FP_MODE=window FP_WINDOW_ID=rr95-w1 FP_ELAPSTIM_REQ=10:00:00
   export PBS_JOBID="smoke-$FP_NONCE"
   export PBS_O_WORKDIR="$PWD"

   bash tools/pegasus/floor_pair_window.sh
   ```

   script自身まで到達すれば期待は rc=4、`site/compute_node_required`。scratch・driver・測定成果物は未作成。`PBS_JOBID` の設定で compute とみなすことはない（`site_policy.py:30–46`）。

   **起動確認の到達性には留保がある。** 新規pathはmain側登録簿で未登録、着地後もjob bodyは `dispatch-required` なので、login hookがscriptより先に拒否しうる（`V/F660.md:3–10`、`test_hooks.py:4433–4439`）。その場合は「hook拒否」と記録し、hostname gate到達を報告しない。絶対path・動的path・generic経由で迂回しない。契約snippetの負例と全job bodyの起動確認は別成果として扱う。

   親の検証commandは最低限以下。テストは正規runner経由とする。

   ```bash
   python3.10 tools/run_tests.py \
     orchestrator/tests/test_floor_pair_job_contract.py \
     orchestrator/tests/test_plain_runner_coverage.py \
     orchestrator/tests/test_ccbench_spawn_sites.py \
     orchestrator/tests/test_hooks.py

   python3.10 -B tools/check_codex_agents.py
   python3.10 -B tools/check_docs.py
   python3.10 -B tools/check_ai_provenance.py
   ```

   `test_codex_worker_launch.py::test_guard_bytes_mismatch_is_launch_error` も関連確認に含める。変異は対象nodeに絞ってrunner経由、M6はchecker直接実行。

   | 項目 | 今回観測するもの | 未観測のもの |
   |---|---|---|
   | bash構文 | 実ファイルの構文 | schedulerでの実行 |
   | submitter負例 | 実checkout・binary・実時計、到達できたgate | qsub受理・env伝播 |
   | job負例 | 模擬PBS値＋実login hostname、到達できたgate | compute正例 |
   | 窓正例 | 実spec＋注入epochで実関数 | 未来の実時計での投入 |
   | receipt契約 | schema・create-only・rc処理 | walltime切れ時の実配送・保存 |
   | 本走 | なし | run_window/finalize成功、床値採用 |

8. **P1・P2・P3・P6 の採否**

   | provisional | 判断・理由 |
   |---|---|
   | P1 | **採る。** １job＝１spec×１窓またはfinalize。６window＋３finalizeに分け、３段は同じdetached H・同じcheckoutで維持する。申し送り `V/t2288-a5-freeze-handover.md:6–9` に合う |
   | P2 | **時間値は採る。** window 10h、finalize 30mを運用上限とする。ただし成功時間の保証ではない。全rep timeoutの44.4hを覆わず、途中終了で窓を失いうる。保管場所はsubmitter一箇所へ変更 |
   | P3 | **採る。** finalizeもcompute jobのmodeとする。driver自体にlive gateがなくても入口を統一できる。summaryの再検証・exclusive createは `floor_pair_driver.py:2995–3011,3083–3087` に任せる |
   | P6 | **repo外rootは採る、所有記述は変更。** submitterとjobのファイル名を分離する。測定JSONL・summaryは凍結specどおりrepo内に残るので、repo全体がuntracked-freeになるとは説明しない |

9. **scope 外と完了境界**

   driver・issuer・verifier・凍結specは **0 byte変更**。`tools/pegasus/README.md` と tests READMEも変更しない。新規shell２本、契約test１本、registry２entry、親のrunbook差分で閉じる。

   実測・qsub・窓延長・再凍結・aggregate発行は行わない。job bodyに `--validate-only` を載せない。これは測定の代替ではない（`V/t2288-a5-freeze-handover.md:3–5`）。

   job rc=0を「床値生成成功」と読み替えない。driver CLI は window/finalize resultを書いた後に0を返し、結果の `status` は別に存在する（`floor_pair_driver.py:3132–3144,3063`）。n=62、欠測率、実campaign分離、採用は後続の証拠確認に残す。

## 親 brief への訂正

- **P5の `"$PY" -I -B -m orchestrator...`**  
  何が：isolated modeでcheckoutをmodule探索対象にできる前提。  
  正しくは：`-I -B -c` でcanonical repo rootを明示挿入し、正規driverの `main()` を呼ぶ。driverを変更しない。

- **P4/P5のwindow IDの粒度不足**  
  何が：CLIの `w1/w2` とdriverのIDが区別されていない。  
  正しくは：driverへ渡すのは `<workload>-w1/w2`。specの実fieldで選択する。

- **P5/P9のwalltime保持方法不足**  
  何が：mode別時間とPBS header literalを両立すると二重管理になりうる。  
  正しくは：値はsubmitter一箇所、`qsub -l` とenvへ同じ値を渡し、headerには置かない。

- **P6の所有記述の矛盾**  
  何が：同directoryへsubmit receiptを保存しながら「投入側はmkdir以外置かない」。  
  正しくは：directory内のファイル所有をsubmitter／scheduler／jobで分ける。

- **P5のhostname gateとsite evidenceの説明**  
  何が：prefix regexだけでは `bnode009evil` も通り、PBS envが証拠になるようにも読める。  
  正しくは：第一labelの完全一致を使う。`site_policy.py:33–46,66–84` はPBS envを分類条件に使わない。shell判定はdriver gateの代替ではない。

- **P5のsignal説明と起動確認の到達保証**  
  何が：「driverは殺さない」でwalltimeから保護できるかのような余地と、loginでは必ずhostname gateまで進む前提。  
  正しくは：shellから追加killしないだけで、schedulerによる終了は防げない。login起動はhookが先に拒否しうるため、実際の到達点を記録する。

## 総括

shell２本・契約test１本・registry２entry・親のrunbook差分で閉じる計画とする。  
P1/P2の時間値/P3/P6のrepo外rootは採用し、P5の起動argv・walltime配置とP6の所有記述を修正する。  
driverのgate・create-only・凍結specは変更せず、未来時刻の正例は契約snippetで確認する。  
残る不確定はlogin hook下での全script起動到達性と、後続waveでのみ確認できるPBS伝播・compute実行である。  
本段は静的読解のみで、テスト緑・起動成功・実測成功は主張しない。