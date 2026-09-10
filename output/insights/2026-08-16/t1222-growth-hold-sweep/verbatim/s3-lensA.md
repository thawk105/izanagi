結論は BLOCKER です。現行の「74 件をそのまま登録」は段 5 へ進められません。

### 所見 1 — BLOCKER: A10 の guard binding は既定受入を確実に赤にする

- 主張: `test_dev_waves_integration.py` には段 2 が見落とした standalone subprocess self-import があり、guard 追加後は非保留 node が import 時に落ちる。さらに `plain_runner="pytest-delegating"` 自体が現行 AST 契約と不一致。
- 根拠 file:line:
  - 段 2 は `s2-plan.md:484-495` で self-loader 無し、`pytest-delegating` と判定。
  - `orchestrator/tests/test_dev_waves_integration.py:2050-2058` は fresh subprocess で同 test module を package import。
  - その経路を既定実行する `test_socket_roundtrip_works_beyond_108_byte_repository_path` は `:2165-2167` にあり、推薦 40 件には入っていない。
  - subprocess の到達先は `_serve_child_main` `:2019-2029` → `_run_long_path_serve_harness` `:1685-1695`。
  - fresh import では pytest enforcement も明示 token も `__name__ == "__main__"` も無いため、`growth_test_holds.py:595-604` が `GrowthTestHoldBypassRefused` を送出する。
  - runner 判定は main guard の終端が直接 `pytest.main(...)` の場合だけ delegating とする (`test_growth_test_holds_contract.py:433-471`)。現行 main は `SystemExit(_run())` (`test_dev_waves_integration.py:2718-2726`) なので期待値は `manual`。不一致は `test_growth_test_holds_contract.py:550-555` が赤にする。
- これが真なら何が壊れるか: socket test は構造化 child result を得られず failure になり、guard meta-test も失敗する。2026-08-16 の floor campaign と同型。
- 提案: A10 の 40 件と guard 追加を全撤回する。将来扱うなら subprocess helper を別 module へ分離し、runner 契約を直したうえで targeted fresh-import 検査を置く。自動で解除 token を child に渡す案は「explicit-user-command-only」を破るので不可。

### 所見 2 — BLOCKER: A06/A09/A10 の「代替経路」は同じ拒否条件を検査しない

- 主張: production が同じ関数を呼ぶだけでは、crafted negative input に対する fail-closed 性の代替にならない。推薦 71 件の大半で既定 detector がゼロになる。
- 根拠 file:line:
  - A06 の production 経路は `cli.py:188-195` → `task_run_check.py:15-20,52-75` → clean な実 repo に対する `check_codex_agents.py`。不正なら checker rc=1 (`check_codex_agents.py:346-368`)、wave verification では `CODE_DIRTY` (`checker.py:337-347`)。
  - しかし A06 の 20 negative node は native profile、symlink、byte drift、duplicate key、非有限 JSON、bijection、schema weakening 等を一時 fixture に注入する (`test_codex_agents.py:252-542,1108-1196,1269-1331`)。clean repo の正常系はこれらを発火させない。
  - A09/A10 の「代替」は、検査対象そのものを production が呼ぶだけ。daemon は `verify_wave` を一度呼ぶ (`daemon.py:1295-1305`)。A09 は passive failure、trust-root tamper、receipt mismatch、exactly-once、active side effect を注入 (`test_dev_waves_checker.py:182-326`)。
  - A10 は malformed output、wrong receipt、14 種 gate failure、crash/recovery、dirty recovery、WAL/capacity/permission failure 等を制御注入する。通常の成功 wave はそれらを発火させない。
  - D451 は最後の node を消すことと、fixture 費を残して検出力だけ削ることを明示的に禁止 (`decisions.md:18868-18885`)。
- これが真なら何が壊れるか: checker/daemon を fail-open に変異しても、clean な production 実行は rc=0 のまま。A06 の 20、A09 の少なくとも 9、A10 の全 rejection family が既定走行ゼロになる。
- 提案: A06/A09/A10 の 71 件は登録しない。A06 の clean positive 1 件や A09 の成功系 1 件だけを再検討する場合も、file-wide guard の副作用を先に解消する。

