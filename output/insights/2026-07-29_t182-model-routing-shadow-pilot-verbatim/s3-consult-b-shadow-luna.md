静的検査のみ実施しました。編集・commit・pytest はしていません。新規 `tools/codex_model_shadow.py` と新規テストは未作成のため、以下は plan v1 と既存コードからの所見です。

### 所見1 — gate が受入経路へ配線されていない

- 深刻度: `blocker`
- 該当: `s2-plan.md:18-35`, `tools/run_tests.py:784-830`
- 再現手順: `tools/run_tests.py` の実行経路には `codex_model_shadow.py` 呼出しがない。新 gate の CLI を手で一度実行しなくても、既存 pytest 全走は成立する。新テストも直接 `main()` を import するだけで、実運用 caller を検査しない。
- 成果物影響: gate 未実行のまま receipt/report が T-184 比較対象へ入り、全テスト緑でも pilot の受理集合は未検証になる。

`run_tests.py` の既定 policy を変更する必要はありませんが、pilot 受入用の明示 caller と、その不正 manifest が赤になる統合テストが必要です。

### 所見2 — arm と成果物の結合が弱く、同じ md を複数 arm が再利用できる

- 深刻度: `blocker`
- 該当: `s2-plan.md:80-92,120,135-143`
- 再現手順: 異なる `session_id` を持つ authoritative/shadow 2 arm に、同じ `artifact_md_path` を指定する。両 rollout の最終 `agent_message` が同一の有効本文なら、各 arm の checker rc、hash、model_calls が成立し、現 schema は artifact path の arm 間一意性を要求していない。
- 成果物影響: 2 arm の比較に見せかけて1成果物を再利用でき、finding coverage・token・model_calls が arm 別観測でなくなる。

`arms=[]`、authoritative 1本のみ、同一 `session_id` の2 arm は schema 上拒否予定ですが、対応する直接テスト node がありません。`test_authoritative_count_and_request_is_fixed_d` は authority 数を、`test_duplicate_or_missing_session_id_is_invalid` は rollout file 選択を主題にしており、manifest 内 arm 重複を保証していません。

### 所見3 — prompt hash が「同一 frozen input」を完全には束縛しない

- 深刻度: `blocker`
- 該当: `s2-plan.md:103-118`, `tools/codex_worker_ledger.py:291-293,399-401`
- 再現手順:
  1. frozen prompt を `A\nB`、実 rollout の最初の user message を `A B` にする。ledger の whitespace-normalized hash は一致する。
  2. 最初の user message は全 arm で同じにし、後続 `user_message` だけ arm ごとに変える。ledger は最初の user message しか hash しない。
  3. 全 arm の `prompt_hash` を欠落させ、実装が `set(hashes)==1` だけを検査すれば、全て `None` のまま一致扱いできる。
- 成果物影響: 異なる入力の finding と誤検出を同一 frozen input の比較として記録する。

plan の「frozen prompt の再計算値と一致」は `None` を明示拒否すれば一部を閉じますが、空白差・複数 user message の負例がありません。raw prompt bytes を正本にするか、ledger 正規化を仕様上の同値関係として明記すべきです。

### 所見4 — malformed usage と process rc が真正な完走証拠になっていない

- 深刻度: `blocker`
- 該当: `s2-plan.md:116-142`, `tools/codex_worker_ledger.py:304-307,773`
- 再現手順:
  1. 有効な token usage を1件置いた後、`token_count` の `info:null` を置き、valid な agent message と `task_complete` を置く。ledger は `info` 非 object を黙って読み飛ばすため、model_calls>0、cli_reported>0、completed になり得る。
  2. 実際の CLI が非ゼロ終了しても、manifest の `codex_cli_exit_code` を親が誤って0と記録すれば、ledger 側の `exit_code` は常に `"unknown"` なので検出できない。
  3. `task_complete` まで書かれた JSONL を途中で切っても、EOF/launcher receipt がなければ正常終了と区別できない。
