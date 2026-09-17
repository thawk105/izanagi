単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/parent-brief.md — 親 brief (研究前進・scope・確定済み裁定・不変条件・段 1 実測・provisional 裁定 P1〜P5)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/D1603.md — pin 前進は材料 3 点を揃えてから裁定 (材料の定義)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/D297.md — pin 前進時の規律 1 検査の保証名と設計理由 (header 差分は保証外、比較 0 件の緑を作らない、compiler 依存)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/D986.md — checker の既知の穴 3 件は塞ぐ (ユーザー裁定)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/D722-D723.md — mocc 実供給 define の配線、commit tree 走査、submodule の限界。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/D2114.md — Silo 固定解除と mocc 第 2 例の準備着手、pin 前進は未承認 (本 wave の起点裁定)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/D2104-item13.md — 非 silo between-run 実測の保留と pin 再承認の手続き。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/insight-cross-protocol-s4-s6.md — 前 wave insight の §4 候補観測・§5 波及表の骨格 (13 行)・§6 準備 T。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/archive-872-t1506.md — T-1506 の記録 (511c→058d0c4e の checker 通過、16 context・実効 define map 4 種・digest 2 種、既存の穴 3 件)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/archive-1079-t1943.md — T-1943 の記録 (058d0c4e→e9e477ca の checker 通過)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/phase3-T167-row.md — 見送り台帳 [T-167] 行の現状 (提示先)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/pin-closure.tsv — 親が実測した pin 束縛 file の閉包 134 件 (path、形ごとの出現数、行番号。台帳・archive・insights 除く)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/spool-README.md — spool fragment の書式 (worklog / decisions)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/tools/check_trace0_preprocess_identity.py — 材料 (2) を出す checker (祖先性 gate、mocc trace.hh 特例、context 行列、report schema)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/orchestrator/campaign/source_digest.py — `_context_overlays` / `_head_defines` / `EVOLVE_BLOCK_SOURCE_PROTOCOLS` / `PROVEN_REPO_ABSENT_MACROS` の所在。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/output/README.md — insight の配置規約。読めなければ即停止。

## 依頼

親 brief の docs-only 成果物「[T-2756] ccbench pin 更新項の再承認材料 3 点」の plan を file:line 粒度で起草せよ。あなたは read-only で、書込み可能な tmp が無いので pytest・checker の実走は不要 (静的検査でよい)。checker の実走・check_docs・受入は親が行う。repo 内の path は上の worktree のものを使う。

**背景 (親が段 1 で確定した事実):** 候補 e9e477ca は現 pin 511c9538 の直系子孫 (4 commit、全 commit が cc/mocc/transaction.cc のみ変更)。checker は old ⊑ new の祖先性を要求し、今回は通る形。過去の checker 実走は区間別 (511c→058d0c4e、058d0c4e→e9e477) で、直接区間は未実施。context 行列は SILO_SPACE 8 genome × overlay 2 = 16。login node の compiler は g++ 11.4 / g++-12 / clang++ 14。gitlink・pin.py・s8b_approved.py は不動。gate・検査の新設は scope 外。

**親 brief の provisional 裁定 P1〜P5 と不変条件を前提に、次を書け:**

1. **事実の裏取り (file:line):** 親 brief の事実のうち次を repo の現物で確認し、誤りがあれば訂正せよ — (a) checker の祖先性 gate・`--expect-paths` の厳密一致・mocc trace.hh 特例 (`_mocc_trace_include_addition_index`) の受理条件・report の schema と `result` field (tools/check_trace0_preprocess_identity.py の該当行)、(b) `_context_overlays` の中身と `_head_defines(source_rel='cc/mocc/transaction.cc')` が mocc の CMake 供給 (RWLOCK / TEMPERATURE_RESET_OPT 等) をどう引くか (source_digest.py の該当行)、(c) D986 の 3 穴が現行 checker / source_digest でどう塞がれているか (fail-closed の箇所を file:line で。塞がれていない穴があれば「未対応」と書く)、(d) `_assert_proven_repo_absent_macros` が commit tree 走査で gitlink をどう扱うか (D723 の限界の所在行)。

2. **材料 (2) の実走計画と「保証範囲」の逐語案:** 親が login node で走らせる正確な argv (3 compiler 分)、report JSON の保存先 (insight verbatim 配下)、合格 / 拒否それぞれの記載形。保証範囲の逐語は親 brief P3 を土台に、**言い過ぎ (checker が保証しないことを保証するように読める文) と言い足りなさ (checker の docstring・D297・D986・D722/D723 が明記する限界で P3 に無いもの)** を列挙し、訂正版の逐語を書け。「16 個の異なる macro 構成を検証した」と書けない理由も含める。

3. **材料 (3) 波及表の分類案 (全数):** pin-closure.tsv の 134 file を親 brief P4 の分類軸 {A 定数, B 事前登録, C identity/lock/evidence, D 凍結物, E 歴史記録・figure provenance・paper-story 結果, F テスト pin/fixture, G 一致検査 consumer} へ **1 file ずつ** 割り当てよ (path → 分類 → pin 前進時の帰結 1 句 → 根拠となる該当行の役割)。分類できない file は「不明 (理由)」と書き、親が読む優先順位を付けよ。§5 骨格 13 行との対応 (骨格の行が閉包のどの file に当たるか、骨格に無い層があるか) も示せ。**特に**: `orchestrator/campaign/buildcache.py:1059`、`p3_s4_loop.py:112`、`silo_ladder_rung1.py:61`、`silo_ladder_rung1_contract.py:543`、`patches/ledger.json:10`、`tools/pegasus/mocc_trace_v1_policy.json:20`、`tools/pegasus/paper_story_a1_paired.sh:366`、`output/env/pegasus/calibration/registered/*.json`、`tools/known_violations/*.json` の役割を現物で確認して分類せよ。

4. **成果物の骨格:** insight README (`output/insights/2026-09-17/t2756-pin-evidence/README.md`) の節構成案 (材料 1〜3 を見送り台帳の再承認提示として読める順序、「この wave が判定しないこと」の明記位置)、verbatim の file 一覧 (checker report JSON ×3、閉包 TSV、子の逐語、MANIFEST)、`docs/phase3.md` [T-167] 行への 1 行追記の逐語案 (承認語を含めない)、spool worklog fragment の見出し案と記録項目。decisions fragment が要るか (新しい設計判断があるか) の判断と根拠。

5. **P1〜P5 への異議:** それぞれ「同意 / 異議 (根拠 file:line)」で答えよ。特に P1 (候補の確定に本 wave が足すべき根拠は何か、e9e477ca の commit 本文・author・trailer は確認したか)、P2 (`--expect-paths` を付けるべきか、3 compiler の選び方、`--cxx` に絶対 path を渡すべきか)、P4 (分類軸に欠けている層は無いか、規律 7 の適用が正しいか)。

6. **リスク:** check_docs.py の exact pin・byte 予算に当たる docs 編集 (phase3.md 行の追記が pin に当たるか)、三軸語・placeholder 走査 (`s8b_holdout_freeze search`) に当たる語、並行 wave (t2757 mocc-mutation-proof-design、t2760 tictoc-floor-baseline、同日) と編集面が重なる file、insight に checker report の生 JSON を置くときの size・NFC。

予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式

Markdown。先頭に `## 総括` (10 行以内: 訂正した事実の数、分類済み file 数 / 不明数、保証範囲の訂正点数、親 brief への異議の有無、decisions fragment の要否)。続けて上の 1〜6 を見出しにして書く。file path は worktree の絶対 path または repo 相対 path で書き、行番号を付ける。
