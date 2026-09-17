静的検査のみ実施しました。**real 4 件、refuted 4 件**です。revS の実装・前処理・build は未実行であり、一致や green は確認していません。

以下、`B`＝[s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/s1-brief.md)、`P`＝[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/codex-artifacts/dev-wave-t2737-ss2pl-gate-controls/s2-plan.md)、`G`＝`orchestrator/campaign/condition_meaning_gate.py`、`R`＝`tools/pegasus/run_ss2pl_lock_study.py`、`Δ`＝`patches/ss2pl-lock-protocol-study.patch` とします。

1. **分類：骨抜き — real。tpcc の一致を「費用付きで成立」と扱ってはいけない。**

   根拠：B:26、P:383、G:1907–1912。owner は target ごとに選ばれ、YCSB 専用 define は YCSB target にだけ入る（Δ:49）。abort と common 宣言の差を workload 条件で消した tpcc の一致は、YCSB の一致を保証しない。D790 は「patch を当てただけでは baseline が動かない」ことを要求する（`docs/decisions.md:30350`）。D2120 項12の逐語:7–11も、stock 側 YCSB target/owner の問題を未解決としている。

   **影響：** shadow の green を採用根拠へ昇格すると、未検査の YCSB 経路を残したまま、対象を変えることで防壁を迂回した結論になる。

   **是正案：** P3 の「費用」を「D2120 の必要比較は未成立」に改める。T± は機構診断として残してよいが、insight・裁定案・台帳で「tpcc owner の比較成立」と「YCSB の採用条件未成立」を明記する。shadow admission を production の認証や certified 選択に流用しない。gate の変更・適用範囲縮小は不要。

2. **分類：正しさ境界 — real。空の `wfg.cc` でも現行 runner の不在検査は拒否する。**

   根拠：P:46、51 は無条件 source 追加を要求する。一方、R:353–354 は **source list 自体**を `_wfg_text_hits` に渡し、R:238–245 は任意の `wfg` を検出する。R:432–444 は `source_hits` があれば拒否する。したがって、完全な source population に `cc/ss2pl/wfg.cc` がある限り、空の object でも受理されない。親ディレクトリの改名では解消しない。

   また P:50 は `<cstdint>` と `<string>` を無条件 include にするため、「WFG 宣言が消える」と「前処理 TU が空」は同義ではない。`__FILE__`、symbol、binary strings の残留は別途未確認であり、source-list 拒否だけで計器コード残留まで断定もできない。

   **影響：** plain build 成功をもって性能 build の計器完全除去や runner 接続可能性を示すと、既存契約への確定的な抵触を落とす。

   **是正案：** S の plain build 材料に、既存 `_wfg_absence_evidence` の結果／例外を追加し、無加工の source population とともに保存する。source-list 拒否、binary・前処理の観測、D791 の完全除去条件を区別する。`wfg.cc` の除外・改名や検査緩和で通さず、現試作の採否上の障害として記録する。

3. **分類：監査可能性 — real。ただし欠陥は未実装 probe の受理条件の曖昧さ。**

   根拠：P:177 の「許可した行以外が byte 同一」だけなら、許可行内で `owner_tus`、`inert_values`、実行式まで変更できる。これらは実際に owner 選択・inert 分類を左右する（G:59–67、940–956、986–995）。P:183 の完全一致置換はよいが、**生成手順の制約と完成した shadow の検算条件を同一視できない**。

   import 案自体は妥当であり、固有名での `sys.modules` 登録は正準 gate の置換ではない。しかし P:172 の `__package__` と P:179 の所在地記録だけでは、正準 module・package 属性が前後で不変という検算にはなっていない。

   **影響：** logic bytes 同一という表示のまま登録内容を通じて判定意味が変わり、receipt の監査可能性が落ちる。

   **是正案：** shadow を実行する前に、固定した repo bytes から生成した **O/T+/T− の期待 bytes 全体との一致**を受理条件にする。変更可能なのは4 target の所定値、および T− の KIND companion の空 tuple 化だけとする。同じ許可行への `inert_values`・owner・式の混入を selftest の拒否例に加える。import 前後の正準 gate、`source_digest`、package 属性の object identity と実体 path も検算する。独自名の登録は明示して管理し、「`sys.modules` 無変更」とは称さない。

4. **分類：一般化 — real。親の「既存 pragma は両側に等しく出る」は未証明。**

   根拠：B:19。現行 patch は `rwlock.hh` の直接 include を外して wrapper を別位置に入れる（Δ:720–732）。さらに P:47–50 は標準 header の無条件 include を増やす。同じ compiler を使うことは必要だが、stock/patched の include 順序・初回展開位置まで一致させない。G:2621 以降も compiler 同一性と bytes 一致を別に判定する。

   **影響：** login の局所実験を計算ノードでの S 一致へ一般化すると、revS の成立見込みと採用材料を過大評価する。

   **是正案：** B:19 を login の観測事実に限定する。P:388–395 の実 compiler・実 TU による確認を維持し、親案の `g++ -E -P`＋`cmp` は前検査と位置づける。最終根拠は計算ノードの gate receipt とする。別 vendor の網羅試験は今回追加しない。

