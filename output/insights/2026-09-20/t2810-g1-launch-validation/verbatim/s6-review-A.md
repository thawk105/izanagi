## 所見 (RA-1, RA-2, …)

以下、`F` = `orchestrator/campaign/s8b_ratified_freeze.py`、`T` = `orchestrator/tests/test_s8b_ratified_verify.py`、`O` = `orchestrator/tests/test_s8b_oracle_driver.py`。行番号は統合 commit `dc5b0f39b`。**裁定外に受理集合や fail-closed 挙動を変える must-fix は確認しませんでした。**

**RA-1 — M12 は独立した拒否能力ではなく、拒否段階の契約を検出する。**

- 対象: `T:3102`、`T:3145`、`F:3123`、`F:3628`。
- 問題: 世代文書導入検査を削除しても、wrong_g=A は段階 7 の `scan-exemption-invalid / active-chain-mismatch` で拒否されます。新 test と既存 test は赤になりますが、受理への転化による kill ではありません。裁定 §3 末尾の F820 条件には、そのままでは適合しません。
- **放置時の帰結: production の受理集合・成果物の値は変わりませんが、変異 matrix が「独立した防壁を検証した件数」として過大に参照されます。**
- 分類: **should**。
- 推奨: M12 は独立拒否能力の集計から外し、reason/cause と拒否段階の契約試験として別記してください。test 自体は維持が妥当です。最初に失敗する assertion は cause より前の reason 比較です。

**RA-2 — binding の保証境界は comment にあり、指定された docstring にはない。**

- 対象: `F:2063`、`F:2236`。
- 問題: 「PBS job の外部認証ではない」は正しく記載されていますが、裁定 §2-1 項 6 が指定する docstring ではなく処理中の comment です。
- **放置時の帰結: 受理集合・成果物の値・実行時参照は不変で、docstring 経由では保証境界を参照できません。**
- 分類: **nit**。
- 推奨: `_validate_journal` の docstring にも同じ限定を記載してください。

## 受理集合の照合

裁定 §2-1 項 6 と実装の照合です。他の既存 gate を満たすことを前提とします。

| 裁定の形 | 実装 | 判定 |
|---|---|---|
| reservation 無し、campaign binding 無し | 両 claim が False | 従来どおり受理 |
| campaign binding 無し、binding 無し reservation 1 件が campaign 前 | 型・件数・順序を満たす | 指定どおり新規受理 |
| campaign binding 付き、同値 binding 付き reservation 1 件が campaign 前 | 両 claim True、両値一致 | 指定どおり新規受理 |
| campaign のみ claim、reservation 無しを含む | `journal-binding-claim` | 拒否 |
| reservation のみ claim | `journal-binding-claim` | 拒否 |
| binding 値不一致 | `journal-binding-mismatch` | 拒否 |
| binding key 片欠け | 交差集合が非空なので両 key を要求し、`schema-keys` | 拒否 |
| binding 型不正 | 厳密な str 型かつ非空を要求 | 拒否 |
| reservation 型不正 | formula は非空 str、共有 prebuild は厳密な bool、7 数値は厳密な正 int | 拒否 |
| reservation 2 件以上 | `reservation-preflight-count` | 拒否 |
| campaign 後の reservation | `reservation-preflight-order` | 拒否 |

`F:2088` の拡張は指定された 2 event だけです。他 event の binding key は expected に加わらず、未知 key として拒否されます。数値の bool・0・負数も拒否されます。

構造検査は全 record の exact 検査と campaign 一意性確定後にあります。全 allowlist が `event` を要求するため、`F:2224` の `r["event"]` 参照は安全です。既存の launch-start 先頭条件も残り、reservation が launch-start より前へ移ることはありません。

既存 event の key 集合は AST 比較ですべて不変でした。campaign record は binding を落とさず保持され、`F:2620` の wall_ledger 再導出も record 全体を `_plain_json` に通します。

裁定 §2-2 項 5 との照合です。

