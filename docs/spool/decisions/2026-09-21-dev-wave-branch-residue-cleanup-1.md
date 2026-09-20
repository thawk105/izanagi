---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-21
wave: dev-wave-branch-residue-cleanup
seq: 1
---

## {{D:cleanup-force-delete-and-child-branch}}. D204 の狭い例外を 2 経路へ広げる — dev-wave 段 9 は統合証明済みの Codex 子 branch を履歴退避後に `-D` し、`/cleanup-branches` は裁定条件つきで `-D` する

**決定 (ユーザー裁定 2026-09-21 00:40 頃「`/cleanup-branches` は branch の `-D` をしてよい / 残骸 155 本は消す / 自己改善 wave で再発を防ぐ」に基づく):**
D204 (branch 削除は対象を特定したユーザー指示があるときだけ) の狭い恒久例外を、D703 (自 wave の branch、`-d` のみ) と
D2163 (manifest 登録済み子 worktree、branch は残す) から次の 2 経路へ広げる。権限の根拠はこのユーザー指定であり、manifest は対象を
束縛する信頼済み入力 (未署名、作成世代を証明しない) であって権限の根拠ではない。

- **経路 1 — dev-wave 段 9 の自己撤去 (`DW-O28`、`tools/dev_wave_cleanup.py remove-child`):** manifest に exact path で登録された
  子木のうち integration を証明できたもの (子 HEAD reflog の全 commit が main の祖先、または所有 path の tree entry が main と一致) は、
  **manifest 現行 branch** を tool 内の専用経路で `git branch -D` する。順序は、backup phase (unlock・detach の前) で子 HEAD が main の祖先でなければ
  `refs/heads/<name> ^<main tip>` の履歴を証拠 dir の `history.bundle` へ退避し verify (失敗は rc=30 で木・admin・branch を保持) →
  木と admin の撤去と不在確認 → 証明時の main tip・子 tip の再照合 → `-D` → 削除後の不在確認 → receipt。HEAD が main の祖先なら履歴は main にあり
  bundle は作らない。detached 子は渡せる ref が無いので bundle を作らない (木の撤去で reflog は失われる — 現行どおり)。
  共通 git runner は `-D` を実行前に拒否し、wave 本体の branch は D703 のまま `-d` だけ。証明不能 (rc=20) の子は木も branch も残し、
  理由を worklog へ記録する (現行どおり)。同じ木で切り替えた旧 fix branch は manifest に無いので経路 1 の対象外 (経路 2 が回収する)。
- **経路 2 — `/cleanup-branches` の ahead>0 branch:** 次を全部満たすときだけ `-D` する。(i) 所有 wave の完了 entry が `docs/worklog.md` か
  `docs/archive/` にある、(ii) 稼働 wave・locked checkout・棚卸し後の新規でない、(iii) 全対象を runbook §7.2 の repo 外 dir へ
  `git bundle create` + `verify` + `list-heads` 一致で退避済み、(iv) §1 の rescue gate (`check_branch_rescue.py --ledger-check`) を同じ候補集合で
  1 回走らせ JSON を同 dir に保存済み。台帳への損失 commit 転記は cleanup 実行内では行わず (F747 の default-deny は不変、台帳の追記条件は削除後の
  到達不能)、§5 で別 dev-wave へ引き渡す。ahead=0 の `-d` 経路 (D2042) は不変。削除直前の再確認に並走 wave が入れた「非施錠」を、対象 checkout の
  `.git/worktrees/<name>/locked` 不在検査として具体化する (棚卸し後に別 session が lock した実例への対応)。別の裁定で保持と名指しされた対象は、その裁定の更新なしに経路 2 で消さない。
- **台帳:** 2026-09-21 00:46 の削除で恒久 ref から到達不能になった損失 commit 227 件と、同日の照合で通知された削除閉包外の未記帳 21 件を、
  既存 schema のまま `status=pending`・`resolution_note=null` で `docs/unreachable-object-ledger.md` へ転記した (bundle の所在・sha256 は
  `assessment_reason` に置く)。元 report は消失しており `assessment_report_sha256` は候補なし再走 report のもの。`accepted-loss` への遷移は
  人間の明示受容が要るので行わない。台帳「覆わない範囲 2 (`DW-O28` の自動撤去)」は据え置く。
- **byte 予算:** `.claude/commands/cleanup-branches.md` の予算を 6,204 から 7,058 bytes へ上げる (完成本文 7,055 = 並走 wave の land 版 6,201 に
  §0/§2/§3/§5 の改訂 854 bytes、余白 3 は D2043 の 6,201 / 6,204 と同じ幅。余白 0 だと 1 byte 追加の負例が SHA と予算の 2 件で落ち、
  test の期待 1 件と食い違う — 焦点走で実測)。最長行予算 110 は不変。