- 成果物影響: 不完全・失敗 rollout が成功 arm として受理され、resource と品質値が汚染される。

T-180 の launcher receipt を実際に消費するまで、`codex_cli_exit_code` は自己申告値にすぎません。`info:null`、複数 `session_meta`、末尾 partial JSON、valid prefix EOF を raw event 単位で赤にする必要があります。

### 所見5 — F43 型の「空本文を水増しした断片」が rc=0 になる

- 深刻度: `blocker`
- 該当: `s2-plan.md:120`, `tools/check_codex_output.py:67-115`, `docs/failures.md:790-805`
- 再現手順: 最終 message と artifact を `"\n" * 600 + "## 総括\n"` とする。raw bytes は500以上で、fence外の見出しもあるため既存 checker rc=0。model_calls>0、cli_reported>0、task_complete、CLI rc=0 にすれば全条件を通る。
- 成果物影響: 本文を失った review が valid arm として受理され、finding 0件や低 coverage が実際の品質値に化ける。

194 bytes の実 F43 は現在の最小サイズ検査で落ちますが、F43 の本質は意味・本文の喪失です。T-183 所有へ送るなら、T-182 receipt はこの状態を `valid` と呼ばないことを明記すべきです。

### 所見6 — `reasoning="ultra"` と不正型を明示的に受理している

- 深刻度: `blocker`
- 該当: `s2-plan.md:87,119,231`, テスト案 `s2-plan.md:275-276`, `tools/codex_worker_ledger.py:271-275`
- 再現手順: shadow arm の requested/recorded reasoning をともに `ultra` にし、model_calls、artifact、prompt hash、CLI rc を正常にする。plan 自身が rc=0 を許し、`test_ultra_echo_remains_unattested_even_when_rc0` もそれを固定する。
- 成果物影響: unsupported reasoning を有効比較 arm として受理し、T-181 所有の reasoning 軸へ不正値を混入させる。

また raw `model=123` は `"123"`、raw `effort=null` は `"None"` に変換され、manifest の同名文字列と一致できます。recorded field は文字列型かつ許可値を検証すべきです。

### 所見7 — requested/recorded 一致は served model identity の証明にならない

- 深刻度: `must-fix`
- 該当: `s2-plan.md:201-243`, 親 brief `s1-brief.md:55-58`
- 再現手順: backend が別実体を使っても JSONL の recorded model が requested slug のままなら、receipt は `requested_model_matches_rollout_recorded=true`、`valid=true` になり得る。実測の400応答が `gpt-5.4-mini-codex-1p-codexswic-ev3` を露出した一方、receipt は `gpt-5.4-mini` だったことが既に示している。
- 成果物影響: 「model identity receipt」が実体 identity でなく request echo になり、model routing の帰属結論を保証できない。

`served_model_attested:false` の明記は正直ですが、`valid:true` のまま downstream が比較に使える点が穴です。served identity が取れない arm は `eligible_for_model_comparison:false` として分離する必要があります。

### 所見8 — テスト一覧が必須攻撃を直接殺さない

- 深刻度: `must-fix`
- 該当: `s2-plan.md:254-281`
- 再現手順: 次の変異を入れても、列挙済み node だけでは生存し得る。

  - arm 0本・1本、同一 session_id の2 arm
  - 同じ artifact path、prompt/labels path の衝突
  - 全 prompt hash 欠落
  - whitespace 差、2個目の user message
  - `info:null`、複数 meta、valid prefix EOF
  - padded fragment
  - recorded model/reasoning の非文字列、unknown model
  - missing/empty/truncated artifact の rc=1 境界
  - `run_tests.py` からの実 caller 不在

- 成果物影響: 実装が fail-open へ変異しても合成テストは緑のままとなり、受理集合の回帰を検出できない。

