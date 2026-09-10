## 総括

- must-fix は1件。既存テストが静的に失敗するため、現状の land は止めるべき。
- 生成2経路と schema 検証への束縛は正しく配線され、入口の欠落は見当たらない。
- 現在の authority は `CANDIDATES` だけから導出され、comparator literal の再掲もない。
- `STOCK_NAME` の除外、read-heavy 流用、remeasure、`stock_common` に承認外の過剰拒否はない。
- MUT-1 と MUT-3 の期待 node 完全集合は実装後のテスト構成と一致していない。
- pytest は実走していない。親が提示した焦点 node の PASS は否定しない。

## R1

判定: **refuted。ただし drift 検知には nit あり。**

`_build_sort_name_comparator_index` は引数だけを走査し、実 index は `s6_sort_sweep.CANDIDATES` だけから構築される。comparator literal の再掲はない (`orchestrator/campaign/sort_comparator_authority.py:25`, `:54`; `orchestrator/campaign/s6_sort_sweep.py:143`)。name と implementation の重複も import 時に拒否する (`sort_comparator_authority.py:43`, `:45`)。

単純な候補追加は固定件数 assertion が赤にする (`orchestrator/tests/test_sort_comparator_authority.py:16`)。一方、同数の候補置換や comparator 置換は同じ `CANDIDATES` を入力と期待値に使うため、このテスト単体では検知しない。これは現在の閉包違反ではないが、将来の受理集合 drift に対する独立 witness にはなっていない。

`STOCK_NAME` は executable comparator ではなく説明用 `STOCK_IMPL_NOTE` しか持たず (`s6_sort_sweep.py:161`, `:164`)、main 選定でも full-order 集合から除外される (`s1_known_axes_freeze.py:524`)。`stock_common` も flags 専用である (`s1_known_axes_freeze.py:657`)。authority に入れない判断は正しい。

## R2

判定: **refuted。3箇所すべて発火する。**

- read-heavy: write-heavy provenance から取得した直後に検査 (`s1_known_axes_freeze.py:501`, `:506`)。
- main: 選定 name の provenance comparator を取得した直後に検査 (`s1_known_axes_freeze.py:533`, `:539`)。
- schema: workload ごとの `sort_best` に検査 (`s1_known_axes_freeze.py:842`, `:846`)。

`build_document` の全 workload は `_sort_entry` を通る (`s1_known_axes_freeze.py:738`, `:745`)。trigger 側の生成検査 (`:605`, `:612`) と schema 検査 (`:831`, `:836`) に対応しており、生成・検証の入口欠落はない。

## R3

判定: **refuted。両拒否分岐とも恒真ではない。**

型分岐は exact `type(...) is str` を要求する (`sort_comparator_authority.py:62`)。`_sort_entry` の前段は `isinstance(..., str)` なので (`s1_known_axes_freeze.py:504`, `:537`)、`str` subclass は前段を通って authority の型分岐で拒否される。したがって生成経路でも意味がある。`_validate_schema` には前段の型検査自体がなく、より直接的に意味を持つ (`s1_known_axes_freeze.py:842`)。

index 不一致分岐 (`sort_comparator_authority.py:64`) は、未知 name、正準 comparator の取り違え、外側 whitespace を含む comparator を拒否する。型分岐を失うと、正準文字列との hash・等価比較を装う非文字列 object という性質の反例が残るため、型分岐は index 分岐にも包含されない。

## R4

判定: **real。MUT-1 と MUT-3 の完全集合が不正確。**

MUT-1 の正しい集合は、射影された新テスト内だけでも次の6 node。裁定記載の2 node (`s4-adjudication.md:103`) は不足している。

- `test_binding_rejects_outer_whitespace` (`test_sort_comparator_authority.py:38`)
- `test_binding_rejects_canonical_name_comparator_mismatch` (`:44`)
- `test_validate_schema_rejects_sort_comparator_outside_authority` (`test_s1_known_axes_freeze.py:162`)
- `test_validate_schema_rejects_sort_name_comparator_mismatch` (`:172`)
- `test_sort_entry_rejects_comparator_outside_authority_before_output` (`:183`)
- `test_sort_entry_rejects_name_comparator_mismatch_before_output` (`:198`)

