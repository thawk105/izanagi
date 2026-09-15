---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-15
wave: dev-wave-t2591-aggregate-material-report
seq: 2
---

## {{D:seam-allowed-by-position}}. 正例で差し替えてよい seam は本数でなく機構上の位置で決める

**決定:** 本 wave の正例について、差し替え可否を次のとおり位置で定めた。本数では定めない。

- **禁止 (機構上の seam):** 検査している機構そのものを構成する呼び出し。本 wave では
  `issue_aggregate_authoritative_floor`、`resolve_preregistered_authoritative_floor`、
  `build_material_report_document` とその内部の投影・検査関数。ここを差し替えた正例は無効とする。
- **許可 (環境 seam):** 検査している機構の外にあり、既存テスト群が既に定型として使っているもの。
  本 wave では calibration loader、Git の `subprocess.run`、`os.fsync`、
  材料レポート module の repository root、共有 publication fixture 内部の既存 patch。
- **許可 (観測 wrapper):** 実物へ委譲して引数や呼び出し回数だけを記録するもの。差し替えではない。

**理由:**

- 親が段 1 brief で「許可する monkeypatch は 3 つだけ」と本数で書いたところ、段 3 の敵対相談が
  矛盾を出した。**指定した共有 publication fixture 自身が 3 つ以上を patch している**ため、
  本数で縛ると指定した fixture を使えない。制約が実体と矛盾していた。
- 段 2 のプランは、本数制約を満たすために既存 helper へ keyword 引数を足して Git seam を
  条件化し、一時 fixture に実 Git repository を作る案を出した。制約側の誤りに合わせて
  コードを曲げる案であり、採らなかった。
- 段 3 の逐語: 「Git patch は最大値計算、3 spec 閉包、source 再構成、report 投影を置換しない。
  外して増える検査は Git による入力の凍結・履歴 binding であり、集約 → report の結線そのものでは
  ない」。**検査している機構の識別力を増やさない差し替えの除去は、正例を強くしない。**
- 位置で決めれば、何を証明していないかも同時に決まる。本 wave の正例は
  「3 本の source summary が実 Git に凍結された成果物であること」「calibration が真正であること」
  を証明しない。これは環境 seam の外側に残る。
- 事前登録した 5 変異はすべて機構上の位置に置き、新走で 5/5 KILLED、旧走で 5/5 SURVIVED だった。
  環境 seam を残したまま、機構の識別力は実測できている。

**却下した選択肢:**

- **許可する差し替えを本数で列挙する** — 指定 fixture の内部と矛盾し、
  「fixture 内部は数えない」という後付けの例外を必要とする。
- **既存 helper に keyword 引数を足して Git seam を条件化し、実 Git fixture を新設する** —
  機構の識別力を増やさない。同時稼働の床値系 wave と最も衝突しやすい共有 helper を触る。
  依頼が scope 外と明示した範囲に入る。
- **環境 seam をすべて禁じる** — 材料レポート・床値 issuer の既存テスト群が全面的に依拠する
  定型であり、本 wave が検査する機構ではない。禁じれば既存群ごと書き直すことになる。

**この決定の射程:** 本 wave の裁定である。同型の欠陥が別の producer / consumer で独立に
2 件再現するまで、族全体への制度としては一般化しない。

## {{D:material-report-reach-scope}}. 材料レポートの「届く」は生成 bytes までとし、publish と certification を含めない

**決定:** 集約床値が材料レポートへ「届く」ことの証明範囲を、公開 builder が返す
JSON / Markdown bytes までとする。次は含めない。

- `write_material_report` による publish の成立。
- 材料レポートが certified であること。

**理由:**

- `write_material_report` は公開 builder を呼ばず、生成処理を別に組み立てている。
  publish には出力先の拒否条件、campaign 非交差、commit marker が加わるため、
  builder の正例から publish の受理集合を推論できない。
- 材料レポートの現物は `certifying=False` / `closed_world=False` を宣言し、
  報告範囲を `evidence-only`、事前登録 §5 を `not_in_effect` と表示する。
  Markdown も selection を certify しない。親が段 1 brief で「certification 成果物」と
  書いたのは現物より強い主張だった。
- 明示 output_root では reproduction argv が変わり JSON / Markdown の hash も変わる。
  保存済みペアと commit marker の存在は builder では証明されない。

**却下した選択肢:**

- **正例を publish まで伸ばす** — 現在の投影目的からは必要でない。
  publish 固有の受理条件を同じ正例へ混ぜると、どちらが赤にしたか分からなくなる。
- **「certified なレポートへ届いた」と記録する** — 現物の宣言と食い違う。
