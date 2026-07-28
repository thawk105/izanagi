静的検査のみ。pytest は実走していない。

1. [refuted-候補] 候補 A の exact 実装から、永久 deadlock は直ちには構成できない。manager mutex 内で行うのは待機を伴わない strong CAS 1 回だけで、失敗すれば mutex を解放して caller へ戻る設計だからである（[s2-plan.md:13](</home/SFC/tanab/.claude/jobs/496a8b50/tmp/dev-wave-t139/s2-plan.md:13>)、[atomic_wrapper.hh:67](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/include/atomic_wrapper.hh:67)）。D38 の `record_lock` は CAS 成功後、D41 の permutation 検査は lockWriteSet 前なので、exact hunk なら直接の相互侵食もない（[transaction.cc:174](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/cc/silo/transaction.cc:174)、[transaction.cc:390](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/cc/silo/transaction.cc:390)）。

   成果物影響（未対応時）: この deadlock 攻撃だけで A を除外すると rung 台帳の候補受理集合を不当に狭めるが、既存 certified 選択・レポート値は不変。

2. [must-fix] ただし「新しい lock-order cycle を作らない」の論拠は誤っている。2 個目以降の CAS では既取得の record lock を保持したまま manager mutex を待つため、実際には `record-prefix → manager` の hold-and-wait が生じる（[transaction.cc:155](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/cc/silo/transaction.cc:155)、[transaction.cc:181](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/cc/silo/transaction.cc:181)、[transaction.cc:650](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/cc/silo/transaction.cc:650)）。record 競合なら即 abort する `NO_WAIT_LOCKING_IN_VALIDATION` も、manager 待ちには効かない（[transaction.cc:160](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/cc/silo/transaction.cc:160)）。manager owner の deschedule、mutex の非公平性、unlocked-version CAS 失敗時の再獲得で、全体は進んでも一部 worker が飢餓する「実質 livelock」があり得る。aggregate `txns/writes` だけでなく、t4 各 worker の commit/update > 0、timeout、適用 workload/thread 数を liveness envelope として gate にすべきである。D41 も per-thread 偏りが未観測だと認めている（[decisions.md:1263](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/docs/decisions.md:1263)）。

   成果物影響（未対応時）: 一部 worker 飢餓でも characterization JSON が `all_pass=true` となり、台帳の `liveness/characterized` 受理集合と後続 RF 測定適格性が過大になる。

3. [must-fix] CAS 同値性の契約に「`expected` を参照で受け、failure 更新を caller に返す」が欠けている。stock helper は第2引数を `T&` とし、成功 `ACQ_REL`・失敗 `ACQUIRE` の strong CAS である（[atomic_wrapper.hh:67](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/include/atomic_wrapper.hh:67)、[atomic_wrapper.hh:69](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/include/atomic_wrapper.hh:69)）。wrapper が値渡しなら caller の `expected.lock` が更新されず、no-wait abort と retry の意味が変わる。`stock_cas_exact` は、参照型・CAS 1 回・同じ3引数・代替 store 無し・memory order 無変更まで固定すべきである。

   成果物影響（未対応時）: verifier が偶然緑のスケジュールでも serializable 不変の静的根拠が失われ、JSON の `verifier_certified` を rung 台帳の correctness proof 参照として受理できない。

4. [should] B/C/D は同じ gate で代替可能ではない。

   - B は全 record lock を保持したまま manager を待ち、mutex 内に TRACE I/O、WAL、data install、GC まで入る（[s2-plan.md:35](</home/SFC/tanab/.claude/jobs/496a8b50/tmp/dev-wave-t139/s2-plan.md:35>)、[transaction.cc:584](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/cc/silo/transaction.cc:584)、[transaction.cc:626](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/cc/silo/transaction.cc:626)）。永久 cycle は同様に成立しにくいが、convoy と TRACE 依存の critical-section 長が A よりはるかに強い。
   - C は同じ SWO comparator を使う限り correctness は最も素直だが、既に整列した小 write-set の8回 sort は gap が識別不能になりやすい（[silo_op_element.hh:67](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/cc/silo/include/silo_op_element.hh:67)）。D41 の permutation gate は残す必要がある。
   - D は CAS 自体を保存するが、pause 中に winner が変わり no-wait abort 分布を変える。固定遅延であり、per-worker progress と x86 toolchain の適用範囲を別途固定しない限り ability probe として弱い。

   成果物影響（未対応時）: fallback 候補を A と同じ受理集合へ入れると、trace 固有 convoy または実質 gap 0 の案まで台帳上の「rung」に昇格する。

