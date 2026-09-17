単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/parent-brief.md — 親 brief (研究前進・scope・確定済み裁定・不変条件・段 1 実測・provisional 裁定 P1〜P5)。**親 brief 自身も検査対象**。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/s2-plan.md — 段 2 plan (codex 起草)。守るのではなく検査する対象。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/checker-run-facts.md — 親が login node で実走した checker 3 本 (g++ 11.4 pass / g++-12 pass / clang++ 14 fail-closed) の事実と clang 拒否の原因 probe。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/checker-summary-gcc.txt — GCC 2 本の report 要点 (digest・define map・活性・policy) の逐語。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/D1603.md — pin 前進は材料 3 点を揃えてから裁定。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/D297.md — 検査の保証名と設計理由 (翻訳単位の同一性を名乗らない、header 差分は保証外、複数 compiler、admission toolchain と同一とは主張しない)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/D986.md — checker の 3 穴は塞ぐ (ユーザー裁定)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/D722-D723.md — mocc 実供給 define・commit tree 走査・submodule の限界。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/D2114.md — 本 wave の起点裁定 (pin 前進は未承認、材料が揃ったら別途提示、初回候補は mocc 単独)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/archive-872-t1506.md — T-1506 の記録 (16 context・define map 4 種・digest 2 種、既存の穴 3 件)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/archive-1079-t1943.md — T-1943 の記録 (058d0c4e→e9e477ca の checker 通過、CCBench local branch 2 commit)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/tools/check_trace0_preprocess_identity.py — checker 本体 (docstring の限界文、祖先性 gate、mocc 特例、report schema)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/orchestrator/campaign/source_digest.py — `_cpp_normalize` (環境 prefix 剥がしの GCC 前提、-dD、限界文)、`_context_overlays`、`_head_defines`、`_assert_proven_repo_absent_macros`。読めなければ即停止。

## 依頼 (レンズ A: 正しさ境界 — 材料 (1)(2) の「言えること・言えないこと」)

あなたは read-only の敵対検証子である。plan と親 brief を守らず、**正しさ境界 (規律 1 の検査としての意味、規律 2) と整合・実効性を分けて**攻撃せよ。pytest・checker の実走は不要 (親が実走済み、結果は上の射影)。

攻撃対象:
1. **材料 (2) の合格の言い方。** 親は「g++ 11.4 と g++-12 で rc=0、16 context 全一致、clang++ 14 は checker が判定不能 (候補の拒否ではない)」と書く予定である。(a) clang の fail-closed を「候補の拒否ではない」と分類するのは正当か — `source_digest._cpp_normalize` の環境 prefix 設計と親の probe (空入力の末尾空行) を現物で検証し、別の原因 (clang が old/new を実際に区別している可能性) を排除できているか。(b) D297 の「複数の compiler で走らせ」を GCC 2 版で満たしたと言えるか、「admission toolchain と同一であるとは主張しない」をどう書くべきか (計測 job の実 compiler は何か、`tools/pegasus/mocc_trace_v1_policy.json` の `expected_compiler_version_body_sha256` と login node の g++ の関係を確認せよ)。(c) 「16 context 一致」の読み方: 実効 define map 4 種・正規化 digest 2 種 (BACK_OFF でだけ分かれる) を材料に書くとき、言い過ぎ (「mocc の macro 空間を検証した」) と言い足りなさ (SILO_SPACE の genome 軸 NO_WAIT_LOCKING_IN_VALIDATION / NO_WAIT_OF_TICTOC / WAL が mocc TU に無関係である事実の扱い、mocc 固有の `#if` 分岐が context 列挙に無い可能性) を specific に指摘せよ。cc/mocc/transaction.cc の new 側 (e9e477ca) にある条件付き指令 (`#if` / `#ifdef`) を列挙し、16 context がそのどれを両枝で評価しているか / していないかを表にせよ (`git -C <worktree>/external/ccbench show e9e477ca1b55348ab4530de0b1cf663ce4555290:cc/mocc/transaction.cc` で読める)。
2. **保証範囲の逐語 (親 brief P3)。** checker docstring・D297・D986・D722/D723・source_digest の限界文 (`#pragma push_macro`、include 相対位置、-dD の skipped 枝、submodule 不在証明の限界) のうち P3 に無いものを列挙し、訂正版の逐語 (箇条書き 8 行以内) を書け。逆に P3 が checker の保証より強く読める句があれば指摘せよ。
3. **材料 (1) 候補の確定 (P1)。** e9e477ca の 4 commit の commit 本文・author・trailer (`git -C <worktree>/external/ccbench log --format=fuller 511c9538e4e8efa54b45cda62e72389ed3b706ec..e9e477ca1b55348ab4530de0b1cf663ce4555290`) を読み、(a) D16/D18/D20 (CCBench 改変の手続き) と AI provenance の観点で候補として提示するのに欠けている記載があるか、(b) 候補の先端 = local branch の先端であり remote (GitHub) には push されていない事実を材料にどう書くか、(c) 「mocc 単独」の判定: 4 commit に mocc 以外の path 変更が無いことは親が diff-tree で確認済み — それ以外に「単独」を崩す要素 (例: include/trace.hh 自体の版、mocc 以外の TU が trace.hh を include するか) を現物で確かめよ。
4. **規律 2 / 規律 3 の観点。** 材料の提示が「合格したから前進可能」と読まれる書き方になっていないか。本 wave が判定しないことの明記位置と文面を提案せよ。checker が拒否した場合の記載形 (今回は非該当だが plan が用意しているか)。
5. **親の実測値の一般化。** 親 brief・checker-run-facts の実測値 (wall 秒、bytes、digest) のうち、insight に書くと誤解を生むもの・不要なもの・書くべきなのに欠けているもの (例: 実走した checker 自身の blob sha、source_digest の blob sha、worktree HEAD) を挙げよ。

各所見は「所見 / 根拠 (file:line または射影名) / 正しさ境界 or 整合・実効性 / must-fix or nit / 推奨是正」の形で書け。予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式

Markdown。先頭に `## 総括` (10 行以内: must-fix 件数、nit 件数、親 brief P1〜P5 のうち異議あり、clang 分類への賛否、保証範囲の訂正点数)。続けて上の 1〜5 を見出しにして書き、最後に `## 訂正版の保証範囲 (逐語案)` を置く。
