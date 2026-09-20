必読8ファイルは読めました。以下は静的検査と既存 ledger の集計結果です。ファイル変更・pytest・変異実走は行っていません。

## 所見 1: 85／163／78 を f94b61fc8 の実測として書くのは偽になる

**判定: real。親 brief と plan 両方の欠陥。**

**根拠:** brief P4、plan §2、measured-facts §1、D2081 条件1・2。

f94b61fc8 の実測は **63／163／100**。85／163／78 は、その発見集合に対して提案する85本を収載した場合の集合差であり、同 commit の実測値ではありません。plan の「D2081 の4条件を満たします」は成立しません。

brief の「63 と直接 import 先等22」という括弧も、条件2が落とすよう命じた内訳の再導入です。plan はこの点だけは修正済みです。「推移閉包ではない」という限定、非 import 委譲の括弧、実行時計算・発行器名・凍結成果物を書き換えない方針は妥当です。

**直し方:** 内訳を削除し、例えば次のように測定と本版の集合差を分離する。

> identity: curated exact 85 path; source-import 推移閉包ではない。発見集合は測定commitの収載tupleから静的importとpackage初期化を辿った集合で、2026-09-20（f94b61fc8）の実測は163 module。
> excluded: その固定発見集合と本版の収載tupleとの差集合78 module、および同発見集合に入らないmodule、…

「78」は**本版との集合差**と明記し、既存の非 import 委譲の限定を続ける。

## 所見 2: 22本の段階選択は許容されるが、発行器の穴を閉じたとは言えない

**判定: 段階選択の違反は refuted。P1の理由づけには real な欠陥がある。親 brief の欠陥。**

**根拠:** D1884「段階のどこまでを次の変更単位に含めるかは実装waveが決めてよい」、brief P1、layer1-edges.json、T-2344一次資料「production到達性」「候補集合そのものの欠落」。

22本は再現可能な切り方であり、`analyze.py`／`backoff_hole_grammar.py` の直接依存漏れと、観測された認証受理経路の `materializer_admission.py`／`backoff_hole_grammar.py` を収載します。この段階選択自体は壊せませんでした。

一方、`sort_swo_oracle.py`／`coder_effect_gate.py`、発行器群は残ります。親の producer-universe.json でも、`s8b_oracle_report.py` 等を含む10本はtuple起点集合の外です。22本追加後も、基準snapshot上でtuple起点の未収載78、発行器起点との和では88が残ります。

「発行器追加は候補集合の定義変更だから次段の裁定対象」という説明は不正確です。**発行器起点を含む目標はD1884が既に裁定しています。** また「drift2本だけでは1段と言えない」も、裁定がBFS単位を義務づけていない以上、却下理由として弱い。

**直し方:** 本waveの22本は維持し、「委譲された材料22本の束縛を追加するが、発行器自身の穴は残る」と限定する。
**裁定パッケージ候補:** 発行器6本を先行／同時収載する案は、D1884が名指しした穴にはより直接的。ただし依存先まで閉じる案ではなく、本waveへの追加要求とは分ける。

## 所見 3: 「63 keyが20本」と「exact-63 grammarが20本」は同じ証拠ではない

**判定: real。親 measured-facts §3と、それを無条件に採用したbrief P2／planの証拠不足。**

**根拠:** 親のlock-grammars.json、D1653必須条件、T-2483 insight §2。

親JSONの該当20行が持つ情報は `path`／`keys:63`／`schema` だけです。**key集合・wire順序・記録commitの宣言tupleとの一致を記録していません。** D1653は件数ではなくexact ordered tupleを要求します。T-2483では実lockのwire列hashと歴史tupleの対応まで確認していました。

exact-63実在そのものには、T-1998の63 blob記録とcertified再読の既存資料もあり、収載方針を否定する材料はありません。ただし「20本すべてexact-63」「20本すべてHISTORICAL_RAWで読め続ける」までは件数表から導けません。後者にはactivation、WAL、policy等の条件もあります。

K2 durable rootの欠落は、**実在証明には致命的でないが、影響件数の網羅性には影響する**。20本を全影響集合として扱えません。

