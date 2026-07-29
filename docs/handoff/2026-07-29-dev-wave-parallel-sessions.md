# dev-wave 並行セッション取り込み改善
- 目的: dev-wave a1 / a2 の並行実行で、他セッション所有物が安全な local main 取り込みを妨げない契約を Claude / Codex 共通面へ実装する
- 状態: 中断
- 最終更新: 2026-07-30 JST
- 基準コミット: fa4774cd5de5b81840984168d1ac12a15a3d16a6

## 完了した中間成果

- AGENTS.md / CLAUDE.md / Codex dev-wave Skill / Claude dispatcher / 自己改善契約を全文確認した
- worklog 末尾、Phase 3 の T-171 完了記録、全残 handoff を確認した
- 既存の専用 `codex/dev-wave-skill` worktree が clean かつ対象一致だったため、local main へ ff-only で揃えて再利用した
- main で別セッション所有の `.codex/worktrees/` と handoff が untracked として cleanliness を汚す症状を実測した
- worktree の submodule を初期化し、`tools/check_wave_startup.py --mode fresh` が green
- D69 / D70 / D74 / D85 / D94 / D95 / D97 と F48 / F50 / F51 を照合した
- 既存 checker は fresh/resume 開始条件と supervisor 専用 land を被覆するが、対話型 dev-wave の
  ownership-aware main cleanliness、受入基準 SHA、並行 main 前進後の再同期を機械検査しない
- 段 2 plan は rc=0 / 形式 gate pass。P1/P3 は強化採用、P2 の lock 無し案は棄却し、短時間
  common-git-dir lock と `9→6→7→8→9` の最大 3 回再同期を提案した
- 段 2 実行中に main が `fa4774c` から `180d3c1` へ先行 land し、Codex worktree と active handoff
  も増えた。別 session 所有物には触れていない

## 段 1 brief

- scope: Claude command と Codex Skill が共有する対話型 dev-wave の段 9 land 契約を並行 session 対応にする
- scope: repo-local worktree コンテナを ignore し、所有権を検査する local-main land helper と境界テストを追加する
- 確定裁定: ユーザーが `dev-wave a1` / `a2` の並行開発と、他 session 作業物が最終取り込みを妨げないことを要求した
- 不変条件: tracked/staged/submodule の main dirt、未知 untracked、未監査 commit、stale 受入結果は従来どおり拒否する
- 不変条件: 他 session の handoff / worktree を削除・stash・commit・上書きせず、rebase / force / push を使わない
- 不変条件: local main の変更は監査済み wave tip への fast-forward のみとする
- 成果物: 共通 dispatcher/reference、Claude/Codex 共用 land helper、境界テスト、D/F/phase/worklog 記録
- `(P1)` 親の provisional 裁定・攻撃対象: main の例外 dirt は形式が正しい他 session handoff と
  `.claude/worktrees/` / `.codex/worktrees/` コンテナだけに閉じ、その他 untracked は拒否する
- `(P2)` 親の provisional 裁定・攻撃対象: 長時間 lock は採らず、受入に使った main SHA の exact
  比較と ff-only の失敗で race を fail-closed にし、main 前進時は audit→merge→受入再走を有界反復する
- `(P3)` 親の provisional 裁定・攻撃対象: main 前進は「予期せぬ停止」から「監査対象の新 upstream」に
  再分類するが、競合解決と受入再走が完了するまで land しない
- 既存被覆: supervisor checker は main unchanged / dirty / ff-chain を、startup checker は fresh base を拒否する
- 純増検出力: active handoff だけの main を受理し、未知 dirt・stale accepted-main・non-FF・race loser を拒否する
- 実行時依存: helper は Python 標準ライブラリと allowlist 済み Git argv のみを使い、shell / network / remote を使わない
- 受入: 本 worktree で targeted pytest、mutation、`tools/run_tests.py` 全走、docs / Codex agent / provenance 検査
- 成果物影響: 未実装なら並行 wave が正常成果を作っても別 session の制御ファイルまたは先行 land で停止し、
  local main の開発台帳と次 wave の開始点へ反映できない
