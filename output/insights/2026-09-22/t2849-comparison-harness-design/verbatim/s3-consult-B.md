## 所見

以下、`skeleton.md`・`facts.md`・`request.md` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2849-comparison-harness-design/` 配下を指す。コードと指定文書の静的照合のみを行い、テスト・計算・書込みは行っていない。

**B1・must-fix・対象 P2/P10、骨子 §2・§3・§9 — scope 外の一般化と台帳新設が設計に入っている。**

- **確認済み:** §9 は「兄弟 series runner と arm 汎用の台帳」「S3 adapter」を列挙し、末尾では「新しい台帳は足さない」としている。依頼は台帳・一般化の追加を明示的に除外する。S2 は差し込み口の記述として必要だが、稼働する第2空間の設計まで確定する必要はない。
- **根拠:** `request.md:7–9`、`skeleton.md:18`、`:26–30`、`:73–80`。
- **影響:** 比較基盤の設計完了が、新しい実行基盤・台帳・未実装IRへの対応に依存し、依頼の完了条件が拡大する。
- **修正案:** S1 の5手法について、既存単回評価の呼出し手順と入出力対応を具体化する。系列の制御が必要でも S1 専用の薄い制御に限定し、汎用 runner／台帳 schema の新設を要求しない。S2 は将来必要な入力と前提、S3 は既存設計への参照と未接続の明記に縮める。

**B2・must-fix・対象 P1/P5、骨子 §2・§9 — 接頭辞解除だけでは5手法の口は成立しない。**

- **確認済み:** `machine_proposal_document` は random／sweep と整数 literal 専用。`slot_argv` は LLM に `K2Args` を必須とし、K2 なしの proposal を機械生成扱いにする。したがって主比較の K0 LLM は、その関数へそのまま入らない。一方、base loader には K2 なしの proposal 読込みがあり、LLM 由来の build authority も別に存在する。K0 を実現するため新しい proposal schema が必須というわけではない。
- **根拠:** `orchestrator/campaign/b5_generator_contrast.py:139–153`、`:506–528`、`:710–715`；`orchestrator/campaign/p3_s4_loop.py:2976–2995`、`:3547–3566`、`:3675–3682`、`:3742–3761`。
- **確認済み:** S3 はさらに別物で、既存設計は planner を外し、IR JSON／C++ 本文と兄弟 driver を使う。現行の planner／coder.value 文書へ統一する骨子と一致しない。
- **根拠:** `output/insights/2026-09-21/silo-function-synthesis-space/README.md:367–387`。
- **影響:** K0 LLM が拒否されるか機械生成と誤記録され、S3 では候補を読めない。[consumer 取り残し]
- **修正案:** §9 に S1 の機械4手法の literal 文書化、K0 LLM の通常文書＋coder authority、slot の識別と既存 sidecar consumer の対応を明記する。共通なのは候補適用・検証・計測とし、由来を運ぶ入口まで同一と書かない。S3 は現行CLIへ接続済みとしない。

**B3・should・対象 P8、骨子 §7 — 「そのまま使う」に、規則の継承とコードの無変更再利用が混在する。**

- **確認済み:** random／sweep は preimage の文字列だけでなく workload、系列1..12、A≤30、28点格子に拘束される。`slot_key` は ARMS・予算定数・PREREG_VERSION に拘束される。`classify_slot` は B-5 sidecar schema、`b5_slot`、`BACKOFF_FIXED != -1` による候補判定、legacy＋performance の WAL 列を要求する。endpoint は整数値で失格・同点処理を行う。
- **根拠:** `orchestrator/campaign/b5_generator_contrast.py:105–168`、`:323–346`、`:417–444`、`:815–828`。
- **確認済み:** 逆に、`SeriesLedger` 自体には ARMS や整数値の検査がない。任意の追加値を event に入れられるため、「arm が増えるから台帳を汎用化する」はコードから導けない。ただし schema 名は B-5 固有である。
- **根拠:** 同ファイル `:207–248`。
- **影響:** 実装量を過小評価する一方、不要な台帳改造を増やし、正当な結果を分類不能に落とす。
- **修正案:** 「継承する意味」「S1・同じwire形式なら呼べる関数」「変更が必要な結合」の3区分へ直す。S1 では値文法と値による endpoint 処理を変える必要はない。S3 の identity 対応は別設計へ送る。

**B4・must-fix・対象 P5、骨子 §2・§5 — 観測 field の列挙だけでは、生成器へ渡る入力が決まらない。**

- **確認済み:** base module の `current_perf`／leading indicators 組立は責務外だが、B-5 の `expected_inputs` は既に最新の正常 certified 結果から current_perf／baseline を組み立てる。したがって観測組立が全面的に不在ではない。一方、これは履歴全部・leading indicators 全体・critic 診断を一括生成する関数でもない。
- **根拠:** `orchestrator/campaign/p3_s4_loop.py:1303–1304`；`orchestrator/campaign/b5_generator_contrast.py:451–496`。
- **確認済み:** B-5 whiteboard に入るのは投入後の `evaluation-result`。Tier0 拒否は別 event であり、スモークの性能数値は探索入力へ流さない。
- **根拠:** 同ファイル `:796–807`；`docs/decisions.md:71152–71154`。
- **影響:** 手法ごとに拒否履歴、欠測、古い性能値の扱いが変わる。「同じ観測を渡す」という宣言だけが残る。[設計調査漏れ]
- **修正案:** 新 producer の新設を既定にせず、既存結果から各入力への対応表を定める。特に拒否時の tell、品質欠測時の fitness 不在、最後の正常値の継承、初期候補の履歴への挿入、Tier0 数値の非入力化を固定する。critic 診断は性能WALから自動生成できるデータとして扱わない。

**B5・must-fix・対象 P4/P6、骨子 §4・§5 — 小予算で「探索」が何回起きるか未定である。**

- **確認済み:** BO の初期 design 数、進化の μ・λ・選択方式は未定で、共通初期候補も「5／10 µs など」「k」のまま。手法固有初期化は B を消費するとだけ書かれている。
- **根拠:** `skeleton.md:35–36`、`:46`；`output/insights/2026-09-21/silo-function-synthesis-space/README.md:448`。
- **推論:** B=8 で追加初期 design が8なら獲得関数による提案は0回。μ=4、λ=4を同じ予算から払えば、初期集団後は1世代しかない。これは性能予測ではなく予算の算術である。
- **影響:** 「BO」「進化」の比較が実質的に初期点の比較となり、手法名と実験内容がずれる。
- **修正案:** S1 は共通初期点を BO の学習データ・進化の親選択にも使い、追加初期化数を固定する。小予算の推奨は逐次 GP-EI と (1+1) 変異で、各正常観測後に更新する形。整数への丸め・境界処理・同点・重複・fitness 不在時の処理まで定義する。(μ+λ) を選ぶなら、初期集団費と完全世代数を数字で示す。

**B6・should・対象 P4、骨子 §4、facts の実装出所 — 「依存が見つからない」から標準ライブラリだけの再実装必須は導けない。**

- **確認済み:** 手元の根拠は login の import 調査報告で、計算ノードは未測定。しかも facts では未照合の [子] 項であり、本レビューでもその環境調査は再実行していない。
- **根拠:** `facts.md:26–27`、`skeleton.md:34–36`。
- **設計判断:** S1 の小標本・1000点列挙なら小さな GP-EI 再実装を選ぶ余地はある。しかし混合kernel・可変構造IR・型付き交叉まで同じ理由で自作するのは、実装量と正しさの負担を増やす。numpy を使わないこと自体は比較の公平性を改善しない。
- **影響:** 最適化手法の比較に、自作数値計算や未定義の表現処理の差が混ざる。
- **修正案:** S1 の採用方式を先に決め、GP の重複観測・ノイズ・特異行列・EI同点の扱いを仕様化する。numpy 不使用を研究要件にせず、実行環境の可搬性との実装判断に戻す。TPE／RF型／型付きGPへの変更は、S3 の表現確定後の別択一とする。小予算だけを根拠に他方式の有効性は断定しない。論文名の列挙だけで元手法との同一性を主張せず、変更点を伴う「再実装」とする。

**B7・must-fix・対象 P1/P7/P8、骨子 §2・§6 — A と物理費用の単位がB-5の継承宣言と一致しない。**

- **確認済み:** 骨子は「LLM の役割呼出し1回＝1 ask」とするが、B-5 は planner・coder・critic を含む親運用の中の候補提出機会を A とする。また骨子は内部の型検査による選び直しを無料にする一方、事前登録は候補提出前の選び直しも A とし、乱数の偏り除去を別扱いにしている。
- **根拠:** `skeleton.md:14`；`docs/b5-generator-contrast-preregistration.md:109–111`、`:161–167`、`:204–209`。
- **確認済み:** 現行 slot の時間は subprocess wall。job Elapse を slot ごとに持つわけではない。
- **根拠:** `orchestrator/campaign/b5_generator_contrast.py:618–645`；`skeleton.md:55–56`。
- **影響:** LLM だけ A を複数消費する解釈や、進化の候補棄却を無料にする解釈が生じる。同じjobの Elapse を各slotへ載せれば費用も重複計上される。
- **修正案:** A は候補提出機会、LLM call は別の物理費用とする。獲得関数の候補点採点・乱数偏り除去と、完成候補の棄却再生成を区別し、B-5から変更する規則は変更と明記する。job Elapse はjobにつき1回、slot wall は内訳とし、BO／進化の生成計算、初期点、参照点、失敗・retry・endpoint再測定の費用も含める。

**B8・must-fix・対象 P6、骨子 §5・§7 — 参照点・初期点・endpoint の接続が未完成である。**

- **確認済み:** 現行 B-5 は stock-start を `BACK_OFF=1, BACKOFF_FIXED=-1` に固定し、その後すぐ探索へ入る。初期点用の段はなく、endpoint は探索の evaluations から選ぶ。`p2_2_flag_opt` の `BACK_OFF=0` は、この既存stock口には入らない。
- **根拠:** `orchestrator/campaign/b5_generator_contrast.py:588–595`、`:723–740`、`:815–828`；`orchestrator/campaign/p3_s4_loop.py:2314`；`skeleton.md:45–46`。
- **推論:** 初期点を B 外で観測させても endpoint 集合に入れなければ、初期点より劣る探索結果が endpoint になる。静的backoffは、flags・PIN・sourceが一致すればS1候補と一致しうるため、「参照だから空間外」とは一律に言えない。
- **根拠:** `output/insights/2026-09-21/silo-function-synthesis-space/README.md:391–414`。
- **影響:** 初期点の扱いだけで成果曲線と最終scoreが変わり、既知最良を同じ口で測るという主張も未成立になる。
- **修正案:** 初期列とk、参照結果を見せる構成の採否、初期点のendpoint資格、初期点不成立時の扱いを固定する。参照測定は候補生成経路と区別しつつ検証・計測条件を揃える。既知最良の exact flags と測定条件を記し、旧性能値を新条件の性能値として代入しない。

**B9・must-fix・対象 P9、骨子 §8 — MOCC の共有headerは差し込み可能性の根拠であり、S2成立の証明ではない。**

- **確認済み:** MOCC は abort 処理で `BACK_OFF` が有効な場合に共有backoffを呼ぶ。ただし patch の既定合成式は単純な固定値式ではない。特に `BACKOFF_FIXED=1000` は、patch本文の式では余り0の枝へ入り待機量0になる。S1 は proposal の literal への置換でこの既定式を置き換える。MOCCでmacro設定だけを流用すると、S1と同じ1..1000にはならない。
- **根拠:** `external/ccbench/cc/mocc/transaction.cc:1079–1089`；`patches/silo-backoff-fixed.patch:69–70`；`orchestrator/campaign/b5_generator_contrast.py:146–147`。
- **確認済み:** MOCC_SPACE の8点は YCSB の3フラグ空間であり、backoff値空間の全列挙ではない。X/Pの protocol 登録も certified 全般の証明ではなく、評価対象は compiled-source の証拠である。既存裁定はproof完了と探索開始・pin前進を分けている。
- **根拠:** `orchestrator/campaign/genome.py:119–136`；`orchestrator/verifier/model.py:58–81`；`docs/decisions.md:66747–66764`。
- **影響:** 同名の値が別の待機量を意味する比較、限定的なflag最良の「MOCC既知最良」への拡大、登録済みというだけの恒真な成立判定につながる。[恒真ゲート]
- **修正案:** S2は「pin前進後、固定したMOCC flags上で同じliteral材料化が成立する場合の差し込み候補」と書く。BACK_OFF=1、材料化、較正済み動作点とその正しさ測定が必要。8点全列挙は採るとしても「指定YCSB・PIN・条件下のflag参照最良」に限り、差し込み口のための必須追加研究にしない。人間push→pin再承認の提示→承認後のgitlink更新別waveという順序を維持する。

**B10・should・対象 facts、骨子 §4・§8 — 未照合報告と設計・実装・実走の区別を修正すべきである。**

- **確認済み:** facts の末尾の「いずれも設計のみで未実装」は、直前の D2216・D2217 に限れば合うが、裁定全体へ広げると D2215 に反する。D2215 は実装済みである。また候補Cの「6走」は正例と負例を含む行列で、6件の certified 結果という意味ではない。
- **根拠:** `facts.md:39–44`；`docs/decisions.md:71140–71158`、`:71177`、`:71197`、`:71215–71218`。
- **未確認:** repo全体のBO／進化実装0件、計算ノードのpackage、MOCC実績の網羅的な不存在は、指定範囲の静的照合では確定していない。
- **影響:** 未実装扱いによる重複実装、負例まで含めたcertified実績の水増し、未確認環境を根拠とする実装方式の固定が起きる。
- **修正案:** factsを「コードで確認」「裁定文書の記載」「未照合の調査報告」に分ける。骨子の「T-2849完了条件＝20〜40候補×3 workload」は、今回の逐語依頼が計算なし設計なので削除する。
- **根拠:** `skeleton.md:69`、`request.md:4–9`。

## 削るべきもの

- §2・§9の「arm汎用の兄弟runner／上位互換台帳」：明示scope外。S1の具体的な制御手順と既存記録の利用へ縮める。
- §3・§9のS3混合kernel・型付き交叉・adapterの実装設計：表現と接続が未成立。既存policy設計への参照と未接続の注記だけ残す。
- §3の「LLM×C++も本基盤の同じ口を通す」：現行proposal契約と一致せず、今回の5手法比較にも不要。
- §8のMOCC8点全列挙を差し込み必須作業にする記述：比較対照を得る別研究。必要な参照条件だけ記す。
- §8の「T-2849完了条件＝疎通20〜40候補×3 workload」と計算見積り：今回の設計依頼の完了条件から外す。
- §4の「numpyにも依存しない」を絶対条件にする記述：未確認の計算ノード環境からは導けない。
- §2の新しい永続観測producer：既存結果を読む射影で足りる部分は対応表に置き換える。観測契約そのものは削らない。

## 反証済み

- S1の機械proposal→単回評価の入口自体は実在する。問題は5手法・K0・別空間への接続範囲である（`b5_generator_contrast.py:139–153`、`:506–528`）。
- Tier0不通過はAのみ、投入後build失敗・anomalyはBという分離は実装・裁定と一致する（`docs/decisions.md:71149–71151`、`b5_generator_contrast.py:646–650`）。
- retryが同じ論理Bを再加算しない実装は存在する（`b5_generator_contrast.py:603–604`、`:646–664`）。
- B-5の受理集合と生成器の支持集合を区別する説明は正しい。ただし、それだけでS3の表現差の影響が消えるわけではない（`docs/b5-generator-contrast-preregistration.md:89–91`）。
- B-5標本と新比較標本を混ぜず、判定規則をそのまま移植しない方針は妥当（`skeleton.md:62`）。
- MOCCの共有headerとBACK_OFF条件下の呼出しは確認できた。温度述語proofを探索認可としない扱いも妥当（`external/ccbench/cc/mocc/transaction.cc:7`、`:1079–1089`；`docs/decisions.md:66763–66764`）。

## 総括

must-fixは **7件（B1・B2・B4・B5・B7・B8・B9）**。
設計着手前の択一は、①S1具体化＋MOCC差し込み口に限定するか一般化へ拡張するか、②小予算を逐次GP-EI／(1+1)で使うか初期design・集団へ配分するか、③参照情報を与える構成と初期点のendpoint資格をどう固定するか。
推奨は①限定、②共通初期点を使う逐次更新、③参照情報の有無を一つに固定し、正常な空間内初期点をendpoint候補に含める。