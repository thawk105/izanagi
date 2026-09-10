## 総括

- **must-fix — recovery の拡張 seam が実質的に存在しない（scope 内）。** `allow_recovered_abandonment` は未参照で、event 表へ `recovery` を足しても terminal として解釈される。次 wave は profile/adapter だけで実装できず、core 再改修が必要になる。[attempt_registry_core.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:87) [attempt_registry_core.py:920](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:920)

- **must-fix — core の genesis API に 8c 固有の manifest 契約が残り、共通 core という約束を満たさない（scope 内）。** 8b は使用しない `manifest_path`・`manifest_sha256`・`freeze_id` を渡さないと genesis を作れず、しかも値は成果物へ封印されない。[attempt_registry_core.py:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:104) [attempt_registry_core.py:1060](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:1060)

- **must-fix — 段4変異 M1 の「観測後 retry 禁止」は kill されない（scope 内）。** テストは `observed` terminal を作り、「non-retryable outcome」で先に拒否されるため、観測固有の検査を削除しても緑のままである。[test_attempt_registry_core_s8b_profile.py:306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:306) [attempt_registry_core.py:827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:827)

- **should-fix — equivalence test が production 定数を期待値にも流用しており、凍結 path・公開 signature の回帰を偽緑にできる（scope 内）。** 現 HEAD の値は正しいが、既定 path を変更すると legacy/core/facade が一緒に動き、比較は通る。[test_attempt_registry_core_equivalence.py:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_equivalence.py:94) [trial_registry.py:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:58)

- **should-fix — facade の公開 namespace は完全同値ではなく、2 名増えている（scope 内）。** 消えた public 名はないが、`PurePosixPath` と `attempt_core` が新たに `trial_registry.X` として露出する。[trial_registry.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:24) [trial_registry.py:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:43)

- **should-fix — 最終 HEAD は reports が記す所有面を越えて docs と `output/**` を変更している（実装 scope 外）。** registry の値・受理集合は変わらないが、公開文書・insight 参照集合が増え、報告だけでは最終差分を説明できない。[stage4-adjudication.md:104](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/stage4-adjudication.md:104) [phase3-8b-restart-runbook.md:424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/docs/phase3-8b-restart-runbook.md:424) [README.md:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/output/insights/2026-08-22_t1484-floor-restart-registry/README.md:1)

- **nit — M3/M4/M5 は kill されるが「赤理由が一つ」にはなっていない。** facade 再束縛検査や budget key 検査が重複し、変異時に複数 test が同時に赤くなる。成果物の受理集合には影響しないが、変異帰属が曖昧になる。[test_attempt_registry_core_equivalence.py:428](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_equivalence.py:428) [test_attempt_registry_core_s8b_profile.py:549](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:549)

## 詳細

### 1. recovery seam

`SchemaProfile.event_keys` は任意 event 名を表現できるものの、replay は `start`、seal、classification、observation 以外をすべて terminal 分岐へ送ります。`_parse_row` も同じく残りを terminal schema として検査します。[attempt_registry_core.py:616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:616) [attempt_registry_core.py:920](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:920)

段4が要求した「recovery event 本体ではなく、載せられる穴」にも達していません。event handler/policy callback など、terminal 以外の profile event を委譲できる seam が必要です。

**未修正時の成果物影響:** 8b profile に `recovery` を追加しても受理集合は増えず、terminal field 不足として拒否されるか terminal と誤解釈されます。

### 2. core に残る 8c genesis 契約

`create_attempt_registry_genesis()` は全 domain に manifest path/hash を必須化し、`build_genesis_fields` の型も manifest 前提です。一方、8b genesis schema に manifest field はなく、builder も設定されていません。[s8b_attempt_profile.py:277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_attempt_profile.py:277) [s8b_attempt_profile.py:418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_attempt_profile.py:418)

そのため 8b test は架空の `_MANIFEST` と `output/s8b-freeze/holdout_freeze.json` を渡していますが、それらは生成 row に入りません。[test_attempt_registry_core_s8b_profile.py:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:81)

literal 検査も `trial_id` 等の5文字列しか見ず、この漏れを検出しません。[test_attempt_registry_core_equivalence.py:455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_equivalence.py:455)