**直し方:** 少なくとも代表実lockのexact key列と記録宣言順を照合し、20本という主張には20本分の対応を付す。「探索した19 rootで63 keyを20本確認」と「全体の影響数」を分ける。全面的な新inventory機構は不要。

## 所見 4: exact-63の歴史scopeを旧2定数から凍結する方針は壊せなかった

**判定: refuted。コード方針の欠陥は確認できない。**

**根拠:** plan §2、`artifact_admission.py:76`、D1653「grammar固有のscope」、D2081条件2・4。

現行63文言は、D2081に従って内訳を除いた訂正文です。これを新設のexact-63歴史定数として独立に固定することは妥当です。exact-62が24／36／2の内訳を持つのは、その歴史定数の内容がそうだったためであり、**歴史scope全般に内訳を復活させる義務ではありません。**

ただし「全20成果物の発行当時の文言とbyte一致」とは言えません。exact-63期間中にもD2081の文言訂正が入りました。planが実際に示しているのは「今回の変更直前の2定数との一致」です。

**直し方:** 「exact-63の最終現行scope（D2081訂正後）を凍結」と説明する。既存62／24定数と記録済み成果物は変更しない。

## 所見 5: 「記録commitかHISTORICAL_RAWで足りる」は実在する再解析運用を救わない

**判定: real。最大の運用リスク。親brief／measured-facts §5の欠陥で、plan §6も解決を示していない。**

**根拠:** `campaign_lock.py:402`、`b10_backoff_static_tail_formal.py:393`、`paper_story_a2_certification.py:3300`、`t1998_stock_inline_pair.py:981`。
特に [T-1998再検証記録](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-closure-stage/output/insights/2026-09-15/t1998-landed-main-recheck/README.md) §1・2と、T-2589 insight §1。

tuple前進後の通常decoderが旧63を拒否する説明は正しい。しかし「20本が現在certified受理されていて、その全20本を失う」とまでは親資料は確認していません。

それとは別に、**新しいcheckoutで旧成果物をcertified再解析する実運用は実在します。** T-1998は測定commit `a551cdd3…` のconsumerに欠陥があり、後日の修正 `4d7cd40a9…` で同じ成果物をacceptedにし、さらにmain `0600887d9…` で再現しています。

したがって測定commitへ戻すと修正を失います。HISTORICAL_RAWも `CertifiedCampaignView` の代替にはなりません。修正済みのexact-63 checkoutを保存して使う余地はありますが、それは「記録commitへ戻す」と異なる手順です。A-2のsubmit-tree運用だけを全consumerへ一般化できません。

**直し方:** 本waveでは通常decoder／consumerのpurposeを緩めず、失われる「最新checkoutからのcertified再解析」を明示する。
**裁定パッケージ候補:** 修正済みexact-63解析checkoutの保存で足りるか、最新consumerでの再解析継続を別途扱うかを諮る。D1653／D1770だけで後者まで解決済みとはしない。

## 所見 6: dirty拒否は増えるが、現在のK2本走・受入と衝突する証拠はない

**判定: 本走が新たに止まるという一般論は refuted。開発中の焦点走への影響は real で、planは既に認識している。**

**根拠:** `contract_loader_binding.py:518,535`、`artifact_admission.py:1173`、plan §7、`tools/pegasus/p3_s4_loop_pegasus.sh:237`、`tools/dev_wave_wait.py:2873`。

D1163が許すのは、certified読取りにおける**記録E1とcleanな現在E1の差**です。未commitの収載fileはcaptureで拒否されます。resumeのlive照合も別条件です。

ただしK2 launcherは既にsuperprojectのtracked dirtyを拒否しています。K2第3巡は固定SHAのclean submit-tree、第4巡に先行するpair試行もfresh submit-treeでした（K2 round3 insight「実測」、`docs/worklog.md:2006`）。受入にもclean preflightがあります。これらの正式経路には新しい矛盾を確認できませんでした。

一方、loop／criticの編集直後に実certified admissionを通す焦点testは、新たに赤になります。共有fixtureがHEAD blobでlockを作っても、後続captureはdirty diskを検査します。

**直し方:** 親の実行計画に「実certified consumerを含む焦点走は対象変更をcommitした状態で行う」と明記する。captureをmockして通す共通互換層は追加しない。

