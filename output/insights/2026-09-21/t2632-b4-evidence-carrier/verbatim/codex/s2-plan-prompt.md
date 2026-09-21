単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/stage1-brief.md — 親 brief (scope・不変条件・変更面アンカー・provisional 裁定 P1〜P7)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/request.md — 依頼の逐語。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/d2194-item3.md — 本 wave の裁定 (D2194 項 3) の逐語。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/d2120-item5.md — D2120 項 5 の逐語 (bootstrap 集合は定義しない)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/insight-t2632-s7.md — 一次資料 §7 (裁定パッケージ、推奨形の最小 field)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/insight-t2632-s2.2-2.3.md — 一次資料 §2.2 (現行 carrier 一覧) / §2.3 (caller の欠陥)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/insight-t2632-s4.md — 一次資料 §4 (参照点の量の所在、2 つの canonicalization の差)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/prereg-s5.1.1-reference.md — 凍結事前登録 §5.1.1 の共通参照点 (逐語、編集禁止)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/prereg-s5.1.1-population.md — 同 §5.1.1 の母集合・適格性述語 (逐語)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop.py — 変更対象 1 (base driver、3646 行。`drive_iteration`・`_run_one_iteration_resolved`・`_resolve_duplicate`・`_duplicate_snapshot`・`load_proposal_file`・`canonical_b4_proposal_sha256`・`main` の `--run-iteration` / pair mode 経路)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop_trigger_gating.py — 先例 (`_provenance_path` / `_load_provenance` / `_write_provenance` / `_append_provenance_entry` / `_wal_attempt_provenance` / `_write_source_preimage_artifact`、および `drive_iteration` 内の呼び出し順)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_b4_prerun_caller.py — 変更対象 2 (172 行)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/campaign_lock.py — 既存 codec (`decode_campaign_lock` / `decode_campaign_lock_bytes` / `DecodedCampaignLock`)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/agent_outputs.py — `canonical_bytes` / `canonical_sha256` (allow_nan=False)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/wal.py — `read_records` / `records_by_stage` と WAL record の型。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/artifact_admission.py — `_validate_trigger_provenance` (trigger の provenance を admission が検査する先例。本 wave では base に admission 検査を足さない = scope 外)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_s4_loop.py — 既存 test (drive_iteration / duplicate / dry-pass の fixture の作り方)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_b4_prerun_caller.py — caller の既存 test (v1 形 lock fixture `_campaign`)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/campaign_lock_test_support.py — v2 lock fixture helper `build_v2_campaign_lock`。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_s4_loop_trigger_gating.py — 先例 side channel の test (書き順・冪等・破損退避)。読めなければ即停止

## 親の実測 (段 1、本 prompt 作成時点、main `5f48a298a`)

