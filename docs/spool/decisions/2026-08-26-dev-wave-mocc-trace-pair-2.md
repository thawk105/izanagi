---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-mocc-trace-pair
seq: 2
---

## {{D:mocc-trace-pair-gate}}. mocc の TRACE=1 / TRACE=0 pilot は、job が hash した証拠 bytes を束縛する事後 gate で「対」と認める

**決定:** `orchestrator/campaign/mocc_trace_pair.py` を、既存 verifier と TRACE=0 preprocess
identity checker の**出力を消費する事後 gate** として置く。両者の受理集合は変更しない。
対として受理する条件は次の積とする。

1. 全 leg で outer commit・ccbench base/new OID・cmake target・workload tuple・
   `mocc_trace` から `trace_mode` を除いた projection が一致する。outer commit は
   `--expected-outer-commit` で外から必須指定する。
2. `n_trace0 == n_trace1 >= 2`。exact な N は要求しない。
3. 規律 1 の分離を双方向で要求する。TRACE=1 leg は性能 artifact 参照と SHA が null で、
   receipt 内に性能 key が再帰的に存在しない。TRACE=0 leg は verifier artifact 参照と SHA が
   null で `verifier_rc` が `not-run`、receipt 内に verifier verdict key が再帰的に存在しない。
4. 渡された証拠 bytes の SHA-256 が、**job 自身が記録した SHA-256** と一致する。
5. 全 leg の `official_certification` と `eligible_for_refreeze` が strict boolean の false。

**理由:**
- 実装前の receipt は証拠 artifact を filename か null でしか指しておらず、
  **実 job が生成していない合成 JSON を certified として通せた。** 段 3 の 2 レンズが
  独立に同じ穴へ収束した。job 側が bytes を hash して receipt へ入れない限り、
  checker が計算する hash は「事後に渡された bytes の hash」にすぎない。
- 事後 gate にすることで、正しさ防壁 (規律 2) の受理集合を触らずに対の妥当性だけを検査できる。
- tracked policy 全体の byte identity は現行 receipt に該当 field が無く到達不能なので採らない。

**却下した選択肢:**
- **verifier / identity checker を改造して pair 判定を内蔵する** — 正しさ防壁の受理集合を
  変えることになり、規律 2 の攻撃面を自分から広げる。
- **散文で「対である」と書く** — 検証不能。台帳から再検査できない。
- **pair receipt を読む consumer gate を headline / certified 選択 / floor / oracle / fitness 側へ
  同時に新設する** — proof chain と oracle gate に触る。本 wave の依頼の射程外。
  `prohibited_uses` は宣言であって強制ではない旨を成果物本文へ明記し、裁定パッケージへ回した。

## {{D:mocc-pair-no-binary-sha-gate}}. 同一 mode の binary SHA 一致は pair の必須条件にしない

**決定:** pair checker は同一 mode の leg 間で `build.binary_sha256` が一致することを要求しない。
各 leg の値を記録し、一致したかを `same_mode_binary_sha256_equal` として真偽で残すに留める。
「同一 build 系統」は build の決定要因 — compiler version、cmake target、ccbench の base/new OID、
trace defines — の leg 間一致で担保する。

**理由 (実測):**
- 同じ ccbench source の TRACE=0 ビルドが 2 回で異なる binary SHA-256 を出した。
  本 wave の対に入れた 2 leg がそれ自体その例で、`same_mode_binary_sha256_equal` は false である。
- 機序は build source が jobid 依存の scratch path に在り、対象 executable が展開する
  エラーマクロが `__FILE__` を binary へ入れる一方、prefix-map を設定していないこと。
- `DW-O13` は「要求する値が実環境で到達可能か確かめてから述語を採用する。到達不能なら採用せず、
  測った値域を裁定へ書く」と定める。**この gate を採っていたら本 wave の対はそれ自身に
  拒否されていた。**

**却下した選択肢:**
- **prefix-map を足して binary を再現可能にする** — build flag を変えると binary bytes の
  意味が変わり、既存の binary identity 検査と過去の計測値の比較可能性に波及する。
  本 wave の依頼の射程外。
- **gate を残して落ちたら都度例外にする** — 到達不能な述語を恒常的な例外運用で維持することになり、
  gate の意味が失われる。

## {{D:mocc-pair-cardinality-not-relaxed}}. certified な leg が足りないとき、対の本数条件を後から緩めない

**決定:** `n_trace0 == n_trace1 >= 2` は実装前に決めた述語であり、実測の結果 certified な
TRACE=1 leg が想定より少なかったからといって事後に緩めない。数が揃わない側に合わせて N を
下げ、対から外した leg とその値を成果物本文へ全部書く。**緑が出るまで正しさの run を
追加投入しない。**

**理由:**
- 事後に `>= 1` へ落とすのは、規律 2 が禁じる「正しさゲートを緩める変異」と同型である。
  最適化圧力は必ず正しさを攻撃しに来るという前提で動く以上、自分の都合で緩める前例を作らない。
- 正しさの run を緑が出るまで回して緑だけを報告するのは selection bias であり、規律 3 の
  「なぜ壊れたかを次の一手のシグナルにする」に反する。anomaly は隠すのではなく構造化して残す。

**却下した選択肢:**
- **本数条件を非対称 (`n_trace1 >= 1`) にする** — 対称性は「対」の定義の一部として段 4 で
  決めたものであり、データを見てから定義を変えることになる。
- **certified が 3 本揃うまで TRACE=1 を投げ続ける** — 上記の selection bias。
- **anomaly の出た run を無かったことにする** — 規律 2・3 の直接の違反。