## 所見 7: 実装の過剰は見つからず、必要な局所追随も概ね含まれている

**判定: refuted。planを壊せなかった。**

**根拠:** plan §1〜5、`contract_loader_binding.py:577`、`test_s1_9pair_figure_provenance.py:74`、D1653。

3 production fileへの局所変更、独立literal、兄弟validator、既存歴史分岐への追加で足ります。新module、汎用registry、実行時計算、通常decoderの互換unionは入り込んでいません。

`contract_loader_binding.py` の63表記、codecコメント、admission docstring、`CURRENT_E0_EPOCH`、layer3の現行／歴史ラベルもplanにあります。`FROZEN_E0_EPOCH`や日付付きpaper-story記録を変更しない判断も正しい。

兄弟validatorを減らすための共通化は、本waveの差分と影響範囲をむしろ広げます。追加の広範なdocs改訂が完了条件になる証拠も見つかりませんでした。

**直し方:** 実装範囲は維持する。scope文言の訂正を独立test期待値にも反映し、運用上の限定だけ今回のinsight／briefへ追記する。

## 所見 8: 変異の「未収載検出」という名乗りは広すぎる

**判定: real。親brief P5の分類が不正確で、plan §8にも名称が残る。**

**根拠:** brief P5、plan §8、`campaign_lock.py:680`。

tupleから新memberを削除する変異、順序交換、live／captureでの新path skipは、収載追加の回帰検出として妥当です。planは独立literalだけでなく実際の照合まで対象にしており、この部分は壊せませんでした。

しかしsuperset許容や旧63の通常受理は、**未知grammar拒否・認証境界の検査**です。残る未収載78／88 moduleの依存漏れを検出する証拠ではありません。また「歴史63を現行分岐へ送る」変異で落ちるのは、通常decoderの拒否によって失敗する**歴史読取りの正例**です。briefの「拒否testが赤」という一括説明は誤りで、planはここを修正しています。

**直し方:** 「収載追加の回帰」「未知grammar拒否」「certified隔離」「歴史可読性」に主張を分ける。新しい未収載検出機構は追加せず、各変異の対象assertionと失敗段を事前登録する。

## 所見 9: 約3秒は63件だけの見積りで、wave全体の増分ではない

**判定: real。親measured-facts §5の見積りが不完全。63件の削除が必要という主張は refuted。**

**根拠:** `orchestrator/tests/acceptance_duration_ledger.json:371`以降、plan §4・7。

ledgerを静的集計した結果は次のとおりです。

| 対象 | 既存記録からの見積り |
|---|---:|
| exact-62 blob不一致62件 | 合計2.771秒、平均0.0447秒 |
| 同型exact-63を63件追加 | **約2.82 worker秒** |
| T671の既存4系列を63→85へ拡張 | **約21.55 worker秒増** |

さらに通常codecの欠落path検査、新22本のcertified dirty検査、scope／grammar検査、既存fixture処理量の増加があります。したがってwave全体を「約3秒増」と読むことはできません。

ただしこれらはnode時間の合計・外挿であり、受入wallではありません。既存ledger全体は約17,959 worker秒ですが、並列配置、fixture共有、混雑、測定時点が異なるため、ここから5分達成／超過は判定できません。63件だけが5分目標を脅かす根拠もありません。

**直し方:** 約2.82秒を63件固有の見積りと明記し、既知の追加分を別記する。全path照合の検出力は維持し、親の受入実走でwallと実増分を記録する。

探索時に仮定した `docs/dev-wave/{checks,stages}.md`、`docs/dev-wave.md`、`docs/{testing,test-policy}.md` は存在せず未読です。実在するcore／operations／workers、runbook、decisions、insightで検査を続行しました。

## 総括

最大のriskは、旧63成果物のcertified再解析を失う影響を「記録commitか歴史閲覧で解決済み」と扱うことです。T-1998にはそれでは足りない実例があります。
22本の段階実装自体は妥当ですが、発行器の穴は残ります。
scopeの測定時点混同と、63 key件数をexact grammar確認へ一般化した説明は修正が必要です。
本wave内は局所修正を維持し、再解析継続と発行器優先案は裁定パッケージへ分けるのが妥当です。