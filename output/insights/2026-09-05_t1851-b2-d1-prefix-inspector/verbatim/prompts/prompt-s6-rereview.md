単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s4-adjudication.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s4-adjudication.md` — 親の段 4 裁定 (plan v2、変異事前登録、不変 pin 表)
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s6-review-a.md` と `s6-review-b.md` — 段 6 レビュー 2 本 (fix 前の所見)
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/prompt-s6-fix1.md` — fix1 へ渡した契約 (F1〜F7)
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s6-fix1.md` — fix1 の完了報告。**自己申告であり検証対象**
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s6-fix1.patch` — fix1 の test 差分 (統合前 test → fix 後 test の unified diff、4 file)
6. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s5-integrated.patch` — 段 5 統合差分 (production 4 file は fix1 で変わっていない)

**統合後のコードは `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a` にある (未 commit の作業 tree)。所見はここの現物で裏を取れ。**
親は統合 tree で消費側 20 file の焦点走を実走している (結果は親が持つ。本レビューは静的検査)。

## 依頼 — fix 後の焦点再レビュー (DW-O16)

fix1 が段 6 レビュー A / B の所見を閉じたかを、**所見ごとに closed / partial / regressed** で判定せよ。表なしで「閉じた」と判定してはならない。

## 検査の軸

1. **F1 (M14 実台帳 2 世代 test):** 同一 shared root に production API で有効な v2 世代 A / B を作っているか (手書き行・stub でないか)。artifact / reported proof が B、wrapper の外部引数が A で、
   正しい実装が拒否し、M14 変異 (expected binding を reported proof から採る: `s8b_floor_stats.py` の `expected_binding = _attempt_profile.S8BAttemptBinding(` ブロック) だけが B を replay して受理する単一理由形か。
   同じ test 内に A/A の受理正例があるか。inspector を monkeypatch していないか。
2. **F2 (validator stub 除去):** 通常時の validator monkeypatch が全 v5 test から消えたか。spy が production validator を包み reported / expected の 2 回呼出しを assert しているか。
   `raising=False` が残っていないか。fake inspector test の期待 freeze が外部引数から独立に導出されているか。
3. **F3 (不変 pin node):** `test_floor_campaign_directly_reexports_shared_leaf_objects` が base `50dbf9158` の bytes と完全一致か (`git show 50dbf9158:orchestrator/tests/test_s8b_floor_contract.py` と比較せよ)。
   移した assertion が新規 node にあるか。
4. **F4 (M10 再照準):** 合成 v1 が production scheduler authority で作られ、v2 schema guard (`genesis.get("schema_version") != profile8b.S8B_V2_ATTEMPT_REGISTRY_SCHEMA_VERSION`) を
   `not in (v1, v2)` へ緩めたときに後段 (`_profile_and_binding_for_generation`、`core.load_attempt_registry`) まで成功して受理される入力か。guard 以外の gate が拒否しないことを test 内で示しているか。
5. **F5 (M13 再照準):** v4 node の validator seam が、v5-only guard (`and artifact.get("schema") == _floor_contract.RESULT_SCHEMA_V5`) を消したときだけ inspector tripwire へ到達させるか。v4 の `[]` 正例が維持されているか。
6. **F6 / F7:** 診断 node の明記、parametrize id の区別。
7. **弱体化の検査:** fix1 の差分に既存 assertion の削除・反転・緩和・skip が無いか。不変 pin 表の 4 file の既存行削除が 0 件か。production 4 file が段 5 統合 patch と byte 一致か。
8. **変異帰属表の更新:** 段 6 レビュー B の帰属表を fix 後の現物で更新し、M1〜M6、M8〜M18 (M7 除外) それぞれについて (old 逐語の所在 file:line、観測 nodeid、帰属成立 / 遮る層) を書け。
   親が用意した probe spec の anchor は次のとおり。各 anchor が現物に一箇所だけ存在するか確認せよ。
   M1 `if actual_keys != ATTEMPT_REGISTRY_PREFIX_PROOF_KEYS:` / M2 `freeze_sha256 = _digest(...)` の 3 行 / M3 `row_count < 1` / M4 `if chain_head_sha256 == _ZERO_SHA256:` /
   M5・M6 `return core.load_attempt_registry(payload, profile=generation_profile, expected_binding=expected_binding)` の 5 行 (M5 = 最初の parse 失敗で止まる寛容 decode、M6 = chain 検査なしの decode-only) /
   M8・M9 `if rows[row_count - 1]["event_sha256"] != chain_head_sha256:` / M10 v2 schema guard の 3 行 / M11 `_RESULT_V5_KEYS = ...` / M12 `if reported_attempt_registry != independent_attempt_registry:` /
   M13 v5-only guard の 3 行 / M14 `expected_binding = ...` の 7 行 / M15 `_RESULT_V4_KEYS = frozenset({` の先頭 2 行 / M16 header freeze 比較の 4 行 / M17 `if registry_schema != ...:` / M18 `root = admission.shared_admission_root(Path(repo_root))`。
   各変異について「その変異で赤になる node の完全集合」を静的に予測し、登録 node 以外に赤になりうる node があれば列挙せよ (DW-M08 は完全集合の一致を要求する)。

## 出力形式

所見 F1〜F7 の closed / partial / regressed 表を最初に置く。新規所見は `所見 N` の見出しで (a)〜(d) を書き、blocker / must-fix / nit を分ける。変異帰属表を別節に置く。各主張に [実測] / [推測] を付けろ。

## 制約

- 読取専用である。pytest の実走は要求しない。静的検査でよい。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 出力の最後に `## 総括` 節を置き、closed / partial / regressed の件数、新規 blocker / must-fix の件数、GO / NO-GO を 10 行以内で書け。
