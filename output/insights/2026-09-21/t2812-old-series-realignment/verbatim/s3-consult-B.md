## must-fix

以下、`brief`＝[brief-s1.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2812-old-series-realignment/brief-s1.md)、`plan`＝[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2812-old-series-realignment/codex/s2-plan.md)。静的検査のみ。probe は親の記録を照合し、再実行していない。

1. **real — B-4 の既定継続を不要な裁定へ返している。**
   `plan:211` の「f1をOで完了／新mainへ移転」は削るべき。前者は依頼の固定 checkout 継続そのもので、後者は同 plan:148–160 が成立しないと説明している。D2184、依頼逐語 `verbatim/origin.md:9`、probe `B4-W1-HEAD` に従い、親が **O継続を確定事項として扱えばよい**。新 pin の新 campaign は並行・後続で可能なので、O継続とNも排他的ではない。人間には必要が生じた新実験の条件だけを返す。

2. **real — S' の「W-5まで閉じた実装申し送り」には旧 binary 配置経路が不足。**
   `plan:177,188` は配置を「別途設計」「所定storeへ揃える」と残している。一方、probe `READONLY` は対象新 checkout の binary store 不在を記録し、`s8b_floor_campaign.py:5825` の配置入口は現行 policy を要求する。消費側は `s8b_oracle_driver.py:1043` で実体を必須にする。
   **既存12 binaryの取得元、対象root、配置に使う既存経路、manifestのhashとの照合、欠落時の扱い**を設計に追加する必要がある。新しい配置機構を作る必要があるとは断定しない。段階4だけの修復としては成立候補だが、W-5解決の閉包としては未了。

3. **real — B-4「床値」と「本走」の依存関係が欠落。**
   `plan:134–162,206–234` には D2194項3の base driver 修復が登場しない。同裁定は carrier実装・定義発効を**新規base campaignの起動前**に置き、callerのlock読取り修復も要求する（`docs/decisions.md:69714`）。床値O継続やN整合だけでB-4本走が動くような提示は不可。
   別waveの着地を依存として明記し、このwaveでは carrier・callerを重複実装しない。固定f1 submit-treeへ修復を移植する必要もない。

4. **refuted — S' は policy照合除去・曖昧fallback・receipt張替え・live `None` と同じ、という批判。**
   これら4つとは違う。**検証済みprotocolからpinを取り、現行registryで期待policyを再構築し、exact型・SHA・source照合とreceipt bytesを保持する**ためである（`plan:108–114`、probe `POLICY-SERIES-PIN`）。

   ただし、**「現行repoの `repo_stock_pin` への依存を切り離す」という効果では、D2184が別裁定へ返した択と実質同じ**。field自体は残るが、live consumerの期待値を決める権威が変わる。`plan:132` はこの点を明示しており、隠れた既裁定違反ではない。無裁定実装は不可。

## should

- **費用表を裁定資料へ追加する。** `plan:124,162,213` は単発所要を示すが、spec数・job数・wave数・人間手番の比較がない。特にB-4は3 specであり、69〜77分を全体費用にしてはいけない。下表参照。
- **scope外の拡張を候補の説明から実施予定へ昇格させない。** S'の他系列への展開、Nの汎用世代対応、A-1の第三study枠組みは今回実装しない。`plan:108` の共通policy構築変更も、任意pinを全consumerから渡せる汎用APIへ広げず、名指しした2入口の必要範囲に限定する。
- **A-1のNには既裁定改訂費用を追加する。** `plan:72,74` の「新study／登録」だけでは足りない。D2172項2は別study案について、D2096項5の「3 study目の枠組みは作らない」の改訂が必要と明記している（`docs/decisions.md:68543`付近）。一方、0003の再裁定要求はD2178の明文なので、不要な差戻しではない。
- **並走後に変わる事実を区別する。** 候補削除後はscan hitとheld期待値、pair修復後は認可所有範囲とstock到達、closure前進後は新lockのidentityが変わり得る。`plan:222,224` は各waveの所有事項への参照とし、同じ作業を二重に割り当てない。
- **受入への影響を具体化する。** `plan:228` の実測対象に加え、D2196決定4の `_ACTIVATED_G1_REFUSALS` の追随を名指しする。policy不一致が解けても、候補削除・未承認spec・held checksを一括してgreenへ変更しない。

新規gate・台帳・一般化機構を今回追加する明示的な指示は認めなかった。既存検査の負例を申し送ること自体はscope逸脱ではない。

## nit

- `brief:29` の「policy epochだけ」は「**段階4の観測された拒否**」に限定する。plan:8,96の訂正を採用する。
- `brief:31` の結論は支持するが、`READMIT-STOCK` は再admission成功の実測ではない。receipt変更による束縛破壊は静的帰結として書く。
- O／H／O'／S'／Nの定義を表の前へ置く。特に「旧系列の継続」と「新pinの別系列」は同時に選べる。

## 既裁定の照合表

