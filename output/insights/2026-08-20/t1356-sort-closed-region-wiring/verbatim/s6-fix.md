## 総括

fix 完了。変更は [auditor.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/.claude/agents/auditor.md:67) と [review_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1356-sort-closed-region-wiring/orchestrator/codex_roles/review_ledger.py:17) のみです。docs・テスト・adapter・commit は変更していません。

修正後の該当箇所全文:

```text
17. **新しい型/関数の追加** — comparator に新しい型または関数を追加する契約違反。機械 gate が検査しないカテゴリ（詳細な分類は `.claude/agents/coder-v4-autonomous-sort.md` の「機械執行の範囲」表を参照）。
18. **非決定ビルトイン** — comparator で非決定ビルトインを使う契約違反。機械 gate の検査が部分的にとどまるカテゴリ（詳細な分類は `.claude/agents/coder-v4-autonomous-sort.md` の「機械執行の範囲」表を参照）。
19. **副作用のある呼び出し** — comparator から副作用のある呼び出しを行う契約違反。機械 gate の検査が部分的にとどまるカテゴリ（詳細な分類は `.claude/agents/coder-v4-autonomous-sort.md` の「機械執行の範囲」表を参照）。
20. **ループ** — comparator にループを置く契約違反。機械 gate の検査が部分的にとどまるカテゴリ（詳細な分類は `.claude/agents/coder-v4-autonomous-sort.md` の「機械執行の範囲」表を参照）。
21. **例外送出** — comparator から例外を送出する契約違反。機械 gate の検査が部分的にとどまるカテゴリ（詳細な分類は `.claude/agents/coder-v4-autonomous-sort.md` の「機械執行の範囲」表を参照）。

14. **sort closed-region の禁止5項目 (型17〜21):** `working_diff` 内の sort(...) 実装を行単位で確認し、新しい型/関数の追加、非決定ビルトイン、副作用のある呼び出し、ループ、例外送出をそれぞれ確認する。該当時は型17〜21の該当番号として場所・正しさへの影響を報告し、`violations[].verifier_blind_spot` に verifier がなぜ見逃すかを書いて報告する（詳細な分類は `.claude/agents/coder-v4-autonomous-sort.md` の「機械執行の範囲」表、または型17〜21）。
```

diff 相当:

```diff
- 型17〜21に file:line、識別子、具体的構文、corpus 境界、見逃し機序を記載
+ 違反名と機械 gate の検査粒度（なし／部分的）および既存表への参照だけに限定

- checklist14 が「具体的な機序」を role prompt 内で要求
+ violations[].verifier_blind_spot への事後報告として要求し、既存表への後方参照を追加
```

D48/D511 の自己点検は合格です。具体的な識別子・コード形状・file:line 機序・corpus 発火条件は型17〜21から削除し、「非検査は許可ではない」も前後2箇所に維持しました。型20の「字句形だけ」という不正確な説明も削除済みです。

`sha256sum`:

```text
e33c65d446bedb5bc1d372f8bcdd1b59968a0a3093ff23f300cb0af0dddebc3e
```

`get_role_spec('auditor')` は例外なしで成功、`git diff --check` も成功しています。