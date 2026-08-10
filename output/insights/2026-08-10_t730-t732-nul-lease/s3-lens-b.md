結論: **NO-GO**。静的検査のみで、pytest・probe・`check_docs.py` は実走していない。

T-730 は、H1/H2 が NUL のみを追加し、TAB 正例で C0 一般化を殺す構成なので、裁定逸脱は見つからない。

### B1

`69379268` は取得後の merge と受入投入を明記するが、`local main` の再取得は暗黙で、明示的な post-`acquired` 再読がない。

根拠: [`docs/pegasus-runbook.md:767`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/docs/pegasus-runbook.md:767)、[`docs/pegasus-runbook.md:789`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/docs/pegasus-runbook.md:789)、`69379268`。実測なし。

成果物影響: stale な `tested_main_sha` で受入結果が land 拒否され、レポート・台帳の参照 SHA が再走値へ変わる。

深刻度: **must-fix**。推奨: **採用**（取得後の `git rev-parse main` と merge 対象を明記）。

### B2

T-732(b) の「受入 + land」粒度不採用と、現行の land 終了まで保持する記述が矛盾している。

根拠: [`docs/pegasus-runbook.md:794`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/docs/pegasus-runbook.md:794)、[`.claude/commands/dev-wave.md:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/.claude/commands/dev-wave.md:57)、`docs/decisions.md:11175`。実測なし。

成果物影響: lease 保持時間が延び、待ち wave の受理集合と land 済みレポート・台帳の件数が縮む。

深刻度: **must-fix**。推奨: **裁定へ**（既存 D239 を supersede するか、T-732(b) を再確認）。

### B3

P2(iii) の「claim・merge・受入を同一 script」は、tracked な正本・所有者がなく、docs-only 変更では実効性が保証されない。

根拠: [`s2_out.md:273`](/work/1/SFC/tanab/dev-wave-jobs/t730-t732-nul-lease/s2_out.md:273)、[`tools/wave_land_window.py:1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/tools/wave_land_window.py:1)。実測なし。

成果物影響: consumer が merge を省略して受入を投入し、受入結果が land 不能になる。

深刻度: **should-fix**。推奨: **裁定へ**（canonical waiter を追加するか、runbook の直接手順に縮める）。

### B4

既存の実待ち手は JSON を parse せず `*acquired*` を glob 判定し、`release` の論理状態も検査していない。

根拠: [`run_acceptance.sh:20`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t683-caller-closure/run_acceptance.sh:20)、[`tools/wave_land_window.py:768`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/tools/wave_land_window.py:768)、[`tools/wave_land_window.py:922`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/tools/wave_land_window.py:922)。実測なし。

成果物影響: `not-owner` や `unavailable` を成功扱いし、lease の重複受入または永久滞留を起こす。

深刻度: **must-fix**。推奨: **採用**（1 コマンド 1 値、JSON field と固定 literal の比較、pipeline 不使用）。

### B5

`git commit -F` だけでは merge commit の provenance trailer を保証せず、P2 は `DW-O17` の preflight・full-history 監査を欠く。

根拠: [`s2_out.md:269`](/work/1/SFC/tanab/dev-wave-jobs/t730-t732-nul-lease/s2_out.md:269)、[`docs/dev-wave/operations.md:92`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/docs/dev-wave/operations.md:92)。実測なし。

成果物影響: provenance 監査で land が拒否され、certified 選択・レポート・台帳が main に反映されない。

深刻度: **must-fix**。推奨: **採用**（既存 `DW-O17` を明示参照）。

### B6

TTL 失効と、2 回の受入走の間の claim・再 merge・release 境界が手順にない。

根拠: [`tools/wave_land_window.py:218`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/tools/wave_land_window.py:218)、[`docs/pegasus-runbook.md:806`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/docs/pegasus-runbook.md:806)、[`run_acceptance.sh:63`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t683-caller-closure/run_acceptance.sh:63)。実測なし。

成果物影響: 2 走目が別 holder と並行し、受入 report の main/tip 参照と台帳の受理集合が不整合になる。

深刻度: **must-fix**。推奨: **裁定へ**（fencing/renewal/再 claim を決める。lease 粒度を land まで黙って拡大しない）。

### B7

merge 後の `HEAD..main` 再検査と受入投入の間にも main が進む race が残る。

根拠: [`s2_out.md:278`](/work/1/SFC/tanab/dev-wave-jobs/t730-t732-nul-lease/s2_out.md:278)、[`tools/dev_wave_land.py:1335`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/tools/dev_wave_land.py:1335)。実測なし。

成果物影響: 受入全走は完了しても `stale-main` で land できず、再走により report・台帳の参照が変わる。

深刻度: **should-fix**。推奨: **裁定へ**（再走必須の境界か、追加の束縛を決める）。

### B8

`docs/failures.md` の F191/F196 は旧契約の「改訂は scope 外」を残し、F197/`69379268` と状態説明が食い違う。

根拠: [`docs/failures.md:4722`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/docs/failures.md:4722)、[`docs/failures.md:4809`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/docs/failures.md:4809)、[`docs/failures.md:4824`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/docs/failures.md:4824)。実測なし。

成果物影響: 後続 reviewer が T-732 を未裁定と誤認し、重複作業または受入延期を記録する。

深刻度: **should-fix**。推奨: **採用**（履歴本文は残し、superseded 注記を追記）。

### B9

`tools/check_docs.py` は `docs/pegasus-runbook.md` の byte／最長行 cap を登録していない。

根拠: [`tools/check_docs.py:168`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/tools/check_docs.py:168)、[`tools/check_docs.py:3986`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/tools/check_docs.py:3986)。静的計測のみ。

現在値は runbook **68,982 UTF-8 bytes、checker の文字数基準で最長 185 chars**。§7.3 は 1,165 bytes、提案 hunk は 936 bytes・最長 82 chars。runbook の予算上限は存在しないため、残余は **N/A**。`docs/dev-wave` の 10,625 / 9,566 / 1,000 bytes cap を runbook に流用してはならない。

成果物影響: checker が runbook の肥大を検出せず、文書受入の判定だけが過大に報告される。

深刻度: **should-fix**。推奨: **採用**（brief の「予算内」という表現を訂正し、予算引き上げは不採用）。

## 総括

- **NO-GO**
- must-fix は **5 件**（B1, B2, B4, B5, B6）。
- 段 4 で裁定すべき点:
  - `取り直し` を明示的 post-`acquired` 再読として T-732 の未実装と扱うか。
  - T-732(b) と既存 D239／runbook の「land 終了まで release」の優先順位。
  - canonical waiter を新設するか、外部 script を正本として認めるか。
  - JSON/rc 判定、merge provenance、TTL・2 走 lifecycle、main race の扱い。
