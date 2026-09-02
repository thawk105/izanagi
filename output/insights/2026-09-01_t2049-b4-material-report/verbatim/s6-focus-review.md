## 総括

fix1/fix2 により、正常経路、単回観測、独立 oracle、campaign root 導出、公開 marker、Markdown は概ね閉じた。  
ただし campaign root を復元できない場合の fail-closed は限定的で、sol F4 は partial のままである。  
遅延キャッシュ自体には現行 node 間の順序依存を認めないが、共有 campaign への残留出力による実在の順序依存が変異走にある。  
SURVIVED 7 件を単独 gate の証拠から外す結論は妥当だが、M23/M24 の因果解釈は誤っている。

## sol の所見の対応表

| F | 判定 | 根拠 file:line |
|---|---|---|
| F1 | closed | canonical role path は `test_p3_b4_material_report.py:67-71`。fixture は publication 生成だけで、正常 assembly、binding、evaluation、document の検査は call 段階の `:151-180` に移った。 |
| F2 | closed | artifact 在否は frame 作成時の一度だけ `p3_b4_material_report.py:283-307` で凍結され、row は `:465-487`、独立検査は `:576-579` の同じ値を使う。観測回数 test は `test_p3_b4_material_report.py:387-407`。 |
| F3 | closed | oracle は manifest、registry、source bytes から独立に期待値を作る `p3_b4_material_report.py:498-663`。ABORT の非 null 理由は `test_p3_b4_material_report.py:73-91,307-309`、public builder 負例は `:423-482`、Markdown 一致は `:344-377`。 |
| F4 | partial | unresolved source は保持する `p3_b4_material_report.py:1029-1085` が、partial 時の拒否は字面上 `output/.../campaigns` を含む場合だけ `:1109-1118`。その形を使う test `test_p3_b4_material_report.py:240-269` は閉じたが、それ以外の未知 campaign root への出力は許す。 |
| F5 | partial | M16 は三層へ分割済み `test_p3_b4_material_report.py:664-726`。一方 M13 test の alias `:580-592` は、対象比較前に `p3_b4_material_report.py:965-982` で解決済みとなり、M13 自身へ照準していない。 |
| F6 | closed | rejection typed reason、provenance、argv、artifact hash を Markdown に表示する `p3_b4_material_report.py:846-918`。一致 test は `test_p3_b4_material_report.py:183-237,344-384`。 |
| F7 | closed | 対象 test 全体 `test_p3_b4_material_report.py:1-890` に skip、xfail、期待値緩和はない。commit `ee13b00c7` 自体の変更対象は同 test file のみ。 |

## luna の所見の対応表

| F | 判定 | 根拠 file:line |
|---|---|---|
| F1 | closed | sol F1 と同じ。正常経路の専用 node は `test_p3_b4_material_report.py:169-180`。 |
| F2 | closed | lock path の parent、WAL の `parents[1]` を使う `p3_b4_material_report.py:996-1010`。実 campaign root の確認は `test_p3_b4_material_report.py:300-306`、三方向 test は `:552-577`。 |
| F3 | closed | file fsync、JSON/Markdown link、directory fsync、最後の commit marker、BaseException rollback は `p3_b4_material_report.py:1143-1228`。marker、二本目失敗、marker 失敗、rollback 失敗の test は `test_p3_b4_material_report.py:729-820`。 |
| F4 | closed | provenance、argv、rejection reason と正しい escape 順は `p3_b4_material_report.py:828-918`。独立 renderer oracle は `test_p3_b4_material_report.py:326-384`。 |
| F5 | partial | standalone import bootstrap は `test_p3_b4_material_report.py:15-17` で閉じた。一方 subprocess は依然変数 `argv` を渡す `:832-863` ため、原レビューの bytecode checker 盲点は残る。 |
| F6 | closed | CLI bootstrap は `p3_b4_material_report.py:26-28`、canonical JSON は `:150-180`、clean subprocess と byte 一致は `test_p3_b4_material_report.py:823-875`。 |
| F7 | closed | `_ImmutablePublication.root` は削除済み `test_p3_b4_material_report.py:40-46`。`contract_binding` は provenance の生成・検査に使われる `p3_b4_material_report.py:751-758,797-807`。 |
| F8 | closed | commit `ee13b00c7` の変更は対象 test file のみで、対象外 file への fix2 混入はない。 |

## fix が入れた新しい欠陥

- 遅延キャッシュについては、現行 suite での順序依存は refuted。`_INPUT_CACHE` と `_DOCUMENT_CACHE` は `test_p3_b4_material_report.py:49-50` にあるが、成功値だけを `:151-166` で格納し、現行 `_document()` caller は未 patch 状態で読み取り専用に使う。mutation run も process ごとに分離されている。

- ただし別の実在する順序依存がある。`[below]` node は共有 campaign の固定先へ書く `test_p3_b4_material_report.py:558-574`。gate mutation で拒否されないと、`pytest.raises` が失敗した時点で後続 cleanup assertion `:575-577` に到達せず成果物が残る。その後の symlink node は同じ実体 `:595-610` を検査し、先行 node の残留 file で二次的に赤になる。登録 report でも M23/M24 の両方が `[below]` と symlink の2 nodeを記録している `mutation-registered-report.json:1274-1279,1321-1352`。

