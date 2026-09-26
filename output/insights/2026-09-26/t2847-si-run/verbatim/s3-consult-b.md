## 所見

**B-01 — must-fix：V28 を未実走のまま完了扱いにできない。** 依頼は V28・V29・V36 の実走を明示している。一方、plan は V28 の build・run を投入しないとしており、検出表の1行が E から実測分類へ進まない。根拠: `request.md:1-7`、`s2-plan.md:11-19,65,69`。**成果物への影響:** V28 行の値と分類が欠ける。**推奨:** 可視性の status 除外だけを切り替える局所 patch を作り、事前登録後に使い捨て binary で実走する。SIGSEGV・停止・verdict のいずれも結果として分類する。V07 でも異常終了を「別の層で検出」と記録している（`output/insights/2026-09-23/t2847-sort-nonswo/README.md:14-20,97-103`）。未完成 body の読みは実在する危険だが、それを理由に行を消すのは依頼の縮小である（`external/ccbench/cc/si/transaction.cc:287-292`）。

**B-02 — should：V28 の危険経路を、今回の workload で同列に扱いすぎている。** YCSB の実行ループは READ・WRITE・READ_MODIFY_WRITE だけで、INSERT・DELETE を生成しない（`external/ccbench/include/ycsb.hh:117-147`）。したがって abort INSERT による `Tuple` 削除は今回の K/W では到達根拠にならない。GC の版再利用と、公開後に body を代入する順序は残る（`external/ccbench/cc/si/garbage_collection.cc:82-99`、`external/ccbench/cc/si/transaction.cc:287-292`）。**成果物への影響:** V28 を除外する根拠と、異常終了時の原因分類が不正確になる。**推奨:** 到達可能な危険だけを記し、異常終了の原因は実測なしに特定しない。読んだ版の stamp は trace 出力時に再読するため、orphan が出なくても可視性違反の不発とは判定しない（`external/ccbench/cc/si/transaction.cc:541-544`、設計書 `§4.5:218`）。

**B-03 — should：条件 gate 登録は経路選択に従属させる。** 既存 gate に新 macro を通すなら、spec・witness・site 数と追随表の更新は実際の admission に必要で、単なる仮想防壁ではない（`condition_meaning_gate.py:79,347,473`、`s2-plan.md:46-52`）。こちらが D2239 の新規変異と mocc の先例に最も合う（`docs/decisions.md:72043-72047`、`output/insights/2026-09-26/t2847-mocc-run/README.md:27-28,34-38`）。repo 外起動器から直 CMake で `-D<macro>=1` を渡す方が差分は軽く、gate の判定自体も変えない。ただし D2239 項5の直 CMake **でも gate は通している**ため、gate 省略の先例とは言えない。**成果物への影響:** 省略経路では build の供給意味が gate で確認された受理集合とは主張できない。**推奨:** 先例と同じ供給確認を成果物に求めるなら登録する。直 CMake を選ぶならその限定と実コンパイル定義を記録する。どちらの場合も、repo の `patches/` に裸の `IZANAGI_` macro patch を置くなら、未登録 patch は既存テストの path 別 allowlist に追加する必要がある（`test_p3_s4_loop.py:8490-8524`）。gate 登録だけではこのテストの登録済み判定にならない。

**B-04 — should：W の「巡回が構造的に出ない」は条件付きの命題に直す。** L0 の W t1/t4 は R=0・巡回0だったが、これはその2走の観測である（`liveness.md:17-21`）。R が0で、版 ID が一意かつ commit 順のままなら、残る ww 辺は前向きで巡回しない（`orchestrator/verifier/dsg.py:915-925`）。V28 でも W の R が0になることや、変異時に版の前提が保たれることまでは L0 が証明しない。**成果物への影響:** W の I を無条件の「盲点」と数えると、発火・trace 完全性・版異常を取り違える。**推奨:** V29 の W は `changed>0`・`committed>0`、R=0、期待層 counter=0、対照正常を確認した走だけ「発火したが巡回で観測できない」とする。診断が無ければ「発火未確認の I」とする（`s2-plan.md:30-36`）。

