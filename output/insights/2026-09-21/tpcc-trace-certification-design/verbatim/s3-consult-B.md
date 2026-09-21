## 判定

**草案は要修正。** 主な反証は、①現行拒否している v1 を「互換維持」として復活させる点、②一般 API の rollback 漏れを TPC-C の必須前提に広げた点、③段1の実行比率と容量計算の不一致、④17単位・5 wave に認定成立までの費用が閉じていない点である。

静的検査のみ。build・binary 実行・pytest・性能測定は行っていない。親の configure 成功・build 拒否は依頼文の報告であり、こちらで再実証していない。

以下、`CC/`＝`external/ccbench/`、`TP/`＝`CC/include/tpcc/`、`V/`＝`orchestrator/verifier/`。`brief` と `plan` は指定された[親 brief](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-tpcc-trace-design/brief.md)、[設計草案](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-tpcc-trace-design/stage2/plan.md)を指す。

## 1. 親の P1〜P8

複合主張は、結論まで成立しなければ **refuted** とした。

| 項 | 判定・重大度 | 根拠 path:line | 放置時の成果物への影響 | 修正案 |
|---|---|---|---|---|
| P1 | **refuted / must-fix**。「表番号を足せば足りる」は誤り | brief:15、`CC/include/op_element.hh:19`、SI `transaction.cc:239,246,361,365` | SI の read→update/delete が作る辺を欠き、cycle を隠す | `(table,key)` に加え、外部版読みを値として TRACE 専用履歴へ保存 |
| P2 | **real** | brief:16、`CC/include/tpcc.hh:102,110,111` | 未修正なら正常 trace も counter 不一致で認定不可 | 成功 commit の counter 加算を保証。許容幅は作らない |
| P3 | **real、現行五取引限定** | brief:17、`TP/tpcc_initializer.hh:365,370,380`、`TP/tpcc_tx_payment.hh:114,165` | 不変索引の追加 trace は認定集合を改善せず容量だけ増やす | 索引不変の根拠を記録し、選択後 Customer の CC 読みを残す |
| P4 | **refuted / must-fix** | brief:18–20、`CC/include/masstree_wrapper.hh:287`、SI `transaction.cc:448,451` | 物理上限による途中打切りを全域不在と誤解し、偽依存・偽認定を生む | scan 別観測と物理 prefix を保存。「最後の返却 key」で代用しない |
| P5 | **refuted / must-fix**。node validation の存在は real | brief:21、Silo `transaction.cc:478`、SI `:485`、MOCC `:1042`、各 abort | node validation を寿命・可視性の保証と誤認し、不正な履歴や未完走を扱う | 全五取引で露出する tuple 寿命問題を独立に扱う。ただし一般 rollback 漏れは下記の射程限定 |
| P6 | **real、現行状態として** | brief:24、MOCC `transaction.cc:78,1173`、SI `:539` | watermark を転用すると行を破壊し、INSERT/DELETE で実行が停止する | TPC-C では無効。SI の新形式は別途実装する |
| P7 | **refuted / must-fix** | brief:22、`TP/tpcc_tx_delivery.hh:69`、SI `transaction.cc:365` | 「scan の R が残る」とした依存が実際には消える | SI 読み履歴を native read set から独立させる |
| P8 | **real、費用の一般化は修正必要** | brief:23、`hooks/guard_write.py:44`、`orchestrator/campaign/s8b_approved.py:67` | 手続きを過小評価すると新 pin で受理不能、過大評価すると不要な旧系列再凍結が増える | 新候補の公開・承認・pin 整合を残し、旧系列の再開作業を除く |

P4 の「OrderLine・Order は挿入のみ」は、**membership の変化に限る**なら成立する。行への操作全体では Delivery の UPDATE がある（`TP/tpcc_tx_delivery.hh:106,150`）。また、brief:19 の「親の実測」は、提示された資料からは実行による観測と確認できないため、静的に導いた曖昧性と記すべきである。

