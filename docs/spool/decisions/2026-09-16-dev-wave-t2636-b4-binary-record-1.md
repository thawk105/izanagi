---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t2636-b4-binary-record
seq: 1
---

## {{D:floor-masstree-root-reaches-issuer}}. build が使った FetchContent masstree root は BuildResult 経由で receipt 発行へ渡す

**決定:** `buildcache.BuildResult` へ、`compiler_input_dependency_prefix_roots` と同じ性質の
additive field を 1 つ足し、build 成功時に既に読んでいる実効 masstree root をそのまま載せる。
floor 側は `current_compiler_input_masstree_root` を、sort_best の dependency binding があるときは
従来どおりそこから取り、無いときだけ result の新 field から取る。既定値は空で、legacy build を
含む既存 caller の挙動は変えない。sort_best 経路の値と分岐も変えない。

**理由:**
- `buildcache` は build 成功時に実 CMake cache から masstree の実効 root を読み、その結果
  compiler input は `fetchcontent-masstree` に分類される。しかし floor は同じ値を sort_best 専用の
  dependency binding からしか取らないため、offline 依存を供給した非 sort build では None が渡り、
  compiler input manifest の完全検証が root 不在で拒否する。**渡す経路が無いだけで、検査が過剰なのではない。**
- 同種の情報である dependency prefix roots は既に BuildResult 経由で floor へ渡っている。
  masstree root だけがその経路を欠いていた。**同型に揃えるのが最小で、意味も正しい。**
  receipt には絶対 root を保存せず live validation にだけ使う射程も同じである。
- 受理側は、正しい masstree 入力を使った非 sort build が root の伝達漏れだけで拒否されなくなる。
  拒否側は不変で、root 不在・root の重なり・per-entry の実 bytes hash 不一致は従来どおり拒否される。

**却下した選択肢:**
- floor 側で source dir を渡すのをやめる — 計算ノードは外部ネットワーク不在で、CCBench の
  トップレベル CMake は ThirdParty を無条件に include するため configure が落ちる。
- 呼び手が注入した builder seam の中で root を自己申告する — build が実際に使った値ではなく
  申告値になる。実 CMake cache から読んだ値を運ぶ形を崩さない。
- compiler input の分類規則や root 必須検査を緩める — 正しさゲートの弱体化であり採らない。

## {{D:calibrated-toolchain-resolved-by-path-not-by-relaxing}}. 較正が束縛する道具は PATH で実際に解決する。一致要求は緩めない

**決定:** 計算ノードの clean 環境で、登録済み較正が束縛する toolchain を解決できないときは、
**実在する道具の directory を PATH の先頭へ置いて解決する。** 呼出し時の引数として受け、
機械固有の path を repo の code へ hardcode しない。指定 directory が実在しない、または
非 directory なら起動前に fail-closed で拒否する。`floor_toolchain_matches` と
`_bind_current_toolchain` は編集しない。

**理由:**
- `dispatch_compute --task generic` は `env_mode=clean` で `MODULEPATH` ごと環境を落とす。
  較正取得 job は既定 module 環境を持つため、そこが供給する cmake が PATH から消えて
  system の別版へ落ちる。**環境が変わったのではなく、同じ機械の同じ道具が見えなくなっただけである。**
- gate の目的は「build の toolchain が較正のそれと同じであること」である。実物を PATH 上へ
  置くのは、その要求を**満たす**行為であって緩める行為ではない。
- 機械固有 path を code へ入れると、別 site で静かに誤った道具を掴む。引数で受ければ、
  どの道具を使ったかが呼出しの記録に残る。

**却下した選択肢:**
- 一致要求から cmake の leg を外す — 検査の弱体化であり採らない。
- 新しい較正を取り直す — 較正の取得は本 wave の scope 外であり、compiler の leg は既に一致している。
- 既定値として module path を code へ埋める — site 依存を隠す。
