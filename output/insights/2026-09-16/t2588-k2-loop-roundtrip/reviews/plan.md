## 1. role 入力の射影

**login では射影関数を直接呼ぶ。`--emit-planner-context` は使えない。** 以下の参照パスは指定 repo root 基準。

実行順は次で固定できる。

1. `knowledge_manifest.load_and_resolve_manifest(manifest_path, repo_root=repo_root)`
   定義は `orchestrator/campaign/knowledge_manifest.py:482`。commit の blob を読み、raw bytes の SHA-256 と UTF-8 を検査する。同ファイル `:428`、`:447`。web source は現実装で拒否する。
2. `knowledge_manifest.planner_projection(resolved)`
   定義は同ファイル `:490`。戻り値は `data_boundary`、`knowledge_level`、`knowledge_manifest_sha256`、本文 `content_utf8` を含む `sources`。source は正準順へ並べ直されるため、coder の `source_index` は**この射影後の配列**を指す。
3. `planner_context_payload(LoopState(), default_cfg(), knowledge_input=knowledge_input)`
   定義は `orchestrator/campaign/p3_s4_loop.py:1222`。戻り値は `whiteboard`、任意の `knowledge_input`、設定時だけ `policy_hint`。`current_perf` と `leading_indicators` は生成しない。

この直接呼び出し列には計測 site gate がない。`default_cfg()` 内の `build_run_context()` も計測を起動せず、site 判定を行わない。根拠は `p3_s4_loop.py:1486`、`orchestrator/campaign/build_admission.py:480`。

対して CLI は `p3_s4_loop.py:2678` で `_current_site()` → `_admit_env_contract()` を実行し、その後の `:2689` で初めて emit 分岐へ入る。`_admit_env_contract()` は `OTHER` / `PEGASUS_COMPUTE` だけを許すため、**`PEGASUS_LOGIN` では emit も `--no-build` も拒否される**。根拠は同ファイル `:133`、`:138`。site 判定は `orchestrator/campaign/site_policy.py:30` で、`pegasus01` 等と NQSV の存在から login を決める。PBS 環境変数で compute へ変わるものではない。

親が組み立てる JSON の分担は以下。

| 入力 | 生成元 |
|---|---|
| planner の `whiteboard` / `knowledge_input` | 上記 `planner_context_payload()` |
| planner の `current_perf` / `leading_indicators` | 親が測定値から射影。第6節参照 |
| coder の `knowledge_input` / `whiteboard` | planner と同じ射影 |
| coder の `planner_direction` | planner 出力の内側 `proposal` から `axis` / `direction` / `magnitude` / `justification` |
| coder の `baseline` | 親が選定した測定の `throughput_ops_sec` / `abort_rate_pct` |
| coder の `leakproof_context` | 親が既存の軸・文法・workload 制約を最小射影 |

**この driver に coder 入力全体や `leakproof_context` を作る factory はない。** 入力契約は `.claude/agents/coder-v4-autonomous-k2.md:54`、機械 schema は `.codex/role-adapters/coder-v4-autonomous-k2.json:99`。既存 K0/K1 向け知識禁止文の全文流用は同 role 本文 `:19` 以降の契約と合わない。

hole 条件の現物は `p3_s4_loop.py:125`、`backoff_hole_grammar.py:581`、workload は `p3_s4_loop.py:1565`。records=100000、threads=4、rr50、skew0.9、rmw=false、extime=1、reps=2 を射影する。

## 2. proposal file の受理形

入口は `orchestrator/campaign/p3_s4_loop.py:2254` の次の署名。

`load_proposal_file(path, *, knowledge_input=射影dict, coder_role="coder-v4-autonomous-k2") -> (PlannerProposal, CoderProposal, bool | None)`

K2 では次の全 key が必要になる。

| 階層 | 必須 key / 値域 |
|---|---|
| top | `planner`, `coder` |
| `planner` | `axis`, `direction`, `magnitude`。任意で `justification`, `uncertainty` |
| `coder` | `proposal`, `knowledge_use`, `classification`, `data_boundary_report` |
| `coder.proposal` | `axis`, `value`, `implementation`, `justification`, `confidence` |
| `knowledge_use[]` | `source_index`, `use` |
| `data_boundary_report` | `instruction_like_content_detected`, `details` |