## 2. CC 改修の実在性

### B1 — scan の容器は新設が必要。既存 set では代替できない

**重大度：must-fix**

| CC | read phase で保存する位置 | commit 時の出力位置 | 後始末・編集面 |
|---|---|---|---|
| Silo | `transaction.cc:291` の引数、`:299` の物理候補、`:305,311,317` の既読・自書込み・新規読みに対応 | `:602` の C、`:606` の R、`:611` の W、`:698` の E | abort `:27`、begin `:55`、成功終了 `:700`。transaction.cc は内 |
| SI | `:417,424`、`:433` の key コピー、`:434,441,448` の版選択。deleted/null の区別は `:451` より前 | `:539`。現行 read set のみを使う `:541` は置換対象 | abort `:578`、成功終了 `:560`。transaction.cc は外 |
| MOCC | `:375,383`、`:389,395,401`。abort になる `:402` の観測を成功 frame へ残さない | `:1134`、E `:1204` | abort `:1059`、begin `:189`、成功終了 `:1207`。transaction.cc は内 |

**根拠 path:line：** 上表、各 `include/transaction.hh` の `node_map_` は Silo:39、SI:41、MOCC:35。これはノード版の集合であり、scan の境界・limit・個々の返却集合を持たない。

**成果物影響：** commit 時の set から scan を再構成すると、同じ取引内の複数 scan・既読再利用・自書込みを混同し、述語辺の受理集合が変わる。

**修正案：** 草案の値コピー方式を採用する。ただし次を実装単位の完了条件へ明記する。

- 境界 key、物理候補 key、版、状態は所有する値として保存する。`string_view`・tuple/version/body ポインタを持ち越さない。
- 型・TLS/container・追加 include・記録呼出し・clear をすべて `#if TRACE` 内に置く。現在の `trace.hh:25` 内へ置けば header による perf 常駐を避けられる。
- abort、次の begin、成功終了を閉じる。MOCC の native RLL は retry 用なので、trace buffer と一緒に消してはいけない。
- 物理末尾は scan buffer の順序から採る。Silo/MOCC は既読要素を先に result へ入れ、新規 read を後から足すため、一般に `result.back()` は物理末尾を表さない。

これは**実装可能な配置の確認**であり、未実装の容器が TRACE=0 から消えることを検証したという意味ではない。

### B2 — v1 の「互換維持」は現行拒否を緩める

**重大度：must-fix**

**根拠 path:line：** plan:34,468 に対し、`V/parse.py:323` は5-field Cを明示的に拒否。`output/insights/2026-08-12/t816-step4-impl/README.md:12` も v1 互換分岐を設けなかったと記録する。

**成果物影響：** v1 を再受理すると、件数・終端を欠く履歴が parser を通り、現在より広い受理集合になる。

**修正案：** 「既存 v2 の判定・出力を維持し、TPC-C v3 を追加。v1 拒否も維持」に訂正する。SI が現在 v1 を**出す**ことは、verifier が v1 を**受ける**根拠にならない。

## 3. tuple 寿命と rollback を分ける

### B3 — 公開後・write set 登録前の漏れは real。ただし既定 TPC-C の必須修正ではない

**重大度：should**

**根拠 path:line：**

- Silo：公開 `transaction.cc:88`、不一致 return `:97`、登録 `:109`。
- SI：`:319,328,340`。
- MOCC：`:504,513,525`。
- node_map への新規記録は scan callback：Silo `:733`、SI `:685`、MOCC `:1286`。
- NewOrder/Payment の操作：`TP/tpcc_tx_neworder.hh:295`、`tpcc_tx_payment.hh:242`。scan を行う他三取引には insert がない。
- 試行終了時の node_map clear：Silo `:40,703`、SI `:562,597`、MOCC `:1077,1212`。

**成果物影響：** 到達しない一般 API 分岐を必須工事とすると、TPC-C の認定集合は改善しないまま工数と baseline 変更を増やす。

