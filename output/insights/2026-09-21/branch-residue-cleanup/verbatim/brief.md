# 段 1 brief (未採番、worklog fragment の新規 {{T:branch-residue-cleanup}}) — 残骸 branch/worktree が溜まらない構造にする

起点: ユーザーの `/dev-wave` 起動 (2026-09-21 00:59 JST、背景 job a5f1786a)。一次資料 = `/work/1/SFC/tanab/dev-wave-jobs/cleanup-branches-20260921-rescue/self-improvement-brief.md` (同 dir: deleted-branches.tsv 140 / excluded-branches.tsv 24 / loss-commits.tsv 227 / retire-worktrees.json / deleted-branches.bundle 5,933,267 bytes、bundle verify rc 0・heads 140)。起点 local main `285477c00` (fresh worktree `worktree-dev-wave-branch-residue-cleanup`、開始 gate rc 0 01:17 JST (未採番 T を slug に使った旧木 dev-wave-t2820-branch-residue から作り直し))。

## 研究前進 (土台)

止めている研究: 残骸 worktree 1 本で land が rc=21 になり全 wave が止まる (F26)。branch は 40 wave 分 155 本まで溜まり、掃除は 2026-09-17 と 09-21 の 2 度とも「ahead>0 なので消せない」壁で人間の手作業に落ちた (00:20〜00:46 JST の 1 session を消費)。完了判定 = (a) 改訂後の段 9 自己撤去で、integration 証明済みの Codex 子 branch が残らない (正例 = 本 wave 自身の子木で実走)、(b) `/cleanup-branches` が裁定条件下で `-D` を打てる条文と pin が main にある、(c) 3 台帳 fragment と台帳転記が land する。最小差分 = remove-child の postcondition 1 か所 + argv allowlist 1 行 + docs 3 leaf。

## 確定済みユーザー裁定 (2026-09-21 00:40 頃、一次資料の brief 冒頭)

(i) `/cleanup-branches` は branch の `-D` をしてよい。(ii) 残骸 155 本は消す (実施済み: 140 本を bundle 退避後 `-D`、unlocked・clean・所有 wave 終了済みの子 worktree 13 本を撤去、除外 24 本)。(iii) 自己改善 wave で再発を防ぐ (成果物 1〜6 はユーザーが起動引数で明示)。

## brief 前の実測で更新した前提

- `.claude/commands/cleanup-branches.md` は main で 6,181 / 予算 6,204 bytes (起動引数の「5,900 / 5,888」は旧値、D2043 で 6,204)。T-2814 wave (`dev-wave-t2814-cleanup-command`、段 5 親起草中、00:55 JST) が同 file を 6,201 bytes へ改訂中 → land 後の余白は 3 bytes。§0/§2 の改訂は圧縮で収めるか、実 byte 分だけの予算増 (D704 型、親裁定) が要る。
- `rescue2.json` は job dir `f9f84e36` の削除で消失。残る一次資料は loss-commits.tsv (227 commit: landed 26 / indeterminate 197 / not-landed 4、列 = oid / landed_state / branches / commit) と bundle。台帳 26 field のうち report sha256 / storage_kind / mtime / gc 系 / loss_possible_not_before は `check_branch_rescue.py --ledger-check` の再走で取り直す (候補なし形)。
- 現行 `tools/dev_wave_cleanup.py remove-child` は integration (子 reflog 全 commit が main の祖先、または所有 path の tree entry が main と一致) 成立時も子 branch を残し (postcondition が retained child branch 不変を検査、L1834-1836)、不成立は rc=20 "child is not integrated" (L1533-1547)。git argv allowlist は `branch -d --` だけ (L293-299)。
- D703 (2026-08-23) = D204 の狭い例外 (自 wave branch・`-d` のみ・`-D` 禁止)。**D2163 (2026-09-20、前日) が対象を manifest 登録済み子 worktree へ広げたが「子 branch は削除しない」「子 branch の `-d` は固定費削減に不要 (段 3 所見)」と明示的に却下している。** 今回の 155 本 / 40 wave 分の実測は D2163 の却下理由 (固定費に効かない) を覆す未見事実 → 新 D は D2163 を部分改訂する。
- `DW-O28` (996 / 1,000 bytes) は「子 branch は残す」「`-D` を使わない」を明文化し、`tools/check_docs.py` の `DEV_WAVE_DW_O28_SECTION_LITERAL` (L629) と `orchestrator/tests/test_check_docs.py` の `_SYNTHETIC_DW_O28_SECTION` (L189) が exact pin。台帳「覆わない範囲 2. DW-O28 の自動撤去」は `test_branch_rescue_ledger.py:340` と `check_branch_rescue.py:73` が文言 pin。
- 隔離 session は自 worktree の `git worktree lock` を guard に拒否される (01:08 JST 実測、既知)。子木の lock は Codex launcher が付ける。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) 段 9 の子 branch 削除は、remove-child が integration を証明した子だけを tool 内で `-D` する。証明不能 (rc=20) の子は現行どおり branch も木も残し理由を報告する — bundle 退避しての `-D` も、`/cleanup-branches` への名指し引き渡しも採らない。理由: 証明不能 = 内容が main に無い可能性で D204 の範囲、D2163 の「統合済みを条件とする裁定を緩めない」。
- (P2) `/cleanup-branches` の `-D` 許可条件 = 所有 wave が land 済み (記録 commit が main にある) ∧ 稼働 wave・locked checkout・HEAD 1h 以内・棚卸し後の新規を除外 ∧ 削除前に repo 外へ `git bundle` 退避 + verify ∧ `check_branch_rescue.py --ledger-check` を候補集合で 1 回 ∧ 損失 commit を台帳へ。ahead=0 の `-d` 経路は不変。
- (P3) 台帳転記 227 件は `status=pending`、`resolution_note` に bundle path + sha256 + 判定 (landed/indeterminate/not-landed) を書く。`accepted-loss` への遷移は人間の明示受容が要るので本 wave では行わない。
- (P4) `DW-O28` の「子 branch は残す」を「integration 証明済みの子 branch は tool が `-D` で消す」へ。argv allowlist の `branch -D --` は remove-child 経路限定、wave 本体は `-d` のまま。
- (P5) 「覆わない範囲 2」は据え置く (DW-O28 の削除は台帳の対象外のまま。内容は main に統合済みが前提)。

