## 所見 (A-1 …)

静的検査の結論です。指定資料と関連実装を読みました。編集・pytest・実測は行っていません。以下の行番号は対象 worktree のものです。

**A-1 — must-fix／plan・brief P1/P2：保持 report は「現在の木の full validation 成功」を保証しない。**

次の入力は、plan の条件をすべて満たしたまま委譲できます。

1. active v2 の実 `launch_validate` が成功する。
2. namespace・receipt・closure の外にある、既に列挙済みの通常ファイルを、無害な内容から合成 holdout hit へ変更する。
3. HEAD、相対ファイル名集合、active 世代を変えずに receipt を再解決する。

`resolve_active_generation` の dirty 検査は namespace 内だけです。`_enumeration_digest` は名前集合だけなので変わりません。凍結文書の候補・式・規約も変わりません。したがって保持 report には新しい未申告 hit が現れず、委譲が成立します。現時点で `launch_validate` を再実行すれば C2-4 が拒否する木です。

誤認の向きは「hit を持つ report を zero-hit と読む」ではありません。**既存の承認済み hit を持つ古い report を、現在も期待集合と完全一致している証拠として扱う**ことです。closure 内の hit を同名ファイルの内容交換で消す場合も、古い report は消失を示しません。

既存の走査中 TOCTOU と、返却済み report を campaign-start まで再利用する窓は区別すべきです。single-tenant でも、同じプロセスによる逐次的な内容変更は可能です。

局所修正は、古い token の名前集合照合だけで再検証済みとせず、必要な receipt 境界で既存 `launch_validate` を再実行して新しい report を使うことです。新しい内容 hash 機構や C2-4 の再実装は不要です。

**放置時の成果物影響：現時点の C2-4 が拒否する木まで receipt が active-valid になり、他条件が揃えば oracle gate／campaign-start が通ります。**

**A-2 — must-fix／plan：変異 matrix は単一理由性をまだ満たしていない。**

m2・m3・m4・m8 は、現状の記述だけでは変異位置と受理集合の変化を一意に結び付けられません。特に、公開 gate が別理由で拒否し続けるのに refusal の件数だけが変わる赤は、DW-M03 の kill ではありません。

m6・m7 は必ずしも世代再解決と冗長ではありません。ただし入力の選び方と、前後に置く重複比較の実装次第です。具体的な切り分けは後述します。

**放置時の成果物影響：弱体化を検出した証拠にならない赤で変異受入を満たし、未検証の変更を land するおそれがあります。**

**A-3 — should／plan・brief scope：adapter への委譲追加は現行 production 経路では到達しない。**

driver の adapter は、選択した freeze の SHA が receipt の v1 holdout SHA と一致したときだけ発火します。正常な v2 文書では一致しません。一方、v1 経路では launch token を取得しません。

もう一つの production caller、`s8b_holdout_freeze.py:1247` の T-080 検証経路も、token なしで `verify_receipt` と adapter を呼びます。したがって adapter 自体は生きていますが、**追加予定の委譲分岐には到達しません**。

提示された裁定には adapter への同条件適用が明記されています。しかし今回の直接依頼は、到達しない追加を除くよう求めています。この差を説明したうえで、adapter の新引数・driver の転送・委譲専用 test は外す判断が妥当です。既存 adapter 検査は維持します。

**放置時の成果物影響：oracle の必要経路を改善しないまま、adapter 直接 API の受理集合と land 差分だけが広がります。**

**A-4 — should／plan：fixture 切り離しの証拠に、draft 側の実 hit 負例も必要。**

宣言された削除集合 S は走査結果と独立であり、方向は妥当です。ただし、copy の差分集合検査と floor の `clean_scan_digest` 負例だけでは、T-080 draft の zero-hit 拒否を残したことの挙動証拠にはなりません。

切り離し後の同じ fixture に、S 外の既存検索対象 path へ合成 hit を置き、実 draft が層2で拒否する対照を使うべきです。これは検査を緩める変更ではありません。

