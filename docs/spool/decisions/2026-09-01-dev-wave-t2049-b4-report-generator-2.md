---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-01
wave: dev-wave-t2049-b4-report-generator
seq: 2
---

## {{D:b4-material-report-evidence-only}}. B-4 の材料レポートは floor が発効するまで evidence-only とし、正規経路が生む分類は 1 つだと自ら宣言する

**決定:** B-4 の材料レポート生成器と正規コマンドは、分析の `floor` を caller から受け取らない。
CLI 引数も既定値も持たず、既存評価器へ floor 不在のまま渡し、`floor_domain_error` を伴う
`protocol_violation` をそのまま材料化する。レポートは自分が evidence-only であること、
事前登録 §5 が未発効であること、正規経路で到達する分析 verdict が 1 つだけであることを
機械可読に宣言する。**本 wave は事前登録 §7.1 の 4 分類を実効化したとは主張しない。**

**理由:**
- 事前登録は `floor` を「§5 の凍結 artifact から読んだ値。関数の引数として渡す。関数内で
  導出しない」と定める。D1060 は §5 を 1 欄も埋めないと決めている。したがって CLI 引数は
  caller の自己申告を凍結値の位置へ入れることになる。
- 生成器は publication root だけを入力とし判断値を caller から受け取らない設計であり、
  floor 引数はその境界と自己矛盾する。D162 が producer 側で立てた向きと同じである。
- 未記入を独自に「判定不能」へ読み替える案も採らない。既存の凍結された分析契約が
  floor 不在を `protocol_violation` と定めており、生成器が別の意味を与えてはならない。
- 到達できる分類が 1 つであることを黙っておくと、renderer だけで作った 4 分類の試験が
  「正規経路が 4 分類を出せる」証拠と読まれる。宣言と試験の呼び名を分けて閉じる。

**却下した選択肢:**
- CLI 必須 `--floor` と出所の自由記述 — 値も出所も caller の自己申告であり、レポートへ
  文字列を刻んでも正当性は増えない。
- 未記入を「判定不能」へ読み替える — 凍結された分析契約の意味を生成器が上書きする。
- 権威ある floor artifact を本 wave で作る — 事前登録 §5 の発効は別の手続きであり、
  AI が既成事実にしない。

## {{D:b4-material-report-output-disjointness}}. 材料レポートの出力先は campaign root と 3 方向で交差してはならず、証明できないときは配置を拒否する

**決定:** 材料レポートの writer は、書込みに使うものと同じ実体 path で、出力先が
(a) campaign root と一致する、(b) campaign root の配下にある、(c) campaign root を配下に含む、
の三方向をすべて拒否する。symlink component も拒否する。証拠の欠落や破損により campaign root
集合を完全には復元できない場合は、その状態を機械可読に `partial` と宣言したうえで、
`output` directory 配下に `campaigns` を含む配置だけを追加で拒否する。

**理由:**
- campaign root 配下の完全性検査は root を再帰列挙し、宣言された artifact 集合との厳密一致を
  要求する。レポート 2 file を campaign 内へ置くと、この検査が実際に赤になる。
- 字面比較だけでは symlink 親を経由した配置と祖先方向の交差を閉じられない。
- 読めない証拠があるとき campaign root 集合は不完全になる。そこで黙って通すと、
  復元できなかった root の内側へ書ける fail-open が残る。証明できない状態を宣言し、
  危険な配置だけを狭く拒否するほうが、一般化した許可制を新設するより射程が小さい。

**却下した選択肢:**
- 一般化した official-root の許可制を新設する — 本件に必要な射程を超える。
- campaign root 集合が不完全なときも従来どおり通す — 具体的に構成可能な fail-open を残す。
- 出力先を publication root 配下に固定して検査をやめる — publication root が campaign 配下に
  置かれることを発行側が排除していないため、固定だけでは交差を防げない。
