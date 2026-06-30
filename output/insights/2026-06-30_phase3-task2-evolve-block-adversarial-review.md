# Phase 3 タスク2 (EVOLVE-BLOCK template patch) の敵対レビュー結果

- **日付:** 2026-06-30
- **対象:** Phase 3 kickoff タスク2 — `backoff.hh` の `BACKOFF_FIXED` 骨格に EVOLVE-BLOCK マーカーを画定
  (coder の編集面)、template patch (`silo-backoff-fixed.patch`) 再生成、`patches/README.md` + テスト追加
- **方法:** 多エージェント workflow (3 レンズ = 観測者効果 / 偽 cache hit / scope・規律) で実機反証を試み、
  各 finding を独立エージェントが裁定 (確定 4 / 棄却 3)。10 エージェント / 約 45 万トークン。
- **位置づけ:** izanagi 内部の設計レビュー記録 (CCBench バグではないので上流還元は無関係)。

---

## 確定した指摘 (4 件)

### F1 (medium) — `Options.cmake` は ALLOWLIST 内だが digest 対象外 → 偽 cache hit
**根:** `source_digest.py` で digest 対象 `EVOLVE_BLOCK_SOURCES = ("include/backoff.hh",)` に対し、編集許可
集合 `ALLOWLIST = {"cmake/Options.cmake", "include/backoff.hh"}` が真に広い。`Options.cmake` は
`parse_options_defaults()` のデフォルト供給源としてのみ使われ、**その内容は digest の pre-image に入らない**。

**実機 exploit (検証済み・実験後 revert 済み):** ピン commit `dff0f1e`、stock silo genome
{BACK_OFF=1, NO_WAIT_LOCKING_IN_VALIDATION=1, NO_WAIT_OF_TICTOC=0, WAL=0} に対し `Options.cmake` の
`CCBENCH_VAL_SIZE` を 4→4096 に変えても、allowlist gate=PASS / src_token=stock / cache_key / variant_id が
すべて不変。`VAL_SIZE` は全バイナリの `-D` に出力され `ycsb.hh` の `char val_[VAL_SIZE]` (struct layout) と
`memcpy` を駆動する = 確実に別バイナリなのに identity 不変 = 偽 cache hit (規律2 への直撃)。

**D23 防御の穴:** D23 は「Options 値変更は backoff.hh の preprocess digest に伝播する二重計上」を却下理由と
したが、伝播するのは backoff.hh の `#if` が参照するマクロ (`BACKOFF_FIXED`/`BACKOFF_NOINLINE`) だけ。
`VAL_SIZE`/`KEY_SIZE`/`MASSTREE_USE` は backoff.hh が参照せず silo genome.flags にも無いため伝播ゼロで digest 盲。

**対応:** タスク3 (H3 hook) で coder の編集面を EVOLVE-BLOCK の `#if` 枝に絞り、`Options.cmake` (人間 template
専有) への coder 書き込みを拒否することで発火経路を構造的に閉じる。identity 側で塞がない理由は D24 (後方互換 +
D7 編集面隔離 + 恒久 honest 化は configure 最終 -D 集合の digest として cicada/oze 拡張段に繰延)。現状は
coder 未実装ゆえ発火経路が人間 template のみで潜在。

### F2 (low) — `-undef` cpp は `#if` 枝内の build 時マクロ・builtin を素通し
digest は backoff.hh を `g++ -E -P -undef -nostdinc` で単独 preprocess する。実ビルドが供給するが digest の
`-D` 集合に無いマクロ (`NDEBUG`/`__OPTIMIZE__`、TU 先頭 `#define GLOBAL_VALUE_DEFINE`、`__builtin_*`) を
coder が `#if` 枝の active コードに書くと、識別子が**テキストのまま**残り digest に入る = digest は「書いた
文字列」は区別するが「その識別子が build 時に取る値」を覆わない。`#if/#elif` selector 側は `-Werror=undef` が
fails-closed で守るが、active 枝の値素通しは捕まらない。**現 wiring では実害なし** (ビルドは Release 固定で
これらは定数、per-genome に変わるのは genome.flags のみ)。D23 道Y が「領域内の生条件指令・非決定 builtin を
hook 禁止」と既に認識済みの面 → タスク3 scope。

### F3 (nit) — phase3.md の `#if <AXIS> > 0` と実装 `#if BACKOFF_FIXED >= 0` の境界不一致
phase3.md §EVOLVE-BLOCK 機構が合成枝を `> 0` (strictly greater) と記述するが、実装・コメント・README・
Options.cmake・D18 はすべて `>= 0` / sentinel=-1 規約。値 0 の意味 (実装=合成枝 0us / 文言=stock) が逆転して
いた。**タスク2 commit で phase3.md を `>= 0` 規約に整合修正済。**

### F4 (nit) — 領域内の説明コメントに生プリプロセッサトークン文字列が埋まっていた
EVOLVE-BLOCK 領域先頭の説明コメントに `#if`/`#ifdef`/`#elif`/`#include`/`__DATE__` の文字列が含まれ、タスク3
hook が素朴な substring 走査だと in-comment 文字列を誤検出する罠。**タスク2 commit でコメントを散文化し生
トークンを除去済** (「条件指令 (if/ifdef/elif 系)」「非決定ビルトイン (DATE/TIME 系)」等)。加えて hook は
**行頭アンカー** (`^\s*#`、コメント除去後) で走査する方針を phase3.md タスク3 に明記。

---

## 棄却した指摘 (3 件、設計通りと裁定)

- **`#else` 枝の改変は digest 不感 (not-a-bug):** `cpp -P` が非選択枝を落とすため active 枝のみ digest が覆う
  のは原理的に正しい。枝を選ぶ `BACKOFF_FIXED` 自体が canonical/cache_key に入るため `#if`/`#else` の active
  枝が入れ替わる二重キャッシュは成立不能 (実機で衝突しないことを確認)。
- **`#else` 不可触は「ドキュメント約束のみ」、機械執行は hook 待ち (nit):** その通りだが設計通りの非ブロッキング
  繰延。digest は `#else` 改変を cache-miss/drift として扱い (偽 hit ではない) ので規律2 防御は崩れない。
- **`#if BACKOFF_FIXED >= 0` の signed 比較が未定義時 fixed-0 枝へ倒れる (nit):** cmake CACHE default -1 +
  source_digest の `-Werror=undef` の二重ガードで未定義経路は到達不能。潜在的な防御脆さの指摘に留まる。

---

## タスク2 の健全性 (結論)
マーカー導入のコア (inert 不変) は無傷: 確定 finding のうち F3/F4 は doc/comment の hygiene で commit 修正済、
F1/F2 はタスク2 由来でなく source_digest (タスク1/D23) の既存被覆ギャップで、タスク3 (H3 hook) の scope に
取り込んだ。inert digest は `7664020a` 不変、silo 8 golden id 不変、preprocess 後出力は HEAD 原本と byte 一致。
