## 所見

1. **must-fix — 小型 fixture が production 専用 configure 経路につながらない。** plan は `_v2_commands` を configure argv の生成元としつつ、別の小型 CMake project で header 分岐を実走させるとしている（`s2-plan.md:24,42`）。現行テストの合成 repo は最小限の `cmake/Options.cmake` 等しか持たない（`test_check_trace0_preprocess_identity.py:110–130`）。このままでは fixture が新分岐に到達できず、受入条件を検証できない。**直し方:** production の configure 選定と、compile database 以降の検査を分ける。fixture には小型 project の configure argv を渡す狭い seam を設け、依存列挙・TRACE 確認・前処理比較は実 cmake・実 g++ で走らせる。

2. **must-fix — 比較予定集合が承認済み R4 の集約規則と食い違う。** R4 は同一 `(entry, argv)` の比較を 1 回に集約する（`README.md:62`）が、plan は `(compiler, configure, entry)` を予定集合として全 configure で比較すると書く（`s2-plan.md:26,32`）。放置すると同じ比較の再実行で所要が増え、規則 v2 の実装にもならない。**直し方:** 依存列挙は各 configure の全 entry・両 side・両 TRACE 値で維持し、比較だけを正規化済み `(entry, argv)` で集約する。report には、その比較が属する configure を列挙する。

3. **should — 0.52 node 時間は新検査器の実測単価ではない。** 生死確認は 3 構成だけで、TRACE 実効値は `#define TRACE 0` の **21/21** 件を確認した（`s1-live-summary.md:5,13,18`）。plan が求める各 consumer・各 side の TRACE=0/1 確認（`s2-plan.md:9,30`）と、全 34 対の所要は未測定である。放置すると 2 node 時間の確認線を誤判定しうる。**直し方:** 0.52 を暫定外挿と明記し、追加の TRACE=1 確認、tree 照合、配置、後片付けを含む 1 対の実費で投入前に見積り直す。

4. **should — 計算 job の実行条件が未確定。** plan は 1 job、scratch・offline cache・dependency prefix を指定するが、配置済み source と依存 prefix の検証、scratch 容量、job の時間枠、並列上限を具体化していない（`s2-plan.md:16,22,36,60–64`）。生死確認の 48 並列依存列挙・8 並列比較は 48 core node の 3 構成での値に限る（`s1-live-summary.md:3,12,15`）。放置すると途中で時間切れや配置不足となり、完了条件の結果・実費を得られない。**直し方:** 既存の hydrate と生死確認 driver の手順を使い、投入前に cache、prefix、compiler、scratch、時間枠を確認する。まず実測と同じ構成内並列度で走らせ、構成間の同時起動は必要になった場合だけ調整する。

5. **should — 実 CCBench の負例を通常 test に置くと受入時間を圧迫する。** `test_real_ccbench_h_line_negative` は実 source・生成物・計算ノードを要する（`s2-plan.md:56`）。通常 suite の小型 fixture と同列に置けば、5 分枠と実行場所が不安定になる。さらに commit OID で検査する現行 API（`check_trace0_preprocess_identity.py:651–675`）では、checkout を一時編集しただけの負例を新分岐経由で検査できない。**直し方:** 通常 suite は小型 fixture に限り、実 CCBench 負例は計算 job 内で別 commit を作る一回の焦点走として扱う。

## 削れるもの

- **should:** 既存の決定的 report test は stdout の二回一致を既に確認する（`test_check_trace0_preprocess_identity.py:219–226`）。plan の追加 stdout bytes 回帰（`s2-plan.md:40`）は、header 入力を付けない既存 test の維持で足りる。固定 snapshot を増やすと保守負担が増える。
- **should:** `--cmake`、cache、prefix、scratch を常に一組で CLI に要求する案（`s2-plan.md:16`）は引数が多い。header 分岐の明示的な有効化は保ち、計算 job が確定できる値は job 側で解決して渡す。検査器には検証に必要な実パスだけを受けさせる。
- **should:** report の「比較 digest」は既存の `_comparison_evidence` が値と旧新 digest を作れる（`check_trace0_preprocess_identity.py:248–264`）。header 専用の独立した digest 機構や schema 変更は不要（`s2-plan.md:34`）。選定集合・実行件数など R4 が要求する証拠に絞る。
- **nit:** plan の失敗 fixture 一覧（`s2-plan.md:44`）は、既存拒否の再演と新分岐の固有リスクが混在する。A/D/R/C・mode・非 C/C++ の拒否は既存 test（`test_check_trace0_preprocess_identity.py:708–738`）を維持し、新しい変異登録に重ねない。`#4` の生成失敗と `-MG` 偽緑は、plan 自身の指摘どおり別の理由として検証する（`s2-plan.md:53,58`）。

## (P1)〜(P8) への意見

- **P1:** 明示的な有効化と従来の header 拒否文言は維持。ただし五つの必須 CLI 引数という形までは支持しない。
- **P2:** 維持。GCC ごとに configure する必要がある。
- **P3:** `_v2_commands` の再利用は実 CCBench に適する。合成 fixture まで同経路に固定する点は覆す。
- **P4:** 選定規則は維持。比較の同一 `(entry, argv)` 集約を plan に戻す必要がある。
- **P5:** 別 configure を作らない方針は維持。生死確認が実測した TRACE 実効値は 0 側だけなので、1 側の成功を既成事実にしない。
- **P6:** masstree の隔離は維持。既存 hydrate と生死確認手順を再利用する。
- **P7:** 実 cmake・実 g++ は維持。production configure を fixture に強制せず、実 CCBench 負例は通常 suite から分ける。
- **P8:** `.cc` だけの report bytes 維持は妥当。新しい schema や専用 digest 機構は要らない。

## 総括

規則 v2 の比較範囲を削らずに前進できる。先に直すべきは **fixture の configure 接続**と**同一比較の集約**である。生死確認は実行可能性を強く示すが、TRACE=1 の実効値、全 34 対の所要、改訂後の検査器による C → C2′ の判定までは証明していない。今回は指定どおり静的検査のみ行った。