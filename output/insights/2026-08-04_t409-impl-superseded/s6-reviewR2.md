## 所見

### R2-1 — fresh trigger campaign が artifact admission で自己拒否する

- file:line: [artifact_admission.py:648](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/artifact_admission.py:648)、[wal.py:633](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/wal.py:633)、[wal.py:674](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/wal.py:674)
- 根拠: `artifact_admission` は `_validate_attempt_topology()` に `trigger_grammar_locked` を渡さないため既定値 `False` になる。v2 receipt は必ず 674–679 行で拒否される。一方、通常 replay は [wal.py:803](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/wal.py:803) で lock の grammar 宣言を渡しており、経路間で不整合。
- 成果物影響 (DW-G05): 新規 trigger campaign は `AdmittedCampaign` を取得できず、Layer3・p3 autonomous・admission-aware selection が全面停止する。
- 提案: **must-fix**。artifact admission も同じ lock 判定を渡し、実 v2 trigger receipt を持つ campaign の正例を追加する。

### R2-2 — 1 個の無関係な source tree で旧 record 全件を一括 PASS にできる

- file:line: [trigger_gate_reinspection.py:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/trigger_gate_reinspection.py:64)、[trigger_gate_reinspection.py:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/trigger_gate_reinspection.py:131)、[test_artifact_admission.py:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/tests/test_artifact_admission.py:166)
- 根拠: `create_reinspection_ledger()` は同じ `source_root` を全 record に渡すが、その source と record の `src_token`・実装 provenance を一切照合しない。テストも一つの `izanagi_gate_pass = true;` を全 build_start に使う。対象実 artifact は [wal.jsonl:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/runs/wal.jsonl:1) と [wal.jsonl:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/runs/wal.jsonl:7) で異なる `src_token` を持つ。
- 成果物影響 (DW-G05): 任意の安全な現行 source 一つで、別実装から作られた旧 trigger WAL を `admitted-reinspected` に昇格できる。
- 提案: **must-fix**。record ごとの source/provenance 束縛を必須化し、再計算した evidence と記録済み `src_token` を照合する。照合材料がない record は A-9 どおり `SOURCE_UNAVAILABLE` にする。

### R2-3 — S8B oracle は receipt/grammar を lock せず、report も共有 admission を迂回する

- file:line: [s8b_oracle_driver.py:981](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8b_oracle_driver.py:981)、[s8b_oracle_report.py:1281](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8b_oracle_report.py:1281)、[s8b_oracle_report.py:1025](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8b_oracle_report.py:1025)
- 根拠: oracle lock は manifest/block/campaign ID だけで、`search_config.build_admission` と trigger grammar がない。report は `wal.read_records_collected()` で raw WAL を読み、build_start について `variant/src_token/genome` しか比較せず、v2 receipt body・SHA・topology を検証しない。この lock は共有 artifact admission からは未登録 pre-policy artifact と判定される。
- 成果物影響 (DW-G05): receipt を改竄・欠落させた unbound trigger WAL から official oracle observations を生成でき、同時に正規の admitted view は発行不能。
- 提案: **must-fix**。mixed oracle campaign の lock に current policy と grammar を束縛し、report は共有 admitted view、または同値の全 v2 topology 検査済み viewだけを読む。

### R2-4 — Layer3 に reinspection ledger を渡す経路がない

- file:line: [layer3_report.py:379](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/layer3_report.py:379)、[layer3_report.py:387](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/layer3_report.py:387)、[artifact_admission.py:714](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/artifact_admission.py:714)
- 根拠: shared API は `reinspection_ledger=` を持つが、`build_report()`・`render()`・CLI はその引数を公開せず、常に ledger なしで呼ぶ。
- 成果物影響 (DW-G05): 正当に再検査できる旧 trigger campaign でも Layer3 v4 を生成できない。
- 提案: **must-fix**。明示的な ledger path を Layer3 API/CLI から共有 admission へ伝播し、その hash を report receipt に残す。

### R2-5 — Layer3 v4 schema は正当 overlay を拒否する一方、reinspection proof 欠落を許す

