単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence

必読事項の射影:
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/output/insights/2026-09-17/t2756-pin-evidence/README.md — 段 5 で親が書いた成果物 (再承認材料 3 点)。**これがレビュー対象**。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/output/insights/2026-09-17/t2756-pin-evidence/verbatim/pin-closure.tsv — 親が採取した 134 行 (path、形別出現数、行番号)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/output/insights/2026-09-17/t2756-pin-evidence/verbatim/pin-impact.tsv — 134 行の分類 (段 2 plan 子起草、段 3 レンズ B 検算)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/output/insights/2026-09-17/t2756-pin-evidence/verbatim/pin_closure_scan.py.txt — 閉包の採取 script。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/output/insights/2026-09-17/t2756-pin-evidence/verbatim/s4-adjudication.md — 段 4 の親裁定。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/output/insights/2026-09-17/t2756-pin-evidence/verbatim/consult-B.md — 段 3 レンズ B の所見 (あなたの前段)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/D2114.md — 起点裁定 (理由節に pin 束縛の列挙と規律 7 の適用)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/D1603.md — 材料 3 点の定義。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/phase3-T167-row.md — 見送り台帳 [T-167] 行の現状。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/spool-fragment-draft.md — 親が書く予定の spool worklog fragment (完了 [T-2756] と [T-167] への見送り追記 1 行)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/CLAUDE.md — 絶対規律 7 の逐語。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/docs/spool/worklog/README.md — fragment の書式 (完了 / 見送り追記 / base)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/tools/check_docs.py — living docs の pin literal 拒否・行番号参照拒否・placeholder。読めなければ即停止。

## 依頼 (段 6 敵対レビュー B: 材料 (3) 波及表・集合外依存・提示形・再現条件)

あなたは read-only の敵対レビュー子である。段 5 の成果物 README (特に §4〜§7) と spool fragment 案を、**波及表が再承認の判断材料として正確か**、**規律 7 の適用が正しいか**、**提示形が台帳規約と check_docs に通るか**の観点で攻撃せよ。pytest の実走は不要 (親が実測する)。段 3 レンズ B の所見 (M1〜M6、N1、N2) が README に反映されているか、反映が誤っていないかも検査せよ。

攻撃対象:
1. README §4.2 の層別表: 件数 (A12 / B12 / C31 / D1 / E35 / F31 / G12) を pin-impact.tsv で再集計し、代表例の path が実際にその分類か (例: `phase3-8b-restart-runbook.md` は G、`buildcache.py` は E) を TSV で照合せよ。帰結欄が「保持」で閉じるべきでない層を名指しせよ。
2. README §4.1 の作業一覧 10 項: 各項が現物で裏付けられるか (`buildcache.py` docstring の再実測要求、`test_s8b_approved.py` の gitlink 照合、`p3_s4_loop.py` の D1936 固定、`pin.py` 冒頭の歴史的 driver 注記、前回の pin 前進 commit `fb5e74a17` の本文)。`git show --stat fb5e74a17` を読み、README の要約 (「現用 23 箇所追随・歴史据置・校正 pin 4 件・再測定なし」) と一致するか。
3. README §4.3 の境界表: 規律 7 の逐語 (CLAUDE.md) と D2083 (`docs/decisions.md` の見出しを grep して該当項を読む) に照らし、「保持 / 再取得 + 新登録 / 再承認パッケージの一項」の判定が過不足ないか。親の推奨 (旧較正の流用は既定で再取得) が D または規律の逐語と矛盾しないか。「orchestrator/campaign に record の head_sha を読む consumer は無い」を grep で検算せよ。
4. README §4.4 の集合外依存表: 各 file が実在し、記述した役割 (gitlink を読む、preimage 不一致を拒否、7 桁 pin) が現物と一致するか。凍結 raw-manifest 3 本の `current_pin` の形を実測せよ。
5. README §4.2 の取得条件 (日付・HEAD・除外 pathspec・母集合・形別 regex) が pin_closure_scan.py.txt と一致するか。「134 は依存閉包でも更新対象件数でもない」が明記されているか。
6. spool fragment 案: `完了` の `remaining: none` と `base:`、`見送り追記` の 1 物理行が README 書式に合うか。追記文が pin literal (7 桁) を含まないか、承認語を含まないか、`.md:数字` 形の行番号参照を含まないか、`状態:` を含まないか。title が worklog 冒頭の書式に合うか。
7. README 全体で、`tools/check_docs.py` や `s8b_holdout_freeze search` (三軸語 `ycsb_rratio` / `ycsb_zipf_skew` / `ycsb_rmw` の値付き表記が 1 file に 3 軸そろうと hit) に当たる語、placeholder 文字列、非 NFC 文字があるか静的に検査せよ (verbatim の生 report / TSV / 較正 JSON の転載を含む)。

各所見は「所見 / 根拠 (README の節、verbatim 名、file:line) / 正しさ境界 or 整合・実効性 / must-fix or nit / 是正案 (どの文をどう書き換えるか)」の形で書け。予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式

Markdown。先頭に `## 総括` (10 行以内: must-fix 件数、nit 件数、件数・分類の誤りの件数、段 3 レンズ B の未反映件数、fragment 案の可否)。続けて上の 1〜7 を見出しにして書く。
