## 変更計画 (A)

- [tools/check_ai_provenance.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:113) 付近に frozen `KnownViolationSpec(commit, expected_finding_kind)`、finding 種別定数、固定 tuple `KNOWN_PROVENANCE_VIOLATIONS` を追加する。full SHA と期待種別は次の 6 件だけとする。

| full 40-hex SHA | `expected_finding_kind` |
|---|---|
| `88f0f9f081f7c76c8ab5fc4a94e2640f70af129b` | `missing-ai-agent` |
| `85dacc27054db0bd3db55d73cab4f8ca3b4843e5` | `missing-ai-agent` |
| `6e69ca5c2bc2df403e1cda595aeffcba3a97c248` | `missing-ai-agent` |
| `16affe169185040b33f8c6cbdd452260bddc4089` | `missing-ai-agent` |
| `905c867a7b2342ff250a1bcf28a3ce74abdacc06` | `missing-ai-agent` |
| `b0a07672737cf03424ec1790cc25a06e4c85b737` | `missing-codex-author` |

  `3f2c43d7580b8c26724d90278589862057508965` は含めない。registry 構築時に 40 桁小文字 hex、SHA 重複なし、finding 種別が閉集合内であることも検査し、壊れた台帳は `RuntimeError` → rc=2 とする。

- [tools/check_ai_provenance.py:176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:176) の既存 `CommitAudit` に、`normal_findings` と同順の `normal_finding_kinds` を追加する。[HistoryAudit:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:205) には既存 3 field を維持したまま、既定値が空 tuple の `known_violations` を末尾追加する。`HistoryAudit.findings` は「新規 finding のみ」という意味へ限定する。

- [tools/check_ai_provenance.py:791](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:791) の `_normal_commit_audit()` で finding 発生元を構造化する。

  - `validate_message()` の exact な「AI-Agent trailer がない」だけを `missing-ai-agent` とする。
  - `validate_implementation_author()` が返す非 waiver の finding だけを `missing-codex-author` とする。
  - path、subject、message、finding 文字列の前方一致から種別を推測しない。
  - correction / waiver の既存判定順と `normal_findings` の逐語・順序は変えない。

- [tools/check_ai_provenance.py:849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:849) の `_audit_history()` で、既存の forward-correction 処理後に normal finding を分離する。

  - `audit.commit` の full SHA を台帳 dict へ完全一致 lookup する。
  - SHA と `expected_finding_kind` が一致した finding を entry 当たり 1 件だけ `known_violations` へ移す。同種 finding が重複した場合、2 件目以降は新規に残す。
  - 同じ SHA の別種 finding、同じ subject/path の別 SHA、短縮 SHA は抑止しない。
  - 台帳 SHA が selected revision set にあり、correction 抑止後の実効 finding が 0 件なら `known-violation-stale` を新規 finding として追加する。
  - 台帳 SHA が範囲外なら stale にしない。期待種別と異なる finding がある場合は、その finding 自体を新規として残す。
  - correction findings は常に新規側とし、既存 `suppressed_missing`、`corrected`、`waived` の意味を変えない。

- [tools/check_ai_provenance.py:1790](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1790) の `main()` では history 分岐だけが `known_violations` を受け取る。各既知 entry を stdout に `known-violation sha=<full SHA> finding=<kind>`、続いて `known-violations=<N>` と出す。これは新規 finding の有無にかかわらず出力する。

- [tools/check_ai_provenance.py:1845](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1845) の rc 分岐は `HistoryAudit.findings`、すなわち新規 finding だけを見る。既知のみなら rc=0、新規が 1 件以上なら rc=1。既知を含む監査の終端要約は「新規違反なし／新規違反 N 件」とし、既知 0 件の既存出力と `--message-file` の逐語出力は維持する。

- [docs/provenance/audit.md:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/docs/provenance/audit.md:13) の `PR-A02` 内へ台帳契約を統合する。単純追記ではなく、現行 594 bytes の節を意味等価に圧縮しつつ、full SHA＋finding 種別一致、不一致/stale、新規だけの rc、既知の stdout 公開、message-file/correction/waiver 不変を記録する。code はこの文書を parse しない。

