## must-fix

**0 件。** plan の主要修正は採用できます。以下は静的読解の結果です。pytest・変異実行・compute 投入は行っておらず、KILLED や実 job 完走は未実測です。

## should

**S1 — receipt が記録する source と、build 入力を証明する範囲を分ける。**

- **根拠:** plan:250–257、pilot:1690–1737, 3030–3037, 3206–3232。`patched_source_sha256` は適用直後の `transaction.cc` の digest で、plan は finalization 時の再照合も行います。一方、`build.binary_sha256` と `binary-trace1.sha256` は binary の digest です。**その binary が当該 source bytes から生成されたことを独立に検査する field はありません。** configure argv と shell の実行順が対応を支えます。
- **放置時の影響:** receipt の source 記録を、コンパイル時に読まれた bytes や verifier の source snapshot まで束縛する証明として解釈すると、discriminator 結論の根拠を過大に記述します。
- **是正案:** 本題の四 field を残し、「適用直後と finalization 時の source digest 一致、build/verifier は同じ BUILD_SOURCE を指定」と明記してください。追加した `trace0_built_from_patched_source` と `trace0_identity_witness` は省略し、実行順と witness の説明を insight に置くのが簡潔です。新しい build 証明 gate は不要です。

併せて、TRACE=0 witness の保証名を限定してください。`test_mocc_proof_surface.py:117–150,435–451` は **include 行を除去し、固定 macro context で前処理した論理行番号・非空本文の列**を比較します。完全な翻訳単位、include 活性、compute binary の同一性を検査する test ではありません。plan は「binary 同一性ではない」と限定していますが、include 除去の限定も必要です。

**S2 — patch marker の exactly-one を明示的に追加する。**

- **根拠:** job contract test:2727–2739 と 4193–4209 は固定 tuple に列挙した marker だけを数えます。新しい二組を自動では数えません。plan:99 は hydrate marker の一意性を指定していますが、patch test の説明（:301〜）には同じ指定がありません。
- **放置時の影響:** patch marker が重複しても、最初の区間だけを抽出する test は通り得ます。新 marker の一意性が契約テストの被覆から外れます。
- **是正案:** patch test に BEGIN/END 各 count==1 と順序を追加してください。hydrate は plan の指定どおりで十分です。既存二 test の両方へ重複登録する必要はありません。

## nit

**N1 — version 変異について、質問にある二例も文字列検査で検出できる場合があります。**

- **根拠:** plan:115,123,127 は `sys.version_info >= (3, 10)` の文字列を検査します。これを `>= (3, 9)` に置換すれば文字列が消えます。条件を `True` に置換し、単に `(3, 10)` だけ残しても同様です。
- **放置時の影響:** 指定された負例の KILLED 判定は変わりませんが、何を検出できないかの説明が不正確になります。
- **是正案:** 限界は「期待する文字列をコメントや未使用式に残したまま、終了条件を恒真にする変異は検出を保証しない」としてください。それは今回指定された単純な比較除去とは別変異です。意味実行 fixture の追加は不要です。

**N2 — 旧候補の hydrate 拒否はケース依存にする。**

- **根拠:** plan:112–113,122。ケース(a)の python3 は拒否候補ですが、(b)の python3 は成功候補です。
- **放置時の影響:** python3 の hydrate を無条件に拒否する stub にすると、正常実装でも(b)が失敗し、正例が成立しません。
- **是正案:** hydrate 拒否を(a)の旧候補設定に限定してください。plan は無条件拒否まで指定していないため、設計矛盾とは判定しません。identity assertion があるので、この拒否 stub 自体を省いても指定変異は検出できます。

**N3 — hydrate 実行失敗の stage は、この test 設計では観測しません。**

- **根拠:** pilot:154–161,1534–1537。hydrate の非0は既存 ERR trap により stage=`shell` になります。plan の抽出 prefix は `set -Eeuo pipefail` と `write_failure` stub を置きますが、ERR trap は含めません。
- **放置時の影響:** 抽出 test は非0終了・suffix 未到達を観測できますが、本番の failure stage を実証しません。正常実装の(a)〜(d)には、選択成功後の hydrate 失敗例もありません。
- **是正案:** 「gate 拒否の stage は third_party、hydrate 実行失敗の stage は既存 shell、後者は新 test の被覆外」と記してください。今回 stage の変更や追加ケースは必須ではありません。

**N4 — 全候補不在時の `rejected: none` は診断上の限定です。**

