## 所見一覧

1. **real — M2 は単一理由変異ではない。**

   - コード: [policy.py:492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:492) の scalar membership の内側に、K2 専用 `knowledge_use` 検査が [policy.py:521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:521) でネストされている。
   - M2 で K2 を `:492` の集合から外すと、backoff 文法・value 一致だけでなく参照整合性検査も迂回する。
   - 放置時: M2 を「backoff scalar 分岐だけを殺した単一理由 KILLED」と記録すると、異なる検査を同時に無効化した結果を一つの検出力として過大計上する。
   - 判定: **real**。production 実装の受理欠陥ではなく、変異事前登録の欠陥。

2. **real・scope 外 — acceptance duration ledger に旧 13 件名が残り、新しい 4 node が未収載。**

   - コード: [acceptance_duration_ledger.json:5605](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/acceptance_duration_ledger.json:5605) と [同:5608](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/acceptance_duration_ledger.json:5608) は改名前の `thirteen` nodeid。現行名は [test_codex_agents.py:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/test_codex_agents.py:123) と [同:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/test_codex_agents.py:129)。新規 `knowledge_use` の 2 param node は [同:968](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/test_codex_agents.py:968) にあるが ledger に無い。
   - 未収載 node は収集・実行・合否から除外されず、未知 cost に置換される [conftest.py:1583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/conftest.py:1583)。
   - 放置時: 検出力や受理集合は変わらないが、4 live node の scheduling cost が擬似値となり、2 旧 entry が不活性なまま残る。
   - 判定: **real・scope 外**。実測値を捏造して直してはならず、変更後 JUnit による add-only 更新として**実装せず裁定パッケージへ**。

3. **refuted — 追加テストが stub だけを通って緑になる経路はない。**

   - テストは repo の checker を直接 import し [test_codex_agents.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/test_codex_agents.py:20)、実 `ROLE_POLICY` を import する [同:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/test_codex_agents.py:28)。
   - source-wrapper 負例は実 `get_role_spec()` と実 `_validate_source_output_shape()` を呼ぶ [同:1341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/test_codex_agents.py:1341)。`replace()` は検査対象 schema の変異であり依存先の stub ではない。production checker も同 helper を呼ぶ [check_codex_agents.py:317](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/tools/check_codex_agents.py:317)。
   - literal/value テストは実 `validate_output_semantics()` を呼び [test_codex_agents.py:949](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/test_codex_agents.py:949)、そこから実 `backoff_hole_grammar.validate_backoff_implementation()` へ到達する [policy.py:499](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:499)。
   - `knowledge_use` 正負例も同じ実 validator を呼ぶ [test_codex_agents.py:1001](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/test_codex_agents.py:1001)。
   - 放置時: なし。これらは schema と runtime を含む E2E ではなく、実 semantic/helper の単体検査として有効。
   - 判定: **refuted**。

4. **refuted — 既存 assertion の反転・緩和・skip・削除はない。**

   - `git show f015d7e80 -- orchestrator/tests/test_codex_agents.py` では、許可済みの 13→14 と関数名更新、K0 の正負例を同じ内容のまま K0/K2 loop へ包む変更、K2 tuple 追加、参照整合性テスト追加だけ。
   - 既存 K0 の有効値 2 件、無効値 5 件、`pytest.raises`、診断への入力反射禁止 assertion は [test_codex_agents.py:945](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/test_codex_agents.py:945) 以降に維持されている。
   - 放置時: 既存 K0 受理・拒否期待値の検出力は従来どおり。
   - 判定: **refuted**。

5. **refuted — K2 以外の role の受理集合は変わらない。**

   - 入力/output family と axis map は K2 の entry を追加しただけ [policy.py:340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:340)、[同:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:475)。
   - scalar 条件の membership 化も K0 の従来経路を保持する [同:492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:492)。
   - `f"{spec.name}"` は K0 では従来の逐語 `"coder-v4-autonomous"` と同じ文字列を生成し、判定条件を変えない [同:503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:503)。
   - 放置時: K2 以外の受理・拒否集合および K0 の診断内容に変化なし。
   - 判定: **refuted**。

6. **refuted — schema-valid かつ proposal-valid な K2 出力が参照整合性検査を回避する分岐はない。**

   - `validate_output_semantics()` は最初に入力 semantic を検査し [policy.py:394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:394)、K2 は入力 family [同:340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:340) と出力 family [同:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:475) の双方で一意に backoff 軸へ入る。
   - 軸・confidence・value・文法・value 一致を通過後、必ず K2 分岐 [同:521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:521) に到達する。
   - 検査前の例外は不正入力・不正 proposal を既に拒否しており、不正 `knowledge_use` を受理する bypass にはならない。
   - 放置時: 現行 membership を維持する限り、不正 index を持つ成功出力は受理されない。
   - 判定: **refuted**。ただし M2 のように `:492` から K2 を外すと本検査も同時に失われる。

