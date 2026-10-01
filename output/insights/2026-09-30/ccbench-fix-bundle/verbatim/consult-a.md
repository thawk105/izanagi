## 所見

- **A1｜must-fix｜brief P1・plan §3｜根拠:** `s1-brief.md:25-26`、`plan.md:34-36`、`D2322-item4.md:5-7`。A は F と各 tip の差分から作り、B′は実際の束ねた tree から作るため、**merge と同じ手順を二度行う恒真の比較ではない**。ただし Cicada の修正 3 本は A と B′で同じ blob となり、A→B′の D297 比較には一度も入らない。Silo の先例は pin＋修正案と新 tip を比較していたが、今回は基点が F であり、C→F の合格を別証拠としてつなぐ構成である。**放置した場合:** 一次資料や push 依頼文が「D297 で Cicada 修正も検査した」と過大に主張する。**推奨:** F→各修正 tip の許容 hunk を独立した manifest に固定し、A の blob 照合と A→B′の D297 がそれぞれ証明する範囲を分けて記録する。

- **A2｜must-fix｜brief P4・plan §4 Cicada 正しさ｜根拠:** `plan.md:5,48`、`ccbench-cicada-bugfix/README.md:95-105`、`D2322-item4.md:5`。計画の既定 genome は `INLINE_VERSION_OPT=0` なので promotion の修正枝を通らない。YCSB K の 1 走だけでは delete と GC の修正枝の発火も示せない。判定器の巡回 0・integrity 0 は、この枝が未実行でも成立する。**放置した場合:** 束ねた tip の正しさの取り直しを Cicada の修正全体に拡張して報告する。**推奨:** 修正ごとに発火条件と計数方法を事前登録し、promotion を有効にした cell と delete・GC に到達する cell を加える。既存判定器の上限が `indeterminate` であることは維持する。

- **A3｜should｜plan §1 テスト｜根拠:** `plan.md:9-20`、`check_trace0_preprocess_identity.py:649-652`、`test_check_trace0_preprocess_identity.py:648-687`。予定する 32 件の件数確認と `SINGLE_EXEC` の負例は、既定値 1 文脈だけに縮める変異、および名前だけを既知にする単純な変異を殺せる。一方、16 値組合せのうち `SINGLE_EXEC=1` だけを含めて文脈を重複させる変異、他の値 macro の枝を落とす変異は、件数 32 のまま生存しうる。**放置した場合:** 検査器の「16 組合せを比較した」という一次資料の主張が偽緑になる。**推奨:** report の define 集合が 16 組合せ×2 overlay に厳密一致することをテストし、各 macro の既定値と反対側でだけ現れる TRACE=0 差分の負例を置く。

- **A4｜should｜brief P1・plan §2–3｜根拠:** `s1-brief.md:17,26`、`plan.md:28,34-36`、`check_trace0_preprocess_identity.py:565-652,1128-1135`。Silo の `#line` 6 本の一致は有用だが、TRACE=0 に影響する経路を尽くさない。A→B′は Silo `.cc` の include 活性と、変更された `trace.hh`・`ycsb.hh` の選定 consumer を検査する。一方、F→A に含まれる Cicada header と `.cc` は両側で同一のため、この比較からは評価されない。**放置した場合:** 束ねた branch の全 TU や全 header 効果まで同一性を確認したという主張になる。**推奨:** report には D297 の選定 context・consumer の範囲を明記し、F→A の Cicada 変更は hunk manifest と正しさ実走による別の証拠として扱う。

- **A5｜should｜plan §4 MOCC 正しさ｜根拠:** `plan.md:47`、`mocc-validation-fix/README.md:54-71`。48 thread・100 万 record・3 秒は先例と同じ cell だが、1 回の巡回 0 だけでは修理対象の割り込みが起きたとは分からない。先例の 112 走では修理後の `recheck_abort` と修理前対照の G2 を別に数えていた。**放置した場合:** 正しさの小走行が修理 X の効き目の再確認として読まれる。**推奨:** 1 走の合格範囲を判定器の観測結果に限定し、修理経路の発火を主張するなら `recheck_abort` 等の件数を別途事前登録する。

- **A6｜should｜brief P5・plan §6｜根拠:** `s1-brief.md:20,30`、`plan.md:63-72`、`gen-opt-gate-verifier/README.md:149-157`。約 3,300 秒は ycsb.hh を含む **GCC 11 の一例**で、同条件の GCC 12 完了実測はない。CI build の 33～51 秒も束ねた tip の所要を保証しない。**放置した場合:** 2.04～2.24 node 時間と各 job の walltime が実測済みの確定値として伝わる。**推奨:** GCC 12 と束ねた tip の単価を推定と表示し、投入前見積りと実績を別々に残す。

## brief・plan で正しいと確認した点

- plan は、祖先が重なる Cicada の 3 tip を個別に F→tip 差分適用できない点を正しく修正している (`plan.md:1-3,85`)。
- Cicada の値 macro を検査器内で 16 組合せとして列挙し、既定値を含め、`source_digest.py` を変更しない設計は妥当。実装時には未登録 macro の停止、比較 0 件拒否、Cicada 以外の 16 件／file を維持する必要がある (`plan.md:9-13`、`source_digest.py:345-351`、`check_trace0_preprocess_identity.py:1096-1125`)。
- Silo の `--require-gate-witness`、commit 件数照合、`serializable`・`certified` の事前登録は、計画された 2 workload の正しさ取り直しとして具体的である (`plan.md:46`、`gen-opt-gate-verifier/README.md:59-65`)。
- push を人間に委ね、bundle と最終 OID を記録する境界は依頼と一致する (`md_16.txt:24-26`、`plan.md:26-30`)。

## 総括

A→B′は merge による余分な TRACE=0 変化を検出できる独立した比較だが、**修正 hunk 自体、とくに両側に共通する Cicada 修正を D297 が認証する比較ではない**。その証拠範囲を明記したうえで、Cicada の修正枝の発火確認と 16 文脈の網羅テストを計画に加えるべきである。