- file:line: [layer3_schema.json:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/layer3_schema.json:35)、[layer3_schema.json:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/layer3_schema.json:40)、[layer3_schema.json:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/layer3_schema.json:65)、[artifact_admission.py:570](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/artifact_admission.py:570)
- 根拠: schema は `verification_status = not-evaluated-by-overlay` 固定だが、再検査済み overlay decision は裁定どおり `historically-certified` を保存する。また `reinspection` は required でなく、ledger SHA は nullable。したがって正当 overlay receipt は赤、証拠を削除した `historical-trigger-reinspected` receipt は緑になる。
- 成果物影響 (DW-G05): 正当な歴史的 report は発行不能なのに、detached ledger 証拠を失った report は schema-valid になる。
- 提案: **must-fix**。classification ごとの exact `oneOf` にし、historical-trigger-reinspected では非 null ledger SHA・record SHA 集合を条件付き required にする。

### R2-6 — receiptless abort の「閉 enum reason」が validator に存在しない

- file:line: [wal.py:762](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/wal.py:762)、[artifact_admission.py:657](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/artifact_admission.py:657)、[s4-adjudication.md:20](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s4-adjudication.md:20)
- 根拠: receiptless attempt の abort は attempt ID だけ検査し、`reason` の欠落・任意文字列を受理する。artifact admission も receiptless build_start をそのまま読み飛ばして `admitted-new-schema` にできる。
- 成果物影響 (DW-G05): 裁定外の拒否理由を持つ偽 pre-admission terminal が admitted WAL view に入る。
- 提案: **must-fix**。全正規 issuer を列挙した共有 closed enum と reason 別 payload 形を検証し、unknown/missing reason の負例を置く。

### R2-7 — 新しい文法 authority が oracle の 5-generator pin 閉包外

- file:line: [s8b_oracle_manifest.py:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8b_oracle_manifest.py:45)、[s1_direct_comparison.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s1_direct_comparison.py:39)、[s1_direct_comparison.py:522](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s1_direct_comparison.py:522)、[s8b_oracle_report.py:904](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8b_oracle_report.py:904)
- 根拠: manifest が live hash するのは正確に5ファイルだが、そのうち materializer と report が未 pin の `trigger_gate_language.py` に新規依存する。文法 checker の bytes を変更しても5本の hash は変わらない。
- 成果物影響 (DW-G05): 再発行後の oracle manifest が、実際の acceptance authority の変更を検出できず、materialization/report semantics が pin 緑のまま drift する。
- 提案: **must-fix**。既存5本の pinned file 内で recognizer source SHA を固定して live 照合する。6本目追加は exact-five 契約変更になるため、行うなら別裁定が必要。

## 構成できなかった面

- B-5 の編集禁止・編集回避ファイルは status/diff に皆無。generic quarantine 経由の trigger 検査追加は A-12 の承認経路で、sort/backoff marker には発火しない。
- SourceEvidence v1 の直列化 key、非 trigger cache preimage、artifact admission v1 分岐に変更は見つからなかった。Layer3 の非 trigger v4 化は B-7 の明示承認範囲。
- 既存 sort sentinel は byte 不変。期待値変更は承認済み trigger whitespace 2 node と B-7 の v3→v4 assertion のみ。テスト削除なし、skip/xfail は HEAD/現行とも22件で diffなし。
- role diff は文法 v1 と事実配線だけ。manifest/review-ledger/adapter の SHA は一致し、`python3 tools/check_codex_agents.py` は rc=0。s5-unitB2 の一時的 adapter 赤は現統合 diff では refuted。
- 直接の外部再発行対象変更は `s1_direct_comparison.py` と `s8b_oracle_report.py` で、B-5 の編集可範囲。transitive pin 例外は R2-7。
- `git diff --check` は異常なし。pytest は指示どおり未実走。

## 総括

- must-fix 候補: **7件**。
- 最重要所見: R2-2 の record 非束縛再検査と、R2-3 の S8B oracle admission 迂回。
- 即時の全面回帰は R2-1で、fresh trigger campaign が shared admission を通れない。
- 親実測: real v2 trigger の admission→Layer3/p3、record 別 legacy reinspection、overlay Layer3 schema。
- 親実測: S8B oracle receipt/hash/grammar-lock 変異、unknown receiptless reason、recognizer pin 変異。
- pytest は Pegasus 計算ノードで関連群を実走すること。