**B-05 — should：全 build に K/W × t1/t4 を掛ける設計は削れる。** L0 は V36 の K t4 で巡回を、W 両条件で R=0 を観測した（`liveness.md:15-18`）。V29 の同一 key 競合には W t4、V28 の汚れた版を読む機会には R が残る K t4、V36 には K t4 が焦点となる。K t1 と W t1 は低競合・対照の補助にはなるが、3行を埋める必須 cell ではない。V28 に W を全面適用する理由も弱い。**成果物への影響:** cell を増やしても主分類を強めず、計算と解釈だけが増える。**推奨:** 各行の主 cell と同 job・同 cell の V2 対照を先に固定し、補助 cell は発火不成立など具体的な欠落が出た場合だけ追加する。V29 の K t4 は対照自体が N になり得るため、そこで出た N を変異の検出に帰属しない（`parent-position-s3.md:6`）。

**B-06 — should：事前登録は L0 と本走を明確に分ける。** L0 は期待表を確定する前の探索走である（`liveness.md:22`）。plan の表は V28 を実走対象外とするため、依頼の3行を対象にした投入前の期待・分類規則になっていない（`s2-plan.md:25-36`）。**成果物への影響:** V28 の crash・停止・I・N を事後解釈する余地が残り、V36 の L0 値を事前登録後の実測と取り違える。**推奨:** V28 を含む主 cell、発火診断、対照異常時、異常終了時、verdict と integrity counter の優先順を投入前に固定し、V36 は本走でも取り直す。V36 は無改変 si の巡回検出または巡回未観測であり、certified にはしない（設計書 `§4.5:216-218`）。

**B-07 — nit：計算見積りは2 node 時間未満が妥当だが、plan §4だけでは総額を示さない。** L0 は1 build・4 run で36秒と64秒。plan の2 job は概算2～6分だが、変異 matrix・焦点走・受入を含まない（`liveness.md:7-11`、`s2-plan.md:40-44`）。brief の上側で足すと、生死確認200秒＋本走900秒＋焦点300秒＋matrix 1,400秒＋受入1,800秒＝**4,600秒、約1.28 node 時間**（`brief.md:28`）。先例の mocc は計測・焦点・matrix で2,898秒、受入前だった（`output/insights/2026-09-26/t2847-mocc-run/README.md:21`）。**成果物への影響:** 現見積りでは依頼の確認閾値2時間に届かないが、再走や受入失敗を無制限に含める根拠もない。**推奨:** 投入直前に予定 job の Elapse 合計を更新し、2時間以上になった場合だけ依頼どおり確認する（`request.md:8-9`）。

## 削れるもの・足りないもの

| 対象 | 判断 | 成果物への関係 |
|---|---|---|
| si v2 patch、V28/V29 patch | 必要 | 3行の E を実測値へ変える本体。v2 は L0 で受理済み（`liveness.md:20`）。 |
| V28 の実走と事前登録 | **不足** | 現 plan では1行が未実走のまま（`s2-plan.md:19,32`）。 |
| 発火診断 | V28/V29 に必要 | I と未発生・盲点を分ける。D2239 の先例（`docs/decisions.md:72045-72050`）。 |
| repo 外起動器 | 局所拡張が必要 | 既存の V2 起動器は macro build を拒否する（`launch_si_run.py:105-108,277-279`）。汎用 driver 化は不要。 |
| 条件 gate 登録と追随表 | gate 経路を採る場合のみ必要 | 先例に沿う供給確認。直 CMake なら省けるが、gate admission 済みとは書けない。 |
| 裸マクロ patch の allowlist | gate 経路でも必要 | 既存テストは patch ledger または path 別許容集合を見る（`test_p3_s4_loop.py:8490-8524`）。 |
| 全 build の K/W × t1/t4 | 縮小可能 | 主 cell と対照を優先。補助 cell は具体的な発火不足が出てから。 |
| 新しい gate・検査・一般化・台帳 | 不要 | 依頼の scope 外で、検出表の値を改善しない（`request.md:10`、`docs/dev-wave/core.md:82-88`）。 |
| insight と受入 | 必要 | 3行の観測、分類、受理範囲を残す。実装差分がある wave の既存手順に従う（`docs/dev-wave/core.md:97-107`）。 |

## 総括

最優先の修正は **V28 を実走計画に戻し、3行すべての期待と分類を投入前に固定すること**。V28 の危険は結果の限界として扱い、異常終了も分類する。条件 gate 登録は先例に最も忠実だが、登録するなら実際にその経路で build する必要がある。cell は主目的に絞れ、現資料からの計算見積りは約1.28 node 時間で、2時間の確認閾値未満である。今回は指定どおり静的検査のみで、テスト・build・実走はしていない。