### 所見 3 — real（条件付き）: A05 は同じ checker だが、land は普遍的な代替ではない

- 主張: A05 の 3 node は同じ `check_docs.py` 正常系なので代替可能性は高い。ただし「land が必ず同時点で守る」は誤り。
- 根拠 file:line:
  - 3 node は実 repo の同じ checker を引数無しで起動 (`test_check_docs.py:7282-7289,7462-7471,9433-9441`)。
  - checker は finding があれば rc=1、無ければ rc=0 (`check_docs.py:5212-5217,5433-5439`)。
  - land は同じ checker を起動するが `--expect-active-transaction` 付き (`dev_wave_land.py:2211-2237`)。fold が noop なら検査前に return する (`:2337-2341`)。失敗は最終的に land rc=26 (`:2438-2444`)。
  - wave checker は check-docs exactly-once を要求し (`checker.py:351-361,643-645`)、completed・passive-green の場合だけ isolated checkout で実行する (`:648-688`)。noncompleted は不要扱い、passive failure 時は skip。
- これが真なら何が壊れるか: land だけに依存すると、noop fold、非 supervisor 作業、受入から land までの時間窓では同時点の防壁が無い。
- 提案: standard acceptance の pre-commit `tools/check_docs.py` 実行を独立不変条件として確認できる場合だけ A05 を登録候補に残す。確認できなければ D451 で見送る。

### 所見 4 — real: 段 2 の「全件走査」は少なくとも 8 function を落としている

- 主張: `230 candidate / 74 registered` は閉じていない。
- 根拠 file:line:
  - `load_role_specs` は実 `.claude/agents/*.md` を glob・全読込する (`orchestrator/codex_roles/spec.py:320-331,500-532`)。checker は adapter directory を全 `iterdir` する (`check_codex_agents.py:216-245`)。
  - 段 2 の A06 一覧に無い次の 7 node が実 ROOT のその経路へ到達する:
    - `test_codex_agents.py:121-124`
    - `:127-150`
    - `:164-213`
    - `:216-230`
    - `:233-249`
    - `:511-519`
    - `:1300-1307`
  - A10 では `test_socket_roundtrip...` `:2165-2167` が subprocess import `:2050-2053` を介し、`_run_long_path_serve_harness` `:1685-1690` → `_temporary_repo` `:168-185` → real `tools/task_runs` copytree `:160-165` に到達する。段 2 の 40 件には無い。
- これが真なら何が壊れるか: 母集合件数、insight の exact inventory、追加後 count=130、両 SHA pin が虚偽の「全件」結果に固定される。
- 提案: 少なくとも candidate は 230 でなく 238 以上として再棚卸しする。subprocess 内 import 文字列と、`load_role_specs(ROOT)` のような production enumerator も call closure に含める。ただし追加 8 件も自動保留せず D451 を個別適用する。

### 所見 5 — real/refuted 分割: P1 の blanket refutation は覆るが、全件 real でもない

- 主張: 親 P1 は部分的に誤り。正しい分類は三分割。
- 根拠 file:line:
  - refuted: `test_s8b_ratified_verify.py` は実 repo から固定 `_REAL_V1` と固定 calibration path を読む (`:48-55,450-463`)。ccbench も tmp repo に 1 file を合成する (`:256-263`)。search は tmp root。
  - refuted: 最初の silo node は固定 evidence/raw 2 file と固定値を読むだけ (`test_silo_ladder_rung1_evidence.py:1202-1213`)。
  - real: 二本目は `runtime_modules_binding(ROOT)` を呼ぶ (`:1216-1274`)。production は activation JSON を glob、verifier subtree を rglob し、全 file を hash する (`silo_ladder_rung1.py:262-296`)。
  - real: copytree は現在小さくても file 追加ごとに増える。D335 は「file 数・台帳量への比例」を秒数に関係なく構造で判定する (`decisions.md:14959-14974`)。