- fix2 は setup ERROR を call FAILED に変えたが、単一 node 帰属までは閉じていない。document build が失敗すると cache に入らない `test_p3_b4_material_report.py:160-166` ため、M03 は16 nodeへ波及している `mutation-registered-report.json:136-174`。一部は各 node 本来の期待理由より前の `projection_value_mismatch` で赤になっている。

## 冗長 gate 裁定の検査

SURVIVED 7件を「その単独 gate が不可欠だという証拠」から外す結論自体は妥当。ただし M23/M24 を使った説明は因果帰属として成立しない。

| 変異 | 裁定 | 静的根拠 |
|---|---|---|
| M05 | 妥当 | 件数 gate `p3_b4_material_report.py:504-506` を外しても、行不足なら identity 集合が必要件数にならず `:507-509` が拒否する。 |
| M06 | 妥当 | 全単射 gateを外しても、各位置を publication と照合する `:538-586` が複製行を拒否する。 |
| M07 | 妥当 | 全体 round-trip `:657-659` を外しても、各 source の UTF-8、hash、object を元 bytes と照合する `:588-637` が拒否する。 |
| M10 | 結論は妥当、M23 の解釈は不当 | equality `:1103-1104` は、同一 path も真になる below と above `:1105-1108` の双方に包含される。M23 の実際の赤には `[equal]` がなく `[below]` だけが一次原因 `mutation-registered-report.json:1274-1279`。M10 を露出させるなら equal、below、above の三層 `p3_b4_material_report.py:1103-1108` を同時に外す必要がある。 |
| M13 | 結論は妥当、M24 の解釈は不当 | 比較箇所の resolve `:1100-1102` は、output が既に `:982`、campaign roots が `:1003,1007-1009` で解決済みなので冗長。M24 の一次赤は below gate の除去であり、M13 の効果ではない。全 resolve 層を試すなら `:982` と `:1100-1102` を同時に外し、lexical には campaign の配下でない sibling/`..` alias を使う。現行 `campaign/runs/..` を使うなら below `:1105-1106` も同時に外す必要がある。 |
| M21 | 妥当 | count と round-trip を同時に外しても、行不足は `:507-509`、source 改変は `:588-637` が拾う。実走 survivor は `mutation-registered-report.json:1173-1202`。 |
| M22 | 妥当 | bijection と3 identity field の期待値を外しても、row/block ordinal、planned path 等の位置照合 `p3_b4_material_report.py:538-586` が複製を拒否する。実走 survivor は `mutation-registered-report.json:1219-1248`。 |

M23/M24 の symlink node 赤はさらに、先行 `[below]` nodeが残した report を見た二次障害である。したがって「KILLED 20 / SURVIVED 7 / MISMATCH 0」は登録 spec との一致としては正しいが、M23/M24 が M10/M13 の mask 仮説を実証した、とは言えない。

## 残る所見

- **real / report 配置:** partial discovery で未知 campaign root が `output/.../campaigns` 形でなければ出力可能 `p3_b4_material_report.py:1109-1118`。report が campaign 成果物集合を汚染し得る。certified selection への直接変更はない。**must-fix**。
- **real / 変異台帳:** M23/M24 の赤理由に共有 filesystem の残留状態が混入する `test_p3_b4_material_report.py:552-610`。台帳の failed-node 因果帰属が誤る。runtime report 自体は不変。**must-fix**。
- **real / 変異台帳:** M03 などの builder mutation が専用 node以外へ広く波及し、fix2 の単一 node 帰属を満たさない `test_p3_b4_material_report.py:160-166`。KILLED 判定そのものは維持できるが、台帳の単一理由証明が弱い。**must-fix**。
- **real / M13 test:** alias は対象 gate 前に canonical 化される `p3_b4_material_report.py:982`。現行 runtime は安全だが、M13/M24 の説明は証拠にならない。変異台帳のみ影響。**must-fix**。
- **refuted / 遅延キャッシュ:** 現行 node は cached object を変更せず、patch 中に `_document()` を初期化する node もない `test_p3_b4_material_report.py:151-166`。report、台帳、certified selection への影響なし。**対応不要**。
- **real / bytecode checker 盲点:** subprocess の変数 argv `test_p3_b4_material_report.py:832-863` は原レビューどおり checker の静的対象外。現在は `-B` も環境変数も存在するため成果物影響はなく、将来の pyc 防壁だけが弱い。**nit**。

## 検査できなかったこと

- read-only 制約に従い、pytest、test 並べ替え走、mutation run は実行していない。緑とは報告しない。
- 親提示の 41 passed、103件一覧、baseline、27件 mutation 結果は所与として扱った。
- process 強制停止時の commit marker durability と、異なる test 順序での二次失敗集合は実走再確認していない。