- 分割: read-only plan 1、敵対相談 2、workspace-write author 1、実装後 review 2。親は docs と統合を担当する

## 未完の作業と次の一手

- main 所有側で `6b64d21` の provenance 欠落を裁定する。規約上、子孫 commit・例外追加・
  checker 弱体化では閉じず、rebase / force は本 wave の権限外
- main 所有側で T-179 ledger の `cached > input`、負の reasoning token、非 null 非 object
  `info`、model / reasoning identity の扱いを裁定・修正し、negative test / mutation を追加する
- 新しい main SHA ができた fresh context で本 branch を再利用し、新 upstream の独立監査をやり直す
- GO 後だけ固定 SHA merge。main の T-179 を `F54` / worklog `(64)` に残し、T-186 を
  `F55` / `(65)` へ振り直す。worklog は単純併合で 100,000-byte 上限を超えるため rotation 契約を適用する
- merge 後に targeted / repository 全受入、docs / Codex agent / provenance、監査 commit 列を固定し、
  `DW-O23` を実行する

## 落とし穴・気づき

- 現行 `DW-S09` の「main が開始基準から予期せず動いていない」と、別 session の正常 land を両立させる明示的な再同期手順がない
- `.git/info/exclude` は `.claude/worktrees/` のみで `.codex/worktrees/` を除外しておらず、Codex worktree 作成自体が main の untracked cleanliness を壊す
- 他 session の handoff は生きた所有宣言なので、削除・commit・stash・巻き込みの対象にしてはならない
- `.gitignore` を広げると strict cleanliness consumer の受理集合まで変わるため不採用。例外は land helper 内で
  schema-valid handoff と Git admin に双方向登録された worktree に限定した

## dev-wave 改善候補

- 本 wave の対象そのもの: 並行 session が main を前進させた場合の再同期・再検証・直列化された ff-only land を共通 reference に追加する
- worktree コンテナの存在自体ではなく Git admin との双方向束縛を検証し、なりすまし path は拒否する
- 段 8 裁定: 上記候補は本 wave で実装済み。再開監査では追加の手順欠落を実測せず、
  新設防壁が main の未見 blocker を正しく停止したため、追加自己改善は行わない

## 段 2〜5 の確定結果

- 段 2 plan、段 3 の独立 2 review、段 4 の裁定を完了。長時間 lock、`.gitignore` 拡張、
  同一 wave 内の `9→6→7→8→9` back-edge は不採用とした
- race loser は `stale` / `busy` で停止し fresh context から既存 branch を再利用する。新 main の監査、
  wave-side merge、条件再評価、必要な受入再走を経ない再試行は禁止した
- 段 5 author が `tools/dev_wave_land.py`、境界テスト、`check_docs` の共通配線検査を実装した
- 親が `.claude/commands/dev-wave.md`、`.agents/skills/dev-wave/SKILL.md`、共通 reference を統合した
- `docs/dev-wave/**` は hard ceiling 24,000 bytes、`python3 tools/check_docs.py` は違反なし、
  land/check-docs 関連テストは 155 passed
- 作業中にも local main は複数回先行し、並行 session の handoff / worktree は非接触で維持している
- 段 6 の独立 2 review はともに形式 gate pass / `NO-GO`。ignored control container の検査抜け、
  lock 前検査 race、effective config 漏れ、gitlink sync 後の回復不能、暫定 checker allowance などを
  real と裁定し、相互依存する 4 file の単一 Codex fix 単位へ戻す
- fix 子は採用 must-fix 9 件を所有 4 file だけで修正。子実測は land 29、checker 143、合同 172、
  plain-runner/meta 175 passed、docs/Codex agent/compile/diff check green。親受入と焦点再レビューは未完