**修正案：** 「scan→同じノードへの insert」を行う一般取引の実在バグとして分離する。現行五取引では、insert する取引に scan がなく、scan する取引に insert がないため、この不一致分岐を TPC-C 必須前提に数えない。将来合成が取引操作自体を変更する場合は再評価する。

### B4 — abort 即時解放は全五取引で問題になるが、三 CC 共通の回収条件は未設計

**重大度：must-fix（全五取引の実行基盤）**

**根拠 path:line：** Silo abort `:32` と待機 `:250,255`、SI abort `:583` と tuple 参照 `:153,433`、MOCC abort `:1064` と温度・lock 参照 `:276,322`。NewOrder は `TP/tpcc_tx_neworder.hh:308` 以降で公開し、後続品目で `:320` の失敗が可能。意図的失敗生成は `tpcc_query.hh:122`。

**成果物影響：** reader が保持するポインタを abort が解放すると、クラッシュ・待機停止・不正データ参照が起こり得る。完走した trace の cycle 検査だけでは、その実行基盤の正当性を補えない。

**修正案：**

- **Silo：** 木から外すだけでなく、既存 reader が lock 待機から抜け、不在として終了できること、その reader が参照を捨てるまで回収しないことを満たす。
- **SI：** tuple と Version を別々に扱う。`cc/si/include/tuple.hh:9` の Tuple には Version を delete する destructor がない。したがって `abort():583` 後の `:586` を直ちに「解放済み Version への書込み」と断定するのは誤り。tuple の UAF と、Version の退役・回収は別問題である。
- **MOCC：** read set だけでなく CLL の lock ポインタ、abort 後も使う RLL を退役条件に含める。`construct_RLL():902`、`unlockCLL():1094`、`begin():189` が対象。単純な「一取引終了まで待つ」では足りると断定できない。

全五取引では、NewOrder が公開済み OrderLine を後で rollback し、その間に他取引が範囲から生ポインタを取得する経路を静的に排除できない。後段の validation が abort しても、先行した危険な dereference は救えない。

一方、**段1では挿入先 Order/NewOrder/OrderSecondary/OrderLine/History を他取引が読む・scan する経路がない**。この寿命修正三単位を段1開始前の必須条件にする根拠は薄い。全五取引に向けて扱えばよい。

## 4. 編集面・pin・過剰な手続き

### B5 — pin 前進は必要だが、旧系列の全面再凍結は不要

**重大度：should**

**根拠 path:line：** `hooks/guard_write.py:44`、`docs/decisions.md:67618`（D2150）、`:69180`（D2184）、裁定控え:23。

| 変更 | 現 hook の三ファイル境界 | 必要な扱い |
|---|---|---|
| Silo/MOCC transaction.cc の計装 | 内 | 本採用は D16 の trace 枝へ収容 |
| SI transaction.cc、trace.hh、tpcc.hh | 外 | 基盤改修として編集経路を整え、新候補へ収容 |
| transaction header、wrapper、initializer | 外 | 必要部分だけ追加。scratch 迂回を前提にしない |
| tuple 寿命の本体修正 | ファイル依存 | TRACE 計装と分離し、両 build の baseline 変更として扱う |
| verifier・pipeline | CCBench 三ファイル制限外 | 新TPC-C経路の統合 |

**成果物影響：** pin だけ変更しても admission policy・identity が旧値なら新経路は拒否される。一律再凍結は不要な作業と計算費用を生む。

**修正案：** D2150 の候補公開・取得可能性・gitlink/承認定数/`CURRENT_PIN` 同時更新は残す。ただし同決定は、旧較正の一律再取得を要求していない。D2184 も旧証拠を固定 checkout で保持し、新 main へ移す系列だけ整合させる整理である。

裁定控え項5に従い、**旧8b/8cの再開、旧 lock の移行、旧凍結 chain の新設を本見積りから削る**。新TPC-C経路が実際に要求する契約は残す。

