# 判定と範囲

**GO。must-fix は検出していません。材料の説明に should が1件あります。**

対象は `36fb14a3..6fa89b563` の3 commit と submodule C=`68106660686232781bca3be792a750d3e19d7a8a`。指定資料、Git object、差分、テスト本文、親の実測記録を読んだレビューです。**build・テスト・変異・benchmark・D297・provenance checker は未実走・静的読解**です。親・実装子の実走結果と、自分の確認を区別します。

以下では参照を短縮します。

- `D` = `orchestrator/campaign/s3_mocc_lock_coverage.py`
- `T` = `orchestrator/tests/test_mocc_xp_pin_candidate.py`
- `J` = `output/env/pegasus/calibration/s3_mocc_xp_pin_candidate.json`
- `JOB` = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2844-mocc-xp-hook-branch`
- `C:…` = C の Git object 内のファイル。現在の submodule checkout の行番号ではありません。

# 所見一覧

refuted の重大度は、その疑義が成立した場合の重大度です。

| ID | 判定・重大度 | 根拠と成果物への影響 |
|---|---|---|
| A-S1 | **real / should** | `JOB/s4-ruling.md:11` の「verdict が indeterminate」という一括表現は `J:14908` の lockskip_high=`non-serializable` と不一致。転載すると材料レポートが実測を誤記するが、現行の certified・14 check・受理集合は変わらない。 |
| A-R1 | refuted / must-fix相当 | `C:cc/mocc/transaction.cc:993`、候補 patch`:18`、`JOB/verify-candidate.log:11`。指定3箇所以外の意味変更、X/P の移動・弱化は不成立。候補内容を別物として受理する問題は見つからない。 |
| A-R2 | refuted / must-fix相当 | `D:609`、`D:640`、`D:668`。4条件の欠落・識別不成立のまま build する経路は不成立。依存物 build を含め、候補識別完了後に進む。 |
| A-R3 | refuted / must-fix相当 | `D:694`、`D:708`、`D:710`、`T:156`、`T:192`。checkout・patch・verifier root の取り違えは不成立。別 source の診断を C の証拠として受理する経路は見つからない。 |
| A-R4 | refuted / should相当 | `T:24`、`T:74`、`T:102`、`T:251`。固定期待値の JSON からの逆算、候補識別自体の stub 化は不成立。ただし consumer 単体を実走内容全体の独立再検証と呼ぶことはできない。 |
| A-R5 | refuted / must-fix相当 | `D:451`、`patches/README.md:591`。現行 README は `.text` bytes 一致を主張していない。補助証拠を完全除去の証明へ昇格させる記述は、この変更箇所にはない。 |
| A-R6 | refuted / must-fix相当 | `JOB/run-d297.log:7`、`:14`、`:21`、`:34`。GCC 2版 pass、clang 比較未完了、include 契約による負例拒否は一次資料と一致。checker の受理集合拡大もない。 |
| A-R7 | refuted / must-fix相当 | `JOB/mk-C-amend.log:7`、`:33`、`docs/ai-provenance.md:51`。最終 C の親・tree・trailer と証拠 OID の不整合は不成立。旧 C の実測を OID だけ差し替えた形ではない。 |

# C の内容と規律1・2

Git object 上で、C の親は BASE ちょうど1本、tree は `6dc0883c5bcc854eb6425101508b81a36bd7bf45`。BASE→C の raw diff は `cc/mocc/transaction.cc` の `100644→100644 / M` 1件、新 blob は `e393efbfd5fad7bbe05117b43669ccc0f44abb6a` です。

旧 patch と候補 patch の差分、C の実差分、親の独立検算は整合しています。旧計装適用後 source との差は次の3箇所です。

- `#include <set>` 1行の削除。
- 前後の pointer snapshot の宣言2箇所を `std::unordered_multiset<const void*>` に変更。

include 11行は BASE と同じです。BASE の `include/trace.hh:25` の TRACE 枝内に `<unordered_set>` があり、供給不足の疑義は不成立です。

`#line` は `17, 990, 991, 1158, 1169, 1187, 1195` の7箇所を保持。X は入口の CLL の key/mode/lock pointer と counter、UPDATE/DELETE の payload 操作直前、非 INSERT の publish 直前という既存の条件・位置を保持しています。P も sort 前後の size と pointer 多重集合の比較です。ハッシュ値だけの比較へ変更されていないため、ハッシュ衝突を理由に異なる多重集合が等しいと判定されるという攻撃は不成立です。

一方、X は owner ID や検査点間の連続保持を証明しません。P の動的負例も size 違反までです。これは既存の射程であり、本変更が新たに強い保証を与えたとは読めません。

追加の実行コードは TRACE 内、外側の追加は復元用 `#line`。verifier・D297 checker・承認定数・gitlink は対象差分に含まれません。診断 build は `J:14851` でも NON_ADMISSIBLE です。**診断の all_pass を探索の受理へ直結させたり、異常を certified に昇格させたりする変更は見つかりません。**

