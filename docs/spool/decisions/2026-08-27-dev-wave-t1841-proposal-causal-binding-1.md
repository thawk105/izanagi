---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-27
wave: dev-wave-t1841-proposal-causal-binding
seq: 1
---

## {{D:b4-bootstrap-bound-to-authoritative-history}}. B-4 の bootstrap 判定は checkpoint でなく実履歴へ束縛する

**決定:** 「これが B-4 の最初の合成である」という判定を、削除可能な checkpoint
(`loop_state.json`) の内容ではなく campaign の実履歴へ束縛する。bootstrap を名乗る state に
対し、admitted history が非空なら fail-closed で拒否する。空判定は WAL の**物理 byte の存在**で
行い、byte があるのに parse 済み record が空という状態も拒否する。3 driver すべての
`drive_iteration` が、state 構築直後・authorization 直前にこの検査を通る。

**理由:**
- D1061 が land した受領証 gate は、continuation にだけ閉じた critic の受領証を要求する。
  bootstrap 判定は `state.iteration == 0 and not state.whiteboard` だけを見ており、
  loop state が読めなければ driver は zero state を作る。**checkpoint を 1 つ消すか
  zero state へ置換するだけで、受領証の要求そのものが飛んだ。** 受領証の偽造すら要らない。
  critic の決定を 1 度も経ていない iteration が certified な B-4 標本へ入り、
  還流アームの on/off 差が treatment の効果でなくなる。
- 空判定を parse 済み record の有無で行うと、末尾が改行で終わらない frame だけを持つ
  非空 WAL が空と判定される。`wal.wal_bytes_present()` の docstring が
  「resume 拒否は parse 可能 record の有無でなく byte の存在で判定する必要がある」と
  既に定めている。同じ規則をこの判定にも適用する。
- 3 driver は proposal loader も authorization も別実装を持つ。1 か所だけ締めると
  残り 2 経路で迂回できる。共通検査を 1 つ置き、3 driver からの呼出を AST テストで固定する。

**受理集合:** 新たに拒否するのは「bootstrap を名乗る state かつ admitted history が非空」と
「bootstrap を名乗る state かつ WAL に物理 byte があり parse 済み record が空」の 2 つだけである。
真の bootstrap (WAL 不在 / zero-byte)、bootstrap を名乗らない正当な継続、B-4 でない通常走行の
受理は 1 bit も変えない。承認外の過剰拒否を検出する正例を登録した。

**却下した選択肢:**
- **checkpoint に世代印や署名を持たせる** — checkpoint 自体が削除可能である以上、
  そこへ何を書いても削除で回避できる。権威を可搬な file に置き直すだけである。
- **bootstrap を廃止して常に受領証を要求する** — 最初の合成には先行する決定が存在しない。
  受理集合を実際に空にする。

## {{D:causal-proposal-binding-needs-unforgeable-receipt}}. 決定と proposal 本文の因果束縛は hash 鎖では閉じない

**決定:** 閉じた critic の決定と次 proposal 本文の因果束縛を、file へ書く hash 鎖として
実装しない。閉じられる形は 2 つで、いずれもユーザー裁定を要する。裁定までは
「因果鎖を閉じた」と主張しない。

**理由:**
- terminal receipt を持つ者は、その隣にある critic 応答本体を読める。artifact path は
  `<terminal receipt と同じ directory>/envelope_<invocation_id>` で導かれ、
  `invocation_id` は receipt 自身の欄である。決定原像は receipt 所持者に開いている。
- 設計案の handoff receipt が持つ全欄 (決定 hash、envelope hash、campaign、arm、iteration、
  pair、projection、proposal の bytes と hash と長さ) は、receipt + envelope + 自分で選んだ
  proposal から計算できる。**秘密も署名も外部権威も 1 つも関与しない。**
  排他生成は「最初の書き手」を証明するが「正規の生成器」を証明しない。
- したがって決定を無視して選んだ proposal に、整合する受領証を作れる。
  自己申告の所在が file 1 枚ぶん移動するだけで、D1061 が名指しで却下した形と同型になる。
  これを実装して因果鎖を閉じたと書けば、規律 2 が禁じる緑化にあたる。
- **D1099 がこの型の問題に対する方針を既に定めている** — 「repo 外の権威による機械証明は
  今は作らず、偽造不能な受領証の機構が着地した時点でそこへ相乗りさせる」。本件は同型である。

**閉じられる 2 つの形 (ユーザー裁定へ返す):**
- **生成前の依頼を封じて応答を provider 受領証で束縛する形** — 生成前に決定原像・依頼・
  生成 ID を排他 record へ束縛し、planner/coder の応答を provider envelope
  (閉じた critic と同じ信頼根) で依頼 bytes と応答 bytes に束縛し、その 1 応答だけを
  proposal として確定する。偽造の困難さが critic envelope と同水準になる。ただし
  planner/coder を projected provider 経由にすることになり、**D39 決定 7 の supersede と、
  実験が測る対象そのものの変更**を伴う。
- **偽造不能受領証の機構へ相乗りする形** — D1099 の方針をそのまま適用する。

**却下した選択肢:**
- **proposal 自身に鎖 hash を書かせ、受領証の決定 hash と突き合わせる** — receipt を持つ者が
  誰でも計算できるため恒真である。D1061 が自己申告として却下した形と同じである。
- **設計案どおり handoff receipt を実装し、非保証を明記して land する** — 非保証を書いても、
  gate が実際には何も拒否しない事実は変わらない。受理集合が 1 件も変わらない機構を
  「因果を束縛した」と台帳へ載せることになる。
