## must-fix

なし。静的レビューでは、成果物の値・受理集合・参照を裁定外に変える実装差分は確認できなかった。

## 裁定逐語との一致表

| 項目 | 判定 | 実際の値・根拠 |
|---|---|---|
| 注記の連結後文字列 | 一致 | `python3 -c` 評価で production/test とも `trailer は本文に実在するが、AI-Agent 行と Co-Authored-By 行の間の空行で trailer block 不成立`、`production_exact=True / test_exact=True`。[production](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:183)、[test oracle](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1365) |
| ruling | 一致 | `worklog(293) 2026-08-07 /rulings`。[tools/check_ai_provenance.py:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:182) |
| guard predicate | 一致 | `not isinstance(spec.note, str)`、続いて `spec.note != "" and spec.note.splitlines() != [spec.note]`。[tools/check_ai_provenance.py:236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:236) |
| guard 位置・順序 | 一致 | ruling 検査の直後、`registry[spec.commit] = spec` の直前。型検査→改行検査→登録の順。 |
| `_KNOWN_VIOLATION_RULING` | 一致・未変更 | AST で HEAD と比較し `True`。値は `worklog(284) 2026-08-07 /rulings`。[tools/check_ai_provenance.py:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:147) |
| `_known_spec()` signature | 一致・未変更 | AST で HEAD と比較し `True`。`(commit: str, finding_kind: str = "missing-ai-agent")`。[test_check_ai_provenance.py:266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:266) |
| 既存空-note stdout test | 一致・未変更 | `test_known_violation_stdout_is_public_on_rc0_and_rc1` の関数 AST が HEAD と完全一致。[test_check_ai_provenance.py:1841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1841) |

## 実装子の申告と実物の差

申告の主要部分は実物と一致した。

- `git status --short` は変更された2ファイルだけ、`git diff --cached --quiet` は rc=0。index変更・追加ファイルはない。
- HEAD は `bb824d8b` のままで、reflogにも新規commitはない。
- 受理集合は申告どおり、`3f2c43… / missing-ai-agent` だけが既知集合へ追加された。prefix、wildcard、複数finding消費、stale、correction、waiver、message-file、range式に差分はない。
- `git diff --check` rc=0、AST parse成功、`check_codex_agents.py` rc=0、`check_docs.py` は `check_docs: 違反なし`。追加行に88文字超は0行だった。
- 「期待して赤くなるものなし」は静的には矛盾しない。ただし実走結果ではない。[s5/out.md:21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t618-provenance-known-ledger/s5/out.md:21) のとおり、pytest開始前にrc=16で止まり、passed=0/failed=0である。

差は1点だけある。

- `[nit]` 「所有外caller」の列挙は一層不足している。実際の自動wave経路は [tools/dev_waves/cli.py:188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/dev_waves/cli.py:188) が provenance `CheckSpec` を構築し、[checker.py:328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/dev_waves/checker.py:328) がその stdout/stderr を `DEVNULL` へ捨てる。申告は後者だけを挙げている。T-621の裁定自体は変わらない。

## 未 scope の層と陳腐化

- [D221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/docs/decisions.md:10420) は現在も entry を3要素 `(SHA, kind, ruling)` と定義しており、4フィールドの実装と不一致。裁定済みどおり、段7のaddendumで直す親所有の差である。
- [PR-A02](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/docs/provenance/audit.md:22) は exact record schemaを固定せず、既知行と `known-violations=N`、rc/staleだけを規定する。条件付き `note=` suffixとの矛盾はない。
- [docs/ai-provenance.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/docs/ai-provenance.md:80) に台帳schemaや既知行の固定形式はなく、追加の本文不整合は見つからなかった。
- `tools/`・`orchestrator/`・`hooks/`・`.claude/` の検索結果は次のとおり。いずれも producerと当該testの2ファイルだけで、外部parserは0件だった。

| grep語 | hit行 / files |
|---|---:|
| `known-violation` | 19 / 2 |
| `known-violations=` | 6 / 2 |
| `KNOWN_PROVENANCE_VIOLATIONS` | 22 / 2 |

件数焼き込み検索の結果:

- `既知違反 6 件`: 1 hit — [docs/worklog.md:478](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/docs/worklog.md:478)。
- `既知 6`: 8 hit。この台帳に関係するのは [worklog:495](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/docs/worklog.md:495)、[509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/docs/worklog.md:509)、[923](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/docs/worklog.md:923) の3行。他5行は別のallowlist/test-node記録。
- `6 SHA`: 8 hit — worklogの478、480、485、486、538、542行と、archiveの `worklog-phase3-0807-286.md:406`、`worklog-phase3-0807-283-284.md:848`。
- `既知6件`、`6件ちょうど`、`6 件ちょうど`、`known-violations=6`: 0 hit。

