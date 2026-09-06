単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s4-adjudication.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s4-adjudication.md` — 親の段 4 裁定。4 節 (plan v2 — C1a) と変異 M1〜M12 が受入基準の正本
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/artifacts/t1851-unit-c/s6-rereview.md` — 焦点再レビュー 1 回目 (NO-GO)。残った A-1 / A-3 / R-1 / R-2 の所見と、M12 の指摘
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/prompt-s6-fix3.md` — fix3 へ渡した契約と親の裁定 (A-1 / A-3 / R-1 must-fix、R-2 nit、M12 は本 wave で変更しない = C1b 持ち越し)
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/artifacts/t1851-unit-c/s6-fix3.md` — fix3 の完了報告 (4 件 closed と自己申告)。**検証対象**
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s6-fix3.patch` — fix3 の差分 (launcher +13/−1、test +59/−12)
6. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s5-s6-fix3-integrated-snapshot.patch` — 統合差分の全文 (実装子 + fix1 + fix2 + fix3、base `04f06d032` に対する差分)

**統合後のコードは `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a` にある (未 commit の作業 tree)。所見はここの現物で裏を取れ。**

## 依頼

あなたは統合後の焦点再レビュー 2 回目 (最終) である。fix3 の 4 件 (A-1、A-3、R-1、R-2) が現物で閉じたかと、fix3 が新たに持ち込んだ破れが無いかだけを見る。1 回目で closed とした 6 件は再検査しない (fix3 差分がそれらに触れていないことの確認だけでよい)。

## 検査の軸

1. **4 件の closed / partial / regressed 表。** 各件に (a) 修正の現物 file:line、(b) 検査 node と単一理由性、(c) 判定。
2. **A-1。** `_snapshot_keyword_argument` は Mapping → `dict`、`list` / `tuple` → `tuple`、他は identity。(i) この型変換が実体 `calibrator/runner.py` の `capture_measure_point` / `open_measurement_point` の受け取り (`numactl: Sequence[str]`、`extra_env`、`workload`) と衝突しないか、(ii) `_CERTIFIED_MEASUREMENT_KEYWORDS` の中で Mapping / sequence を取る key はどれで、identity を保つべき object (capability 系) が dict 化されていないか、(iii) node が nested container の変異を pre-probe 中に起こし capture 側で検査時の値を観測しているか。
3. **A-3。** `_CallableDict` 入力が `_contains_callable` を外すと後続の canonical 化・receipt 検査を通るか (静的に追う)。拒否 message の固定が callable gate 固有か。
4. **R-1。** exact tuple 比較が private sink の 3 record 全体 (6 key の値) を固定し、fix2 前と同等以上の強さか。
5. **R-2。** observed 申告の non-null 値が実 core の observed null matrix に適合する形か。deferred reader の未封印検査が registry recorder の実装と整合するか。
6. **fix3 の新規持ち込み。** fix3 差分の中に、4 件に対応しない変更 (削除された検査、緩められた assertion、新しい fail-open 経路、期待値の書き換え) が無いか全件列挙せよ。所有外 (`test_official_perf_closure.py` の 2 guard 逐語、`test_ccbench_spawn_sites.py:212`、adapter / core / profile / campaign / calibrator) が無変更か。
7. **変異 M1〜M12 の観測 node 名**が fix3 で変わっていないか (改名・分割があれば新旧対応)。

## 出力形式

先頭に 4 件の表を置く。新規所見は `所見 R-N` (N は 3 から) の見出しを付け、(a) 何が問題か、(b) 現物の file:line、(c) real なら放置時に成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるか 1 行、(d) 修正案、を書け。各主張に [実測] / [推測] を付けろ。**blocker / must-fix / nit** を分けろ。成果物影響を書けない所見は must-fix にしない (DW-G05)。

## 制約

- 読取専用である。pytest の実走は要求しない。静的検査でよい。実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 出力の最後に `## 総括` 節を置き、closed / partial / regressed の件数、新規 blocker / must-fix / nit の件数、GO / NO-GO の判定を 8 行以内で書け。