- 焦点再レビューは 4 closed / 4 partial / 1 regressed で `NO-GO`。ignored sibling 過剰拒否、
  mutation 直前 snapshot、削除 gitlink、別 command 構文、再受入接続の 5 点を第 2 fix に採用した
- 第 2 fix 子は残余 5 点を所有 4 file だけで修正。子実測は land 32、checker 145、合同 177、
  plain-runner/meta 180 passed、docs/Codex agent/compile/diff check green。第 2 焦点レビューは未完
- 第 2 焦点レビューは 3 closed / 1 partial / 1 regressed で `NO-GO`。gitlink→通常 file と
  interpreter/Git global option の 2 点だけを最終 fix round 3/3 に採用した
- 最終 fix 子は子実測 land 34、checker 146、合同 180、plain-runner/meta 183 passed。最終レビューは
  gitlink closed、checker の合成 false-positive だけ `NO-GO`。後者は現 living route/成果物へ影響せず
  exact topology gate も独立に残るため、fix 上限後の親裁定で backlog とした
- 親環境でも関連 pytest 180、plain-runner/meta 183 passed。`check_docs`、Codex agent、
  py_compile、staged diff check は green。次は統合 commit 上の M1〜M13 と全受入
- 実装 commit `43c4ec4` 上で M1〜M13 は 13/13 KILLED、SURVIVED 0、全回 source bytes 復元。
  復元後の関連 pytest 180 と `check_docs` も green。M13 の再照準は mutation ledger に erratum 固定
- mutation ledger commit `16e418b` の後、並行 main `0912975` を merge commit `08adb89` で
  conflict なく統合。main 側の RuleOps / rung 記録と本 wave の checker 契約を両方保持し、
  provenance は導入時点から 531 commits green
- 段 7 で [T-186] / D100 / F54 / worklog (64) を採番。別 session 所有の main 側 handoff と
  `.codex/worktrees/` は削除・stash・commit せず残置した
- 強制終了後の fresh context で再開し、wave tip `c63a005` と最新 main `7be05ef` の両 commit 列を固定。
  read-only Codex に新 upstream を独立監査させ、validator green / 結論 `NO-GO`
- 親が main で provenance を再走し、`6b64d21` の trailer 欠落を
  `533 件中 1 違反` / rc=1 と再現。T-179 ledger の token 関係制約欠落と非 null 非 object
  `info` 黙殺も実コードで real と確認した
- 段 9 は `DW-STOP`。固定 SHA `7be05ef` を wave へ merge せず、main も変更していない。
  裁定正本は
  `output/insights/2026-07-29_dev-wave-parallel-land/s9-main-resync-adjudication.md`
- 停止記録反映後の branch 受入は targeted 188 passed、repository 全走
  **3725 passed / 18 skipped**。`check_docs` / `check_codex_agents` / py_compile /
  `git diff --check` は green、branch provenance は 533 件・違反なし
- ユーザー報告後の fresh context で再開。wave tip `59c9484`、latest main `ff82133`、
  merge-base `0912975`、左右 commit 数 `5 / 14` を固定し、resume startup gate は green
- read-only Codex の latest-main 独立監査は exit 0 / validator green / `NO-GO`。
  provenance 欠落と `cached > input` は closed、負の reasoning token と非 null 非 object
  `info` の黙殺は partial のままと判定した
- 親が main の ledger 実装・negative tests・T-179 凍結記録を照合し、残る2件を real と再裁定。
  強制終了前の再開条件を緩めず `ff82133` は merge せず、local main も変更していない
- main 側の採番進行により、本 wave の生きた記録候補は
  `T-188 / D102 / F55 / worklog (67)`。また main の hardened `DW-O17` と wave の
  `DW-O23` を単純 union すると reference aggregate が 37 bytes超過するため、再同期時に
  安全義務を保つ意味保存縮約が必要
- 最新の監査・親裁定は
  `output/insights/2026-07-29_dev-wave-parallel-land/s9-main-resync2-{audit,adjudication}.md`
