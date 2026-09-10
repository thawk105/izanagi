## M1〜M13 を殺すテストの対応表

pytest は実走していない。以下は静的に追跡した結果である。

| ID | 殺すテストと赤になる箇所 | 判定 |
|---|---|---|
| M1 | `test_group_unsuffixed_expected_node_matches_suffixed_failure`。恒等 `_match_key` では `MH.main` が 1 となり、[test_mutation_harness.py:898](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:898) の `== 0` が赤。比較座は [mutation_harness.py:2019](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:2019)。 | 殺す |
| M2 | `test_group_suffixed_expected_node_is_collected_and_killed`。[test_mutation_harness.py:876](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:876) の実 harness 呼出しが、raw collection への変異では未捕捉 `HarnessError` で赤。座は [mutation_harness.py:1477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:1477)。 | 殺す |
| M3 | `test_match_key_preserves_real_parametrize_ids_containing_at`。[test_mutation_harness.py:1076](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:1076) の literal 同値 assert が赤。 | harness 座を殺す。fanout 座は後述 |
| M4 | `test_match_key_removes_only_group_after_nested_real_parametrize_id`。[test_mutation_harness.py:1088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:1088) が、内側の `@` を拾って group を除去できず赤。 | harness 座を殺す。fanout 座は後述 |
| M5 | `test_group_suffix_normalization_keeps_strict_superset_as_mismatch` の [test_mutation_harness.py:983](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:983)。`expected_keys <= failed_keys` 型の包含化で `KILLED` になり赤。既存の raw superset assert [test_mutation_harness.py:967](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:967) も同じ変異を殺す。逆向き `failed_keys <= expected_keys` は既存 subset assert [test_mutation_harness.py:999](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:999) が殺す。 | 殺すが過剰決定 |
| M6 | 新設 [test_mutation_harness.py:1146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:1146) が `SURVIVED != PARSE_ERROR` で赤。既存 [test_mutation_harness.py:1133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:1133) も同じ gate を殺す。 | 殺すが重複 |
| M7 | `test_group_suffixed_expected_node_is_collected_and_killed`。`_normalize_node` 側で除去すると raw 台帳値が base へ変わり、[test_mutation_harness.py:881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:881) の `failed_nodes` assert が最初に赤。 | 殺す |
| M8 | `test_group_suffixed_expected_node_resume_reuses_valid_ledger`。初回は通るが、resume 呼出し [test_mutation_harness.py:918](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:918) が未捕捉 `HarnessError` で赤。座は [mutation_harness.py:2387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:2387)。 | 殺す |
| M9 | `test_match_key_does_not_collapse_at_in_realistic_paths`。nodeid 全体へ除去を当てると、最初の literal assert [test_mutation_harness.py:1099](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:1099) が赤。 | harness 座を殺す。fanout 座は後述 |
| M10 | `test_merge_matches_group_suffixed_failure_and_preserves_raw_nodes`。raw 比較では ledger の `KILLED` と再導出した `MISMATCH` が食い違い、[test_mutation_fanout_contract.py:617](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_fanout_contract.py:617) の `_merge` 中に赤。照合は [mutation_fanout_contract.py:358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_fanout_contract.py:358)。 | 殺す |
| M11 | `test_split_rejects_group_suffix_alias_as_expected_node_duplicate`。raw 重複検査だけでは `derive_split` が正常終了し、[test_mutation_fanout_contract.py:557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_fanout_contract.py:557) の `pytest.raises` が DID NOT RAISE で赤。 | 殺す、単一理由 |
| M12 | `test_merge_keeps_group_normalized_strict_superset_as_mismatch`。[test_mutation_fanout_contract.py:686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_fanout_contract.py:686) の `_merge` 中、包含化した再導出 `KILLED` と記録 `MISMATCH` が食い違って赤。 | 殺す、単一理由 |
| M13 | `test_merge_accepts_group_suffixed_expected_against_base_collection`。raw collection 比較では [test_mutation_fanout_contract.py:651](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_fanout_contract.py:651) の `_merge` が、[mutation_fanout_contract.py:932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_fanout_contract.py:932) で拒否され赤。 | 殺す、単一理由 |

指定された主座について殺すテストが完全に無い M はない。ただし M3・M4・M9 は harness の `_match_key` だけを攻撃しており、同じ実装を複製した fanout 側には敵対入力がない。

## 検査項目 2〜10 の結果

1. 単一理由性

   M1、M2、M8、M10、M11、M12、M13 は、それぞれ比較、fresh collection、resume collection、fanout status、fanout duplicate、fanout strict equality、fanout collection の別座へ届いている。

   M5 は新設 group-superset と既存 raw-superset の双方が同じ包含変異を殺すため過剰決定である。M6も既存・新設の両方が同じ `rc != 0 and not failed` gate を殺す。M7を test file 全体で走らせると raw 台帳 assert だけでなく parametrize literal の保存 assert も赤になり得るため、帰属には [test_mutation_harness.py:881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:881) を使う必要がある。

