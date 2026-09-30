## 所見

**B01｜must-fix｜plan「生死確認」**  
根拠: `plan.md:117–130`、`gen-opt-correctness-gate/README.md:134`。F の素の build と U1 tip の比較では、刻印だけでなく Q/V 記録も同時に変わる。設計資料が求める「刻印あり／なし」の影響は分離できない。  
放置時の成果物: README の commit・abort 差を刻印の観測者効果として解釈できなくなる。  
**推奨: 局所修正に置き換える。** 同じ Q/V 計装で刻印だけを切り替えた比較を一回行う。F との比較を残すなら、計装全体の参考値と明記する。

**B02｜should｜plan「API と D5」、brief (P4)**  
根拠: `plan.md:4,87–89`、`md_14.txt:20–25`、`model.py:183–201,233–265`。今回の実走は CLI であり、capability と source snapshot の schema 更新、fanout の再水和まで今行う必要は示されていない。D5 の header 証拠は必要だが、既存の証拠面の走査を局所的に広げられる。  
放置時の成果物: 今回の受理集合を変えずに snapshot と既存 campaign の互換面だけが増え、変更・検査範囲が広がる。  
**推奨: 局所修正に置き換える。** 今回は verifier と CLI の要求指定、既存 `ProofSurfaceAssessment` を使った header 照合に絞り、capability 経路は U5 の接続時に実物で確認する。

**B03｜should｜plan「結果と証拠面」**  
根拠: `plan.md:83–85`、`model.py:475–519`、`report.py:112–137`。D1/D2 の違反計数は判定に必要。一方、計数・位置付き notes に加えた別の機械可読詳細投影が、今回の採否をさらに変える根拠はない。  
放置時の成果物: certified の集合は変わらず、結果 schema と receipt digest の変更だけが増える。  
**推奨: 局所修正に置き換える。** 既存 `Integrity` の計数と、txid・key を含む上限付き notes を先に使う。

**B04｜should｜plan「照合順・発生条件」**  
根拠: `plan.md:48–83`、`gen-opt-correctness-gate/README.md:148–150`。発生条件が 0 の実走を採用しない判断は事前登録した実験側の仕事であり、plan 自身も verifier の certified 条件に入れないとしている。全種類を production 結果へ恒久的に載せる必要は未証明。  
放置時の成果物: 判定の受理集合は変わらず、結果 schema と実装量が増える。  
**推奨: 局所修正に置き換える。** D2b(i)/(ii) と B1 の採否に使う件数だけを実走記録で確保し、残りは [T-2889] の本走で追加する。

**B05｜should｜plan「U1 の計画」、brief (P2)・(P3)**  
根拠: `plan.md:16–32`、`s1-brief.md:28–29`、`md_14.txt:17–19`。共通 `run` から Silo だけが Q を出す制御は必要だが、全 protocol の `id_` 利用調査と恒久的な thread local 有効化・pending txid 機構の細部まで先決めすると、Silo の実際の commit 経路より設計が大きくなる。  
放置時の成果物: 今回の D1/D2 受理集合は変わらず、TRACE 計装の変更面と故障点が増える。  
**推奨: 局所修正に置き換える。** Silo の YCSB 経路と共有 header の consumer を確認し、Q と C の一対一および txid 欠落の赤を満たす最小の受け渡しにする。R/W/M の記録、V、TRACE=0 復元は残す。

**B06｜should｜plan「生死確認」**  
根拠: `plan.md:119–130`、`gen-opt-gate-liveness/README.md:62–72,158`。U0 照合器は trace parser を production と共有する。全 archive に対する必須の二重確認は独立検証ではなく、D2a・D5 も確認しない。  
放置時の成果物: README が「独立に全検査を照合した」と読める一方、共有 parser の誤りは残る。  
**推奨: 局所修正に置き換える。** U0 は D1/D2b の代表的な照合と件数差の診断に使い、production の fixture・変異 test を主証拠にする。

**B07｜must-fix｜plan「test と変異」**  
根拠: `plan.md:95–113`、`md_14.txt:22–23`、`gen-opt-correctness-gate/README.md:180–191`。表は「殺す変異」を列挙しているが、判定器の比較を一つずつ実際に外して各 test が赤になる実施手順と記録がない。  
放置時の成果物: B1〜B7 fixture が緑でも、条件を削った判定器を拒否できるという成果物の主張が未検証になる。  
**推奨: 局所修正に置き換える。** D1、D2a、D2b、到達可能性、D5 を一条件ずつ外し、対応 test の失敗を記録する。

