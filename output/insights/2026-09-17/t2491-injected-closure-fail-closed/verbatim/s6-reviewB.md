## 報告と実体の一致 (食い違い表)

以下、T＝[test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/tests/test_ccbench_spawn_sites.py)、N＝[s8b_oracle_n_pilot.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s8b_oracle_n_pilot.py)。

**実装子の報告と差分・実ファイルに、確認できた実装上の食い違いはない。段4の変異期待集合には更新が必要。** pytest・変異は実行していない。

| 照合対象 | 結果 |
|---|---|
| 変更ファイル・行番号 | 指定Tのみ。報告の変更位置と一致。差分の全9 hunkを実ファイルと照合した |
| R0 | T:1835で文の値そのものに限定、1842で3要素を記録。一致 |
| R1 | T:1615でscopeごとにstack初期化。1981以降でbody／orelse／handlerをpushし、`finally`でpop。当該finalbodyは積まない。一致 |
| R2 | T:1746–1749で全stackのTryStar・finally脱出をR3より先に拒否。一致 |
| R3 | T:1757–1810の分類・脱出検査・末尾Raise・外側追跡は報告と一致 |
| R4 | T:2309の`and unswallowed`、2312以降の保証限界コメントと一致 |
| 新nodeid・期待値 | 正例7、負例12、production pin 1。報告のID・assertと一致 |
| 「67 node（追加20）」 | ASTから独立集計して67。追加は7＋12＋1＝20 |
| 実走件数 | 親ログは **66 passed / 0 failed / 1 skipped**。67件と整合。authorの「実走0」はauthor自身の失敗したdispatchの報告であり矛盾しない |
| production 4 check | N:997→1018、1017-try、1028–1029の変換は実ファイルで一致。他3件は射影されたs3・s4の追跡と一致するが、対象production原文が射影にないため独立再確認済みとは扱わない |
| 束縛名交差・helperの明示raise 8件 | 同じ理由で、このレビューでは独立確認できない |
| 波及・既存test不変 | 差分から旧ソースをメモリ内で復元しAST比較。既存のトップレベル定義で変更されたのは`_PythonGateFlow`のみ。既存test、`_GateFlowState`、`_campaign_checked_root`は不変 |
| anchor一意性 | M0〜M7のoldは各対象ファイル内で1箇所 |
| 段4との期待集合差 | s4はM2＝n1〜n12、M4＝n4・n5。s5の**M2＝n8以外、M4＝n4のみ**が実装に適合する |

親ログにはnode別結果・skip理由・Python版がない。Python 3.10と新testのskip条件からn10のskipと整合するが、ログ単体がnode名まで証明するわけではない。また、ログ自身が受入全走として扱わないよう明記している。

## scope / 最小形の判定

**D1882／D1869に対するscope逸脱は確認しなかった。**

- 変更はinjected判定と、それに必要な名前情報・try位置・check記録、および直接対応する新testに限定される。
- 共有Try処理にはstack操作が増えるが、既存のflow状態・継続・合流処理は維持されている。
- campaign専用判定、繰延べ台帳、既存testの期待値、productionには差分がない。
- `_RETURNED_EVIDENCE_ERROR`／`_RETURNED_EVIDENCE_CATCHERS`は分類材料。基底classやhelperの全raiseを固定するassertは追加されていない。
- module代入は再束縛の保守的判定に使うだけで、alias chainを解決していない。
- T:3259のproduction pinは指定4 sinkのcovered確認だけ。全injected集合固定、floorのdeferred固定、`failures == []`の再assertはない。
- 変換後の外側処理、MAYBEの未変換経路、with・guard・結果名再束縛はコメントで保証外とされる。段4でscope外と裁定済みの問題を、今回のmust-fixとして再投入しない。

## 変異の帰属 (anchor 一意性、専属 killer、期待集合、追加登録案)

以下は**静的予測**。KILLED／SURVIVEDの実測報告ではない。負例の短縮IDはすべて
`orchestrator/tests/test_ccbench_spawn_sites.py::test_define_sink_cross_product_t2491_rejects_injected_swallow[ID]`。

| 変異 | oldの位置・出現数 | 期待赤／帰属 |
|---|---|---|
| M0 | T:2311、1 | 空。等価コメントの陽性対照 |
| M1 | N:1028、1 | 下記7 node。synthetic負例には帰属しない |
| M2 | T:1842、1 | n1〜n7、n9〜n12。3.10ではn10を除く10件 |
| M3 | T:1758、1 | `n2-bare-pass` |
| M4 | T:1792、1 | `n4-conditional-raise`のみ |
| M5 | T:1748、1 | `n6-finally-return` |
| M6 | T:1835、1 | `n8-lambda` |
| M7 | T:1802、1 | `n9-system-exit` |

M2ではn8のcallがR0で記録されないため、boolを恒真にしても変わらない。M4ではn5が先行する`has_escape(handler.body)`で拒否される。authorの補正は正しい。

M2〜M7にはそれぞれ新負例killerがある。既存campaign syntheticは利用する判定が異なり、未検査injected既存例は一致check自体がない。既存production consumerを追加赤とする根拠も見当たらない。ただし完全赤集合の確定はprobeを要する。

M0は意図的な無害対照、M1はproduction変異なので、「全変異に新負例killerが必要」をこの2件に適用してはならない。

**M1の期待7 nodeは過不足のない静的予測。**

