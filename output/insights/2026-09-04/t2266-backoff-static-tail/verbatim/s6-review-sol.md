## 観点 1 — 8 点を本当に測るか

- **must-fix** — trace-disabled binary の hash 比較は固定 6 点だけです。`none` と `adaptive` は `_static_backoff_amount()` が `None` を返すため検査対象から外れ、8 binary の distinct 性を保証できません。[orchestrator/campaign/backoff_extended_sweep.py:187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:187) [orchestrator/campaign/backoff_extended_sweep.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:194)  
  放置時: `none` または `adaptive` が別点と同じ perf binary でも受理され、基準線比較の TPS と abort 率が別 genome の値として記録されます。

格子自体は exact 8 点で、固定 0 はなく、999 は `BACKOFF_FIXED=999` の genome として build に直接渡ります。[orchestrator/campaign/backoff_extended_sweep.py:345](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:345) T-2266 も既存 `run_campaign` 経路へ入り、trace-enabled bench への新しい迂回はありません。[orchestrator/campaign/backoff_extended_sweep.py:803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:803)

## 観点 2 — rep 単位の保存

- **must-fix** — abort 率は rep identity を持たない global parser の呼出順として蓄積され、throughput の添字へ位置だけで結合されています。parser 呼出数が 5 を超えても先頭 5 件へ切り詰められ、exact cardinality や対応順を検査しません。[orchestrator/campaign/backoff_extended_sweep.py:487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:487) [orchestrator/campaign/backoff_extended_sweep.py:501](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:501)  
  放置時: 5 TPS に対して abort parser が代表値を先に含む 6 回、例えば `[0.9, 0.1, 0.2, 0.3, 0.4, 0.5]` と呼ばれると、先頭 5 件が rep 0〜4 として受理され、実際の rep 4 の `0.5` が失われます。

- **nit** — 採用 round の WAL TPS 照合とされた後段条件は恒真です。`reps_for()` が同じ `run_cmd` かつ `throughput_tps == bench["tps"]` の capture だけを返した後、その同じ配列を再比較しています。不一致入力は line 530 で先に拒否されるため、line 613 の例外を発火させる入力はありません。[orchestrator/campaign/backoff_extended_sweep.py:523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:523) [orchestrator/campaign/backoff_extended_sweep.py:611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:611)

throughput は中央値の複製ではなく `point.throughputs` の生配列から取得されています。[orchestrator/campaign/backoff_extended_sweep.py:504](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:504)

- **backlog** — capture は当該 process のメモリだけに存在する一方、report loader は WAL の全 committed point を読みます。部分 campaign を別 process で再開すると、既存 commit の capture がなく report 化できません。[orchestrator/campaign/backoff_extended_sweep.py:477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:477) [orchestrator/campaign/backoff_extended_sweep.py:576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:576)

## 観点 3 — 新 gate の恒真性

追加の must-fix はありません。

7 commit は exact-set/件数検査で拒否され、8 commit 中に未知 genome があっても拒否されます。[orchestrator/campaign/backoff_extended_sweep.py:582](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:582) [orchestrator/campaign/backoff_extended_sweep.py:639](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:639) report は全 8 commit 後だけ生成され、CLI completion は両成果物の欠落を拒否します。[orchestrator/campaign/backoff_extended_sweep.py:841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:841) [orchestrator/campaign/backoff_extended_sweep.py:884](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:884)

create-only は事前存在確認に加え、両 writer が `O_EXCL` を使用するため、既存 file を実際に拒否します。[orchestrator/campaign/backoff_extended_sweep.py:269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:269) [orchestrator/campaign/backoff_extended_sweep.py:686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:686)

## 観点 4 — 規律 2

- **must-fix** — trace-disabled の数値行へ `"certified": True` を付けています。裁定は全測定値を非認証と明記しており、ここでは correctness verify の通過と性能値の認証を分離する必要があります。[orchestrator/campaign/backoff_extended_sweep.py:617](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:617) [orchestrator/campaign/backoff_extended_sweep.py:630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:630) [s4-adjudication.md:122](/work/1/SFC/tanab/dev-wave-artifacts/t2266-backoff-static-tail/s4-adjudication.md:122)  
  放置時: trace-disabled TPS と abort 率が certified point として出力され、variant 採用など認証値だけを許す参照先へ流用され得ます。

- **must-fix** — 全 rep テストは synthetic `points` を作って serializer だけを呼び、実測 producer の `_T2266RepCapture` と WAL consumer の `_load_t2266_report_points` を両方迂回しています。事前登録された「代表 1 rep だけ残す」変異でもこのテストは緑のままです。[orchestrator/tests/test_backoff_extended_sweep.py:236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/tests/test_backoff_extended_sweep.py:236) [orchestrator/campaign/backoff_extended_sweep.py:477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:477)  
  放置時: abort 率を代表値 5 個へ複製する実装も受入テストを通過し、歩行 model に偽の rep 分布を渡す成果物が受理されます。

`_require_backoff_condition_gate` は選択後の T-2266 genome に対して発火し、既存 `run_campaign` の correctness 経路も維持されています。[orchestrator/campaign/backoff_extended_sweep.py:797](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:797) 既存テストの変更、反転、skip、削除は統合差分にありません。

## 観点 5 — 申告と実物の照合

- **must-fix、観点 2 と同一所見** — `s5-author.md` の「各 rep から abort 率を採取」は、実物では parser 呼出順を rep 番号と仮定しているだけで、rep との実体的な束縛がありません。[s5-author.md:12](/work/1/SFC/tanab/dev-wave-artifacts/t2266-backoff-static-tail/s5-author.md:12) [orchestrator/campaign/backoff_extended_sweep.py:501](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:501)

- **nit** — 同じ行の「採用 round の WAL TPS と照合」は、照合自体は `reps_for()` の選択条件で行われますが、後段に独立照合があるように読める申告です。後段の比較は恒真です。[s5-author.md:12](/work/1/SFC/tanab/dev-wave-artifacts/t2266-backoff-static-tail/s5-author.md:12) [orchestrator/campaign/backoff_extended_sweep.py:528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:528)

- **must-fix、観点 4 と同一所見** — 「合否、閾値、shape 分類は追加していない」と報告していますが、数値を含む各 point に無限定の `certified: true` を新設しています。[s5-author.md:32](/work/1/SFC/tanab/dev-wave-artifacts/t2266-backoff-static-tail/s5-author.md:32) [orchestrator/campaign/backoff_extended_sweep.py:630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:630)

受理集合、既存 31 点 identity、変更 4 ファイル、run kind receipt、report の create-only に関する残りの申告は統合差分と一致します。

## 総括

must-fix は重複を除いて 4 件です。  
1 件目は `none` と `adaptive` を含む 8 binary 全体の distinct hash gate がないことです。  
2 件目は abort 率を rep identity なしの parser 呼出順で throughput に結合していることです。  
3 件目は非認証である trace-disabled 測定値を `certified: true` と出力することです。  
4 件目は rep 保存テストが producer と WAL consumer を迂回し、登録済み変異を検出できないことです。  
exact 8 genome、999 の build flags、固定 0 の排除、全点 commit、report 存在、create-only は静的に成立しています。  
correctness gate と既存 pipeline の呼出しも維持されています。  
このレビューでは検査を実走しておらず、親が報告した結果以外を緑とは判定していません。