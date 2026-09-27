## 所見

1. **種別: 削りすぎ／重大度: must-fix**
   根拠: [tools/mutation_harness.py:2400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:2400)、[同:2405](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:2405)、[同:2462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:2462)。runner 後の HEAD・bytes 検査が orphan 判定より先にある。dispatch の結果が `job_may_remain` または timeout を示し、同時にこの検査が失敗すると、hold を確定する前に `finally` が復元へ進み得る。**成果物影響:** 生存し得る job が読む M を H に戻し、変異結果の値と受理集合を汚す。推奨: runner 結果を受けたら既存の `_dispatch_orphan_stop` を先に実行し、hold の保全経路でも HEAD・bytes を検査する。

2. **種別: 不足／重大度: should**
   根拠: [orchestrator/tests/test_mutation_harness.py:3398](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/orchestrator/tests/test_mutation_harness.py:3398)、[同:3470](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/orchestrator/tests/test_mutation_harness.py:3470)、[tools/mutation_harness.py:2400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:2400)。新テストの runner は HEAD・bytes を正常に保つか、HEAD を attached にする。detached のまま HEAD または touched bytes を変える負例がなく、裁定が要求した runner 直後の照合を直接検出しない。**成果物影響:** runner が M 以外を実行しても KILLED／SURVIVED を M の結果として台帳に記録し得る。推奨: 既存 T1 または T4 に、runner が HEAD もしくは bytes を変える一例を加え、記録前の拒否を確認する。

3. **種別: 既存策あり／重大度: should**
   根拠: [s5-author-a.md の M5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1418-closure-mutation/out/s5-author-a.md)、[tools/mutation_harness.py:2402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:2402)、[orchestrator/tests/test_mutation_harness.py:3496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/orchestrator/tests/test_mutation_harness.py:3496)。M5 が復元直前の detached 検査だけを外しても、T5 の attached 化は runner 直後の既存検査で先に拒否される。T5 は M5 の新規検出力を証明しない。復元直前の検査自体は、runner 後から復元までの ref 移動を防ぐため残すべき。推奨: M5 の期待 node を、復元直前だけで attached になる単一理由の試験へ再照準する。

4. **種別: 既存策あり／重大度: nit**
   根拠: [tools/mutation_harness.py:2578](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:2578)、[同:2881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:2881)、[同:3030](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:3030)、[同:3042](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:3042)。policy の選択式と commit 復旧文言がそれぞれ複数箇所に重複する。新しい台帳項目や gate は不要で、既存の完全一致照合と orphan 処理で足りる。推奨: policy の組と復旧文言を各一箇所へ局所化する。これは規模削減であり、機能削除の必須条件ではない。

5. **種別: 削れる／重大度: nit**
   根拠: [orchestrator/tests/test_mutation_harness.py:3599](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/orchestrator/tests/test_mutation_harness.py:3599)。T9 の 8 組は同じ起動前 author 判定を反復する。fresh／resume／plan-only と両モードを確認する裁定には沿うが、全直積の成果物影響は一行で区別できない。推奨: 代表組に縮め、各軸が少なくとも一度現れるようにする。T4 の正常・非 0・timeout、および T8 の両方向は結果や照合方向が異なるので残す。

6. **種別: 削りすぎ／重大度: should**
   根拠: [tools/mutation_harness.py:3296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:3296)、[同:748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:748)、[同:763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:763)。起動前の残留 M 拒否、注入後の親・changed paths・blob・clean・detached 照合、復元前の detached 照合と `_assert_head` は削れない。前者を削ると clean な M を H として起動でき、注入後の照合を削ると別の木の失敗を M の KILLED と数え得る。復元側を削ると branch ref 移動または復元漏れに至る。推奨: `_assert_head`、`_assert_clean_tracked`、`_verify_originals`、`_assert_only_expected_dirt` を引き続き利用し、これらの境界を保つ。

## 変異 anchor 判定

M1〜M4、M6〜M8 は、提示された置換と期待 test の対応に静的な重複検出は見つからない。**M5 は上記のとおり既存の runner 直後検査でも落ちる性質で、単一理由の新規検出力に数えられない。** M1 は注入後の detached 検査でも拒否されるが、その時点では attached branch の ref が既に動くため、起動前拒否を検出する T2 の branch ref 確認には意味がある。変異 probe は実走しておらず、その他の anchor の単一理由性は未確定。

## 総括

**NO-GO。** orphan 判定より先に追加された runner 後照合の順序を修正する必要がある。M5 の再照準と runner 後照合の負例を追加すれば、裁定の正しさ境界をより直接に検証できる。裁定を超える新たな設定・台帳・一般化は差分に見当たらない。これは静的レビューであり、テストの緑は主張しない。