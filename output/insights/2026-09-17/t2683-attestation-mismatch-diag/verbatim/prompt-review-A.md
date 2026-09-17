単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/parent-brief.md — 親 brief。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/stage4-ruling.md — 段 4 裁定・plan v2・変異事前登録 (M1〜M11、E1) と報告枠。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/author-snapshot.patch — 段 5 author の統合差分 (レビュー対象の正本)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/author-out.md — author の最終報告 (未実走の申告を含む)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/focus1-driver.log — 親が走らせた変更 test file の単独焦点走 log (実走結果)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/ruling-items-14-15.md — ユーザー裁定 (D2104 項 14・15)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/D474.md — D474。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/qualification/t126_driver.py — 変更後の実体。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/tests/test_t126_qualification_driver.py — 変更後の test。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/qualification/artifacts.py — create-only / strict loader の契約。読めなければ即停止。

## 依頼 — レビュー A: 正しさ境界・受理集合・規律

段 5 の差分を**敵対的に**レビューせよ。あなたは read-only で pytest 実走は不要 (静的検査でよい)。実走結果は focus1-driver.log を一次資料とし、log に無い緑を主張しない。

観点:
1. **受理集合の不変性:** 差分のどこかで attestation の受理・拒否が 1 bit でも動くか。`_attest` の条件式、`_run_attestation_child` の rc、`except BaseException` の位置、closure の親分岐 (timeout 分岐の文言は不変か)。
2. **成功経路の bytes 不変:** `_run_attestation_child` の成功分岐が旧 closure と同じ payload (`stage` / `round_index` の追加順序を含む) を同じ相対 path へ書くか。test `test_t2683_match_preserves_accepted_bytes_without_sidecar` の期待値が helper の出力から独立に組み立てられているか (自己参照になっていないか)。
3. **sidecar の内容 (段 4 P2):** exact 9 keys、`comparisons` が無加工の全行、`failed_fields` の導出。`comparisons` の行に JSON 化できない値が来る経路は無いか。
4. **D474 との整合:** 診断の書込み失敗が rc を変えないか。sidecar が受理判定・checker authority に一切使われていないか (`_attestation_rejection_message` は表示だけか)。
5. **親 message helper:** `path.exists()` / `load_json_strict` の例外吸収が完全か。`capability.root / Path(relative).with_suffix(...)` と成功経路 `capability.root / relative` の整合。attempt_dir 相対 path の導出が `relative_to` で失敗する条件。
6. **test の弱さ:** 各 test が実物 (parser・比較・hash・create_json・strict loader) を通しているか、stub 境界が段 4 の指定 (較正 loader と probe だけ、書込み失敗 test は mismatch path だけ) を超えていないか。`monkeypatch.setattr(Path, "exists", fail)` のような広い patch が他 fixture を壊さないか。既存 test の assertion が弱められていないか。
7. **変異事前登録との対応:** author の anchor 表 (author-out.md) の各行番号が実体と一致するか。M1〜M11 の各変異について、期待 killer test が**その test の assertion で**赤になるかを静的に追い、赤にならない (恒真) 候補と、複数理由で赤になる (単一理由性を欠く) 候補を指摘せよ。E1 (docstring 変更) が等価か。

各所見に「放置時に成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるか」を 1 行で付け、示せない所見は nit とし must-fix にしない。既存テストの期待値変更を是正案にしない。

予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式

Markdown。先頭に `## 総括` (10 行以内: must-fix 数 / nit 数 / GO or NO-GO)。続けて観点 1〜7 の見出しで所見 (所見 / real か refuted か / 根拠 file:line / 是正案)、最後に `## 変異の帰属判定` (M1〜M11・E1 の表)。