- **根拠:** plan の `command -v … || continue` と既存 checker の pilot:1756〜。
- **放置時の影響:** receipt は生成されず停止しますが、不在だった候補の内訳は記録されません。
- **是正案:** 既存 gate と同じ挙動として許容できます。必要なら説明で「rejected は probe 実行後に拒否された候補」と限定してください。

**N5 — decisions fragment と重複した実物再検査は増やさなくてよい。**

- **根拠:** 親 brief の「必要なら decisions fragment」、plan:263,275,381、pilot:3297–3341。
- **放置時の影響:** decisions fragment の有無では実行成果物は変わりません。同じ digest 再検査を二 writer に複製しても、build 入力の束縛範囲は広がりません。
- **是正案:** schema 判断は insight に残せば足り、decisions fragment は削除可能です。receipt writer が実物・sidecar を照合し、job-result writer は既存 digest 鎖と v2 の必須 field・型を確認する役割分担で十分です。

## verifier source 配線と規律2

**切替は「配線修正」と判定します。** ただし、固定 trace に対する出力が切替前後で同じ、という意味ではありません。

読取りの経路は次のとおりです。

1. `__main__.py:5–8` は CLI に委譲します。実際の引数受取りは `cli.py:52–53`、引渡しは `:70–74` です。
2. [`model.py:130`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2780-mocc-pilot-discriminator/orchestrator/verifier/model.py:130) 以降は指定 root の `cc/mocc/CMakeLists.txt` を読み、SOURCES の各ファイルを `:174–177` で開きます。Git OID を読んでいません。
3. コメントと literal `#if 0` を除き（:94–116）、literal `#if TRACE` の first branch を抽出します（:204–230）。
4. emitter の字句的存在から X/P を evidence-present/absent にします（:278–310）。X/P の両方が present であることが certification gate の条件です（:78–82）。

今回の checkout の HEAD は読取りで **511c9538e4e8efa54b45cda62e72389ed3b706ec** と確認しました。CMake の SOURCES は `transaction.cc util.cc lock.cc` です。現行 pilot:2231 はこの checkout を指定し、**build した e9e477ca の worktree さえ読んでいません**。

patch 適用後の BUILD_SOURCE に変えれば、同じ判定関数へ「計装済み e9e477ca」の source を渡します。X/P 判定規則も rc の許可集合も変更しません。source を入力に含めた verifier の受理条件は不変で、入力が正されるため結果は変わり得ます。なお、字句的 evidence-present は実際の発火・到達可能性・コンパイル条件の証明ではありません（model.py:236–240）。

plan の逐語変更は source 変数の選択と argv 置換だけです。pilot:2239–2242 の **rc∉{0,1} で停止**、:2985 の finalization 条件を緩める案はありません。rc=3 を通す分岐も追加されません。

general mode で CCBENCH_BASE を維持する判断は、今回の「既存 general mode の挙動を変えない」に合います。ただし、その既存 source 不一致も維持します。「general mode の source 配線まで正しい」とは主張しないでください。

## HYDRATE_PY の import と fail-closed

`silo_ladder_rung1.py` の module 直下は、stdlib・repo module の import、Path 解決、定数、正規表現、class/function 定義と decorator が中心です（:15–168,208–247,1901）。環境変数を読む処理や file 作成処理は関数内で、末尾の main は `__name__` guard 内です（:5120）。**同 module 直下から hydrate・build・file 作成を起動する処理は見つかりません。**

ただし repo module の推移 import はあり、無依存・副作用皆無の軽量 probe とまでは言えません。F1027 の import 鎖を実際に通せるかを確認する選択として妥当です。今回、import の実行時間や推移 import 全体の副作用は実測していません。

`orchestrator/orchestrator/` と `orchestrator/orchestrator.py` は存在しません。外側 `orchestrator` は `__init__.py` のない namespace package、`campaign/__init__.py` は説明文のみです。指定した二 root による、質問の二重 package 衝突は見つかりません。`fetch_third_party.py:52–64` の root 挿入方針とも整合します。

## patch 適用 block の確認

現物 patch は同一 pathname の `transaction.cc` を変更する通常の diff です。plan の適用順は妥当です。

