## real 所見

1. **自動 consumer は `rc=0 + known-violations=7` を pass と扱い、唯一の抑止情報を捨てる（既知 T-621、T-618 scope 外）。**

   - **所見:** 予定どおり新規 0 / 既知 7 になると、checker 自体は注記を stdout に出して rc=0 を返す。しかし自動 dev-wave 層は stdout/stderr を破棄し、rc=0 だけで `pass` にする。`PR-A02` の「緑と読まない」は機械化されていない。
   - **根拠:** checker は既知行を出した後 rc=0 を返す [check_ai_provenance.py:2105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:2105)。task-run は `exit_status` のみ、`counts=None` を記録する [task_run_check.py:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/task_run_check.py:43)。自動 checker は両 stream を `DEVNULL` にし、rc=0 を `_pass` に変換する [checker.py:328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/dev_waves/checker.py:328)。規範との衝突は [audit.md:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/docs/provenance/audit.md:22)、既知タスクは [worklog.md:939](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/docs/worklog.md:939)。
   - **具体入力:** 今回の entry を追加し、他の新規違反がない tip を自動 provenance check に渡す。checker は `known-violations=7` / rc=0、自動 receipt は単なる pass となり、7 SHA・注記を復元できない。さらに不正 `note` を持つ registry でも、`--message-file` 分岐は registry を読まず、land 側も message preflight しか直接実行しない [dev_wave_land.py:1387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/dev_wave_land.py:1387)。
   - **成果物影響 1 行:** 自動 dev-wave receipt では「既知 7 件を消費した監査」と「既知 0 件の監査」が同じ pass / exit_status=0 になり、例外消費の証跡を失う。
   - **推奨対応:** consumer 改修は T-621 の別 wave に残す。本 wave の land 証拠には、権威ある post-commit full 監査の生 stdout と `known=7 / new=0` を明記し、自動 pass receipt だけを根拠にしない。

2. **既定 “full” 監査には pre-policy branch merge の実在 blind spot がある（既知 T-619、T-618 scope 外）。**

   - **所見:** `--ancestry-path` のため、policy 導入前から分岐した branch 上の違反 commitを後で merge すると、その commit は `HEAD` から到達可能でも既定監査から落ちる。
   - **根拠:** 既定範囲は `rev-list --ancestry-path policy..HEAD` [check_ai_provenance.py:820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:820)。同じ欠陥と成果物影響は [worklog.md:928](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/docs/worklog.md:928) に T-619 として記録済み。
   - **具体入力:** `50c1ef4e…` より前から分岐した lineage に `AI-Agent` 欠落 commit を置き、正常な merge commit で現在 lineage へ取り込む。素の `policy..HEAD` には入るが `--ancestry-path` からは落ち、他に新規がなければ rc=0 / known=7 になり得る。
   - **成果物影響 1 行:** 到達可能な新規 provenance 違反があるのに、既定 gate の受理結果が rc=0 へ広がる。
   - **推奨対応:** 範囲式変更は brief が明示的に scope 外としているため混ぜない。最終 tip で plain range と ancestry-path の集合差を再確認し、T-619 を独立して閉じる。

## refuted

1. **注記の一次資料と payload**

   指定コマンドの末尾は次の形だった。

   ```text
   AI-Agent: product=claude; model=claude-opus-5-1m; reasoning=default; role=manager; scope=t503-disposable-worktree$
   $
   Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>$
   $
   ```

   default `git interpret-trailers --parse` は `Co-Authored-By` だけを返した。したがって空行で `AI-Agent` が最終 trailer block から切り離されたという注記は一次資料と一致する。payload の field 順、各 ident、`role=manager`、scope は [ai-provenance.md:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/docs/ai-provenance.md:19) と production regex [check_ai_provenance.py:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:70) を満たす。裁定前提は崩れない。

2. **`3f2c43d7` に別 finding が隠れる攻撃**

   commit は 1 parent で、変更 path は次の Markdown 3 本だけだった。

   ```text
   docs/spool/failures/2026-08-07-dev-wave-t503-disposable-worktree-3.md
   docs/spool/worklog/2026-08-07-dev-wave-t503-disposable-worktree-1.md
   output/insights/2026-08-07_t503-disposable-worktree/README.md
   ```

   D95 epoch `8c6d3f3b…` は祖先だが、classifier はこれらを実装面にしない [check_ai_provenance.py:671](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:671)。baseline も全体で target の `missing-ai-agent` 1 件しか出していない [baseline-default-audit.txt:2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t618-provenance-known-ledger/s3/baseline-default-audit.txt:2)。`missing-codex-author` は立たない。

