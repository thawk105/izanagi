## レンズ A

### must-fix

**A1 — P1 は「再利用候補あり」の推定であり、warm/cold の実績分類にはならない。**

根拠: `parent-prelim-receipt_chain_classify.py:107–161`、`check_ai_provenance.py:2451–2464, 2516–2646`。

| 条件 | 親分類が外れる具体例 |
|---|---|
| 並走 | B の lookup 後、B の publish 前に A が publish。A.mtime < B.mtime でも B は A を読めず、推定 warm／実際 cold。 |
| selection / delta | bindings が一致しても、`commits ∩ ancestors(tip)` の digest/count、または `tip..head` と差分集合が不一致なら cold。 |
| correction | prefix 検査に成功しても、選ばれた delta の message に raw `AI-Agent-Correction` candidate があれば全史へ戻る。 |
| registry | manifest 一致だけでは、prefix に対応する `eligible`、coverage の eligible/matched、known_violations の集合・件数の整合を検証したことにならない。 |
| 読取・形式 | directory 0700、regular file 0600、非 symlink、schema/rc、records の型・参照先などを親 script は検査していない。 |
| prune | 当時利用した受領証が後から消えると推定 cold／実際 warm。lookup 前に候補が淘汰されれば実際 cold。現在の残存集合だけでは履歴を復元できない。 |
| 同 tip 上書き | `os.replace` で前回分が消え、最新 mtime だけ残る。同 tip 再走の warm を cold と推定したり、別走の時刻へ対応付けたりする。 |
| 実行時失敗 | bindings 計算・候補読取等が当時だけ失敗して cold になっても、事後 replay は成功し得る。 |

mtime は厳密には publish 時刻でもない。temporary file を書いてから `os.replace` するため、mtime は可視化より前になる（2490–2498）。

**影響:** 「45 監査 = cold 2 + warm 43」「他 binding cold 0」という実績表は成立しない。

**是正案:** 「残存受領証45件について、候補あり43件／候補なし2件」と出発点を訂正する。offline replay は以下まで行う。

- 比較対象は候補 A と対象 B。A.bindings と B.bindings の一致を先に確認し、B の選択集合・祖先閉包と当時の registry を使う。A 自身の bindings を無条件に渡して一致検査を自明にしない。
- `_receipt_prefix` で selection、delta、coverage、records を検査する。registry は保存 manifest に対応する内容を復元できなければ未判定。
- **raw correction の判定は `_receipt_prefix` の外側**なので、2634–2646 相当も別途再現する。
- 実装と同じ距離・filename 順で候補を選ぶ。任意の成功 pair があるだけでは実際の選択を再現しない。

これで静的な (ii)〜(iv) は条件付きで閉じるが、(i)(v)(vi) は閉じない。候補の publish 完了が対象走開始より前だった証拠、当時の候補 bytes・存在履歴、走の識別がなければ「再利用可能性の事後推定」と明記する。短い wall は補助情報に留める。

---

**A2 — cold の tip と81秒の分類が、生出力と直接矛盾している。**

根拠: `parent-prelim-receipts-classified.txt` の次の行、`parent-prelim-land-accept-wall.txt` の00:15:49行。

| partition | tip | 受領証時刻 | 親 script の分類 |
|---|---|---|---|
| c508d1de93e1 | 65966f4d8a92 | 23:45:43 | checker変更 cold |
| 4608b761416c | 65966f4d8a92 | 00:08:30 | partition跨ぎ cold |
| 4608b761416c | c383bac070f7 | 00:17:10 | **warm推定、Δ=9** |

**影響:** 「land 初回 cold 81秒」と、それを基にした「partition統一で30〜55秒削減」が崩れる。

