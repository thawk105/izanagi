---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-15
wave: dev-wave-t1851-c3c-official-floor
seq: 2
---

## {{D:condition-detail-both-ends}}. condition gate の拒否は全 red record の detail を先頭と末尾の両方で残す

**決定:** `orchestrator/campaign/s1_direct_comparison.py` の
`_condition_records_for_genome` は、admission が拒否を返したときに **supply / meaning 両 arm の
全 non-green record** について `macro` / `arm` / `reason_code` に加えて `evidence.detail` を
拒否本文へ添える。1 件目だけにしない。

detail の整形には**診断専用の byte 予算**を同 module 内の定数として置き、予算を超えるときは
**先頭と末尾の両方を残して中央を省略**する。省略の印、省略した bytes 数、引用整形した全文の
sha256 を添える。予算の値は観測された診断長への倍率で決め、根拠を comment に書く。
「切り詰めが起きない」とは書かない。

拒否本文は整形を試みる前に確定させる。整形側の例外は `Exception` 境界で捕らえて固定文字列へ
置換するだけとし、**元の gate 拒否を置き換えてはならない**。`BaseException` は捕捉しない。

**gate の受理集合・reason code 語彙・admission 判定・rc・green 経路の bytes は変えない。**
`condition_meaning_gate.py` は変更しない。同型の「record を作って捨てる」を持つ兄弟 driver へ
**横展開しない**。

**理由:**

- D1912 が `p3_s4_loop.py` で直した欠陥と同型の破れが、official 床値 campaign の materializer で
  再現した。D1912 自身が `DW-G03` (族一般化には独立 2 例) を理由に横展開を保留していたので、
  第 2 実例が出た時点で条件が満たされた。直すのは走行を実際に塞いでいる 1 箇所だけとする。
- gate 専用の isolate worktree は `/scr` にあり job 終了で消える。reason code 2 語だけを上げると
  失敗本文 (rc・stderr・argv) が永久に失われ、**同じ投入を繰り返しても新しい情報が得られない**。
  official 床値は 3 回の投入で初めて原因に到達した。
- **argv 用の byte 予算を診断本文へ流用したのが初稿の誤りだった。** argv は先頭に command が来るので
  先頭を残す切り詰めが正しいが、コンパイラ診断は末尾に結論が来る。先頭だけを残す切り詰めでは、
  残るのは `In file included from` の連鎖だけで原因が判らない。実機の走行で観測された 1057 bytes の
  診断のうち、後半 557 bytes に fatal error 行があった。
- 全文 sha256 と省略 bytes 数を添えるのは、切り詰めた detail どうしが同じ印に潰れるのを防ぐためで
  ある。先頭と末尾が同じで中央だけ異なる 2 つの診断は、印がなければ区別できない。

**却下した選択肢:**

- **`condition_meaning_gate` の argv 用定数を書き換える** — argv の切り詰めは先頭優先で正しく、
  そこを診断本文に合わせると argv 側の可読性を壊す。予算の意味が違うものを 1 つにまとめない。
- **先頭だけ、または末尾だけを残す** — 前者は原因を落とし、後者は失敗した TU と include 連鎖を
  落とす。どちらも単独では診断にならない。
- **切り詰めをやめて全文を載せる** — 診断長に上限が無いので、拒否本文が無制限に伸びうる。
- **兄弟 driver (`p3_kickoff` / `p3_s4_loop_sort` / `backoff_sweep`) へ横展開する** — 依頼が
  一般化を scope 外と明示しており、それらで同型の破れが実在した観測もまだ無い。
- **拒否を送出せず record を保存して続行する** — 正しさゲートを緩める向きであり、絶対規律 2 に反する。
