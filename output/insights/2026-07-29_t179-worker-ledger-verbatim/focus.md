判定は **NO-GO** です。指定ファイルはすべて全文読了しました。pytest・runner・CLI 実走は行っておらず、以下は静的判定です。親の `224 passed` を私の緑とは数えていません。

## 成果物 1: 所見ごとの対応表

### レビュー A

| 所見 | 状態 | 根拠・残余 |
|---|---|---|
| A1 usage schema/type | `regressed` | final-null、欠損、非 int は [ledger:156](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:156) で issue 化された。一方、fix が `reasoning_output_tokens` まで必須化し、旧 CLI の健全な usage を拒否する [tests:335](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:335)。負整数も int として通る。 |
| A2 delta の因果誤称 | `closed` | 中立名と `cumulative - per_turn` の符号は [ledger:309](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:309)。event 数と非単調検査は同ファイル 267–301。`test_cumulative_usage_stays_canonical_and_metrics_are_explicit` が `-70` を literal 固定。 |
| A3 `turns` の名乗り | `partial` | API・テストは `model_calls` / `turn_contexts` へ移行し、定義も [ledger:4](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:4) にある。しかし正本 worklog は依然「434 model turns」「71 turns」[worklog:1459](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/docs/worklog.md:1459)。 |
| A4 同一 session の複数 file | `closed` | ID 小文字化は [ledger:240](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:240)、重複 issue は同 719–726。`test_case_normalized_duplicate_is_the_only_strict_failure_m2_prime`、`test_same_session_id_in_two_files_fails_closed`。 |
| A5 複数 `session_meta` | `partial` | 通常経路は [ledger:233](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:233) で検出。ただし filter は最初の meta の cwd だけで file 全体を除外するため、先頭 meta が選外、2個目が選択対象なら issue ごと消える。 |
| A6 複数 model/reasoning | `partial` | `turn_contexts` 数は公開されたが、model/effort は今も最初の1件だけ [ledger:249](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:249)。異なる2 context の拒否・分割帰属テストがない。 |
| A7 stage 乗っ取り | `partial` | 先頭非空行限定と ambiguous 化は [ledger:315](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:315)。しかし実 dispatch の `段6 fix 後の` [prompt-focus:1](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/prompt-focus.txt:1) は、空白なし `fix後の` だけを許す regex に一致しない。 |
| A8 cwd 部分一致 | `not-adjudicated-in-scope` | 裁定どおり manifest/allowlist は未実装。現在も substring OR filter [ledger:129](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:129)。こっそり一般化されていない。 |
| A9 retry lineage | `not-adjudicated-in-scope` | cwd と正規化 prompt hash の同文 group のまま [ledger:373](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:373)。launcher receipt による因果同定は未実装。 |
| A10 path 決定性 | `closed` | root、rollout path とも `resolve()` [ledger:183](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:183)、同 669–684。`test_relative_absolute_and_symlink_roots_produce_identical_bytes`。 |
| A11 library import pycache | `not-adjudicated-in-scope` | 自 module の loader 前書込みは防いでいない。テストも import ではなく script subprocess [tests:1095](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:1095)。裁定どおり未実装。 |

### レビュー B

