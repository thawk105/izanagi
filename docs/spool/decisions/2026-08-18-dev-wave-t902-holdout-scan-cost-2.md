---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-18
wave: dev-wave-t902-holdout-scan-cost
seq: 2
---

## {{D:holdout-scan-coefficient-only}}. holdout live scan の最適化は係数削減に限り、読取経路と例外契約は変えない

**決定:** `s8b_holdout_freeze.search_repository` の最適化は、report の canonical bytes を
1 bit も変えない範囲の**係数削減**に限る。全対象 file の列挙・open・read・decode は維持する。
prefilter を強めるときは新しい regex 文法を自作せず、既存 `_derive_required_literal` を
1 要素 mapping `{axis: expression}` で軸ごとに呼び直す形だけを使う。
memo は 1 回の `search_repository` 呼出しに閉じ、`texts` object の identity へ束縛し、
内容変化は fail-closed で拒否する。

**理由:**
- 「ファイル数比例をやめる」は出力契約と両立しない。`skipped_binary_count` は全 file の
  binary / UTF-8 判定を要し、regex hit は file の任意位置にありうるので先頭だけ読む短絡ができず、
  exact 免除の判定は全 bytes の SHA-256 を要する。
- 律速は Python overhead ではなく共有ファイルシステムのメタデータ遅延である
  (stat 163 us/file、open+read+close 346 us/file、`pathlib` と raw syscall の差は 10 us 未満)。
  file ごとに触る回数を減らす以外に比例は消えず、それは受理集合に触る設計変更になる。
- 新しい literal 導出文法は false negative 面を増やす。量指定子が literal 末尾に掛かる形
  (`(?:k=0*)` の prefix を `k=0` とすると `k=` を落とす) は、無作為 40 万試行の fuzz で
  prefilter 適用 78 件中 5 件の反例が出た。既存 helper は未対応 grammar を `None` へ倒す
  保守性を既に持ち、その正しさは既存テストが固定している。
- prefilter の false negative は holdout hit の見落とし = 未既知性の偽保証であり、
  検索式の陽性対照は別 literal で生き残るため fail-closed 検査を素通りする。

**却下した選択肢:**
- `path.is_file()` を open 後の `os.fstat` へ畳む — 実測で 18% 相当の削減があるが、
  directory / symlink 先の特殊 file / FIFO / Unix socket / device / dangling symlink /
  列挙後の削除 race / stat 権限不足 / NUL を含む path の 9 系統で、例外の型・文言と
  「そもそも open しない」現行挙動を保存できない。性能を理由に厳密等価性は緩めない。
- 各 alternative の value literal prefix まで導出する自作 parser — 追加削減は約 5% にとどまり、
  量指定子・escape・文字クラス・inline flag・空 alternative・nested group・非 ASCII を
  自前で正しく扱う負債に見合わない。
- `git grep` / `--cached` / 結果 cache への読取経路置換 — 対象集合が既に一致しない
  (worktree grep と in-memory 列挙で件数が違う)。untracked / submodule / worktree bytes と
  binary / UTF-8 / 免除の意味論を別途証明しない限り受理集合を静かに変える。
- 出力に現れない `per_axis_paths` の順序を保つための全件再走査 — report には件数しか出ず、
  conjunction は別途 sort される。順序を守る変異は等価変異であり、それを固定するテストは
  ファイル数比例の走査を設計契約として凍結してしまう。

## {{D:equivalent-output-mutation-needs-firing-count-guard}}. 出力等価な最適化変異は発火回数で番人を張る

**決定:** 検索の prefilter のように「結果を変えずに走査量だけを減らす」層を入れるときは、
report 比較だけを番人にしない。同じ入力に対する検査器の**発火回数**を、
最適化あり / 中間層だけ無効 / 完全 slow path の三段で分離できる fixture を置き、
各段の回数を exact に固定する。

**理由:**
- prefilter を wave 前の形へ戻す変異は出力が変わらないため、canonical bytes の等価性テストでは
  1 件も殺せない。実測でもこの変異は発火回数を見る node でだけ赤になった。
- 従来の「slow path」比較は helper 1 つを `None` へ差し替えるだけだったため、
  新しい層がその外側にあると optimized と slow が同じ経路を通り、assert が恒真になる。
  検査器そのもの (`_scan_one` に相当する単位) を、prefilter も memo も持たない
  reference 実装へ差し替え、reference が期待回数だけ呼ばれたことまで assert する必要がある。
- 三段分離は fixture の中身に依存する。中間層だけを通す入力 (共通 literal は含むが
  軸 literal は含まない text) を意図的に置かないと、段が縮退して検出力が消える。

**却下した選択肢:**
- production API に prefilter 無効化 knob を足して比較する — 防壁の迂回口を製品側へ残す。
- 出力へ path 一覧を足して順序を検査可能にする — schema と canonical bytes が変わる。
