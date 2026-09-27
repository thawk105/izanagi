### 所見 1 — 変異 M5 の検出理由が二つ混ざっている

**主張:** plan の M5 は「tally を任意位置・任意 bytes として許す」を一つの変異にしている。余分な行を tally 近傍へ足す負例だけでは、位置の制約が効いたのか、bytes の制約が効いたのかを帰属できない。  
**根拠:** [s2-plan.md:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/out/s2-plan.md:47)、[s2-plan.md:49](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/out/s2-plan.md:49)。正規 tally の挿入位置は [tally patch:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/patches/instr-silo-backoff-trigger-gating-tally.patch:8) に固定されている。  
**影響:** mutation ledger が、検証していない位置制約にも単独の検出力を帰属しうる。  
**推奨:** **should。** 任意 bytes と位置移動を別変異・別入力にする。直接 admission node と contract-loader drift node の分離方針は維持する。

### 所見 2 — 「凍結」は `abort()` 内の提示形に限られる

**主張:** 案 B は提示された R4 の型差し替え・reason reset、R5 の `return;`、R7 の `FLAGS_clocks_per_us`／`Backoff` shadowing を、元の位置でも prologue 直前への移設でも拒否する。同じ固定領域内での `using`、typedef、ラムダ、別綴りの局所宣言も bytes 不一致になる。一方、関数宣言より前の file scope 定義、header 側の名前解決変更、前処理器による置換は受理境界の外に残る。  
**根拠:** 照合は BEGIN 行頭より前の凍結 suffix に対する `endswith` である（[s2-plan.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/out/s2-plan.md:16)、[s2-plan.md:33](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/out/s2-plan.md:33)）。実際の固定対象は `abort()` 宣言から prologue まで続く（[骨格適用後 source:61](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/evidence/transaction.cc.skeleton-applied:61)）。plan 自身も外側の限界を記す（[s2-plan.md:55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/out/s2-plan.md:55)）。  
**影響:** 「R4/R5/R7 を無条件に閉鎖」と成果物に書けば、受理集合の保証を過大に示す。  
**推奨:** **should。** plan の限定した docstring 表現を、insight と完了報告にもそのまま適用する。前処理器・他 file・file scope は別経路として明記する。

### 所見 3 — 原文との独立照合には初期化状態による空白がある

**主張:** 骨格・tally の定数を patch と照合する案は、定数と生成入力が同時に動く T-1048 MUT-3 型を防ぐ。一方、CCBench 原文との照合は submodule 未初期化時に skip するため、その環境で HEAD 定数の正本性は確認できない。  
**根拠:** 三つの出所と原文テストの skip 条件は [s2-plan.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/out/s2-plan.md:24)〜[29](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/out/s2-plan.md:29)。既存テストの skip 判定も `.git` の有無である（[test_campaign.py:11322](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_campaign.py:11322)）。定数由来のテスト入力だけでは独立照合にならないことは [t1048-README.md:137](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/verbatim/t1048-README.md:137) に実測されている。  
**影響:** 未初期化環境の緑だけでは、CCBench 原文部分の定数 drift を否定できない。  
**推奨:** **should。** 受入結果では原文照合 node が実行されたことを個別に示す。この worktree では `.git` と pin object を確認できたが、テスト実走はしていない。

### 所見 4 — 発火層と既知の非発火層を成果物で分ける必要がある

**主張:** 新条件を予定位置へ入れれば、derive、require、pipeline、buildcache、S8a characterization の fresh build では発火する。ENOENT は早期受理し、S8b resume と非 admissible materializer には同じ保証が伝わらない。  
**根拠:** 共通検査への入口は [build_admission.py:668](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/build_admission.py:668)、[同:805](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/build_admission.py:805)。pipeline と buildcache はそれぞれ require を呼ぶ（[pipeline.py:1937](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/pipeline.py:1937)、[buildcache.py:2492](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/buildcache.py:2492)）。S8a も derive と require を呼ぶ（[s8a_trigger_coverage.py:243](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/s8a_trigger_coverage.py:243)）。ENOENT 受理は [build_admission.py:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/build_admission.py:189)。非発火層は [consult-a2.md:33](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/verbatim/consult-a2.md:33) に整理されている。  
**影響:** fresh admitted build の検査結果を resume や非認証 build の保証へ広げると、参照する成果物の意味が変わる。  
**推奨:** **scope 外。** 実装を広げず、完了報告の適用範囲を fresh admitted build に限定する。

## 総括

案 B の bytes 境界は、提示された R4 二例・R5・R7 と同じ固定領域内への移設を拒否できる。  
tally 形は patch の行を宣言直後にだけ許す設計で、新たな任意行の受理口は見つからなかった。  
BEGIN 行頭直前までの `\n` と空行を比較するため、その領域の CRLF 化も拒否する。複数 marker は既存の件数検査で拒否される。  
brief の原文 20 行・tally の挿入位置・C2′ の `writePhase()` 限定差分・変更前 SHA は、指定 source と照合できた。  
最も明確な修正点は M5 の変異帰属を分けること。  
独立原文テストの実行確認と、fresh build に限る保証表現が受入時に必要である。