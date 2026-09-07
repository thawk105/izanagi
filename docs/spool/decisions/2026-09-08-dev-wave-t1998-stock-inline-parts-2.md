---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t1998-stock-inline-parts
seq: 2
---

## {{D:t1998-thin-launcher-single-job}}. balanced stock-inline の投入器は 1 job だけを出し、job body は既存物を無改変で再利用する

**決定:** T-1998 の薄い sanctioned launcher は、balanced 1 workload だけを 1 回 `qsub` する
新しい login 側投入器とする。計算ノードの job body は既存の A-5 job body を 1 byte も変えずに
再利用し、新しい job body も新しい汎用 driver も作らない。A-5 の投入器・契約テスト・登録簿 entry も
変更しない。

**理由:**
- 既存 A-5 投入器は同じ checkout から 2 job を出し、先に終わった job の終了処理が打つ
  global `git worktree prune --expire now` が、共有 submodule gitdir 上の他 job の worktree 登録を
  消す。後に終わる job が必ずこの経路で落ちる構造であり、実測でも 8 genome を計測した後に
  finalizer 前で落ちている (F251 の 2026-09-07 再発)。1 job だけを出す投入器なら
  同一 invocation 内にこの経路が成立しない。
- job body を変えると A-5 の受理集合が変わる。契約テストが 2 workload fan-out と global prune を
  正例として固定しており、そこを触るのは別の変更単位である。
- 投入器だけを足すのは、既存の測定経路を呼ぶ薄い層という要求の範囲に収まる。

**却下した選択肢:**
- 既存 A-5 経路をそのまま使う — 後続 job が prune で落ちる構造が残る。
- A-5 job body を balanced 専用へ直す — A-5 の受理集合を変える。
- A-5 投入器を checkout ごとに分ける — 同じ欠陥の恒久対応であり、既にユーザー裁定へ返っている。

**限界:** 別 invocation どうし、あるいは既存 A-5 job と同時に走る場合は、再利用している job body の
global prune 経路が残る。この投入器はその競合を解消しない。

## {{D:t1998-diagnostic-build-rejection-by-source-digest}}. 診断 build の排除は「明示値の不在」でなく事前登録の source digest 照合で行う

**決定:** 対照 consumer が診断 build 由来の値を拒否する根拠は、事前登録が arm ごとに持つ期待
`source_bytes_sha256` と記録済み値の一致とする。genome と configure command に診断 knob の
明示値が現れないことは補助的な検査に留め、単独の根拠にしない。configure argv は
`-DNAME[:TYPE]=VALUE` を正規化してから判定する。

**理由:**
- producer の genome はそもそも診断 knob を持たないので、「明示値 1 が無い」は候補集合に
  含意されて恒真になる。knob の既定値を 1 にした source から同じ genome で証拠を作れば素通りする。
- 型付きの `-DNAME:STRING=1` は literal token の完全一致検査を通り抜ける。正規化しないと
  同じ意味の入力が別の受理結果になる。
- 診断計器の実効値は単一 field として記録されていない。commit 束縛の source bytes から
  導出するしかない。

**却下した選択肢:**
- 明示値の不在だけを根拠にする — 恒真であり、診断 build を排除しない。
- producer の result schema へ実効値 field を足す — 現在の受理条件には不要で、
  既存 producer の出力 bytes を変える。

## {{D:t1998-shape-binding-over-content-reading}}. 固定 2 点だけ内容を読む契約の下でも、producer の形は全点で束縛する

**決定:** 事前登録で固定した 2 点だけを読む consumer でも、campaign 全体に対して次を要求する。
どの `build_start` の genome にも診断 knob の key が現れないこと、全 `verify_done` / `bench_done` が
既知の build attempt に属すること、anomaly を報告する record や非 serializable の verdict が
1 つも無いこと。対の外の点については throughput も median も順位も読まない。

**理由:**
- 束縛した job body は診断 knob 付き genome では結果を発行しない。そのような入力を受理すると
  「束縛済みの sanctioned producer の完全な出力である」という provenance 結論が偽になる。
- attempt に属さない verify record は上流の topology 検査も certified admission も見ない。
  anomaly が明記された variant を通す経路になり、正しさゲートの迂回になる。
- これらは値の内容を読む検査ではなく producer の形を束縛する検査なので、
  「固定 2 点だけ内容を読む」契約と両立する。

**却下した選択肢:**
- 対の 2 点だけを見る — 診断 knob 付きの根や anomaly record を通す。
- 対以外の throughput も読む — 事前登録で固定した 2 点だけを読むという契約を破る。