5. [must-fix] `compile_commands.json` からの preprocess command 射影が未定義で、空 stdout 同士を一致扱いする経路がある。典型的 compile command の `-o <object>` を残したまま `-E -P` にすると出力はファイルへリダイレクトされ、stdout hash は stock/OFF とも空になり得る。`-c`、`-o`、dependency flags を除き、stdout 非空かつ `TxExecutor::lockWriteSet` 等の sentinel を含むことを必須にすべきである。また `transaction.cc` は workload ごとに複数 compile entry を持つので、`ycsb_silo.exe` の output へ一意に束縛する必要がある（[s2-plan.md:215](</home/SFC/tanab/.claude/jobs/496a8b50/tmp/dev-wave-t139/s2-plan.md:215>)、[ProtocolHelpers.cmake:32](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/cmake/ProtocolHelpers.cmake:32)）。既存 digest は stdin→stdout を明示している（[source_digest.py:237](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/campaign/source_digest.py:237)）。

   成果物影響（未対応時）: 空 hash の一致で `default_off_preprocess_matches_stock=true` が偽緑となり、JSON の inert witness と台帳の stock 同一性参照が無効になる。

6. [must-fix] この real-TU witness は D23 の `cpp -E -P byte-identical` と同一契約ではなく、特定 compiler・特定 compile argv に束縛された別 witness である。D23 は include 除去、実 TU マクロ供給集合、TU 注入文脈、未知条件マクロ、TRACE diff-of-diffs をまとめて扱う（[source_digest.py:221](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/campaign/source_digest.py:221)、[source_digest.py:388](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/campaign/source_digest.py:388)、[source_digest.py:600](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/campaign/source_digest.py:600)）。OFF 枝の stock CAS 逐語検索は補助に留め、pin から採った stock と同一 argv による TRACE=0/1 双方の出力比較を正本にすべきである。単なる substring は dead code 内に stock CAS を残しても通る。

   成果物影響（未対応時）: inert の受理範囲が実測 compiler 1 個へ暗黙に縮み、レポートが D23 相当保証を誤参照するか、patch 更新時に有効な変更を偽赤で拒否する。

7. [must-fix] 「裸マクロは pipeline から定義不能」は偽である。`Genome.cmake_defines()` が `CCBENCH_` しか生成しないことだけは正しい（[model.py:57](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/campaign/model.py:57)）。しかし buildcache の configure は `CMAKE_CXX_FLAGS` を固定せず、subprocess は環境を継承するため、`CXXFLAGS`、既存 CMake cache、toolchain/wrapper compiler から注入できる（[buildcache.py:585](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/campaign/buildcache.py:585)、[buildcache.py:739](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/campaign/buildcache.py:739)）。既存 s3 driver 自身も `CMAKE_CXX_FLAGS=-DIZANAGI_BREAK_*=1` を使っており、その経路の実在を示す（[s3_lock_coverage.py:129](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/campaign/s3_lock_coverage.py:129)）。専用 driver は環境を scrub し、実 compile argv に macro が OFF 時 absent、ON 時 exactly-one であることを検査すべきである。

   成果物影響（未対応時）: patch 適用中の将来 recovery/baseline build が意図せず ON となり、certified 選択が stock と誤同定され、レポートの source/compiler provenance と台帳 identity が食い違う。

8. [must-fix] 緑 fixture は「意味的空 patch」をまだ殺せない。`patchharness` が拒否するのは touch file 0 本だけである（[patchharness.py:155](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/campaign/patchharness.py:155)）。wrapper call を生かしたまま lock_guard を消す、`thread_local`/呼出ごとの local mutex にする、CAS の前後で無関係な mutex を取る、という変異は `manager_callsite_live` と certified 緑を通り得る。M2 は「直接 CAS に戻す」1形しか覆っていない（[s2-plan.md:236](</home/SFC/tanab/.claude/jobs/496a8b50/tmp/dev-wave-t139/s2-plan.md:236>)）。単一 namespace-scope・非 thread-local mutex、lock_guard lifetime が exact CAS を包含、bypass 無しを静的契約にし、実 trace も INSERT ではなく `U/D` が存在することを確認すべきである（INSERT は lockWriteSet を通らない: [transaction.cc:157](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/cc/silo/transaction.cc:157)）。

   成果物影響（未対応時）: 実質 no-op が `all_pass=true` で「rung」に昇格し、台帳の slowdown mechanism が虚偽、将来 RF の分母は 0/識別不能になる。

9. [must-fix] 実証 JSON と現 patch の継続 binding がテスト計画にない。JSON へ patch SHA を入れる予定はあるが（[s2-plan.md:134](</home/SFC/tanab/.claude/jobs/496a8b50/tmp/dev-wave-t139/s2-plan.md:134>)）、committed JSON テストは schema・check-key・`all_pass=true` しか要求していない（[s2-plan.md:219](</home/SFC/tanab/.claude/jobs/496a8b50/tmp/dev-wave-t139/s2-plan.md:219>)）。patch 更新後に driver が失敗しても旧 JSON が残り、静的全走は緑になり得る。テストで current patch SHA256、full PIN、macro、compiler realpath/version、workload と JSON を再照合すべきである。

   成果物影響（未対応時）: レポートと台帳が旧 patch の certified JSON を新 patch の証拠として参照し、characterized rung の受理集合が stale evidence まで広がる。