7. **refuted — adapter byte parity と既存 13 adapter 不変性に欠陥はない。**

   - renderer は role-local source、manifest、role-local ledger、固定 policy version から JSON を `sort_keys=True, indent=2` で生成する [spec.py:803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/spec.py:803)、[同:871](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/spec.py:871)。
   - checker は全 adapter に対して actual text と renderer 出力を exact 比較する [check_codex_agents.py:235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/tools/check_codex_agents.py:235)。
   - K2 adapter の schema・ledger・source pin は renderer の構造と一致する [.codex adapter:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/.codex/role-adapters/coder-v4-autonomous-k2.json:139)、[同:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/.codex/role-adapters/coder-v4-autonomous-k2.json:240)。実ファイルは 17,790 bytes、SHA-256 `a41de8b5…aff914`。
   - `f015d7e80^..d87a8090a` の既存 source/adapter 限定 diff は 0。変更されたのは新規 K2 source と adapter だけ。`EXPECTED_ROLE_COUNT` は render 内容に含まれず、既存 role の ledger entry・manifest entry・policy version も不変。
   - 放置時: 既存 13 adapter の実 bytes と期待 render bytesは変わらず、K2 の drift は checker が拒否する。
   - 判定: **refuted**。

## 変異の単一理由性と期待 node

| 変異 | 変異時に赤となる完全な node 集合 | 単一理由性 |
|---|---|---|
| M1 | `orchestrator/tests/test_codex_agents.py::test_planner_and_coder_source_output_wrapper_shape_parity_is_enforced` | **成立**。pytest 上は role 別 parametrized node ではなく、5 role を loop する単一 node。K2 iteration だけで expected exception が消える |
| M2 | `…::test_coder_v4_output_semantics_requires_literal_only_single_statement_value_match`、`…::test_coder_v4_k2_knowledge_use_source_indices_are_valid_and_unique[invalid_knowledge_use0]`、`…[invalid_knowledge_use1]` | **不成立**。文法/value と参照整合性の二機構を同時に迂回する |
| M3 | `…::test_coder_v4_k2_knowledge_use_source_indices_are_valid_and_unique[invalid_knowledge_use0]`、`…[invalid_knowledge_use1]` | **成立**。前者は範囲外 index、後者は `use` が異なる同一 index なので schema の object-level `uniqueItems` では拒否されない [manifest.json:917](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/manifest.json:917) |

M2 の再照準案は、membership 全体ではなく K2 に対する文法 rejection だけを迂回する変異です。例えば [policy.py:503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:503) を変異させ、K2 のときだけ `decision.accepted == false` を拒否しない形にする。この場合、suffix 付き literal または追加文が受理されて literal/value test だけが赤になり、valid implementation を使う `knowledge_use` 2 node は参照検査へ到達したままです。

診断文字列 assertion は残っていますが、M1/M2/M3 の赤はいずれも「期待した例外が発生しない」という受理集合差であり、診断文字列だけの差を kill に数えていません。

## 閉包の全走査結果

| 面 | 実装位置 | 判定 |
|---|---|---|
| A role source | [.claude/agents/coder-v4-autonomous-k2.md:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/.claude/agents/coder-v4-autonomous-k2.md:1) | 実装済み |
| B manifest | [manifest.json:733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/manifest.json:733) | 実装済み |
| C count＋5 ledger | [review_ledger.py:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/review_ledger.py:13)、[同:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/review_ledger.py:26)、[同:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/review_ledger.py:57)、[同:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/review_ledger.py:80)、[同:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/review_ledger.py:118)、[同:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/review_ledger.py:212) | 実装済み |
| D policy 全面 | [policy.py:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:62)、[同:340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:340)、[同:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:475)、[同:492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:492)、[同:521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:521) | 実装済み |
| E adapter | [.codex adapter:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/.codex/role-adapters/coder-v4-autonomous-k2.json:1) | 実装済み |
| F source parity set | [check_codex_agents.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/tools/check_codex_agents.py:52) | 実装済み |
| G architecture | [agent-architecture.md:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/docs/agent-architecture.md:105) | 実装済み |
| H tests | [test_codex_agents.py:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/test_codex_agents.py:123)、[同:913](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/test_codex_agents.py:913)、[同:968](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/test_codex_agents.py:968)、[同:1332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/test_codex_agents.py:1332) | 実装済み |
| I README 件数 | [.codex/agents/README.md:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/.codex/agents/README.md:1)、[同:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/.codex/agents/README.md:88) | 実装済み |
| 追加走査 | exact role 名は上記 A〜I の 9 file だけ | 追加 role-key pin の取り残しなし |
| duration ledger | [acceptance_duration_ledger.json:5605](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/acceptance_duration_ledger.json:5605) | real・scope 外 |

README の「当時の 13 件」は D56 の歴史的件数として明示されているため変更不要です。`review_ledger.py` と削除テストの「1 role 削除後 13 件」も 14→13 の意図した負例です。`t080_freeze_migration.py` の exact 13 や歴史文書中の件数は別集合であり、本 role closure とは無関係です。

## 総括

production の K2 role・policy・参照整合性・adapter 閉包には実在欠陥を確認しませんでした。追加テストも stub ではなく実 helper／実 semantic validator／実 backoff grammar を通ります。K2 以外の受理集合と既存 13 adapter bytes も不変です。

ただし、**M2 の単一理由性は不成立**です。M2 は期待 1 node ではなく 3 node を、文法/value と参照整合性の二理由で赤にします。KILLED 証拠を採る前に、文法 rejection だけへ再照準する必要があります。

別件として duration ledger に旧名 2 件・未収載 live node 4 件がありますが、これは検出力や合否ではなく scheduling hint の問題です。実測無しには直さず、scope 外の裁定パッケージへ送るべきです。

pytest、checker、renderer は実走しておらず、緑は主張しません。実施したのは静的読解、repo 全文検索、commit 差分確認、既存 13 source/adapter の差分 0 確認、ファイル hash/size の読取だけです。