また、寿命修正を含む旧→新 pin 全体に TRACE=0 同一性を要求してはいけない。本体修正済み baseline と、それに trace 計装を加えた候補を比較する必要がある。

## 5. 工数と段階分割

### B6 — 17単位・5 wave は分割案であり、完了見積りとして未成立

**重大度：should**

**根拠 path:line：** plan:348–372 と下表。

**成果物影響：** 未成立の X/P 証拠面と統合修正を予算外にすると、emitter/parser 完成後も certified が作れず、レポートの完了予定だけが先行する。

**修正案：** author 所有範囲、review/fix、公開待ち、計算投入を別欄で見積もる。

| 比較対象 | 数値・事実 | 出所区分 | 根拠 |
|---|---|---|---|
| D296/T816 C++部分 | 1 wave、C++差分は最終記録で +14/−1 | 記録 | `output/insights/2026-08-11/t816-fn2-trace-v2/README.md:6`、翌日 step4 README:31 |
| T816 parser・pin移行 | 別実装 wave。前段は blocker で停止。現用 pin 23箇所を追随、fix 2巡 | 記録 | `output/insights/2026-08-12/t816-step4-impl/README.md:7,22,35` |
| D295/T756 witness | 1 wave 内で fix 2巡、焦点走4回、変異3走 | 記録 | witness README:32、`docs/archive/worklog-phase3-0811-427-428.md:623` |
| MOCC trace pair | 1 waveでも投入系の実在障害3件を修正。成果は certified 用ではない | 記録 | `output/insights/2026-08-26_mocc-trace-pair.md:18,44` |
| 草案 | 17 author単位・5 wave、SI追加1〜2単位 | 試算 | plan:360,362,364 |
| 推奨する扱い | 5 wave は暫定の工程枠。日数・総作業量への換算根拠なし | 静的評価 | 上記実績では小差分も統合・修正が別費用 |

**17単位から必須でない部分：**

- 最初の三単位に含めた「scan→insert の rollback 漏れ修正」は現行TPC-Cに必須でない。
- tuple 寿命三単位を**段1より先**に置く順序は不要。全五取引では残る。
- 独立したTPC-C reporter は実装選択。旧出力を保つ条件分岐で足りるなら、別 subsystem は不要。
- 旧系列再凍結、全表キー衝突の網羅台帳、一般再挿入・任意取引向けの存在管理は今回の必須範囲から外せる。
- 初期キー集合、scanとの対応、counter、構造化 anomaly は削れない。

逆に、X/P は SI だけの追加注意ではない。`V/model.py:77,466` は両証拠面を要求する。各 CC が新TPC-Cでこれを満たす具体案を、認定開始前に閉じる必要がある。

**段1を先に閉じる価値はある。** 述語・初期キー・公開 tuple の reader 寿命を待たずに、表付き点依存とSI読み保存を検査できる。ただし公開・pinを二回にする必然はない。共通v3を設計し、段1を内部の受入節目として先行、全体で一度公開する構成が安い。

## 6. 容量の再計算

### B7 — 段1の flag 設定と45:43正規化が一致しない

**重大度：should**

**根拠 path:line：** `TP/tpcc_common.hh:7`、`tpcc_query.hh:58,64,289`、plan:432。

他三取引の flag を0にすると、その三つの閾値は0になる。`x >= threshold_payment` が必ず成立するため、他三取引は完全に停止できる。ただし Paymentを43のままにすると、**NewOrder 57%・Payment 43%**になる。

**成果物影響：** 実行設定を57:43にして45:43正規化の容量・取引構成を報告すると、必要保存量とレポートのmixが食い違う。

**修正案：** 最小構成は57:43を採用して明記する。45:43の厳密な正規化は現行整数％ flag では表せない。

草案と同じ桁幅・平常時条件で再計算した。C/Eを各1行としている。

