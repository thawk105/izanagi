---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2153-witness-requested-us
seq: 2
---

## {{D:witness-multifile-sites}}. 複数 file に散る directive 箇所群は 1 macro の副 file 宣言として同じ深い鏡像で計装し、複数 file macro に限り箇所ごとの識別 marker で総数の相殺を拒否する

**決定:** D1490 / D2182 の compile-time 枝選択 witness に、1 macro が所有 TU 以外の file にも逐語 directive を持つ型を足す。
(1) 主 entry は既存 2-tuple のまま `_CONDITIONAL_BRANCH_WITNESSES` に置き、副 file は別 mapping
`_CONDITIONAL_BRANCH_COMPANION_SITES` (macro → (source_rel, start_directive, N) の tuple) に宣言する。`_declared_site_count` は
主宣言 file の N のまま (S1 fixture helper の consumer 契約)、総数は `_declared_total_site_count` (和) で導出し期待式 (N·v, N) の N に使う。
(2) 主 + 副を各々 no-follow capture して file ごとに N_i 箇所を計装し (file ごとの箇所数不一致は既存 reason
`compile-time-branch-site-count-mismatch`、detail に file 名)、副があれば主 == owner TU でも D1613 の深い鏡像を使い、全計装 file を
symlink 作成対象から除いて同じ shadow に書く。(3) **複数 file macro に限り**、各箇所に固有 marker
`IZANAGI_COMPILE_TIME_BRANCH_SITE_{SELECTED,COMPLETED}(f<i>s<j>)` を総数 marker の隣に挿入し、preprocess argv に token 貼り付けの
`-D…(k)=…_OBSERVED_##k` 2 本を足して、総数 (N·v, N) の判定の後に箇所ごとの要求 (1,1) / 対照 (0,1) と和 = 総数を
`compile-time-branch-site-observation-mismatch` で要求する。(4) 複数 file macro の green evidence にだけ `companion_sources`
(副 file の登録値と計装に使った capture) と `site_observations` (全箇所 × 両腕) の 2 key を載せ、green 再検証は副宣言の有無を登録簿から
決め (record の key から決めない)、row の型・順序・登録値・digest・identity・site 集合・各 row の値・和・両腕 argv の site marker define を
検査する。既存 dataclass に field を足さず、`proof_kind` も変えない。(5) 登録簿へ `BACKOFF_REQUESTED_US` (`cc/silo/transaction.cc` ×2 +
`include/backoff.hh` ×2、対照 0) を足す (枝選択 21 → 22、対応集合 22 → 23)。driver は配線しない (`backoff_requested_us` /
`backoff_sweep` / `screening_driver` は admission を成果物へ載せない、D1492)。

**主張の範囲:** 確立するのは「宣言した owner TU を当該 configure で前処理したとき、DefineSpec patch の逐語 N 箇所すべてで define の値が
枝の選択を決めている」ことまで。副 file の証拠はその owner TU と configure の include 文脈に限り、同 header を include する他 TU や
header 単体の意味は主張しない。箇所の活性は configure に依存し (abort() 内の箇所は `#if BACK_OFF` の内側)、`BACK_OFF=0` では
completed 3/4 で red になる (fail-closed、実測)。`BACK_OFF` を companion define にしない (検査する configure を変えてしまう)。

**理由:**

- 所有 TU 2 箇所だけの登録は D2161 (2) の部分登録であり、header 2 箇所が未観測のまま macro 名が未確立一覧から消える (前 wave が退けた過大主張)。
- 総数一致だけでは全箇所観測を含意しない。静的に構成できる反例 = owner の 2 箇所を外側 `#if 0` で殺し、`#pragma once` の無い header を
  2 回展開すると、各 file の逐語箇所数は 2 のまま総数は (4,4)/(0,4) になる (段 2 plan が指摘、段 3 の 2 レンズが独立に成立を確認)。
  箇所識別を足すと `f0s0=(0,0,0,0)` で拒否される (合成 fixture の独立 node と、評価側の直接検査で実測)。単 file macro では
  .cc の TU は再展開されず、header 単 file は N=1 で重複が総数に出るので総数で足り、既存 21 macro の計装・argv・record を変えない。
- 箇所固有 marker を `-D` の function-like macro + token 貼り付けで作ると、既存の総数 marker と同じくコメント / raw string 内では展開されず
  数えられない (D1490 の構造的 fail-closed を保つ)。g++ 11.4.0 で生死実験のうえ採用。
- header 宣言の既存例 (BACKOFF_NOINLINE) の深い鏡像 (D1613) は 1 file しか書かなかった。副 file を同じ鏡像へ書くとき、計装 file を
  symlink 作成対象から除かないと symlink 越しの write で元 source を書き換える (段 3 A / 段 2 plan の条件)。
- 副 file の証拠を record に載せないと、再検証が「主 2 箇所 + header 2 箇所」を裏付けられない (段 3 A の must-fix)。既存 dataclass に
  field を足すと既定値でも canonical JSON へ出て既存 record の bytes が変わる (D2182) ので、複数 file macro にだけ現れる key にする。
- 実 TU (pin e9e477ca1、fixed → requested-us、official 同形供給) で login と計算ノードとも (4,4)/(0,4) green / admitted / 未確立 []、
  `BACK_OFF=0` は (3,3)/(0,3) red。既存 SORT / NOINLINE / RUNG1 の record は変更前後で一時 path 由来の digest 以外同一 (代表 3 cell、
  他 18 macro の bytes 同一は主張しない)。

**却下した選択肢:**

- **所有 TU の 2 箇所だけで登録する** — 部分登録 (D2161 (2))。
- **総数 (4,4)/(0,4) だけで判定し、相殺は主張範囲の限定で対応する** — witness の主張「各箇所で値が枝を決める」が一般には偽になる。
  複数 file の型を足す本題の健全性であり、仮想リスク向けの新 gate ではない (段 3 B の判定)。
- **登録簿の value を tuple of tuples にする / `_CONDITIONAL_BRANCH_SITE_COUNTS` を file 別にする** — 2-tuple consumer 3 件と
  `_declared_site_count` の S1 consumer を壊す。別 mapping で持つ。
- **別 proof_kind / 既存 dataclass の optional field / 副 file 用 dataclass** — 同じ owner-TU 枝選択の主張に validator 分岐を増やすだけ、
  optional field は canonical JSON へ出る、新 dataclass は過剰 (段 2 / 段 3 B)。
- **`BACK_OFF=1` を companion にする** — 検査する configure を変え、`BACK_OFF=0` の red (fail-closed) を失う。
- **単 file の複数箇所 macro (RUNG1 / GATING) にも箇所識別を広げる** — 総数で足りる型に argv と record の変更を持ち込む (I1 違反)。
- **所有 TU 内の未宣言 directive の走査・include 専用 gate** — 前 wave と同じく裁定パッケージ候補のまま。