| 裁定の形・保証 | 実装 | 判定 |
|---|---|---|
| 従来 fixture の i=G | 一意・非 merge・C≤G を満たす | 維持 |
| 現物形 i=C=G^ | ancestor 判定が同一 commit を許す | 新規受理 |
| C と G の中間で導入 | C≤i≤G | 新規受理 |
| C 後に分岐して導入し、G 前に合流 | 導入 i 自身が非 merge なら可 | 新規受理 |
| C が i の祖先でない | `artifact-introduction-before-cert` | 拒否 |
| merge commit で初導入 | 捕捉済み `graph.parents` により検査 | 拒否 |
| 同 bytes の複数導入 | `_unique_introduction` | 拒否 |
| 到達履歴に別 bytes が存在 | `_immutable_introductions` | 拒否を維持 |
| i が G の祖先でない | `artifact-introduction-outside-generation` | 拒否。上限は重複検査 |
| cert の一意・非 merge・C<G | 既存 block 不変 | 維持 |
| G/H/worktree の bytes・mode、hash・semantic・binding・scan | 既存検査不変 | 維持 |
| 世代文書の導入集合 {G} | `F:3625` で独立に導出・比較 | 指定どおり |
| 段階 7 の active chain と G の一致 | `F:3123` | 維持 |

`_CommitGraph` は `F:452` に実在します。helper は捕捉済み graph、そこから得る導入 OID、呼出し元の C/G を使い、HEAD を再解決しません。`_git_ok` が False なら拒否し、起動失敗も例外となるため受理側には倒れません。

世代文書検査は H の履歴から導入集合を求め、段階 7 の resolver の結果を使いません。循環はありません。ただし拒否能力には RA-1 の重複があります。

`F:3244` の新 docstring は裁定 §2-2 項 4 と一致し、旧 `C<i` の説明は削除されています。

## fixture と実物の 1 文字照合

AST で文字列を抽出し、指定 probe の集合と比較しました。

| 対象 | probe | production allowlist + binding | fixture + binding |
|---|---:|---:|---:|
| reservation-preflight | 12 key | 完全一致 | 完全一致 |
| campaign-start | 17 key | 完全一致 | 完全一致 |

reservation の base 10 key は次のとおりです。綴りの差はありません。

```text
event, required_s, safety_margin_s, formula, build_cap_per_cell_s,
shared_dependency_prebuild, dependency_configure_cap_s,
dependency_target_cap_s, verify_cap_per_attempt_s, finalize_reserve_s
```

追加 2 key は `pbs_jobid` と `submission_nonce` です。campaign の既存 15 key も不変でした。

producer (`s8b_floor_campaign.py:6548`、`:7620`) と fixture (`T:565`、`:2834`) の差は以下です。実 journal の先頭 4 record も読み取りで照合しました。

| 項目 | 実物・producer | fixture |
|---|---|---|
| reservation 数値型 | 7 field とも int | 同じ |
| reservation 数値 | required=30000、margin=600、各 build/dependency cap=900、verify=120、finalize=600 | required=100、他は10 |
| formula | production の計算式文字列 | `"fixture-reservation"` |
| shared_dependency_prebuild | 現物 True、producer は cells から算出 | False。型は同じ bool |
| binding | job/nonce の非空 str | fixture 用の非空 str |
| campaign の job_id | 現物は str | None。既存の許容形 |
| その他 campaign 値 | 実 host/process/receipt/hash | fixture 用値。key 集合は一致 |
| event 順序 | launch-start → reservation → perf-preflight → campaign-start | launch-start → reservation → campaign-start |
| launch-start との位置関係 | reservation は直後 | 同じ |
| wall_ledger | campaign 全体を転記 | binding を含めて同期 |

したがって一致するのは key 文法と今回追加する型契約です。値や journal 全体の bytes が同じという証拠ではありません。perf-preflight を含む現物経路は、提示された無変異 historical reverify の段階 8 到達が別に裏付けます。

fixture の検証機構についても問題は見つかりませんでした。

- `T:2882` の負例 helper は、同じ構築・hash 確定経路の無変異対照を先に public launch に通します。campaign mirror も同期するため、対象検査の削除を後続 wall_ledger 検査が覆い隠しません。
- `T:3023` の DAG 再構築は G/A/X/H の tree OID を再利用します。worktree bytes を書き換えず、index を H に戻して両 diff を確認し、さらに `_capture_g_h_worktree` を実行しています。endpoint 検査の迂回ではありません。
- `_need_v1()` がなくても `T:496` が実 v1 を直接読みます。不在なら失敗し、skip や代替 fixture で緑にはなりません。違いは診断文です。
- 独立 fixture は一時 repo を使い、validator を置換しません。既存の独立 fixture test (`T:2822`、`:3134`) と同様、sealed decorator 不在は妥当です。ただし loader 全体の成功証拠にはなりません。

`O:135` の refusal 定数は、AST から復元した文字列を UTF-8 bytes で比較しました。**第 1 要素は base と不変、第 2 要素は `p3-after-g1.json` と完全一致し、実測の 2 件全体も一致**しています。定数は frozenset なので、「第 1・第 2」はソース上の記載順を指します。

