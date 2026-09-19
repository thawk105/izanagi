## レンズ A

**must-fix A1 — 非 docs 木の一致では、同一 tip・同一条件を満たさない。**

- **根拠:** `s1-brief.md:28`、`s2-plan.md:49,53` に対し、D2148 項6・D357 は同一 tip を要求する。待ち手は `tools/dev_wave_wait.py:3836-3853` で main を取り込む。実際に `test_real_repo_serialization.py:1264-1283` は実 repo の `output/` を前後比較し、その helper `:809-838` は `rglob` と各 entry の `lstat` を行う。したがって insight 増加が走査量を変える経路がある。docs も `test_s8b_oracle_driver.py:245-249` の検査対象であり、履歴には `t080_freeze_migration.py:702-703` の `rev-list --parents` がある。
- **成果物への影響:** 異なる入力・履歴の走を有効対として採用し、その差を pairing に帰属させる。
- **是正:** 投入前 HEAD ではなく、receipt の **tested tip の完全一致**を有効条件にする。さらに、中央値をまとめる全有効対を同じ tip に属する系列に限定する。対内だけ一致しても、対ごとに tip が違えば D357 の同一条件反復にならない。途中で tip が変わった系列は別表に残し、混ぜない。台帳・runner/xdist・実行条件、未追跡の実 repo 入力の変化も記録する。上限内に同一 tip の3対を得られなければ「反復不足」で終える。docs/output の検査除外で解決してはいけない。

**must-fix A2 — 判定規則は内部矛盾があり、全場合を分類できない。**

- **根拠:** `s1-brief.md:20` は「10% は1対だけ、中央値には適用しない」だが、`:36` は中央値比に適用して「D357 の変化なし域」と呼ぶ。D357:4-5 と T-2710 事前登録:8 は前者。D1260:3 は特定施策について paired full K=3 中央値差10%未満を不採用とする別の採用条件である。また現行(ii)では全対負の大きな退行も「中央値差 <10%」に入り、ゼロを含む場合・有効3対未満の扱いが未定義。
- **成果物への影響:** 同じ対表から異なる判定が生じ、退行や反復不足を「小さい方向一致」と誤分類する。
- **是正:** 次を分離して事前登録する。
  - 各対の差・率と、D357による単走比較の「10%未満＝変化なし」注記。
  - 対差の中央値、対率の中央値、条件別中央値差をそれぞれ表示。これらは同じ量ではない。
  - 中央値比10%を採否提示の閾値に残すなら、**本 wave 独自の保守的基準**と明記し、D357からの直接導出としない。
  - 3分類は「全対正かつ閾値以上」「全対正だが閾値未満」「それ以外」とし、最後に符号混在・ゼロ・全対負を明記。有効3対未満は判定不能として先に分岐する。3/3一致は有意差認定にしない。

**must-fix A3 — rank / partner だけでは、計画どおりの独立した witness 検証が閉じない。**

- **根拠:** `s2-plan.md:14,49` は「JUnit の nodeid」から unit と候補順を再構成する。しかし `_pytest/junitxml.py:114-142` は nodeid を `classname/name` に変換し、標準の完全な nodeid 属性を出さない。さらに既存 reorder は `conftest.py:1718-1758` の台帳キー解決、`:1820-1827` の unknown cost と元 index に依存する。最終順位だけでは元順の同値 cost の tie-break を独立に復元できない。
- **成果物への影響:** 正しいBを誤除外するか、B自身の出力から期待値を作って誤った partner 選択を見逃す。
- **是正:** 完全な runtime nodeid・実際の loadgroup scope・pairing 前の基準順を、property または既存成果物との一意な対応で確保する。対応が欠落・曖昧なら検証不能として扱う。台帳の正規化、未知 cost、同値 cost の規則も固定する。検証対象は partner 集合だけでなく、全 rank、head、rest、unit 内順、48 **unit**であること、selected の全件被覆とする。property の自己申告順位を期待順位として再利用しない。

property の転送経路自体は静的に確認できた。`_pytest/reports.py:452` → `:596` の report直列化 → `xdist/remote.py:281-289` → `workermanage.py:424-431` → `dsession.py:326-329` → `_pytest/junitxml.py:490-497` である。hold の precedent も `conftest.py:2231-2235,2248-2253` にある。ただし、これは今回の property の実受入出力を実測した証拠ではない。

**should A4 — 隣接対は許容できるが、同一 job・同一 allocation と同義ではない。**

