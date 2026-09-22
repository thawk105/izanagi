## 閉鎖表

対象 HEAD は `b79bccff115521a064e98f9ff0c56ae76ebde34e`。静的照合のみ実施し、書込み・テスト・計算投入はしていない。

以下の略記を用いる。
- 設計: `output/insights/2026-09-22/t2849-comparison-harness-design/README.md`
- 決定片: `docs/spool/decisions/2026-09-22-dev-wave-t2849-comparison-harness-design-2.md`
- 作業片: `docs/spool/worklog/2026-09-22-dev-wave-t2849-comparison-harness-design-1.md`
- B5: `docs/b5-generator-contrast-preregistration.md`
- コードのファイル名のみの参照は `orchestrator/campaign/` 配下。

| ID | 判定 | 根拠 |
|---|---|---|
| R1 | partial | 初期点の兄弟keyと継承照合の変更は明記されたが、空・不正出力の direction / magnitude を閉じた値域へ写す規則がない。設計:153–155,355；`p3_s4_loop.py:1420–1439`。F1。 |
| R2 | partial | endpoint不在時の品質欠測優先は修正済み。ただし機械欠測をendpoint不在に条件付け、系列全体の欠測というB-5契約と不整合が残る。設計:194–200；B5:143–144；`b5_generator_contrast.py:810–823`。F2。 |
| R3 | closed | 許容領域と局所支持集合を区別し、失敗点を再抽選せず提出してA/Bを計上すると明記。設計:103,121–125,159。 |
| R4 | closed | read-heavyのexact flags、参照Genomeの測定入口、実装単位と作業片への接続が揃った。設計:175–177,356；決定片:15；作業片:29；`output/s1-freeze/known_axes_freeze.json:542–549`。 |
| R5 | closed | coderのrole・proposal契約の差を明記し、知識射影だけの効果という主張を撤回。設計:130；決定片:14；`p3_s4_loop.py:2976–2995`。 |
| R6 | partial | BO・package・MOCC実績の限定は改善。ただし識別子の直接検索から「消費するdriverは無い」へ広げた断定が残る。設計:15,261–262,332–334；`genome.py:209–220`。F3。 |
| R7 | closed | D2214の項とinsightの節を区別し、算術条件・R0の探索履歴・非LLM四手法を修正。第31回裁定の原本パスも追加。設計:5,16,60,82,145,169；決定片:24；`docs/decisions.md:71079–71087`。 |

## 新規所見

**F1・must-fix・対象: whiteboardへの全提出機会の射影**

- **確認済み:** 設計:153はschema不合格まで含めて`rejected`とし、iterationをaの連続にする。一方、既存5 fieldではdirectionとmagnitudeも必須で、欠測値は許可されない（`p3_s4_loop.py:1420–1439`）。既存拒否eventには有効なplanner情報が保証されない（`b5_generator_contrast.py:750–752,782–785`）。
- **設計からの反例:** 空出力、またはplanner自体が不正な提出では、resultだけ決めても5 fieldの行を構成できない。
- **影響:** 拒否行の省略ならaの連続性と拒否履歴が失われ、任意補完ならLLMへ架空の方向・大きさを伝える。
- **修正案:** 有効なplanner情報がない拒否の表現を明示する。5 fieldを維持するなら、固定代用値と「この拒否では方向・大きさに意味がない」ことを役割入力契約まで定義し、親の裁量で補完しない。

**F2・must-fix・対象: 機械欠測の優先順位**

- **確認済み:** 設計:197と決定片:15は「endpointが無い」場合だけ機械欠測をscore欠測へ写す。しかしB5:143–144はretry上限を超えた**系列**を欠測とし、実装も既存の正常候補の有無を問わずendpoint選択前に終了する（`b5_generator_contrast.py:810–816`）。設計:234の「上限を超えたら欠測」は対象が明示されず、この条件分岐を解消していない。
- **設計からの反例:** 初期点5 µsが正常で、後の探索slotが機械故障のretry上限を超えた場合、設計:194からは初期点を再計測してscoreを得られる読み方が成立する。B-5では系列欠測となる。
- **影響:** 機械欠測を含む系列が正常scoreとして残り、arm別の欠測率と比較標本が変わる。
- **修正案:** stock不成立とは別に「初期点・探索の機械故障がretry上限を超えたら、endpointの有無を問わず系列を終了しscore欠測」を明記する。品質欠測とは分け、設計:195–200・決定片:15・作業片:17の「B-5と同じ優先」を同期する。

