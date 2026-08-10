静的再レビューの結論は **NO-GO** です。Critical 0、Major 3。pytest は実行しておらず、親報告の `128 passed / rc=0` を独立した緑とは主張しません。

## 所見の閉包表

| 採用所見 | 判定 | 根拠 |
|---|---|---|
| A 所見1 / B M-04：実要求数 | **partial** | 現在の実値は `2347 + 1` commits × 3 paths = **7,044**、予算 **75.5784秒**で、動的計算自体は合っています。しかしテストは path 集合を独自に再実装し、synthetic stdin を helper へ渡すだけです（[test_s8c_preregistration_core.py:1025](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1025)、[同:1035](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1035)、[同:1047](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1047)）。production の実 path/request 構築は別実装です（[s8c_preregistration.py:1122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:1122)、[同:1344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:1344)）。両者が同時に食い違っても検出できません。 |
| A 所見2：変異9 | **closed** | stdin が `2 × MAX_BATCH_REQUESTS` へ増幅され（[test_s8c_preregistration_core.py:1070](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1070)）、MAX単位の chunk mutant は成功側の call-count assertion（[同:1087](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1087)）で落ちます。 |
| A 所見3：変異10 | **partial** | `_git_text` と全 subparser は追加されています（[test_s8c_preregistration_core.py:1112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1112)）。現在の parser は root＋`check`＋`prepare-revision` の全てへ到達します（[s8c_preregistration.py:1804](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:1804)）。ただし検査は3語の blacklistにすぎず、`wait_seconds`、`time_limit`、`git_wall_seconds` 等の override、CLI positional の `timeout` は生存します。したがって変異10は一般形では依然生存します。 |
| A 所見4：durable binding の module コメント | **regressed** | コメントは `8.3613e-5` を「48 worker 全走負荷下」と記述しています（[s8c_preregistration.py:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:95)）が、訂正版正本では最大サンプルは worker 0、worker実在時最大は別値です（[MEASUREMENT.md:26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/MEASUREMENT.md:26)）。さらに参照先 `output/insights/2026-08-09_t553-git-budget/`（[s8c_preregistration.py:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:100)）は現在存在せず、durable binding が dangling です。 |

## fix が持ち込んだ欠陥

### Major 1 — F1 は実 workload の oracle になっていない

テストは次を独自に再構成しています。

- worktree の glob で generation paths を列挙
- `SOURCE_PATH`、`EVIDENCE_CONTRACT_PATH` と結合
- `(commit_count + 1) × len(paths)` を要求数と仮定

production は history namespace から最大 generation を決め、連続した generation path を生成して `_batch_oids` へ渡します（[s8c_preregistration.py:1337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:1337)）。production に path が追加・削除されても F1 は同じ synthetic R で通るため、元の「実要求数との不一致」を完全には閉じません。

さらに一回とはいえ、実 repo に対して無制限の `git rev-list --count HEAD` を追加しています（[test_s8c_preregistration_core.py:1026](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1026)）。テスト helper は固定10秒です（[同:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:72)）。production の `--max-count=MAX_COMMITS+1` とも異なるため、履歴増加時にテスト側だけが重くなります。

この nodeid は `REAL_REPO_SERIAL_NODES` に入っておらず（[conftest.py:126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/conftest.py:126)）、`real-repo` xdist group も付与されません（[同:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/conftest.py:240)）。既存 invariant の候補実 repo テストが専用 group を使う作法（[test_s8c_preregistration_invariant.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_invariant.py:29)）とも不一致です。

通常の commit 増減には追随しますが、`MAX_COMMITS` または `MAX_BATCH_REQUESTS` を超えた場合、production は拒否する一方、このテストは clamp 後の予算一致として通り得ます。

### Major 2 — F3 は変異10を完全には殺さない

subparser traversal 自体は正しいです。Python の list iterator は追加された parser も辿るため、現行の2 subparserと将来の nested subparserまで到達します。

欠陥は検査対象です。`action.option_strings` しか見ないため（[test_s8c_preregistration_core.py:1127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1127)）、positional argument の `dest` は検査されません。また3語の部分一致なので、別名 override は通ります。

逆に `--budget-report` や `deadline_reason` のような、timeout override ではない正当な名前も拒否します。完全な baseline signature・option集合との一致ではなく、過少検出と過剰拘束を同時に持っています。

### Major 3 — F4 コメントが訂正済み測定と矛盾する

大きい `0.588973` を保守側として採る裁定自体には異議ありません。しかし、そのサンプルを「48 worker 負荷下」と表現するのは訂正版 `MEASUREMENT.md` と矛盾します。数値選択と sample provenance は分けて記述する必要があります。

## snapshot 全差分監査

既存期待値の削除・反転・緩和・skip・xfail はありません。

F2 では snapshot の以下をすべて保持しています。

- helper への元 stdin 伝播
- 成功時の timeout 値伝播
- 成功時 subprocess 1回
- `TimeoutExpired → git-timeout`
- timeout 時 subprocess 1回

snapshot の assertion 群（[snapshot-s5-test.py:1043](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/snapshot-s5-test.py:1043)）は現行でも維持されています（[test_s8c_preregistration_core.py:1070](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1070)）。

production は snapshot からコメントだけが変わり、制御フロー・定数・signature・reason code・呼出回数に変更はありません。fix による fail-open はありません。

## 変異12件の静的再確認

| # | 判定 | 指定 nodeid への帰結 |
|---:|---|---|
| 1 | killed | RATE literal pin が赤 |
| 2 | killed | BASE `15.0` pin が赤 |
| 3 | killed | CAP `300.0` と非従属性の両 assertion が赤 |
| 4 | killed | CAP `min` 削除で amplified input が445秒となり赤 |
| 5 | killed（構造 pin） | CAPを1000へ隔離した検査で875秒対445秒となり赤 |
| 6 | killed | `not-byte-length` が1要求対1000要求の差を検出 |
| 7 | killed | `no-trailing-lf` が15.0086秒対15秒の差を検出 |
| 8 | killed | helper callまたは123.25秒の伝播 assertion が赤 |
| 9 | killed | 100,000行を50,000行ずつ分割すると成功側が2 callsとなる |
| 10 | **survived** | `wait_seconds` 等の別名、または positional CLI override は blacklist を通る |
| 11 | killed | `git-timeout` reason assertion が赤 |
| 12 | killed | input-limitより先に budget helperが発火して赤 |

変異5を「構造 sensitivity pin であり、現 production の semantic kill ではない」とする段6レンズAの分類は妥当です。現定数では request clamp を外しても絶対CAPが先に効き、production の戻り値は変わりません。

## scope 外所見

A 所見5の CR path alias には手が入っていません。差分は指定2ファイルだけで、production の `read_blob_at` は従来どおり path をLF終端して渡し（[s8c_preregistration.py:958](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:958)）、`_safe_path` も制御文字拒否を追加していません（[s8c_preregistration_evidence.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration_evidence.py:183)）。受理集合を狭める変更はありません。

## 総括

**NO-GO。Critical 0、Major 3。**  
F2／変異9は closed。  
F1は現値7,044を算出するが、production path構成の再実装なので partial。  
F1は固定10秒の実repo全履歴gitを追加し、real-repo xdist groupにも未登録。  
F3のparser traversalは完全だが、語片blacklistのため変異10が別名・positionalで生存する。  
F4コメントは訂正済み測定と矛盾し、参照先directoryも現在存在しない。  
既存期待値の緩和・削除・skip、およびproduction fail-openはない。  
CR path aliasには手が入っていない。pytestは未実走。