| 取引 | R/W/S/Q | 総行数/commit | 約B/commit | 出所 |
|---|---:|---:|---:|---|
| NewOrder、n=10、重複なし | 23/24/0/0 | 49 | 2,133 | コードから数えた＋形式試算。`tpcc_tx_neworder.hh:295,308,314` |
| Payment | 3/4/0/0 | 9 | 355 | 同。`tpcc_tx_payment.hh:242` |
| Delivery、g=10、L=110 | 140/140/20/120 | 422 | 19,853 | 同。`tpcc_tx_delivery.hh:199` |
| OrderStatus、L=11 | 14/0/2/12 | 30 | 1,478 | 同。`tpcc_tx_orderstatus.hh:106,113,118,130` |
| StockLevel、L=u=220 | 441/0/1/220 | 664 | 29,659 | 同。`tpcc_tx_stocklevel.hh:42,50,67` |
| 段1、45:43正規化 | — | 29.45 | 1,264 | 試算。草案の仮想mix |
| **段1、既存flagによる57:43** | — | **31.80** | **1,368** | コードの閾値＋試算 |
| 全五取引、45:43:4:4:4 | — | **70.56** | **3,152** | 既定比率＋試算 |

草案の行幅計算は概ね成立する。8-byte key の R≤43 B、W≤45 Bは提示した桁幅内の値であり、実測平均・無条件の上限ではない。Q/Sは仮定したstate表記・桁幅に依存する。abort時の一時buffer容量、allocator overhead、verifierの展開メモリはこの表に含まれない。

### B8 — OrderLine の番号差は real。全走を初期Lで代表させない

**重大度：should**

**根拠 path:line：** loader `TP/tpcc_initializer.hh:259,279`、NewOrder `tpcc_tx_neworder.hh:314`、Deliveryの境界 `tpcc_tx_delivery.hh:133`、StockLevel `tpcc_tx_stocklevel.hh:46`。

**成果物影響：** 初期・実行時の区別を省くと、manifest件数、範囲内キー集合、容量予測が変わる。隣接orderのline 0を除外すると実際のscan結果と一致しない。

**修正案：** 実コードの範囲をそのまま使い、初期中心・実行時中心の例を分ける。

| 対象 | 数量 | 出所 |
|---|---:|---|
| 初期1 order | 1..n+1、平均11行 | コードから数えた |
| 実行時1 order | 0..n−1、平均10行 | コードから数えた |
| 単一order範囲 `[o,1; o+1,1)` | 自orderのline 0を除外し、次orderのline 0を含み得る | コードから数えた |
| 初期OrderLine/warehouse | 平均330,000キー | 30,000 order×11、試算 |
| 三表の初期G一覧 | 約8.60 MB/warehouse | 9,000×22＋30,000×38＋330,000×22、試算 |

したがって草案のL=110/11/220は初期状態中心の例として妥当だが、長い走行の平均値ではない。番号差を今回直すなら容量だけでなくworkloadそのものが変わるため、trace計装とは分ける。

## 7. verifier時間と2 node時間

### B9 — 既存速度からは点処理の目安まで。全五取引の上限は出ない

**重大度：should**

**根拠 path:line：** `output/insights/2026-09-20/verifier-capacity/README.md:40,41,46`、plan:244–249。

**成果物影響：** YCSB単価をTPC-Cの確定所要として使うと、述語列挙・到達可能性の費用を落とし、計算投入台帳の予算を過小評価する。

**修正案：** 総commit数で条件付き試算を出し、新述語処理は別項にする。今回検索したrepoのworklog・insights・decisionsのMarkdown記録には、この換算に使える**三CCのTPC-C throughput実測は無い**。

| 記録／試算 | 時間 | 出所 |
|---|---:|---|
| YCSB write-heavy 8,323,838取引 | 297秒、35.7秒/百万取引 | 記録、capacity README:40 |
| balanced 14,748,197取引 | 478秒、32.4秒/百万取引 | 記録、同:41 |
| read-heavy 16,819,316取引 | 433秒、25.7秒/百万取引 | 記録、同:46 |
| 段1・57:43 | 約77〜106秒/百万commit | 操作数29.8をYCSB約10操作へ比例、試算 |
| 全五取引 | 約170〜240秒/百万commit＋新述語処理 | R/W/Q/S量による粗い試算 |

