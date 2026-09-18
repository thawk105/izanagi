実装済み・未実走です。

- [テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2686-recovery-codex/orchestrator/tests/test_check_branch_landed.py:2382)の観測・注入selectorを7か所修正しました。根因は`diff --name-only`の混入です。差分は追加7／削除7行。既存期待値・全assert不変をASTで確認しました。
- productionは変更なし。カウンタ、受理集合、期限・上限・判定式、limit+1正例を維持しています。
- [比較driver](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2686-recovery-codex/build/t2686_ab_compare.py)は117行。`sys.modules`登録、repo rootの`sys.path`指定、固定target／900秒の旧・新・旧・新、全走main照合、指定fieldだけ除いたcanonical byte比較、旧＞新process数と指定環境情報の保存を実装しました。開始・終了時の負荷観測では途中の同居負荷を除外できない限界も記録します。ignore対象を確認済みです。

m10は[productionの初回parseから再走査条件まで](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2686-recovery-codex/tools/check_branch_landed.py:871)の7行を、次へ一括置換する候補です。置換元の出現は1か所、置換後の構文解析も確認済みです。

```python
            raw = self._log([*command, f"--max-count={bound}", *tail]).stdout
            entries = _parse_history_candidate_stream(raw, len(self.main_oid))
            n = raw.count(b"\0\0") + bool(raw)
            if n > bound:
                raise AssessmentError("history-candidate-parse-error", "history exceeded commit bound")
            derived = self._derive(entries, paths)
            if n == bound and any(len(rows) < self.limit + 1 for rows in derived.values()):
```

正常parse後のentry境界を数えるため、候補列のdistinct化を保ったまま、上限・再走査判定だけが親別entry数になります。期待killerは`test_history_candidates_bounded_walk[merge_entries_count_once]`。変異は適用・実走していません。

静的確認は3ファイルの構文解析と`git diff --check`が成功。pytest・性能測定の実走は0件で、緑の主張はありません。共有fixture・テスト名は変更なし。所有外consumerは`tools/check_branch_rescue.py`とそのテストで、関連制約テストへの直接の名前参照は検索で見つかりませんでした。

残余は親の焦点走・変異spec/harnessと実走・計算ノード対測定・受入です。docs編集、add／commit、他agent起動は行っていません。