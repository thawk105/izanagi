## 所見

**実装レビューは GO。must-fix は検出しませんでした。** 統合 commit `cfab7a2f2` の差分と `author-impl.patch` は完全一致し、変更は指定2ファイルのみです。静的検査だけを行い、編集・pytest実走はしていません。

以下、G＝[condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-requested-us/orchestrator/campaign/condition_meaning_gate.py)、T＝[test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-requested-us/orchestrator/tests/test_condition_meaning_gate.py)。行番号は現物で確認済みです。

1. **refuted／must-fix候補：fixture が供給検査で先に落ち、負例が意図した検査へ届かない。**
   T:264–290 は独立期待表から owner・header・中継headerを生成し、installer後にREQUESTED_USの既定0とTU mappingを局所追加しています。両腕に本文が残ります。T:1713–1740は拒否reasonだけでなく観測数2・6・3を検査し、T:1743–1759は相殺入力を `_assert_compile_time_branch_selection` に直接渡して個別観測の拒否を検査しています。依存先のstubはありません。
   **成果物影響：懸念は成立せず、別の先行エラーを全箇所観測の検出実績に数える構造ではありません。**

2. **refuted／must-fix候補：既存21 macroの契約や期待値が緩む。**
   親commitとの比較で、既存21 entryの値・順序・2-tuple、全既存classの本文、`DEFINE_SPECS` の本文が不変でした。G:339の主fileのN、G:3036の既存reason/detail、単file時の計装本文とargv、既存evidence key集合も維持されています。D1491の5箇所（G:705、3574、4030、4049、4433）も変更なし。既存テストの緩和・反転・skip追加・削除はありません。
   **成果物影響：既存macroの受理集合を広げる変更は確認されません。全21件のrecord bytes同一を実測したとは扱いません。**

3. **refuted／must-fix候補：裁定の必須機構が欠落、またはframework化している。**
   G:3088・3132で複数fileを深いshadowに置き、全計装fileをsymlink対象から除外。G:3200でsite用defineを複数fileだけに追加。G:3423→3430→3450は非識別→総数不一致→個別不一致の指定順です。G:4084・4164–4212は登録簿に基づく2 keyの必須化、型・順序・digest・identity・個別値・argvを検証しています。新dataclass、汎用validator、include gate、未宣言directive走査、別proof_kind、新moduleはありません。G:343のhelperは登録データの共有に留まります。
   **成果物影響：4箇所の相殺をgreenにする穴と、単fileへの副証拠混入を防いでいます。**

4. **real／nit：DW-G05上、総和の再検査は削除可能です。**
   G:3461–3468と4205–4209は、直前に「登録簿由来の全rowが固定期待値に一致」「総数も同じ期待値に一致」を検査済みなので、その後の総和不一致には到達しません。これは[ruling.md:34](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-requested-us/ruling.md:34)・38が要求した冗長性であり、authorの仕様逸脱ではありません。
   **成果物影響：現行登録簿と先行検査を維持する限り、この2ブロックを削ってもcertified選択・レポート・台帳・受理集合は変わりません。削除は必須としません。**

5. **real／should：実走証拠はfile単位まで照合でき、node単位の完全一致は未確認です。**
   author報告の新設9関数・31 schema変異・直接呼出し計75ケースは現物と整合します。ログが参照する[receipt.json:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-requested-us/output/pegasus-dispatch/0a87dd359c8da48d12484d4764ec738e/receipt.json:50)には、所有test、S1、MOCC 3件、spawn・B-4目録を含む**合計15 file**が列挙され、計算ノード`bnode019`・child rc=0を確認できます。[focus-own1.log:31](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-requested-us/focus-own1.log:31)は1148 passed／2 skippedです。ただしnode名とskip理由がなく、各新設nodeのPASSやskipの帰属までは断定できません。`--force-dispatch`の親argvもこの証拠にはありませんが、計算ノード実行自体は確認済みです。
   **成果物影響：実装の受理集合には影響せず、「全対象nodeが緑」という報告の検証可能性が不足します。既存のnode別記録があれば添付してください。**

## pin 追随表

| 対象 | 現物・判定 |
|---|---|
| 登録簿末尾追加／既存順序・2-tuple | G:325、T:58・1083：維持、22件 |
| 対応集合23件 | T:3403–3407：追随済み |
| docstring `Twenty-two` | G:13、T:3620：双方追随 |
| 主N=2／総N=4 | G:329–352、T:1095–1101：分離済み |
| 独立fixture・対照0 | T:62–66・264–290：production mappingから生成していない |
| patch header×2＋owner×2 | T:365–373：順序付き完全列挙。他macroの式は維持 |
| NOINLINE特例assert | T:293–296：維持 |
| 非対値／旧CLI拒否 | T:2293–2311・2338–2362：REQUESTED_US追加 |
| evidence dataclass field pin | T:1912–1935：追加済み、既存field/key維持 |
| schema再構成 | T:1809・1871：`require_issuer=False` |
| CLI subprocess非追加 | T:1894：CLI直接呼出し |
| 未登録例 | T:2275：`SS2PL_LOCK_IMPL`維持 |
| D1491／`DEFINE_SPECS` | 変更なし |
| spawn 1／B-4 49 | G:1683、各目録T:123／329：維持 |
| S1 stock fixture | `test_s1_direct_comparison.py:716–731`：変更なし。複数file対応済みとは主張不可 |
| 揮発payload | 新規期待値への一時path・tree hashの焼込みなし |

## 判定

**GO：レンズBの実装レビューとして。** 必須pin、局所fixture mapping、判定順序、個別観測、再検証、既存契約維持を確認しました。

これはwave完了・landの判定ではありません。提供されたlogin要約の実TU成功と3代表cellのI1比較は整合しますが、計算ノードの実TU観測、正式変異matrix、受入全走の完了は今回の資料から認定していません。焦点走ログ自身も受入全走ではないと明記しています。

## 総括

must-fixなし。削除候補は裁定由来の冗長な総和検査2箇所、記録上の改善点はnode別結果・skip帰属の補足です。成果の主張は、指定owner TU・configureにおける4箇所の枝選択とCLI admissionまでに限定するのが妥当です。