| D番号 | 判定 | 根拠・帰結 |
|---|---|---|
| D2150項1 | 整合 | ②③⑤は各新系列着手時。今回設計し実行を別waveに残す形は適合。K2/A-1のHでは⑤不要と理由付きで示している（plan:37,74）。 |
| D2184 | 条件付き整合 | S'はrepo pin依存切離しと実質同じ。別裁定候補として提示する限り適合。旧bytes保持も適合。 |
| D1777 | 整合 | Hのsubmodule切替は既存手順。probe `K2-PIN-H` が境界通過を裏付ける。pair成立の証明ではない。 |
| D2187 | 整合 | 修復→pair再投入→成立後の4巡目。予算再提示は明文で必要（逐語:13–16）。 |
| D2194項2 | 整合 | round 3派生入力を使う方針を保持。pair走を直前巡へ置換しない（plan:39）。 |
| D2194項3 | **欠落** | B-4新規base campaign前のcarrier・定義発効・caller修復が依存表にない。 |
| D2194項4 | 整合 | exact-63旧lockのlive復活や新grammarによる再測定を提案していない。需要時の限定解析checkoutは別扱い。 |
| D2194項5 | 整合 | 候補fileだけの別commit削除、scan除外不変。S'採択待ちに束ねないこと。 |
| D2180 | 整合／Nは未確定 | g1のA/X作成はAIへ委任済み。「人間がcommitする費用」を復活させない。一方、g2採用まで既認可とは読めない。 |
| D926 | 要補記 | Nのofficial再測定は固定official wrapperとnonce束縛を通す。planは迂回を提案していないが経路の明記が不足。 |
| D1641 | 整合 | B-4の既存委任を維持。f1継続を再裁定しない。新系列の全条件まで自動認可されたとはしない。 |
| D2172項2／D2178 | 整合 | 0003は新裁定と定数追加が必要。prior解除集合の確認も必要。 |
| D2196 | 整合 | O'のT-2810修復移植は既裁定修復。policy照合やscan除外の緩和には使えない。 |

`repo_stock_pin`、固定checkout、批准、exact-63、base driver、attempt-0003等で後続Dも検索した。D2194項6はA-1の**2 attemptの観察記述**を認めるが、0003認可や統計的再現判定は与えていない（`docs/decisions.md:69764`）。

P1〜P5への判断は以下。

- **P1：限定付き支持。** pin整合追加は不要だが、pair修復・再投入とstock admissionは未了。
- **P2：補正して支持。** admission preimage差は1 field。campaign全体の同一性や0003認可までは示さない。
- **P3：設計候補として支持。** SHA到達可能性は実測済み、live型・store・後段成功は未確認。
- **P4：f1継続は支持。** 新main系列とB-4本走の依存を追加する。
- **P5：支持。** class問題ではなく、再発行receiptが旧凍結のSHA束縛を変える問題。

## 費用と順序

実測値は旧条件での参考値。以下のwave数は依存工程からの見積りで、計算資源の認可上限ではない。

| 択／対象 | 計算費用の根拠 | wave・人間手番 | 動かせる研究と順序 |
|---|---|---|---|
| g1 S' | 床値再build・再測定は設計上不要。W-5費用は別 | 整合実装1 wave以上。受理集合裁定、W-4承認・W-5予算は別 | S'＋独立した候補削除→launch確認→承認spec・store・環境等→W-5→certified選択 |
| g1 O' | 床値再測定不要。移植・受入費用は未見積り | 移植検証1 wave以上。採る修復閉包を確定 | S'と同じ研究へ進む候補。ただし現行検査と同等と主張するならplan:121の追加移植が必要 |
| g1 N | 12 cell build 438秒、96 session約4284秒、job全体4769秒＝約1.325 node-hour | 世代契約実装、測定、再凍結・発効の複数工程。新系列採用とg2契約・予算の裁定が必要 | successor **commit**→build・official→新凍結・批准→W-4→W-5。g1そのものの再開ではない |
| K2 H | 旧pair失敗jobは74秒、候補build15秒。stock未到達なのでpair完走時間へ外挿不可 | D2187修復wave→予算再提示→pair 1 job→成立後4巡目1 job | D2194項2の派生入力を使う4巡目。旧lock復活不要 |
| A-1 H | 0002の3 job elapsed合計2218.79秒＝約0.616 node-hour。CPU合計約7.58時間 | 0003の目的・prior解除・予算裁定→認可実装→新attempt | 次attempt。既存2 attemptの記述更新はこれを待たない |
| B-4 f1 O | w1の3 jobは4182＋4145＋4607秒＝**約3.593 node-hour**。w2同規模なら参考量は同程度 | 新たな経路裁定不要。w2 3 job、finalize 3 job。finalize実測費用は未確認 | 09-29以降の登録窓でw2→同HEADでfinalize。B-4本走には別途carrier等と既存事前登録順序が必要 |
| B-4 N | 少なくとも新build・登録。現在と同じ3 spec×2窓なら測定参考量約7.19 node-hour＋finalize等 | successor・新record/spec・凍結の準備、測定工程。必要時に具体化 | 新系列の床値。既存f1を待たせる理由にはならない |

費用根拠：

- official：[T-2698 README:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2812-old-series-realignment/output/insights/2026-09-16/t2698-official-floor-resubmit/README.md:27)、同:62。
- B-4：[w1 README:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2812-old-series-realignment/output/insights/2026-09-19/t2288-floor-pair-w1/README.md:111)。3 node並走の実績とnode-hour合計を区別する。
- K2：[pair README:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2812-old-series-realignment/output/insights/2026-09-20/t2795-k2-pair-attempt/README.md:52)。
- A-1：[attempt-0002 README:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2812-old-series-realignment/output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/README.md:22)。

planのNの約79.5分は根拠と一致する。ただし予約10時間、queue待ち、失敗時の費用、g2実装、再凍結・批准、W-4/W-5を含まない。S'推奨の費用上の根拠は妥当だが、総所要の比較はまだ完成していない。

## 総括

**real must-fixは3件：B-4の不要な再裁定、S'のstore配置経路未了、B-4本走への別wave依存欠落。**

S'はD2184のrepo pin依存切離しと実質同じであり、別裁定候補として扱うplanの方針は妥当。推奨は維持できるが、採択直後に実装waveが着手できる裁定パッケージとしては、上記の閉包と費用・順序表を補う必要がある。