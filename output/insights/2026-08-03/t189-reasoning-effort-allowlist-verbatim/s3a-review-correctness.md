静的検査の判定は **NO-GO**。pytest は実行しておらず、テストを緑とは報告しない。

### 平坦な Codex 許可集合は既知の有効組を拒否し、既知の非対応組を通す

- **深刻度:** blocker
- **根拠:** `brief.md:51-53` は `gpt-5.4-mini` が `none` を受理し `max` を拒否すると記録している。現行 launcher は model を制限せず reasoning も任意文字列である (`tools/codex_worker_launch.py:2474-2475`)。プランは model を見ず `none` を除外し `max` を含める (`s2-plan.md:31-37,44-46`)。その値はそのまま `-m <model> -c model_reasoning_effort="<reasoning>"` になる (`tools/codex_worker_launch.py:1097-1105`)。
- **失敗シナリオ:** 現在 product-valid な `run --model gpt-5.4-mini --reasoning none` は変更後 argparse rc=2 になる。一方 `--model gpt-5.4-mini --reasoning max` は新 gate を通過して Codex を起動し、そこで初めて拒否される。つまり有効組を落とし、既知の非対応組を admission する。
- **成果物影響:** certified 選択候補から有効な `mini/none` が消える一方、材料レポート／試行台帳には非対応な `mini/max` の失敗 session・requested 値が残り、比較母集団が歪む。

「repo で未使用」は capability 不正の根拠ではない。model-aware map を入れるか、「製品 capability」ではなく明示裁定された repo policy として `none` 禁止を確定する必要がある。

### 新しい正本が supervisor digest の閉包外に置かれ、F30 型の trust-root 漏れを作る

- **深刻度:** blocker
- **根拠:** 正本は `orchestrator/codex_roles/effort_levels.py` に新設する計画 (`s2-plan.md:9-15`) だが、`_supervisor_digest()` が hash するのは `tools/dev_waves/` 直下の `.py/.json` だけである (`tools/dev_waves/daemon.py:179-186`)。この digest は run manifest と wave context に記録され (`tools/dev_waves/daemon.py:733-737,1211-1217`)、checker は before/after の等号で trust-root pass を出す (`tools/dev_waves/checker.py:626-631`)。Git 側 trust root も check scripts・task_runs・tests に限定され、新 leaf を含まない (`tools/dev_waves/git_state.py:801-830`)。さらに submodule import でも package の `__init__.py` が `spec` / `policy` を実行する (`orchestrator/codex_roles/__init__.py:3-7`)。
- **失敗シナリオ:** run 作成後に `effort_levels.py` の集合を変更して daemon を再起動する、または wave が同ファイルを変更して land する。次のプロセスでは受理集合が変わるが `_supervisor_digest()` は同値のままで、checker は `trust-root=pass` を返せる。
- **成果物影響:** 試行台帳／run manifest の `supervisor_code_sha256` が同じ参照値のまま受理集合だけ変わり、将来 real 開放後は異なる gate で certified 選択した成果物を同一 supervisor と誤認証する。

M9 の「receipt schema digest は動かない」は `schema_vN.json` に限れば正しい (`tools/dev_waves/receipt.py:106-121`)。しかし `schema.py` 自体は既に directory digest の入力であり、正本 leaf をその閉包外へ出す案は不可。正本を hash 対象内に置くか、外部 leaf と package 初期化依存を明示的に digest へ加え、変異テストを追加すべきである。

### 必須の F56 限界 insight が実装所有から脱落している

- **深刻度:** must-fix
- **根拠:** brief は `max` と F56 の限界を記録した insight を必須成果物とする (`brief.md:33-36`)。しかしプランの所有単位にはコードとテストしかなく、insight の path・内容・担当がない (`s2-plan.md:129-137`)。receipt は要求された model/reasoning をそのまま記録する (`tools/codex_worker_launch.py:1400-1405`)。過去 receipt の reasoning は non-empty string しか要求されず (`tools/codex_worker_launch.py:1983-1985`)、`check-receipt --expect-reasoning` も unrestricted である (`tools/codex_worker_launch.py:2512-2513`)。
- **失敗シナリオ:** 過去の `reasoning=ultra` receipt、raw DW-O01 起動、または新 gate を通った `mini/max` の requested 値を、後続レビューが「値域検査済みの実効構成」と読む。コードだけでは model compatibility・served identity・historical receipt が非保証だと成果物に残らない。
- **成果物影響:** 材料レポートが requested 値を served identity の attest と誤読し、汚染された receipt を certified 選択の参照根拠へ再利用できる。