2. 恒真化

   production helper で期待値を再 parse する round-trip は見つからなかった。harness 正例は literal spec から実際の `MH.main` を通る。fanout fixture は status と stdout を組み立てるが、実 verifier が [mutation_fanout_contract.py:1000](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_fanout_contract.py:1000) で stdout から status と failed node を再導出するため、両側 stub ではない。

   `MH._match_key(node, repo) == node` の保存性テスト単体は恒等 stub でも通るが、接尾辞除去 assert [test_mutation_harness.py:1088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:1088) と実 harness 正例が対になっているため、suite 全体として恒真ではない。

3. 負例の実体性

   `arxiv` node は ledger 実在 literal と一致する。[acceptance_duration_ledger.json:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/acceptance_duration_ledger.json:143) と [test_mutation_harness.py:1055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:1055)。

   `[@]`、`[試験::場合@直列]`、`[試験::場合[値@例]]` は実 parameter 値 [test_acceptance_schedule_order.py:486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_acceptance_schedule_order.py:486) と ledger [acceptance_duration_ledger.json:2037](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/acceptance_duration_ledger.json:2037) に一致する。M4はその実在 nested literal に group suffix だけを付けた入力である。

   M9は裁定どおり `tests@left/...` と `tests@right/...` を literal で使用している [test_mutation_harness.py:1095](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:1095)。

4. 正例の比較器経路

   harness 正例は動的 fixture 内で本物の `xdist_group` markerを付け [test_mutation_harness.py:188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:188)、`-n 2 --dist loadgroup` [test_mutation_harness.py:362](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:362) を付けて `MH.main` を通す。内部比較器の直呼びによる正例ではない。

   fanout 正例は runner 自体を起動しない純 fixtureだが、終端 verifier の実体 `MF.merge_group` を通る [test_mutation_fanout_contract.py:450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_fanout_contract.py:450)。M10、M12、M13が対象とする merge 比較器は迂回していない。

5. 比較座の網羅

   harness の key 比較座は、登録時の正規化後重複 [mutation_harness.py:1112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:1112)、flaky hold [mutation_harness.py:1314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:1314)、fresh collection [mutation_harness.py:1477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:1477)、KILLED 完全一致 [mutation_harness.py:2019](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:2019)、resume collection [mutation_harness.py:2387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:2387)。

   fanout は spec の raw＋key 重複 [mutation_fanout_contract.py:498](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_fanout_contract.py:498)、KILLED 完全一致 [mutation_fanout_contract.py:358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_fanout_contract.py:358)、collection [mutation_fanout_contract.py:923](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_fanout_contract.py:923)。

   raw のまま残る抽出重複排除、artifact 再導出との順序込み一致、spec・registration・record 間の一致、cross-shard collection 一致は観測証拠・proof link の完全一致であり、`_match_key` 化すべき座ではない。`tools/mutation_fanout.py` 自体には `expected_nodes`、`failed_nodes`、`collected_nodes` の比較座は 0 件で、split/merge を contract に委譲する [mutation_fanout.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_fanout.py:35)。

6. 4方向

| 方向 | harness | fanout_contract |
|---|---|---|
| 期待なし × 記録あり | [test_mutation_harness.py:894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:894) | [test_mutation_fanout_contract.py:604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_fanout_contract.py:604) |
| 期待あり × 記録あり | [test_mutation_harness.py:868](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:868) | [test_mutation_fanout_contract.py:638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_fanout_contract.py:638) |
| 期待あり × collectionなし | fresh [test_mutation_harness.py:868](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:868)、resume [test_mutation_harness.py:908](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:908) | [test_mutation_fanout_contract.py:638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_fanout_contract.py:638) |
| 期待なし × collectionなし | 既存実 harness [test_mutation_harness.py:708](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:708) | 既存 merge fixture [test_mutation_fanout_contract.py:583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_fanout_contract.py:583) |

7. 既存 consumer への波及

   `test_mutation_worktree.py` は live harness source をコピーして実行する [test_mutation_worktree.py:645](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_worktree.py:645)、[test_mutation_worktree.py:1435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_worktree.py:1435)。既存 spec は接尾辞なしなので期待挙動は変わらないが、必須回帰対象である。

   `test_flaky_test_holds_contract.py` は接尾辞付き alias も held node として拒否するよう挙動が変わる [test_flaky_test_holds_contract.py:722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_flaky_test_holds_contract.py:722)。

   `test_mutation_fanout.py` は production driver 経由で `derive_split` と `merge_group` を参照する [mutation_fanout.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_fanout.py:35)。既存 fixtureは接尾辞なしで、意味変更はない。

   `test_pytest_failure_digest.py` は `_failed_nodes` のみを直接 consumer とする [test_pytest_failure_digest.py:978](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_pytest_failure_digest.py:978)。抽出器は未変更なので期待挙動は変わらない。