MUT-2 は登録どおり2 nodeで閉じる (`test_sort_comparator_authority.py:22`, `:30`)。各 synthetic tuple は対象外の重複を作らないため、単一理由性も満たす。

MUT-3 は登録された2 node (`s4-adjudication.md:105`) 以外にも、少なくとも次が無条件に赤くなる。

- `test_current_six_frozen_trigger_predicates_pass_semantic_membership` (`test_s1_known_axes_freeze.py:134`)
- `test_validate_schema_accepts_both_mask31_names` (`:233`)
- schema が balanced sort を先に通るため、workload loop 後半で期待した trigger エラーへ到達できない3 node (`:459`, `:471`, `:483`)

submodule 初期化環境では `build_document` を前処理に使う node (`:118`, `:650`, `:665`, `:673`, `:689`, `:705`, `:715`, `:725`, `:742`) も先に sort 拒否で赤くなる。したがって global な単一理由性と完全集合は成立していない。

## R5

判定: **refuted。承認外の過剰拒否は見当たらない。**

read-heavy は固定された `sk_ad` と write-heavy provenance の comparator を同じ pair として検査するため、正規の流用経路は通る (`s1_known_axes_freeze.py:495`, `:501`, `:506`)。

`remeasure_reference` は main comparator の検査後に、参考用の `argmax_name` と fitness だけを構築する (`s1_known_axes_freeze.py:542`, `:556`; `_remeasure_reference` は `:484`)。nested reference に comparator がなく、新検査による過剰拒否はない。

`stock_common` は sort authority の対象外 (`s1_known_axes_freeze.py:657`, `:746`)。`stock` を `sort_best` とする入力は既存 selection rule の full-order 制約外なので、拒否は承認外ではない (`:524`)。

## R6

判定: **real。既存テスト回帰1件と、型防壁の未固定がある。**

`test_verify_rejects_one_byte_freeze_tamper` は `sp_dd` を `xp_dd` に変え (`test_s1_known_axes_freeze.py:680`)、後段の機械再構成不一致を完全一致で期待する (`:684`, `:686`)。しかし現在は `verify_document` が最初に `_validate_schema` を呼び (`s1_known_axes_freeze.py:860`)、新しい authority 検査 (`:846`) が先に `sort_best.name/comparator が権威集合と不一致` を投げる。したがってこの既存 node は、実走せずとも静的に期待値不一致となる。

新しい負例は対象以外を現行値で満たし、生成テストの stub も拒否位置を隔離する目的なので、負例の単一理由性自体は妥当 (`test_s1_known_axes_freeze.py:64`, `:162`, `:183`)。

ただし正例は authority と同じ live `CANDIDATES` を入力に使う (`test_sort_comparator_authority.py:16`)。また型拒否分岐を直接固定する非文字列・`str` subclass・比較偽装の sort テストは存在しない。現行コードは正しいが、この防壁の退行検知は弱い。

## R7

判定: **判定不能。ただし確認できた範囲の食い違いは refuted。**

変更ファイル4件と内容は報告どおり (`s5-author.md:8`〜`:23`)。worktree status にもその4件以外の変更はない。pytest 未実走との報告 (`s5-author.md:25`〜`:37`) も、親の後続実測と矛盾するものではない。

所有外 caller・consumer/meta test の完全性 (`s5-author.md:39`〜`:66`) は、単独段の射影にそれらの実体が含まれないため独立確認不能。

「自走 harness を実装した」 (`s5-author.md:5`) はやや過大な表現で、差分は既存 harness に自動収集される test 関数の追加である。

## must-fix

- `orchestrator/tests/test_s1_known_axes_freeze.py:673`: one-byte tamper の検証レポートが「機械再構成不一致」から「authority 不一致」へ変わり、既存 node とエラー分類を壊すため land を止める。

## nit

- `test_sort_comparator_authority.py:16` は live source と authority を相互比較しており、同数の候補置換を独立に検知しない。
- sort authority の exact-type 分岐 (`sort_comparator_authority.py:62`) に直接の退行テストがない。
- MUT-1/MUT-3 の期待 node 完全集合を実装後のテスト構成へ更新する必要がある。
- `s5-author.md:5` の harness 実装という表現は、既存 harness への自動収集対応と書く方が正確。