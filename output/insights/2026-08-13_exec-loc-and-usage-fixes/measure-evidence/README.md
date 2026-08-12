# §7.0 実行場所分類の実測 (rulings 第 7 束のユーザー委任、2026-08-13)

worklog fragment (branch worktree-rulings8-20260813、commit 8dbdadb7) の一次資料。
測定 job は gen_S へ qsub した 3 本。

| run dir | job | node | 対象 | 結果 |
|---|---|---|---|---|
| `run-0:908392.nqsv` | 908392 | bnode013 | ledger ×3, usage ×3 | ledger 有効 (delta +19.7/+11.6/+11.9 MiB, rc=2)。usage は --project 欠落で本体未走行 |
| `run2-0_908396.nqsv` | 908396 | bnode094 | 同上 | ledger 有効 (delta +18.1/負/+11.5 MiB)。usage は slug 先頭 - で SystemExit(2) |
| `run3-0_908401.nqsv` | 908401 | bnode094 | usage ×3 | 等号形でも内側 parser で同じ欠陥。実 slug では実行不能と確定 |

## 判定

- **claude_session_ledger.py (既定 argv `--json`) = local-ok 相当。**
  有効 5 走の charged delta 最大 20.6 MiB、margin 128 MiB 込み約 149 MiB < 規範値 512 MiB。
  入力 1.40 GB / 1,045 jsonl (既定は新しい 25 file)。
- **collect_wave_usage.py = 分類不能 (unknown 据置)。** tool 欠陥 (slug 先頭 `-` を内側
  parser へ渡せない + 失敗時 rc=0) の修正後に再測定。
- **mutation_worktree.py = 未測定 (意図的)。** 軽い複製への変更の実装後に測る。

## 方法論の注記

- login node では hooks/guard_bash.py が registry unknown の実行体を拒否する (正しい挙動、
  迂回していない)。計算ノードには per-job cgroup も cgroup delegation も無く
  (`/proc/self/cgroup` は `0::/system.slice/nqs-jsv.service` の 1 行のみ、2 ノードで確認)、
  runbook §7.0 の専有 scope 手順は非 root では実行できない。
- 採った方式は共有 service cgroup (`nqs-jsv.service`) の `memory.current` を busy sampling
  する delta 方式。同居 job の充当変動が混入する (実際に 1 走で delta が負になり無効化した)。
  registry へ反映する際は evidence にこの方法論の差を明記すること。

## erratum (2026-08-13 02:4x JST、反映 wave `dev-wave-exec-loc-and-usage-fixes` が追記)

**本 README の原文は上に保存してあるが、次の 3 点が誤りである。** 反映先の registry と runbook は
訂正後の値を使っている。原文を書き換えず、ここで訂正する。

1. **見出しの「§7.0 実測」は誤り。** 採られた方式は共有 service cgroup の delta sampling であり、
   §7.0 が定める専有 scope 手順ではない。正しくは**非 canonical な補助観測**である。
2. **「判定」節の `local-ok 相当` と数値は誤り。**
   - 最大 delta は `842317824 − 821682176 = 20,635,648 bytes`。これは **19.7 MiB** であって
     20.6 MiB ではない (20.6 は MB 値)。
   - margin 込みは **147.7 MiB** であって約 149 MiB ではない。
   - 結論は `local-ok 相当` ではなく **`unknown` 据置**である。§7.0 の canonical 手順を満たさず、
     本番 helper が渡す `--max-files=1000` の cap 境界も測っていない。
3. **「有効 5 走」の意味。** ledger は 6 走すべてが command `rc=2` (当時の
   `message_id_collision` 誤判定) で終了している。5 は「成功した走」ではなく
   **「正の delta を得たメモリ sample の数」**である。走査自体は完走しているので
   メモリ観測としては有効だが、「5 valid runs」と読んではならない。

補足: 測定 commit は `04d85f93`。report は既定 cap により **1,045 file 中 25 file・4,728,545 bytes**
だけを読み、`limit_reached=true` だった。母集団の総量は約 1.40 GB。

## 消してよいか

registry 反映 wave が evidence として参照し終えるまで残す。raw の peak/base/rc/stdout が
全走分ある。
