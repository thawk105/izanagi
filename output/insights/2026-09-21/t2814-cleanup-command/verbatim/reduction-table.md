# command 本文の削減・追加の対応表 (親、段 5、docs commit f6a530523)

予算 6,204 bytes、旧 6,181 → 新 6,201 (余白 3) → fix 1 後 6,200 (余白 4) → fix 2 後 6,204 (余白 0、既存 test と衝突) → fix 3 後 6,201 (余白 3、最終)。最長行 105 文字 (上限 110)。上限は動かしていない。
D782 手順 1 段目 (既存記述の削減) だけで収容し、2 段目 (独立 3 例)・3 段目 (上限引き上げ) には進んでいない。

## 追加 (2 命令)

| # | 節 | 新文 (逐語) | 一次資料の根拠 |
|---|---|---|---|
| A1 | §2 | `- 未追跡 \`output/\` (\`exploration/\`・\`env/\`) は該当 wave の insight「証拠の所在」節で` / `  repo 外原本か確かめ、原本なら候補にせず残置・報告 (F1034)` | loss record §2 見落としの 2 段目、§5 教訓 2 (「未追跡 = 捨ててよい」ではない。候補にする前に insight「証拠の所在」節を引く) |
| A3 (fix 2) | §2 | `- 高い条件: 削除直前に status 空と非施錠を再確認。§3 の占有・判定不能は保持。` (旧: `削除直前に §1 の status 空を再確認。`) | 稼働中だった cleanup session (00:20〜00:36 完走) の final の罠「棚卸し後に lock 状態が変わる (実行中に /rulings session が submit-tree-pair を lock)」(memory cleanup-discipline 2026-09-21 節)。「§1 の」を落とすのは削除直前の再確認が新規取得の status であり §1 保存分との比較は §4 が担うため |
| A2 | §3 | `§5 で引き渡す dirty 撤去 script も本節に従い、退避を撤去の前提にする: tar は \`-C <worktree>\`` / `を \`-T\` の前に置き、\`ls-files -o\` の list 数を tar の非 dir entry 数が下回れば撤去しない (F1034)。` (fix 1: 段 6 must-fix で「list と entry 数が一致」を一次資料の条件へ訂正) | loss record §2 原因 (1) (`-T -` の後ろの `-C` は効かない)、§4 修正 (list と tar の非 dir entry 数を照合、不足なら撤去せず rc=6)、§5 教訓 1 (rm の前に退避物を検算するまでが退避) |

## 削減 (11 件 R1〜R11。R6 以外は意味を変えない縮約、R6 は手段指定の削除)

