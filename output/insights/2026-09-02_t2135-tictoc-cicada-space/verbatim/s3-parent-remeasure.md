# 段 3 レンズ A の指摘に対する親の再実測 (2026-09-02 00:20 JST)

レンズ A は親 brief の実測 3 点を「過大一般化」と指摘した。親が base commit
`c6a94ec998bba8c20c302105f28af3850f8134a6` の worktree で測り直した結果を記す。

## 指摘 1: tictoc `PARTITION_TABLE` の「死にフラグ」判定 — **指摘は正しい。検索範囲が不足していた**

親の初回検索は `cc/tictoc/*.cc`, `cc/tictoc/*.hh`, `include/` だった。これは
`cc/tictoc/include/` 配下と workload source (`ycsb_tictoc.cc` 等) を**取りこぼしている**。

再実測 (全件検索、`head` で切っていない):

```
grep -rn "PARTITION_TABLE" external/ccbench/cc/tictoc/ external/ccbench/include/ external/ccbench/common/
→ external/ccbench/cc/tictoc/CMakeLists.txt:7 の 1 件のみ (README を除く)
```

`cc/tictoc/` の実体は CMakeLists.txt / README.md / bomb_tictoc.cc / include / sbomb_tictoc.cc /
script / tpcc_tictoc.cc / transaction.cc / util.cc / ycsb_tictoc.cc であり、**すべて検索対象に入れた**。

repo 全体での `PARTITION_TABLE` の live site (`.cc/.hh/.h/.cpp`):

```
cc/cicada/util.cc:331-332   (print のみ)
cc/silo/util.cc:167          (print のみ)
cc/oze/util.cc:86-87         (print のみ)
```

**結論は変わらないが、根拠は今回はじめて成立した。** tictoc は print にも現れない完全な不在、
cicada は print 専用。いずれも探索軸にならない。**この再実測をもって notes の主張を支える。**
初回の brief の根拠 (`cc/tictoc/*.cc` と `*.hh` だけ) は不十分だったので撤回する。

## 指摘 2: `CACHE STRING` = 直交操作可能、の一般化 — **指摘は正しい。語を分ける**

「CLI から個別に指定できる」ことと「全組合せが異なる挙動を持つ」ことは別である。
tictoc の `#if NO_WAIT_LOCKING_IN_VALIDATION` / `#elif NO_WAIT_OF_TICTOC` がその反例で、
`(1,1)` は `(1,0)` と同一挙動になる。cicada の promotion も同型。

**依頼文の「直交操作できる軸」は前者 (個別指定可能) の意味で読む。** 後者は制約述語が担う。
notes ではこの 2 つを混同しない書き方にする。

## 指摘 3: `space_for` の caller 0 が「測定経路を開かない」の根拠になる — **指摘は正しい。根拠を差し替える**

`Genome` は registry を通さず直接構築して評価入口へ渡せるため、`space_for` の caller 数は
測定経路の閉包を証明しない。**親の根拠は誤りだったので撤回する。**

正しい根拠は次の 2 層で、**いずれも SPACES とは独立**である (親が実測)。

1. `orchestrator/campaign/between_run_floor.py:59` の `BASELINES` の key は
   実測で `['mocc', 'silo']` のみ。
   **【2026-09-02 01:05 訂正】** 初出時「`BASELINES[protocol]` を先に引くため `KeyError` で止まる」と
   書いたのは**誤り**。正しくは `_parse_cli_args` 末尾 (`:344-348`) が `protocol not in BASELINES` を
   `ValueError` で拒否し、`:361` の添字参照には到達しない。段 6 レビュー B が指摘し、親が実測で確認した
   (`tictoc -> ValueError: unknown protocol: 'tictoc' (選択肢: ['mocc', 'silo'])`)。
   fail-closed であるという結論は変わらない。SPACES への登録はこの dict を変えない。
2. その先の `between_run_floor.py:363` に D1373 の source 束縛 admission がある。
   親の実測で silo=True / mocc=False / tictoc=False / cicada=False。

**結論 (登録は測定経路を開かない) は維持されるが、根拠は差し替えた。**
レンズ A が「射影資料だけでは証明できない」と言ったのは正しく、親は射影外を読んで確かめた。

## この再実測が段 4 裁定へ与える影響

- tictoc `PARTITION_TABLE` 除外: **維持** (根拠を強化)。
- 「直交操作できる」の語義: **notes で書き分ける** (段 5 実装子への指示に含める)。
- 正しさ境界: **維持** (根拠を BASELINES + admission の 2 層へ差し替え)。
  新しい gate は追加しない (scope 外、既存の 2 層で fail-closed)。
