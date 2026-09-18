静的検査と保存済み receipt の照合を行いました。変更・build・pytest・probe の再実行はしていません。

以下、`J`＝[job directory](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls)、`P`＝`J/probe/t2737_gate_probe.py`、`ΔS`＝`J/probe/patches/ss2pl-lock-protocol-study-define-only.patch`、`G`＝`orchestrator/campaign/condition_meaning_gate.py`、`R1/R2`＝`J/receipts/probe-result-{1,2}.json`。receipt の `supply` は `supply_canonical_json` を JSON として解釈した内容です。

1. **骨抜き：refuted — S 復元に新しい lock 意味論を入れた形跡はない。**

   現行／revS の差分と stock 本文を照合した。`update`、`delete_record`、既取得ロック検査、`unlockList` は stock の本文・配置への復元。DLR の5組も、正規の `-DDLR0`（値1）／`-DDLR1` と数値 `SS2PL_DLR=0/1` の対応では分岐を保存する。任意の `DLR0=0` や複数 marker の組合せまで同値とは言えない。根拠：stock `transaction.cc:172,263,309,411,436`、ΔS:576,707,969,1052,1129,1226。

   `rwlock.hh` の class 囲いも、define 未設定なら stock class を残す。SS2PL の define は target-private であり、d2pl の include をこの変更だけで壊す理由はない。根拠：ΔS:30–41,1357–1373、`external/ccbench/cmake/ProtocolHelpers.cmake:41`、`cc/d2pl/include/transaction.hh:10`。他 protocol の実 build 成功までは未確認。

   **影響：** 復元そのものを骨抜きとして却下する根拠にはならない。  
   **是正：** fix 不要。保証範囲を正規の define と検査した経路に限定する。

2. **骨抜き：real — 最終版について「phase1 前処理一致」とは書けない。**

   [局所検査スクリプト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/probe-t2737/work/check_phase1_projection.py:17) は include と pragma を除去し、6ファイルを個別に前処理する検査である。依存 header の展開、実 TU 全体、linked binary は射程外。

   最終 `phase1-source-review-f1.json` は transaction の `equal=false`。差は `insert()` の return を囲む stock の括弧だけで、他5比較と raw 3比較は一致。差分上、study lock・WFG 呼出しの変更は認めない。README:165–179 と fix1 報告はこの不一致を正しく開示している。

   **影響：** 旧 author 時点の一致を引用すると、最終版の検証結果を過大評価する。  
   **是正：** insight を「呼出し保持の局所確認。完全な bytes 一致は未達」に修正。これを隠すための patch 修正は不要。

3. **shadow：refuted — A3 の受理条件は実装され、正準 module の置換も認めない。**

   P:40–65 は固定4-entry blockから期待 bytes を生成し、候補**全体**との一致を要求する。P:421–433 の `inert_values`／owner／式／非SS2PL／logic の変異はいずれも期待 bytes と異なり、同じ `accept_shadow()` で拒否される。

   P:95–102,256–295 は固有 module 名を使い、正準 gate・package 属性・`source_digest` の identity と path を記録・比較する。R1/R2 とも `shadows` は9件、全件 `before==after`。R2 の保存済み9 shadow は、今回独立に組み立てた許可置換後 bytes とも全体一致した。

   **影響：** shadow による隠れた分類・owner・logic 変更を疑う根拠はない。ただし T± は target を変更した機構診断である。  
   **是正：** fix 不要。T± の結果を production YCSB 比較へ転用しない。

4. **receipt 整合：refuted — reason の転記不整合はない。予測差は以下で尽くされる。**

   R1/R2 の全90 cellで `observed_reason == supply.reason_code`。R2 の probe・3 patch・runner・gate の入力 SHA256 も現在の実ファイルと一致した。

   下表は `expected_reason != observed_reason` の**全 cell**。各行の prefix に列挙した各 axis と `.warm` を付けたものが cell ID である。略号は裁定どおり。

   | receipt | ID prefix | axis（全列挙） | 期待→観測 | 裁定との関係 |
   |---|---|---|---|---|
   | R2 | `revs.T-.S.` | impl, kind, dlr, wfg | I→M | 条件付き予測どおり |
   | R2 | `revs.T+.S.` | impl, dlr, wfg | I→M | 条件付き予測どおり |
   | R1 | `current.O.phase1.` | impl, kind, dlr, wfg | D/E/A/D→P | 予測外。warm-up 前提不成立 |
   | R1 | `revs.T-.S.` | impl, kind, dlr, wfg | I→P | 同上 |
   | R1 | `revs.T+.phase1.` | kind | E→P | 同上 |
   | R1 | `revs.T-.phase1.` | impl, kind, dlr, wfg | E/B/E/E→P | 同上 |
   | R1 | `abort-unconditional.T-.S.` | impl, kind, dlr, wfg | M→P | 同上 |
   | R1 | `revs.T+.S.` | impl, dlr, wfg | I→M | 条件付き予測どおり |

   R2 は7件の表面的不一致がすべて条件付き予測内。R1 は20件中17件が helper 内部例外による前提不成立、3件が条件付き予測内である。

   両 receipt の11 family中、`["revs","O","phase1","warm"]` だけ `admitted=true`、残り10件は false。全 cell の meaning は `unestablished / meaning-witness-undeclared`。

   dispatch は job 1＝5036.nqsv／bnode022／rc=1、job 2＝5051.nqsv／bnode048／rc=0。ログの request・rc と、対応する `compute-visible.json` の node・PBS ID が一致する。

   **影響：** R1 の P を設計の反証として数えると誤る。また「plain build 後16 cell」は正確には**20 cell**。16件は期待 reason と完全一致、残る4件も条件付き予測を含め有効である。  
   **是正：** insight の件数・失敗分類を上記に合わせる。probe fix は不要。

