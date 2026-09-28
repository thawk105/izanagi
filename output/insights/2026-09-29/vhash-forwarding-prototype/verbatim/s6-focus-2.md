## 対応表

| fix | 判定 | 静的検査の根拠 |
|---|---|---|
| fix3：counter 型・集計の必要セル | **partial** | `long` は bool、他の値は非負整数として検査し、各入力 run job の計画セルと空 records も検査する。[driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/vhash-fwd-integ2/orchestrator/campaign/vhash_forwarding_prototype.py:250)・[集計](/work/1/SFC/tanab/izanagi/.claude/worktrees/vhash-fwd-integ2/orchestrator/campaign/vhash_forwarding_prototype.py:411)。ただし **3 workload 全体の充足は未検査**。 |
| fix4：4 target から compile entry を選択 | **closed** | ycsb target の目印で絞り、0 件・複数件を拒否する。[driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/vhash-fwd-integ2/orchestrator/campaign/vhash_forwarding_prototype.py:123) |
| fix5：空 job のエラー順 | **closed** | 空 records を必要セル検査より先に拒否する。[driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/vhash-fwd-integ2/orchestrator/campaign/vhash_forwarding_prototype.py:422) |
| fix6：生成済み依存物で inert 比較 | **closed** | stock build の entry を使い、3 macro の `-D` 引数を除去した**同じ argv**で pin と patch を前処理する。行 marker と空白行を除く。[driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/vhash-fwd-integ2/orchestrator/campaign/vhash_forwarding_prototype.py:141)・[比較](/work/1/SFC/tanab/izanagi/.claude/worktrees/vhash-fwd-integ2/orchestrator/campaign/vhash_forwarding_prototype.py:180) |
| fix7：gate への重複 define | **closed** | gate には CXX_FLAGS を足す前の引数を渡し、通過後の configure に供給 macro を足す。[driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/vhash-fwd-integ2/orchestrator/campaign/vhash_forwarding_prototype.py:99) |
| fix8：config.h の事前生成 | **closed** | macro なしの dependency build を先に完了し、失敗時は後続へ進まない。その後 stock・fwd・count を build する。[driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/vhash-fwd-integ2/orchestrator/campaign/vhash_forwarding_prototype.py:520) |
| fix9：元ソースの行番号 | **closed** | `#line` は次の pin 行を指す。transaction.cc は 9、29、35、103、178、301、349、420、460、746、896、ycsb_cicada.cc は 21、23、26、40、41 と照合した。[patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/vhash-fwd-integ2/patches/cicada-forwarding-variant.patch:9)・[pin transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/vhash-fwd-integ2/external/ccbench/cc/cicada/transaction.cc:9)・[pin ycsb_cicada.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/vhash-fwd-integ2/external/ccbench/cc/cicada/ycsb_cicada.cc:21) |

## 新しい所見

**must-fix — 全 workload の欠落を集計が受理する。** `aggregate_jobs` は渡された各 job 内のセルだけを検査するため、例えば `wait_after_reads` の job 自体が無くても集計できる。[driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/vhash-fwd-integ2/orchestrator/campaign/vhash_forwarding_prototype.py:415)。作図側も欠けたセルを空値として扱う。[make_figures.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/vhash-fwd-integ2/output/insights/2026-09-29/vhash-forwarding-prototype/make_figures.py:88)。**放置時の成果物：workload が欠けた主図と provenance を正常な成果物として発行できる。**

## 総括

HEAD `c0d860936` では、build sink は `_build_variant` の 1 箇所で、供給 macro ごとの supply・meaning の 2 腕、起動箇所 `checked`・`_run_binary` 各 1 箇所を維持している。[driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/vhash-fwd-integ2/orchestrator/campaign/vhash_forwarding_prototype.py:73)・[build](/work/1/SFC/tanab/izanagi/.claude/worktrees/vhash-fwd-integ2/orchestrator/campaign/vhash_forwarding_prototype.py:99)・[binary](/work/1/SFC/tanab/izanagi/.claude/worktrees/vhash-fwd-integ2/orchestrator/campaign/vhash_forwarding_prototype.py:295)。`#if` は ENABLE 11／COUNT 4／LONGTX 4、既存テストの期待値は差分上変更されていない。`#line` は元の行の `__LINE__` を pin に戻す一方、追加コードの診断行番号には重複が生じ得る。追加コードに明示的な `__LINE__` 利用は見当たらず、挙動を変える経路は確認できなかった。親提示の smoke `all_pass` と登録関連 401 passed は実測結果として受け取り、本レビューでは再実行していない。