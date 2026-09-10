## 総括

指定された段 1 brief と段 2 plan を先に全文読んだうえで静的検証した。

結論は次のとおり。

- **(P1) はそのまま維持できない。** 「本件は検査なし・無承認の事故ではなかった」は確認できた。しかし「防壁が発火する余地はなかった」は誤りである。`77db32c` は main の ancestor ではなく、削除後に `rescue-t213` が作られたのは **32時間36分51秒後**だった。現存 ref で同 commit を含むのは `rescue-t213` だけである。したがって「surviving durable ref に到達不能なら、先に rescue ref を作る」という防壁なら本件でも発火した。
- **(P4) は「今すぐ制度を land しない」という結果に限って維持してよい。** DW-G03 の独立 2 例は依然見つからなかった。一方、「未承認 0 件」を母集団全体の事故率ゼロとして制度不要を導くことはできない。これは surviving transcript 内の観測値にすぎず、手動 shell、別 clone／別ホスト、消去済み reflog、GC 後の object を含まない。
- 事後監査の穴は大きく、**pre-delete の回復可能性確保を裁定候補にする強さはある**。ただし、全削除を hard-block する制度の即時 land までを DW-G03 抜きで正当化する証拠ではない。裁定語は「却下」より「証拠不足で保留、rescue-first 案を保持」が正確である。

## 1. 「0 件」の意味と単一事例主義

親が確認した本件の一次証拠は崩れなかった。

- `9f45e239` / `2026-08-03T11:57:22Z`: 内容を検査。
- 同 / `2026-08-03T14:10:58Z`: ユーザーが `-D` を承認。
- 同 / `2026-08-03T14:12:08Z`: tip を記録して削除。

一方、「ahead>0 かつ未承認の `git branch -D` は 0 件」は、実質的には次の値である。

> surviving session transcript に記録された実行のうち 0 件

ローカル `.bash_history` も確認したが、branch `-D` は残っていなかった。ただし履歴は 16,707 bytes にすぎず、非対話 shell、未終了 shell、履歴抑止、旧 clone、別ホストを覆わない。さらに Git 2.34.1 の `git-branch(1)` は、branch 削除時にその branch reflog も削除すると明記している。

したがってこの 0 件には、分母の完全性も観測期間もない。事故が古いほど GC により証拠が消えるため、欠測はランダムでもない。ただし、これは独立 2 例の存在を立証するものでもないため、[DW-G03](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/docs/dev-wave/core.md:52) を突破はできなかった。

## 2. 事後監査の検出範囲

[audit_dangling_commits.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/audit_dangling_commits.py:78) をコードから確認した。

| 対象 | 判定 |
|---|---|
| 既存ファイルへの編集だけ | **検出不能。** `changed_files()` は path を返すが、`audit()` は同名 path が main に存在するだけで除外する。blob、patch、mode、内容は比較しない。 |
| 既存ファイルの削除 | **通常は検出不能。** main tree に旧 path が残っているため同じ除外に入る。 |
| 同名・別内容 | **検出不能。** 別 local branch tip に同名 path があるだけでも除外する。テストもこの非報告を固定している。 |
| 新規かつ固有の path | object が残り、除外 prefix 外で、main／他 branch tip に同名 path が無ければ検出可能。 |
| GC prune 後 | **検出不能。** `fsck --unreachable` が列挙できる object 自体が無くなる。復元機能はない。 |
| `docs/` | 全体除外ではない。既定除外は `docs/spool/` と `docs/archive/` だけ。 |
| `output/` | 除外 prefix ではない。ただし既存 output file の編集は path 存在判定で見逃す。 |

除外は [19–25行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/audit_dangling_commits.py:19)、実際の path 除外は [121–152行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/audit_dangling_commits.py:121) にある。`--include-fold-trees` は存在するが、通常入口は引数なしで呼ぶため既定除外が有効である。

GC の既定値もこのホストの Git 2.34.1 同梱 manpage と repo config から確認した。

- `gc.pruneExpire`: **2 weeks ago**。repo に上書きなし。
- `gc.reflogExpireUnreachable`: **30日**。
- 通常 reflog expiry: 90日。
- ただし branch 削除は当該 branch reflog 自体を削除する。他 reflog、tag、remote-tracking ref、pack があれば長く残り得るため、「必ず14日で消える」保証ではない。
- 逆に `--prune=now` なら即時消去も可能。

さらに運用 caller を静的検索すると、実行入口は [cleanup-branches.md:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/.claude/commands/cleanup-branches.md:17) のみだった。定期監査でも ref-delete hook でもない。直接削除後に `/cleanup-branches` が呼ばれなければ、2週間の窓内に走る保証はない。