## 不変条件

`-D` は tool の integration 証明後だけで、手打ちの `-D` は dev-wave では引き続き禁止。wave 本体 branch は `-d`。段 9 では bundle 退避しない (統合証明が代わり)。push・remote・rebase・force 禁止。正しさ防壁 (verifier / freeze / oracle) 非接触 → `DW-O08`/`O09`/`O10` 不成立。`DW-O11` (file 削除) 不成立 (追記のみ)。`DW-O13`: gate 新設ではなく既存述語 (remove-child) の受理形拡張 → 段 2 前に読む。

## 成果物の形

1. decisions fragment `{{D:cleanup-force-delete-and-child-branch}}` (P2 + P4、D204/D703/D2163 との関係)。
2. `.claude/commands/cleanup-branches.md` §0 allowlist (1)/(2) に `-D` 経路を足し §2 を改訂 + `.agents/skills/cleanup-branches/SKILL.md` overlay (T-2814 land 後、その版を base、Codex author で `CLEANUP_COMMAND_SHA256` / `CODEX_CLEANUP_BRANCHES_SKILL_SHA256` / test literal・len を追随)。
3. `tools/dev_wave_cleanup.py` remove-child: 統合証明後に子 branch を `-D` し receipt に記録、`_validate_git_argv` に `branch -D --` を追加、docstring 更新 + `test_dev_wave_cleanup.py` の正例・負例 + `DW-O28` literal (check_docs + fixture placeholder) — Codex author。`DW-O28` 本文は親。
4. failures fragment `{{F:cleanup-allowlist-structural-residue}}` (型: 掃除規約の allowlist が構造的残骸に届かず 40 wave 分が溜まった。F747 の対)。
5. `docs/unreachable-object-ledger.md` に 227 entry 追記 (親、生成 script は job dir、値は再走の JSON から)。
6. §2 高い条件に lock file (`.git/worktrees/<name>/locked`) の存在検査 1 行 (2 と同 commit)。

## 並列分割・段構成

- author A (T-2814 と非競合): `tools/dev_wave_cleanup.py` + `orchestrator/tests/test_dev_wave_cleanup.py` + `tools/check_docs.py` の DW-O28 literal + `test_check_docs.py` fixture。
- author B (T-2814 land 後に main を取り込んでから): `cleanup-branches.md` + `SKILL.md` + `check_docs.py` の 2 sha + `test_check_docs.py` の literal / len。
- 親: `DW-O28` 本文、台帳 entry、3 fragment、insight。
- DW-C00 該当 (削除の受理集合が変わり、P1/P3 の設計択一が割れる) → 段 2 plan 1 + 段 3 consult 2 レンズ (正しさ境界 / 過剰・scope) + 段 5 author 2 + 段 6 review 2 + fix。全 9 段はユーザー未明示なので各段は最小本数。
- 受入・実測: 焦点走・受入は計算ノード dispatch (所在 = worklog 直近、機体 = pegasus-runbook)。変異 matrix は remove-child の `-D` 経路と argv allowlist、check_docs pin。生死確認 (DW-G01) = 段 9 で本 wave の子木に改訂後 tool を実走 (最安)。

## 変更面 (実アンカー)

| file | anchor |
|---|---|
| `tools/dev_wave_cleanup.py` | docstring L1-16 / `_validate_git_argv` L225-300 / `_assert_child_integration` L1533 / `_run_child` postcondition L1834-1836・receipt L1837 |
| `orchestrator/tests/test_dev_wave_cleanup.py` | `test_remove_child_archives_dirty_integrated_author_and_keeps_branch` L171 ほか child 系 L232-520 |
| `tools/check_docs.py` | `DEV_WAVE_DW_O28_SECTION_LITERAL` L629 / `CODEX_CLEANUP_BRANCHES_SKILL_SHA256` L780 / `CLEANUP_COMMAND_SHA256` L788 / `COMMAND_LIMITS` L286 |
| `orchestrator/tests/test_check_docs.py` | `_SYNTHETIC_DW_O28_SECTION` L189 / cleanup-branches literal + `len == 6_181` (T-2814 後 6_201) |
| `docs/dev-wave/operations.md` | `DW-O28` L209- (996 bytes) |
| `.claude/commands/cleanup-branches.md` | §0 L6-24 / §2 L42-49 (T-2814 版を base) |
| `.agents/skills/cleanup-branches/SKILL.md` | overlay 節 |
| `docs/unreachable-object-ledger.md` | 「覆わない範囲」L142-146 (据え置き) / entry 末尾 L148- |
| `docs/spool/{decisions,failures,worklog}/` | fragment 3 本 |
