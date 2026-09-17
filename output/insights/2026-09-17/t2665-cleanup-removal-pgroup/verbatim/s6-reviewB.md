## 適合表

参照略号：

- **L** = [tools/cleanup_remove_dirs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2665-cleanup-removal-pgroup/tools/cleanup_remove_dirs.py)
- **T** = [orchestrator/tests/test_cleanup_remove_dirs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2665-cleanup-removal-pgroup/orchestrator/tests/test_cleanup_remove_dirs.py)
- **D** = [.claude/commands/cleanup-branches.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2665-cleanup-removal-pgroup/.claude/commands/cleanup-branches.md)
- **C** = `tools/check_docs.py`、**CT** = `orchestrator/tests/test_check_docs.py`

| 区分・項目 | 判定 | 根拠・file:line |
|---|---|---|
| S1 空・NUL の拒否 | 適合 | L:65 |
| S1 絶対・正規形、`/`・`//`・末尾 `/`・`.`・`..` の拒否 | 適合 | L:65–68。途中の重複 `/` も拒否 |
| S1 途中を含む symlink 拒否 | 適合 | L:69–74 |
| S1 実在 directory | 適合 | L:72–74 |
| S1 realpath 一致 | 適合 | L:75–76 |
| S1 重複・相互包含を component 単位で拒否 | 適合 | L:79–82 |
| S1 cwd の一致・包含拒否 | 適合 | L:63、77 |
| S1 option 検証・全件検証後に起動・usage rc64 | 適合 | L:49–83、182–200、258。裁定外の過剰拒否は認めない |
| S1 固定 argv、TemporaryFile、Popen の禁止引数なし | 適合 | L:197–202 |
| S1 全対象の連続起動・直後の PGID 実測 | 適合 | L:194–205 |
| S1 TERM/INT/HUP handler は最初の番号記録のみ | 適合 | L:174–180 |
| S1 共通取消、5 秒→KILL→1 秒、killpg 不使用 | 適合 | L:100–117、225、247 |
| S1 子ごとの timeout・50 ms poll | 適合 | L:199、207–220 |
| S1 removed/failed/interrupted/unknown の判定順 | 適合 | L:120–146。負の returncode は failed より先 |
| S1 全対象の最終 lstat、ENOENT のみ absent | 適合 | L:125–130、228 |
| S1 最終集約・取消 flag・JSON summary と終了 rc | **逸脱** | L:241–258。summary 作成と終了 rc 再計算の間に取消状態が変わる〔B-01〕 |
| S1 stdout JSONL、子 stderr 先頭 4 KiB の診断 | 適合 | L:231–244。診断は stderr に出力 |
| S1 docstring 必須事項 | 適合 | L:2–14。保証外、名前空間、PATH、仮 timeout、prune 等不実施を明記 |
| S1 scope | 適合 | 任意 command、再試行機構、監視機能、PDEATHSIG 実装、prune、`--one-file-system`、余計な CLI option は追加なし |
| S2 必須 helper・summary/rows 整合・終了 rc assert | 適合 | T:21–67、95–99 |
| S2 wrapper exact 3 行・同 PID exec | 適合 | T:75 |
| S2 実 rm 正例・独立 PGID 観測正例 | 適合 | T:120–148 |
| S2 TERM/INT/HUP、T→pending→CONT、`-signum` | 適合 | T:151–170。逃げの `or`、signal node の skip なし |
| S2 timeout の同期・`-SIGTERM`・対象残存 | 適合 | T:173–190 |
| S2 一部失敗と他対象成功・chmod 復旧 | 適合 | T:193–209。ただし起動例外時の復旧漏れ〔B-02〕 |
| S2 usage path/cwd/options・対象残存 | 適合 | T:212–263。必須列挙を包含し、NUL・double-slash・dot を追加 |
| S2 判定関数直呼び・summary 負例 | 適合 | T:266–292。追加余地あり〔B-03〕 |
| S2 待機期限 ≤10 秒・KILL 経路 node なし | 適合 | 通常期限 6/8 秒、後始末は最大 2+2 秒。launcher の KILL escalation を成功条件にする node なし |
| S2 skip 条件 | 適合 | wrapper node はなし。chmod node の root skip のみ、裁定で明示許可 |
| S2 ASCII id・一時物・自走 harness | 適合 | T:71、151、212、235、251、295。独自の repo 内一時物作成なし、harness は参照元と同形 |
| S3 exact 文案・6201 bytes・指定 SHA | 適合 | D:56–62。実ファイルの bytes/SHA を静的計算して一致確認 |
| S3 SHA pin 2 箇所・synthetic 全文一致 | 適合 | C:752、CT:580、627 |
| S3 `6_201` 2 箇所・`"x" * 3` | 適合 | CT:9849、9854–9856。6205 bytes の負例、上限 6204/110 不変 |
| S3 削除述語・閾値・評価順 | 適合 | §1・§2・§3 冒頭・§4 以降が HEAD と byte 単位で一致 |
| S3 運用順序・Codex overlay | 適合 | D:53–62 を通読すると占有検査→detach→branch -d→前景 launcher 1 回→rc0→prune 判定。D:14–15 と overlay:28–29 により Codex の real prune 禁止は維持 |