- 実物 v2 lock (B-5 試走の campaign 10 件、例 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-6fc5d263/campaign.lock`) は
  top-level key が `authority` / `identity_preimage` / `schema_version` だけで top-level `trial` を持たない。`identity_preimage` 内の `trial` = `"p3-s4-loop"`、
  `search_tag` = `"s4-autonomous"`、`search_config.axis` = `"silo-backoff-magnitude"` (jq 実測)。同 campaign の `reports/` は空、whiteboard は 1 行 (`success`)。
- `p3_s4_loop.py` は `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` (85 path) と `p3_b4_closed_critic` の projection closure に入る。未 commit の bytes 変更で、
  v2 lock を作る test が内容と無関係に 114 node 落ちる ([T-2795] wave の実測)。事前登録 §5 の projection hash 欄は `未記入` (陳腐化する記入値は無い)。
- `test_campaign.py` の certified-writer 目録は `run_campaign` 呼び出し点を数えるもので、本 wave の変更 (file 書き出し) では登録が要らない見込み (親の静的読み)。
- `drive_iteration` は proposal bytes を受け取らない。`load_proposal_file` の `capture` は `--agent-inputs` 指定時しか渡されていない。
- stock 対照 (`_run_stock_cli_step` → `_run_stock_control_resolved`) は whiteboard / loop_state に触れない。

## 依頼

file:line 粒度の実装プランを起草する。次を必ず含める。

1. **side channel の file と schema。** path (`<campaign root>/reports/p3_s4_loop_provenance.json` を provisional とする)、top-level の形
   (先例の header + `entries[iteration]` か、別形か)、entry の field (D2194 項 3 (1) の 6 field: `iteration` / `variant` / `build_attempt_id` /
   `initial_proposal_sha256` / `wal_refs` / `outcome`) の型と値域。outcome ごと (certified / aborted / rejected / dry-pass / duplicate /
   duplicate-skip / rejected-preprocess、pair mode の候補側) に各 field が何になるか (null を含む) の表。`wal_refs` の構成規則 (brief P6) と、
   variant が WAL 上で複数 attempt を持つ場合の扱い。
2. **書き込み位置と順序。** `drive_iteration` 内の挿入行と前後のアンカー文字列。`save_loop_state` より前に置く理由と、例外時に checkpoint を
   進めないことの保証。`b5_mode` の早期 return 経路 (`duplicate-skip` / `rejected-preprocess`) との順序。入口停止 (`stopped-before`) では書かない (P5)。
3. **proposal の canonical hash の配管。** `main()` の `--run-iteration` 経路で `load_proposal_file` が読んだ document から
   `canonical_b4_proposal_sha256` を計算し `drive_iteration` へ渡す形 (引数名・既定値・None の意味)。B-4 mode の receipt key 除去との整合。
   `drive_iteration` を直接呼ぶ既存 caller (test・sort / trigger は自前の drive_iteration) を壊さないこと。
4. **書き込みの堅さ (P4 / P7)。** atomic 公開 (tmp + fsync + `os.replace` か、先例 `_write_source_preimage_artifact` の O_EXCL + link か)、
   同 iteration の再実行時の冪等 (上書き merge か、差分があれば拒否か)、破損時の退避と停止。先例 2 つのどちらをどう組み合わせるかを根拠つきで。
5. **参照点の定義 (2) の置き場 (P1)。** code に resolver を作らない場合、定義文を docstring のどこにどう書くか (新 object・新 producer を作らない
   制約の下で)。事前登録 §5.1.1 の凍結文と矛盾しない書き方 (祖先無し・同着・PerfConfig / env_tag 不一致は不適格、代替基準へ切り替えない、
   reps と ycsb_max_ope は run_cmd から確認できない不足)。
6. **caller の修正 (項 4)。** `collect_scheduled_batch` の変更行、codec の例外 (`CampaignLockCodecError`) を既存の `CampaignInputUnreadable` へ
   どう写すか、v1 lock (tracked 3 campaign) が引き続き読めるか (codec の v1 受理形の実測)、test fixture `_campaign` の v2 化
   (`build_v2_campaign_lock` の使い方と identity_preimage の canonical 形)、`broken == "trial"` 系の既存 test の書き換え。
7. **test 案。** 追加する test の名前・file・アサートする literal。最低限: entry が outcome ごとに正しく書かれる、whiteboard 5 field と
   `whiteboard_for_planner` / `project_whiteboard` の出力が不変、save_loop_state より前に書かれる (書けなければ checkpoint が進まない)、
   冪等、破損で停止、proposal hash が receipt key を除いた canonical hash と一致、caller が v2 lock を読める / v1 も読める / 壊れた lock は
   `campaign_input_unreadable`。contract-loader drift を避ける test の組み方 (v2 lock を作る test を未 commit で走らせない、等の注意) も書く。
8. **触ると壊れる既存 pin・目録の一覧**と更新方法 (`test_campaign.py` の certified-writer 目録、`test_official_perf_closure.py`、
   `test_p3_exploration_namespace.py`、`test_p3_b4_wiring_probe.py`、`test_p3_b4_closed_critic.py`、`acceptance_duration_ledger.json` 等。該当しないなら該当しないと根拠つきで)。
9. **変異負例の候補**: どの 1 行を変えるとどの test が落ちるか、最低 8 件 (side channel 5 件以上、caller 3 件以上)。等価対照 1 件も。

## 制約

- sandbox は read-only で書込可能な tmp が無い。**静的検査だけでよい。** テストの実走・計測は親が行うので、実走していない事柄を「確認した」と書かない。
- 凍結された事前登録本文 (`docs/phase3-b4-reflux-ablation-preregistration.md`) は編集しない。
- gate・検査・台帳の新設、admission への base provenance 検査の追加、sort / trigger への展開は scope 外 (D2194「付随する gate・台帳・汎用化を足さない」)。
- whiteboard の 5 field と planner 射影は変えない (D39 決定 3・D1846)。
- 規律 2 を前提にする。side channel は評価結果を変えない記録であり、reject / certified の判定経路を変えない。
- B-4 本走・床値の投入手順は書かない。
- 予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終える。

## 出力形式

項目 1〜9 を見出しで分け、各項目に file:line と前後のアンカー文字列を付ける。brief の P1〜P7 に反対する場合は、その項目で反対と根拠を明記する。
最後に `## 総括` を置く (採否の要点を 5 行以内)。
