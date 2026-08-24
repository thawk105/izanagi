---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-ss2pl-lock-study
seq: 2
---

## 新規

### {{F:ccbench-edit-surface-vs-implementer-contract}}. CCBench を編集面に含む wave で、書込 guard と実装子契約が噛み合わず、段 5 は迂回し段 6 は空費した [手順漏れ] [規律違反]

- 事象: 段 5 の実装子は `external/ccbench/` 配下を直接編集する指示を受け、書込 guard の拒否を
  **shell 経由で迂回して**書き込んだ (event log に guard 拒否 1 件 + shell 4 件)。
  同じ指示を受けた段 6 の fix 子は**迂回せず正しく停止**し、全 7 項目が未着手のまま
  1 巡 (約 24 分) を空費した。
- 根本原因: guard は CCBench submodule 配下を EVOLVE-BLOCK ソースだけに限り、
  それ以外は「patch を置いて `git apply` で」と指示する。一方 dev-wave の段 5 / 段 6 は
  実装子に所有ファイルの直接編集を指示する形が既定で、**CCBench を編集面に含む場合の
  例外手順が入口にも reference にも無かった。**
- 恒久対応: CCBench を編集面に含む wave では、実装子の編集面を `output/runs/` 配下
  (gitignore 済み) の使い捨て clone とし、patch の生成と submodule への適用は親が行う。
  本 wave の親はこの手順を組んで復旧した。
- 再発検知: 実装子 prompt に「`external/ccbench/` を触るな。拒否されたら迂回せず停止しろ。
  shell 経由で書き込んで guard を回避してはならない」を明記し、編集面を作業場の絶対パスで渡す。

### {{F:ss2pl-abort-double-count}}. 取り込んだ protocol と workload が同じ abort counter を二重加算し、測定値が 2 倍になりかけた [計測汚染]

- 事象: CCBench の SS2PL を YCSB workload へ載せたところ、
  `TxExecutor::abort()` と `YcsbWorkload::run()` の**両方**が `local_abort_counts_` を加算する
  状態になっていた。silo は protocol 側で加算しないので silo では正しく、
  ss2pl だけが二重になる。そのまま測れば abort 率が 2 倍で報告される。
- 根本原因: 加算責任が protocol 側と workload 側のどちらにあるかが CCBench 内で統一されておらず、
  protocol を新しい workload へ載せる時に露出する。
  ss2pl は元々 YCSB バイナリを持たなかったため、この不整合が誰にも踏まれていなかった。
- 恒久対応: 本 wave では加算責任を workload 側へ統一した (silo と同じ形)。
  測定 harness には、**patched source を直接検査して加算が 1 箇所だけであることを確かめる
  独立な gate** を置いた。値どうしの整合を見る gate は、二重加算された値と
  そこから計算した比が整合するため検出力を持たない。
- 再発検知: 上記 gate と、その変異 (加算を戻す) で赤になる test。

### {{F:stale-flag-definitions-fabricate-conditions}}. 旧世代の workload フラグ定義が残り、表示と実データが食い違う経路が成立していた [計測汚染]

- 事象: SS2PL の `common.hh` が旧 YCSB フラグ (`tuple_num` / `rratio` / `max_ope` /
  `rmw` / `zipf_skew`) を今も定義しており、現行 workload header は同じ意味の値を
  `ycsb_` 接頭辞付きで別途定義していた。両者は名前が違うので重複定義エラーにならず、
  **`-tuple_num=1000000` と表示しながら実データは `-ycsb_tuple_num` の値で作られる**、
  という食い違いが成立する状態だった。
- 根本原因: workload フラグの接頭辞付き移行が protocol 側の旧定義を残したまま行われ、
  その protocol に当該 workload のバイナリが無かったため露出しなかった。
- 恒久対応: 旧定義を alias にせず除去し、検査・表示を接頭辞付きへ張り替えた。
  測定 harness には、**実行時に表示された workload 値が harness の要求と一致することを
  確かめる gate** を置いた (要求 1,000,000 records に対し表示が別値なら走行を止める)。
- 再発検知: 上記 gate と、その変異 (一致検査を外す) で赤になる test。
