---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t2421-a2-policy-version
seq: 3
---

## 新規

### {{F:historical-grammar-defined-as-diff-from-current}}. 旧世代の文法を現行文法との差分で定義し、次の締め付けで再汚染する設計を起草していた [ドリフト] [射程過大]

- 事象: 段 2 プランは、旧 policy 文法の configure key 集合を
  「現行集合 − `fetchcontent_path_argument_prefixes`」という差分式で定義していた。
  この形だと、次に現行集合へ必須 key が足された時点で旧世代集合にもその key が混入し、
  過去成果物が再び読めなくなる。**直そうとしている再発をそのまま再生産する設計**だった。
- 根本原因: 「旧世代 = 現行世代から 1 つ引いたもの」という**現時点の値の関係**を、
  定義そのものに使った。凍結すべきなのは値であって、現行との関係ではない。
- 恒久対応: {{D:policy-grammar-generation-selection}} が両世代を独立した `frozenset` literal として
  凍結する。加えて producer source の AST を検査するテストが、対象名への module-level 代入が
  ちょうど 1 つであること、その値が `frozenset({文字列 literal})` の呼び出しであること、
  subscript 代入と破壊的メソッド呼び出しが無いことを要求する。
- 再発検知: 差分定義へ戻す変異を登録し、上記 AST テスト 1 node だけが赤になることを実測した。
  **当初この変異は「両定義が同じ値を返すので等価」と裁定していたが、これは誤りだった。**
  守りたい性質が構文的なら構文を検査すればよく、実装子がその一手を採ったため kill できる。

### {{F:public-loader-widened-by-caller-selected-grammar}}. 版選択を公開 loader の引数として足し、受理集合を広げる設計を起草していた [受理集合] [射程過大]

- 事象: 段 2 プランは公開 `load_policy(path, *, generation=...)` を提案した。既定は現行世代なので
  既存 caller の挙動は変わらないが、**任意の caller が旧世代を選べる**ため、
  `fetchcontent_path_argument_prefixes` を欠いた policy 一般が受理されるようになる。
  親自身が段 1 brief に書いた不変条件「受理集合を 1 件も増やさない」と正面衝突していた。
- 根本原因: 「歴史成果物の bytes は consumer 側の exact hash 対で固定されている」という
  **consumer 側の閉じ方**を、producer 側の公開 API の受理言語にも当てはまるものとして一般化した。
  閉じているのは選択であって、文法ではない。
- 恒久対応: {{D:policy-grammar-generation-selection}} が公開署名を不変にし、世代を受け取る本体を
  private 化して、歴史読みを consumer 専用の private entry point へ隔離する。
  これにより歴史 Policy を得られる経路が 1 本になり、producer の認証・実行経路へ流れない。
- 再発検知: `inspect.signature` で公開 `load_policy` が path 1 引数のままであることを固定する
  テストを置いた。未知世代・非 str 世代を fail-closed で拒否する負例も置き、
  未知世代を現行へ fallback させる変異が 1 node で赤になることを実測した。

### {{F:duplicate-gate-makes-single-mutation-unkillable}}. 同じ条件を拒否する gate が 2 箇所にあり、事前登録した変異が単独では殺せなかった [変異帰属] [過剰決定]

- 事象: consumer の `source_binding_status != "bound"` を拒否する gate が 2 箇所に存在し、
  end-to-end の負例はどちらか一方を外しても残る方に拾われる。段 4 で事前登録した
  「歴史世代のときだけ後段検査を飛ばす」変異は、単独では 1 node も赤にできず SURVIVED になる。
  親は変異を走らせる前に、この過剰決定に気づいていなかった。
- 根本原因: 負例を end-to-end (`load_measurements` 全体) で書いたため、
  狙った gate より後段の同型 gate が masking していた。単一理由性を到達 gate の列挙で
  確かめていなかった。
- 恒久対応: 狙った gate だけが到達する単一理由の負例を足し、内部関数を直接呼ぶ形にした。
  2 つ目の gate は**冗長 gate と明記して単独変異の証拠から外した** (DW-M03)。
  end-to-end の負例は正当な検査として残した。
- 再発検知: 変異本走で、当該変異が新設した単一理由テスト 1 node だけを殺し、
  end-to-end 版は緑のままであることを実測した。冗長性が実測で裏付けられている。
