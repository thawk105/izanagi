## 所見 1: capture だけを緩めても、指定された起動テストは赤にならない

**判定: real。plan の変異と期待失敗 node の対応が誤っている。**

**根拠:** [s2-plan.md:333](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-source-bound-emitters/s2-plan.md:333) は、新 11 本の capture 内の disk／HEAD 比較を省略すると、admission の drift テストと `test_loader_drift_rejected_before_campaign_lock_or_wal_bytes` が落ちるとしている。

しかし `orchestrator/campaign/ident.py:283` は capture の直後に `verify_live_contract_loader_binding` を呼ぶ。同 `contract_loader_binding.py:551` の比較が残るため、後者の起動テストは引き続き同じ path の `contract-loader-drift` を受け取る。`orchestrator/tests/test_t671_source_binding.py:627` の例外・reason・path の期待が満たされ、**静的には緑のままになる**。

一方、certified admission は `artifact_admission.py:1201` の capture だけなので、合成 root を使う新 admission テストはこの変異を検出できる。

**親 brief / plan のどちらの欠陥か:** plan。

**直し方:** capture だけの変異の kill 対象から起動テストを外す。起動テストは、後段の live 検証が拒否を維持する対照例として扱う。

## 所見 2: 「exact-85 corpus 0 本」は走査結果を越えた断定

**判定: real。確認できたのは、条件付き走査での未発見である。**

**根拠:** [measured-facts.md:51](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-source-bound-emitters/measured-facts.md:51) の対象は、二つの root 配下、指定 directory を除外し、mtime が 2026-09-20 21:55 JST 以降の `campaign.lock` に限られる。同 `:62` の「着手時点で 0 本」は、この条件からは導けない。

具体的には、除外された `external`／`.cache` 配下、対象 root 外、mtime を古い値で保存・設定したコピーを数えない。なお、コピーが mtime を保存するだけで必ず漏れるのではなく、**保存された値が閾値より古い場合**に漏れる。走査も 08:31〜08:45 の区間であり、全域の同一時点 snapshot ではない。

**親 brief / plan のどちらの欠陥か:** 親 measured-facts と brief。plan も「corpus は 0 本」と継承している。

**直し方:** 「記載した root・除外・mtime 条件の走査では exact-85 を確認できなかった」に訂正する。受入前の再走査も、実際の走査条件と観測時刻付きで報告する。

## 所見 3: P2 は実在記録の認証ではなく、合成 exact-85 も読める grammar 追加

**判定: real。ただし certified への昇格は壊せなかった。**

**根拠:** `campaign_lock.py:629` の先例 validator は wire、field、hash の形を検査する。`contract_loader_binding.py:577` は指定 commit の指定 path の blob digest を照合するが、**その commit の宣言 tuple が exact-85 だったことや、当時この lock が発行されたことは検査しない**。

したがって P2 後は、既存 commit の 85 path の正しい digest を集めた合成 lock も、他の必要条件を満たせば歴史 epoch API で読める。plan の歴史 fixture 自体も、現行 fixture を旧 map に書き換える方式である（`s2-plan.md:185`、`test_artifact_admission.py:3470`）。

受理集合の比較対象にも注意が要る。

- **96 化して85を収載しない案との比較:** exact-85 の HISTORICAL_RAW 受理が増える。
- **現在の85版との比較:** exact-85 は既に歴史入口の現行ラップ経路で読めるため、その読取能力を維持する変更である。

歴史結果は `layer3_report.py:971` の admission decision 等へ流れるが、同 `:978` に現行適合、`:982` に `certifying_input=False` が付く。`artifact_admission.py:1194` と `:1641` は歴史 epoch／view の certified 使用を拒否する。

また、[brief.md:45](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-source-bound-emitters/brief.md:45) の「無条件」という解釈は逐語から一意ではない。D2194 は「同 commit」で **D2193 を参照**し、D2193 は corpus 条件を明記している（`rulings-verbatim.md:156,220`）。将来生成可能という説明は corpus 確認の代替証拠にはならない。

**親 brief / plan のどちらの欠陥か:** 主に親 P2 の根拠・開示。plan は未充足を認めているが、合成入力にも及ぶ読取範囲を説明していない。

**直し方:** 「記録 blob 整合性を検査するが、発行時点・実在 corpus を認証しない」と限界に記載する。P2 の採用根拠は corpus 条件充足と混同せず、本件の指示解釈として記録する。

## 所見 4: 発行器の収載は、すべての成果物書出しに新しい検査を掛けるわけではない

**判定: real。束縛の説明に経路別の限界が不足している。**

**根拠:** capture は現行 tuple 全体を走査するので、96 化すれば6発行器すべてに効く（`contract_loader_binding.py:523`）。ただし実行されるのは、例えば新規 certified lock 作成の `ident.py:584`、certified admission の `artifact_admission.py:1201` である。

確認した6本の入口は次のとおり。

