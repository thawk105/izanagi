---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-18
wave: dev-wave-t1086-report-receipt
seq: 2
---

## {{D:post-run-store-receipt}}. oracle 実走後の store 再検証は報告の receipt で行う

**決定:** oracle 実走が終わってから observations を書くまでの窓について、report が各 cell の store
bytes を読み直し、その結果を observations の `store_reverification` receipt として発行する。
judge はこの receipt を observations の中から検査し、`judge_oracle` の呼び出し規約 (位置引数 1 +
keyword 3) と judge CLI の引数は変更しない。期待 SHA の唯一の源は
`ReverifiedFreeze.binaries_by_cell` であり、run 自身が WAL へ書いた値は使わない。

**この receipt が保証する範囲:** report が各 store を読んだ瞬間に freeze の SHA と一致したこと。
連続不変性ではない。一時的に改変され読み取り前に復元された場合と、読み取り後の差し替えは
検出しない。封印でも偽造耐性でもなく、主張の限度は「単独 oracle 改竄まで」である。

**理由:**
- 実走**前**には二重防壁があった (driver の実走前 store 再 hash と、pipeline の
  `expected_perf_sha256` による TOCTOU 照合)。実走**後**は report も judge も store を
  一度も読み直しておらず、この窓だけが無防備だった。
- judge は `--output-root` を持たず store を読む経路を構造的に持たない。したがって
  「読む側」は report にしか置けない。
- receipt を observations の中に載せれば、judge の consumer (judge CLI と
  combined verdict) の呼び出し規約を一切変えずに検査を届けられる。

**却下した選択肢:**
- **judge API に store の所在を渡す案** — consumer が広く、`judge_oracle` の呼び出し規約を
  変える影響が receipt の利得に見合わない。
- **最終 store seal を作る案** — 封印機構の新設であり、既に見送りが確定している
  observations 層の封印と重複する。
- **期待 SHA を WAL の `build_done.perf_bin_sha256` から取る案** — run 自身の自己申告になり、
  権威源が実走から独立しなくなる。`reverify_published_freeze` が返す値だけを使う。
- **receipt 欠落を緑にする案** — official observations に receipt が無いことを許すと、
  検査を消しただけで通る恒真な gate になる。欠落は judge が indeterminate にする。

## {{D:receipt-outer-state-rederived}}. receipt の総合判定は消費側が cell から再導出する

**決定:** `store_reverification` の outer `state` を judge が信じず、cell ごとの
`state` / `expected_sha256` / `actual_sha256` の整合を検査したうえで再導出し、
申告値と食い違えば理由を積む。cells は非空・重複なし・schedule の logical cell 集合と
完全一致であることも独立に要求する。judge は report 側の定数を import せず、
自分の closed schema 定数で検査する。

**理由:**
- 総合判定を自己申告のまま読むと、`state: "verified"` と書くだけで通る恒真な枝になる。
- cells が空または部分集合のとき、素朴な `all(...)` は空集合に対して真を返す。
  非空検査と完全被覆検査を先に置かないと、空 receipt が「全件一致」に化ける。
- producer の定数を consumer が import すると、片側の定数を緩めただけで両側が同時に
  緩む。独立な定数にしておけば、片方の変異がもう片方の検査で必ず露見する。

**却下した選択肢:**
- **outer state だけを見る単純形** — 上記の恒真枝をそのまま残す。
- **producer の定数を judge が import する案** — 検査の独立性を失う。