| 所見 | 状態 | 根拠・残余 |
|---|---|---|
| R-B1 token 成分公開 | `closed` | record・totals・両 renderer に input/cached/output/reasoning が配線済み [ledger:521](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:521)、同 549–606。 |
| R-B2 stage/model/reasoning oracle | `partial` | healthy 10件の literal 期待は [tests:505](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:505)。ただし異なる複数 context と実 prompt の `fix 後` 空白形を検出できない。 |
| R-B3 root/empty/0件 | `closed` | root 不在は [ledger:669](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:669)、0件 issue は同 745–749。対応3 nodeあり。 |
| R-B4 非 object JSON | `closed` | schema-valid 非 object も malformed [ledger:221](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:221)。`test_schema_valid_non_object_line_is_malformed`。 |
| R-B5 cwd selector 境界 | `regressed` | 選外の正常 meta file を隔離する経路は追加されたが [ledger:692](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:692)、最初の meta だけで file を捨てるため「後続 meta が選択対象」の壊れ file を見落とす新しい順序依存が入った。meta 不明 file は逆に全 filter を汚す。 |
| R-B6 retry の cwd 境界 | `closed` | key は `(cwd, prompt_hash)` [ledger:378](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:378)。`test_retry_groups_do_not_cross_cwd_boundaries`。因果的 lineage は A9 の scope 外。 |
| R-B7 validator 同値性 | `closed` | min/max byte、同一 fence helper、heading を再利用 [ledger:331](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:331)。`test_output_validator_acceptance_is_identical_in_both_directions`。 |
| R-B8 mutation matrix | `partial` | M2′、M5′、M6a/b と M7 pin は是正済み。ただし M8 の健全例は全 usage に reasoning field を強制生成するため、現に入った旧 CLI 過剰拒否を検出しない [tests:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:38)。 |
| R-B9 `compaction_delta` 誤称 | `closed` | 旧列名は実装・テストに残っておらず、event 数と中立差分を literal 固定。`test_non_monotonic_cumulative_and_event_counters_are_exposed`。 |
| R-B10 worklog grammar | `not-adjudicated-in-scope` | entry 本文・fence 外限定は [ledger:427](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:427) で実装。一方 grammar は対象形式専用 [ledger:101](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:101) のままで、一般化は裁定どおり未実装。 |
| R-B11 stage-map/filter 順序 | `closed` | filter 前の全走査 ID 集合と照合 [ledger:681](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:681)、同 728。`test_stage_map_key_filtered_out_by_cwd_is_not_unknown`。 |
| R-B12 renderer oracle | `closed` | human/JSON の完全 literal 期待は `test_human_and_json_outputs_use_independent_literal_oracles`。実装結果から期待値を生成していない。 |
| R-B13 命令様データ | `closed` | fixture/prompt の role 文は regex/hash 入力としてだけ使われ、挙動指示として解釈する経路はない。 |

### 事前登録変異 M1〜M11

ここでの `closed` は「静的に期待する検出経路がある」という意味で、私が mutant を実走して KILLED を確認した意味ではありません。

| 変異 | 状態 | 静的根拠 |
|---|---|---|
| M1 | `closed` | `test_cumulative_usage_stays_canonical_and_metrics_are_explicit` が cumulative 170 / per-turn 240 を独立固定。 |
| M2 → M2′ | `closed` | 旧 M2 は裁定どおり撤回。M2′ は `test_case_normalized_duplicate_is_the_only_strict_failure_m2_prime` が case 正規化された重複だけを固定。 |
| M3 | `closed` | `test_unclassified_is_included_and_strict_fails` が残存 session、stage、strict rc を固定。 |
| M4 | `closed` | fragment と fenced-summary の2 node が常時合格化を検出する。単一 node とは数えない。 |
| M5 → M5′ | `closed` | `test_task_complete_only_missing_with_healthy_message_is_incomplete_m5_prime`。 |
| M6a/M6b | `closed` | `test_worklog_single_reason_mismatch_fixtures_m6a_m6b` が各1 mismatch を固定。 |
| M7 | `closed` | `test_retry_normalizes_surrounding_and_repeated_whitespace` に diagnostic sensitivity pin と明記。**KILL 枠ではない**。 |
| M8 | `closed` | exact mutant「健全 wave も常時 strict failure」は `test_healthy_wave_and_matching_worklog_pass_strict` などで検出可能。ただし旧 schema 互換性の保証にはならない。 |
| M9 | `closed` | `test_bool_usage_field_is_the_only_strict_failure_m9` が issue 1件だけを固定。 |
| M10 | `closed` | `test_zero_selected_sessions_is_the_only_strict_failure_m10`。 |
| M11 | `closed` | `test_quoted_role_below_leading_line_cannot_hijack_stage_m11`。 |