48スレッド全体の生成率を仮に `r` commit/秒、測定区間を3秒と置くと、`N=3r`。**48をさらに掛けない。**

| 仮定した総生成率 | 3秒のcommit数 | 全五取引trace | 検査の比例項 | 1 nodeでの比例項 |
|---|---:|---:|---:|---:|
| 10万/秒 | 30万 | 約0.95 GB＋初期一覧 | 51〜72秒 | 0.014〜0.020 node時間 |
| 100万/秒 | 300万 | 約9.46 GB＋初期一覧 | 510〜720秒 | 0.142〜0.200 node時間 |

すべて**試算上の仮定**であり、TPC-C性能値ではない。build、ロード、traceの終了処理、検査、変異、再試行、述語処理を加える必要がある。

不在選言の単純な到達可能性探索は、草案どおり最悪 `O(a(T+E))`。したがって**1走・wave全体が2 node時間未満とは現時点で判定できない**。上の300万commit例でも、同規模10走なら比例項だけで約1.42〜2.00 node時間となり、上側では追加費用前に確認ラインへ達する。裁定控え:21に従い、wave内の全jobを合算する必要がある。

既定1倉庫・48スレッドは、PaymentのWarehouse更新と10個のDistrictへの集中を生む。NewOrderもDistrictを更新するため、abortと取引別commit比率が変わる。生成比率をそのまま実測commit比率として扱えない。

## 8. 草案の推奨の採否

| 草案の推奨 | 判定 | 修正・参照 |
|---|---|---|
| v3、表付きキー、SI読み保存、counter修正 | **real** | B1。容器とcleanupを具体化 |
| YCSB v1/v2「入力受理」を維持 | **refuted / must-fix** | B2。現行v1拒否を維持 |
| rollback漏れと寿命修正を全て段1の前提にする | **refuted / should** | B3/B4。一般APIの漏れを分離、寿命は全五取引に向けて扱う |
| S＋scan別Q＋初期キー集合 | **real** | B1/B8。実キー・物理順を保存 |
| 選言を既存依存で絞り、未決はindeterminate | **real、保守的初版として** | 観測事実と推論を分ける。B9の費用は未確定 |
| 物理LIMITの欠落を完全な可視行LIMITとして認定しない | **real** | P4。APIの認定射程を明記 |
| MOCC watermark不使用、SIのG2を拒否 | **real** | P6。ただし実TPC-CでのG2再現は未実証 |
| 17単位・5 wave、段1 1.26 GB/百万commit | **refuted、確定見積りとして** | B6/B7。57:43なら約1.37 GB |
| 全五取引3.15 GB/百万commit | **real、指定条件の試算として** | B8。全履歴の上限ではない |
| X/Pとpin整合を残す | **real** | B5/B6。旧系列全面移行は削る |

なお、brief:7の「段1/段2が確定裁定」は **refuted / should**。裁定控え:16では二段構成は親の改訂推奨で、ユーザー明示確認は未取得とされる。放置するとレポートの承認状態が変わるため、「TPC-C必須という意向に対する親の分割案」と訂正する。分割の再承認をこの静的相談で求める必要はない。

## 総括

段1を先に内部受入まで閉じる案を支持する。既存flagで57:43に限定し、表付きv3、SI読み保存、完全counter、既存X/P要件を先に成立させる。

全五取引にはscan別観測・初期キー集合・tuple寿命の解決が残る。一方、一般APIのscan→insert rollback漏れ、旧8b/8c全面再凍結、v1互換復活は必須工事から外す。

**17単位・5 waveは暫定工程表としてのみ残せる。容量は段1約1.37 GB、全五取引約3.15 GB／百万commitという条件付き試算。TPC-C実測速度と述語検査時間が無いため、2 node時間未満の投入とはまだ判定できない。**