top の任意 key は `prior_critic_reverse` と `auditor`。今回は auditor を付けない。K2 分岐の closed-schema 検査は coder proposal の検査後に return するため、任意 auditor の内側を検査する経路ではない。

根拠は `orchestrator/campaign/projection_guard.py:28`、`:44`、`:291`、`:324`。`CODER_CONTRACT_K2 = "k2-role-output"` は同ファイル `:36`。

内側の logical schema は `.codex/role-adapters/coder-v4-autonomous-k2.json:150`。`value` は整数1..1000、`confidence` は high/medium/low、`classification` は de_novo / known_result_conditioned_derivative / reproduction_or_selection。各 object は追加 key 禁止。`knowledge_use=[]` は許される。

検査順序と拒否署名は次のとおり。

1. JSON 読込。K2 指定時は重複 key を拒否する。`p3_s4_loop.py:2274`。
2. `knowledge_input` / `coder_role` の片指定、別 role 名を `ValueError` で拒否する。同 `:2309`。
3. `assert_closed_proposal_schema(..., require_auditor=False, require_coder_value=True, coder_contract=CODER_CONTRACT_K2)`。必須 key 欠落は `KeyError`、未知 key は `ValueError`。`projection_guard.py:269`、`p3_s4_loop.py:2319`。
4. `_consume_k2_coder_output(result, projected_input)`。まず role の output schema を検査し、次に `instruction_like_content_detected is True` を `ValueError` で拒否する。`p3_s4_loop.py:2226`。
5. `validate_output_semantics()` が軸・confidence・値域・完全 backoff 文法・value/literal 一致を検査し、その後 source index を検査する。bool、非整数、範囲外、重複 index は `RolePolicyError`。`orchestrator/codex_roles/policy.py:487`、`:521`。
6. proposal 型の構築、`prior_critic_reverse` の bool/null 検査、禁止素材検査。同 `p3_s4_loop.py:2356` 以降。

保存するのは **planner の内側 `proposal` と、coder の K2 envelope 全体**。`knowledge_use`、`classification`、`data_boundary_report` を親が補筆・修正してはならない。初回の `prior_critic_reverse` は親が `null` とする。

親の `--knowledge-classification=known_result_conditioned_derivative` / `--knowledge-de-novo-claim=false` は別の宣言で、受領証の `claim_boundary` に入る。coder 自己申告との一致を強制するものではない。根拠は `p3_s4_loop.py:2577`、`knowledge_manifest.py:509`、`:567`。

なお、role 本文は `knowledge_use[].use` を非空と要求するが、現 logical schema は string 型のみで、上記 semantic consumer に非空検査はない。本文の要求と機械検査の強さを同一視しない。

## 3. 投入前に login で通せる production 検査

qsub 前の呼び出しを次の順にする。すべて既存関数で、計測 site gate を呼ばない。

| 呼び出し | 引数 | 戻り・失敗 |
|---|---|---|
| `assert_closed_proposal_schema()` | proposal document、`require_auditor=False`、`require_coder_value=True`、`coder_contract=CODER_CONTRACT_K2` | 成功 `None`。欠落・未知 key 等は例外 |
| `validate_backoff_preflight()` | `document["coder"]["proposal"]["implementation"]` | `BackoffGrammarDecision` |
| `load_proposal_file()` | 保存した proposal-1 path、検証済み `knowledge_input`、K2 role 名 | 型付き planner/coder/prior、または第2節の拒否 |

定義は `projection_guard.py:291`、`backoff_hole_grammar.py:186`、`p3_s4_loop.py:2254`。

**preflight は完全な文法検査ではない。** exact str、UTF-8 化、4096 bytes 以下だけを調べる。結果は `accepted` / `stage` / `rule_id` / `reason` を持つ。同ファイル `:49`、`:54`、`:186`。完全文法と literal 整合は K2 loader の semantic consumer まで通して確認する。

これらの成功を、計算ノード上の diff/effect 検疫・verifier 通過と記録しない。正規実走の帰属・検疫順序は `p3_s4_loop.py:1645`、`:1801` 以降に残す。

## 4. job body への引数

