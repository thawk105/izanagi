---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-10-01
wave: worktree-cleanup-stop-hook-ffonly
seq: 1
title: [T-2951] 撤去を促す Stop hook が main へ ff しただけの未 land の木に出る誤検出を直した (md_6) — 免除は作成項・ff main の subject・main の reflog 時刻の 3 つで裏付け、変異 12/12 登録どおり (コード + test + insight、branch worktree-cleanup-stop-hook-ffonly)
---

## 本文

- 依頼: next-tasks 2026-10-01 の md_6 (`tools/dev_wave_cleanup_stop_hook.py` の F1081 の誤検出を直す、Codex author)。対象は [T-2951] (P2) と同じ原因の [T-2957] (P3)。
  一次資料は `output/insights/2026-10-01/cleanup-stop-hook-ffonly/README.md`。設計判断は {{D:cleanup-stop-ff-exemption}}。
- 実物再現 (段 1): 使い捨て repo で、遅れた起点から branch を切り `merge --ff-only main` しただけの木に変更前の hook script を通すと block (誤検出)、
  commit して main へ ff-only land した木も block (正しい)。変更後は前者が通り、後者は block のまま。
- 段 2・3 は軽量版で省いた (変更は小さく設計択一は 1 点)。block する状態の集合が変わるので段 6 の敵対レビュー 2 本は残した。
- 段 6: レビュー A (正しさ境界)・B (過剰・削除) とも NO-GO。real 4 種を採用して Codex fix 1 巡 (作成項の要求、LF だけで分割、空 subject を空として扱う、
  ff 項の OID を main の reflog がその時刻以前に指していたことの照合)。nit 2 件 (test の統合・分岐の統合) は任意とし、分岐だけ統合された。
- 段 6 焦点再レビュー C も NO-GO (反例 5 件)。DW-O16 に従い fix を重ねず親が裁定: main の巻き戻し + 同名 tag、`GIT_COMMITTER_DATE` による記録時刻の逆転、
  `GIT_REFLOG_ACTION=branch` の偽装 commit + 作成項の削除の 3 件は、git の記録の改変が要るので scope 外 (旧 hook も reflog 削除・`branch -f` には負ける、
  hooks/README.md hook 5 の既知の限界)。main の reflog 失効で誤検出が残る件は安全側で scope 外。main reflog 読み取りの時間切れで fail-open する件は、
  そこへ入るのが作成後の全項が ff main の木だけなので不採用。根拠は insight の `verbatim/ruling-stage6-round2.md`。
- 変異 (独立 clone、対象 `70af9ee82`): probe で m8 が SURVIVED。fix 後の書式では OID 直後の区切りが残るので注入が発火経路に届かなかった (erratum として台帳に残し、
  subject 前の区切りへ再照準した m8b を足した)。final 12 変異は 12/12 登録どおり (KILLED 11、等価 m0 SURVIVED、MISMATCH 0)。
  m8b は probe で期待の 1 node だけが落ち、final も KILLED 1/1 で登録どおり。
- 焦点走 (計算ノード): fix 後 `test_hooks.py -k "cleanup_stop or settings_json"` 30 passed。全史 provenance 監査は実装 commit 後と main 取り込み後の 2 回とも rc=0。
- 受入全走は本記録 commit の後に受入待ち手で取る (結果は受領証と land 申告に書く)。
- セッション異常: 段 5 の author 1 回目が委任 (`spawn_agent`) を検出されて未受理になった。prompt に委任禁止を書き忘れた親の手順漏れ (D2335・DW-O01 に義務は既記載) で、
  F452 (段の prompt に DW-O01 の必須事項を書き忘れる型) の再発として記録した。残差 commit を委任禁止を明記した 2 回目が単独で監査して受理された (追加差分なし)。
  workspace-write の Codex 子は sandbox から計算ノードへ dispatch できず (qstat preflight rc=1)、焦点走は親が行った。
- 工数: Codex author 2 (1 回目は未受理)・fix 1・review 3 (A・B・焦点 C)、焦点走 2 (計算ノード、各数秒)、変異は harness 4 走 (probe 14 job・final 13 job・m8b の probe と final 各 2 job)。

## 次の一手差分

### 完了

- [T-2951] `tools/dev_wave_cleanup_stop_hook.py` の判定を直し、`test_cleanup_stop_*` に負例と正例を足した ({{D:cleanup-stop-ff-exemption}})。
  remaining: none
  base: 09e64531302da30abe56cd4656872f8444282ce3b564e9c4422007383b78f4a2
- [T-2957] [T-2951] と同じ修正で閉じた (`merge --ff-only main` で揃えただけの木で終了のたびに出ていた促しが消える)。
  remaining: none
  base: a7ce7478062da91dc2db65d931fd5bf566f2702f56e57dd8fbda35c540efa677

### 新規

- {{T:cleanup-stop-hook-readme-sync}} **P3・新規**: `hooks/README.md` の「hook 5」節の判定と既知の限界を {{D:cleanup-stop-ff-exemption}} に合わせる
  (「branch 作成後に main を fast-forward で取り込んだだけの未 land wave は誤って促しうる」の 1 文を、`merge --ff-only main` は通すこと・残る限界
  (git の記録を改変した木、main の reflog 失効、sha 指定の ff・`pull`・`reset`) へ置き換える)。`hooks/` は guard_write の自己保護で AI が直接書けないので
  D427 の経路で行う。放置すると hook 5 の契約文が実装と食い違う。根拠: md_6 の insight `output/insights/2026-10-01/cleanup-stop-hook-ffonly/README.md`。
