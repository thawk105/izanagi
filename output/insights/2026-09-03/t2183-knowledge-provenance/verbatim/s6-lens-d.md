## 変異追跡

| 変異 | 対応テスト | 静的追跡結果 |
|---|---|---|
| M1 | `test_knowledge_report_projects_verified_receipt_sources` | `dict` 期待に対して `None` となり赤。ただし M3/M4 テストも `None` を添字アクセスして赤になるため単一理由ではない。 |
| M3 | `test_schema_rejects_unknown_nested_knowledge_key` | 変異後は未知 key が schema を通り、`pytest.raises` が成立せず赤。改変は report 生成後なので WAL・receipt 層は関与しない。 |
| M4 | `test_schema_rejects_missing_injected_sources` | 変異後は欄欠落が schema を通り、`pytest.raises` が成立せず赤。M3 とは別入力で単一理由。 |
| M6 | `test_campaign_chain_reads_legacy_layer3_without_knowledge_provenance` | `setdefault` を外すと persisted の欠落と fresh の `null` が不一致になり赤。ただし非 knowledge campaign しか試していない。 |
| M7 | `test_report_rejects_receipt_replaced_after_build_start` | 現行では receipt/lock 不一致で期待どおり拒否。事前登録どおり raw `workload` へ差し替えると後段 schema も拒否し、M1/M3/M4 も赤になるため単一理由ではない。 |

M3・M4・M6の登録変異は対応テストで殺せる。M1・M7は殺せるが、現状のままでは F820 の単一理由証拠にはならない。

## must-fix: M6 は既存 K2 report の互換性を検査していない

M6 テストは `knowledge_provenance` が元から `null` の非 knowledge campaignだけを使うため、旧 K2 report の「欠落対 fresh object」という本来の互換ケースを守っていない。

- 根拠: [_layer3_campaign](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_autonomous_trial_completeness.py:3551) の `search_config` には knowledge binding がなく、[M6テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_autonomous_trial_completeness.py:4733) も削除値が `None` だと明記している。一方、比較は両側へ一律 `setdefault(..., None)` するだけであり、[fresh K2 report の object](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_report.py:760) は保持されたまま [canonical bytes 比較](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/autonomous_trial_completeness.py:5016) に入る。
- 成果物影響: 新欄導入前の K2 persisted report は欠落→`None`、fresh は object となって拒否され、その report を参照する試行台帳・certified 選択の受理集合が縮む。
- 判定/最小是正: **must-fix** — knowledge-aware campaign から旧 report を作って欄を削除する正例を追加し、persisted に欄が無い場合だけ fresh 側も比較射影から除外する。同時に、欄が存在する report の digest 改変が拒否される負例を追加する。

## must-fix: 二段の出所一致は恒真的な正例しか持たない

`declared_sources` と `injected_sources` の出所差を検査する部分は、同じ `expected_sources` を両欄へ入れて比較しているだけで、verified/canonical 一致検査の退行を検出できない。

- 根拠: [reportテスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_layer3_report.py:1696) と [readerテスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_p3_s4_loop.py:1870) は双方とも一つの `expected_sources` を二欄へ流している。実装も [verified/canonical 一致検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:842) 後に canonical 側だけを返し、[同じ配列から二欄を生成](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:960) している。M7 は top-level digest を壊すため、この一致検査より前で止まる。
- 成果物影響: 一致検査が削除されると、verified source が canonical manifest と異なる receipt でも受理され、材料レポートは canonical 値を両欄へ複製して偽の `injected_sources` 参照を残す。
- 判定/最小是正: **must-fix** — BUILD_START 後に receipt の verified source `sha256` と `verification.observed_sha256` を揃えて変更し、canonical manifest と lock は維持する負例を追加する。これなら exact key・kind・verification 検査を通り、一致検査だけで拒否される。

## must-fix: M1 と M7 は事前登録した単一理由性を満たさない

M1 は schema 負例の前提生成まで壊し、M7 の raw workload 変異は receipt gate だけでなく report schema にも殺される。

- 根拠: M1 で出力を `None` にすると、[M3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_layer3_report.py:1715) と [M4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_layer3_report.py:1727) が mutation 操作前に `None` を添字アクセスする。M7 の出所とされた `workload` は [search_configそのもの](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_report.py:820) だが、provenance schema は [exact 4-key object](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_schema.json:31) を要求するため後段 schema でも赤になる。
- 成果物影響: この KILLED を単一 gate の証拠として採用すると、live receipt 由来であることを独立に証明しないまま K2 材料レポートを certified 選択の根拠へ昇格できてしまう。
- 判定/最小是正: **must-fix** — M3/M4 は schema-valid な独立 specimen を用いる。M7 は通常時に同一の schema-valid 値を返しつつ receipt 差替えだけを見逃す変異、例えば検証済み WAL projection からの生成へ再照準する。

## nit: source/identity schema の負例がない

新 schema の source・identity exactness、空配列・重複配列に対する拒否は、新規テストでは直接固定されていない。

- 根拠: schema は [配列の `minItems`/`uniqueItems`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_schema.json:38) と [source/identity の `additionalProperties: false`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_schema.json:279) を追加したが、負例は provenance 直下の未知 key と `injected_sources` 欠落だけである。
- 成果物影響: WAL producer は既存検査で防護されるが、standalone schema reader の材料レポート受理集合は将来の schema 退行で広がり得る。
- 判定/最小是正: **nit** — source未知 key、identity未知 key、空・重複配列を直接 `_validate_schema` に通す parameterized 負例を追加する。M5の `kind` 制限は事前登録どおり冗長 gate 扱いでよい。

## その他の確認

- 新規テストは実体の receipt、WAL、artifact admission、schema、完全性比較を通っており、新規経路を stub/monkeypatch していない。
- fixture の commit・source digest・manifest digest は実行時に導出され、working-tree hash、時刻、絶対パスなどの期待値焼き込みはない。
- commit 差分には既存 assertion の削除・反転・緩和・skip・xfail はない。既存 v2 fixtureへ forward field の削除を追加しただけで、共有 `_campaign` の既定経路も維持されている。
- 新規 test file はなく、repo 内検索でも今回の関数名追加に追随必須な exact test-name/file-set meta-test は見つからなかった。
- pytest・変異走はこのレビューでは実行していない。

## 総括

must-fix は重い順に次の3件。

1. M6 が旧 K2 report を試しておらず、現実装もその legacy report を拒否する。
2. verified/canonical source 不一致の負例がなく、二段の出所主張が恒真的な候補集合に依存している。
3. M1・M7 は複数テスト／後段 schema に殺され、F820 の単一理由変異として採用できない。