---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-23
wave: dev-wave-acceptance-reds-probe-perf
seq: 1
---

## {{D:probe-worktree-reuse-cannot-prove-isolation}}. 非帰属 probe の worktree 再利用は、状態隔離を証明できないため採用しない

**決定:** `tools/check_acceptance_reds.py` の probe worktree を node 間で使い回す高速化は
**実装しない**。node ごとに worktree を作り直す現行設計を維持する。

**理由:**

- 潜在利得は小さくない。過去 receipt 130 件の全数集計では probe worktree の構築が
  705 回発生しており、`(receipt, tip)` 単位で使い回せば 230 回まで減る (475 回削減)。
  それでも採らない。
- **現行 fingerprint は submodule 内の gitignore された生成物を検出しない。**
  本 wave で対照実験を行った。probe と同一手順で作った worktree に対し、
  `git status --porcelain=v1 --untracked-files=all --ignored=matching --ignore-submodules=none`
  は (a) submodule 内の untracked file を ` M external/ccbench` として検出し、
  (b) 親 repo 側の gitignore された file を `!! orchestrator/__pycache__/` として検出したが、
  (c) **submodule 内の gitignore されたビルド生成物** (`external/ccbench/build/` 配下、
  ccbench の `.gitignore` が `build*/` を無視) は検出せず、fingerprint は空のままだった。
- これは最も再利用したい対象に直撃する。受入で赤になった実測 26 件は
  `orchestrator/tests/test_sort_swo_oracle.py` で、失敗理由は CCBench のビルド生成物への
  依存 (`config-h-missing`) である。node N のビルドが node N+1 の判定を変えても
  どの検査も発火しない。本来 `attributable` (この wave が壊した regression) と
  判定すべきものが `flake` として素通りしうる。規律 2/3 の違反である。
- **救済案 (fingerprint を submodule へ再帰させる) も不十分と判明した。**
  `git status --ignored=matching` は ignored ディレクトリを**ディレクトリ単位で折り畳む**
  (出力は `!! build/` であって配下の file 名ではない)。既に `build/` がある状態で
  内部 file の bytes・mtime・mode を変えても status 文字列は変わらない。
  さらに initialized な CCBench には最初から ignored build dir があるため再帰 fingerprint は
  初期状態で非空になり、これを通すために空判定を baseline 判定へ緩めると盲点が復活する。
- **worktree の外の副作用も残る。** 共有 build cache、ccache、`$HOME` 配下、`/tmp`、
  共有 git module cache、PBS 側の状態は worktree を捨てても残る。
  `-p no:cacheprovider` は pytest の CacheProvider しか止めない。
  状態隔離を worktree の中だけで完結して証明できない。
- 「速くなった」と記録しながら regression 見逃し経路を残すのが最悪の結果である。
  利得より重い。

**却下した選択肢:**

- initialized submodule がある場合だけ再利用を諦める fallback — 安全だが、実測対象は
  必ず initialized なので利得がゼロになる。実装する意味がない。
- 再帰 fingerprint を足して再利用する — 上記のとおり ignored ディレクトリの折り畳みにより
  内容変化を捉えられず、隔離の証明にならない。
- node 間で submodule working tree を `git clean -xdff` する — 再帰・外部状態・
  tracked metadata をリセットせず隔離の証明にならない。再帰 clean を足せば
  毎回ビルドし直すことになり、再利用の利得を消す。

再訪条件: probe の状態隔離を「何によって証明するか」の設計が先に立ったとき。
worktree 内の status では足りないことが本 wave で確定したので、
内容ベースの再帰 manifest か、probe を状態から切り離す別の隔離機構が要る。

## {{D:collection-cache-residual-selector-risk}}. 非帰属 probe の collection cache は、selector 誤選択の残余リスクを受け入れたうえで採用する

**決定:** 同一 `(tip, path)` に対する `pytest --collect-only` を 1 回に cache し、
receipt の `collections` を distinct key ごとに 1 entry へ畳み込む。
**閉じきれない残余リスクが 1 つあることを明示して受け入れる。**

**理由:**

- 利得は全数実測で確定している。過去 receipt 130 件で collect-only dispatch は 476 回、
  distinct `(receipt, path)` へ畳むと 169 回になる (307 回削減)。
  node 数が多い receipt ほど distinct path が少なく (37 node で 3 path、
  26 node で 1 path が 7 receipt)、痛いところほど無駄が大きい構造だった。
- テストは 1 件も間引かない。全 node の単一 node rerun は維持する。
- consumer 契約を壊さない。`collections` の件数を縛る述語は live code に存在しない
  (root 9 field と collection 6 field の形だけを検査し、`len` も node との対応も見ない)。
  `checker_receipt_sha256` の chain は digest の**形**しか検査せず内容へ束縛していない。
- **残余リスク:** cache 集合と真の集合が食い違うと、`_selector_from_collection` の
  prefix + 最長 + 一意 の規則の下で「有効だがより短い selector」が選ばれ、
  fail-closed にならないまま誤った node を再実行しうる。再 collection なしにこの穴は塞げない。
- 成立には 2 条件が要り、どちらも満たされにくい。
  (a) 同一 tip で collection が非決定的であること。本 wave で本番経路の独立 2 PBS job と
  login node の計 3 観測を比較し、62 nodeid が完全一致した (機種を跨いでも一致)。
  probe worktree は HEAD 一致と fingerprint 空を毎回 assert しており、collection の入力である
  木が同一であることは証明済みで、変わりうるのは環境だけである。
  (b) `X` と `X - Y` が両方 collected nodeid になる形であること。pytest の命名では
  関数名に空白は入らず parametrize は `[...]` を生み、`[` 始まりの suffix は規則で弾かれる。
- 到達可能な誤りは fail-closed である。cache 集合に対象が無ければ `InvalidInput`、
  suffix 規則を外れれば `InvalidInput`、存在しない selector なら pytest rc=5 で
  `{0,1}` 以外として拒否、rc=1 なら実出力と selector の一致を要求する。

**却下した選択肢:**

- 1 回の collection 観測を node 数だけ複製して `collections` の件数を保つ — 複製すると
  `request_id` / `submission_nonce` / `stdout_sha256` という 1 回の dispatch に固有の値が
  並び、26 回 dispatch した外観になる。証拠の捏造に近い。件数を縛る consumer は無く、
  「1 観測 = 1 entry」の方が実態を正直に反映する。
- cache 由来であることを示す field を `collections` entry へ足す — consumer が
  6 field ちょうどを要求するため receipt が拒否される。schema 変更は別裁定を要する。
- cache を採らない — 残余リスクは消えるが、本 wave の利得も消える。
  上記のとおり成立条件が実測で否定されており、割に合わない。

再訪条件: 同一 tip で collection が非決定的だと実測されたとき。
その時点で cache は撤回し、node ごとの再 collection へ戻す。