- **根拠:** `s1-brief.md:12,34`、D357:6、D104 決定4、T-2710 事前登録:5。今回の隣接2受入は別々に3 shardをdispatchする。T-2710の同 job 比較とは異なる。
- **成果物への影響:** 裁定パッケージが node割当・時間差の交絡を制御済みと過大に述べる。
- **是正:** 「対ID」と「実際のjob/allocation ID」を分け、今回を逐次の隣接対比較と呼ぶ。同時に2 worktreeから自分の受入を投入する案はD357に反する。一方、逐次化しただけでD104の同一allocation条件まで満たしたとは書かない。

A,B／B,A／A,B は対内位置が2対1であり、位置効果を完全には打ち消さない。全走列も A,B,B,A,A,B で、厳密な走ごとの交互ではない。順序を明示した現設計は使えるが、各shardのjob ID・node・投入／実行開始／終了・queue待ち・受入間隔・他waveの並行状況を残す。login loadと投入時leader数だけでは実行中の共有FS負荷を表さない。負荷やnodeによる事後的な選別はせず、条件別の説明資料とする。

**should A5 — W_max は妥当だが、受入全体の経過時間と区別し、O/Fを同じshardに結び付ける。**

- **根拠:** `s1-brief.md:33`、`acceptance_shards.py:1127-1133,1174-1185`。W_max は各JUnit時間の最大で、queue待ちやshard開始時刻のずれを含む受入全体の経過時間ではない。
- **成果物への影響:** pytestの短縮を受入全体の短縮と誤読したり、異なるshardのWとOを引いて架空のFを作る。
- **是正:** W_maxを主指標にすることを支持する。Bは全shardに効き、順位逆転はあり得るため、各走のargmaxとW_0/W_1/W_2を併記する。O_j、F_j＝W_j−O_jをshardごとに計算し、最大shardの内訳を選ぶ。Fは残差であって、固定費と実証された量ではない。

**should A6 — 除外と12走上限は支持するが、赤と停止の扱いを固定する。**

- **根拠:** `s1-brief.md:34,37`、`s2-plan.md:47`、T-2710 README:40、同事前登録:10。
- **成果物への影響:** Bの順序依存失敗を再試行で隠したり、良い対が揃うまで測る停止規則になる。
- **是正:** 赤を含む対全体の無効化は妥当。ただしF945「型」だけで非帰属と断定せず、失敗内容・arm別件数を全て残す。B固有の再現性ある赤は実装問題として扱う。最初の有効3対で停止するのか、固定対数を完了するのかを決める。12測定走とlandingの1走を区別し、上限到達時に3対未満なら反復不足とする。T-2710の「条件ごと置換1回」から変更した規則であることも明記する。

**should A7 — 親briefの数値は、次の範囲に限定すべき。**

- **根拠:** `s1-brief.md:63-66`、T-2710 README:35-41、T-2766起票文:2-3。
- **成果物への影響:** 予測値が既知の効果として裁定パッケージに混入する。
- **是正:** 次の区別を付ける。
  - 「直近40 sessionでshard-0最遅」「gw5、items 2」「F≈67〜70」は、射影にはsession別原表・抽出条件がなく、今回独立に再検算できていない。依頼文の94/99との母集団の違いも明記する。
  - items数が2という一致だけで「T-2710と同じregime」とは言えない。replica／実受入、単独node／同時3shard、cache状態が違う。
  - 全台帳でzeroが51件あっても、各shardのhead外に48個のzero-cost **unit** があるとは限らない。groupの合算、hold、未知項目もある。各shardで候補cost分布を算出する。
  - cost≈0は過去台帳値であり、B走の実測duration≈0ではない。
  - 一度のcollect-onlyはbytecode準備にはなるが、計算nodeのpage cacheや共有fixtureまでwarmと保証しない。
  - Bが全走緑でも「順序依存testの不在」ではなく「今回のB走では順序依存失敗を観測しなかった」と書く。

## レンズ B

**must-fix B1 — cardinality負例が成立せず、M4のkill設計も成立していない。**

- **根拠:** `s2-plan.md:10,28,39`。realizedはcardinality降順なので、「headに1-item unitがあるのに候補側に2-item unitがある」という状態は作れない。xdist実物も `loadscope.py:374-379` で同じsortをする。
- **成果物への影響:** 無変異版のテストが失敗するか、本番では作れない中間状態をstubで作り、M4を閉じたと誤認する。
- **是正:** 本番入口から到達する負例にする。例えば2-item unitを49個以上置き、head外に高costの2-item unitが残る一方、48 partnerは低costのsingletonになる構成なら、pairedの後方に残った2-item unitが再sortで前へ戻り、検算が失敗する。M4ではその検算だけを削除し、指定した例外が出なくなることをkill理由にする。