**過剰に該当する実装は認めません。**

## 所見

**B-01 — 種別: 仕様逸脱／出力契約、推奨: must-fix**
場所: [L:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2665-cleanup-removal-pgroup/tools/cleanup_remove_dirs.py:241)、L:258。

`summary` は 241 行で取消状態をコピーします。その後、JSON 出力または flush 中に TERM/INT/HUP を受けると、handler が `cancelled` を更新し、258 行の再計算は rc2 を返します。一方、出力済み summary は `rc: 0, cancel_signal: null` のままです。これは flush 前、すなわち仕様の成功境界前にも成立します。既存 signal test は子の停止中に配送するため、この窓を検査しません。

成果物影響: **取消を受けた実行が JSON 上は成功と記録され、summary と実終了コードが不一致になります。**
推奨: 成功境界と summary の確定を一貫した状態遷移として設計し、出力中の取消についても契約を確定・検証すること。出力失敗時の rc2 という明示例外とは区別が必要です。

**B-02 — 種別: テスト後始末、推奨: nit**
場所: [T:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2665-cleanup-removal-pgroup/orchestrator/tests/test_cleanup_remove_dirs.py:200)。

chmod 復旧はありますが、`_launch()` が `try` の外です。起動が例外で失敗すると `parent.chmod(0o700)` に到達しません。

成果物影響: **起動失敗時に一時 directory の権限が戻らず、fixture 清掃の二次障害を招きます。**
推奨: chmod 後から復旧用 `try/finally` に含めること。

**B-03 — 種別: テスト網羅性、推奨: nit**
場所: [T:280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2665-cleanup-removal-pgroup/orchestrator/tests/test_cleanup_remove_dirs.py:280)。

summary test は空集合、件数不足、重複、unknown、interrupted、取消、failed、fault を検査しています。一方、件数超過、未定義 status、failed と interrupted/unknown の混在による rc2 優先は直接検査していません。`_read_results()` の rc oracle に本体の `summarize()` を再利用しているため、独立した負例に追加価値があります。現状の実装判定自体は正しいです。

成果物影響: **集約の優先順位や完全性条件に対する一部の退行を見逃す余地があります。**
推奨: 上記境界例を直呼び test に追加すること。

## pin 閉包の照合

| 項目 | 結果 |
|---|---|
| command 実 bytes / SHA | **一致**：6201 bytes、`a6380f90dcaf8e5e5ac21cc9af0619e000697816257f3e3e8a8844595dad1f26` |
| whole-file pin 2 箇所 | **一致**：AST から定数値を取得して実 SHA と照合 |
| synthetic 本文 | **byte 一致**：AST から文字列を取得して実本文と照合 |
| 予算 test | **一致**：6201 を 2 箇所、超過 fixture 6205、上限 6204/110 不変 |
| branch rescue ledger の §1 edge | **静的に保存**：§1 全文が byte 不変。consumer は `test_branch_rescue_ledger.py:344` |
| plain runner coverage | **静的に適合**：T:295–296 に参照元と同形の harness、allowlist 変更なし |
| その他登録簿 | tracked 差分は指定 3 file のみ、新規は指定 2 file。registry・除外表の変更なし |
| focus1 | **36 passed、rc0**。skip なし。ただしログ自身が受入全走ではないと明記 |
| focus2 | **1169 passed、3 skipped、rc0**。3 件はログに列挙された growth-hold 対象。全件緑ではない |
| 個別 consumer/meta node の実走照合 | focus2 は省略付き集約ログで、全 nodeid・選択引数は非掲載。branch rescue、plain runner、collection、login headroom、qdel、real-repo serialization の**個別通過まではこのログだけでは確証不可**。receipt publish node は warning 欄に実走記載あり |
| author「36 nodeid」 | **一致**：静的な parameter 展開数と focus1 の 36 passed が一致 |
| author「変更 file 5」 | **一致**：git status は tracked 3＋新規 2。現在の tracked diff は提出 patch と完全一致 |
| author「pytest 未起動」 | **矛盾なし**：author 自身の試行結果の報告。後続の親実測では起動・通過しているため、現在の未実走状態を表す記述としては更新が必要 |
| overlay 未変更 | **byte 一致**。real prune 禁止は維持 |

## 総括

**NO-GO — must-fix 1 件、nit 2 件。**
S3 の exact 文案・pin・予算・削除述語の保存は確認できました。
S1 の summary 確定後の取消により、JSON と終了 rc が不一致になる点を修正してください。
親の焦点走は 36 passed および 1169 passed / 3 skipped。受入全走・全個別 node の通過証明とは扱いません。
本レビューは静的検査のみで、ファイル変更・pytest 起動は行っていません。