**維持・supersede の対応:**

| 既存裁定 | supersede する文 | 維持する文 |
|---|---|---|
| D204 | — (狭い例外を 2 経路追加) | その他の branch は対象特定の都度指示、恒久 permission rule の常設禁止、remote/push 境界 |
| D703 | 例外対象を「wave 本体だけ」に限る部分 | wave 本体は tested tip の main 祖先性 + `-d` のみ |
| D2163 | 「子 branch は削除しない」、および「登録専用 CLI・履歴 pack・子 branch の `-d` は固定費削減に不要」の却下のうち履歴退避 (子 branch 削除に必要な `history.bundle` に限る) と子 branch 削除 | manifest exact path・非占有・統合条件・証拠 dir 退避・producer 終端・判定不能は保持・周期 sweep なし・登録専用 CLI の却下 |
| D2042 | 決定「削除の述語の連言と閾値は変えない」のうち、branch 側の述語 (`ahead=0` → `-d`) に裁定条件つきの `-D` 分岐を足す部分 (command §2 の実文「`ahead=0` のみ `-d` (`-D` 禁止)」が対応箇所) | 安い条件 → 高い条件の順序、全 surviving status 保存、破壊操作の直列化、`ahead=0` の `-d` 経路 |

**理由:**
- 2026-09-21 00:20〜00:46 JST の `/cleanup-branches` (cleanup session 約 26 分) の観測を独立に書くと: 棚卸し時の branch 165 本のうち
  `ahead=0` で消せたのは 4 本。ユーザー裁定時に「消す」と指示された残骸は 155 本 (指示時の数)。削除実績は 140 本 (bundle 退避後 `-D`)、
  除外 24 本 (稼働 11 / locked 7 / HEAD 1h 以内 1 / 棚卸し後の新規 5)。約 40 wave 相当は名前からの概算で wave 単位の対応表は無く、
  原因別の比率も未確定。機構としては、`DW-S05-A` の patch 統合が子 commit を main の祖先にしないため Codex 子 (author / fix / probe / unit) の
  branch が恒久に `ahead>0` で残る経路がある。09-17 の一括掃除も同じ壁で「Codex 子木は裁定へ」で止まっていた。
- D2163 が子 branch の削除を「固定費削減に不要」と却下した根拠は worktree と handoff の走査費用であり、branch の蓄積が掃除の摩擦
  (棚卸し 165 本 11 秒 + cherry 156 本 53 秒 + cleanup session 約 26 分) になることは当時未見だった。branch 残骸は worktree 残骸と違い land を
  止めない (F26 は worktree) ので、改訂の理由はこの摩擦に限る。
- 「内容統合 (所有 path の tree 一致) は履歴保全ではない」— 子 HEAD の祖先にだけ存在する中間版 (追加して削除した所有外 file 等) は、
  所有 path 一致で通っても main にも `committed.patch` にも無い。段 3 lens A が静的反例で示した。bundle 退避で内容は復元でき、
  Git object の延命は主張しない (`object_retention_provided: false` と同じ立場)。
- 経路 2 で「所有 wave が land 済み」を内容の全着地ではなく完了 entry で判定するのは、今回の 140 本と同じ条件 (bundle 退避 + 台帳転記が
  保全を担う) をそのまま条文にするためである。判定不能は保持。

**却下した選択肢:**
- 証明不能 (rc=20) の子を bundle 退避して `-D` する、または `/cleanup-branches` へ名指しで引き渡す — 「統合済みを条件」とする D2163 を
  緩める。名指し引き渡しは現行の「理由を worklog へ記録」で足りる。
- 段 9 の `-D` を reflog 全 commit が main 祖先の子だけに限る — Codex author は patch 統合なので祖先にならず、ほぼ全ての子 branch が残る。
- cleanup 実行内で台帳へ pending 転記してから削除する (段 2 案) — 台帳契約 (削除後に到達不能になった object) と land の tracked dirt 拒否と
  F747 に同時に衝突し、削除失敗時に起きていない喪失を記録する。
- `pending` の `resolution_note` を非 null に広げる schema 改訂 — bundle 情報は `assessment_reason` で足り、validator・test・文書 pin の
  変更は不要 (段 3 lens B)。
- 損失 227 件のうち監査に通知された 66 件だけ転記する — 台帳契約は削除閉包の全 commit を対象とする。監査非通知 161 件は「変更 path が
  main か他 branch tip に存在する等で報告対象外」であって内容着地の証明ではない (段 3 lens A)。
- manifest に旧 fix branch を記録して段 9 で消す — manifest schema と `DW-S05-A` の改訂を要し本 wave の範囲外。次の一手へ。