**是正案:** land 側の候補なし初回は `65966f4d8a92` に訂正する。81秒は、対応付けが成立するなら **warm推定走の開始→mtime間隔**。同じ条件で残す land の間隔は27/40/51/**81**秒、n=4となる。land 初回 cold の wall は別途対応ログが見つかるまで不明とする。

---

**A3 — 原因4種への写像は一対一でなく、旧 checker の26件という説明も誤っている。**

根拠: 分類 script:121–159、生出力23:12:12／23:17:15／23:36:39、D2192「理由」。

`env_diff` に checker があれば最優先する分岐は、分類規約としては使える。しかし比較対象は「他 partition の最新祖先」であり、checker・config・inherited が同時に違う行もある。これは checker 単独の因果同定ではない。近接する一候補との差も、全候補が使えなかった理由そのものではない。

また26件は `7c02fb2d` だけではなく、`65476dafe9c0` の3件を含む。`attributes` digest 差から、実際の `.gitattributes` 変更か旧方式の absent 候補増加かは区別できない。

**影響:** checker変更／partition跨ぎの件数が比較対象と優先規則に依存し、`.gitattributes` 起因の件数を過大に読ませる。

**是正案:** 主分類に加えて「比較相手・差分全項目・複合差・判定不能」を残す。新 directory による旧 attributes fingerprint 失効は、厳密には `.gitattributes` 変更でも「attributes以外」でもなく、指定4種に入らない参考区分にする。旧期26件の詳細な再調査は参考説明に留められるが、依頼の母集団は**着地時期**であり現行 checker だけではない。着地後に旧 checker で受入・land した wave は除外せず扱う。

---

**A4 — wall の突合が監査単位を保証せず、「監査 wall 上限」とも断定できない。**

根拠: wall script:37–55, 87, 110–139、`dev_wave_wait.py:3789–3804, 3874–3895`、`dev_wave_land.py:3559–3576, 5698–5705`。

- `match_receipt` は終了時刻で制限せず、partition_hint も呼出側から渡していない。
- 実際に04:54:42の land は **1秒でrc=23**なのに、その後の受入 partition の受領証へ結び、206秒と出している。22:33:41も173秒で終了した走に373秒を結んでいる。
- 04:40:27と04:40:32は同じ merge tip `088bbdec71e4` の同じ受領証を使う。23秒を claim前監査、18秒を別の merge後監査の実測として数える根拠はない。02:28の21秒／17秒も同型。
- 現行受入コードは claim前に監査し、merge commit を作成した後に再監査する。D2045当時の「同じHEAD」という説明を現行経路へ流用できない。
- `attempt`／`merged`／`it=N land` は提示コード内の計測点ではない。外側 launcher の出力位置を確認しない限り「監査直前」「起動時刻」は未証明。
- mtime は checker 終了前。開始前の処理を含む一方、publish後の処理を含まないため、checker全体 wall の厳密な上限ではない。

**影響:** n、claim前／merge後の内訳、warmの範囲、480秒との比較が変わる。

**是正案:** wave・attempt・stage・監査時HEAD・partition・開始終了区間で突合する。区間外／別partition／後続上書きは未対応にする。既存値は「ログ点→対応候補のmtime間隔」と表示し、監査単独時間と分ける。日付をfile mtimeから最大1日前へ戻す方式と、未使用のJST定義も、日跨ぎログの根拠を確認して修正する。

---

**A5 — partition の用途帰属と「dispatch 0件」は未証明。**

根拠: `dev_wave_wait.py:651–659`、`dev_wave_land.py:564–580`、checker:2395–2422、dispatch:138–143, 1661–1672, 4014–4027。

受入は単純な全環境継承ではなく、`_GIT_ENV_KEYS` を除去する。land は全 `GIT_*` を除去して上書きするが、`LANG` や他の `LC_*` は残る。したがって現在の親envをそのまま使う(a)は受入相当を保証しない。

dispatch の `inherit` は**計算ノードのjob環境**を継承する意味である。provenance のoverlayは空で、qsub argvにも親環境全体を渡す指定はない。`LC_CTYPE=C.UTF-8` だけの状態は計算ノード固有の識別子にはならない。

**影響:** 「現行checkerで計算ノードpartitionなし → dispatchは一度もない」という結論と、P4のcold前提が成立しない。

**是正案:** 用途はログで結べた走に限って確定する。launcherの `env -i`、sessionごとのLANG、worktree固有config、bounded local子の環境変化を含め、checker直前の `GIT_* / LC_* / LANG` と `git config --list` の**全文**を受領証と照合する。P4-bではjob ID・hostname・tip・checker hashも結ぶ。その走の帰属は確定できるが、過去の似たpartition全部の帰属までは確定しない。

### should

**A6 — 一晩の残存受領証を、全land監査の母集団へ一般化しない。**

根拠: brief「前提実測」、D2192「保証しないこと」、checker:2467–2502。

**影響:** 成功して保存されたtipだけの偏りを、cold率や全waveの安定性として結論付けてしまう。

**是正案:** 09-20 23:41〜09-21 05:22、残存45件、partition別34/11件、ログ対応件数、loadが付く行の範囲を別記する。対話直打ち、失敗・未publish、同tip複数走、未対応waveを区別する。load1 1.4〜4.7は受入gateの観測であり、全監査中の負荷ではない。

「cold率2/45」「時間短縮率」「混雑時も480秒以内」「他binding失効は起きない」は不可。「対象期間の残存受領証には再利用可能な祖先候補が多数ある」が現段階の結論。

## レンズ B

### must-fix

**B1 — P4-bはdispatch本体の対照になるが、混雑時・landの480秒関門をそのまま再現しない。**

根拠: checker:3676–3689, 2938–2975、land:3559–3576、dispatch:68、DW-O25。

`--force-dispatch` と `headroom_short + queue可` は同じ `_invoke_dispatch` を呼ぶ。この点は妥当。ただしforceはadmissionとqueue可否判定を迂回する。さらに直接呼出しには、landが設定する外側480秒deadlineがない。dispatch既定walltimeは1時間であり、queue待ち込みのland関門とは別物。

**影響:** 「同じ関数を通った」「計算ノード実行が480秒未満」から、本番混雑時のland成功を誤って確定する。

**是正案:** bの目的を「dispatch先partitionと、その条件でのcold/warm対照」に限定する。480秒適合も評価するなら、land相当envと既存の外側deadline契約をlauncherで再現し、親の全経過時間、queue待ち、計算ノードのchecker時間、終了・cleanupを分けて記録する。rc=16はcold監査結果ではなく、dispatch不成立として別記する。

---

**B2 — P4の走数より、cold/warmの成立条件と実行場所を修正する必要がある。**

根拠: brief P4／段構成、checker:2386–2646、dispatch:907–918, 1128–1132, 1842–1847、および提示AGENTS.mdの性能測定規律。

**影響:** 予定の「cold→warm」が実際にはwarm→warm／別partitionのcold→coldとなり、対照も本番性も失う。

**是正案:**

- (a)は性能測定目的の3走であり、提示規律ではloginで実施できない。計算ノードでの対照へ変更するか、通常監査の既存ログを使いlogin値は未測定と残す。checkerのbounded local許可だけで性能測定規律を満たしたことにはならない。
- 新 `GIT_*` によるcoldは人工的なpartition missの対照。実際の残存cold原因を増やした実績には数えない。冷却前に既存一致partitionがないこと、Git動作を変えない変数であることを確認する。
- bの初回は事前storeだけで保証しない。実際のjob env/configからpartitionを求め、有効な祖先候補の有無を確認する。2回目は同じtip・全bindings・利用可能な初回受領証が必要。同一nodeは必要条件でも十分条件でもない。
- `--force-dispatch` を2回呼ぶ計画なら、通常は**2 request／2 job**。briefの「計算ノード1 job」と統一する。1 job内で2回checkerを動かすと、2回目のdispatch・queue経路は測れない。
- 同一worktreeでは前jobの終了・ledger/cleanup確定後に次を開始し、途中でHEAD/index/checkerを変えない。request ledgerを手で消したり、`_JOB_SESSION_SWEEP_ENV` を自作launcherへ流用したりしない。これはjob終了処理の印で、checker子では除去される。
- 副作用は「数件追加」だけではない。同tip上書き、prune、dispatch記録・request ledgerもある。追加走の前に診断対象の受領証bytes・mtimeを保存する。

最小形は、目的を絞ったbの2走を優先する。aの人工coldはbでcold対照が成立すれば削除可能。受入／landの2env対照は、区画統一の効果を裁定材料に残す場合だけ必要であり、5走してもregistry等の全binding失効や混雑時分布は閉じない。

---

**B3 — 「混雑時＝headroom_short」は撤回が必要。**

根拠: checker:3680–3740、brief P4、D2045の混雑時実測。

メモリ余力があってもCPU・I/Oが混雑する場合がある。逆にメモリ不足でもloadは低くなり得る。queue停止時の再admissionやbounded localのOOM後dispatchも、forceの2走では検証しない。

**影響:** 依頼の「混雑時」を測定済みとする結論が過大になる。

**是正案:** 「dispatch経路の強制実行を観測。現行checkerの自然なlogin混雑時は未観測」と残す。負荷を人工生成する必要はない。旧42〜126秒はA4に従って再点検し、旧checker・別時期・異なる計測区間の参考値とする。換算するなら「現行の適切なcold実測値C秒に仮定倍率kを掛ける感度試算」と明記し、7倍は旧資料由来の仮定であって予測・上限ではない。異なる上限値同士の比から現行値を推定しない。

---

**B4 — P3の「主因」と局所修正の効果見積りは現状の証拠では成立しない。**

根拠: A1–A3、brief P3、D2045区画方針、T-2803 insight §11。

**影響:** 未証明の30〜55秒を根拠に、局所修正不要／区画統一不採用を確定してしまう。

**是正案:** 第1案は「観測範囲では§11の3候補を支持する原因を確認できず、追加実装を提案しない」とする。「残るcoldの主因は初回だけ」とは書かない。

区画統一は **裁定パッケージ候補・scope外**。D2045が明示した受入／landの区画分離を見直すため、今回実装しない判断は妥当だが、費用対効果の数値は未確定である。

効果は次の単位で示す。

- 「checker変更1回当たり、救済可能な初回cold回数」。祖先・bindings・時系列が揃う場合に限り、2区画を1区画へ統一すると最大1回を回避できるという条件付きモデル。
- 「救済されたland 1本当たり `C−W` 秒」。同じ実行条件で得たchecker単独時間を使い、81秒と27〜51秒の差は使わない。
- dispatch先coldは、実際に発生・帰属を確認できたら別項目として数える。頻度不明のまま主因には加えない。正常化案の評価には、dispatch先のC/Wと、正常化後に他bindingsも一致する根拠が必要。

「毎landが30〜55秒短縮」「checker変更ごとに必ず1回救える」「区画を統一すればdispatch coldが消える」は不可。

### should

**B5 — P5はauthorの再実行だけで確定値にならない。再実装より、証拠単位の修正を優先する。**

根拠: brief scope／P5、依頼のF75前提、親scriptのA1–A4の欠落。

**影響:** 同じ推定ロジックをauthorが書き直すだけなら、誤分類を「確定値」へ昇格させてしまう。

**是正案:** briefが引用する「実行可能scriptは所在不問で実装面」という前提に従えば、確定probeをauthorが担当する構成は妥当。ただし全面的な独立再実装は不要。親scriptを参考入力として渡し、正解扱いせず、修正・採用範囲を明示させる。親作を「仮説」と呼ぶだけで作者規律を満たしたことにはしない。

authorには、今回の反例、保存入力、対象waveの定義、実装と一致する候補選択、未判定の扱いを渡す。段6 review 1本では少なくとも以下を行単位で照合する。

- 各監査attemptと、未対応・失敗・上書きによる欠測。
- 各受領証のpartition、候補、bindings差、prefix/delta/correction検査結果。
- cold候補全件の原因と複合差、81秒等の訂正行。
- 時間表の開始・終了・tip・partitionとn、裁定案の効果式・出所・限定文。

stdoutの転記一致だけでは不十分。F75本文自体は今回の指定資料に含まれていないため、以上はbriefに引用された規律の範囲での評価である。

### nit

**B6 — 結論を変えない拡張は削れる。**

根拠: origin.mdの診断scope、brief、T-2803 insight §11。

**影響:** 削除しても、対象期間の分類と裁定結論は変わらず、作業量だけ減る。

**是正案:** 全19partitionの詳細履歴表、旧26件全部の原因再構築、主因に結び付かないmemo化／attr.tree／errnoの個別効果実測、人工的なlogin混雑、全bindingの失効実験は不要。旧期は必要な比較行と限界に絞る。主表は監査attemptと証拠の対応、cold候補の説明、追加対照、裁定候補だけでよい。新gate・新台帳は不要。

## 総括

must-fix: A1 推定と実績の分離、A2 cold tip／81秒の訂正、A3 原因写像、A4 時刻突合、A5 partition帰属、B1 deadline、B2 実測条件・場所、B3 混雑の定義、B4 主因・効果見積り。
(a) は提示規律上login性能測定として実施不可。計算ノード対照または既存ログ利用へ変更し、不要な人工coldは削る。
(b) は条件修正後に実施可。2 requestを直列化し、実partition・受領証・deadline・queue時間を確認する。ただし過去のwarm実績と混雑時保証は確定しない。