cardinality検算自体は、今回の「意図したqueueを実現したBだけ測る」契約には妥当である。ただし各shardの実データで事前確認し、不成立が確定しているBを高価な受入へ投入し続けない。cardinality制約下の別の最小化へ変えるなら別方式として事前登録を改める。96 unit未満で元のordered_unitsを返しpropertyも付けない設計は支持するが、その走をB発火済みと数えない。

**must-fix B2 — A不変の負例が、要求するcollection順を検査していない。**

- **根拠:** `s2-plan.md:16,26` はbyte同一を要求する一方、負例1はdequeueとpropertyだけ。`loadscope.py:374-379` のcardinality sortにより、異なるcollection順が同じdequeue順になる場合がある。`conftest.py:1762-1780` のidentity multiset検査も、順序・marker・nodeidの不変までは保証しない。
- **成果物への影響:** Aのcollection順やgroup/holdを変えた実装が通り、「既存A対B」の比較ではなくなる。
- **是正:** 未設定・空文字について、変更前の確定した期待collection列、item identity、unit内順、既存property、group/skip marker、selectedを比較する。AとAを同じ変更後関数で呼ぶ自己比較は避ける。Bにもgrowth/flaky hold、複数item group、real-repo suffix処理を含め、順序と追加property以外の不変を検査する。既存hookではhold処理→yield中のshard選択→suffix処理→reorderの順であり（`conftest.py:2201-2282`）、この配置を維持すれば干渉を避ける設計にはできる。

**should B3 — realized queueの49〜96位と、各workerの2個目は区別する。**

- **根拠:** `loadscope.py:263-282,313-336,396-402`。初回は各workerへ1 unit、その後はpending **item数** が2以下のworkerだけに1 unitを追加する。既存harnessも `test_acceptance_schedule_order.py:1447-1449` でworkerへの割当を捨て、`:1597-1602` で完了通知なしの追加rescheduleを行う。
- **成果物への影響:** dequeue検査だけから「全workerの相方が最小」「最長workerに3個目なし」と主張する。
- **是正:** queue順検査として既存harnessを使うことは支持する。ただし次の反例を配布検査に追加する。
  - 初期unitが3 itemsのworkerは最初の2個目配布を飛ばされる。その後のworkerの2個目は単純な48+i番ではない。
  - 飛ばされたworkerがpending＝2になる前に他workerがpartner群を消費すれば、そのworkerの2個目は重いrestになり得る。
  - 初期unitが2 itemsのworkerはpartnerを受けても、1 item完了でpending＝2となり、重い3個目を受け取り得る。

実 `LoadGroupScheduling` の送信先とindicesを記録し、実物の完了通知でこれらを駆動する。scheduler本体をstubにしない。「先頭48固定＋次48を低cost化」は成立可能だが、全workerの2個目を保証する一般命題ではない。

**should B4 — production witnessの主張範囲を決め、必要ならworker対応だけを追加する。**

- **根拠:** `acceptance_shards.py:1117-1133` はnodeid→workerを内部保持するが、`:1160-1186` の出力は主に集計である。rank/propertyはcollection変換の発火証拠であり、実配布の証拠ではない。
- **成果物への影響:** partner集合は正しいが律速workerに意図した相方が届かなかった場合を区別できない。
- **是正:** 最小構成では全3shardの最忙worker ID・items・durationとtimelineをA/B併記し、実配布は未観測と明記する。T-2710同様に「最長unitの相方が変わった」まで述べるなら、Bの各itemに実行worker IDとworker内実行順を追加するか、既存のnodeid→worker対応を小さな成果物として保存する。items＝2だけでは相方の識別にならない。JUnitと別の大きなprobe基盤を新設する必要はない。

**should B5 — env経路はallowlist追加で静的に成立するが、exact pinは伝播試験ではない。**

- **根拠と判定:**

| 段 | 現物 | 判定 |
|---|---|---|
| 待ち手→launcher | `dev_wave_wait.py:847-849` | 環境をcopyしてK=3を追加 |
| launcher→login runner | `acceptance_launcher.py:571-586` | copy後にbindingをoverlay |
| login runner→shard dispatch | `run_tests.py:1295-1304,2329-2334` | 対象envを削除しない |
| dispatch request | `dispatch_compute.py:3693-3696` | **現行allowlistには対象keyがなく、ここで落ちる** |
| compute `_job_run` | `dispatch_compute.py:1827-1853` | allowlist検証後、inherit環境へoverlay |
| compute runner→pytest | `run_tests.py:1509-1532` | copyしたenvを子へ渡す |
| pytest→xdist worker | ローカルpopen worker経路 | 親環境を継承する構成 |

