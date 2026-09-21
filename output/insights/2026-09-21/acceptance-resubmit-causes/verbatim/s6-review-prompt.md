単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-resubmit-causes

必読事項の射影 (読めなければ即停止):
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-resubmit-causes/output/insights/2026-09-21/acceptance-resubmit-causes/README.md — レビュー対象 (親が起草した診断 insight、docs のみ、未 commit)。
- 同 dir の verbatim/: origin.md (依頼の逐語)、classification.md (分類表の機械出力)、s1-brief.md、s3-consult.md (段 3 相談の報告)、s3-consult-prompt.md、s4-ruling.md (段 4 裁定)、waves.txt (対象 20 wave)、scripts.sha256 (job dir の script と抽出物の束縛)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-resubmit-causes/timelines-all.txt — 20 wave の job dir から機械抽出した時系列 (sha256 は verbatim/scripts.sha256 の timelines-all.txt 行と一致すること)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-resubmit-causes/classify.py、extract.py — 集計・抽出 script (同 sha256 束縛)。
- 一次資料 (job dir、必要な試行だけ直接読んでよい): /work/1/SFC/tanab/dev-wave-jobs/<job dir 名>/acceptance-*.chain.log、gate-loop-*.log、acceptance-<label>-<n>.log、acceptance-child-<label>-<n>.log、acceptance-receipt-*.json、acceptance-<label>-<n>.started.txt / .finished.txt、land*.json / land*.log、run-acceptance-gated.sh / gate-acceptance-loop.sh。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-resubmit-causes/tools/dev_wave_wait.py (`_behind_count`、`_StageFailure("postcheck")` 3905 行付近、`terminal-merge`)、tools/dev_wave_land.py (`_forward_main_merge_topology` 2120 行付近)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-resubmit-causes/docs/dev-wave/operations.md (`DW-O17` 付近 94 行「記録 commit が tested tip から漏れ land が rc=23」、`DW-O18` 137 行付近、`DW-O20` 156 行付近、`DW-O26` 185 行付近、`DW-O27`)、docs/failures.md (`### F902`、`### F1013`、`### F524`、`### F1000`、`### F474` の見出しを grep して該当節だけ)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-resubmit-causes/output/insights/2026-09-21/dev-wave-wall-decomp/README.md (51 行付近・87 行付近、README §6 が訂正する対象)。
- 帰属判定の出所: docs/worklog.md の entry 1777 (711〜731 行、T-2817 の非帰属判定)、docs/archive/worklog-phase3-0921-1770.md (T-2344 の自分起因判定)、docs/worklog.md entry 1776 (63〜110 行、T-2810 の非帰属判定)、/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-backup-loss-record/HANDOFF.md (23〜26 行、1759 の判定)、output/insights/2026-09-20/t2797-b5-contrast/README.md (91〜92 行、T-2797 fix4)。

## 目的

これは自分たちの開発 wave の受入手順の診断 insight の独立 read-only レビューである (段 6、reasoning=medium、1 本)。
親が起草した README が **一次資料で閉じているか** を、次の 2 レンズで検査し、根拠 (file:line、job dir の file 名と行、README の節) 付きで所見を出せ。親を守る側に立つな。見つからなければ「見つからない」と書け。

## レンズ

1. **派生値の再計算 (DW-O16):** README §4.1〜§4.3 の数値 (門番待ち・外側 wall・追加 wall・合計 342.3 / 273.1 / 175.7 / 97.4 / 69.2、「11 / 5」、分類ごとの件数と分)、§4.3 直下の文 (D1〜D4 で 7 件・152.0 分・門番 144.0 分、test 実行の再試行 7 件・外側 wall 84.7 分)、§4.2 の「119.5 分は 1761 と 1759 の 2 試行」、§5 の各分類の数値 (D4 の 0.8〜2.5 分・再門番 2.0〜2.9 分、E の 25.2 分、B の 57.0 分、D1/D2 の 121.6 / 119.5) を、verbatim/classification.md と timelines-all.txt と一次資料 (started/finished、chain / gate-loop log) から再計算して照合せよ。少なくとも 4 wave (1779 / 1769 / 1759 / 1775) は一次資料の時刻から手で検算する。「すべて」「だけ」「0 件」の量化 (C 0 件、F 0 件、lease 失効の停止行なし、9 wave が 1 試行) は原データで裏取りする。
2. **分類と手順の名指しの正しさ + 過剰・削除:** (a) 15 件の再試行の分類が attempt log の `classification` / `reason`、child log の FAILED 行、chain / gate-loop log の停止行、land 記録の `reason` と一致するか。(b) §5 の「守られなかった既存手順」の名指しが正本の該当節を正しく引いているか (DW-O17 付近の順序命令、DW-O18 の worklog 記録義務と hold 登録の撤回、DW-O20、DW-O26、F902 / F524 / F474 / F1000)。名指しの無い断定 (「守られている」「該当事象なし」「wave の手順では防げない」) が資料より強くないか。(c) §6 の entry 1774 への訂正が同 insight の記述と一致するか。(d) §8 の裁定パッケージが依頼の禁止 (gate・台帳・一般化の追加、受理集合・門番・hold の意味論の変更、規律 2 の緩和) に触れていないか、実装提案に踏み込んでいないか。(e) §9 に値なし前方参照・placeholder が無いか (走査・check_docs は親が commit 前に実測して埋める予定; 現状の文が「実測後に埋める」と読めるなら placeholder として指摘せよ)。(f) 診断 wave として書きすぎ (一般化・断定) と、依頼に対する欠落 (6 分類の件数と追加 wall、3 手順への回答、裁定パッケージ) を挙げよ。

## 出力形式

- 所見ごとに「所見 N: <要旨> / 根拠: <file:line or job dir file 名> / 影響: <数値・分類・名指しのどれがどう変わるか> / 提案: <README の書き換え内容>」。
- 最後に `## 総括` を必ず置き、GO / NO-GO と、must-fix / should / nit を分けて列挙し、must-fix 0 なら「must-fix なし」と明記する。
- 書込可能 tmp は無い。静的検査 (読取り + grep + 手計算) でよい。test の実走は不要。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。
