# 所見リスト

pytest は実行していない。385 passed、変異 10 KILLED、実 repo 件数は親提示の前提としてのみ扱った。

1. **real / blocker — R1-1 は partial：境界文字集合が実際の pathname を覆っていない**

   [`_has_bounded_path_reference()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/tools/audit_dangling_commits.py:456) は左右を検査し、拒否した出現の後も `start = index + 1` で全出現を走査している。この2点は閉じている。

   しかし境界集合は [`A-Za-z0-9.-_/` のみ](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/tools/audit_dangling_commits.py:28)。Linux の filename に使える `+`、`@`、`%`、非 ASCII byte などを含まない。実装の直接評価でも次になる。

   - `/jobs/w/a.py.backup` → 正しく非参照
   - `/jobs/w/a.py+backup` → 誤って `/jobs/w/a.py` の参照
   - `/jobs/w/a.py@backup` → 同上
   - `/@/jobs/w/a.py` → 誤って `/jobs/w/a.py` の参照

   したがって右側・左側とも一般形では閉じておらず、別 pathname の landed hit を短い候補へ流用できる。

   **成果物影響:** 条件 5 を満たさない `(commit,path)` が findings から消え、最後の finding なら rc が 1→0、抑止数が過大、残存対数が過小になる。

2. **real / must-fix — F26 の正本ポインタ削除は安全義務を弱めている**

   現 command は F26 を名指しするものの、[`docs/failures.md` への到達先を削除](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/.claude/commands/cleanup-branches.md:29)している。F26 本文には、command に複製されていない「[1 worktree ずつ削除し、必要なら timeout を延ばす](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/docs/failures.md:391)」という、半削除を防ぐ運用則がある。

   bare な「F26」だけでは正本が非一意・非自明であり、whole-file pin の再同期はこの意味欠落も正常として固定してしまう。

   **成果物影響:** cleanup の安全な受理集合が一括削除まで広がり、timeout 時に一部だけ消えた worktree を残し得るほか、F26 の authority reference が失われる。

## その他の fix 回帰判定

| 対象 | 判定 | 根拠 |
|---|---|---|
| 比較後 fstat | 安全 | [`final_stat`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/tools/audit_dangling_commits.py:351) で size・mtime_ns・ctime_ns・inode・mode を open 直後と比較し、変化時は `failed=True`。受理集合を安全側へ縮める |
| 既存 audit テスト | 安全 | 既存 node の変更は主に env 汚染を除く `monkeypatch.delenv`。期待値反転・assert 緩和・skip・削除はない |
| env 名 pin | 安全 | 実装は `OFFREPO_ROOT_ENV = "IZANAGI_DEV_WAVE_JOBS_DIR"`、positive test は[独立 literal を設定](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/orchestrator/tests/test_audit_dangling_commits.py:488) |
| command の synthetic/hash | 安全。ただし意味検査ではない | 実 command と synthetic はともに 3924 bytes で byte 一致。実測 SHA-256 と[checker 定数](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/tools/check_docs.py:403)・[test 定数](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/orchestrator/tests/test_check_docs.py:264)は `5d0087…586a` で一致 |
| `check_docs` の他検査 | 安全 | 実装変更は whole-file SHA-256 定数だけで、他 checker の述語は変更されていない |
| cherry 説明の縮約 | 安全 | ahead 単独では不足、rebase/cherry-pick の理由、`+` 行と main 不在時の報告義務はすべて残る |
| worklog 文の削除 | 安全 | command はクラス 2 を宣言し、[`CLAUDE.md` がクラス 2/3 終端の worklog 更新を直接要求](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/CLAUDE.md:156)している |
| F26 ポインタ削除 | **回帰** | 所見 2 のとおり、command に無い一件ずつの削除義務へ到達できなくなる |

## 変異が裏取りしていない穴

1. **real / blocker — 境界判定族**

   M01 は landed-reference の連言全体を落とすだけで、境界 helper を変異していない。現在の `+`／`@` 漏れ自体が、10 KILLED と385テストの前提下で残っている。また、全出現ループを「最初の出現だけ判定」に変えても、invalid occurrence の後に valid occurrence がある test がないため検出できない。

   **成果物影響:** 記号付き別 path では findings/rc が過小に、first-hit-only 回帰では正当な抑止数が過小になり得る。

2. **real / must-fix — fstat の各安定性 field は独立に pin されていない**

   追加 test が変化させるのは [`st_mtime_ns + 1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/orchestrator/tests/test_audit_dangling_commits.py:830)だけである。実装から `st_ctime_ns` の比較だけを削除してもこの node は通り、M01〜M10 にも該当変異がない。mtime を復元する writer に対する ctime 防壁を失っても検出できない。

   **成果物影響:** 比較中に変化した外部実体を一致として抑止し、findings と rc を誤って縮め得る。

3. **real / must-fix — command の意味削除と3者同時再 pin**

   command の安全文を削り、synthetic literal と2つの SHA-256 定数を同時更新すれば、whole-file 検査は通る。今回の F26 ポインタ削除が具体例で、10変異は command/check_docs を一切対象にしない。

   **成果物影響:** cleanup の安全義務・参照を削った内容が新しい「正しい bytes」として受理される。

[T-593]、ack 台帳、即時 prune、hardlink/root-symlink 防護、10倍規模実測は scope 外であり、本判定には混ぜていない。

## 総括

| 前レビュー | 判定 | 逐語根拠 |
|---|---|---|
| R1-1 landed 参照の部分文字列衝突 | **partial** | 左右判定と `start = index + 1` の全出現走査は実装済み。ただし `_PATH_EXTENDING_BYTES` の記号・非ASCII漏れで左右とも衝突が残る |
| R1-2 比較中のファイル変化 | **closed** | 比較後 `fstat` が size・mtime_ns・ctime_ns・inode・mode の変化を fail-closed にする |
| R2-2 env 名の誤記検出 | **closed** | test が実装定数ではなく literal `"IZANAGI_DEV_WAVE_JOBS_DIR"` を設定する |
| R2-3 command の SHA-256 pin 同期 | **closed** | 実 command、synthetic、checker定数、test定数の bytes/hash が一致する |

- 新規 blocker: **あり、1件**。R1-1 fix の境界文字集合漏れ。
- 別に real / must-fix が **F26 正本ポインタ削除**と未変異の防壁に残る。
- land 判定: **NO-GO**。