**F3・should・対象: MOCC_SPACE検索の結論**

- **確認済み:** `MOCC_SPACE`を含む`orchestrator/`の`.py`が`genome.py`だけという検索結果は再現した。ただし同ファイルは`SPACES["mocc"]`に登録し、`space_for(protocol)`経由で取得できる（`genome.py:209–220`）。直接識別子の出現だけでは間接利用を除外できない。
- **未確認:** MOCCの8点を探索・評価するdriverの不存在。
- **影響:** 設計:334の「消費するdriverは無い」が、限定検索で確認していない再利用可能性まで否定する。
- **修正案:** 「この識別子の直接参照は定義元のみ。間接利用と探索driverの有無は未確認」に限定する。今回は追加調査を必須にする必要はない。

**F4・nit・対象: pin定数の表記**

- **確認済み:** 設計:317・作業片:18は両定数を`e9e477ca`とするが、`CURRENT_PIN`のliteralは7桁の`e9e477c`（`pin.py:31`）、`CCBENCH_FULL_SHA`は`e9e477ca1b55348ab4530de0b1cf663ce4555290`（`s8b_approved.py:67`）。
- **影響:** 比較対象commitは変わらないが、実測した定数の文字列が台帳上不正確になる。
- **修正案:** 「CURRENT_PINは7桁prefixで、FULL_SHA・gitlinkと対応する」と記す。

## 反証済み

- 初期点の兄弟keyは自系列のv・結果分類・正常fitnessだけを渡す設計であり、他armや既知最良の値を混入させる指定はない。機械的遮断の証明ともしていない（設計:154,163–165,184）。
- iterationをa順にする変更自体はA/Bの計上を変えず、継承照合の変更も実装単位に含まれる。残る問題はF1の欠測planner表現である（設計:153,209–210,355）。
- 進化は失敗点を除外せず再提出するため、無料再抽選による予算上の利益は導入されていない。anomaly即rejectと投入後のB消費も維持される（設計:124,210,232；B5:113–116,289–290）。
- 進化の数値例は、`exp(ln 10 ± ln 4) = 10 × [1/4, 4] = [2.5, 40]`で正しい。丸め前という限定も適切（設計:103,122）。
- `(μ+λ)`の例は、初期集団4評価をB=8から支払う条件なら残り4評価、λ=4の子世代が1回で正しい。共通初期点を無料で使う場合の一般論にはしていない（決定片:24）。
- read-heavyのflagsは`BACK_OFF=0 / NO_WAIT_LOCKING_IN_VALIDATION=0 / NO_WAIT_OF_TICTOC=1 / WAL=0`で一致する（設計:175；`output/s1-freeze/known_axes_freeze.json:542–549`）。
- endpoint不在時の**品質欠測**優先、再計測anomalyのfallback、再計測品質欠測のscore欠測は実装と一致する（設計:197–200；`b5_generator_contrast.py:817–835`）。
- `68106660`を含む対象`.py`はtest1本だけ、`MOCC_SPACE`を含む対象`.py`は`genome.py`だけというファイル数は再現した。後者には定義とregistry登録の2出現がある（`orchestrator/tests/test_mocc_xp_pin_candidate.py:26`；`genome.py:124,211`）。
- BO・進化の指定語検索は無関係な1件のみという結果を再現した。package importの成否は今回再実行せず、過去の親実測として扱った（設計:261–262；`tools/codex_reasoning_ab.py:9466`）。
- 訂正された実装単位は既存射影・評価入口・集約の接続であり、新しいgate・汎用台帳・一般化の追加は見られない（設計:350–359；作業片:27–30）。
- decisions fragment本文に角括弧付きT番号はない。設計・両fragmentの主要な構成は揃っており、F2の不整合は三文書に共通して残っている（決定片:11–39；作業片:17,27–30）。

## 総括

**NO-GO。must-fix 2件（F1・F2）、should 1件、nit 1件。**
R1〜R7はclosed 4件・partial 3件・regressed 0件。残る必須修正は、planner情報のない拒否の表現と、機械欠測を系列全体へ優先する規則。