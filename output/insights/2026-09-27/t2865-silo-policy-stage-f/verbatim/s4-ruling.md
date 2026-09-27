# 段 4 裁定 — [T-2865] 段階 F (2026-09-27)

入力: brief.md、codex/s2-plan.md、codex/s3-consult-A.md (正しさ境界、must-fix 2・should-fix 3・nit 1)、codex/s3-consult-B.md (過剰・削除、must-fix 3・should-fix 3・nit 1)。wave 開始後の local main の進み・新裁定は 0 件 (段 4 直前に `git log ad114fba0..main` 空を確認)。

## 所見の裁定

| 所見 | 判定 | 採否 | 扱い |
|---|---|---|---|
| A1 / B2 既存の呼出し数検査が `p3_s4_loop_policy` を `p3_s4_loop` の接頭辞として数える | real | 採用 | 単位 B: 既存検査の照合を module 名の境界まで exact にする。既存の期待件数 (p3_s4_loop 2・B-5 1) は変えない。方策 driver は別の件数・順序検査 |
| A2 pair の候補が例外で終わると iteration は進むが履歴に行が無い | real | 採用 | 単位 A: `drive_iteration` で評価が例外なら履歴に `eval-exception` の行を足してから再送出 (閉じた reason code は既存)。pair は例外でも stock を試み、最後に候補の例外を再送出 (rc≠0)。成立判定は両 attempt の WAL |
| A3 login と計算ノードで同じ campaign の証明 | real | 採用 | 単位 A: `--campaign-env {linux-baremetal,pegasus}` (既定 linux-baremetal = 現行 identity 不変)。計測する操作 (stock・pair・replay・run) は解決 site の env tag と一致しなければ拒否。emit・preview・record-reject は指定値で campaign を組む。両側の `ident.campaign_id` 一致を実 `default_cfg` で test |
| A4 / B1 共有 campaign base と複数 checkout | real (B の代案) | 採用 | 共有 base・`IZANAGI_EXPLORATION_OUTPUT_ROOT` の再設定は作らない。AI worktree 容器外の submit checkout 1 本で stock job・login 側操作・pair job を直列に行う (runbook に「同一 campaign の操作は直列」と明記) |
| A5 D2212 項 4 の「検査込み」は親の解釈 | real | 採用 | 記録で「実験 job 合計へのユーザー裁定」と「開発検査を足す親の保守的運用」を分けて書く |
| A6 / 変異の単一理由性 | real | 採用 | 変異は下表で到達 gate を固定し、実装後に単一理由性を確かめて登録を確定 (DW-M01) |
| B3 login の record-reject で walltime 起点が早まる | real | 採用 (手順のみ) | コードは変えない (停止条件は D2256 項 3 の予算、`MAX_WALLTIME_S` は D39 の凍結値)。runbook に「投入前に loop_state の残り walltime を確かめ、足りなければ停止として記録」を足す |
| B4 `--purpose` 新設と必須 R2 run id は不要 | real | 採用 | search_config に `evaluation_purpose` key を bootstrap・r2 のときだけ焼く (loop は key なし = 既存 identity 不変)。run id は置かない (同一候補の複数回 R2 は後で必要になったとき) |
| B5 R2 は job mode が要る、replay-pair は不要 | real | 採用 | job mode は `stock|pair|replay` の 3 値 |
| B6 test・変異の削減 | real | 採用 | 下表の最小集合。stock への coder authority 変異と前処理順序の独立 test は削る |
| B7 台帳 entry の説明更新 | nit | 不採用 | 台帳は変えない。README と runbook だけ親が更新 |
| plan P2 bootstrap の別 campaign | real (A・B とも支持) | 採用 | 初回 stock は `evaluation_purpose=bootstrap` の campaign、pair の stock は loop campaign (同一 variant の terminal skip を避ける、`loop.py:770–885`) |

## plan v2 (確定)

**単位 A (所有: `orchestrator/campaign/p3_s4_loop_policy.py`、`orchestrator/tests/test_p3_s4_loop_policy.py`)**

1. `default_cfg(*, form, reflux=True, campaign_env='linux-baremetal', evaluation_purpose=None)`。`campaign_env='pegasus'` は `L._campaign_cfg_for_site` と同じ形 (`measurement_env` marker + `pegasus` 契約の束縛) で identity を作る。`evaluation_purpose in {None,'bootstrap','r2'}`、None のときは key を焼かない。既存の `linux-baremetal` の campaign id は不変。
2. 計測する操作は `L._current_site()` → `L._admit_env_contract()` で契約を得て、`campaign_env` が契約の env tag と一致しなければ拒否。`run_campaign` へ契約の `env_tag`・`clocks_per_us`・`numactl`・`authorization_contract`、`env_contract`、`dependency_prefix` (p3_s4_loop と同じ取り方)、`--fetchcontent-prebuild-receipt` (`L._load_masstree_prebuild_receipt` の 5 値) を渡す。`p3_s4_loop.py` は編集しない。
3. stock: genome = `BASE` から `axis.FLAG` を除いた flag、pin の原型 source (方策 template patch なし)、`build_run_context(generator_id=BACKOFF_SWEEP)` (coder authority なし) と `L._stock_capability_resolver`。LoopState と `policy_history.jsonl` は動かさない。出力 JSON = `outcome`・`variant`・`fitness_tps`・`abort_rate_pct` (同じ attempt の BENCH_DONE `leading_indicators.abort_rate` × 100、欠損は null)・`verdict`。
4. CLI: `--stock-baseline` (bootstrap campaign で stock 単独)、`--run-iteration P [--stock-control]` (loop campaign、候補 → 同じ authorization session で stock)、`--replay-proposal P` (r2 campaign、保存 `{coder,auditor}` を共有 gate (検疫・構文・単独 TU・auditor digest 照合と veto・書込後 digest 再照合) に通して評価、LoopState・履歴は作らない)。候補系 (`--run-iteration`・`--replay-proposal`) の build は `--allow-coder-derived-build` 必須。
5. `drive_iteration`: 評価が例外なら `eval-exception` の履歴行を足して再送出。
6. test (最小): 実 source の stock 分類と stock genome の flag、同じ attempt の WAL からの baseline (× 100)、pair の順序と session と stock context の分離、login (`pegasus` 指定) と計算側の campaign id 一致・`linux-baremetal` / bootstrap / r2 との不一致、replay の gate 再照合と loop 非進行、候補例外の履歴行、campaign env と site の不一致拒否。