fixture の固定日時・UUID・相対 path 方針は適切ですが、正例が都合よく全フィールド正常なため、probe の `unknown exit_code`、fragment、ultra、backend alias を代表していません。

### 所見9 — T-180 と private helper の依存契約が弱い

- 深刻度: `must-fix`
- 該当: `s2-plan.md:37-46,277,308-310`, `tools/codex_worker_ledger.py:23-37,227-343,399-401`
- 再現手順: T-180 が `_stream_rollout()` の malformed event 処理や返却 field を変更しても、private name が残っていれば import は成功する。valid fixture だけの adapter test は通り、T-182 の受理集合だけが変わる。loader が `sys.path` や同名 `sys.modules` を変更しても現テストは検出しない。
- 成果物影響: T-180 land 後に token/hash/outcome の意味が静かに変わり、T-179 の既存台帳出力または T-182 receipt が同時に壊れる。

公開 adapter、または private helper の入力・出力・malformed 処理を固定した契約 test が必要です。import 前後で既存 ledger の同一 fixture 出力が byte 単位で不変であることも必要です。

### 所見10 — strict 受理集合の仕様が曖昧で健全 run を落とし得る

- 深刻度: `must-fix`
- 該当: `s2-plan.md:151-186,272`
- 再現手順: labels の `findings:[]` は line 186 では valid zero coverage ですが、line 176 は real/refuted を各1件以上要求します。どの `findings` を `test_explicit_empty_findings_is_valid_zero_coverage` が指すか不明です。また artifact と rollout message の末尾改行差を「一致」とするかも未定義です。
- 成果物影響: zero-finding または一方の分類しかない健全 pilot が invalid になり、coverage denominator と valid receipt 数が変わる。

labels truth set と成果物 declaration を別 fixture 名で固定し、artifact の canonical serialization を決めるべきです。

### 所見11 — 親 brief の P1/P2 は裁定パッケージへ戻すべき

- 深刻度: `backlog`
- 該当: `s1-brief.md:47-58`, `docs/phase3.md:541-551`, plan `s2-plan.md:312-317`
- 再現手順: 段3 B と段6 Bを同一 pilot の第二レンズとして集計する。また `mini@xhigh` を model 効果、`luna@max` を軽量 model として扱う。
- 成果物影響: 異なる task/oracle と model・reasoning 二軸変更を一つの比較証拠へ混ぜ、T-184 が policy 採用に使える参照集合を誤る。

これは T-184 の既定 policy を変更する must-fix ではなく、段4で「段3 Bのみ」「receipt qualificationのみ」へ裁定する候補です。

## 必須ケースの静的判定

- arm 0本・1本: schema 上は rc=2 の予定。ただし直接 node がなく、cardinality 検査を削る変異が未検出。
- 同一 session_id を2 armが指す: plan は rc=1 の予定。ただし manifest 内重複の直接 node がない。
- artifact 欠落・空・短小: checker を通常通り呼べば rc=1。欠落を構成エラー rc=2へ畳むか、run evidence rc=1にするか未固定。
- 全 prompt_hash 欠落: frozen prompt の再計算値・非空・型を検査すれば rc=1。単なる全値一致なら緑になる。
- 同一 session_id の rollout 複数 file: plan は rc=1。ただし単一 file 内の複数 meta と valid prefix EOF は別問題。
- requested/recorded 一致だが served 実体が別: 現 plan は limitation を出して rc=0になり得る。
- `ultra`: 明示的に rc=0 とされており、fail-closed の穴。
- model_calls>0＋本文なし断片: 500 bytes未満なら落ちるが、padding＋見出しなら通る。

## 変異の事前登録案

以下は期待値のみで、実走結果ではありません。