- **成果物への影響:** exact pinだけを根拠にすると、request生成・適用の断線を見逃し、B不発火の走を消費する。
- **是正:** allowlist追加とpin更新に加え、実request生成でtokenが載ること、受信側overlayとshard子envまで保存されることを対応する検査で確認する。最終的には各B走の3shard witnessを必須にする。collect-onlyは `conftest.py:1846,1853-1854` でreorder無効、allocateはyield中に済むため、予定配置なら選択集合に作用しない。

env変更はrunnerのblob bytesを変えず、log hashは各走自身の照合なので、A/Bでlogが違うことは問題ではない。ただしreceiptを自動的なB証明とは扱わず、env記録・request・JUnitをsession/shard IDとhashで結び付ける。これは静的判定であり、全段のlive伝播確認済みという意味ではない。

**should B6 — 6変異の「killされた理由」を固定する。**

- **根拠:** `s2-plan.md:34-41`。現在は期待killのテスト名・検査面だけで、無変異の成功や固有の失敗箇所が未定義。
- **成果物への影響:** 共通のfixture故障・環境漏れ・別のassert失敗を6件の検出力として計上する。
- **是正:**

| 変異 | 帰属させる検査 |
|---|---|
| M1 | 非同値costの候補から得た、独立した期待partner列 |
| M2 | 固定headの完全一致と、48 partnerの境界 |
| M3 | 新しいitem集合・明示unsetでのA期待collection列 |
| M4 | B1の到達可能fixtureで、指定検算例外が出ないこと |
| M5 | 本番hookが付与するpropertyの欠落。XML出力面も別に確認 |
| M6 | 実allowlistのexact pin欠落。伝播全段のkillとは呼ばない |

各変異は単独適用し、同じ条件の無変異版成功を先に確認する。期待partnerを本番helperで算出したり、テスト側でpropertyやenvを補填したりしない。既存harnessはitemを浅く共有するため、A/B間でpropertyが残らないようfresh itemを作る。

**should B7 — 実装非landは支持するが、branch名だけでは再現資料が不足する。**

- **根拠:** `s1-brief.md:26`、`s2-plan.md:49,54`、D104 決定3。
- **成果物への影響:** cleanupやbranch移動後、対表は残っても測定コード・集計コードを復元できない。
- **是正:** 測定commit SHA、実装差分の保存物とhash、全tested tip、台帳、集計script、起動手順、raw成果物索引を記録側に保存する。残置branchの所有者・用途・再訪／cleanup条件も記載する。D104は「効果を示せない機構をlandしない」であって、結果によらず永久に非landという規則ではない。ただし今回、採用を先取りせず記録だけlandする選択は整合的である。既定offでlandする案には再現性上の利点がある一方、効果未実証の保守面をmainへ増やすため、今回必須ではない。

**nit — 実装境界とアンカーの小修正。**

- **根拠:** `s2-plan.md:9,12-13`、`conftest.py:1794,1820`。
- **成果物への影響:** それ自体で対表・判定は変わらないが、authorが補完すべき点が残る。
- **是正:** 後段helperへ`unknown_cost`をどう渡すか、scope比較に必要な識別子をどう得るかを明記する。既存unit dictには明示的なscopeキーがない。hold propertyのアンカーは実際には`:2231-2235,2248-2253`、scheduler helperの定義は`:1566`。JSON/Markdown両出力や1行commentを削ることは研究前進上の必須事項ではない。

## 総括

**must-fixは5件**：同一条件の定義、判定規則、witnessの独立再構成、cardinality負例、A不変の検査。

親briefのprovisional裁定は次のとおり。

| 裁定 | 判定 |
|---|---|
| P1：env opt-in | **支持**。allowlist追加が必要。live伝播は未確認 |
| P2：実装をlandせず保存 | **支持**。測定コード・集計器の再現資料を残す |
| P3：JUnit property witness | **条件付き**。転送経路はあるが、識別情報と主張範囲を補う |
| P4：非docs木一致で有効 | **反証**。output走査・docs入力・履歴依存があり、完全なtested tip一致が必要 |
| P5：軽量段構成＋2レンズ相談 | **条件付き**。上記修正、author後の実配線・変異・集計器レビューを完了条件にする |

**envは現状のままではdispatch request生成で落ちる。予定のallowlist追加後は、全段を通る経路が静的には成立する。** pytest・計算jobは実行しておらず、実装の緑・変異kill・live発火は未確認である。