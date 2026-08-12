---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-t1005-acceptance-flake-attribution
seq: 2
---

## 新規

### {{F:acceptance-flake-budget-margin}}. launcher テストの wall 予算は 48 並列下で余裕がほぼゼロで、判定に使った情報は保存されていなかった [テストフレーク] [資源競合] [恒真ゲート]

- 事象: ([T-1005] 診断 wave、2026-08-13) F57 の族について、2026-08-13 の受入 8 走を一次資料に
  機序を特定した。走 A (`acceptance.log`、bnode130、request 908484) の失敗 21 件すべてに
  receipt の job 側 wall clock が記録されており、実測は **3.0099 / 3.0460 / 3.1160 / 3.1369 /
  3.2324 / 3.2650 …** 秒。テストが渡す予算は **3.0 秒ちょうど**で、超過幅は
  **0.010〜0.265 秒 (0.3%〜9%)** しかない。
- 根本原因: 次の 3 つが重なっている。
- (1) **余裕の欠如**: 48 並列下では launcher の job 全体所要が予算の縁に常時張り付く。
  必要な摂動が極小なので、負荷指標に現れる必要がない。F57 既載の未説明の性質
  (失敗 node が毎回移動する / 単独再走で非再現 / loadavg 0.80 でも 17.42 でも発火 /
  件数が 1〜21 と振れる) はすべてこれで説明できる。
- (2) **判定量が失敗報告に現れない**: wall gate は **job clock**
  (`tools/codex_worker_launch.py:1244`、起点は `:35` の module import 時刻) で判定するが、
  失敗診断が印字する `wall_clock_s` は **attempt clock** (`:1540`、起点 `:1347`) である。
  同じ名前の別量が出るため「予算 3 秒に対し 0.716 秒で wall 超過」という不可能に見える記録になる。
- (3) **近接原因を事後に区別できない**: `codex_exit_code=-9` は外部 SIGKILL と識別不能、
  `evidence_forced_stop` は代入されるだけで receipt にも受理判定にも出ない (`:349` / `:1497`)、
  `residual=None` の出所は 4 つ以上あって区別されない、phase 別時刻も記録されない。
  実装は `if/elif` で複数原因を単一 `limit_trigger` へ縮約し (`:1461-1475`)、
  `limit_trigger` が立つと evidence deadline を見ずに break する (`:1487-1499`)。
  **F57 が 20 回以上「未確定」だったのは解析不足ではなく観測設計の帰結である。**
- 恒久対応: 未実施。本 wave は診断のみで実装差分ゼロ。選択肢と親推奨を
  `output/insights/2026-08-13_t1005-acceptance-flake-attribution/package.md` の R1〜R3 で
  裁定へ返した。第 1 手は計装 (発火した latch の識別・強制停止の理由・`residual=None` の出所・
  phase 別時刻・失敗時 receipt の保存) であり、F57 既載の [T-190] と同じ対象に対して
  **必要 field を初めて具体化した**。予算是正は test file 内に限り launcher parser の既定を
  触らないこと、壊れる 12 nodeid の個別対応が要ることを同 package に列挙した。
- 再発検知: 受入全走の `receipt_actuals.wall_clock_s` が予算の 90% を超える件数。
  計装が入るまでは、失敗 record の `receipt_actuals.wall_clock_s` と予算の比を手で見る。

### {{F:landed-handoff-blocks-startup-check}}. main に landed した handoff が、背景 job の wave をすべて起動時 rc=1 にする [恒真ゲート] [手順漏れ]

- 事象: (2026-08-13, [T-1005] 起動時) `tools/check_wave_startup.py --external-handoff` が
  `worktree-local handoff remains (2026-08-13-known-red-octopus.md)` で rc=1 になった。
  当該 file は別 wave が main へ **tracked** で land したものであり、worktree 固有の残骸ではない。
- 根本原因: `_check_worktree_handoff` は `docs/handoff` を列挙し README 以外を一律に残骸と扱い、
  tracked/untracked を区別しない。一方 land は `docs/handoff` 直下の削除を拒む (rc=21) ため、
  **wave 側では解消できない。** 背景 job は `DW-O20` により `--external-handoff` が必須で、
  この flag は同検査を必ず起動するので、**landed handoff が 1 つ残っている限り
  以後の背景 job wave はすべて起動時 rc=1 になる。**
- 恒久対応: 未実施。{{T:startup-check-excludes-tracked-handoff}} として起票し、
  checker 側で tracked file を除外する案を親推奨として裁定へ返した (package の R4)。
- 再発検知: `git ls-files docs/handoff/` が README.md 以外を返すこと。

## 再発

### F57

- **再発: 2026-08-13 ([T-1005] の帰属調査)。** 新規 F ではなく本族の機序特定として記録する。
  2026-08-13 の受入 8 走で同一 file の失敗が **21 / 8 / 3 / 0 件**と振れた
  (既載の再発はすべて 1〜2 件で、**1 桁大きいのは初出**)。
  機序と判定不能の理由は {{F:acceptance-flake-budget-margin}} に記録した。
  **新しい情報は 3 点。** (i) 予算超過幅が 0.3%〜9% しかないこと (縁張り付き) を
  一次資料の `receipt_actuals.wall_clock_s` で初めて実測した。
  (ii) 「バーストの述語が均一なのは 1 原因の証拠」ではないこと — 実装が複数原因を単一 field へ
  縮約するため、均一性は selection effect でも生じる。
  (iii) 並行 codex 子は判別子でない — 同じ窓で codex 子は**緑の走とも重なっていた**。
  これは [T-139] land2 の K5 (受入 lease を他 wave の codex 子まで広げるか) の
  親推奨「現状維持」を支持する実測である。
  本 wave の差分は docs のみで launcher 実装へ到達しえず、`DW-O18` により帰属しない。