- これが真なら何が壊れるか: 親分類のままなら second silo と copytree の比例性を見落とす。一方、比例だから即保留すると D451 を破る。
- 提案: ratified 全体と first silo は refuted、second silo と copytree は `growth-real / D451-not-held` と記録する。

### 所見 6 — real: 親 probe の「合計数十 ms」は node 費へ一般化できない

- 主張: probe は一回の primitive 下限であり、fixture の反復・parametrize・process/Git 費・xdist critical path を含まない。
- 根拠 file:line:
  - A06 `_fixture` は 3 copytree を一回行う (`test_codex_agents.py:37-53`)が、literal loop を静的展開すると推薦 20 negative function 内で 65 回作られる。最大は 13 role × input/output の 26 回 (`:1137-1183`)。
  - A09 は各 10 node が `_fixture` を一回構築 (`test_dev_waves_checker.py:60-154,171-326`)。
  - A10 の 40 hold key は parametrize 展開後 78 pytest item。helper 呼出しと二 repo caseを含め、推薦分だけで最低 79 copytree、見落とした socket closure を含めると 80 回。
  - 親の値をそのまま掛けても、A06 `65 × (0.016+0.009+0.007)`、A09 `10 × 0.008`、A10 `79 × 0.008` で約 2.79 秒。数十 ms ではない。
  - 同時に A10 の実費は copytree 以外が支配的で、source comment は work 68.0→84.5 秒を記録している (`test_dev_waves_integration.py:59-79`)。holding で消える大半は比例源でなく固定正しさ検査。
- これが真なら何が壊れるか: 「0.04 秒を消すための 71 件」という費用評価も、「node 実費が probe と同じ」という段 2 の評価も成立しない。ただし約 2.8 秒でも正しさ 71 key/109 item を消す根拠にはならない。
- 提案: 実測するなら計算ノードで actual collection、xdist group、warm cache込みの差分を測る。裁定自体は測定を待たず、D451 により 71 件を見送れる。

### 所見 7 — real: P2 は「1 node でなく 3 node」が正しいが、保留不可

- 主張: `repository_candidate_commit` の比例費は consumer 3 件全てに帰属し、全部保留も部分保留も不可。
- 根拠 file:line:
  - session fixture は `git read-tree`、`add -A`、`write-tree`、`commit-tree` を実 ROOT に対して一度行う (`test_s8c_preregistration_invariant.py:76-121`)。
  - consumers は `:124-161`, `:190-203`, `:206-228` の 3 件で、同じ xdist group。
  - 防壁はそれぞれ generation chain、candidate 非有効・12 predicate 全不成立、wave files の holdout 非汚染＋positive control。
  - D451 は一部だけ保留して fixture 費を残す純損失を禁止 (`decisions.md:18880-18885`)。また 3 node は xdist group 所属なので D452 の期待赤にも使えない (`:18888-18904`)。
- これが真なら何が壊れるか: 全保留で candidate/preregistration/holdout 防壁が消え、部分保留では費用を残して検出力だけ減らす。
- 提案: 3 件とも登録しない。親 P2 の D451 結論は real、段 2 の「名指し 1 件ではない」という補正も real。

### 所見 8 — real: 74 key は 112 pytest item と大量の固定検査を同時に失う

- 主張: `collateral_note` は任意ではない。推薦 74 key は A10 の parametrize 展開を含め 112 itemを既定走行から外す。
- 根拠 file:line:
  - A05 3 item、A06 21、A09 10、A10 40 key→78 item。
  - 少なくとも次を per-key `collateral_note` に記す必要がある。