- **numstat は適用しません。** `patchharness.py:155–171` も読取り用途です。hunk が現在の tree に当たらなくても統計は取得できるため、適用可否を確認するのは後続 `apply --check` と実 apply です。
- awk は **一行・三列・数値二列・期待 path 完全一致**を要求します。空出力、複数行、quoted path、第三列に `old => new` が現れる形は拒否します。ただし `NR == 1` 単独が一般的な rename の old/new 全 touch set を証明するわけではありません。今回の既知 patch に対しては十分で、汎用 rename 検査の追加は不要です。
- `if ! PATCH_SHA=$(sha256sum … | awk …)` は、pipefail により sha256sum 側の非0も検出します。`if !` 内では ERR trap に任せず、明示した `instrumentation_patch` 失敗処理へ進みます。逐語案はこの用途に整合しています。
- apply 除去では、preimage の hash と receipt field が依然生成できます。親 brief の「apply を外す → receipt 束縛欠落」は検出条件として不十分です。plan が **既知 postimage・apply 呼出記録で検出する**よう修正した点を採用してください。

## schema v2 と consumer

**v1→v2 の置換を推奨します。**

pilot:76–79 は attempt directory を create-only で作り、:2490〜で今回の receipt を生成し、:3303〜でその receipt を job-result writer に渡します。既存 receipt の再開・再処理入口は見つかりません。08-28 の v1 receipt を現行 writer に再投入する通常経路は確認できず、歴史的成果物を置換で書き換えることもありません。

consumer は schema literal だけでなく、`t1943_g2_discriminator`、`discriminator_result`、receipt filename、pilot 名でも repo の Python/shell を検索しました。

- `mocc_trace_pair.py:27,409–410` は **v4 完全一致**です。
- `mocc_g2_repro_ledger.py:27,197–200,603–604` は **v3 完全一致**です。
- discriminator 自身は receipt を読まず、trace/witness manifest と verifier JSON を読みます（:658–663）。
- submitter の同名 field は submit receipt の mode 指定で、pilot receipt の reader ではありません。

schema を組み立てる追加の専用 consumer は見つかりませんでした。ただし「pilot 自身と test だけ」は、**今回検索した repo 実装における専用 consumer**という限定付きの結論です。

v2→v1 改変 test は残してよいと考えます。既存 helper は receipt と sidecar だけでなく `RECEIPT_WRITER_SHA` も再計算します（test:3111–3132）。この形なら digest 不一致による停止と schema 拒否を区別でき、「置換した」という契約を直接検査できます。

## 親 brief の再検算と scope

親 brief の補正点は次のとおりです。

- **TRACE-only + `#line`:** patch 現物は説明と整合します。ただし witness の保証範囲は S1 の限定が必要です。今回は test 未実行です。
- **checker が OID を読む:** 正しいです。`check_trace0_preprocess_identity.py:528–529` は old/new を `_git_show` に渡します。今回の作業ツリー patch は対象外です。D297 の保証と patch witness を混同できません。
- **判定 source 捕捉は外側 repo:** 正しいです。pilot:637〜の HEAD/status 捕捉は REPO_ROOT 対象です。外側 status に submodule 状態が現れる場合はありますが、別の BUILD_SOURCE の bytes を捕捉しません。
- **「nm/strings」:** pilot は TRACE=0 binary の bytes を読み、同 fd に `nm -a` を実行します（:1850–1888）。plan の訂正を採用してください。
- **前 wave の「indeterminate しか出せない」:** 現行 pilot では verifier rc=3 で停止するので、discriminator の `indeterminate` が生成されるとは限りません。親 brief 冒頭の「verifier rc=3 で pilot 停止」の表現が正確です。

scope の採否は以下です。

| 追加事項 | 推奨 |
|---|---|
| verifier source 配線 | 残す。本題の patch 適用を verifier に届けるため必要 |
| general-mode 漏れ検査への五 file 追加 | 残す。追加 artifact の既存分類契約への追随 |
| v2→v1 改変ケース | 残す。schema 置換を直接検査 |
| decisions fragment 一件 | 削除可能。insight の判断記録で足りる |

新しい verifier gate、汎用 patch 検証、build provenance 機構は不要です。追加すべき局所的な契約は S2 の patch marker 一意性です。

## 総括

**must-fix は 0 件。verifier source の切替は「配線修正」、schema v2 は置換採用を推奨します。**

実装時は patch marker の一意性を補い、receipt の digest 記録と build 入力の証明を区別してください。TRACE=0 witness は include 除去後の限定的な前処理比較として記述し、実測結果は親の test・変異・compute 一走で確定してください。