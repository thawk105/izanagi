単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/s5-diff.patch (レビュー対象の commit de7cc6424 の差分。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/s4-ruling.md (段 4 裁定と plan v2。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/brief.md (親 brief。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/out-plan.md (段 2 plan。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/out-consult-A.md (段 3 レンズ A の所見。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/out-consult-B.md (段 3 レンズ B の所見。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/D1893.md (ユーザー裁定の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/D227.md (予算原資の条件。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/dw-s03-after.md (改訂後の DW-S03 = 段 6 レンズの定義元。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/dev-wave/workers.md (改訂後、commit 済み。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/dev-wave/core.md (改訂後、commit 済み。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/dev-wave/operations.md (改訂後、commit 済み。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/dev-wave/mutation.md (不変。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/.claude/commands/dev-wave.md (入口、不変。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/tools/check_docs.py (pin と予算の実装、不変。読めなければ即停止)

## 目的
これは自分たちの開発手順書 (dev-wave の docs) の docs-only 変更のレビューである。ユーザー裁定 D1893 の P2 / P6 を `docs/dev-wave/` へ収容した commit de7cc6424 (3 file、+8/−8 行、実装面 0 byte) を、**レンズ A = 正しさ境界・整合・実効性**で点検する。欠陥を指摘するのが役目で、差分を追認するものではない。

## 親が実行済みの分担 (差分は commit 後のもの)
- 親が段 4 裁定 (s4-ruling.md) に従い 7 編集 (E1〜E7) を当てて commit した。`git diff --check` rc=0、`python3 tools/check_docs.py` 違反なし、層予算の実測 L1 10,616 / 10,625、L1.5 9,660 / 9,696、full provenance 監査 rc=0。
- consumer test 3 file (`orchestrator/tests/test_check_docs.py`、`test_dev_wave_launch_authority.py`、`test_codex_worker_launch.py`) の焦点走は親が並行して実走中。結果は本レビューの入力ではない。
- 実装面差分ゼロのため変異 matrix は DW-S04 により免除、受入全走は免除しない。

## レンズ A の問い
1. **安全義務の消失**: E3 / E4 / E6 / E7 と E2 の pointer 削除について、差分の逐語と担い手節の逐語を並べ、D227 の 3 条件 (同一読点・上位互換・単一正本化) を満たさない要素があれば挙げよ。段 3 の照合 (out-consult-A.md の対照表) が見落とした要素を探せ。
2. **D1893 との一致**: 収容後の DW-S03 / DW-S06-A (P2) と DW-S04 (P6) の文言が、D1893 の逐語より狭い・広い点を列挙せよ。特に (a) P2 のレンズ定義「研究前進・実測欠陥への対応、削除・局所修正の可否」が D1893 の「過剰・削除」を過不足なく表すか、(b) P6 の「資料/実測で示せる場合だけ」が D1893 の「根拠が無い」を判定可能な形にしつつ、静的に確認した正しさの破れを落とさないか。
3. **規律 2 と変異義務**: 差分が正しさゲート・DW-S04 の変異免除条件・DW-M01・DW-STOP に触れていないことを逐語で確認せよ。P6 が停止・受入・変異義務の免除と読める余地があれば指摘せよ。
4. **pin・構造検査・予算**: `tools/check_docs.py` の pin (reasoning pin、`CODEX_FIRST_REFERENCE_LITERALS`、`DEV_WAVE_LAND_HELPER` 系、exact 節 pin、層予算の計算) に対し、差分後の bytes が通ることを関数名・定数名を挙げて静的に確認せよ。親の「違反なし」を鵜呑みにしない。
5. **二義化**: 改訂後の DW-S04 (P6) と DW-G05 第 1 段落 (nit/backlog)・第 2 段落 (追加実装の許容条件)、`docs/skill-self-improvement.md` routing 2 との間で、同じ所見が違う扱いになる経路があれば示せ。段 4 裁定は「段を問わず同じ基準、routing を迂回路にしない」を解釈として記録した — この解釈が docs の逐語と矛盾するなら指摘せよ。
6. **fixture と実物の 1 文字照合**: s4-ruling.md の plan v2 表の置換後文言と、commit 後の実 file の逐語が 1 文字も違わないか照合せよ (改行位置を含む)。

## 制約
- 静的検査のみ。pytest を要求しない (書込可能 tmp が無い)。テスト実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- 出力は file に書かず、最終メッセージの本文に全文を書け (親の launcher が保存する)。
- 見出しは全部 H2 (`## `) で書く。`###` を使わない。
- 所見は 1 件ずつ「RA-n / 対象 / 主張 / 根拠 (file:line) / 放置時に成果物 (手順書の義務・受理集合) がどう変わるか / 分類 (must-fix・nit・記録) 」の形で書く。must-fix は放置時の影響を 1 行で書けるものだけにする (DW-G05)。

## 出力形式
## 所見 (RA-1 …)
## D1893 逐語との対照
## 逐語照合 (plan v2 と実 file)
## 総括