| file:line（各行の test node） | 失う固定検査 |
|---|---|
| `test_check_docs.py:7282 / :7462 / :9433` | current model-pin 正例／normative section pin の過剰拒否正例／real repo clean と admission finding ゼロ |
| `test_codex_agents.py:159` | byte-exact render と native profile 空集合 |
| `:252 / :266 / :291` | native TOML 拒否／config role・TOML parse 拒否と globals 正例／`--write` 拒否・無変更 |
| `:306 / :325 / :338 / :367 / :391 / :408` | missing-extra-symlink／adapter byte drift／body・description ledger／tools-model-effort／description quoting／manifest-source bijection |
| `:421 / :440 / :459 / :475 / :524` | capability lowering／Codex model-effort／verifier pin／semantic weakening 5 種／runtime activation block |
| `:1108 / :1134 / :1186` | auditor `diff_digest`／全 role schema・adapter 独立 ledger／consumer AST required-field drift |
| `:1269 / :1286 / :1312` | duplicate key／NaN・Infinity／lockstep role deletion count floor |
| `test_dev_waves_checker.py:171 / :182 / :193` | valid isolated active check／passive failure時 side-effect ゼロ／first-reason 順序 |
| `:207 / :252 / :256` | trust-root tamper／run_tests tamper／task_run_check tamper |
| `:260 / :282 / :294 / :320` | receipt-main-tip binding／task-run completed／check-docs exactly-once／active side-effect reobservation |
| `test_dev_waves_integration.py:468 / :492 / :542 / :546 / :550` | exact receipt・land／direct-child fold／run-id・wave-index namespace／3-wave identity・session・prompt 分離 |
| `:577 / :621 / :646 / :670` | 4 child failure停止／cancel・shutdown signal順序／handshake reason |
| `:692 / :713 / :743` | malformed output 7種／receipt binding 3種／独立 gate failure 14種 |
| `:755 / :774 / :827 / :861` | request idempotency・conflict／busy exclusion／passive-before-active／専用 reason mapping |
| `:900 / :947 / :987 / :1024 / :1068` | 5 crash phase no-duplicate／3 SIGKILL recovery point／accepted reconcile／dirty recovery／identity・branch rebind |
| `:1120 / :2170 / :2187 / :2199` | invalid-request audit／linked identity／nested launch拒否／settings-hook・model slug |
| `:2245 / :2278` | cross-wave budget clipping／artifact byte accounting |
| `:2328 / :2362 / :2380 / :2403` | vanished artifact分類／capacity fail-closed／aggregate cap／deadline-before-write |
| `:2441 / :2457 / :2469 / :2496` | outcome 5種の一意 mapping／blocked+main move／spawn kill-reap／cancel identity ambiguity |
| `:2536 / :2553 / :2631` | partial WAL拒否／fsync failure poisoning順序／危険 argv 非再構築 |
| `:2654 / :2689` | run-thread-bound idle／terminal後の完全 quiescence |

- これが真なら何が壊れるか: 現行 plan の `collateral_note` 任意扱い (`s2-plan.md:522-526`) では、ユーザー提示が検出力損失を隠す。加えて manual runner では top-level guard が file 全体を拒否するため、`test_check_docs.py` の非保留 302 function、`test_codex_agents.py` の20、`test_dev_waves_checker.py` の2も走らなくなる。前者は plain Python 対応を明記している (`test_check_docs.py:2-14,9613-9642`)。
- 提案: 71 件を見送る。A05 を残す場合は3件全てに note を付け、manual runner 全体拒否もユーザー提示へ含める。

## 総括

- BLOCKER: A10 guard は fresh subprocess self-import を壊し、非保留 socket test を既定で赤にする。
- BLOCKER: A10 の `pytest-delegating` 指定は現行 AST runner 契約上 `manual` と不一致。
- BLOCKER: A06/A09/A10 の production caller は negative/tamper 条件を作らず、71 件の代替検査ではない。
- BLOCKER: 段 2 の全件数は A06 の7件と A10 subprocess closure 1件を少なくとも漏らしている。
- real: A05 は同じ checker を使うが、land は noop fold では走らず、発火時点と rc が異なる。
- real: P2 は3 consumer全てが比例し、全保留も部分保留も D451 違反。
- real: second silo と copytree は構造成長比例。ただし copytree 群は D451 で保留不可。
- real: 74 key は112 pytest itemと上表の固定検査を失う。
- refuted: ratified-verify 全体と first silo node に実 repository 成長閉包は見つからない。
- pytest は実行しておらず、緑は主張しない。dev-wave 段3契約どおり read-only 静的検査のみ。