- arm cardinality 検査を削除 → 新設 `test_arm_cardinality_zero_and_one` が rc=2→rc=0 の受理集合変化で赤。現 plan では生存。
- arm 間 session_id 一意検査を削除 → 新設 `test_duplicate_session_id_across_arms` が rc=1→rc=0 で赤。現 plan では生存。
- artifact path 一意検査を削除 → 新設 `test_artifact_paths_must_be_unique` が赤。現 plan では生存。
- frozen prompt 再計算を削除し hash singleton のみ検査 → `test_prompt_file_and_rollout_hashes_must_all_match_a` が赤。
- `None` hash を許す → 新設 `test_all_prompt_hashes_are_required` が赤。現 plan では生存。
- whitespace 正規化または first-user-message 依存を維持 → 新設 `test_prompt_bytes_and_all_user_messages_are_bound` が必要。現 plan では生存。
- model/reasoning 比較を削除 → `test_requested_model_and_reasoning_must_match_rollout_b` が赤。
- inconsistent turn context 検査を削除 → `test_inconsistent_turn_context_is_invalid_b` が赤。
- model_calls/cli_reported の下限を削除 → `test_zero_model_calls_and_cli_reported_are_invalid_c` が赤。
- outcome/checker 検査または final-message binding を削除 → `test_nonzero_cli_exit_noncompleted_or_validator_reject_is_invalid_c`、`test_artifact_must_match_rollout_final_agent_message` が赤。
- malformed `token_count.info` の issue を消す → 新設 `test_malformed_token_count_info_is_invalid` が rc=1 で赤。現 plan では生存。
- authoritative 数検査を削除 → `test_authoritative_count_and_request_are_fixed_d` が赤。
- concurrency 欠落を受理、または confounded wall-clock を順位付け → `test_concurrency_and_wall_clock_fields_are_required_e`、`test_confounded_wall_clock_is_not_ranked` が赤。
- full session selector を短縮 ID/cwd substring に戻す → `test_full_session_id_selects_exactly_one_rollout`、`test_cwd_suffix_collision_cannot_change_selection` が赤。
- labels hash marker/exact declaration を緩める → `test_labels_hash_must_be_embedded_in_every_rollout_prompt`、`test_unknown_duplicate_or_multiple_finding_declaration_is_invalid` が赤。
- score を float・誤分母へ変更 → `test_scores_use_exact_integer_fractions` が赤。
- padded fragment を許す → 新設 `test_bodyless_padded_fragment_is_invalid` が必要。現 `test_small_fragment_is_rejected_even_with_heading` だけでは生存。
- `ultra` を「非 attested だが valid」とする現仕様 → 現 `test_ultra_echo_remains_unattested_even_when_rc0` は fail-open を固定するため、reject 変異の正しい kill にならない。`rc=1` と supported positive を追加すべき。
- served identity を true と誤表示 → `test_receipt_never_attests_served_model_or_reasoning_support` は赤になるが、これは受理集合でなく診断・表現の pin なので mutation kill には数えない。
- sibling import が `sys.path`/`sys.modules` を汚染 → 新設 `test_import_preserves_import_state_and_ledger_output` が必要。現 plan では生存。
- `run_tests.py` の gate caller を削除 → 新設 integration node が必要。現 plan では生存。

## 総括

plan v1: **NO-GO**

最大のリスクは、receipt の構造が整っていることと、実際に同一入力を同じ要求・同じ実体で完走したことを混同している点です。現在の設計は、first user message の正規化 hash、親が記録する CLI rc、rollout 内の要求 slug、最小サイズ＋見出しだけの成果物 checker を組み合わせており、見た目の JSON は作れても、入力の完全一致・process 完走・成果物の arm 帰属・served backend identity を証明できません。さらに `ultra` を rc=0 とするテストは、unsupported request を valid receipt として受理する挙動を固定しています。少なくとも gate caller、arm/artifact 一意性、raw input 束縛、launcher receipt、malformed event、padded fragment、invalid reasoning の負例を追加し、served identity 不在の receipt を比較対象外へ隔離するまで、pilot の coverage/token/model 結論を T-184 へ参照させてはいけません。pytest は未実走であり、緑とは記録していません。