**未修正時の成果物影響:** 任意の安全な manifest path・任意の64桁 digest・任意の `freeze_id` を渡しても同じ8b genesis bytesになり、API入力と封印された証拠の対応が偽装可能です。

### 3. 変異 M1

観測後テストが作る terminal は `terminal_status="observed"` です。後続 reserve はまず「previous terminal が retryable-failure か」を検査し、観測有無へ到達する前に拒否されます。テスト自身も観測専用文言ではなく `a slot after a non-retryable outcome...` を期待しています。[test_attempt_registry_core_s8b_profile.py:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:319) [test_attempt_registry_core_s8b_profile.py:331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:331)

8b の理由集合は空なので、test-only synthetic profile にだけ理由を一つ注入し、「retryable terminal かつ observation 有り」を構成する必要があります。

**未修正時の成果物影響:** `forbid_retry_after_observation` または core の観測検査だけを無効化してもテストは赤くならず、将来理由集合が確定した際に観測後 slot が受理され得ます。

### 4. facade・golden の裏取り

静的 AST 比較では以下は反証されませんでした。

- 抽出前の public 名は一つも消えていない。
- 公開6関数の引数・既定値・戻り annotation は抽出前と同一。
- 6関数はすべて実 `def` で、当該名への top-level 再束縛はない。[trial_registry.py:2302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:2302) [trial_registry.py:2834](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:2834)
- `assert_trial_registry_acceptance` は `5a4cbfa8` 版との属性除外 AST が完全同一。[trial_registry.py:4843](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:4843)
- C03 必須13関数は全て実 `def`。
- 既存 consumer が参照する load/reserve/classify/observation/terminal は残っている。

ただし permanent test は signature を pin せず、旧実装相当 builderも production 定数を参照しています。既定 path は literal golden として独立固定すべきです。

**未修正時の成果物影響:** `DEFAULT_ATTEMPT_REGISTRY_PATH` を変更すると registry の生成・参照先が変わるのに三者比較は通り、凍結参照の破壊を検出できません。

### 5. 取り残した層と所有面

固定14-file scan は15へ正しく追随しています。[test_reflux_formal_consumer.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_reflux_formal_consumer.py:22) [test_reflux_formal_consumer.py:816](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_reflux_formal_consumer.py:816)

repository-wideの literal・file集合検索では、これ以外に追随必須の固定集合は反証されませんでした。plain-runner、campaign import、production sibling scan は動的列挙です。新 core は subprocess/Gitを持たないため spawn-site固定表への追加も不要です。

所有面では次を確認しました。

- 既存 `s8b_*.py` の編集なし。追加されたのは新規 profile のみ。
- `s8c_preregistration_evidence.py` は未変更。
- 8b retryable理由集合は空。[s8b_attempt_profile.py:379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_attempt_profile.py:379)
- recovery event は schema 表に存在せず、production 8b 配線もない。
- `output/s8b-freeze/**`・`output/s8c-*` の凍結成果物は未変更。
- 一方で runbook、docs spool、`output/insights/**` は変更済み。実装子 reports の「docs/output未変更」は各子の作業時点では成立しても、最終HEADの説明にはなっていません。[s5b1-report.md:69](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s5b1-report.md:69) [s5b2-report.md:6](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s5b2-report.md:6)

**未修正時の成果物影響:** registry bytes・受理集合は不変ですが、本commitが所有する文書・output参照集合は段4の実装面より広いままです。

## 変異 M1〜M6 の静的判定

- **M1: 未 kill。** 観測固有 clause の単独削除が生存する。
- **M2: kill。** strict reason mismatch test が拒否されなくなる。
- **M3: kill。** 実 `def` 消失をC03と再束縛guardが検出する。
- **M4: kill。** `create_attempt_registry_genesis` 再束縛をguardが検出する。ただし2 testが赤。
- **M5: kill。** repetition込みbudget keyへ戻すとkey同値比較とcell-wide budget testが赤。
- **M6: kill。** unknown eventの期待文言検査がcore/8b双方で赤。

pytestは実走しておらず、以上は静的検査結果です。実装子reportsに記録された過去の直接実走も、今回の緑としては採用していません。