## 成果物 2: fix が持ち込んだ新規欠陥

### 1. 旧 CLI の健全 usage を拒否する回帰

`_USAGE_FIELDS` は `reasoning_output_tokens` を必須扱いし [ledger:147](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:147)、1 field 欠けるだけで usage 全体を破棄します。さらにテストがこの過剰拒否を正解として固定しています [tests:335](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:335)。

`info: null` は [ledger:274](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:274) で正しく無視され、現実装は拒否しません。ただし対応テストは strict rc=0 と issues 空を assert しないため、将来の過剰拒否を検出できません。

成果物影響: 旧 CLI session が strict で不当に落ち、非 strict では正しい core token 値まで 0 に見えるため、CLI version 間比較の受理集合と totals が変わる。

### 2. 負の token 値は依然 fail-open

型検査は `int` だけを条件とし、負値を許します [ledger:163](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:163)。最初の cumulative が負なら非単調検査にも当たりません。`cached_input_tokens > input_tokens` 等による負の billable 値も未検査です。

成果物影響: strict rc=0 のまま session・stage・総 token が負値になり、T-180〜T-184 の閾値と比較値を破壊する。

### 3. 実 dispatch prompt が focus 規則に一致しない

focus regex は `fix後の` / `fix2後の` のみ [ledger:48](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:48)。保存された実 prompt は `段6 fix 後の` [prompt-focus:1](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/prompt-focus.txt:1) です。8件テストは空白を除いた文字列へ書き換えており [tests:751](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:751)、この drift を隠します。

成果物影響: 実 focused reviewer が `unclassified` となり、strict は落ち、非 strict の focus session/token は欠落する。

8つの正規化済み文字列自体は、静的にはすべて期待どおりです。

| パターン | 結果 |
|---|---|
| 段2 planner | plan |
| 段3 consultant | consult |
| 段5 implementation worker | author |
| 段6 fix worker | fix |
| 段6 fix2 implementation author | fix |
| 段6 adversarial reviewer | review |
| 段6 fix後 focused reviewer | focus |
| 段6 fix2後 focused adversarial reviewer | focus |

`_classify_stage` は全規則を集合化するため [ledger:321](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:321)、現在の規則順序そのものには依存しません。単なる並べ替え mutant が緑でも意味論は不変です。first-match 化は `test_conflicting_stages_on_leading_line_are_ambiguous` が検出します。8件表は前回の fix2→author 回帰を検出しますが、dispatch 文字列との逐語同期は証明していません。

### 4. 複数 model/reasoning の誤帰属が未修正

複数 `turn_context` を数えるだけで、model/effort は最初の値に固定されます。payload が truthy だが model が object 直下にある schema 形も空文字になります。

成果物影響: 混在 session の全 token が最初の model/reasoning bucket に移り、T-181/T-182 の A/B 比較が逆転しうる。

### 5. 「選択 file 限定」が meta 順序依存になった

例として、同じ file に次を置くとします。

1. 最初の meta: cwd=`/other`
2. 2個目の meta: cwd=`/target`
3. target lifecycle の壊れ行

2個目は `multiple_session_meta` を立てるだけで record の cwd に反映されず、その後 main が最初の `/other` だけで file 全体を `continue` します。別の健全な target session が1件あれば `no_selected_sessions` も出ず、strict rc=0 が可能です。

逆方向では、meta を一つも解読できない無関係 file は選外と判定できず、すべての cwd filter を汚します。fixture は「最初の meta が選外」の正常形しか検査していません。

成果物影響: target session とその破損が同時に消えて totals が過少になるか、無関係な壊れ file により健全な選択集合が過剰拒否される。

### 6. 改名・符号の追随