**単位 B (所有: `tools/pegasus/p3_s4_loop_pegasus.sh`、`orchestrator/tests/test_p3_s4_loop_job_contract.py`)**

1. `IZANAGI_S4_POLICY_MODE=stock|pair|replay`、`IZANAGI_S4_POLICY_FORM=cpp|ir`、`IZANAGI_S4_POLICY_PROPOSAL_PATH` (pair・replay で必須、stock で禁止)。方策 mode は T-2849・B-5・K2・`IZANAGI_S4_PROPOSAL_PATH`・fixture・`IZANAGI_S4_STOCK_CONTROL` の env と排他 (repository 解決前に rc=2)。方策 env は方策 mode 無しでは拒否。
2. 方策 mode では `IZANAGI_TRACE_ARCHIVE_ROOT` を必須 (絶対 path、repo と git common repo の外、`realpath -m` で解決) にし、driver 起動前に検査。他 mode の挙動は不変。
3. pin: 方策 mode では `axis_silo_function_policy.PIN` を CCBench で `rev-parse --verify '<pin>^{commit}'` して 40 桁へ解決し、HEAD と比較。他 mode は現行のまま。`resolve_python` は方策 mode のときだけ方策 module の import も確かめる。
4. driver 起動 (前処理・receipt の後): `IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"` を export し、`"$PY" -B -m orchestrator.campaign.p3_s4_loop_policy --form "$FORM" --campaign-env pegasus --fetchcontent-prebuild-receipt "$prebuild_receipt"` に mode 別引数 (stock: `--stock-baseline`、pair: `--allow-coder-derived-build --run-iteration P --stock-control`、replay: `--allow-coder-derived-build --replay-proposal P`) を足して 1 回だけ呼び、rc を job の rc にする。
5. 契約 test: 既存の呼出し数照合を exact にする (期待件数不変)、方策 mode の実 shell argv・env (保全 root・bench lock・receipt)・pin、排他と保全 root の拒否、方策 driver の 1 回起動。

**親**: runbook (§0.2・§1 共通引数・§1(f)・stock・R2・保全・直列運用・walltime 確認)、`tools/pegasus/README.md` の方策 mode の qsub 例。台帳は変えない。

## 変異の事前登録 (実装後に到達 gate と単一理由性を確かめて確定)

| id | 壊す箇所 | 期待して落ちる test |
|---|---|---|
| M-F1 | 方策 driver の stock genome に `axis.FLAG: 1` を残す | A: stock genome の flag test |
| M-F2 | stock baseline の `× 100` を落とす | A: 同じ attempt の baseline test |
| M-F3 | stock baseline が別 attempt (最後の BENCH_DONE) を読む | A: 同じ attempt の baseline test |
| M-F4 | `--replay-proposal` が `drive_iteration` を通る (loop を進める) | A: replay の loop 非進行 test |
| M-F5 | replay で auditor を None にして gate へ渡す (digest 照合を抜く) | A: replay の gate 再照合 test |
| M-F6 | `campaign_env='pegasus'` で `measurement_env` marker を焼かない | A: campaign id 一致 test |
| M-F7 | job body の方策 mode の pin を `p3_s4_loop.PIN` に戻す | B: 方策 mode の pin test |
| M-F8 | job body の保全 root の必須検査を消す | B: 保全 root 拒否 test |

## 計算の見積り (現時点、E2E 投入前に実測で更新)

実験 job: stock 単独 1 + pair 1 (+ preview 拒否時の再試行は計算ノード不要)。1 評価の固有費 217〜509 秒 (B-5 試走)、前処理込みの job Elapse は未実測 → stock job の Elapse を単価にして pair を見積もる。実験 job 合計の目安 0.4〜0.7 node 時間。開発の検査 (焦点走 2〜3 回・変異 8 本・受入 2 回) は段階 E の実測 (焦点走 466 秒、変異 16 本 2,544 秒、受入 3 shard 約 1,070 秒/回) から約 1.2〜1.5 node 時間。合計が 2 node 時間に届くかは E2E 投入直前に実測値で確定し、届くならユーザーに確認する (実験 job の合計はユーザー裁定の線、検査を足すのは親の保守的運用)。