### 正例が `high` と `max` だけで、5 値の受理集合を固定できない

- **深刻度:** must-fix
- **根拠:** 面1は既存既定 `high` と追加 `max`、面2・3も追加正例は `max` だけである (`s2-plan.md:143-167`)。既存 argv test も `--effort=high` のみ (`orchestrator/tests/test_dev_waves_schema.py:233-249`)。
- **失敗シナリオ:** 実装時または将来変更で正本が `("high", "max")` だけになっても、計画済みの `none` 負例、`high` 既存例、`max` 新規例はすべて通る。`low` / `medium` / `xhigh` の拒否を検出できない。
- **成果物影響:** 正当と宣言した arm が試行台帳へ入る前に落ち、材料レポートと certified 選択の候補集合が無言で狭まる。

F27 型の既存期待弱体化は見当たらない。F28 についても `none` は現行 `_EFFORT_RE` を通るため、追加 membership gate の単独検出に帰属できる (`tools/dev_waves/schema.py:801,832-854`)。ただし全正例を parameterize しなければ、受理集合の縮小を緑で隠せる。M10 は「3 対象面に well-formed unknown のテストがない」と狭く言えば正しいが、role policy や child argv grammar の既存検査まで含めて「関連テスト 0 件」は過大である (`orchestrator/tests/test_codex_agents.py:406-436`, `orchestrator/tests/test_dev_waves_schema.py:243-255`)。

### task-runs は任意 reasoning を記録できるため、別裁定なしに全台帳を検査済みとは言えない

- **深刻度:** must-fix
- **根拠:** `agent_run --reasoning` は choices なし (`tools/task_runs/cli.py:76-84`) で、そのまま event に入る (`tools/task_runs/cli.py:138-155`)。schema は一般 slug 形しか検査しない (`tools/task_runs/schema.py:425-430`)。一方 authority は `development-observation-not-evidence` 固定 (`tools/task_runs/schema.py:300-305`) で、集計 cohort key も reasoning を含めない (`tools/task_runs/aggregate.py:382-410`)。
- **失敗シナリオ:** `agent_run --product codex --model gpt-5.6-sol --reasoning ultra ...` が正常な ledger event として受理される。3 面の gate を実装してもこの試行台帳値は変わらない。
- **成果物影響:** 試行台帳の reasoning 受理集合には引き続き `ultra` 等が入る。ただし現行 authority と集計では certified 選択・材料 cohort へ直結しない。

これは T-189 へ無条件に gate を足すべきという意味ではない。失敗した raw 起動も記録する観測台帳なら、拒否より `requested_reasoning` と validity の分離が妥当である。段4の裁定パッケージへ必ず残すべき層である。

### 永続 profile 経路は child を止めるが、不正値を含む wave artifact を先に作る

- **深刻度:** nit
- **根拠:** `parse_server_profile()` と `SupervisorProfile` は effort を non-empty ASCII としか検査しない (`tools/dev_waves/cli.py:244-251`, `tools/dev_waves/daemon.py:219-229`)。daemon は worktree・WAL・manifest・prompt・worker spec・context を作った後 (`tools/dev_waves/daemon.py:1143-1218`)、`build_child_argv()` で初めて値域検査へ到達する (`tools/dev_waves/daemon.py:1223-1232`, `tools/dev_waves/worker.py:231-251`)。例外は通常 terminal FAILED に畳まれる (`tools/dev_waves/daemon.py:863-887`)。
- **失敗シナリオ:** 改竄された `server-profile.json` の `effort=none`、または programmatic `SupervisorProfile(..., effort="none")` で submit すると、worker spec に `none` が保存された後で child spawn が拒否される。
- **成果物影響:** certified 選択は発生しないが、試行台帳には `FAILED` wave と `effort=none` の spec、作成済み worktree が残る。

したがって child への fail-closed は成立するが、「不正値は artifact に一切入らない」は成立しない。後者も要求するなら profile 構築・復元時に早期検査が必要である。

### M1 は documented vocabulary の根拠であり、Claude の実受理集合の実測ではない