| ファイル | node | 発火点 |
|---|---|---|
| `test_s8b_oracle_n_pilot.py` | `test_injected_build_fn_without_condition_records_is_rejected` | 782の`pytest.raises` |
| 同上 | `test_build_binaries_uses_binding_flags_and_prepared_records_independently` | 819の不一致record拒否 |
| 同上 | `test_r33_successor_protocol_document_loads_from_repository` | 323のdriver digest。冗長gate |
| T | `test_define_sink_cross_product_has_no_unreviewed_ungated_member` | 2829の空failure |
| T | `test_define_sink_cross_product_classifies_t2155_production_sinks_exactly` | 3355の空failure |
| T | `test_define_sink_cross_product_t2520_certify_entry_removal` | 3377の台帳除去前の空failure |
| T | `test_define_sink_cross_product_t2491_injected_production_sinks_stay_covered` | 3273のN:997 covered pin |

他の空failure assertはsynthetic sourceを使う。繰延べ台帳exact／live sink検査は例外handlerの意味を評価せず、M1は行数・sinkを変えない。process／sink inventoryも追加killerにならない予測。

r33は完全赤集合に含め、意味的帰属から除外する。DW-M08の証拠は、M1自体のKILLEDではなく**旧閉包PASSED／新閉包FAILED**。今回の焦点走ログはその証拠を含まない。歴史的m04とのbytes一致も、射影台帳に置換bytesがないため親の照合記録に依存する。

**追加登録候補と検出力の穴：**

| 対象 | anchor案 | 静的予測・推奨 |
|---|---|---|
| 未知名をNONEに緩和 | T:1780–1783の`return "none"`→末尾`return "maybe"`→次の`for`を文脈anchorにし、末尾だけ`return "none"`へ | n7がkiller。登録を推奨 |
| 外側追跡停止 | T:1783の`reversed(self.injected_try_stack)`→`reversed(self.injected_try_stack[-1:])` | n11がkiller。登録を推奨 |
| handler脱出検査除去 | T:1790の`if has_escape(handler.body):`→`if False:` | n5がkiller。M4とは独立なので登録を推奨 |
| 局所再束縛判定除去 | T:1768の`if name in local_names or name in self.module_assignments:`→`if name in self.module_assignments:` | **n12はkillerにならない。** MAYBEからDEFINITEになっても末尾Passで拒否される |
| TryStar拒否除去 | T:1746–1747のTryStar判定を除去 | **n10は3.11でもkillerにならない。** 後続R3が末尾Passを拒否する |

「NONE分類を外す」は意味を分ける必要がある。未知名をNONEにする変異ならn7が検出する。一方、既知ClassDefのNONE分岐を削除してMAYBEへ落とす変異は、p4やs1 productionを誤拒否する方向であり、新負例専属の変異ではない。

局所再束縛を単独で守るには、別の新負例として「module classへの変換raiseを、局所再束縛したXのhandlerに置く」形が必要。MAYBEなら拒否、判定除去後のDEFINITEなら変換停止で受理される。既存n12の期待値は変更しない。

TryStar単独変異は今回の3.10本走に検出保証として登録せず、**実装あり・実走未検証・現n10では単独除去も検出しない**と保証限界へ記録することを推奨する。将来3.11で検証するなら、別負例の`except* X: raise`、さらに順序検証用の外側TryStar＋内側変換が必要。

## 新 test の形式

- 全19 parameter IDは`[a-z0-9-]+`に適合し、一意。
- 展開した19個の`orchestrator/campaign/synthetic_t2491_*.py`は実在ファイルと衝突しない。
- 正例はmodule class定義2行を含み、sinkは8行目。負例は6行目。`_BuildSink`と一致する。
- production pinはpath・scope・lineno・kindによる辞書参照なので、対象sinkが移動すると赤になる。T2155と同型の位置固定であり、裁定で指定した4件を超える集合・台帳・全体閉包の義務は追加していない。

## must-fix と nit (DW-G05 の 1 行付き、修正案)

**実装コードのmust-fixは確認なし。変異受入前の記録修正が1件ある。**

1. **must-fix：段4のM2／M4期待集合をauthor補正へ更新する。**
   修正先は[s4-ruling.md](/home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s4-ruling.md)の変異事前登録節、および親が作るspec。対応実装はT:1835／1842、1790／1792。
   - M2：`n1〜n12` → `n8以外。n10は対応Pythonのみ`
   - M4：`n4・n5` → `n4のみ`
   - 補正理由とprobe前の更新であることを残す。既存testの期待値は変えない。
   **DW-G05：旧期待集合のままでは正しい変異結果がMISMATCHになり、完全赤集合による帰属証拠を成立させられない。**

2. **nit：n12を局所再束縛規則の単独killerと扱わない。**
   authorはその単独検出を主張していないため、現報告の虚偽ではない。追加負例案は上記。
   **DW-G05：局所判定除去による受理集合の拡大を現n12は検出しないが、登録済みM2〜M7の帰属は崩れない。**

3. **nit／保証限界：n10のskipと検査重複を併記する。**
   「3.11で走せばTryStar規則を保証できる」とは書かない。
   **DW-G05：TryStar専用拒否を削除しても現n10は拒否され続けるため、その規則やR2の順序の変異証拠にはならない。**

4. **nit：事前登録の時刻表記を照合可能にする。**
   s4見出しは22:55 JST、焦点走は22:19〜22:20、統合commitは22:22。改訂時刻なのか誤記なのか、この資料だけでは判別できない。実装後登録だったと断定はしない。
   **DW-G05：受理集合には影響しないが、時刻表記だけでは「実装前の事前登録」を追認できない。**

## 総括

scopeと最小形は裁定に沿い、報告・差分・実ファイルは概ね一致する。親の焦点走は66 passed／1 skipped／0 failedで、静的67 nodeと整合する。

変異受入前にM2／M4の期待集合を更新し、M1の旧新両走を別途証拠化する必要がある。n12とn10には規則単独の検出力がなく、そこまで保証したと報告してはならない。本レビューは静的検査のみで、変異成功・受入完了は主張しない。