5. **分類：正しさ境界 — refuted。「DLR の数値 define 化や revS の stock 復元自体が不正な再実装」という主張は成立しない。**

   根拠：stock の5組は `#ifdef DLR0`／`#if DLR0` と `defined(DLR1)` の組合せである（`external/ccbench/cc/ss2pl/transaction.cc:172,263,309,411,436`）。所定の `-DDLR0`／`-DDLR1` と数値0／1の対応では、対応する分岐選択を保存できる。実際の出力一致は G:2674 以降の bytes 比較で確かめられる。**独立した stock を固定したまま patched 出力を一致させることは、inert 設計の目的そのもの**である。

   ただし現行 patch の `update()`、既取得ロック確認、`delete_record()` の `break` などの差は、分岐名の置換だけでは消えない（Δ:1634–1845、1913–1917、1990–2105）。

   **影響：** この疑いだけで revS を止める必要はないが、S の一致を非既定 arm や binary 全体の意味保存へ拡張すると誤る。

   **plan への反映：** stock の本文・配置を復元する範囲と、既存 study 経路を保持する範囲を固定する。S 一致は所見1の target 境界内に限定し、DLR=2、任意の marker 組合せ、runtime correctness の証明としない。

6. **分類：正しさ境界 — refuted。plan は4軸 admission を arm 全体の意味保証とはしていない。**

   根拠：R:831 は期待値生成、R:911–937 は compile entry の define 値の確認である。**供給値の束縛は確認するが、その組合せで各軸が実効を持つことは保証しない。** G:4068–4133 も request ごとの record を集約するだけである。P:385 はこの限界を明記している。

   KIND companion を外した場合、IMPL=0 下で KIND=0 が効かなければ G:2662 以降で拒否される。P:204 の予測もその拒否を残しており、既に隠してはいない。

   **影響：** この限界説明を落とすと、供給確認・個別軸の実効・arm 全体の意味・certified が混同される。

   **plan への反映：** 現行の区別を44 cell版にも維持する。T+ の phase1 と T− の S を一つの登録簿の成功として合成しない。新しい arm 意味検査や gate は今回追加しない。

7. **分類：恒真 — refuted。追加の1行変異 cell は必須ではない。**

   根拠：P:95–103、312–316 の abort 無条件除去版が、既に stock との差を作る対照である。revS/T−/S が一致し、対照版との差が abort ブロックだけなら、対照版の `stock-inert-mismatch` が要求された負例になる。G:2674–2710 は bytes 一致と残差を独立した stock に照らして判定するため、期待値を付けただけで green になる仕組みでもない。

   **影響：** revS が一致しないまま両版 red なら、abort 単独の検出実績とは言えない。

   **plan への反映：** 親案の既存4 cellを負例対照として明記し、2版差分が abort のみであることを検算する。revS の一致・対照版の残差を実測できなければ「負例対照未成立」とする。追加 cell は不要。

8. **分類：scope — refuted。revS への一本化・44 cell化自体には逸脱を認めない。**

   根拠：P:119 は stock 経路の復元対象を既に列挙し、P:121 の8群版先行は計画上の選択である。親案はその選択を変更するもの。runner 改修は実施項目に含まれず、P:377–385 の runner 言及は将来必要な変更層の記録である。

   **影響：** 旧60 cell・S red予測・旧 patch 名を残すと、receipt と台帳が別設計の結果として読まれる。

   **plan への反映：** author 着手前に revS、44 cell、期待 reason、selftest の件数、abort 対照の基底を一括更新する。「一致するまで」を新しい lock 意味論の追加許可にせず、固定した復元範囲で届かなければ残差を成果とする。

分類別の real 件数：正しさ境界1、骨抜き1、監査可能性1、一般化1、恒真0、scope0。

## 総括

- real は4件。最重要は、tpcc の一致では D2120 が要求する YCSB 比較は成立しない点。
- もう一つの確定的障害は、無条件 `wfg.cc` が現行 runner の source-list 検査に抵触する点。
- plan は上記を反映して続行してよい。現状のまま採用条件成立・certified へ進めることは止める。
- revS の bytes 一致を目指す行為自体は骨抜きではない。認証対象のすり替えが問題である。
- 追加の負例 cell は不要。既存 abort 対照を使える。
- 予算終了時も「tpcc 比較の結果」「YCSB 比較未成立」「runner 不在検査との衝突」を途中結論として残す。