## 変更計画 (B)

- [tools/run_tests.py:504](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:504) の `_is_acceptance_run()`、許可 option 集合、戻り値は変更しない。

- [tools/run_tests.py:1756](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:1756) の `main()` にある 3 preflight の順序と rc を維持する。

  - `_preflight_unstaged_deletions()` の非受入時 return: [590-594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:590)
  - `_preflight_ruleops()` の非受入時 return: [628-632](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:628)
  - `_preflight_submodule()` の targeted 継続経路: [697-711](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:697)

- [tools/run_tests.py:1780](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:1780) の login dispatch early-return 群の直後、現行 `use_xdist = False` の直前へ 1 回だけ判定を置く。False なら stderr に次の 1 物理行を `flush=True` で出す。

  `警告: 受入形でない走行です。この結果を受入全走として扱わないでください。`

  この位置なら login 親は dispatch 前に出さず、実際に pytest を起動する compute/bounded child 側だけが出すため、同一走行での二重表示を避けられる。警告は既に skip 済みの 3 acceptance-only gate を可視化するだけで、pytest argv、受理集合、rc を変えない。

## テスト計画

[orchestrator/tests/test_check_ai_provenance.py:1309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1309) 付近へ以下を追加する。

- `test_known_violation_ledger_is_exactly_six_literal_entries`

  production 定数から期待値を導出せず、6 件ちょうど、tuple 順、full SHA 集合、各 `expected_finding_kind` をリテラルで pin する。7 件目の full SHA が集合外であることも明記する。

- `test_known_violation_ledger_matches_real_commit_findings`

  6 SHA を実 repo の `_audit_history()` へ渡し、各 entry が期待種別 1 件に一致し、新規 finding が 0、既知集合が 6 件になることを固定する。

- `test_known_violation_requires_exact_full_sha_and_finding_kind`

  短縮 SHA entry と誤った finding 種別を別ケースにし、どちらも既知扱いされないことを固定する。

- `test_known_violation_suppresses_only_one_expected_finding`

  同一 SHA・同一種別 finding を人工的に重複させ、1 件だけ既知、残りは新規になることを固定する。

- `test_known_violation_selected_clean_entry_is_stale`

  台帳 SHA を正常 commit に向けた synthetic history で stale finding と rc=1 を固定する。

- `test_known_violation_outside_range_is_not_stale`

  台帳 entry が selected set 外なら finding を増やさないことを固定する。

- `test_known_violation_stdout_is_public_on_rc0`

  既知だけの range で rc=0、stdout に full SHA と `known-violations=1`、stderr に新規 finding なしを exact pin する。

- `test_unledgered_3f2c43d7580b_remains_new_and_rc1`

  `3f2c43d7580b8c26724d90278589862057508965^!` を監査し、台帳出力なし、missing trailer finding、rc=1 を固定する。

既存の [forward-correction 順序不変テスト:1628](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1628)、[worker/ancestry 等価テスト:3883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:3883)、[empty-range テスト:4059](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:4059) へ `known_violations` の空／等価性 assertion を足す。`--message-file` の exact 出力テスト [2167-2187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:2167)、correction 群、waiver 群は期待値を変更せず回帰検査として使う。

[orchestrator/tests/test_run_tests_preflight.py:220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_run_tests_preflight.py:220) 付近へ追加する。

- `test_nonacceptance_main_warns_once_on_stderr_and_preserves_rc`
- `test_acceptance_main_does_not_emit_nonacceptance_warning`
- `test_login_parent_defers_nonacceptance_warning_to_execution_child`

最初のテストは 3 preflight と pytest call を mock し、警告が stderr の exact 1 行、stdout は空、pytest の sentinel rc がそのまま返ることを pin する。3 番目は login 親の mocked dispatch 経路では警告が出ないことを固定する。

既存出力依存の静的確認結果は次のとおり。

