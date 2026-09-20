# 段 1 brief 追補 1 — 段 2 plan 受領後の親の provisional 判断 (段 3 consult の攻撃対象に追加)

作成 2026-09-20 19:50 JST。plan は `codex/s2-plan.md`。

## 新事実 (plan と並行して親が実測)

- **peer wave (T-2795 pair 投入) の job `13339.nqsv` (19:12〜19:13) で、候補 (certified、811,956 tps、配線規模) の後の同 campaign stock step が
  `campaign_claim.ClaimError: campaign claim は既に <候補 pid> が所有している` で rc=1。** `loop._authorize_measurement` は campaign identity ごとに
  `<identity>.claim` を O_EXCL で作り release しない (`campaign_claim.py:383–`)。同 campaign id を別 process が続けて掴む D2183 の「同 campaign」形は
  claim 層で成立していない (peer の scope)。**B-5 では slot ごとに identity (= claim file・protocol digest = preimage sha256) が別**なので回避できる
  (`loop.py:222–235`)。protocol 競合走査 (`_scan_protocol_conflicts`) は同 protocol digest の live owner だけを見るので、別 slot 同士は衝突しない。
- coder build authority の発行は `materializer_admission.MATERIALIZER_ADMISSION_REGISTRY` の CODER_ENTRYPOINT (`p3_s4_loop.main` ほか 6 site) に閉じ、
  `test_p3_build_authority_cli.py:71` `EXPECTED_CODER_SITES` と `test_p3_exploration_namespace.py:380–` `_DRIVER_CONTRACTS` (driver ごとの argv factory・
  layout / run_campaign 呼出し数) が閉包を pin する。新 CLI を coder entrypoint として登録すると両 test へ driver contract 一式を足す必要がある。

## (P9) 親の provisional 判断: 3 arm とも slot 評価は `p3_s4_loop` CLI の subprocess で行う (plan の in-process seam + 新 entrypoint 案の代案)

事前登録 §4.1 は LLM arm の各評価を「`p3_s4_loop` の単回評価 (proposal file を渡す) を fresh layout で 1 回呼び出す」と定め、§5.1 は 3 arm の目標経路を
「`p3_s4_loop` の proposal 読込みから hole 挿入・検疫・`run_campaign`」と定める。これを逐語で満たす形:

- B-5 系列 driver (新 module) は slot ごとに `python -B -m orchestrator.campaign.p3_s4_loop --run-iteration <proposal.json> --isolate-worktree
  --fetchcontent-prebuild-receipt R --calibrated-perf --perf-workload W --verify-performance --b5-slot <KEY> [LLM: --allow-coder-derived-build
  --knowledge-manifest M --coder-role coder-v4-autonomous-k2 ...] [random / sweep: --machine-generated-proposal]` を subprocess で 1 回呼ぶ。
  stock slot は `--stock-control --b5-slot <KEY> --calibrated-perf ... --verify-performance` の subprocess。
- `p3_s4_loop.main` に足す seam は 2 つだけ: (1) `--b5-slot KEY` → `search_config["b5_slot"]` へ焼く (identity 分離、`main` の較正 fold と同じ位置)、
  (2) `--machine-generated-proposal` → `--allow-coder-derived-build` / `--coder-role` / `--knowledge-manifest` と排他、`build_run_context(generator_id=BACKOFF_SWEEP)`
  (coder authority 無し) + 候補 source に generator receipt を発行する `capability_resolver` (input = sha256(`"p3-s4-loop-machine-proposal/v1|" + sha256(proposal bytes)`)、
  STOCK でも coder 由来でもない機械生成の admission class = machine-generated) を `drive_iteration` → `_run_one_iteration_resolved` → `run_campaign` へ
  keyword-only 既定 None で素通し。既定経路の kwargs・分岐・戻り値は不変 (T-2795 の stock resolver と同型)。
- fresh layout (slot key) の下で `drive_iteration` の入口 `check_stop` は iteration 0 / start_wall 直後なので発火しない (§3.4 の「§4.1 の運用契約では
  この停止は発火しない」を機械で実現。checkpoint の改変・初期化ではなく登録された運用契約そのもの)。`MAX_ITER` / `MAX_WALLTIME_S` は触らない。
  B 完走の保証は B-5 driver のループ + 台帳が担う。
- A / B の消費点は subprocess 終了後に slot campaign の WAL から決定論的に導く: `BUILD_START` record あり → B 消費 (投入済み)、diff-quarantine reject /
  grammar reject record のみ → A のみ、record 無し (proposal schema / 値域で `load_proposal_file` が例外) → A のみ。walltime 打切りは WAL の最終 record で
  投入前 / 後を分ける。「成功時の後付け加算」は起きない (WAL は append-only で失敗も書く)。
- 利点: 新 coder entrypoint の登録・`_DRIVER_CONTRACTS` 追加が不要、private 名を跨がない、K2 job body と同じ起動形、§4.1 逐語。
  欠点: slot ごとに Python 起動 + `assert_pinned_clean` + worktree 作成 (数十秒 / slot、T-2795 実測の build 区間 15 秒と同程度)、in-process seam
  (`before_pipeline`) は持たない。

## その他の親判断 (plan の「親裁定が必要な事項」への回答、いずれも攻撃対象)

1. **Tier0:** 試走は「共通 Tier0 未実装」を台帳に `tier0_status="not-implemented"` で明示した費用試走とする。現行の build 失敗は §3.3 のとおり B 消費。
   固定スモークは足さない (scope 外)。
2. **admission:** 上記 (P9)。random / sweep は generator receipt (machine-generated)、LLM は既存 coder authority。
3. **verifier wall:** 依頼の逐語は「verifier wall (3 秒 × 5 rep + verifier)」= trace 走行込みの verify 区間。WAL の record 時刻差
   (`build_done` → 各 `verify_done`、`bench_done.bench_wall_s`) で rep ごと・session ごとに取り、「trace + verifier 区間」と正確に呼ぶ。
   純 verifier の計時 adapter は足さない (scope 外、必要なら裁定パッケージ候補)。
4. **sweep:** 先頭 10 点を順に評価し、候補起因の不通過なら次点 (11 点目以降) へ進んで B = 10 か A = 30 か格子枯渇まで。§4.3 の「次点」「格子を使い切ったら」の読み。
5. **P7:** 反証を採用。consumer は `purpose="pilot"` の記述経路を持ち、試走では `registered_judgment="not-applicable-pilot"`。試走の直列順は
   block-stock → random → sweep → LLM を基本とするが、queue 待ちが長い場合は 4 job を同時投入して別 node で並列に走らせてよい (試走は配置の再現を主張しない)。
6. **LLM 失敗時の current_perf:** planner 入力の schema は K2 round 3 と同じ 5 key に固定し、`current_perf` は「直近の certified かつ品質正常な評価、
   無ければ系列開始 stock」の値。出所 (`stock-start` / `evaluation k`) は prompt の「親の事実開示」節に書く (schema へ field を足さない)。
7. **LLM handshake の timeout:** 45 分無応答は「候補の処理を始める前の中断」として機械故障扱いで同 slot +2 回まで (合計 3 回の待機)、超えたら系列を
   `proposal-timeout` 欠測で止める。LLM の空出力・schema 不合格は親が `proposal-<a>.json` の代わりに `proposal-<a>.rejected.json` を置いて A 消費を明示する。
