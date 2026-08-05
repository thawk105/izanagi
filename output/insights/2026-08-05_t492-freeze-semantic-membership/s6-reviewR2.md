結論は **NO-GO**。指定された差分・`plan-v2.md`・`impl-out.md` は全て読んだ。以下は静的検査であり、pytest は実行していない。

## 重大所見

### 1. M1・M2 の期待 node は別の `ValueError` で赤くなる — real / blocker

テストは `_campaign_file` に repo 外の相対パスを返している。

- [test_s1_known_axes_freeze.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s1_known_axes_freeze.py:53): `Path("remeasure"), Path("main")`
- [s1_known_axes_freeze.py:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:31): `ROOT` は絶対パス
- [s1_known_axes_freeze.py:521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:521)、[同:533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:533): helper 通過後に `re_path.relative_to(ROOT)` を評価

M1/M2 で対象 helper 呼出しを削除すると、非正準述語が受理されたことを観測する前に `Path.relative_to()` が `ValueError` を投げる。`pytest.raises(M.FreezeError)` の外へ漏れるため node は赤くなるが、これは偽の kill である。M5 の generator 側期待 node も同じ。

公開 `generate()` テストにも同じ相対パスがある（[test_s1_known_axes_freeze.py:176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s1_known_axes_freeze.py:176)）。さらに side effect は2件しかなく、相対パスだけ直しても guard 消失後の後続 `_sort_entry()` が3回目の `_campaign_file` を呼んで `StopIteration` になり得る。したがって [同:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s1_known_axes_freeze.py:189) の「未書込み」も semantic guard 単独の証拠ではない。

放置すると、実 production では coordinated な非正準述語を known-axes 凍結台帳へ書ける変異を、テスト報告だけは killed と認定する。そこから measurement cell・材料レポートへ誤った gate predicate が伝播し、certified 選択が別の実装を評価する可能性がある。

修正は、private node では `M.ROOT / "remeasure"` 等を返して戻り値まで到達させること。公開 producer node では後続 `_backoff_entry`／`_sort_entry` 等も「guard がなければ正常に書込み完了する」状態へ閉じる必要がある。

### 2. 公開 `verify_document()` node の M3/M5 kill は受理集合の kill ではない — real / blocker

テストは現行凍結 doc を読み（[test_s1_known_axes_freeze.py:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s1_known_axes_freeze.py:193)）、`build_document` を未到達 sentinel にする（[同:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s1_known_axes_freeze.py:196)）。

M3 で schema 走査を消した場合の拒否理由は次の順に過剰決定されている。

- generator hash: [s1_known_axes_freeze.py:746](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:746)
- source hash: [同:753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:753)
- pairing・git pin: [同:768](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:768)
- 再構成等値: [同:781](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:781)

実際、凍結台帳の generator pin は `1d4d45…`（[known_axes_freeze.json:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/output/s1-freeze/known_axes_freeze.json:5)）だが、現作業ツリー bytes の静的算出値は `a7505a…` である。M3 後はまず generator mismatch へ移る。これを中立化しても、sentinel の `AssertionError` または最終再構成不一致で node は赤いままである。

つまり [test_s1_known_axes_freeze.py:201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s1_known_axes_freeze.py:201) の診断完全一致は過剰決定を解消せず、「拒否理由・拒否順が変わった」ことを kill に見せている。legacy `verify_document()` の受理集合自体は M3 だけでは広がらない。材料レポートや凍結台帳の値は変わらず、mutation proof chain が誤った node を kill 根拠として参照する。

早期拒否順のテストとして残すことは可能だが、DW-M01 の acceptance kill には数えるべきでない。

### 3. 本当に稼働中の公開 gate への semantic wiring 負例がない — real / blocker

計画自身が、active receipt 経路は `verify_document()` ではなく static adapter だと確定している（`plan-v2.md:13-16`）。

実経路は以下である。

- [s8b_oracle_driver.py:210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s8b_oracle_driver.py:210): `static_gate_adapter`
- [t080_freeze_migration.py:2084](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/t080_freeze_migration.py:2084): `_verify_known_schema`
- [同:1812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/t080_freeze_migration.py:1812): `_validate_schema`

新しい wiring test は legacy `verify_document()` だけを呼ぶ。G7 も `issue_receipt=False`（[test_s8b_oracle_driver.py:2694](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s8b_oracle_driver.py:2694)）なので active adapter の semantic 負例ではない。既存の `_verify_known_schema` 負例（[同:994](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s8b_oracle_driver.py:994)）も private 関数単体である。

したがって static adapter から `known_axes.schema` check を外す変異は、新規7本をすべて緑のままにできる。将来の receipt/refreeze で非正準述語と hash・再構成値が同時更新された場合、active gate の受理集合が広がり、凍結台帳の非正準 predicate が材料レポートと certified 選択へ到達する。