| 発行器 | 確認した経路 |
|---|---|
| `s8b_oracle_report` | `:556` で通常 decoder＋certified epoch gate。拒否は `:576` 以降で `certified_eligible=False` の診断へ投影 |
| `autonomous_trial_completeness` | `:4436`、`:4980` で certified admission。失敗 campaign の分岐 `:4931` は拒否を期待して処理を続ける |
| `backoff_extended_sweep` | `:936`、`:1027` で certified view を取得して report 材料を読む |
| `backoff_extended_sweep_report` | `:464` で certified view を取得し、`:727` 以降で書出す |
| `backoff_overthrottle` | `:182` で certified reference を取得 |
| `b10_backoff_shape_sweep` | report 分岐 `:4350` は歴史 exact-24 と記録 blob を検査し、`:4381` で書出す。現行96の capture は通らない |

最後の B10 経路では、**今回の収載による追加の検査は掛からない**。ただし「何も束縛されていない」は誤りで、既存の `_load_current_analysis_identity` が repository の clean と解析 module の disk／HEAD 一致を別途要求している（[b10_backoff_shape_sweep.py:635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-source-bound-emitters/orchestrator/campaign/b10_backoff_shape_sweep.py:635)）。

**親 brief / plan のどちらの欠陥か:** 親 brief 冒頭の穴を「塞ぐ」という説明と、plan の保証限界の記載不足。

**直し方:** insight の「言えないこと」に、B10 report は収載による追加 capture を通らないこと、拒否診断の出力自体は止めないことを記載する。既存の独自束縛とは区別する。

## 所見 5: exact-85 が現行ラップ経由で certified に入る経路は壊せなかった

**判定: refuted。plan どおりの変更なら、指定された境界に抜けを見つけられなかった。**

**根拠:**

- `campaign_lock.py:840` は、入力の wire key 列と**現行 tuple 全体の sorted 列**を比較する。85 が宣言順 prefix でも、96要素の列とは等しくない。
- `_historical_decoded_from_current` は通常型から歴史型への変換であり、逆変換ではない（`:798`）。
- `_validate_authority` は現行の完全な key 集合を要求する（`:492`）。
- purpose は decode 前に exact enum として検証され、certified は通常 decoder へ進む（`artifact_admission.py:1037`）。
- plan は歴史 authority 白名単、scope／map 対応、記録 blob 検証、epoch の4分岐を追加対象として挙げている（`s2-plan.md:147`）。
- 仮に epoch 分岐を追加し忘れると、85 map と現行96 map の不一致が `_RecordedCampaignVerifierEpoch` の `:330` で拒否される。記録 blob 分岐を忘れても、現行 binding の exact-key 検査で拒否される。

**親 brief / plan のどちらの欠陥か:** 該当なし。実装前なので、計画の静的評価に限る。

**直し方:** 現行の入口分離を維持する。歴史正例と通常 decoder 拒否を別 node で検査する現 plan を保持する。

## 所見 6: 5 grammar の識別は曖昧でないが、「末尾」の意味を混ぜてはいけない

**判定: refuted。識別の衝突は壊せなかった。**

**根拠:** AST から現行 literal を抽出し、`closure-head.json.proposed` と静的照合した。件数は96／85／63／62／24、提案96は既存85＋指定11と全順序で一致した。

- 宣言順の96から追加11本を落とすと既知85になる。
- 96から1本落とすと95で、既知 grammar はない。
- **sorted wire の先頭85本は、既知85とは一致しない。** 追加 path は wire 上では途中にも入る。

旧 grammar は `campaign_lock.py:640` 型の ordered wire 比較で subset／superset／同数別集合／順序違いを拒否する。dispatcher の最後の `else` も exact-24 validator であり、任意 grammar の受け皿ではない（`:858`）。通常96の順序違いは、authority の集合検査を通っても outer canonical 検査 `:774` で拒否される。

**親 brief / plan のどちらの欠陥か:** 本質的欠陥なし。

**直し方:** 「末尾11本削除」は宣言順または追加 path 集合の削除と明記する。この入力は未知 grammar の負例ではなく、歴史85の正例／certified 拒否例として扱う。

## 所見 7: 既存の未知 grammar 負例は維持される。ただし同数・順序違いの拒否理由は別

**判定: refuted。棚卸し対象に、収載後に既知となる既存入力は見つからなかった。**

**根拠:** `test_campaign_lock_codec.py:315,676,790` と `test_artifact_admission.py:2195,3362,3529` を照合した。

- exact-63 の subset は `env_contract.py` を落とすため、**62本だが既知62とは別集合**。
- exact-62＋`unknown_t2483.py` は63本だが、既知63とは別集合。
- exact-63 の末尾 `verify_fanout_worker.py` を落とすと既知62になるが、現 test はその削除を使っていない。
- 現行 minus-one は前進後95で、既知85にはならない。
- 96から追加11本を削除する例は既知85になるが、plan の未知負例には登録されていない。

順序違いは「未知の path 集合」ではない。歴史 decoder では wire grammar 拒否、通常 decoder では canonical JSON 拒否になり得る。admission の `match="codec validation failed"` だけでは両者を区別できないが、plan の兄弟 validator 直接呼出しがこの混同を補っている（`s2-plan.md:224,340`）。