- 実装・テストの公開 key に `turns` / `compaction_delta` は残っていません。
- 符号は一貫して `cumulative - per_turn`。literal は `170 - 240 = -70`、`40 - 120 = -80`。
- 旧名のまま緑になるテストはありません。
- ただし live worklog の「model turns」「71 turns」は未追随です。brief/review/fix artifact 内の旧名は過去時点のデータなので改変対象とは数えていません。

成果物影響: live worklog を下流が読むと、token snapshot 件数を再び model turn 分母として解釈する。

## 成果物 3: 変異 fixture の単一理由性

| Fixture | 判定 | 理由 |
|---|---|---|
| M2′ `case_duplicate.json` | 単一理由 | stage、cwd、usage は健全で、test が issues を `duplicate_session_id` 1種だけに固定。 |
| M5′ `incomplete_task_only.json` | 単一理由 | agent message は既定の健全値。欠けるのは `task_complete` だけで、strict issue もない。 |
| M6a `total_only.md` | 単一理由 | actual bucket 1/2/3/4 は一致し、total 9対10だけ。test が worklog issue 1件を完全一致で固定。 |
| M6b `review_only.md` | 単一理由 | total・planner・consult・author/fix は一致し、review 3対4だけ。 |
| M9 `malformed_usage_type.json` | 単一理由 | total input の bool だけが異常。issues 1種・detail 1件を固定。 |
| M10 `no_selected.json` | 単一理由 | file 自体は健全で、cwd filter による0件だけ。issues は `no_selected_sessions` のみ。 |
| M11 `stage_hijack.json` | 単一理由 | 先頭行は正常 review、2行目の引用だけが全文照合 mutant を ambiguous にする。 |

改訂後の上記7 fixtureに、現 checker 上の過剰決定はありません。過剰決定した旧 fixture は明確に別枠です。

- `incomplete.json`: `task_complete` と agent message の両方が欠落。
- `test_worklog_reports_total_and_review_mismatches_together`: total と review の2 mismatch。

M7 は [tests:445](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:445) で diagnostic sensitivity pin と明記され、rc・受理集合を変える KILL 枠から正しく分離されています。

## 判定

**NO-GO**。残る must-fix は次の6件です。

1. `reasoning_output_tokens` 欠落を旧 schema の健全形として扱い、`info:null` の strict 正例も固定する。  
   成果物影響: 健全な旧 CLI session の受理集合と token totals が失われる。

2. token 各値の非負性、少なくとも cached/input の成立条件を fail-closed にする。  
   成果物影響: 負の stage/総 token が policy 比較へ流入する。

3. `段6 fix 後の` を含む実 dispatch 文字列を focus に分類し、生成 prompt 本文を逐語 fixture にする。  
   成果物影響: focused review session が unclassified となり、focus 値が欠落する。

4. 複数 `turn_context` の model/effort が異なる場合は分割帰属するか、少なくとも strict issue で拒否する。object 直下 schema も扱う。  
   成果物影響: model/reasoning 別 token の静かな誤帰属が残る。

5. cwd filter 前に全 `session_meta` 候補を評価し、後続 meta が対象なら file issue を落とさない。meta 不明 file の filter 契約も明文化・テストする。  
   成果物影響: 選択 session の欠落または無関係 file による過剰拒否が起こる。

6. live worklog の `model turns` / `turns` を `model calls` へ追随させる。  
   成果物影響: T-180〜T-184 が誤った分母名を正本として再利用する。

## 総括

全35項目の静的判定は **closed 23 / partial 6 / regressed 2 / not-adjudicated-in-scope 4**。判定は **NO-GO** です。

親が実測で確かめるべきなのは、実 prompt の raw 先頭行と stage-map 使用有無、旧 CLI usage 欠落形の strict rc=0、`info:null` 正例、負値拒否、異なる複数 model/effort、複数 meta の順序2通り、および修正後の実 session→stage 逐件表です。特に保存 prompt の `fix 後` と親の focus 判定がどう両立したかを、正規化した説明ではなく rollout の raw `user_message` と実行 argv で再確認してください。