投入前に親が用意するのは、新規の専用 submit-tree、固定40桁 HEAD、repo 外の新規 evidence directory、proposal-1、manifest、hydrate の `source_root`。

既存準備 CLI は次の形。

- `python3 -B tools/dev_wave_submodule_init.py --worktree <submit-tree絶対path>`
  `tools/dev_wave_submodule_init.py:43`。登録済み worktree の解決を経て no-fetch 初期化するため、任意 directory で成功するとは扱わない。
- `python3 -B tools/pegasus/fetch_third_party.py hydrate --repo-root <submit-tree> --cache-root /work/1/SFC/tanab/izanagi-thirdparty-cache`
  `tools/pegasus/fetch_third_party.py:697`、`:739`。job に渡すのは出力 JSON の `.source_root`（`:760`）。

`tools/pegasus/p3_s4_loop_pegasus.sh:17` の必須環境変数は、scheduler 側の `PBS_JOBID` / `PBS_NODEFILE` / `PBS_O_WORKDIR` と、親が渡す以下4個。

- `IZANAGI_S4_REPO_ROOT`
- `IZANAGI_S4_EXPECTED_HEAD`
- `IZANAGI_S4_EVIDENCE_ROOT`
- `IZANAGI_S4_THIRDPARTY_SOURCE_ROOT`

K2 用には次を追加する。

| 環境変数 | 本 wave の値 |
|---|---|
| `IZANAGI_S4_PROPOSAL_PATH` | 新規 proposal-1 の絶対path |
| `IZANAGI_S4_KNOWLEDGE_MANIFEST` | 指定 wal-only manifest の絶対path |
| `IZANAGI_S4_CODER_ROLE` | `coder-v4-autonomous-k2` |
| `IZANAGI_S4_KNOWLEDGE_CLASSIFICATION` | `known_result_conditioned_derivative` |
| `IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM` | `false` |

**all-or-none 対は manifest と coder role。** ただし実装は classification / de-novo を含む4変数のどれかが「設定済み」なら K2 mode を要求する。宣言だけの設定でも manifest・role・proposal が必要になる。設定済み空文字も拒否する。任意の宣言2個は互いの all-or-none 対ではない。根拠は shell `:54`〜`:96`。

shell の明示 rc=2 条件は以下。`refuse()` 自体は `:12`。

| 条件群 | shell の行 |
|---|---|
| 必須 env 欠落・空、bnode 以外 | `:17`, `:26` |
| K2 の片指定・空値・proposal 欠落 | `:54`, `:73` |
| repo/evidence/依存 root の不在・symlink・解決不能 | `:99` |
| AI worktree container 内 repo、git common dir 解決不備、repo/common-repo 内 evidence | `:116`, `:121`, `:125` |
| compute-result 既存、終了時一時file既存・公開失敗 | `:131`, `:138` |
| import 可能な Python 3.10 不在、interpreter hash 不備 | `:159`, `:185` |
| scratch 非新規、shim 内容不正 | `:188`, `:202` |
| expected HEAD の形式・一致・tracked clean 不備 | `:214` |
| CCBench root・pin 解決・一致・tracked clean 不備 | `:228`〜`:258` |
| qstat 証拠既存、reservation 抽出不備、script/boot ID 不備、reservation 既存 | `:260`, `:294`, `:300`, `:308`, `:322` |
| claim root、policy file・抽出件数の不備 | `:363`, `:369`, `:398` |
| gflags/glog の不在・HEAD不一致・dirty | `:410`, `:437` |
| third-party 各 source の不在・symlink・HEAD形式・tracked clean 不備 | `:472` |
| scratch masstree の config.h 既存、prebuild receipt 既存 | `:500`, `:504` |

通常コマンドや Python helper の失敗は生の非zero rc もあり、すべてが rc=2 ではない。

qsub は README `tools/pegasus/README.md:386` の9変数と `-o` / `-e` を使い、**固定 submit-tree 内の job body**を1回投入する。job は `:581` で次を呼ぶ。

`python -B -m orchestrator.campaign.p3_s4_loop --allow-coder-derived-build --isolate-worktree --fetchcontent-prebuild-receipt <receipt> <K2引数> --run-iteration <proposal-1>`

