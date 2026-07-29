# dev-wave 並行セッション取り込み改善
- 目的: dev-wave a1 / a2 の並行実行で、他セッション所有物が安全な local main 取り込みを妨げない契約を Claude / Codex 共通面へ実装する
- 状態: 作業中
- 最終更新: 2026-07-29
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

- 段 6 の Git race / trust と契約整合 / scope の 2 レンズで統合差分を攻撃する
- real 所見があれば所有を限定した Codex fix 子へ戻し、焦点再レビューを行う
- 統合 commit 後に事前登録 M1〜M13、全受入、記録、最新 main 再監査、helper land を行う

## 落とし穴・気づき

- 現行 `DW-S09` の「main が開始基準から予期せず動いていない」と、別 session の正常 land を両立させる明示的な再同期手順がない
- `.git/info/exclude` は `.claude/worktrees/` のみで `.codex/worktrees/` を除外しておらず、Codex worktree 作成自体が main の untracked cleanliness を壊す
- 他 session の handoff は生きた所有宣言なので、削除・commit・stash・巻き込みの対象にしてはならない
- `.gitignore` を広げると strict cleanliness consumer の受理集合まで変わるため不採用。例外は land helper 内で
  schema-valid handoff と Git admin に双方向登録された worktree に限定した

## dev-wave 改善候補

- 本 wave の対象そのもの: 並行 session が main を前進させた場合の再同期・再検証・直列化された ff-only land を共通 reference に追加する
- worktree コンテナの存在自体ではなく Git admin との双方向束縛を検証し、なりすまし path は拒否する

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
