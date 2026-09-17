## 所見

1. **real — 単純な file union 削除は、実在する writer の跨ホスト排他を失わせる。**
   `test_repository_candidate_uses_real_s8c_budget_module` は group 無し・resource リスト外で、function fixture から実 `_ROOT` に対する `git add` / `write-tree` / `commit-tree` を実行する。分離されるのは index だけで、object store は実 repo のままである。既存 golden も「同 file の retained group に依存」と明記している。
   根拠: `orchestrator/tests/test_s8c_preregistration_predicates.py:4701,4736,4765`、`orchestrator/tests/test_real_repo_serialization.py:438`。lock は `/tmp` に置かれ、保証は同一 host に限定される（`conftest.py:1028,1169`）。plan の明示 affinity 補完は必要であり、補完前の simulation は安全な候補の評価になっていない。

2. **refuted — 「resource リスト外の module fixture consumer は、node 化で必ず排他を失う」は成立しない。**
   リスト外 consumer 自体は実在する。例えば module fixture `repository_candidate_commit` は parent write/read lock 下で実 repo を扱い、`test_candidate_freeze_matches_contract_and_generation_chain` が消費する。しかし、この consumer は `s8c-preregistration-candidate` group を持つため、group union と D1167 の衝突辺を保持すれば同一 shard に残る。
   根拠: `orchestrator/tests/test_s8c_preregistration_invariant.py:362,388`、`test_real_repo_serialization.py:428,1375`。**今回確認できた無保護化の具体例は function fixture であり、P4 の module fixture という説明は修正が必要。** import 時副作用による新たな退行例は今回確定していない。また全 shard が全 collection を行うため、file 閉包を import 時排他の保証とは扱えない。

3. **real — inventory golden は、実 repo アクセスの網羅的検出器ではない。**
   access map の検査は宣言済み inventory 内の分類一致（`conftest.py:612`）。fixture-owned 検査は golden に列挙した fixture の consumer 一致（`test_real_repo_serialization.py:1348`）。共有 fixture 閉包は、resource node と交差する module/session fixture を seed にした検査であり、seed の無い fixture、function fixture、import 副作用の全探索ではない（同 `:1432,1460`）。
   したがって P4 の必要条件は「`REAL_REPO_RESOURCE_NODES` 単独の完全性」ではなく、**resource node・fixture-owned consumer・その他の実アクセスを合わせた衝突閉包の保存**である。plan が挙げる writer 一件の補完だけで、全移動候補の安全性まで証明したことにはならない。

4. **real — D711 の file 閉包は、現状では排他の防壁も担っている。**
   `_components` は file を頂点にするため、group 無しの兄弟 node も group に接続される（`tools/acceptance_shards.py:325`）。これが所見1の writer を同じ host に留める。一方、file 閉包自体は同一 worker・実行順・module fixture の一回だけの構築を保証しない。
   案(a)では `assignment_closure_gate` の一律 `file_shards` 条件（同 `:477,484`）を、独立に定義した必要 affinity の検算で置き換える必要がある。集合一致・重複拒否・group 閉包・衝突辺閉包は保持する。
   `_validate_real_repo_shard_state` は割付そのものではなく、全 records に resource marker が保存されたことを検査する（`conftest.py:2122`）。**node 化だけを理由にこの条件を緩める必要はない。** 現行 marker を維持し、追加 affinity の欠落も独立した期待集合から検出する。新 affinity を runtime group と混同して writer を再直列化する必要もない。

5. **refuted — plan が割付器の出力だけで検出力維持を自己証明する、という攻撃は現記述には当たらない。**
   plan は `_components` の再利用を避ける直接検算、独立 golden、手書き split selections、affinity 付与削除の変異を要求している（`s2-plan.md:19,60,84`）。この方針は妥当。
   ただし既存 test の `allocate → closure_gate` 成功と component metadata 一致だけでは、必要 affinity の宣言漏れを検出できない（`test_real_repo_serialization.py:1749`）。実装時は所見1の consumer を独立 literal から要求する必要がある。**plan の独立検算方針を守れば循環は避けられるが、まだ実証済みではない。**

6. **real — 親 brief の D358 要約は、現行の直列化境界としては不正確。**
   D358 の逐語は単一 worker 維持だが、後続 D1618 は全 node の shard affinity を保った runtime 分割を承認している（`decisions-verbatim.md:67,195`）。現物も resource marker を records に保存した後、一部 runtime suffix を除去し、runtest protocol で read/write lock を取る（`conftest.py:2154,2264,2278`）。
   守るべき現行境界は、全 resource の shard affinity、retained runtime unit、既存 lock 意味論である。plan のこの区別（`s2-plan.md:61`）は正しい。

## 規律 2 の射程判定

**(c) 一部だけ射程内。**

- 所見1のような衝突 consumer の同居制約を失わせる変更は、規律2の防壁を外す。D711 の文言改訂だけでは足りない。
- 衝突閉包を独立に確認・保存したうえで、排他上不要な file 同居制約を外す部分は、D711 の裁定改訂対象となる。
- 現段階では、plan は保存方法と検査方針を示した段階であり、suite 全体について後者だけの変更になるとは未確認。

## 総括

**must-fix（実装する場合）**

- **file 由来の必要 affinity を保存すること。** 放置すると、現在拒否される「candidate writer と衝突 group の別 shard 配置」が受理され、跨ホスト排他を保証できなくなる。
- **期待 affinity を変更後 records・allocator 出力から独立に検査すること。** 放置すると、affinity 宣言漏れが allocator と gate の双方から消え、不正な分割を正常と判定しうる。

**nit**

- P4 は「module fixture」に限定せず、確認済みの function fixture writer と、複数区分を合わせた衝突閉包で記述する。
- D358 の要約には D1618 による現行境界を反映する。
- plan の既存資料不足に関する記述は親 addendum で更新する。ただし追加実測は排他保存の証拠にはならない。

**P4 の危険指摘は成立するが、説明と必要条件には修正が要る。静的検査のみで、書き込み・pytest 実行は行っていない。**