10. [should] 候補 A の correctness は静的同値性から主張できるが、trace build の liveness 結論は trace-disabled build へ自動転移しない。TRACE は CAS 成功直後の shadow set 更新、sort 前後の multiset、writePhase の I/Oを追加し、record lock 保持時間と競合 schedule を変える（[transaction.cc:174](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/cc/silo/transaction.cc:174)、[transaction.cc:403](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/cc/silo/transaction.cc:403)、[transaction.cc:584](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/cc/silo/transaction.cc:584)）。規律1は別 build/run を要求する（[CLAUDE.md:56](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/CLAUDE.md:56)）。throughput を保存せず、ON の TRACE=0 build/run liveness smoke と trace-diff witness を追加し、`trace_certified` と `perf_liveness` を別 check にすべきである。B は mutex が TRACE I/O 全体を包むため、この問題が特に強い。

   成果物影響（未対応時）: 台帳が trace-enabled での生存を trace-disabled recovery 測定適格性へ誤転記し、レポートの characterization 適用範囲が過大になる。

11. [must-fix] 親の login-node 実測は stock 環境 canary であり、rung の DW-G01 ではない。実測は system g++ 11.4 の pinned stock trace build/run/verifier である（[handoff:63](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/docs/handoff/2026-07-28-dev-wave-t139-ladder.md:63)、[handoff:68](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/docs/handoff/2026-07-28-dev-wave-t139-ladder.md:68)）一方、DW-G01 は rung apply/build/run/certified を要求する（[parent-brief.md:19](</home/SFC/tanab/.claude/jobs/496a8b50/tmp/dev-wave-t139/parent-brief.md:19>)）。production 既定は g++-13（[buildcache.py:118](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/campaign/buildcache.py:118)）で、login node 全走はその preprocess/diff-of-diffs 群を skip する（[tests/README.md:134](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/tests/README.md:134)）。「この1秒 canary に qlogin 不要」は実測・runbook上妥当だが、「rung も g++-13 受入も成立」へは一般化できない。

   成果物影響（未対応時）: stock/g++11 canary が rung/g++13 の証拠として誤参照され、characterization JSON の compiler binding と台帳の DW-G01 完了値が虚偽になる。

12. [must-fix] M1〜M5 は現状「単一理由 kill」の事前登録になっていない。

   | 変異 | 静的帰属 |
   |---|---|
   | M1 | guard を全置換するなら OFF≠stock に加えて ON==OFF も赤。どの guard 1箇所を変えるか未確定で、単一理由でない。 |
   | M2 | `manager_callsite_live` 単独 kill は名目上成立するが、lock_guard 消去・local/thread-local mutex という本命 no-op 変異を覆わない。 |
   | M3 | `stock_cas_exact` に加え、D38 の X 行で strict CLI は rc=3・indeterminate・certified=false となり複数 check が同時に赤（[transaction.cc:617](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/cc/silo/transaction.cc:617)）。 |
   | M4 | strict 単一-run CLI では exit 0 iff certified。したがって `exit==0 OR certified` と AND は実入力上同値で、`exit=0/certified=false` fixture は到達不能（[verifier/cli.py:81](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/verifier/cli.py:81)）。`serializable` 単独受理や rc=3 受理への変異に替えるべき。 |
   | M5 | tracked revert 漏れは `applied()` 自身が既に殺す（[patchharness.py:238](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/campaign/patchharness.py:238)）。post `assert_pinned_clean` の固有価値は revert ではなく body 内 HEAD 移動の検出なので、理由が誤帰属。 |

   成果物影響（未対応時）: mutation 台帳が SURVIVED/重複 kill/到達不能 mutant を「5/5 killed」と誤記録し、レポートの検出力主張と fixture 受理根拠が過大になる。

13. [should] normal recovery pipeline への将来接続には、計画記載の「未知裸マクロ」以外に `<mutex>` include 差分という第2の fails-closed blocker がある。`source_digest.resolve()` は HEAD と include 行が1行でも違えば停止する（[source_digest.py:555](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/campaign/source_digest.py:555)）一方、A は ON 枝用 include 追加を予定する（[s2-plan.md:8](</home/SFC/tanab/.claude/jobs/496a8b50/tmp/dev-wave-t139/s2-plan.md:8>)）。本 wave の台帳では `recovery_measurement_eligibility=false`、`composition=dedicated-driver-only` と明記し、通常 loop 接続済みに見せてはいけない。

   成果物影響（未対応時）: 既存 certified 選択値は不変だが、台帳が未接続 rung を recovery-ready と誤表示し、後続レポートの driver/source identity 参照が実行時に fails-closed で切れる。

プラン推奨（候補 A）を維持してよいか: 候補 A 自体は条件付きで維持してよいが、現プランのままの推奨確定は不可—CAS参照同値性、manager の実効性、per-worker liveness、inert/compiler/JSON binding、変異 M1〜M5 の再登録を must-fix とする。