- **深刻度:** nit
- **根拠:** 一次資料が確認したのは help の5値列挙と `bogus` 一例だけであり、`bogus` 自体は警告後 rc=0 で既定値へ fallback する (`output/insights/2026-08-01_token-hygiene-audit/probes/cli-effort-failopen.md:3-9,18-29`)。
- **失敗シナリオ:** `none`、`HIGH`、前後空白について、Claude が拒否・正規化・fallback のどれを行うかは実測されていない。新 wrapper はいずれも exact choices で拒否するが、それを「Claude 実受理集合と一致」とは言えない。
- **成果物影響:** 現在の certified 選択値は変わらないが、材料レポートで「CLI capability」「documented supported token」「Izanagi policy」を同一視すると受理集合の由来を誤記する。

## 成立しなかった攻撃

- 面1の通常 CLI 経路では、値の組み直しはなく `args.reasoning` がそのまま一つの `-c` token になり、`shell=False` で起動される (`tools/codex_worker_launch.py:1097-1112,1158-1168`)。`CODEX_HOME` を wrapper が読むのは sessions root の決定だけ (`tools/codex_worker_launch.py:2572-2578`)。rollout の recorded effort が要求値と異なれば evidence は不一致になる (`tools/codex_worker_launch.py:750-777`)。
- argparse は artifact 作成より前である。面1は `parse_args()` が `_run()` 外 (`tools/codex_worker_launch.py:2529-2532,2579-2584`)、面2は handler が `SystemExit` を捕捉しない (`tools/dev_waves/cli.py:349-388`)。したがって choices 違反は rc=2 のままである。
- dev-waves の通常経路は概ね `Namespace → SupervisorProfile → WorkerSpec → child argv`、永続復元を挟むと `server-profile.json → SupervisorProfile` が追加される。実 child の唯一の Popen 直前にも `build_child_argv()` が `validate_child_argv()` を呼ぶ (`tools/dev_waves/worker.py:231-251,393-402`)。wrapper spawn 前にも worker spec を再 parse する (`tools/dev_waves/worker.py:595-603`)。
- P2 は守られている。worker spec は `_required_string(..., _EFFORT_RE)` (`tools/dev_waves/schema.py:563-566,800-801`)、argv は token/NUL 検査後に `_EFFORT_RE` (`tools/dev_waves/schema.py:835-854`) なので、空・制御文字・超長・`HIGH` は従来の形診断を保ち、well-formed な `none` だけを新しい `unknown` へ送れる。
- role policy の広がりはない。launcher は `{low, medium, high, xhigh}` (`orchestrator/codex_roles/launcher.py:349-358`)、manifest parser は `{medium, high}` と role 固定 (`orchestrator/codex_roles/spec.py:602-621`) のまま。実 manifest も `high` / `medium` だけである (`orchestrator/codex_roles/manifest.json:24-26,349-351`)。
- `codex_reasoning_ab.py` は直接起動面だが、schedule 全体が `max/high` に閉じている (`tools/codex_reasoning_ab.py:160-165,3575-3623,5220-5231`)。広い capability 集合へ置換すると逆に policy を広げるため、scope 外維持が正しい。
- 面2・3は D74 により fake-only で、real Claude 起動は未開放である (`docs/decisions.md:2955-2962,2985-2995`)。現時点の live real-child 保証として数えてはならない。
- raw `DW-O01` は依然として `codex exec -c model_reasoning_effort=...` を直接叩き、3 面すべてを迂回する (`docs/dev-wave/operations.md:6-12`)。

## 総括

- **NO-GO** — model-dependent な受理集合を逆転させる P1 と、正本を supervisor hash 閉包外へ出す P3 が未解決。
- **blocker: 2件** — ① `mini/none` を拒否し `mini/max` を admission する平坦集合、② `effort_levels.py` が `supervisor_code_sha256` / trust-root の閉包外。
- **(P1改): 反対** — 製品別 tuple は repo policy としては可能だが、capability 集合としては既知の model 依存性と矛盾し、`none` 禁止にも追加裁定が要る。
- **(P2): 同意** — regex を membership より先に残すため、形違反と well-formed unknown の診断・変異帰属を維持できる。
- **(P3): 反対** — 現在の配置では dev-waves の新しい実行時依存が supervisor digest と Git trust-root の双方から漏れる。
- **「値域検査を入れた」が真になる範囲:** 修正後も、`codex_worker_launch.py run` の新規 CLI requested token、`dev_waves serve` の新規 CLI effort、および正規 WorkerSpec/child-argv の pre-spawn repo-policy 検査に限る。raw DW-O01、historical/check-receipt、task-runs、独自 policy の role launcher／reasoning A/B、model×effort compatibility、served identity、未開放の real Claude 経路は含まない。