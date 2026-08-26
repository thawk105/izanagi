---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-t1759-t1742-ratification-history
seq: 2
---

## {{D:ratification-history-dag-append}}. 批准台帳の全史規則を DAG の追記として定義し、保証の文言を狭める

**決定:** 批准台帳の履歴検査は、`git log --full-history <path>` が列挙する版を線形に並べて
前置拡張を求める形をやめ、HEAD の到達可能 commit を自前で列挙して DAG の遷移として検査する。
各 commit について、台帳 entry を持つ実親の行集合の和が子の行集合の部分集合であること、
子の行集合から親の和を引いた大きさが 1 以下であること、実親がちょうど 1 つのときは
親の行列が子の行列の部分列であることを要求する。実親が 2 つ以上のときは順序を課さない。
台帳を持つ実親を 1 つも持たない導入 commit は、到達可能 DAG 全体でちょうど 1 件に限る。

この機構が主張してよいのは
**「台帳は全史にわたり、どの commit でも既存行を落とさず、1 commit あたり高々 1 digest しか
増えない形で成長した」**までである。「人間が批准した」とは主張しない。D526 が既に
「人間が批准したことの機械的証明と記述してはならない」と定めた線を、DAG へ拡張しても保つ。

**理由:**
- 旧規則は merge commit を台帳の改版と数えるため、台帳が byte 不変でも main が進むたびに
  版数が増え、2 件目で必ず落ちた。実測では現行 main で版が 17、うち 16 が merge であり、
  そのすべてが「片方の親が台帳を持たない」ために列挙されていた。検査は台帳の中身と無関係に
  常に赤で、批准行を足しても gate は開かない。
- 分岐した 2 branch がそれぞれ 1 行足して合流する形は、最終 bytes が正しくても
  受理集合の読み込み自体が例外になった。合成履歴で再現済みである。
- 合流で全親の行順を同時に保存させると、`[a,b]` と `[b,a]` のように解の存在しない組合せが
  作れる。順序は受理集合の値に入らないため、合流では集合の一致だけを求める。
- 末尾追記だけを許すと、cherry-pick や rebase で行が中間へ入った正しい履歴を拒否する。
  部分列に緩めても、置換・欠落・並べ替え・複数行追加はすべて拒否のまま残る。
- 導入 commit を一意にしないと、同じ台帳なし祖先から 2 つの独立導入を作って合流させ、
  片方に未批准 digest を載せられる。旧規則はこの形を拒否していたので、
  一意性を課さない DAG 規則は検出力の後退になる。実測で確認した。

**却下した選択肢:**
- **`--full-history` の列挙に規則の健全性を預ける** — 「台帳 blob がどれかの親と異なる commit を
  過不足なく列挙する」ことは 1 repo 1 HEAD で実測したが、git の一般保証としては未確認である。
  さらに blob 同一で tree mode だけ変える commit が列挙される事実があり、
  述語を blob 差と同一視する一般化は既に破れている。到達可能 DAG を自前で列挙すれば
  この依存は消え、実測では所要も呼出し回数も増えない。
- **commit 間で tree mode の一致を求める** — 批准の値は digest の集合であって tree mode ではない。
  守る値に対応しない拒否を足すことになる。entry が regular file の blob であることだけを求める。
- **合流での行追加を禁じる** — 人間が合流の解決中に批准する形を機械的に拒む理由が無く、
  1 commit あたり高々 1 digest という不変条件は親数によらず同じ強さである。

## {{D:ratification-history-environment-guards}}. 履歴検査は shallow と実効 graft を拒否し、replace ref の存在では拒否しない

**決定:** 批准台帳の履歴検査は、開始時に次を要求する。

- `rev-parse --is-shallow-repository` が exact に `false` であること。そうでなければ拒否する。
- `info/grafts` が存在する場合、空行と `#` で始まる行以外を 1 行も含まないこと。
- `refs/replace` の ref が存在すること自体は拒否しない。
- 台帳の tree entry は regular file の blob (`100644` または `100755`) であること。
  symlink と gitlink は拒否する。

**理由:**
- shallow clone では置換された履歴を観測できず、検査が恒真の側へ倒れる。
  「批准済み」という主張が証拠なしに立つ経路を残さない。同型の拒否は既に
  `s8b_ratified_freeze.py` と `trial_registry.py` にあり、家法に沿う。
- graft は実親を書き換えるため、DAG 走査そのものを偽装できる。一方、空の graft file や
  コメントだけの graft file は何も書き換えない。存在だけで拒否すると偽赤になる。
- replace object は検査が使う git 呼出しで既に無効化されている
  (`--no-replace-objects`、`core.useReplaceRefs=false`、`GIT_NO_REPLACE_OBJECTS`)。
  ref の存在を追加で拒否しても検出力は増えず、到達不能 commit の救出などの正当な用途を壊す。
- symlink の object type は blob であるため、type の検査だけでは symlink を弾けない。
  mode の allowlist が実質的な type 検査になる。git が通常経路で
  `100644` / `100755` 以外の regular file mode を書くことはない。

**却下した選択肢:**
- **shallow を受理して警告に留める** — 恒真ゲートを残すのと同じである。
- **graft file の存在だけで拒否する** — 偽赤を作る。実効行の有無で判定する。
- **replace ref の存在で拒否する** — 既に無効化済みの経路に対する重複であり、
  正当な運用を壊す側にだけ効く。