README §7 の正例は shell と整合する。ただし次の記述差がある。

- 任意宣言だけでも K2 必須対を要求する点は、README `:354` の説明より shell の条件が明確。
- README `:368` は primary worktree と「あらゆる repo 内 evidence」を運用上禁止するが、shell の直接検査は AI container と当該 repo/common-repo に限られる。専用 tree・全 repo 外 evidence という運用は維持する。
- README `:394` の「事前構築は消費されない」は、receipt が候補 build に使われないという意味。**job body の事前構築自体は driver より先に実行される**（shell `:539` → `:581`）。

## 5. 走行後の digest

campaign directory の形は次。

`<submit-tree>/output/exploration/campaigns/<campaign-id>/`

本 wave の予定 submit-tree なら、

`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2588-k2-loop-roundtrip/submit-tree/output/exploration/campaigns/<campaign-id>/`

となる。ID は当該走の stdout / lock から読む。根拠は `orchestrator/campaign/layout.py:589`。job が外部 output-root env を unset するため（shell `:39`）、既定 repo output に置かれる（`layout.py:384`）。

読み出す原本は以下。

- `runs/wal.jsonl`：`layout.py:558`
- `campaign.lock`：同 `:546`
- `loop_state.json`：`p3_s4_loop.py:1301`
- `s4_loop_digest.txt`：同 `:2523`
- repo 外 evidence の `compute-result.json`、stdout/stderr、reservation、prebuild receipt

driver は `p3_s4_loop.py:2512` で admitted view を取得し、`make_critic_digest()` と identity projection を使って digest を保存する。`make_critic_digest(view, tag="p3-s4", reflux=True, *, identity_projection) -> str` の定義は同 `:1141`。緑の committed LI と赤の構造化診断を結合する。

**digest は login でも生成可能。** 固定 submit-tree のコードから次の既存 CLI を呼べる。

`python3 -B -m orchestrator.critic.digest --campaign-dir <campaign-root> --tag p3-s4`

根拠は `orchestrator/critic/digest.py:1620`。渡すのは `runs/` ではなく campaign root。CLI は `:1631` で artifact admission を要求するが、計測 site gate は呼ばない。reader は `orchestrator/campaign/artifact_admission.py:1472` の admission・verifier epoch・persisted commit 検査を行う。**login であることは拒否理由ではないが、artifact 不適合なら拒否される。**

既存 `s4_loop_digest.txt` を優先して critic に渡す。再生成 CLI は screen rejection も含めるため、harness の出力と常に同一 bytes とは扱わない（`digest.py:1642`）。

## 6. proposal-2 の入力

緑の入力は **同じ variant・同じ committed attempt に属する `bench_done`** から取る。単に WAL の最終 bench 行を拾わない。既存 reader の対応付けは `orchestrator/critic/digest.py:735`、特に `:762` の `committed_bench`。

`bench_done.payload.leading_indicators` の writer は `orchestrator/campaign/pipeline.py:1455`、WAL emit は `:1516`。

| role 入力 | WAL の field | 変換 |
|---|---|---|
| `current_perf.throughput_ops_sec` | `bench_done.payload.leading_indicators.throughput_tps` | そのまま。現 role 名への写像 |
| `current_perf.abort_rate_pct` | 同 `.abort_rate` | 非nullなら100倍 |
| `current_perf.last_delta_pct` | 対応する WAL field なし | `null` |
| `leading_indicators.cache_miss_rate_pct` | 同 `.llc_miss_rate` | 非nullなら100倍 |
| `leading_indicators.IPC_overall` | 同 `.ipc` | そのまま |
| `leading_indicators.contention_level` | 対応する WAL field なし | `"未判定"` |

単位の現物は `orchestrator/calibrator/model.py:89`。throughput は反復の中央値（`:83`）、LLC miss は misses/loads（`:38`）、IPC は instructions/cycles（`:47`）。abort は aborts/(commits+aborts) で、parser の fallback 計算も同じ（`orchestrator/calibrator/benchparse.py:82`）。abort/cache/IPC は代表 rep の値を採用する経路で、全repの率平均とは限らない（`orchestrator/calibrator/runner.py:1050`）。

