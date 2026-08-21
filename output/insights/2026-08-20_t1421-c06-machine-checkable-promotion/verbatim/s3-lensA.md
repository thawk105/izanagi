## 総括

blocker はありません。D529 の4点変更、hash、CLI、generation chain は整合しています。一方、C06 evaluator の到達性検査には実際の弱点があり、これは段4で裁定すべき scope-out 所見です。

### major

- [real] `orchestrator/campaign/s8c_preregistration_evidence.py:3510-3528`  
  C06 は supervisor 不在時に検査を省略し、`_reachable_calls` は呼出し名の集合だけで順序・戻り値のデータフローを検査しません (`:409-426`)。`sha256` も supervisor 全体に存在すれば通ります。  
  再現手順: `supervisor is None` の分岐、または `reserve_all_cells` を bench launch 後へ移す／`settle` の戻り値を停止処理へ渡さない mutation を読む。  
  影響: named negative control (`:3423`, test `:3637-3640`) は検出しますが、一般の一腕削除や順序破壊を証明しません。現状は `SATISFIABLE_CONDITION_IDS` が空 (`:3070`) なので D529 の受理を直ちに誤らせませんが、弱点を段4へ明示的に送る必要があります。

- [refuted] map 移動による consumer 破壊  
  `orchestrator/campaign/s8c_preregistration_evidence.py:3056-3069` は `_evaluate_c06` (`:3477`) より前なので、単純追加は import 時 `NameError` になります。段2の「map と derived set を C06 定義後へ移動」は正しいです。  
  `_evaluate_undefined` (`:3079`) と registry dispatch (`:3160`) は実行時参照で、`_REGISTRY` (`:3221`) も評価を実行しません。全 `.py` 検索でも外部 import consumer はなく、主な参照は同 module と predicate test だけです。

- [refuted] contract hash  
  `test_s8c_preregistration_core.py:801-830,1195-1198` の assert 対応は過不足ありません。C06 flag を true にした canonical hash は次の通りで、段2値と一致しました。

  - current: `dafd8d61807360c333288a00730e7c9ae13a086b61c770e7faf47fb5dd1f701a`
  - NUL: `be5cfef1199864717098bd90fa8ad98ca65ebb83cd9f66d10045c3e1d0e8e410`
  - CR: `42a3ca1d8b072fcd84aba3ef51ed1ed1981c12246e477103a84fded4e35f70ee`
  - LF: `063ed271b875777d86811b221189360bfc66baf5753b961a64e348f8e025c126`

  v5 の固定 assert は `:2404,2454,2477` の3箇所で、v6 へ更新が必要です。g1 の歴史的 hash (`:1201-1209`) は変更不要です。

- [refuted] `prepare-revision` CLI  
  `s8c_preregistration.py:2169-2181,2200-2205` と `:2035-2087` を照合した結果、提示コマンドの引数名は正確です。`--revision-reason` は argparse 上必須、`--ruling-reference` は構文上任意ですが、既存 generation があるため実行時には必須です。  
  実行順も正しく、変更を未 commit のまま `--commit HEAD` (g9) を指定して実行します。`prepare_revision` は先に HEAD の freeze chain を検証し、その後 worktree の contract を読みます。変更を先に commit すると履歴検査で詰まります。

- [refuted] `supersedes_sha256`  
  `s8c_preregistration.py:2071-2077` は現行 tip record の raw bytes を hash し、履歴検査も `:1659-1660` で親 record の `raw_sha256` と比較します。g9 raw file の `sha256sum` は段2記載の `ef24bdd64fd9fb50ac3652f3c766a2aa99e81f3b18bebd546dd33029f5ac90dd` と一致しました。g9 record 内の自身の `supersedes_sha256` を使う、という意味ではありません。

- [refuted] D529 の受理条件不足  
  D529 (`docs/decisions.md:21856-21873`) が要求する contract flag、registry、DECIDER_VERSION、次世代 record は段2 plan に揃っています。C06 は現在も `SATISFIED` を返さず、named negative control も mutation を `UNSATISFIED` に落とします。従って、reachability の弱点を段4で scope-out と裁定する前提なら、4点変更だけで D529 の機械的受理条件を欠く依存関係は見つかりません。

### minor

- [real] stale な staged 表現  
  `s8c_preregistration_evidence.py:3235-3236,3477-3478` は「contract false」「staged evaluator」と記述していますが、昇格後は production registry です。predicate test でも `test_current_contract_keeps_c06_staged_only` (`:3670-3675`) など名称・コメントが逆になります。実行結果は壊しませんが、将来の判断を誤らせます。

- [unclear] staged negative-control helper の移行方法が曖昧  
  `test_s8c_preregistration_predicates.py:3611-3713` の `_STAGED_EVALUATORS[6]` 参照は除去対象ですが、`STAGED_NEGATIVE_CONTROL_CASES` と wrapper (`:3652-3667`) をどう main `NEGATIVE_CONTROL_CASES` (`:1191-1201`) へ統合するかが plan で明示されていません。wrapper を削除するなら `_negative_control_case` 本体へ C06 分岐を移さないと `AssertionError` になります。

- [refuted] C03/C08 の現行影響  
  `s8c_preregistration_evidence.py:3073-3079,3162-3166` と predicate tests `:3084-3112` は C03/C08 を明示的に別扱いしています。今回の map 移動や C06 登録は影響しません。将来追加する場合だけ、全 evaluator 定義より後に map を置く規則と、contract・exact set・version・freeze record の更新が必要です。

- [refuted] predicate/invariant の見落とし  
  predicate の全 C06 consumer/assert (`:233,1191-1201,2680-2697,2723-2754,3441-3443,3605-3792`) を照合しました。invariant の C06 追加も、静的照合で checks 4件、exclusions 5件、missing 0件となり、段2 plan と一致しました。

## プランへの推奨修正

- C06 の staged helper・constant・test 名・source comment を production 状態へ明示的に移行する。
- `prepare-revision` は contract/core の変更を commit する前に実行し、生成した g10 record を同じ commit に含める。
- reachability の弱点は本 wave で勝手に修正せず、段4で scope-out と後続 wave 化を裁定する。
- pytest は read-only 段のため実行していません。