**親 brief / plan のどちらの欠陥か:** 棚卸しの結論に欠陥なし。拒否理由の説明には区別が必要。

**直し方:** 既知全5列との比較と validator 直接負例を維持する。順序違いは集合未知性ではなく wire 順序検査として説明する。

## 所見 8: 歴史85と現行96の固定 epoch は区別できる

**判定: refuted。同一固定値によって両テストが区別不能になる懸念は成立しない。**

**根拠:** production module を import せず、宣言 literal と標準ライブラリだけで再計算した。

| grammar | 合成 epoch | 順序付き path hash |
|---|---|---|
| 歴史85 | `E1:bc8a6c8c…423dc7` | `bea36246…6b5a1` |
| 現行96 | `E1:244d998f…da07a` | `5c2c4a6a…683af4` |

親・plan の固定値と一致する。歴史85が同一になる相手は**変更前の現行85テスト**であり、変更後の現行96テストではない（`s2-plan.md:189`）。

`test_artifact_admission.py:858` の fixture は宣言位置で bytes を作るため、append なら旧85本の bytes と順序は保持される。現行 epoch を85本に切り詰める変異は96固定値との比較で落ち、歴史側だけ sorted にする変異は85固定値との比較で落ちる。

一方、scope は hash preimage 外なので、**epoch だけでは scope の破壊は検出できない**。plan は型・凍結 scope の独立比較を要求しており、この点も補っている。

**親 brief / plan のどちらの欠陥か:** 欠陥なし。ただし brief の「現行 test」は時点が曖昧。

**直し方:** 「変更前の現行85固定値」と明記する。型・scope・path 対応の検査を epoch 比較で代替しない。

## 所見 9: 変異による赤の帰属は、brief の記述だけでは成立しない

**判定: real は brief の粗い変異指定。plan の選択 node が必ず drift で汚染される、という懸念は refuted。**

**根拠:** [brief.md:58](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-source-bound-emitters/brief.md:58) の「通常 decoder に sorted(85) を union」だけでは、`campaign_lock.py:498` が96 path を取り出す際に不足 path の `KeyError` になる。これは正常な旧85受理を作った変異ではなく、certified 隔離の検出力を示さない。plan `:349` はこの変異を明示的に除外しており、改善されている。

また、`campaign_lock.py`／`artifact_admission.py` の disk 変異と実 root の certified capture を組み合わせれば、`contract_loader_binding.py:527` が狙った関門より前に drift を拒否する。F741／F923 はこの実例である（`docs/failures.md:21720,25402`）。baseline が committed でも、後から注入した変異は dirty になる。

ただし plan の指定 node は一律にこの問題を持たない。

- codec／literal 比較は live capture を使わない。
- 現行固定 epoch の node は `_REPO_ROOT` を合成 committed repo に差し替える（`test_artifact_admission.py:1680`）。
- 歴史正例の先例も同様で、歴史読取では live capture しない（`:3468`、`artifact_admission.py:1192`）。

したがって、これらを静的根拠なく「drift による偽 kill」と断定することも誤りである。

**親 brief / plan のどちらの欠陥か:** 主に brief。plan の到達条件は妥当だが、所見1の期待 node は訂正が必要。

**直し方:** 変異ごとに変更箇所・対象 node・binding root・期待失敗箇所を具体化する。import／fixture／drift の赤を目的の kill に数えず、広い runner の赤を期待集合へ足さない。

## 所見 10: 11本の集合計算は整合するが、173／77は probe 条件付きの値

**判定: refuted。plan が別規則で数え直した形跡はない。ただし本相談で173を独立再測定したわけではない。**

**根拠:** `measured-facts.md:3` は既存 probe の `ast.walk` と package 初期化を使ったことを明記し、plan はその数値を引用している。今回の静的照合では、次を確認した。

- `new_members_sorted` は発行器6本と producer-only 10本の和に一致。
- 重複5本なので追加11本。
- 既存85＋追加11の順序が提案96と一致。
- 追加11本と次段23本の重複なし。
- 記録された発見集合173を前提にすれば、未収載は77。

ただし `closure-head.json` は測定結果であり、173の探索全体を独立に証明する資料ではない。関数内 import を落とす top-level-only 探索や package 初期化を省く探索で、その数値を再現したと称してはいけない。

**親 brief / plan のどちらの欠陥か:** 規則変更の欠陥は見つからない。独立確認できた範囲と親実測への依存を分ける必要がある。

**直し方:** insight に probe の規則と測定 commit を残す。集合・順序の再検算と、import 発見集合の再測定を別の証拠として記載する。

## 総括

最大の risk は、条件付きの未発見を「corpus 0」と断定し、それを P2 の裁定解釈・歴史的真正性の説明へ持ち込むことである。
certified への旧85流入と5 grammar の識別は、plan どおりなら静的には壊せなかった。
具体的な修正点は、capture 変異の期待 node と、発行器書出し経路の保証限界である。
本回答は静的検査と literal／hash の再計算のみ。pytest・変異実走・ファイル変更は行っていない。