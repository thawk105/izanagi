---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-29
wave: dev-wave-t2005-b4-projection-registration
seq: 1
---

## {{D:b4-projection-row-requires-all-three-drivers}}. B-4 の projection 欄は 3 driver 完全形だけを受理し、登録 3 値を実走前に全件 live 照合する

**決定:** 事前登録 §5 の期待値行が受理する形を、base / sort / trigger の固定順・固定 tag を
持つ 3 projection へ限定する。旧 1 値形・tag 欠落・重複・順序違い・末尾余剰を拒否し、
値セルの **raw bytes** と NFKC 正規化後の双方に同じ文法を要求する。model は `claude-opus-`
接頭辞と ASCII slug、hash 4 種は小文字 16 進 64 桁に限る。

`verify_b4_admission_record` は既定値なしの driver 種別を必須引数に取り、受理記録が宣言する
単一 projection が文書の当該 tag と exact に一致することを検査する。あわせて、文書の 3 値
すべてを live `projection_sha256(kind)` と照合する関門を、起動器の bootstrap 経路、
pair 生成点、invoke、最終 certification の 4 か所へ置く。照合は executable 探索・
artifact root 作成・provider 作成のいずれよりも前に行う。

受理記録の canonical JSON schema `p3-b4-prerun-admission/v1`、root key 集合、単一 projection
field、sidecar schema は変えない。

**理由:**
- 1 driver 分だけを登録できる形を残すと、**どの driver で走るかを結果を見た後に選べる。**
  対象 driver 欄は §5.1 (i) の先行 freeze が済むまで埋められないので、この穴は現に開いている。
- 従来 production は実走する driver の 1 値しか照合しなかった。3 値を宣言しても、
  非選択 driver の閉包が陳腐化したまま certified な成果物を出せた。宣言と検査の射程が
  食い違ったまま「登録した」と書くのは、閉じていないものを閉じたと書く行為である。
- bootstrap 経路は `verify_b4_admission_record` しか通らない。照合を pair 生成点だけに置くと
  同経路が無防備になる ({{F:verifier-moved-check-strands-single-caller-path}})。
- `_normalized_source_cell` は NFKC 正規化を行うため、正規化後だけを見る文法は raw bytes に
  対して exact ではない。`ﬀ` (U+FB00) を含む 63 文字の生文字列が正規化後に 64 桁 hex になり、
  U+00A0 は普通の空白へ、全角の角括弧は ASCII へ変わることを実測した。
  commit された文書の raw bytes が事前登録の指定形と違ってよい理由は無い。
- 受理記録側の schema を昇格させても選択 driver の受理集合は 1 bit も強くならない。
  D998 の schema と D999 の sidecar を広く変更する費用だけが増える。

**却下した選択肢:**
- **受理記録へ driver 種別の field を足す** — 記録の自己申告になる。driver は封をした
  起動 context と config から機械導出できるので、記録に名乗らせる必要がない。
- **文書側の照合を「3 値のいずれかと一致」で済ませる** — driver 束縛は pair 生成点の
  live 照合が担うので緩みはしないが、bootstrap 経路がその照合を通らないため成立しない。
- **3 driver 全件の鮮度を任意実行の repository test に任せる** — 実行しなければ効かない。
  production 経路が「登録 3 値が全件 live」を要求しなければ、機械的受理集合は
  「選択 driver だけ最新」のままである。

## {{D:b4-model-snapshot-needs-declared-source-before-the-cell-is-filled}}. B-4 の model snapshot 欄は宣言源・承認者・時点・不一致時の扱いを先に固定するまで埋めない

**決定:** 事前登録 §5.1 の当該欄へ解除条件を足す。本欄は独立した 3 種の値を 1 セルに持ち、
§0 の原子性によりすべてが確定するまで `未記入` のままにする。projection は 3 driver 分を
すべて書き、記入後に閉包 member の bytes が変われば 3 値は同時に無効になる (登録は一度きりの
行為ではなく継続的な不変条件である)。prompt hash は repository の bytes から導出する。

`expected_claude_model_snapshot` は repository の bytes から導出できないので、本欄を埋める前に
**(a) 結果に依存しない宣言源、(b) 宣言を承認する人間の識別子、(c) 宣言の時点、
(d) 観測 slug が宣言と食い違ったときの扱い**を別 commit で固定する。(d) を
「宣言を書き換えて同じ実走を続ける」と定めてはならない。4 点が固定されるまで本欄を埋めず、
その旨を §10 へ記録する。

**理由:**
- D1060 は解除条件が存在しない欄をそのまま埋めることを「拘束力を持たない値を書く行為であり、
  ancestry 条件を形式的に満たすだけの空洞化」と述べ、埋めるのではなく規範を足す形を採った。
  本欄は同じ状態にある — 既存の解除条件は「両アームで同一であることを確認して記入する」だけで、
  同一性の確認は値の選択権限を与えない。
- 実 CLI 応答の `modelUsage` が返す exact slug は走らせる時期で変わる。本 repo の成果物には
  `claude-opus-5[1m]` と `claude-opus-4-8` の両方が実在し、role frontmatter の `opus` は
  snapshot slug ではない。D998 が定めるとおり本欄は「事前宣言 + 実行時照合」であって
  予測ではないので、**値の指名は実験条件の決定である。**
- 宣言源を定めずに AI が fixture・alias・試し打ちの結果から値を選ぶと、結果を見てから
  宣言を選べる経路になる。前向き事前登録の意味が失われる。
- (d) を書き換え許容にすると、実行時照合が拘束でなくなる。D998 が「警告・環境変数・
  CLI flag の逃がし道を作らない」と定めた射程を、運用規範の側から破ることになる。

**却下した選択肢:**
- **AI が値を宣言して埋める** — 新しい権限主体を作る。誤宣言は実行時に fail-closed で
  止まるだけで安全側だが、誰が実験条件を決めたかの記録が残らない。
- **projection と prompt だけ先に埋める** — §0 が部分記入の例外を 1 欄に限り、
  他の 9 欄へ広げることを明示的に禁じている。
- **critic query を試し打ちして観測 slug を宣言する** — 出力を見てからの事前登録になりうる。