## M1〜M6 判定

| 変異 | 判定 | 理由 |
|---|---|---|
| M1 | **偽 kill** | system node は helper 削除後に `relative_to(ROOT)` の `ValueError` で赤い。 |
| M2 | **偽 kill** | ident node も同じ。 |
| M3 | **部分的に有効** | schema 単体2本（[test:140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s1_known_axes_freeze.py:140)、[同:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s1_known_axes_freeze.py:152)）は真の kill。公開 wiring は偽 kill。 |
| M4 | **有効** | ident_all 単体 node は走査縮小後に例外が消える。他の hash・再構成を呼ばない。 |
| M5 | **部分的に有効** | schema 単体2本は真の kill。generator node は相対パス、wiring は hash/rebuild による偽 kill。 |
| M6 | **条件付き有効** | 新正例 [test:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s1_known_axes_freeze.py:97) は baseline 緑を前提に真の kill。「既存 consumer 群」は nodeid 未列挙かつ hash/schema/rebuild 過剰決定なので数えられない。 |

正確な M1〜M6 について、登録 node が緑に残る false-SURVIVED は見つからなかった。ただし M1/M2 と M5 の一部は、赤くなる理由が無効である。

## 診断文字列依存

追加7本中、負例6本が日本語診断の完全一致に依存している（[test:120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s1_known_axes_freeze.py:120)、136、148、160、187、201）。

- private generator/schema nodeでは、例外型だけで登録変異を殺せるため完全一致は不要。
- 公開2本では、完全一致が別理由の赤を semantic kill に見せている。

文言変更だけなら受理集合・certified 選択・凍結値は変わらず、変わり得るのは材料レポートへ載る refusal 文面だけである。この部分単独は nit だが、mutation kill 判定とは分離すべきである。

## G7・巻き込み・揮発値

G7 弱体化の疑いは **refuted**。

- holdout generator の改竄は維持: [test_s8b_oracle_driver.py:2724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s8b_oracle_driver.py:2724)
- refusal 4件・known source mismatch 1件も維持: [同:2744](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s8b_oracle_driver.py:2744)
- `ROOT` patch は `gate_check()` の範囲だけで、known module のみ: [同:2732](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s8b_oracle_driver.py:2732)

holdout verifier自体は mock されておらず、元の公開 gate 到達意図を保っている。成果物の受理集合・refusal 件数に弱体化はない。

新しい literal な working-tree hash・絶対 path・時刻の焼き込みもない。ただし G7 の known-generator replay は Git の完全履歴に依存する（[同:2700](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s8b_oracle_driver.py:2700)）。shallow clone・履歴 pruning では赤くなるが、既存2 recordも同方式であり、成果物には影響しないため nit。

共有 fixture／conftest／plain-runner／独立 golden との未解決衝突は静的には見つからない。

- 新テストは既存 `_run()` に自動収集され、`tmp_path` も注入される（[test_s1_known_axes_freeze.py:403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s1_known_axes_freeze.py:403)）。
- 新規 node は通常経路で shared ccbench を読まないため real-repo allowlist 追加は不要。
- 独立 golden は既に6 predicate を exact 固定している（[s1_expected_goldens.py:636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/s1_expected_goldens.py:636)、[test_reflux_ir.py:445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_reflux_ir.py:445)）。
- 凍結 JSON bytes は既存 manifest pin と衝突しない（[test_frozen_artifacts.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_frozen_artifacts.py:39)）。

## 純増／重複の仕分け

- 純増: `_trigger_entries()` の configuration 別負例2本、`_validate_schema()` の configuration 別負例2本。ただし generator 2本は mock path 修正が必要。
- 純増の意図はあるが現状無効: 公開 `generate()` の write-before-reject。
- 順序だけ純増: 公開 `verify_document()` の「再構成前に拒否」。受理集合の被覆としては純増していない。
- 部分重複: 現行6値の正例。値そのものは既存 golden/reflux test と重複するが、新 helper の過剰拒否 M6 を `_validate_schema()` 経由で殺す部分は純増。

## 総括

**NO-GO**

- must-fix 1: M1/M2/M5 の mock path を `M.ROOT` 配下に直し、guard 消失時に `_trigger_entries()` が正常 return するところまで到達させる。
- must-fix 2: 公開 `generate()` を、guard が無ければ実際に非正準 doc を書く hermetic 経路にし、別例外・未書込みによる偽 kill を除く。
- must-fix 3: active T-080 `gate_check()` の非正準 predicate 負例を追加し、legacy `verify_document()` の診断順テストを M3/M5 の acceptance kill から外す。