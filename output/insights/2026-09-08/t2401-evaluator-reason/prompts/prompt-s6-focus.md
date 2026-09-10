単独段 dispatch: stage=focus; sandbox=read-only; parent=/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s6-ruling.md

## 必読事項の射影

次の絶対パスだけを読む。読めなければ即停止し、その旨だけを出力する。

- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s6-ruling.md` — 段 6 裁定 (所見の採否と fix scope)
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s4-ruling.md` — 段 4 裁定 (設計 v2・不変条件 1〜7・変異事前登録)
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s6-revA.md` — 段 6 レビュー A の所見
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s6-revB.md` — 段 6 レビュー B の所見
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s6-fix.md` — fix 子の完了報告 (自己申告。裏を取る対象)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_cli_entrypoints.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_core.py`

repository の root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason` である。親側の `/work/1/SFC/tanab/izanagi` を読まない。最終差分は commit `8789ea89a` (直前が `134e5926d`)。`git show` / `git diff 134e5926d^ 8789ea89a` で読んでよい。

## この段の仕事 — fix 後の焦点再レビュー

**所見ごとの対応表を作ることが主目的である。** 実装・編集・commit はしない。出力は最終メッセージ本文にすべて書く (file へ書けない sandbox である)。

sandbox は read-only で書込み可能な tmp が無いため、**pytest 実走は要求しない。静的検査でよい。**実走は親が行う。実走していない結果を「緑」と書かない。

1. **対応表 (必須)。** 段 6 レビュー A の所見 1〜3 と、段 6 レビュー B の所見 1〜3・生存変異 S1〜S6 のそれぞれについて、**`closed` / `partial` / `regressed` / `scope 外 (裁定済み)`** を判定し、根拠を `file:line` で示せ。表が無い状態で「root cause が閉じた」と判定してはならない。
2. **裁定に無い変更が混ざっていないか。** fix commit `8789ea89a` の差分に、段 6 裁定の「fix の scope」1〜3 以外の変更が入っていないかを確認せよ。
3. **不変条件の再検査。** 段 4 裁定の不変条件 1〜7 が、fix 後も成立しているかを再度検査せよ。特に次を見よ。
   - sentinel を変えたことで、`reason_code` 語彙や既存 assertion に影響が出ていないか。
   - CLI の診断出力を `except Exception` で囲んだことで、**本来出るべき診断が黙って消える**経路が
     増えていないか。握り潰しが広すぎないか (stdout の print まで巻き込んでいないか)。
   - 追加された負例が、`RuntimeError` の subclass でない例外を本当に使っているか
     (`PreregistrationError` は `RuntimeError` の subclass である)。
4. **新しい生存変異。** fix 後のテスト集合を**全部緑に保ったまま**、診断機構の無効化・虚偽化・
   fail-closed の totality 破壊のいずれかを達成できる変異を探せ。**無ければ「無い」と書き、
   そう判断した根拠を書け。** あれば `file:line` と変異内容を書け。
5. **既存テストの弱体化。** fix commit で既存 assertion が 1 つでも弱くなっていないかを差分で確認せよ。

## 禁止

- 実装・編集・commit・push。
- 新しい gate・検査・台帳・一般化の追加提案。`## scope 外の所見` へ分けて書く。
- 既存テストの期待値の変更・反転・緩和・skip・削除の提案。
- 実走していないものを緑と書くこと。
- 出力に結合文字 U+0300〜U+036F を使うこと。

## 出力形式

次の H2 見出しをこの順で使う。所見は `- 所見 N (深刻度: blocker | must-fix | nit):` で番号を振り、成果物影響を 1 行添える。

- `## 所見ごとの対応表`
- `## 裁定外の変更`
- `## 不変条件の再検査`
- `## 新しい生存変異`
- `## 既存テストの弱体化`
- `## scope 外の所見`
- `## 総括`

予算が尽きそうなら、その時点の途中結論をこの出力形式どおりに書いて終われ。無出力が最悪である。