**放置時の成果物影響：fixture の緑化に伴う draft 拒否能力の低下を見逃したまま land する余地が残ります。**

**A-5 — nit／plan・brief P3：初回解決維持の必要性は確認できない。**

P3' で必要な集約・epoch 比較・解決回数契約を維持できます。3回案が成果物をより安全にする根拠は、現物からは確認できません。

**放置時の成果物影響：受理集合の差は示せません。履歴全検証の重複と既存 call_count 契約の変更が残ります。**

## 報告保持 vs 自前再走 の判定

**A-6 — nit／plan・brief P2：走査範囲の相違そのものは、今回の除外拡大にはならない。**

現物の関係は次のとおりです。

| 比較点 | v1 の通常走査 | v2 の走査 |
|---|---|---|
| 列挙元 | `enumerate_repository_files` | 同じ関数 |
| prefix 除外 | `output/s8b-freeze/` 全体 | 無効 |
| exact 免除 | なし | active-chain と selector 証拠 |
| exact 免除の bytes | 対象外 | 検証済み hash と一致した場合のみ免除 |

`_active_chain_exempt_exact` が返すのは v1 freeze、active 世代、approval、pointer の4 pathです。すべて既存 prefix 内です。

`_selector_evidence_exempt_exact` が免除する predictions、journal、raw、envelope も同じ prefix 内です。検証で参照する builder・parser・role 等の source は、参照しただけで免除集合に加わりません。

したがって、現実装については、

> v2 で exact 免除された path が、v1 では検索対象だった

というケースはありません。むしろ v2 は、prefix 内でも免除されないファイルを走査します。official run_dir と候補 exact file はこれらの免除に含まれません。

よって、**新鮮な v2 report に凍結文書の候補集合・候補 ID・検索式・照合規約を束縛することは意味的に正しい**です。それらは検索の意味を束縛する比較であり、検索 scope 全体の同一性検査ではありません。

**放置時の成果物影響：この論点だけによる受理集合の意図外拡大は確認できません。**

`_assert_search_pass` と委譲先の差集合も区別できます。

| `_assert_search_pass` の要求 | 委譲先の扱い |
|---|---|
| holdouts が Mapping | 実 `search_repository` の構築結果。委譲側の候補集合検査も維持 |
| 各 holdout 結果が Mapping | 同上 |
| `conjunction_hits` が list | C2-4 自体は要求せず `set(...)` 化する |
| holdout hit が空 | 意図的に closure 導出集合との完全一致へ置換 |
| 陽性対照が bool でない正整数 | `_assert_search_operational` が同条件を要求 |

list 型検査は文字どおりには継承されません。ただし実 scanner は list を返し、deep-freeze 後は tuple になり得ます。公開 API で得た report を保持する範囲では、これを入力受理の穴とは判定しません。任意 Python コードによる token 偽造への耐性は、既存型も保証していません。

**比較結論：report 保持を採る意味的根拠はあります。ただし A-1 の鮮度問題は未解決です。** 自前の v1 再走で束縛検査だけを行い、現在の hit を判定に使わない案も、A-1 を解決しません。両案からなら、既存 full validation の新鮮な report を使う方が規律2に整合します。

root 束縛と世代再解決の防御力は以下です。

- 安定した symlink alias は `Path.resolve()` で同じ root になります。同じ実体なので、それ自体は誤受理ではありません。
- bind mount による別 path や同一実体の別名は、通常は文字列が異なり拒否されます。inode 同一性は検査していません。
- 同じ絶対 path の mount 差替えや、resolve 後の symlink 差替えまでは防ぎません。同一 HEAD・名前集合・正常 namespace を持つ別実体なら A-1 と同じ内容差を持ち込めます。これは filesystem identity 保証の限界であり、新しい防壁の追加は今回提案しません。
- dirty namespace file は、型＋HEAD だけでは見逃しますが、世代再解決が拒否します。
- 通常の旧世代 token は HEAD 比較でも落ちます。一方、HEAD フィールドだけを現行値にした旧世代 object は、世代 hash・番号・導入 commit の再照合で拒否できます。
- `ReverifiedFreeze` は同じ active 世代を再解決できても admission 型ではありません。ここは exact type が独立して必要です。

