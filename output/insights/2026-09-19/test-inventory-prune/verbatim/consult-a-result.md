## 所見

以下、`plan.md` は指定された段2成果物、`inventory.*` は指定された scanner 成果物を指す。静的検査のみ実施し、ファイル変更・pytest・変異実走は行っていない。

1. **refuted / should — 唯一の削除候補で検出力が失われる疑い**

   **位置:** `orchestrator/tests/test_s8b_holdout_freeze.py:2381`、`orchestrator/tests/s8b_v2_freeze_fixture.py:737`、`orchestrator/tests/conftest.py:765`

   削除対象と残す `[min-to-max]` は、同じ関数へ同じ型の `True` を渡す。各 invocation は `tmp_path` 配下に新しい Git repository を作り、同じ helper・module 定数・assertion を使う。autouse fixture は環境と出力 root の状態を隔離しており、対象 id による分岐や、3回目だけを検査する共有状態は見つからなかった。

   **推奨処置:** 重複1件に限定する方針を維持する。静的同等性は支持できるが、変異 pre/post の成立とは分けて記録する。

2. **real / should — scanner の AST 同一判定は削除根拠にならない。ただし plan は対処済み**

   **位置:** `orchestrator/tests/test_s6_sort_sweep.py:79`、`orchestrator/tests/test_s8a_trigger_sweep.py:86`、`plan.md:169`

   同一本文の `inspect.getsource(W.run_sweep)` は、異なる production module の実装を検査する。本文 AST の一致から受理集合の一致は導けない。また、`True`・`1`・`1.0` の値比較による重複判定も型境界を消す。

   **推奨処置:** B1全7組と、型が異なるB2の26行を保持する現案を維持。scanner の件数を「削除可能件数」として再利用しない。

3. **real / should — Aの「対象不在」とCの「機構撤回」に誤検出がある。ただし誤削除案はない**

   **位置:** `orchestrator/tests/test_related_work_search.py:1585`、`orchestrator/tests/test_campaign.py:10615`、`orchestrator/campaign/layout.py:375`

   Aの代表は実在する `tools/run_axis3_search.py` を subprocess で呼び、CLIを検査している。Cの唯一の候補も現存 resolver を直接実行する。production は `layout.py:403` で現在も `reject_worktree_container=False` を渡す。決定の一部分の supersede は、この経路の撤去を意味しない。

   **推奨処置:** A/C削除0件を維持。本相談ではA全112件を独立に再確認したわけではないため、plan の全件確認を独立監査済みとは報告しない。

4. **real / should — Dには正しさ gate を実行する test が混入している**

   **位置:** `orchestrator/tests/test_s8c_preregistration_invariant.py:723`、`plan.md:311`、`plan.md:346`、`plan.md:380`

   この代表は docs bytes の固定比較ではなく、読取へ異常を注入して `check_docs.main()` を実行し、拒否と診断を確認する。本番 gate の負例である。plan はこの誤分類を認識しているが、291関数中246件は個別未確認のまま。

   **推奨処置:** 291関数・356 node・225.392秒を「確定D」として裁定に渡さず、scanner候補数として表示する。全件保持は安全側であり、今回の削除候補への誤混入は認めない。

5. **refuted / should — 対象 node の登録簿・literal pin の見落とし**

   **位置:** `plan.md:371`、`tools/update_acceptance_duration_ledger.py:21`、`orchestrator/tests/conftest.py:1584`、`orchestrator/tests/conftest.py:1803`

   対象関数名・idを `orchestrator/`・`tools/` で検索し、duration 台帳以外の名指し参照は見つからなかった。対象 suite は凍結8 suite に入らず、campaign_lock の loader path、check_docs の literal、他 test の golden に対象を束縛する参照も見つからない。

   duration consumer は台帳自身の件数整合を確認し、収集された item ごとに値を参照する。削除済み node の余剰 entry と collection の完全一致は要求していない。したがって、この consumer について「削除には台帳編集が必須」という疑いは反証できる。

   **推奨処置:** 台帳を変更しない現案を維持。`output/` 内の過去の変異結果・collection記録にも対象文字列はあるが、歴史的記録を追随編集しない。