- [test_main_warns_on_user_dist_override_without_reordering_args:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_run_tests_nproc.py:174) は影響経路上だが substring assertion だけなので期待値変更不要。一般警告追加後も `--dist loadgroup` assertion が固有警告を検出する。
- [test_targeted_missing_submodule_warns_without_init:627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_run_tests_preflight.py:627) は `_preflight_submodule()` の直接テストで、`main()` の新警告を通らない。
- [test_run_tests_task_run.py:407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_run_tests_task_run.py:407) 以降の exact stdout/stderr テストは `_call_and_record()`、`_record_task_run()`、conftest hook、または直接 `python -m pytest` を検査しており、新しい `main()` 警告の影響外。
- repo 内には、非受入形の `RT.main()` 成功経路について stderr 全体を空文字と pin する既存テストは見つからなかった。したがって静的には既存テストの期待値変更は不要だが、実測は未実施。

親の実走対象は、関連 2 test file、`python3 tools/run_tests.py` の受入全走、`check_docs.py`、`check_codex_agents.py`。commit 後の既定 provenance 監査は設計どおり「既知 6・新規 1・rc=1」が期待値であり、緑とは扱わない。

## 検出力の保存

- 履歴非書換え: 変更対象は checker・runner・pytest・`PR-A02` のみで、commit object/message の変更手順を含めない。
- SHA exact: [固定台帳と `_audit_history()`:113,849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:113) が full SHA の dict equality だけを使い、短縮 SHA テストで固定する。
- finding 種別一致: [CommitAudit と `_normal_commit_audit()`:176,791](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:176) で発生元から種別を持たせ、path/message/prefix 判定を作らない。
- stale: [ `_audit_history()`:849-959](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:849) が selected entry の実効 finding 0 件を新規 finding にする。
- 既知公開: [main():1832-1852](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1832) が rc 分岐前に full SHA と件数を stdout へ出す。
- message-file/correction/waiver 不変: [main():1795-1826](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1795) の message branch と既存 correction/waiver データフローを台帳分離の外に置く。
- 内容 pin と 7 件目: [test_check_ai_provenance.py:1309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1309) の literal tuple test と実 commit の rc=1 test が、追加・削除・種別変更を可視化する。
- runner 受理集合・rc: [run_tests.py:504-562,1756-1840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:504) は判定・gate・pytest return を維持し、stderr `print()` だけを足す。

## リスクと未解決点

- provenance 文書 family は現在 8,981 / 9,000 bytes、`audit.md` は 1,333 / 1,600 bytes。単純追記は family 上限違反になる。`PR-A02` の現行 594 bytes を約 592 bytesへ意味等価に再構成する案なら収まるため、上限引上げ・新規 reference・`check_docs.py` 変更は行わない。
- `HistoryAudit.findings` が新規専用になる。静的検索では consumer は同 checker の `main()` と当該 pytest file だけだが、親レビューで repository-wide `rg "HistoryAudit\\(|\\.findings"` を再確認する。
- 警告を execution-side に置くため、site 判定拒否や dispatcher 起動失敗のように pytest が始まらない invocation では出さない。目的が「結果の誤記録防止」ではなく「全 invocation への無条件表示」なら、親が plan v2 で位置を再裁定する必要がある。推奨は二重表示を避ける現案。
- 既定 full-history 監査は 7 件目により rc=1 のままになる。これは P1 と要求された検出結果であり、台帳へ追加して緑化してはならない。
- 変更量見積り: A production 約 85–110 行、A tests 約 130–170 行、`PR-A02` 12 行置換、B production 約 5–8 行、B tests 約 35–50 行。合計約 267–350 touched lines。
- 段 5 は 2 並列可。実装子 A は `tools/check_ai_provenance.py` と `test_check_ai_provenance.py`、実装子 B は `tools/run_tests.py` と `test_run_tests_preflight.py` を排他的に所有する。dev-wave の実装子契約に従い、`docs/provenance/audit.md` は親が統合時に担当する。

## 総括

6 SHA だけを full SHA＋finding 種別で固定し、既知と新規を構造的に分離する。  
既知は常時 stdout へ公開し、rc は新規だけで決める。  
`3f2c43d7580b…` は台帳外の新規違反として rc=1 を維持する。  
runner 警告は stderr の 1 行だけで、gate・受理集合・rc を変えない。  
read-only のため pytest は実行しておらず、緑は主張しない。