## P3' (解決 1 回化) の判定

**P3' を推奨します。A-5 のとおり、3回案より劣る正しさ上の点は確認できません。**

必要な条件は、receipt 解決を省く早期 return を作らないことです。

| 経路 | receipt 解決 |
|---|---|
| v2 launch 成功 | token 付きで1回 |
| loader／launch 失敗 | token なしで1回、既存 refusal と集約 |
| 公開 gate の v1 経路 | token なしで従来どおり1回 |
| campaign-start 前 | 採用済み resolution と比較するため、さらに1回 |

`gate_check` の明示的 `ratified_error`、freeze load 失敗、v1 分岐にも解決が必要です。`run_block` は現状、独立した v1 成功経路を持たず、最初に active loader を要求します。

`_make_gate_decision` は渡された resolution の refusals を無条件に集約します。解決時点を後ろへ移しても、この性質は変わりません。`_campaign_t080_value` の invalid 拒否も維持できます。

epoch 比較は、**launch 後に採用した resolution と campaign-start 前の resolution** の4要素を比較すれば成立します。plan の3回案も最初の resolution を成功後に置換するので、その最初の解決を epoch の基準として保存する追加防御はありません。

既存 `test_run_block_resolves_receipt_once…` の実契約は `call_count == 2` です。P3' はこれと、既存 drift test の2要素 side effect を維持できます。

ただし、P3' は呼出し回数の整理であり、古い report の鮮度を保証する策ではありません。A-1 は別途解決する必要があります。

## 変異の帰属表 (m1〜m8)

以下は A-2 の内訳です。まだ実装・注入を行っていないため、kill は未確認です。

| 変異 | 静的判定と具体的な修正 |
|---|---|
| **m1：完全一致→包含** | closure 外・namespace 外の追加 hit なら、C2-4 が狙う境界になる。ただし公開 gate が他理由で拒否し続け、launch refusal だけ消える赤は kill に数えない。実 `launch_validate` の reject→return を直接観測するか、他 gate がすべて成立する接続 fixture を使う。 |
| **m2：集約／invalid 拒否を除去** | 2変異を分離する方針は正しいが、同じ end-to-end 入力では互いに mask する。factory 変異は公開 `gate_check` の allowed 変化を観測する。campaign-value 変異は既存 driver seam で gate 通過後の境界を検査し、production 全体の単独 gate と主張しない。R trailer 改変は token 取得前に確定させ、launch が本当に成功することを確認する。 |
| **m3：承認前委譲** | G のみの木には本物の launch token がない。active 再解決だけを外しても、token 不在・exact type・loader 失敗が残る。公開 driver の未発効負例は必要だが、そのまま単一 predicate の kill 証拠にはならない。単独変異の証拠から外すか、層2 helper の具体的な「token なしでも委譲」変異へ照準を明示する。 |
| **m4：検索規約照合削除** | 改変した凍結 doc を full receipt／adapter に通すと、bytes・再構成等も拒否し得る。各比較を直接層2 helper で検査し、他項目は正常に保つ。adapter 版は A-3 により不要。refusal 文言だけの変化は不可。 |
| **m5：開始前再検査削除** | gate 後に receipt を変更し、他入力を固定するなら独立した証拠になる。再検査と比較を除去した結果、拒否から campaign-start 到達へ変わることを観測する。削除で未定義変数例外が出ただけなら kill ではない。 |
| **m6：activation HEAD 比較削除** | **outer token の HEAD だけを変える fixture なら、条件5とは冗長でない。** 条件5が照合する ratified の世代情報は正常なままだからである。後段でも outer HEAD を再比較する実装なら mask するので、その場合は冗長 gate として単独証拠から外す。旧 HEAD の本物 token をそのまま使う fixture は inner HEAD／世代比較も落とすため不適切。 |
| **m7：列挙 digest 比較削除** | **namespace 外・非 ignored の通常ファイル追加なら、条件5は拒否しない。** namespace 内追加では dirty 検査が mask する。token digest と現在値の比較を除去し、現在値同士の前後一致は残す変異にする。後段にも token digest との比較を重複配置した場合は、単独変異の証拠から外す。 |
| **m8：test 側で search 拒否を外す** | 変異対象が曖昧。test の assertion を削るだけなら、負例が失敗する保証はない。`clean_scan_digest` 内の既存 `_assert_search_pass(report)` 呼出し除去など、実効箇所を明記する。陽性対照・allowlist・列挙一致を正常にし、合成 hit だけが拒否理由になる入力を使う。 |

