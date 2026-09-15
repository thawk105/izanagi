# 段 1 brief — [T-2266] 静的 backoff tail の残帯 901〜998 マイクロ秒

worktree = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-tail-band`、
branch = `worktree-dev-wave-t2266-tail-band`、基点 local main = `0600887d9`。

## 1. 依頼 (逐語の要旨)

正式系列 `run_kind = t2266-tail` の残る帯 901〜998 マイクロ秒の標本を取る。1000 マイクロ秒の
正式標本は取得済みで 2026-09-10 に 3 workload へ投入済み。**まず既投入分の回収・解析が済んでいるかを
`output/insights` で確かめ、済んでいなければ回収から始めて再投入しない。** 投入経路は
`orchestrator/campaign/b10_backoff_static_tail_formal.py`。規律 2 を緩めない。Codex author = D95。
本題の実測だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。

## 2. 段 0 で親が実測した前提 (一次資料で裏取り済み)

- **(F-1) 既投入分は回収・解析とも完了している。** `output/insights/2026-09-10/t2266-formal-1000us/README.md`
  が 3 workload の median throughput・abort 率・rep 単位の生値まで表で持つ (job 988519 / 988520 / 988521)。
  `requested_us` = `realized_us` = (150,200,300,500,750,1000)、`unrealized` は空。
  **→ 回収から始める必要はない。再投入もしない。依頼の前提条件は満たされている。**
- **(F-2) 走行中の job は無い。** `qstat` の出力はゼロ行。
- **(F-3) 帯 901〜998 は、どの登録格子にも 1 点も含まれない。**
  `orchestrator/campaign/backoff_extended_sweep.py:86-87` の
  `T2266_REQUESTED_US = T2266_REALIZED_US = (150, 200, 300, 500, 750, 1000)`。点を絞る CLI 引数も無い。
- **(F-4) 依頼が名指した driver は、この帯を測る口を持たない。**
  `b10_backoff_static_tail_formal.py` の走行種別は `t2500-tail-formal`、格子は事前登録
  `docs/b10-backoff-static-tail-preregistration.md` §4.1 が凍結した右 tail =
  境界参照 1000 + 1250 / 1768 / 2500 / 3535 / 5000 / 7070 / 9999 の 8 点。同 §8.2 は
  「格子・動作点・判定値をコード定数で置換しない」と要求する。**帯を測るには使えない。**
- **(F-5) 帯の両端は 3 workload とも実測済みである。**
  左端 900 = 拡張格子の実測 (0〜900 の有効 28 点、`output/insights/2026-09-02_t2216-adaptive-backoff-nonmonotonicity-mechanism.md:210`)。
  右端 999 = `t2266-tail` v1 (2026-09-07、job 979843 / 979844 / 979845)。さらに 1000 = v2 (F-1)。
  999 と 1000 の median throughput の差は −0.22% / −0.27% / −0.66%、abort 率の差は 3 workload とも 0.0001 以内。
- **(F-6) 帯の内部は両端と同一の code 枝を通る。** 符号化は `b <= 999` で raw = `b`
  (`backoff_extended_sweep.py:69`)。raw 901〜998 は 900 や 999 と同じ商 0 の定数枝であり、
  raw `[1000, 2999]` の発行禁止域にも触れない。**測れないのは符号化ではなく、格子に無いからである。**
- **(F-7) 凍結格子へ点を足す形は、同型の場面で既に却下されている (D1848、2026-09-09)。**
  「探索走は凍結格子へ点を足さず、専用 RUN_KIND と専用 campaign identity で分離する」。
  却下欄は「既存 `t2266-tail` を一般化して両方を扱う — 凍結済みの成果物名と consumer に触れる risk」を
  名指しで退けている。**したがって `T2266_REALIZED_US` を書き換える実装は採らない。**
- **(F-8) 主張の上限は D1724 (2026-09-07) が定めている。** 静的 tail (150〜999) について書けるのは
  記述的な会計まで。当てはめは 6 点 × 3 workload = 18 点で行われ、再構成誤差は 0.064% 以内。
  D1724 の「B-10 に残るもの」列挙は待ち方 grid の判定・真の静的 1000・adaptive の 3 定数であり、
  **901〜998 の帯を残件として挙げていない。**
- **(F-9) 未投入の本走が 1 本ある。** `t2500-tail-formal` (右 tail 8 点 × 3 workload、約 20 分/job、
  sweep 上限 11700 秒・PBS 予約 18000 秒の内側)。driver は T-2566 が、Pegasus 投入経路は T-2593 が
  着地させ、どちらの insight も「本走の投入は行っていない」と明記する。手順書は
  `docs/b10-backoff-static-tail-submission.md`。**新規 Pegasus 実行体は要らない (F660 に触れない)。**

## 3. 研究前進 — 親は帯の測定について示せていない

**(P1) 親の provisional 裁定・攻撃対象: 帯 901〜998 の内部点を測っても、進む論文の主張・図表・実験が
1 つも無い。** 根拠は F-5 / F-6 / F-8 — 両端が実測済みで差は 0.66% 以内、内部は同一 code 枝、
主張の上限は D1724 が記述的会計に固定しており内部点で動かない。下流成果物 (歩行 model・13 点較正・図) は
schema v1 と 999 に束縛されたままで、v2 すら渡せない ([T-2562] へ分離済み)。
**「T-2266 の項目が閉じる」は帳尻であって研究前進ではない** — 同じ語を 1000 の wave 自身が使っている
(「埋まったのは帳尻であって知見ではない」)。

**(P2) 親の provisional 裁定・攻撃対象: 依頼の 2 つの指定 (帯 901〜998 / driver
`b10_backoff_static_tail_formal.py`) は同時に満たせない。** F-3 / F-4。どちらを依頼の本体と読むかで
作業が変わる。親の暫定読みは「依頼者は『静的 tail に残っている実測』を 1 つ進めたい。帯の語は
worklog 1416 の残件表記の写しであり、driver 名は未投入の本走を指している」である。

## 4. scope 候補 (段 4 で 1 つに裁定する)

- **O-A: 専用 RUN_KIND を D1848 の形で足し、帯から数点を測る。** 実装面あり (Codex author 必須)。
  凍結格子は触らない。3 job。(P1) が real なら研究前進を示せない。
- **O-B: 測らず、帯が両端の実測で挟まれていることを一次資料で示し、項目の閉じ方を提案する。**
  実装ゼロ・実測ゼロ。依頼の「本題の実測だけ」に反する読みになりうる。
- **O-C: 名指された driver の本走 (`t2500-tail-formal`) を手順書どおり投入・回収・集団報告する。**
  実装ゼロ、新規実行体ゼロ、3 job × 約 20 分。事前登録済みの飽和判定という研究前進が 1 行で書ける。
  帯は測らない。

## 5. 不変条件 (どの O を採っても緩めない)

1. **規律 2。** anomaly を検出した点・集団は即 reject。正しさゲートを緩める変更を一切採らない。
   `payload.certified is True` が正しさの権威であり、`verdict` 文字列や report の `certified` ではない。
2. **凍結境界。** `T2266_REQUESTED_US` / `T2266_REALIZED_US` / `EXTENDED_SWEEP_US` /
   事前登録文書の bytes を変えない (D1848、事前登録 §8.2、規律 7)。
3. **性能は未認証のまま扱う。** 取得値を根拠に variant を採用しない。
4. **投入したら作業ツリーを汚さない。** 走行中に書いてよいのは `output/` 配下だけ (F936)。
   実装面があるなら投入前に commit する。
5. **scope 外。** 仮想リスク向けの gate・検査・台帳・一般化を足さない (依頼の明示)。
6. 規律 4。飽和する最小規模を使い、点数・rep を無造作に増やさない。

## 6. 成果物の形

`output/insights/2026-09-15_t2266-tail-band/README.md` 1 本 + spool fragment。
O-A / O-C なら測定値の表 (workload × 点 × rep 生値、median、abort 率、変動係数、job ID) と
correctness の判定を含む。O-B なら「測らない」判断の一次資料と、項目の閉じ方の提案。
**どの O でも、測っていないものを測ったと書かない。**

## 7. 並列分割方針

段 2 = plan 1 本 (read-only)。段 3 = 敵対相談 2 本、レンズを分ける —
sol = 「(P1) は誤り。帯の測定には研究前進がある」を最強の形で立証しにいく。
luna = 「(P2) の親の読みは誤り。依頼は帯を literal に要求している」および O-A の実現可能性を攻める。
実装面が生じるのは O-A だけで、その場合だけ段 5・6 に Codex author を立てる。
O-B / O-C は実装面ゼロなので段 5・6 を省き `4→7→8→9` とする。

## 8. 変更面アンカー表 (O-A を採った場合にだけ触る)

| path:anchor | 役割 | 触れてよいか |
|---|---|---|
| `orchestrator/campaign/backoff_extended_sweep.py:81-90` (`RUN_KINDS`, `T2266_*`) | 走行種別と格子の定義 | **既存 3 種別の値は不可。** 第 4 種別の追加のみ |
| `orchestrator/campaign/backoff_extended_sweep.py:55-58` (`EXTENDED_SWEEP_US`) | 認証済み格子 | 不可 |
| `tools/pegasus/submit_b10_backoff_grid.sh` | 投入経路の `--run-kind` 受理 | 第 4 種別の追加のみ。既存 3 種別の受理集合は不変 |
| `orchestrator/tests/test_backoff_extended_sweep.py` | 格子・符号化の pin | 追加のみ。既存 literal は不変 |
| `docs/b10-backoff-static-tail-preregistration.md` | 凍結事前登録 | 不可 |
| `orchestrator/campaign/b10_backoff_static_tail_formal.py` | 本走 driver (t2500) | 不可 |