3. **full SHA / finding 種別 / 1件消費**

   Registry は lower-case 40 hex と種別閉集合を検査する [check_ai_provenance.py:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:196)。照合は `registry.get(audit.commit)` と種別完全一致で、最初の一致だけを消費し、2件目・別種は findings に残す [check_ai_provenance.py:993](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:993)。共通8桁 prefix、別種併存、同種2件の各境界 assert も残る [test_check_ai_provenance.py:1393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1393)、[同:1532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1532)、[同:1569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1569)。prefix・巻き添え消去は成立しなかった。

4. **correction / waiver / merge / message-file 合成**

   Correction が先に欠落を相殺した場合は台帳側が期待 finding 0 と見て stale、waiver が `missing-codex-author` を相殺した場合も同じである [test_check_ai_provenance.py:2189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:2189)、[同:2862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:2862)。merge でも照合キーは commit の full SHA のままで、今回の target 自体は非 merge。`--message-file` が台帳を読まないのは D221 の明示契約 [decisions.md:10435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/docs/decisions.md:10435) どおり。ただし end-to-end consumer 不足は real 所見 1 のとおり。

5. **`note` 検査の rc=2 経路**

   計画どおり `_known_violation_registry()` で型・改行を `RuntimeError` にすれば、その呼出しは `_audit_history()` 内 [check_ai_provenance.py:1040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:1040)、さらに `main()` の `try` 内で、例外は rc=2 に畳まれる [同:2010](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:2010)。予定する `None` と `first\nsecond` について、この経路に穴はない。

6. **rc=1 テストの反転による検出力低下**

   反転 node 単体から raw stderr の assert は消える。しかし計画は、実履歴との照合へ target を追加し [plan.md:58](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t618-provenance-known-ledger/s3/plan.md:58)、空 registry 時に七件すべてと `missing-ai-agent=6` を直接数える [plan.md:59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t618-provenance-known-ledger/s3/plan.md:59)。後者は production 台帳を oracle にせず raw finding を復元するため、代替 pin は成立している。

7. **baseline の読み落としと現在 tip の算術**

   生出力には target finding 1 行、既知6行、`known-violations=6` があり、別の violation 行はない。親の要約から落ちているのは ratified waiver 8件と資源診断で、違反の数え落としではない。現在の `HEAD=bb824d8b…` では policy を含む plain range と ancestry-path がともに1702件だったため、同じ tip・同じ検査意味論なら「target を既知へ移すと既知7 / 新規0 / rc=0」という算術は成立する。

   ただしこれは snapshot 期待値であり、次では成立しない。

   - target を含まない明示 range
   - 新規違反を含む明示 range
   - 並行 wave が違反 commit を land した後の `HEAD`
   - target の期待 finding が消えて stale rc=2 になる checker 変更
   - target を祖先に持たない別 tip
   - real 所見 2 の pre-policy branch merge

   また land commit 分だけ監査件数は1702より増える。最終 tip での再実測が必要であり、固定件数テストにしていない計画は妥当。

## speculative / nit

1. **`note` は構造化されていない表示 field。** 改行は拒否されるが、将来 `sha=`、`finding=`、ANSI制御文字などを含めれば人や素朴な外部 parserを惑わせ得る。repo 内に record parser はなく、実際の注記にも該当文字列はなく、照合・rc は formatter より前に確定するため、これは受理集合ではなく表示完全性の問題。現時点で追加 hardening は不要。

2. **将来の別 entry への機構上の注意。** 実装面 commit で parsed `AI-Agent` が完全欠落すると、`validate_implementation_author()` は `not values` で戻り、別の `missing-codex-author` を生成しない [check_ai_provenance.py:696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:696)。その種の commit を将来 `missing-ai-agent` 台帳へ入れると、意味上は二つの義務を一つの finding で跨ぎ得る。今回の SHA は docs-only なので発火せず、T-618 の real 所見にはしない。

## 総括

最も危ない点は T-621、すなわち `known=7` の唯一の抑止情報を自動層が捨てて rc=0 を pass と読むこと。  
core 台帳照合については、この SHA のこの `missing-ai-agent` 1件を越えて吸収する経路は見つからなかった。  
注記は一次資料と一致し、payload も現行必須形式を満たし、target に D95 finding は立たない。  
T-619 の既定範囲 blind spot は実在するが既存・scope 外で、現在 tip では plain/ancestry-path は同一だった。  
pytest と checker 自体は実行しておらず、結論は静的検査と read-only の `git` 出力だけによる。