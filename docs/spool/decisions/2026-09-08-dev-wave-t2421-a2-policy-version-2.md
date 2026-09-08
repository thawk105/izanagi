---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t2421-a2-policy-version
seq: 2
---

## {{D:policy-grammar-generation-selection}}. A-2 の policy 文法は世代で選び、公開 loader の受理集合は変えない

**決定:** producer の policy 文法に世代 (generation) を導入する。世代は
`POLICY_GENERATION_CURRENT` と `POLICY_GENERATION_PRE_FETCHCONTENT_PATHS` の 2 つで、
`trace0_cmake_argv.configure` の exact key 集合を**それぞれ独立した `frozenset` literal** として持つ。

- **公開 `load_policy(path)` の署名と受理集合は 1 byte も変えない。** 文法定数を引数で受ける
  共有本体を private 化し、`load_policy` は現行世代の定数を渡すだけにする。
  歴史読みは private な専用 entry point からだけ到達でき、caller が世代を選べる公開 API を作らない。
- 世代 id は exact-type (`type(generation) is str`) と登録済みであることを fail-closed で検査し、
  未知値を現行世代へ読み替える fallback を作らない。
- consumer の選択表は値を世代 id だけにする。主 key は
  `(認証 bytes の SHA-256, 埋め込み policy bytes の SHA-256)` の組のまま維持する (D1754)。
  成果物が記録する `source_commit` を第三の選択入力にしない。
- 手書きの歴史 view を全削除し、歴史側も producer の完全な文法を通す。

**理由:**

- 先行 wave の 1 件限定 adapter は受理集合を緩めていなかった (entry の主 key が policy bytes を
  完全に固定するため) が、**再利用できなかった。** 文法が締まるたびに専用コードと新しい pin を
  書き足す必要があり、F884 が名指しした構造が残っていた。
- 旧世代の key 集合を「現行集合 − 追加 key」の差分で定義すると、次に必須 key が足された時点で
  旧世代へ混入し、**まったく同じ再発が起きる**。独立 literal はこれを構造的に防ぐ。
  producer source の AST を検査するテストが、差分定義への退行を構文レベルで拒否する。
- 公開 loader へ caller 選択の世代引数を足すと、`fetchcontent_path_argument_prefixes` を欠いた
  policy 一般が受理される。これは絶対規律 2 に抵触する。private 化により、歴史 Policy を得られる
  経路は plot consumer の 1 本だけになり、producer の認証・実行経路へ流れない。
- 手書き view の削除で受理集合は**狭まる**。`_protocol_preimage` に含まれない
  `tracked_destination` などの検査が歴史側にも効くようになる。
- **過去成果物を読めるようにすることは、当時の測定を現行の正しさ主張へ昇格させることではない。**
  歴史世代は保存時文法での再現にだけ使い、status・correctness・`source_binding_status` を
  再分類しない。これは絶対規律 7 が許す「入力と判定の対応づけ」の側であり、
  「現行の正しさ主張への昇格」ではない。

**この決定が覆わない範囲 (限界):**

世代化されているのは `trace0_cmake_argv.configure` の key 集合だけである。
`schema_version`、top-level key 集合、各値制約、`_protocol_preimage` は全世代共有のままなので、
次の締め付けがそれらに及べば、世代を正しく選べても過去成果物は読めなくなる。
**この決定は再発を無くしていない。減らしただけである。**

**却下した選択肢:**

- 公開 `load_policy` に `generation` 引数を足す — 受理集合が広がる (上記)。
- 旧世代の key 集合を現行集合との差分式で定義する — 次の key 追加で再汚染する。
- `source_commit` を第三の選択 key にする — `source_commit` は認証 bytes の一部であり、
  主 key の認証 hash に既に束縛されている。二重正本になるだけで閉包は強くならない。
- 世代ごとに schema・全 exact-key 集合・protocol preimage 規則・値 validator を束ねた
  完全な文法契約を作る — 発火条件を満たす既存成果物が無く、DW-G04 に反する。裁定パッケージへ返す。
- producer が世代 id を成果物へ書き込む — result schema と producer 出力 bytes、凍結 pin が動く。
  既存成果物には効かない。裁定パッケージへ返す。
- `Policy` dataclass へ世代 field を足す — frozen dataclass で、job-contract fixture の
  `dataclasses.replace` へ波及する。private 隔離で機構は閉じているため足さない。
- producer の実行・生成入口へ current-only の強制 gate を置く — どのコードも通らない経路への
  新設 gate であり、要求外の仮想リスク向け防壁に当たる。
