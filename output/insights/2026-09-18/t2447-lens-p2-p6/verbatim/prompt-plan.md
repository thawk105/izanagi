単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/brief.md (親 brief。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/proposed-edits.md (候補文言と byte 差。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/D1893.md (ユーザー裁定の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/D227.md (予算原資の条件。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/D1798.md (P1 収容時の裁定。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/origin-insight-excerpt.md (P2/P6 の原典。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/dev-wave/workers.md (編集対象。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/dev-wave/core.md (編集対象。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/dev-wave/operations.md (編集対象。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/.claude/commands/dev-wave.md (入口、不変。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/tools/check_docs.py (pin と予算の実装、不変。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/skill-self-improvement.md (routing の正本、不変。読めなければ即停止)

## 目的
これは自分たちの開発手順書 (dev-wave の docs) の docs-only 変更の計画である。ユーザー裁定 D1893 で採った P2 (段 3・6 のレンズ 1 本を「過剰・削除」レンズに固定) と P6 (研究前進か実測欠陥の根拠が無い scope 外所見は起票せず記録のみ) を `docs/dev-wave/` の該当節へ収容する。実装面 (コード・テスト・`tools/check_docs.py`・command 入口) は触らない。P4 (変異 matrix の義務) は触らない。

## 依頼
brief と候補文言 (E1〜E7) を読み、file:line 粒度の plan を起草せよ。次を必ず含める。

1. 各編集 (E1〜E7) について、編集対象の file と現行の行番号、置換前後の逐語、byte 差。親の実測値 (proposed-edits.md) と食い違えば自分の値を示す。
2. 削減原資 (E3、E4、E6、E7) が D227 の 3 条件 (同一読点・上位互換・単一正本化) を満たすか、担い手節の逐語を並べて要素ごとに照合する。欠落要素があれば列挙し、代替の原資を提案する。
3. `tools/check_docs.py` の pin・構造 regex (DW-S03 / DW-S06-A / DW-S06-C の reasoning pin、`CODEX_FIRST_REFERENCE_LITERALS`、`CODEX_AUTHORING_STRUCTURE`、`DEV_WAVE_LAND_HELPER` 系、D2/D4 構造 regex、層予算の計算) のうち E1〜E7 が触れるものを列挙する。触れないなら根拠の関数名・定数名を書く。
4. P2 の収容形 (Q1、Q2) と P6 の収容形 (Q3) について、D1893 の逐語との意味の差 (足りない要素・広がった要素) を列挙する。
5. 親が段 5 で実行する編集手順と検査手順 (`python3 tools/check_docs.py`、関連テストの nodeid) を順に書く。
6. 段 3 の 2 レンズ (A = 正しさ境界・整合、B = 過剰・削除) が点検すべき論点を各 3 件以内で挙げる。

## 制約
- 静的検査のみ。pytest を要求しない (書込可能 tmp が無い)。テスト実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- 出力は file に書かず、最終メッセージの本文に全文を書け (親の launcher が保存する)。
- 見出しは全部 H2 (`## `) で書く。`###` を使わない。

## 出力形式
## plan (E ごとに file:line、逐語、byte 差)
## D227 照合 (原資ごとに要素対照表)
## pin と構造 regex の照合
## D1893 との意味差
## 段 5 の手順
## 段 3 の論点
## 総括