これらは過去時点のworklog/archiveであり、書き換え対象ではない。[T-614 insight](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/output/insights/2026-08-07_t614-known-violation-ledger/README.md:115) の `known=6/new=1` 実測も歴史記録として残し、新しいT-618記録でsupersedeすべきである。

段7では裁定済み3点に加え、次も明記すると後任の誤読を防げる。

1. 非空noteだけが stdout の ` note=…` suffixになり、空noteの既存行は逐語不変であること。
2. worklog293の説明文ではなく、段4が固定したbacktickなし文字列が実装literalの正本であること。
3. 現時点ではpytest・変異・positive control・post-commit full監査が未実走であり、最終記録には親が後で実測した値だけを書くこと。
4. T-619の`--ancestry-path`盲点も不変。既存taskへの参照で足り、新規taskの重複起票は不要。

## real (must-fix ではない)

1. **段7の正本更新は未了。** D221、T-614 supersede、T-621未解決の記録がない現状はland-readyではない。ただし親所有として裁定済みで、今回の実装子へのcode fixではない。

2. **動的な受入証拠はまだ0件。** [s5/out.md:21–25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t618-provenance-known-ledger/s5/out.md:21) はpytest開始前のinfra rc=16を明記している。静的レビューは実装整合を支持するが、テストの緑・赤は主張できない。

3. **T-621は実在したまま。** 自動dev-wave層はrcだけでpassを決め、公開noteと既知件数を保存しない。今回のstdout変更で悪化はしていないが、抑止情報が自動receiptへ届かない状態も改善していない。

## refuted

6テストの「飾りではないか」という攻撃は、静的にはすべてrefuted。

| テスト | 静的な赤化経路 |
|---|---|
| `test_known_violation_ledger_is_exactly_seven_literal_entries` | 7件目削除、順序・SHA・kind・ruling・note driftのいずれでもexact tuple/length/setが不一致。期待値は独立literal。 |
| `test_known_violation_ledger_matches_real_commit_findings` | 7件目削除ならraw findingが残り、checker退行ならstale例外になるため、`findings == [] / known==7`を満たせない。 |
| `test_broken_registry_note_is_rc2` | guard削除時は5 caseがrc=0へ到達する。型guardだけ削除した場合も`AttributeError`が外へ出てtestは失敗可能。診断式は実例5件すべてproduction例外と一致した。 |
| `test_known_violation_nonempty_note_is_public_on_rc1` | linear履歴の `{base}..{new}` はbaseを除きknown/newの2 commitだけ。rc=1側だけ旧formatterへ戻すとexact stdoutのnoteが欠ける。 |
| `test_empty_registry_restores_all_seven_real_findings` | production entry削除は前半のknown=7を壊し、registry外の特別抑止は後半のraw=7を壊す。二段とも観測対象がある。 |
| `test_ledgered_3f2c43d7580b_is_known_and_rc0` | 実commitのsingleton rangeを使い、rc・3行stdout・stderr空をexact pin。note/findingはproduction定数を参照せず独立literal。 |

さらに次の攻撃もrefuted。

- PR-A02と新stdout形式の矛盾。
- repository内の固定field数parser取り残し。
- guardの空文字拒否、順序違い、rc=2経路外配置。
- hiddenなstage/index/所有外変更。
- 新規main呼出しの`site=`漏れ。AST走査は67 call、unpinnedは0。
- whitespace・追加行長・docs lint違反。

## nit

1. 実装子報告のcaller列挙に `tools/dev_waves/cli.py` を加え、`cli.py → CheckSpec → checker.py(DEVNULL) → task_run_check.py` と書くと、T-621の実在層が正確になる。

## 総括

静的判定ではcode must-fixはなく、裁定逐語・guard・受理集合・6テストの検出経路は一致した。  
最も危ない点は、**pytest・変異・positive control・権威full監査が一度も開始されていないこと**である。  
D221の4フィールドaddendumとT-614 supersede、T-621の射程限定は段7で必須。  
T-619と自動waveのstdout廃棄は未解決のままだが、今回の差分が新たに作った退行ではない。  
したがって現状は「実装静的レビュー通過候補」であって、land可やテスト緑とは判定しない。