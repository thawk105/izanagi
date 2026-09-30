### A1: B2 の判定に旧予測が残っている

**重大度: must-fix。** 根拠: [driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/campaign/vhash_cicada_hot_block.py:820)。裁定 §3.2 は post-B2 の到達を見込み、検出の有無を予測しない。一方、`broken_verdict` は T1 の `reached == 0`、T2 の `reached == changed`、`committed == 0` を成功条件にしている。例えば T1 で `reached=1, changed=1, committed=0, cycles=0` なら `prediction-failed` になる。**成果物:** 事前登録に沿った到達を予測失敗と記録する。**修正:** B2 と B2-probe の旧予測分岐を外し、到達・変更・commit・検出を観測値として分類する。

### A2: B2 probe と壊し event の結合が一対一ではない

**重大度: must-fix。** 根拠: [driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/campaign/vhash_cicada_hot_block.py:723)、[probe patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/patches/broken-cicada-vhash-skip-pending-probe.patch:77)。driver は各 probe に同じ `(tx_wts, key, older_wts)` の `changed` が *一つでも* あれば受理する。同一 tx が同じ key を複数回読む、または event 行が欠ける入力では、一つの event が複数 probe を満たし、逆に probe のない `changed` も残せる。**成果物:** R/A/G/M/V/U の件数と committed・witness 件数の対応が崩れても集計が通り、機序の一次資料を誤らせる。**修正:** thread 内 ID を event にも出して一対一に結合し、`changed` と probe の件数・commit outcome を照合する。

### A3: stale-gap の `changed` は同時点の stock 第1段との差を確定しない

**重大度: must-fix。** 根拠: [stale-gap patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/patches/broken-cicada-vhash-post-stale-gap.patch:53)。隣接失敗後に `latest_` から別途たどり、pointer だけを比較している。例えば `latest=A → X` を読んだ直後、writer が新しい適格版 B を先頭へ CAS すると、stock 側が古い A 起点で X を返し、現在の第1段は B でも `changed=0` になる。**成果物:** 誤読 commit を過少計数し、未到達・未検出の判断を誤る。**修正:** 比較対象の列を同一の同期点で固定するか、比較中の列変更を検出して再試行し、確定できない事象を別計数にする。

### A4: post-B1 の「一つ古い版」は疎な hot block で保証されない

**重大度: should-fix。** 根拠: [B1 patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/patches/broken-cicada-vhash-post-stale-hot.patch:47)、[post patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/patches/cicada-vhash-hot-block-post.patch:94)。post は CAS と hot 挿入の間に隙間を許す。列が `A→B→C`、hot が `[A,C]` の間に B1 が A を選ぶと、`ptr[i+1]` は直後の B でなく C になる。**成果物:** 検出結果を「一つ古い確定版」の検出力と記述すると、実際より強い主張になる。**修正:** B1 は `ver->next_` で直後版を選び、確定状態を確認する。hot の次要素を使うなら「次の hot 要素」と記述する。

### A5: pointer 再利用の反例不成立

**重大度: nit（論証の範囲を明記）。** 根拠: [親メモ](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-hot-block-v2/s5-parent-notes.md)、[post patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/patches/cicada-vhash-hot-block-post.patch:178)、[variant patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/patches/cicada-vhash-hot-block-variant.patch:373)、[pin の再利用処理](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/include/transaction.hh:173)。**反例不成立:** X とその前の要素を GC 後に同じ address へ再利用する順序を試した。切離し anchor D が読者の rts 以下なら、D は読者の copy 前に publish 済みで、D の trim または満杯による消去は X も hot から除く。`inline_ver_` も同じ切離し処理を通る。ただし親メモが留保した MinWts／MinRts の公開順と単調性は、この静的検査では独立に証明していない。**成果物:** 無条件の ABA 不在と書くと証明範囲を超える。**修正:** 一次資料では stock と共通の寿命前提に依存する条件付き結論とする。

## 総括

**NO-GO。** 計測前に A1〜A3 を直す必要がある。post の guard は CAS 成功後に取り、再試行・失敗経路で保持しない構造で、COUNT と POST の計器は perf build の指定から外れている。GC の lock 順と親メモの pointer 再利用論証には、上記の範囲で反例を作れなかった。build・テスト・計測は実行していない。