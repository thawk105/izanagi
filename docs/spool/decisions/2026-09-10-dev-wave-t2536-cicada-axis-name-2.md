---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-10
wave: dev-wave-t2536-cicada-axis-name
seq: 2
---

## {{D:genome-axis-cache-name-table}}. genome 軸名から CMake cache 変数名への写像は静的表 1 本で持ち、送り手と受け手が共有する

**決定:** genome の軸名は C++ マクロ名のままとし、CMake cache 変数名への写像を
`orchestrator/campaign/model.py` の静的表 `GENOME_AXIS_CMAKE_CACHE_VARIABLES` 1 本で持つ。
`Genome.cmake_defines()` (送り手)、`orchestrator/calibrator/cli.py` の受領証 genome 復元 (受け手)、
`orchestrator/campaign/screening_driver.py` の局所組み立ては、すべてこの 1 本を経由する。
そのうえで次の 4 つを帰結として固定する。

1. 表に無い名前は `CCBENCH_<名前>` の恒等写像へ落とす。この fallback は撤去しない —
   silo の genome は patch が供給する `BACKOFF_FIXED` などを持ち、既存の受領証と argv がこれを要求する。
2. 同一 protocol 内で 2 軸が同じ cache 変数へ写る表は、正引き・逆引きとも fails-closed で拒否する。
   逆引きで複数の軸が一致した場合も拒否する。
3. 受け手は旧汎用名を受理しない。逆引きは候補軸を正引きへ戻して元の名前と一致しなければ拒否する。
   旧名と新名の両方を通す alias にはしない。
4. 対応の検査は 2 つの独立した実体を突き合わせる。izanagi 側の宣言表と、CCBench の
   `cmake/Options.cmake` と `cc/<protocol>/CMakeLists.txt` を既存 parser
   (`source_digest._parse_supplied_macro_details`) で読んで得た表である。
   宣言表から CCBench 側の期待値を生成してはならない。

**理由:**

- 汎用写像 `-DCCBENCH_<軸名>` は cicada で誤りである。cache 変数は
  `CCBENCH_INLINE_VERSION_OPT_CICADA` であり、汎用名で渡すと CMake が未使用と報告して値が
  コンパイラへ届かない。genome は build の忠実な写像でなければならない (D1864 決定 1)。
- 送り手と受け手が別々の辞書を持つと、正方向と逆方向が独立に drift し、同じ欠陥を別の場所へ
  移すだけになる。逆表は静的に宣言せず、正方向表から完全一致で逆引きする。
- 単射性を検査しない表は、名前の対応が一致していても壊れる。2 軸が同じ cache 変数へ潰れると
  canonical genome には別々の値が残る一方、コンパイラには後勝ちの 1 値しか届かない。
  既存 parser は同じ左辺の衝突は拒否するが、この形は通す (親が probe で実測)。
- 検査を izanagi 側の表から生成すると恒真化する。D1863 が要求する「2 つの独立した実体の突き合わせ」の
  形を保つ必要がある。実行時に CCBench を parse して変換する案も、検査対象と期待値が同じ実体から
  出るため同じ恒真化に落ちる。

**却下した選択肢:**

- **cicada の genome 軸名自体を cache 名へ変える** — cache 名が論理軸へ漏れ、`Genome.canonical()` と
  variant identity が変わる。軸名が C++ マクロ名であることは build の忠実な写像の一部である。
- **受け手で旧汎用名と実体名の両方を受理する** — コンパイラへ届かなかった旧 configure argv を
  正しい genome として認定できてしまう。D1864 が却下した alias 正規化そのものである。
- **実行時に CCBench の CMake を parse して変換する** — build と受領証復元が submodule の可用性へ
  依存し、かつ検査の 2 実体照合を失う。CMake parser はテスト内だけに置く。
- **検査のために新しい CMake parser をテスト側へ書く** — 既存 parser と意味論が二重化する。
  既存 parser は bracket argument・裸 option・universal と protocol OPTIONS の合成を既に扱う。
- **表の件数や「非恒等写像は 1 件だけ」を固定値で pin する** — 軸集合の独立 pin の弱い実装であり、
  SPACES・CCBench・表を同時に正当拡張しても単独で赤になる。実体表との exact equality で契約は閉じている。
- **`parse_options_defaults` の戻り値を「宣言済み cache 名の一覧」として使う** — 同 parser は空値の
  cache entry を意図的に除外するため、CCBench が既定値を空にする正当な変更だけで偽赤になる。