m6・m7 とも、「同じ種類の比較だから冗長」ではありません。**どのフィールドを壊し、どの位置を変異させるか**で判断すべきです。DW-M04 に従い、実装後の一意な置換位置と注入 diff を確認するまでは成立を宣言できません。

## brief と plan の食い違い

**A-7 — nit／brief：実測の射程と一般化を分ける必要がある。**

- **「G は除外内で hit を増やさない」**は、v1 prefix 除外の走査について正しい説明です。v2 は prefix を無効化し、検証済み active-chain の exact record だけを免除します。任意の世代文書に一般化できません。
- **「A/X 前は必ず拒否」**は oracle admission と receipt を分ける必要があります。`verify_receipt` は `never-issued` なら走査前に返り、clean な未発効木の層2も通り得ます。正確には「未発効＋hit は委譲されず拒否」「v2 oracle は active loader／launch が成立しなければ拒否」です。
- **「初回は静的解決」**は誤りです。実 `verify_receipt` は live scan を含みます。この点の plan の訂正は正しいです。
- **407秒**は receipt 解決全体の記録であり、scan 単体時間ではありません。
- G wave の **45 failed／967 passed** は指定6 fileの焦点走です。受入全走の実測値ではありません。また29 nodeは clean 木との対照走なしという留保を残す必要があります。
- scratch の `229982652` は X2 を含みません。その木の緑だけで X1′＋X2＋G の将来 land 集合を実証したことにはできません。

**放置時の成果物影響：これらの文言だけによる受理集合の変更は示せませんが、未実証の land 集合や admission 条件を実証済みと報告するおそれがあります。**

test の削除集合については、plan の方が brief より明確です。

- official namespace 全体と候補 **exact file** を先に宣言している。
- 候補 directory 内の無関係ファイルを残す。
- copy の差分集合、clone の削除 commit、残存 bytes／OID を検査する。
- hit 結果に合わせた S の拡大を認めていない。

この形なら、「赤になった path だけを消す」操作とは区別できます。ただし、切り離した clone は研究上の official clean な木の証拠ではなく、test 入力です。

`_holdout_hit_text` は現行 `HOLDOUTS` と `concrete_axis_encodings` から各軸の文字列を同じファイルへ作ります。現行 scanner の conjunction はファイル単位なので、設計上は hit します。しかし rr50 の陽性対照だけでは、この合成 holdout bytes が hit した証明にはなりません。負例では実 report の `conjunction_hits` に投入 path が載ることを確認し、そのうえで `clean_scan_digest` が拒否することを要求すべきです。単なる任意例外の期待では、allowlist 不備や陽性対照欠落による偽の成功を排除できません。

## 総括

**現 plan のままの採用は不可です。主要な must-fix は、保持 report の鮮度と変異の単一理由性です。**

report の保持・凍結文書との束縛は意味的に妥当で、現物の exact 免除は v1 の既存除外内に収まります。一方、名前集合・HEAD・世代の一致だけでは、report 取得後の内容変更を捉えられません。

P3' の解決1回化を推奨します。campaign-start 前の再解決を含めて既存の2回契約を維持できます。adapter の委譲追加は現行 caller から到達せず、今回の必要差分から外せます。

S を固定した test 切り離しは妥当です。draft と official clean scan の実 hit 拒否をそれぞれ残し、実際の拒否理由と変異の受理変化を確認してから land 判定へ進めるべきです。