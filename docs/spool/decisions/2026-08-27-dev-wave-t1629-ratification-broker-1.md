---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-27
wave: dev-wave-t1629-ratification-broker
seq: 1
---

## {{D:d956-not-applicable-to-ratification}}. D956 は批准機構に適用せず、閉包を 27 path へ広げる

**決定:** D956 (受入 gate の実装は強制ソース閉包を避ける) は enforcement closure の**批准**機構には
適用しない。閉包を 25 から 27 path へ広げ、`ed25519_verify.py` と
`enforcement_source_ratification_receipt.py` を収載する。

**理由:**
- D956 の決定文の対象は「**正式受入の gate** を足す実装」である。正式受入 (受入全走の gate) と
  批准 (campaign 初期化の authority) は別の機構であり、本件は後者である。
- D526 が本件について逆向きに既裁定である。「比較処理と receipt 実装面は closure へ収載する」。
  判定器を閉包の外に置くと、AI が判定器を書き換えても批准が失効しないため機構が恒真化する。
- **D956 が挙げる代償は本件では発生しない (実測)。** tracked な campaign lock 32 件のうち
  closure map を持つものは 0 件。repo の `output/` を除く外部 campaign lock 1536 件のうち
  closure map を持つのは 36 件だが、その 36 件が記録しているのは 8 path (28 件) と
  12 path (8 件) で、**現行 25 path を記録しているものは 0 件**である。
  いずれも T1207 / T1287 より前の epoch の遺物で、現行閉包に対して既に E1-stale である。
  したがって閉包を広げても、新たに失効する certified campaign は repo 内外あわせて 1 件も無い。

**却下した選択肢:**
- **D956 を適用して着手前に停止する** — 主題が違い、D526 と正面から衝突する。
  代償の実測もゼロである。
- **判定器を閉包の外に置く** — AI が判定器を書き換えても批准が失効しなくなる。D526 が
  避けようとした恒真化そのものである。

## {{D:ratification-claim-bound}}. 批准機構の主張上限を定め、判定器が閉包の内側にある限界を明示する

**決定:** 署名 receipt による批准機構について、書いてよい主張は
**「現在の committed 信頼根の鍵で検証できる署名 receipt の集合と、要求された closure digest を
比較する。信頼根の秘密鍵は repo の外にあり、AI はそれを持たない」**までとする。

次は書いてはならない。

- 「人間が批准したことの機械的証明」
- 「AI が追記できない集合との比較」 (無条件には成立しない)
- 「D905 / D906 を満たした」

**理由:**
- **判定器とその呼び出し元は、判定対象の閉包の内側にある。** 呼び出し前に「今動いている判定器の
  bytes が以前に批准された bytes と同じか」を確かめる外側の実行器が存在しない。
  したがって repo を編集できる主体は、鍵を一切持たなくても判定器を無条件 return へ書き換えて
  gate を消せる。`capture_contract_loader_binding()` はその bytes を正直に hash して
  新しい authority に記録する。
- これは v1 から存在する構造であり、署名を足しても塞がらない。段 3 の敵対 2 レンズが
  別のレンズから独立に同じ結論へ達した。
- D906 が署名対象へ「実行器と検査器の bytes」を含めよと書いているのは、まさにこの穴である。
  本 wave の schema はどちらも含んでいない。
- 閉じるには repo の外に固定された実行器が要り、それは本件より大きい別設計である。

**却下した選択肢:**
- **D905 / D906 を満たしたと書く** — 上記のとおり成立しない。実態より強い主張になる。
- **限界を書かずに実装だけ着地させる** — 次の作業者が機構の強さを誤る。

## {{D:divergent-signed-chain-rejected}}. 分岐した署名列は fail-closed で拒否し、台帳追記を単一 writer で直列化する

**決定:** v2 receipt 台帳の履歴検査は、**分岐した署名列を fail-closed で拒否する**。
merge は「両親の台帳 blob が同一」または「一方が他方の exact prefix」のときだけ許す。
それ以外は専用のエラー文言で拒否し、運用として台帳追記を単一 writer で直列化することを案内する。

**理由:**
- v1 の DAG 受理則 (digest の union) は v2 へ流用できない。v1 の行は digest 文字列だが、
  v2 の行は serial と previous hash で連鎖する署名付き dict である。
  分岐した 2 本がそれぞれ serial=2 を足すと、**再署名なしに 1 本の chain へ合流できない**。
- 受理集合を広げない側へ倒すのが規律 2 に沿う。
- 代償は実在する。**該当 merge 以後は新規の certified 選択結果を 1 件も生成できなくなる。**
  ただし台帳へ追記するのは人間の批准だけであり、頻度は全期間で十数件の桁である。

**却下した選択肢:**
- **DAG-native な schema へ変える** — serial / previous hash を捨てる大きな設計変更が要る。
  本件の目的に対して代償が釣り合わない。
- **分岐を受理する** — 受理集合が広がり、どちらの署名列が正であるかを機構が決められない。

## {{D:ratification-bootstrap-contract}}. 信頼根と空台帳は人間が一度だけ置き、broker は生成経路を持たない

**決定:** `hooks/enforcement-source-ratification-trust-root.v1.json` と
`hooks/enforcement-source-ratification-receipts.v2.jsonl` は、**人間が AI の到達できない host から
一度だけ設置する**。`tools/ratification_broker.py` は鍵生成も信頼根生成も行わず、
不在なら fail-closed で停止して人間が打つ手順を表示するだけとする。

repo 内の broker は**参照実装**であり、運用 copy は AI が到達できない host に置く。

**理由:**
- 回収した実装は、鍵が無ければ生成し、信頼根が無ければ自分の公開鍵を信頼根として書いていた。
  親が判定器を副作用なしに静的評価した結果、AI は次を一度も止められずに完遂できた:
  自分の鍵を生成する / broker を起動する / 承認プロンプトへ `y` を流し込む /
  生成された信頼根を `git add` する。**broker は ssh 越しに書くため `hooks/` の
  書込拒否も通り抜ける。** これは D906 が名指しした恒真化そのものである。
- 生成経路を削除すれば、AI が broker を起動しても既存信頼根の秘密鍵が無い限り何も起きない。
- **表示の完全性も同じ理由で要る。** 人間の判断が入る唯一の場所であり、
  初回批准で内容を表示しない実装や、bidi override を素通しする実装は、
  operator に中身を見せないまま署名させられる。

**却下した選択肢:**
- **broker に信頼根の初期生成を残す** — 最初に起動した主体が信頼根になる。AI が先に起動できる。
- **bootstrap writer を `tools/` に新設する** — AI が同じ writer を呼べる。手順書だけを残す。