# driver の識別と配線

`_candidate_identity()` は以下を直接検査します。

1. 解決した commit OID が指定の40桁小文字 hex と同じ。
2. 親列が `[oid, PIN]` と完全一致。
3. raw diff が transaction.cc の通常ファイル・mode 不変・M の1行だけ。
4. 再構成 blob が raw diff の新 blob と同じ。

tree の40桁形式検査もありますが、正しい Git 出力の受理集合を余計に狭めるものではありません。base blob/tree を純関数内で固定値と比較しない点も欠陥とはしません。wrapper が実 Git に対して PIN と候補 OID を指定して取得する契約であり、純関数に任意の捏造 Git 出力まで認証させる設計ではないためです。

`_capture_candidate()` は BASE の clean checkout に候補 patch を適用し、blob を取得して識別します。呼出位置は `_prepare_dependencies()` より前です。**4条件の失敗が build 後まで遅れる経路はありません。**

配線は裁定どおりです。

| 用途 | checkout と適用 |
|---|---|
| stock single/high | C、patch なし、TRACE=1 |
| lockskip single/high | C + lockskip だけ |
| perm-erase single | C + permutation-erase だけ |
| early-unlock single | C + early-unlock だけ |
| TRACE=0 比較 | BASE と C、両方 patch なし |

`_variant_run(binary, flags, source)` が同じ source を `_verify()` に渡し、実 CLI は `--protocol mocc --ccbench-root <source>`。C に計装 patch を二重適用する経路はありません。

`compute_checks()` は本文・signature とも不変。候補 mode の `patch_relatives` は候補＋負例3本で、touch set は BASE 上の候補再構成と C 上の負例適用から得ています。これは「可搬 patch と各負例が transaction.cc だけを触る」という検査として正しい入力です。

legacy の既存処理・定数・出力 schema/path は保持されています。ただし「1 byte も変わらない」を help/usage 表示まで含む絶対表現にはできません。新オプション追加でその表示は変わります。既存の実行経路を変更したという疑義は不成立です。

# 5 node と変異の歯

| node | 保証する内容 | 保証しない内容 |
|---|---|---|
| source_contract (`T:68`) | 旧 source からの指定3変更との byte 一致、include、X/P 構造、固定 blob/SHA、負例3本の厳密適用 | 実行時の全 workload・全 interleaving |
| trace0_logical_rows (`T:95`) | 既存 helper が選ぶ macro context の論理行列一致 | 実 header を含む全 TU、全 compiler、binary bytes |
| identity_checks (`T:102`) | 正例受理と、親・追加 path・mode・A/D・blob 等の1条件拒否 | Git wrapper の実配線そのもの |
| mode_source_routing (`T:127`) | 実 Git の候補子、checkout、patch、識別、build source、verifier argv、旧 path 拒否、blob 不一致で停止 | 本物の compile・benchmark・verifier 判定 |
| json_is_bound (`T:279`) | 固定 C/tree/blob/親/raw diff、再構成 source、patch hash、14 key、run 名、観測値の型、toolchain、NON_ADMISSIBLE | run 内容からの全 check 再計算、元 trace の再検証 |

routing test は環境・依存物準備・toolchain 解決・build・trace 実行・verifier subprocess を差し替えています。Git 呼出は実処理へ流し、識別・checkout・patch 適用・配線自体は実物です。`/bin/true` に対する nm/strings/objdump は配線の検査であり、C の TRACE=0 証拠ではありません。

固定 C/tree/blob/SHA は `T:24` に直接置かれ、JSON より先に source 再構成と独立 fixture を検査します。transaction 数、時刻、inode、一時 path などの揮発値は固定期待値にしていません。

事前登録変異について、静的には次の拒否点があります。

- MP1・MP3・MP4：source の指定変更との一致で拒否。
- MP2：source 契約に加え、論理行列の差で拒否。
- MD1〜MD4：識別の個別拒否対照。MD4 は routing の実 blob 不一致対照もある。
- MD5〜MD7：実 patch 適用または build spy の HEAD/source 検査。
- MD8：verifier subprocess の root 検査。
- MD9：旧 JSON path の拒否対照。
- MJ1・MJ2：consumer の固定期待値。

**KILLED の実測とは報告しません。** 特に MP3/MP4 は `T:74` の byte 一致 assertion が構造 helper より先に失敗します。後続の変異記録で「構造 helper が実際に殺した」と記すには、実際の失敗箇所の確認が必要です。hash 不一致だけに依存する構成ではありません。

# 6走から言えること

`J:14867` 以降の実測は次のとおりです。

| run | verdict / certified | cycle | X | P | other_integrity_clean |
|---|---|---:|---:|---:|---|
| stock_single | serializable / true | 0 | 0 | 0 | true |
| stock_high | serializable / true | 0 | 0 | 0 | true |
| lockskip_single | indeterminate / false | 0 | 1,877,661 | 0 | true |
| lockskip_high | **non-serializable / false** | **3,525** | 2,363,434 | 0 | **false** |
| perm_erase_single | indeterminate / false | 0 | 0 | 221,263 | true |
| early_unlock_single | indeterminate / false | 0 | 1,368,566 | 0 | true |