## 変異の帰属

共通 node prefix は `orchestrator/tests/test_s8b_ratified_verify.py::` です。以下は静的な予測であり、本レビューで変異実走はしていません。

| ID | killer node | 帰属・制限 |
|---|---|---|
| M0 | なし | comment 追加は等価。SURVIVED が期待値 |
| M1 | `test_t2810_launch_positive[unbound]`、`[bound]` (`T:2852`) | 正常 reservation が `journal-event` で拒否される |
| M2 | `test_t2810_launch_positive[bound]` | 正常 binding が `schema-keys` で拒否される |
| M3 | `test_t2810_binding_one_sided_claim[campaign-start]`、`[reservation-preflight]` (`T:2920`)、`test_t2810_binding_campaign_without_reservation` | 各 record の key/type は合法。claim 検査削除後は通過し、期待例外がなくなる |
| M4 | `test_t2810_binding_invalid_type[empty-pbs_jobid-both]` 等、event=`both` の 4 ケース (`T:2947`) | 両側が同じ不正値なので値一致検査では拒否されず、独立に検出 |
| M5 | `test_t2810_binding_value_mismatch[pbs_jobid]`、`[submission_nonce]` (`T:2960`) | 非空 str を保ち、不一致だけを作る |
| M6 | `test_t2810_reservation_invalid_integer[...]` (`T:2972`)、`test_t2810_reservation_invalid_other_type[...]` (`T:2981`) | binding 無し、合法 key 集合。型検査削除後は通過する |
| M7 | `test_t2810_reservation_duplicate[unbound]`、`[bound]` (`T:2988`) | 同じ record を campaign 前に複製。型・順序・値一致は満たす |
| M8 | `test_t2810_reservation_after_campaign[unbound]`、`[bound]` (`T:2995`) | campaign の直後へ移す。launch-start 先頭と他の順序は維持 |
| M9 | `test_t2810_artifact_lineage_rejected[before-cert]` (`T:3082`) | closure の同 bytes を base に導入。cert 条件と endpoint を保ち、下限だけ違反 |
| M10 | `test_t2810_artifact_lineage_rejected[merge]` | 両親に path がない merge で初導入。区間・一意性は満たす |
| M11 | `test_t2810_artifact_lineage_rejected[multiple]` | 同 bytes の導入・削除・再導入。どちらの導入点も区間内で非 merge。先頭要素だけなら通る |
| M12 | `test_t2810_generation_introduction_independent` (`T:3102`)、既存 `test_floor_source_introduction_must_be_exact_generation_commit` (`T:3145`) | **F820 注意。** 段階 7 の別 reason/cause に移り assertion が赤になる。独立した拒否能力の証拠ではない |
| M13 | `test_t2810_artifact_upper_bound_helper` (`T:3113`) | 同じ graph・bytes・下限で上限だけを交換。**helper 単体限定**で、docstring に重複検査と明記済み |
| M14 | `test_t2810_launch_positive[certificate]`、`[bound]`、`[unbound]` | P-b/P-c/P-d の i=C が旧 `{G}` 条件で拒否される。P-b は journal 拡張に依存しない |

M4 の単独 event ケースは、型検査を削除しても値不一致検査が拒否します。これらは cause 契約の検出には使えますが、F820 の独立 killer には数えず、`both` を使う必要があります。

M13 を public 経路に載せると、G-tree 実在検査が先に拒否します。単体へ分離した現在の構成は裁定どおりです。

また、負例 helper の対照自体が M1/M2/M14 で失敗し得るため、「赤になった全 node」を各変異の独立 killer として集計してはいけません。上表は対象 gate に帰属できる代表 node を選んでいます。

## 判定

**GO — 静的な設計・実装レビューとして。**

受理集合は裁定どおりで、信頼の根の循環や裁定外の緩和は確認しませんでした。条件は、正式 matrix で M4 の独立 killer を `both` に限定し、M12 を拒否段階の契約試験、M13 を重複検査の単体試験として区別することです。

pytest・正式変異 matrix・既存回帰の完了は本レビューでは確認していません。提示証拠が示すのは loader 成功、historical reverify の段階 8 到達、live の policy 拒否、P3 拒否 2 件の一致です。

## 総括

**must-fix なし、should 1 件、nit 1 件。** key 集合と refusal 文字列は完全一致しました。主な注意点は M12 の証拠の扱いです。実装の互換性修復は支持できますが、live launch 成功や W-4/W-5 の開始許可を示すものではありません。