したがって、この監査を理由に pre-delete 防壁を不要とはできない。

## 3. 全層の scope

| 層 | 現状と限界 | 裁定パッケージ候補 |
|---|---|---|
| `/cleanup-branches` | ahead=0、`-d` のみという prompt 規律。即興 Bash、手動 shell、他 client を覆わない。 | 専用 wrapper／rescue-first 手順。ただし任意入口であることを明記。 |
| Claude `guard_bash` | 通常の `git branch -D` は防護 path を含まないため [fast path](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/hooks/guard_bash.py:1532) で許可される。 | fast path 前の ref-delete 判定＋対象 ref の到達性 oracle。Claude Bash の部分被覆に限定。 |
| Codex | [hooks/README.md:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/hooks/README.md:15) のとおり未配線で、`.codex/hooks.json` もない。 | D54〜D56 の adapter／runtime 再開条件を満たすまで scope 外。 |
| supervised dev-wave | Git allowlist に branch delete はなく閉じている。ただし Git helper は `core.hooksPath=/dev/null` を明示する。 | 現状は新規対応不要。将来削除 API を足す場合だけ同じ oracle を必須化。 |
| Git common-dir | `reference-transaction` 相当が最も広いが、現在 `.git/hooks` は sample のみ、`core.hooksPath` 設定もない。clone／host ごとの配線が必要で `-c core.hooksPath=/dev/null` 等でも迂回可能。 | ユーザー／環境管理者所有の別裁定。repo 内実装だけで「全 Git 操作を保護」と主張しない。 |
| ExitWorktree harness | repo 外の built-in。ahead-of-base count の変更権限がない。 | harness 所有者へ「surviving refs に対する unique commit 判定」または自動 rescue ref を要請。 |
| 手動 shell・別ホスト・直接 ref 操作 | Claude hook から不可視。local branch は remote server policy でも守れない。 | 環境配線または append-only 削除台帳を別 owner の裁定として出す。 |

実効性を求めるなら、最低でも次の三つを別 owner で扱う必要がある。

1. repo 所有: Claude Bash／cleanup wrapper の rescue-first。
2. harness 所有: ExitWorktree の count 定義修正。
3. 環境所有: canonical common-dir・clone・host への Git hook／削除台帳配線。

一層だけ実装して「branch 削除を保護した」とするのは実装したふりになる。

## 4. ExitWorktree 一般化の再検査

親の「サンプル 2 件」は単独では弱かったため、structured transcript から全 call を再抽出した。

現在の `/work` repo transcript では、

- `discard_changes:true` の remove 成功: **22 call**
- bare `remove`: **6 call**
  - commit count 警告: 5
  - ownership gate 拒否: 1

旧 `/home/.../github/izanagi` transcript では、commit count 警告がさらに 3 件あった。

計 **8 件**の実警告は `N = 1, 1, 6, 8, 10, 52, 79, 113`。全件について前後を追跡したところ、いずれも警告前に fast-forward／`dev_wave_land.py` が成功し、tip は main と同一または main の ancestor だった。警告後に `keep` へ転じた 2 件も未 land 作業ではなかった。

さらに rulings session では、最初の警告後、後続 17 worktree を最初から `discard_changes:true` で除去していた。これは「反射的 override を訓練する」という懸念に対する実際の行動証拠である。

したがって、

- 「サンプル 2 件だけから全件を一般化」は不十分だった。
- しかし今回 8 件へ拡張しても反例はなく、親の警告疲労懸念は**崩せなかった**。
- ただし「22回警告が鳴った」は不正確。22 は override 成功 call で、実際の count 警告は現行 repo 5 回だった。

## 崩せなかった点

- 本件が検査・ユーザー承認を経た削除だったこと。
- ahead>0・未承認削除の独立した第二例。
- ExitWorktree の count 警告が未 land 作業を実際に救った例。観測した 8 件はすべて偽陽性だった。
- `tools/audit_dangling_commits.py` が commit `cc1c2af4fc5f046c04bad2912376822cbada0e96` で main に land 済みであること。
- DW-G03 に基づく「今 wave で新しい全域防壁を実装しない」という結論。

ただし、P1 の「発火余地なし」と、P4 の「0 件だから不要」という読み方は維持できない。現時点で最も証拠に比例した裁定は、**hard-block の land は保留しつつ、意味判断を繰り返さない rescue-before-delete 型を裁定候補として残し、scope 外の harness・環境層を明記すること**である。

静的読み取りだけを行い、ファイル変更・テスト・`git fsck` は実行していない。