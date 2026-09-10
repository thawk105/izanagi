単独段 dispatch: stage=review; sandbox=read-only; parent=/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s4-ruling.md

## 必読事項の射影

次の絶対パスだけを読む。読めなければ即停止し、その旨だけを出力する。

- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s4-ruling.md` — 段 4 裁定 (必須 assertion と変異事前登録の正本)
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s5-author2.md` — 実装子の完了報告 (自己申告。裏を取る対象)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_cli_entrypoints.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_core.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration_evidence.py`

repository の root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason` である。親側の `/work/1/SFC/tanab/izanagi` を読まない。差分は commit `134e5926d` として着地済みなので、`git show 134e5926d` や `git diff 134e5926d^ 134e5926d` で読んでよい。

## この段の仕事 — 段 6 敵対レビュー・レンズ B: テストが機構を通るか、変異を殺せるか

**テストを守るのではなく壊しに行く。** 実装・編集・commit はしない。出力は最終メッセージ本文にすべて書く (file へ書けない sandbox である)。

sandbox は read-only で書込み可能な tmp が無いため、**pytest 実走は要求しない。静的検査でよい。**実走は親が行う。実走していない結果を「緑」と書かない。

1. **必須 assertion の被覆表を作れ。** 裁定「設計 v2」の 6 が列挙する必須 assertion 1 件ごとに、
   それを固定する test 関数の名前と行番号を対応させよ。**対応が無いものは「未被覆」と書け。**
   実装子の報告の表を鵜呑みにせず、test の中身を読んで判定せよ。
2. **fixture が本当に機構を通るか。** CLI e2e の fixture が、`_default_registry_module` の
   live import と blob 照合を実際に越えて `_default_registry_results` に到達しているか、
   コードを追って確かめよ。到達していないなら、その test は何を固定しているのかを述べよ。
   単体 test 側も、`_default_registry_results` / `_normalize_predicate_results` / 診断 helper /
   sibling API のどれかを stub していないか確認せよ。**stub していれば機構を通らない緑である。**
3. **変異事前登録の各項を殺せるか (最重要)。** 裁定の枠 1 (M1〜M3) と枠 2 (D1〜D8) の
   **1 件ずつ**について、現在のテスト集合が本当に検出するかを判定せよ。判定は「どの test 関数の
   どの assertion が落ちるか」を名指しで書くこと。**検出しないものは検出しないと書き、
   検出するために足りない assertion を述べよ。**
4. **新しい生存変異を考案せよ。** 現在のテスト集合を**全部緑に保ったまま**、
   (a) 診断機構を無効化する、(b) 診断を虚偽にする、(c) fail-closed の totality を壊す、
   のいずれかを達成できる変異を **3 件以上**考案せよ。各々に `file:line` と変異内容を添えよ。
5. **偽緑の経路。** テストが揮発 payload (temporary path、時刻、working tree hash) を期待値へ
   焼き込んでいないか。fixture へ現行 hash を差し込んで甘くしていないか。
   assertion が恒真になっている箇所は無いか (例: 空集合に対する `all()`、
   例外が出ないことだけを確かめて中身を見ていない箇所)。
6. **既存テストの期待値が変更・反転・緩和・skip・削除されていないか。**
   裁定が唯一許した `test_non_json_cli_reports_decider_reason` の seam 追随を除き、
   既存 assertion が 1 つでも弱くなっていないかを差分で確認せよ。
7. **新規 test node の副作用。** 追加された test node が、test file 一覧・自走 harness・
   受入所要台帳・meta-test の前提を壊さないか。実装子が既存 test file の末尾へ足した
   自走入口が、その形式を要求する meta-test の期待と整合するか。

## 禁止

- 実装・編集・commit・push。
- 新しい gate・検査・台帳・一般化の追加提案 (裁定の scope 外)。`## scope 外の所見` へ分けて書く。
- 既存テストの期待値の変更・反転・緩和・skip・削除の提案。
- 実走していないものを緑と書くこと。
- 出力に結合文字 U+0300〜U+036F を使うこと。

## 出力形式

所見は 1 件ずつ `- 所見 N (深刻度: blocker | must-fix | nit):` の形で番号を振り、**それぞれに「放置すると成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるか」を 1 行で書く。書けない所見は nit にする。** 所見ゼロなら「所見ゼロ」と明記し、根拠を書く。

次の H2 見出しをこの順で使う。

- `## 必須 assertion の被覆表`
- `## fixture が機構を通るか`
- `## 事前登録変異の検出可否 (M1〜M3・D1〜D8)`
- `## 新しい生存変異`
- `## 偽緑の経路`
- `## 既存テストの弱体化`
- `## 新規 test node の副作用`
- `## scope 外の所見`
- `## 総括`

予算が尽きそうなら、その時点の途中結論をこの出力形式どおりに書いて終われ。無出力が最悪である。