8. pytest対象

   親の既存一覧に加え、全 tracked Python を AST 走査する `test_p3_build_authority_cli.py` が必要。詳細は次節。

9. 揮発 payload

   追加された期待値に worktree hash、時刻、絶対 path の焼き込みは 0 件。`tmp_path` は fixture 配線だけで、asserted literal には入っていない。新規 test file もなく、変更は既存3 test fileだけである。

## 所見一覧 (BLOCKER / MAJOR / MINOR、file:line 付き)

- BLOCKER — fanout 側の `_match_key` に M3・M4・M9 の敵対入力が届かない。[mutation_fanout_contract.py:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_fanout_contract.py:297) は harness と独立した実装だが、実在 parametrize literal と `tests@left/right` は harness だけを呼ぶ [test_mutation_harness.py:1051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:1051)。fanout の追加入力 [test_mutation_fanout_contract.py:604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_fanout_contract.py:604) 以降は path 内 `@` も bracket 内 `@` も持たない。放置すると、fanout だけが parametrize ID を切る、または path 内 `@` を同一視して偽 `KILLED` を作る変異が、harness の M3・M4・M9 を全て赤にしながら通り抜ける。

- MINOR — M5、M6、M7の変異実測を test file 単位で数えると単一理由にならない。M5は [test_mutation_harness.py:957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:957) と [test_mutation_harness.py:970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:970)、M6は [test_mutation_harness.py:1123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:1123) と [test_mutation_harness.py:1136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:1136) が重複する。M7は literal 保存テストにも波及する。放置すると、どの assertion が新しい group 正規化機構を証明したかという `DW-M01` の帰属が曖昧なまま残る。

- MINOR — 親の pytest 一覧から repo-wide AST consumer が1 file漏れている。`test_tracked_python_coder_authority_ast_closure_is_exact` は全 tracked Python を列挙し [test_p3_build_authority_cli.py:637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_p3_build_authority_cli.py:637)、各 source を AST 走査する [test_p3_build_authority_cli.py:654](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_p3_build_authority_cli.py:654)。放置すると、変更した2 production fileを含む coder-authority closure が未実走のままになる。

## 親が走らせるべき pytest 対象

直接機能・consumer:

- `orchestrator/tests/test_mutation_harness.py`
- `orchestrator/tests/test_mutation_fanout_contract.py`
- `orchestrator/tests/test_flaky_test_holds_contract.py`
- `orchestrator/tests/test_mutation_fanout.py`
- `orchestrator/tests/test_mutation_worktree.py`
- `orchestrator/tests/test_pytest_failure_digest.py`

内容・AST・全 source 列挙 consumer:

- `orchestrator/tests/test_pegasus_dispatch_compute.py`
- `orchestrator/tests/test_campaign.py`
- `orchestrator/tests/test_login_headroom.py`
- `orchestrator/tests/test_t338_submission_gate_unit5.py`
- `orchestrator/tests/test_official_perf_closure.py`
- `orchestrator/tests/test_p3_build_authority_cli.py` — 実装子・親一覧から漏れていた追加対象

新規 test file はないため、file 集合列挙のメタテスト追加は不要。

## 探して 0 件だったもの

- `tools/mutation_fanout.py` 内の `expected_nodes`、`failed_nodes`、`collected_nodes` 比較座: 0 件。
- harness／fanout_contract の比較座で、観測 raw 保存・proof link 完全一致を除き、`_match_key` 化すべき raw 集合比較の残り: 0 件。
- group 名 literal 自体に `@` を含む `xdist_group(...)`: 0 件。
- 新規 test file: 0 件。
- 新規期待値への hash、時刻、絶対 path の焼き込み: 0 件。
- source consumer が absolute path を `expected_nodes` に組み立てる例: 0 件。
- pytest 実走: 0 件。5変更fileの `ast.parse` のみ静的に実施し、5/5成功。

## 総括

指定された M1〜M13 の主座には全て赤になる経路がある。しかし production に `_match_key` が2実装あるのに、M3・M4・M9の敵対 literal は harness 側しか通らない。fanout verifierで同型欠陥が再発しても現在の追加テストは緑になり得るため、BLOCKERと判定する。

それ以外では、4方向、raw証拠保存、完全一致、PARSE_ERROR、resume、flaky-hold の経路は静的に閉じている。親の実走対象には `test_p3_build_authority_cli.py` を追加する必要がある。