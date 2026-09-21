## 対応表

パスは worktree 相対。以下、`A-test` = `orchestrator/tests/test_plot_a1_sized_paired.py`、`M-test` = `orchestrator/tests/test_plot_mocc_witlight_four_arm.py`、`M-gen` = `tools/plotting/plot_mocc_witlight_four_arm.py`。ログ・fix 報告は指定 job dir 配下。

| 所見 | 判定 (closed / partial / regressed / refuted 妥当) | 根拠 |
|---|---|---|
| 赤：fig14 bundle 欠落 | closed | `A-test:775` の専用メッセージを `:809` で先頭行完全一致。全欠落＋単独欠落3例を維持し、後段の別 AssertionError を受理する経路は見つからない。修正前 `focus-1.log:323`、修正後 `focus-2.log:28–31`。 |
| 赤：attempt2 可視禁止句 | closed | `A-test:653` が禁止句ごとに異なるメッセージを出し、`:673` は注入した `reproducibility confirmed` の専用文言と完全一致。正常時の事前検査も `:668` に残る。他の禁止句による失敗は通らない。修正前ログ `:324`、修正後ログ `:28–31`。 |
| 赤：fig15 bundle 欠落 | closed | `M-test:415` の専用メッセージを `:446` で先頭行完全一致。全欠落＋単独欠落3例、例外なしの場合の失敗、`REPO` の復元を維持。修正前ログ `:325`、修正後ログ `:28–31`。 |
| 赤：caption／可視禁止句 | closed | `M-test:324` が検出した禁止句をメッセージにし、`:354` は `equivalent` と完全一致。正常時の検査は `:347`、注入後の無検出は `:356` で失敗する。修正前ログ `:326`、修正後ログ `:28–31`。 |
| A#1 | closed | `tools/plotting/README.md:514–516` の列挙と実装が一致。`N`、`m`、`k`、`failure`、`indeterminate`、`decisive_m`、`discriminator_counts`、`identification` は `M-gen:212–213` の等値比較、`k_over_m` は `:214`、`cp95` は `:215` の絶対許容差 `1e-12` の比較。Fisher・commit 平均・曝露比はこの照合に含まれない。 |
| A#2 | refuted 妥当 | **一部 refuted という裁定が妥当**。`docs/failures.md:2002–2023` の F36 は結果欄のプレースホルダ問題だが、`docs/dev-wave/core.md:117` は実際に「hash 自己参照は禁止（F36）」と記す。したがって元文言には先例がある一方、F36 本文との不整合は残る。新文言 `docs/paper-story/figures/README.md:1894,2003` は相互 hash の循環回避を直接説明しており、修正として適切。 |
| A#3 | partial | `M-test:477–480` は可視 `Text` のリストへ曝露比2行の完全一致を要求する。描画 `M-gen:307–308` を削除すれば内部系列が残っても失敗する。`codex/fix-mocc.md:15,69` の M14 KILLED 報告と整合。外部 root 不在では `M-test:454–455` でこの検査全体が skip される。修正後ログ `:28–31` の skip は template patch 関連3件だけなので、今回の計算ノードでは実行されたと判断できる。ただし、この可視検査の環境依存は README に明記されていない。 |
| B#1 | closed | A#1 の summary 照合対象に加え、稿との照合も一致。Fisher の表・p は `M-test:465–468`、commit 平均は `:464,473`、曝露比の数値文字列は `:472`。稿 §2.2／§2.3／§2.6 の対応セルを比較する。曝露比セルの括弧内説明は比較対象外だが、README が述べる量の逐語照合とは矛盾しない。 |
| B#2 | closed | `M-test:21–27` は script 所在ディレクトリを探索先に追加し、同階層の `skiputil` を import。生成器も絶対パスからロードするため repo package 解決用の `PYTHONPATH` は不要。`codex/fix-mocc.md:12` に PYTHONPATH なしで27件成功の報告がある。本レビューでは再実行していない。 |
| B#3 | closed | 削除した分岐は `M-gen:329–330` の唯一の axes 制約を通過した後では到達不能。図外逸脱 `:338–339`、所有 axes 内への包含 `:340–341`、文字重なり `:343–346`、軸装飾の逸脱 `:347–349` は残る。負例 `M-test:286–302` と公開前の検査 `M-gen:435` も維持。 |

先頭行比較は、pytest が付加する後続の説明だけを比較対象から外している。同一行の余分な文言や別メッセージは引き続き拒否する。現在の呼出し経路に、期待する先頭行を共有する別理由の AssertionError は見つからなかった。修正後は **804 passed / 3 skipped** で、修正前の **800 passed / 4 failed / 3 skipped** から赤4件が解消している。

## 新しい所見

| # | 重大度 | 対象 | 内容 | 根拠 | 推奨 |
|---|---|---|---|---|---|
| 1 | should | `docs/paper-story/figures/README.md:2019–2023,2035,2058` | A#3 の修正で追加した可視曝露比検査が、外部 root 不在時には実行されないことの説明が不足している。実装の後退ではなく、修正後の保証範囲の記載漏れ。 | README が明示する root 不在時の skip は外部閉包 test。新検査を含む `test_real_evidence_matches_results_document_when_root_present` は表セル照合としてのみ紹介される。実際には `M-test:454–455` が可視検査 `:477–480` も skip する。 | 当該 test が表セルと可視曝露比2行を検査し、外部 root 不在では双方が未検証になる旨を追記する。 |

追加で確認した regression の範囲は以下のとおり。

- **描画・caption・provenance：** 指定2 commit に描画処理、数値導出、caption 組立て、provenance 組立て、着地図3 file の変更はない。生成器の変更は到達不能な layout 分岐4行の削除だけ。
- **fig15 の閉包：** `M-gen:405` は `generator.sha256` の形式を検査し、現行 source の hash との一致を要求しない。これは README `:2023` の「生成時点の記録」と一致する。出力 hash、稿 hash、保存統計、artist 系列、現行 caption との閉包は `M-gen:404–414` に残り、source hash が変わっただけで着地物を更新する必要はない。
- **既存28 test：** base `36fb14a3d` と `fc6c4f836` の A-1 test 関数を AST で抽出し、関数ソースを比較した。**28本すべて本文・期待値が一致**した。今回の4箇所の変更は本 wave の追加 test に限られる。

## 総括

**GO。must-fix／regressed は見つからず、残件は README の射程明記 should 1件。**
A#3 は今回の計算ノードでは検出力を回復しているが、文書を含む完全閉鎖とは扱わない。
修正後の焦点走は **804 passed / 3 skipped**。ログ自身の警告どおり、受入全走の成功とは扱わない。
本レビューは静的検査と提示ログの照合のみで、書込み・作図・pytest・変異実走は行っていない。