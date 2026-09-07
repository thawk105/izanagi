---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: dev-wave-t2198-trace0-fetchcontent
seq: 2
---

## {{D:trace0-fetchcontent-grammar-shape}}. trace0 の FetchContent 文法は ordered 4-prefix の 1 key で表す

**決定:** D1693 が命じた「`trace0_cmake_argv.configure` へ FetchContent の枠を厳密な期待値として
足す」を、**`fetchcontent_path_argument_prefixes` という順序付き 4 要素の literal 配列 1 key**で
実装する。prefix と依存名を別 key に分けて再合成する案は採らない。
`_exact_trace0_configure_argv` は `(dependency_prefix_argument, *fetchcontent_path_argument_prefixes)`
の 5 本を tail の先頭から**位置で**切り出し、各 token の prefix 一致と値の非空、FetchContent 4 本の
正規絶対 path と NUL 不在を検査したうえで、最終判定は `list(argv) != expected` の全一致のまま維持する。

**理由:**

- policy の 1 要素と producer が出す 1 token が一対一に対応し、prefix と依存名の連結という
  非一意な再合成を経ない。異なる policy 表現が同じ token 言語を表す曖昧さが小さい。
- 受理言語の証明力そのものは分割案と同等である。producer 側の定数と policy の片方だけを変えれば
  最終の全 argv 一致がどちらの案でも拒否し、両方同時に変えればどちらの案でも新しい protocol hash を伴う。
  **「1 key の方が厳密に強い」とは言えない**ので、採用理由は曖昧さの少なさに限る。
- 位置切り出しは、旧実装の「tail 全体から dependency prefix を内容で 1 本だけ拾う」より狭い。
  2 本目の dependency prefix、順序違い、空値、相対 path はいずれも拒否される。

**却下した選択肢:**

- prefix・依存名・順序を 3 key に分ける — 再合成が非一意で、同じ言語を表す policy 表現が複数生まれる。
- 文法を緩めて余分 token を許す — D1693 が却下済み。閉じた文法の証明力を落とす (絶対規律 2)。

## {{D:trace0-path-values-bound-to-producer-domain}}. 認証器が受理する path token の値域は producer が生成できる集合に揃える

**決定:** `_exact_trace0_configure_argv` が FetchContent の 4 path token について課す条件を、
「非空かつ絶対」から「**非空・絶対・lexically canonical・NUL を含まない**」へ狭める。
判定には同 file の既存 helper `_lexical_absolute_path` を使い、NUL 拒否だけを呼び出し側で足す。
helper 自体の意味は変えず、CCBench source root など既存の呼び手の挙動は不変とする。

**理由:**

- producer (`buildcache._canonical_fetchcontent_source_dir` / `_canonical_fetchcontent_base`) は
  NUL・非絶対・非 canonical をいずれも拒否する。**producer が生成できない argv を証拠として
  受理してはならない。** 従来は `/../` や NUL 入りの値が認証器を通り、対応する raw evidence が
  cells と effects を持つ positive report として参照されうる状態だった。
- 認証器は別の機体・別の時点で走るため producer と同じ実 path 解決はできない。
  lexical な canonical 性が実行可能な最も近い対応物である。
- これは受理集合を**狭める**変更であり、絶対規律 2 の方向と一致する。

**却下した選択肢:**

- `_lexical_absolute_path` 自体へ NUL 拒否を入れる — 既存の呼び手の受理集合まで動かす。
  本 wave の scope 外であり、必要なら別件として扱う。

## {{D:certification-third-party-input-is-hydrate-layout}}. 認証経路が受け取る依存の配置は hydrate の実出力形とし、`-src` への変換は job body が行う

**決定:** 認証経路の `--third-party-source-root` が受け取る配置を、
`tools/pegasus/fetch_third_party.py` の `hydrate` が実際に作る `<root>/<name>`
(masstree / mimalloc / googletest、末尾 `-src` なし) とする。build が要求する
`<base>/<name>-src` への変換は**計算ノードの job body が job-local scratch で行う**。

**理由:**

- `<name>-src` を作る主体は既存の投入器 shell と job body だけであり、供給 helper は作らない。
  入力契約を `<name>-src` にすると、その配置を誰が作るのかが設計から欠落し、
  人手の一回限りの手順が発火条件になる (`DW-G04` に反する)。
- 変換を job body へ置く形は既存 2 driver に前例がある。同じ file の既存 dependency prefix の
  扱いとも同型で、新しい供給機構も運用手順の変更も要らない。
- staged 依存の pin・clean・Git top-level 検査は変換後の job-local copy に対して走るため、
  検証の強さは落ちない。

**却下した選択肢:**

- 入力を `<name>-src` 配置にする — その配置の生成者が居ない。
- 投入器側で変換する — job-local scratch のほうが repo 外・job 単位で隔離され、
  同じ file 内の既存手順と対称になる。

## {{D:certification-protocol-hash-scope-is-policy-document}}. 認証プロトコル同一性の射程は policy document までであることを明記し、gate は増やさない

**決定:** `protocol_sha256` が束縛するのは policy document であって、Python 側の判定式や
qsub 環境変数の exact 集合ではない、という事実を**記録として明記するに留める**。
同一性を実装側の code identity まで広げる gate は本 wave では作らない。

**理由:**

- 同じ `protocol_sha256` のまま実装側の述語を書き換えれば受理は動く。これは事実だが、
  本 wave が作った欠陥ではなく認証プロトコル同一性の既存の射程である。
- `CLAUDE.md` 絶対規律 7 は「repo 内の挙動検査は gate と検査を同じ主体が変更できる限り
  意図的な弱体化への完全な防壁ではない。**この限界は主張せず明記する**」と定める。
  明記が規律の求める対応であり、新しい gate は求められていない。
- 要求外の仮想リスクで gate・検査・台帳を足さないという `DW-G05` の scope 規律にも一致する。

**却下した選択肢:**

- code identity gate を新設する — 主目的の外。必要なら独立の裁定として扱う。
- 限界を記録しない — 次に protocol hash を読む者が、実装の同一性まで担保されていると誤読する。
