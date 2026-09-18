**暫定案は、最小変更の実装候補としてGOです。** fixtureの検査内容を維持したまま重複snapshot取得を減らせます。ただし、timeout解消やmain land可能を確定する証拠にはまだなりません。HEADは指定の`26b2968bcebe3ec23dccac8d7626fbfc2aefff9f`と一致し、編集・pytest実走は行っていません。

**現行の受理:** T1259は、実repo由来のHEAD・source digestを含む既存fixtureの下で、R1の明示値一致、R2の正確なargvによる未承認driver拒否、R3の観測されたambient条件など、各ケースの契約を満たす結果を受理します。
**現行の拒否:** 明示値欠落・値交換・承認不一致・source digest不一致・不正な開始repo状態・実行前後のdigest変化・driver timeout・argv改変などは、既存の負例として拒否します。

根拠と変更範囲は次のとおりです。パスは作業rootからの相対表記です。

| 論点 | file:line | 診断 |
|---|---|---|
| 共有対象 | `orchestrator/tests/test_t1259_qsub_env_delivery_probe.py:73` | module fixtureが実`_repo_snapshot`を取得する。`:83`のautouse fixtureにより、本文でsnapshotを使わないケースもconsumerになる |
| ケース間隔離 | 同`:90`、`:94` | templateから各ケースへ、さらに呼出し元へdeepcopyする。集約しても負例の改変が次ケースへ漏れる構造にはならない |
| 現行の分割 | `orchestrator/tests/conftest.py:668`、`:2154` | 既存4関数だけsuffixを保持し、それ以外のresource nodeは`@real-repo`を除去する |
| パラメータ対応 | 同`:800` | `module::function`へ正規化するため、関数単位の登録で全パラメータに効く |
| lock保持 | 同`:452`、`:626`、`:2278` | T1259はparent read、ccbenchアクセスなし。setup/call/teardownを囲む既存P/S lock契約は集合追加では変わらない |
| shard閉包 | `tools/acceptance_shards.py:325`、`:761`、`:895` | fileとmarkerから閉包を作り、suffixはcanonical化する。markerもfileも不変なのでshard分割条件は変わらない |
| 実行順 | `orchestrator/tests/conftest.py:1776` | 同じscopeのitemをまとめ、内部の相対順序を保持する |

静的に数えたT1259は**30関数・51ケース**です。指定JUnitにも51ケースがあり、errorは指定の承認値欠落ケース1件でした。tracebackはfixtureの`:76`からprobeの`:174`へ入り、`git ls-files --others --exclude-standard -z`が30秒でtimeoutしています。これは**負例assertionの失敗ではなくsetup error**です。

**推奨最小変更は2ファイルです。**

- `orchestrator/tests/conftest.py:668`の既存集合へ、T1259の30関数を明示追加する。既存inventoryの`:279`から並ぶ30関数と同じ対象に限定する。
- `orchestrator/tests/test_real_repo_serialization.py:298`の独立goldenへ同じ30関数を明示追加する。production集合からgoldenを生成しない。

集合は4関数から34関数になります。T1259本文・fixture・probe・timeout・access分類・shard allocator・duration台帳の変更は不要です。ファイル名prefixによる包括登録も不要です。

goldenの追随は**既存テスト期待値の変更に該当します**。意味は「worker集約を要求する対象を、既存のmodule snapshot consumerへ拡張する」であり、T1259の成功・拒否条件を変えるものではありません。`docs/dev-wave/workers.md`の期待値変更禁止を黙ってすり抜けず、authorへの変更範囲にこの独立goldenの追加を明記すべきです。

同じ正例・負例が残る具体例は次のとおりです。

| 維持する検査 | file:line |
|---|---|
| R1の明示値一致・実driver非実行 | `test_t1259_qsub_env_delivery_probe.py:231` |
| R2の実driver拒否、rc=2、正確なargv、副作用なし | 同`:266` |
| R3のambient未配送／不一致配送の両条件 | 同`:308` |
| 今回setup errorとなった値欠落を含む3負例 | 同`:407` |
| HEAD・detached・tracked/untracked不正の4負例 | 同`:611` |
| status一致でもsource digest変化を拒否 | 同`:650` |
| driver timeoutを正常拒否と誤認しない | 同`:685` |
| argv改変を拒否 | 同`:753` |

**効果は機構上期待できますが、実測改善は未確認です。** 現行は複数workerにmodule fixtureが生成され得ます。候補では通常のloadgroup実行でT1259全ケースが同一workerの連続した実行単位に入り、既存module fixtureの共有が効きます。ただし「現在51回取得している」「必ず所要が短縮する」とは言えません。fixture再生成回数・worker再起動・I/O競合の寄与は今回測っていません。

より小さい既存策として、失敗ケースだけの追加は不十分です。他のautouse consumerが別workerに残り、重複取得を残します。新しい専用groupは既存marker・閉包契約への変更が増え、全体のworker数削減は本題外へ影響します。この条件では30関数の既存集合追加が最も局所的です。

**制約meta-testと変異の確認点**

- `test_real_repo_serialization.py:1586`のcollection・独立golden一致、`:1735`のshard閉包・意図的split拒否を維持する。
- `test_acceptance_schedule_order.py:721`のG6で、strip→reorder順序、marker、item集合保持を維持する。ここは集合を参照するため、静的には期待値変更不要です。
- `test_real_repo_serialization.py:5938`の実loadgroup同一worker検査と、optionを外した負対照を維持する。
- 注意点として、既存suffix変異killerの`:1545`は代表3件だけを検査し、T1259を直接検査しません。集合とgoldenの追加だけでは「T1259だけ誤ってstripする」変異を直接殺す保証が不足します。同じhelperを独立goldenの全memo nodeへ適用する程度の局所拡張が妥当です。
- 変異は、①T1259の1関数を集合から落とす、②登録済みT1259だけsuffixを除去する、③通常の非memo nodeまでsuffixを保持する、④shard markerを失わせる、を別々に確認する。①は登録漏れ、②③は配置契約、④は閉包契約の検査であり、probeのcorrectness killと混同しないでください。
- 元のT1259全51ケースを残し、変更後の単独走と最終受入で確認する。単独緑を受入緑へ読み替えないでください。

残るリスクは、T1259が**既存4件とも同じ`real-repo`実行単位になる**ことによる直列部分の増加です。また、共有fixtureの取得が1回でもtimeoutすれば、そのworkerのconsumerへsetup errorが波及し得ます。集約は走査機会を減らしますが、外部I/O停滞を解消する保証ではありません。既存fixtureがclean/detachedをモデル化している点も不変であり、各ケースが実repo状態を新規取得する検査へ強化されたとは主張できません。

## 総括

**GO：既存集合へのT1259全30関数追加、独立golden追随、既存suffix検査の局所補強。**

**NO-GO：この静的診断だけによるtimeout根因確定・受入完了・main land判定。** 実snapshot・deepcopy・30秒timeout・全51ケース・既存lockとshard閉包は保持できますが、I/O根因と変更後の受入成功は未確認です。