5. **規律：refuted — gate 緩和や WFG TU の無条件混入は認めない。**

   試作に `#line` はなく、shadow に inert 値追加もない。非YCSBへの stock 復元は明示した分岐であり、検査対象の外へ隠した変更ではない。YCSBでは abort 増分の else が消え、現行どおり workload が所有する（ΔS:501–505）。

   CMake の `wfg.cc` は引き続き `CCBENCH_SS2PL_WFG_DIAG EQUAL 1` の条件付き（ΔS:20–23）。R1/R2 とも S／phase1 plain build は rc=0、S の `builds.S.wfg_absence.accepted=true`。検査対象は3 TUで、`wfg.cc` を含まない。既存契約が許す軸表示文字列は残る。

   **影響：** build成功と「計器TU不在」は支持されるが、runner 全契約の受理までは意味しない。  
   **是正：** fix 不要。「WFGという文字列が一切ない」とは書かない。

6. **規律：real — revS は現行 runner の abort 所有権契約に拒否される。**

   R1/R2 の `static_contracts.revs.abort_ownership.accepted=false`。理由は transaction 増分1、workload 増分2。無条件除去版は true、study header 検査は両版 true。YCSB前処理では消える増分も、現行の静的契約では数えられる。

   **影響：** 「4軸 green＋plain build成功」から runner 接続可能・採用可能へ進めない。  
   **是正：** insight に既存の障害として明記。本レビューを理由に validator を緩めない。試作診断の完了には追加 fix 不要。

7. **主張検算 (i)：real — 非 inert 4軸は登録簿変更なしで supply green。**

   根拠：R2 `cells[id=revs.O.phase1.{impl,kind,dlr,wfg}.warm].supply` は全件 `green / requested-default-preprocess-different`。対応 family は raw-measurement で admitted=true。O の gate bytes は repo と同一。

   **影響：** patch層だけで個別軸の供給実効障害を解消した材料になる。  
   **是正：** 「warm staging・phase1 の個別軸 supply」に限定して採用可。runtime meaning、arm全体、certified の成立とは書かない。

8. **主張検算 (ii)：real — T−でも S は不一致、差分行数は1。**

   根拠：R2 `cells[id=revs.T-.S.{impl,kind,dlr,wfg}.warm].supply` は全件 M、`evidence.root_diff_line_count=1`、`root_diff_has_residual=true`。T+ の IMPL/DLR/WFG も同値。

   `ERR` の `__LINE__`＝97→154という内容の特定は、README:187–205 の保存済み login diffとソース差分が根拠。**計算ノード receipt の行数だけでは、その1行の内容までは特定できない。**

   **影響：** 残差縮小は支持されるが、stock一致の成立材料にはならない。  
   **是正：** 「computeでも差分1行。login diffでは ERR の行番号差」と証拠を分けて書く。

9. **主張検算 (iii)：real — job 2では helper 1回後に両木の前処理が成立。**

   根拠：R2 `warm_up.status=complete`、`before.exists=false`→`after.exists=true`。pristine 8件はすべて Pで、`supply.evidence.detail` に `config.h` 不在がある。helper後・plain build前の `revs.T-.S.*.warm` が Mまで到達し、requested／stock双方の前処理結果を持つ。

   R1 は `warm_up.status=internal-exception`、前後とも config.h 不在であり、この主張の根拠に使えない。

   **影響：** staging準備が前処理失敗を解消する実測材料になる。  
   **是正：** job 2・今回の共有 staging 構成に限定して記載。全cellが greenになったとは書かない。

10. **主張検算 (iv)：real — 無条件除去版の差分行数は大きい。ただし因果対照の成立とは別。**

    根拠：R2 `abort-unconditional.T-.S.*.warm` は M、`root_diff_line_count=218`。revS は1。`abort_patch_pair.accepted=true` と `applied_pair_only_abort` に加え、保存済み適用木でも差が abort の5行ブロックのみと確認した。

    G:2395–2452 は行位置を揃えて数えるため、1行削除による後続行のずれも数える。218は意味変更の箇所数ではない。

    **影響：** 残差増大の対照にはなるが、revSもredなので「abort除去だけでgreen→redを検出した」とは言えない。  
    **是正：** 「両版red、差分行数1対218。abort単独の判定反転は未成立」と書く。

11. **主張検算 (v)：real — 必要な stock YCSB owner比較は未成立。**

    stock `cc/ss2pl/CMakeLists.txt:1–7` は workloads が bomb／tpccのみ。R2 `revs.O.S.{impl,dlr,wfg}.warm` は `owner-tu-unresolved`、detail は target内owner entry `count=0`。KINDは companion による `configure-failed` が先行する。

    **影響：** T±のTPCC比較を D2120 の必要比較の代替にできない。  
    **是正：** insight冒頭に「固定したstock・現行gateでは必要比較未成立」と明記。4軸すべてが owner-tu-unresolvedだったとは書かない。

## 総括

- real 7件：要注意事項2件（2・6）と、限定付きで支持する予定主張5件。骨抜き・shadow改変・receipt転記不整合は認めない。
- 最重要は、stock YCSB比較未成立と現行runnerのabort所有権拒否。採用条件成立とは書けない。
- 試作診断を完了する追加コードfixは不要。insightの限定・件数・検証表現の修正は必要。
- 記載可：warm後の4軸supply green、S残差1行、helper後の前処理成立、abort版の差分行数増大。
- 記載不可：最終phase1 bytes完全一致、S一致、abort単独のgreen→red対照成立、runtime meaning／certified成立。
- job 1のplain build後は16件ではなく20件。job 2を主資料とする。