6. **refuted / should — M1/M2の anchor 不成立・残存 test 不在・対象 fixture の drift mask**

   **位置:** `orchestrator/campaign/s8b_holdout_freeze.py:1981`、同`:1983`、同`:2078`、`orchestrator/tests/test_s8b_holdout_freeze.py:2403`、`orchestrator/tests/s8b_v2_freeze_fixture.py:759`

   M1・M2・E1の `old` はそれぞれ file 内で1箇所だった。M1/M2は earliest selection の拒否を通過させ、残存2 node の `pytest.raises` が要求する挙動を変える。単なる診断文変更ではない。対象3 idはASCIIで、変異自体も待機やループ継続を追加しない。

   対象 fixture は変異後の script を一時 repository に複写して commit するため、元 repository の HEADとの差だけで対象 node が赤くなる構造ではない。

   **推奨処置:** 静的検出予測として採用可能。ただし、`plan.md:216` の20 file全体について、非ASCII失敗 node・別層拒否・source同一性による赤の不存在までは確定していない。`plan.md:299` の条件を維持し、E1の失敗や drift 由来の赤を検出力保持の証拠へ混ぜない。D334に照らし、別層拒否が残る場合は単独変異の成功と数えない。

7. **refuted / should — 規律2の test を共有 fixture・helper・import 経由で弱める疑い**

   **位置:** `plan.md:367`、`plan.md:369`、`orchestrator/tests/test_s8b_holdout_freeze.py:2381`

   現案は decorator の重複入力と対応idだけを除く。関数・module・fixture・helper・import は残り、共有定義の削除や import 副作用の消失は生じない。対象自身は正しさに関わる拒否検査だが、同じ入力の検査が残る。

   **推奨処置:** この2行以外の整理を同時に行わない。規律2の評価は、ファイル除外リストへの所属だけでなく、上記の同等性と変異結果で行う。

## 親 brief への所見

1. **real / must-fix — 台帳値・collection数・実測時間の母集団を分離する。**

   **位置:** `brief.md:3`、`brief.md:4`、`brief.md:16`、`inventory.json:16`、`inventory.json:102`

   現台帳は **24,379 entry・17,958.848秒**で、4.99時間への換算自体は正しい。一方、scanner の collection 入力は **25,381 node**、発見 file は **363**で、brief の391 fileとは一致しない。scanner対象では949 nodeの台帳値が欠落し、集計上0扱いになっている。

   **推奨処置:** 各数値の取得時点・対象範囲を明記する。「放置時は受入 worker 時間4.99 hが維持される」は、現行受入の実測としては根拠不足。33秒は削除対象の過去の台帳値であり、削除後の実測短縮量ではない。

2. **refuted / should — P1は今回の限定削除には妥当。**

   **位置:** `brief.md:9`、`plan.md:371`

   登録簿や凍結台帳を変更しないための保守的境界として整合する。ただし、未登録であること自体は検出力同等性の証明ではない。今回の対象は別途、入力・fixture・本文の同等性で支持される。

3. **real / should — P2/P3には未確定事項が残る。**

   **位置:** `brief.md:10`、`brief.md:11`、`plan.md:380`

   P2の並行所有範囲は本相談の指定資料だけでは確定できない。P3の二段方式は妥当だが、Dの代表確認を全件意味分類へ一般化できない。

   **推奨処置:** author前に所有範囲を確定し、Dは確認済み・未確認を分けた裁定資料にする。

4. **real / must-fix — P4の有限変異を「検出力喪失なし」の一般証明にしない。**

   **位置:** `brief.md:8`、`brief.md:12`、`plan.md:303`

   2〜3個の変異で前後の失敗集合が一致しても、あらゆる欠陥に対する検出力の一致は証明できない。今回の主根拠は同じ test invocation の重複であり、変異はその裏取りである。また「moduleをimportする全file」は意味上の全consumer集合でも、drift maskを除いた集合でもない。

   **推奨処置:** 主張を「静的同等性を確認し、登録変異について残存検出を確認」に限定する。実走前にrunner集合と帰属判定を確定する。

## 総括

**重複 `True` 1件の削除案に、静的検査で具体的な検出力喪失や必須pin破壊は見つからなかった。** A/B1/Cの保持判断も支持する。

修正が必要なのは、親 brief の数値の母集団と、有限変異からの保証の一般化。削除の確定には、既にplanが条件としている変異pre/postの成立、失敗理由の帰属、並行所有範囲の確認が残る。現時点でKILLEDや受入緑は報告しない。