single の負例3本では、公開された直交違反数・cycle・other-integrity 集約値の範囲で狙った X/P に限定した拒否を支持します。early-unlock は入口理由なし、保持理由2種が各684,283件。perm-erase は `size-changed` だけです。

**lockskip_high の単一理由性は不成立です。** X の検出と certified=false は示しますが、cycle と他 integrity 異常を併発しています。`D:555` の旧 check が要求するのは X>0 なので、all_pass=true と矛盾しません。

また、`other_integrity_clean` は `D:398` に列挙した field の集約です。proof-surface や commit-witness 等を含む `Integrity.clean()` 全体と同義ではありません。

A-S1 の最小対応は、材料に「single の負例3本は indeterminate、lockskip_high は cycle・他異常を併発して non-serializable」と追記することです。コードや check を変更して結果を揃える必要はありません。

正例の certified=true から proof-surface gate 真を導く推論は、**実 verifier が当該 C の source root を評価したという配線・実測の前提で成立**します。`model.py:518` → `Integrity.clean():466` → `certification_gate_satisfied():77` の依存関係があるためです。ただし、その gate は X/P の text evidence の存在であり、I 被覆、全経路の実行、将来の全 run の certified を意味しません。stock_high の certified は今回の観測値で、旧14 check が毎回直接要求する項目ではありません。

# TRACE=0 と D297

`J:14856` の証拠は、nm の対象名0件、strings の対象文字列0件、正規化逆アセンブル一致です。binary SHA は異なります。

`D:452` は `objdump --no-show-raw-insn` を使うため、**`.text` bytes 一致は主張できません**。binary SHA の差だけから、その原因を path 文字列や特定 section と断定することもできません。README の限定は適切です。

D297 一次資料は以下と一致します。

- GCC 11.4 / 12.3：rc=0、各 report は最終 C を対象に pass。transaction.cc の16行すべてで正規化前処理一致、include 活性一致、`exact_identity`。
- clang 14：rc=1、stdout 空。stderr は空入力の環境 prefix と前処理出力の不一致。**比較未完了**であり、C と BASE の差異検出や clang pass として扱えません。
- 旧計装の負例：rc=1、stderr は transaction.cc の「include 行文字列（順序込み）が不一致」。include 契約を理由に停止した対照として成立します。ただし fail-fast の一件から「下流の全検査に他の失敗が絶対にない」とまでは導けません。

16 context は report 上の8 genome × 2 overlay です。MOCC に投影された実際の define 集合は各 compiler **4種類**で、report の genome 名は `silo|…` です。「16種類の独立した MOCC 設定」「全 TU」「admission toolchain 全体」の検査へ一般化してはいけません。根拠は `JOB/evidence/d297-gcc11.stdout.json:1` と `d297-gcc12.stdout.json:1`。D297/D780 の限定された保証と整合します。

# provenance と証拠の置換

patch commit、driver/test commit、C は Codex author / reviewer と Claude manager の trailer を持ちます。JSON commit は計測記録だけで Claude manager。`docs/ai-provenance.md:53` の例外に合い、D95 の実装代筆禁止に反する変更は見つかりません。

reviewer の実寄与は段4が記録した段3の独立検討を根拠にできます。ただし model/reasoning の実行設定そのものを、本レビューで別途認証したわけではありません。

旧 C=`1035f1e3` と最終 C は、Git object 上でも親・tree が同一です。旧 log・OID・bundle は `superseded-1035f1e3/` に存在し、最終 bundle の verify・完全履歴・SHA は `JOB/mk-C-amend.log:41` に記録されています。内容の変更はありませんが、厳密には commit の時刻 metadata も更新されており、「message 以外の commit bytes が全部同じ」という意味ではありません。

D297 は最終 C に対して21:17以降、compute も最終 C に対して21:31以降に実施されています。旧 OID の JSON を書き換えた形ではありません。

主 checkout への最終 fetch、変異工程、最終 consumer 実走、provenance 全履歴監査の完了は、今回の指定証拠だけでは確認していません。段6後の工程まで完了済みとは判定しません。

## 総括

**GO — 今回の設計・実装レビュー範囲。pin 前進や wave 全工程完了の承認ではありません。**

- **must-fix：なし。** 最小修正案は該当なし。
- **should：A-S1** — 負例 verdict の一括表現を run 別に訂正する。根拠：`JOB/s4-ruling.md:11`、`output/env/pegasus/calibration/s3_mocc_xp_pin_candidate.json:14908`。受理集合は変更せず、材料レポートの誤記を防ぐ。
- **nit：なし。**

テスト・変異・再 build・再計測・checker は**未実走・静的読解**です。登録変異の kill 実績、`.text` bytes 一致、lockskip_high の単一理由性は認定していません。