**B08｜should｜plan「test と変異」**  
根拠: `plan.md:107–113`、`md_14.txt:22`、`cli.py:76–79,105–110`。欠落・破損の test 案はあるが、要求時の gate 全欠落、部分欠落、読取不能で `certified=false` かつ CLI が失敗するという fail-closed の受入を明示していない。  
放置時の成果物: 入力不在を「検査なし」と扱う経路が残れば、受理集合に無証人の実行が混ざる。  
**推奨: 局所修正に置き換える。** この三条件の verdict と CLI 終了値を直接固定する。

**B09｜should｜plan「意味版と再検証」、brief (P5)**  
根拠: `plan.md:5,91`、`md_14.txt:20–21`、`s1-brief.md:18,31`。gate 結果だけへ v2 を載せ、過去の出力を保つ方針は妥当。ただし plan の登録文は「事前に列挙した trace」と述べるだけで、列挙を結果前の commit にどう固定するかが弱い。  
放置時の成果物: 結果を見てから再検証対象を選べ、certified の受理集合を事後に変えられる。  
**推奨: 局所修正に置き換える。** `prereg.md` に対象の識別子・選定条件・digest を結果前に記録する。旧結果への v1 の一括追記は不要。

**B10｜should｜plan「成果物」、brief (P1)・(P7)**  
根拠: `md_14.txt:13–16,27–29`、`gen-opt-gate-liveness/README.md:140–143,181–184`、`s1-brief.md:26–36`。設計資料 §3.2・§7 の `A` 行を `Q/V` へ訂正した記録と、[T-2889] の前提・計算見積りを spool worklog に更新する具体手順が plan から抜けている。一方、32 本の歴史 lock の分類・再発行検討は今回の受理には不要。  
放置時の成果物: 次の実装者が旧 `A` 仕様を参照し、[T-2889] の投入条件と 2 node 時間判定が古いままになる。  
**推奨: 局所修正に置き換える。** 設計の訂正と worklog 更新を完了条件へ入れ、歴史 lock は維持する。現行 closure の失敗だけを直す。

**B11｜should｜plan「計算の見積り」**  
根拠: `plan.md:132–136`、`common-4.txt:27–30`、`gen-opt-gate-liveness/README.md:85–92`。提示値の合計 1.25〜1.6 node 時間は 2 未満だが、B01 の刻印だけを切り替えた build、やり直し、200k 件の RSS・wall 測定を含むか不明。D297 二本の約 0.55〜0.7 が最大項目で、前回 420 秒の四 job をそのまま 0.4 時間へ膨らませた枠にも余裕がある。  
放置時の成果物: 必要な比較を足した時点で投入条件の 2 node 時間判定が成立しなくなる。  
**推奨: 局所修正に置き換える。** B01 を反映して job 別に再積算し、投入前に 2 以上なら `common-4.txt` の停止条件を適用する。

## 削ってよいもの・残すべきものの一覧

| 判定 | 作業 |
|---|---|
| 残す | U1 の Q/V・刻印、Silo 限定の出力、TRACE=0 同一性・記号検査・build、U2 の D1/D2a/D2b 全 key、D5、意味版、B1〜B7 赤・N1〜N4 緑、修正前 stock の D2b 赤、修正後の D1/D2 ゼロ |
| 局所化 | verifier の `parse/core/model/report` と CLI。既存 integrity 計数・`ProofSurfaceAssessment`・compact trace・前 wave の起動器を再利用 |
| 削る・後送 | 今回使わない capability/snapshot/fanout の拡張、全発生条件の恒久 API、重複した詳細投影、全実走での U0 二重確認、歴史 lock の再発行 |
| 追加する | 設計資料の `A` 名訂正、結果前に固定した再検証対象、fail-closed test、判定器の単独変異実施、[T-2889] の前提と計算見積り |

## 総括

計画の中心である U1/U2 と三条件の生死確認は必要です。最優先の修正は、F 対 U1 を刻印単独の比較として扱わないことと、判定器の条件を一つずつ外す test を実施することです。既存の証拠面・integrity・U0・起動器を使えば、今回の certified 判定を保ちながら API と計算の広がりを抑えられます。これは静的レビューであり、build・test・計測は実施していません。