| # | 節 | 旧 (逐語) | 新 (逐語) | 分類・保持の根拠 |
|---|---|---|---|---|
| R1 | frontmatter | `argument-hint: [任意: 削除対象の限定 (ブランチ名/worktree 名)。省略時は全量棚卸しして安全なものだけ削除]` | `argument-hint: [任意: 対象限定 (branch/worktree 名)。省略時は全量棚卸し]` | 冗長語。「安全なものだけ削除」は §2 (安全条件) が定める |
| R2 | §0 | `final で裁定候補として返し、実装・記録・commit は後から明示起動された別 dev-wave だけが行う。` | `final で裁定候補として返し、実装・記録は明示起動された別 dev-wave だけが行う。` | 「commit」は同段落で `git add/commit/...` が既に禁止、「後から」は「明示起動された」に含意 |
| R3 | §0 | `削除は不可逆に近いので、以下の条件を満たすものだけ消し、迷ったら残して報告する。` (段落ごと削除) | (無し) | 根拠説明 (「不可逆に近い」) + §2 見出し「満たさないものは削除せず報告に回す」と高い条件「迷えばユーザー確認」が同義の義務を持つ |
| R4 | §1 | `rebase/cherry-pick 後も ahead>0。\`+\` 行は実在でなく内容判定` / `(spool 不在は fold で正常)。未着地は §5 へ` | `\`+\` 行は実在でなく内容判定 (spool 不在は fold で正常)。未着地は §5 へ` | 「rebase/cherry-pick 後も ahead>0」は cherry で内容判定する理由の説明。命令「`+` 行は実在でなく内容判定」は保持 |
| R5 | §3 | `2. \`git branch -d <branch>\` (取り込み済み確認の上)` | `2. \`git branch -d <branch>\`` | §2「branch: ahead=0 (main 取込済み) のみ `git branch -d`」と重複 |
| R6 | §3 | `ExitWorktree の remove を \`discard_changes: true\` で押し切らない。main が当該 commit を含むことを` / `\`git log\` で確認し、\`action: keep\` で抜けて本節の手順で畳む。` | `ExitWorktree の remove を \`discard_changes: true\` で押し切らず、main が当該 commit を含むと` / `確認して \`action: keep\` で抜け、本節で畳む。` | **意味不変ではない (段 6 nit):** 確認の義務と `action: keep` は保持、手段指定「`git log` で」は削除 (別手段の確認も許す。撤去集合の拡大は立証されない) |
| R7 | §3 | `cwd 固定の背景セッション (ExitWorktree が no-op・cd 非持続) や occupied/locked worktree は、` | `cwd 固定の背景セッションや occupied/locked worktree は、` | 括弧書きは判定条件の説明 (正本は F51、参照は保持) |
| R8 | §4 | `- \`git submodule status\` — main checkout の external/ccbench が \`-\` prefix なし (初期化済み) で` / `  pin に一致すること` | `- \`git submodule status\` — main checkout の external/ccbench が初期化済み (\`-\` なし) で pin 一致` | 同義の言い換え |
| R10 (fix 1) | §4 | `- cleanup 前の status を保存し、surviving worktree・index・repo file に新しい差分が無い` | `- §1 の status と比べ、surviving worktree・index・repo file に新しい差分が無い` | §1 が「§4 用に保存」を既に命じており「保存し」は重複、「比べ」は §4 の検査の意味を明確化 (所見 1 の +9 bytes を吸収、−10) |
| R9 | §5 | `リモート branch の削除 (\`git push origin --delete <b>\`) と main の push は行わず、対象をユーザーへ列挙。` | `remote branch の削除と main の push は行わず、対象をユーザーへ列挙。` | command 例を落とした (禁止の義務は保持) |
| R11 (fix 3) | §5 | `remote branch の削除と main の push は行わず、対象をユーザーへ列挙。` | `remote branch 削除と main の push は行わず、対象をユーザーへ列挙。` | 助詞 1 語 (−3 bytes、意味同一)。余白 0 が既存 test (先頭空白 +1 byte の mutation) と衝突するため |

## 保持を確認した check_docs の構造 literal

- §3 冒頭 2 行 (`CLEANUP_OCCUPANCY_CONTRACT`、exact)、「正本は `docs/failures.md` F26。」(F26 と `docs/failures.md` の同一可視行共起)、`docs/skill-self-improvement.md` (§6、到達性)、`$ARGUMENTS` 1 件、frontmatter key 集合 {description, argument-hint}、`discard_changes: true` 1 回 (test の byte-neutral slack)。
- check_docs 直叩き (docs commit 前、job tmp `check_docs_docs_only.log`): 違反は「whole-file SHA-256 が契約と不一致」2 件だけ。

## SKILL.md (Codex overlay) の追加 2 項 (2,646 → 3,052 bytes、上限 3,100)

- `- 未追跡 \`output/\` (\`exploration/\`・\`env/\`) を抱える worktree は、command §2 の原本確認 (insight` / `  「証拠の所在」節) を経るまで foreign/unknown と同じく保持して報告する。`
- `- dirty の撤去や引き渡し script は command §3 の退避検算 (tar の \`-C\` 順・非 dir entry 数照合) を前提にし、` / `  検算を欠く撤去手順を人間へ渡さない (F1034)。` (fix 1 で「非 dir」を追加 +8 bytes、3,060/3,100、余白 40)
- 既存記述は削っていない。