`last_delta_pct` を歴史 baseline との比から新しく捏造しない。段4の whiteboard delta は未算出で `None`、成功時もそう記録される（`p3_s4_loop.py:1311`、`:1964`）。`contention_level` の分類器もこの経路にはない。

親の還流順は次。

1. verdict と commit/abort を確認し、緑の場合だけ上の測定値を更新する。
2. critic に当該 digest を渡し、診断逐語を保存する。
3. `load_loop_state(layout)`（`p3_s4_loop.py:1410`）→ `planner_context_payload()` で実走後 whiteboard を作る。5 field と delta=null 制約を保つ。
4. 更新した測定入力で planner-2 を起動し、その方向と baseline、同じ knowledge projection、whiteboard で coder-2 を起動する。
5. proposal-2 を第2節の形式で保存し、評価しない。

赤なら新しい throughput 等が存在しない場合がある。赤の性能を推定せず、維持する過去値には出所と「今回の実測ではない」ことを付ける。停止条件が成立した場合は継続生成を成功として扱わない。

`prior_critic_reverse` の機械 consumer は `_fold_critic_reverse()`（`p3_s4_loop.py:2213`）。True は連続回数を加算、False は0へ戻し、None は不変。`drive_iteration()` の `:2486` で畳み込み、`:2488` で入口停止判定する。停止判定本体は `:1253`、reverse 判定は `:1281` 付近。

**この bool は planner/coder の方向生成器へ渡されない。** `planner_context_payload()` は reverse counter を射影しない。本 wave は proposal-2 を評価しないため、その file に保存した bool は次の `drive_iteration()` にまだ消費されない。critic の解釈を記録したことと、機械的な次評価への適用を分けて報告する。

## 7. 1 投入で skip されない条件

`run_campaign()` の recovery 判定は `orchestrator/campaign/loop.py:574`。

- 当該 layout の WAL を replay（`:579`）
- terminal variant 集合を取得（`:589`）
- retryable abort を除外（`:597`）
- `done` を初期化（`:610`）
- 解決した `variant_id(g, src_tok)` が `done` にあれば skip（`:695`）

したがって、**過去 WAL・checkpoint を持ち込まない新規 submit-tree の新規 campaign directory なら、過去 terminal による skip は起きない。** 別の新規 campaign identity でも同様。ただし gate 拒否・入口停止・build failure が起きないという保証ではない。

**新規 submit-tree は、新しい campaign ID を自動生成しない。** 同じ設定なら文字列 ID は同じになり得る。新しい実行を識別するには submit-tree、固定実行commit、request、evidence root を記録する。ID を変えるために設定を変更する必要はない。

identity の現物は `orchestrator/campaign/ident.py:196`。正準 JSON の5 key は以下で、SHA-256先頭8桁を ID に使う（`:226`、`:232`）。

| identity 要素 | 束縛位置 |
|---|---|
| `spec_content` / `search_tag` / `trial` | `p3_s4_loop.py:1505` |
| `ccbench_commit` | 同 `:1512`、値は `PIN`（`:112`） |
| scale、axis、reflux、records、threads、grammar version | 同 `:1495` の `search_config` |
| build admission policy | 同 `:1517`、`ident.py:91` |
| `knowledge_level` / `knowledge_manifest_sha256` | `p3_s4_loop.py:1548` |
| Pegasus の `measurement_env="pegasus"` | 同 `:147` |

raw `env_tag`、日付、実測値、superproject HEAD、submit-tree path、proposal の選択値は、この5-key identity に直接は入らない。環境契約は別途束縛されるが、raw env tag と identity 内の `measurement_env` を混同しない（`ident.py:100`、`:201`）。

## 総括

親の実行順は、**login で manifest 解決・直接射影 → planner/coder 各1回 → K2 envelope 保存・既存検査 → 新規専用 tree から qsub 1本 → WAL・停止結果・digest 確認 → critic 1回 → 更新入力で proposal-2 保存**で固定できる。

注意点は、emit CLI は login 不可、K2自己申告の代筆不可、率は100倍、delta/競合分類は未実装、新規 tree と新規 ID は別、という6点。編集・テスト・role 起動・qsub は実施していない。実投入の成立と terminal 取得は未確認であり、緑とは記録しない。