---
name: dev-wave
description: Run one Izanagi development wave through its brief, Codex planning and adversarial review, implementation, mutation and acceptance checks, recording, and bounded termination workflow. Use when the user asks to run, continue, or perform a dev-wave, or requests the repository's standard nine-stage development loop; do not use it for a CC synthesis campaign.
---

# Dev Wave

Izanagi の開発作業を 1 wave だけ進める。ユーザー向けの途中報告、裁定、最終報告は日本語で書く。

## 開始する

0. prompt 本文の最初の非空行が `AGENTS.md`「単独段 dispatch の例外」節と同一形式の宣言・射影を
   満たす場合は、以下 1〜5 を適用せず、宣言と射影が指示する資料だけを読む。宣言が欠落・形式不正・
   重複、または射影対象を読めない場合はこの例外を使わず、以下の手順に従う。
1. リポジトリ直下の `AGENTS.md` と `CLAUDE.md` を全文読み、依頼をクラス 3 として起動する。
2. ユーザーが指定した対象を優先する。対象がなければ worklog 末尾の「次の一手」から 1 件選ぶ。
3. `.claude/commands/dev-wave.md` を全文読む。同ファイルを 9 段状態機械、段 dispatch、条件 dispatch、
   巻き戻し、停止条件の共通 dispatcher として扱う。
4. `docs/skill-self-improvement.md` の発火 gate・routing・dev-wave 終端を読み、専用 handoff に
   `dev-wave 改善候補` 節を作る。
5. main では編集しない。既存の専用 Codex worktree があれば状態と対象を照合して再利用し、
   なければ local main の HEAD から `.codex/worktrees/` 配下に専用 branch/worktree を作る。

参照先の節は、dispatcher が指定する段または条件の直前に読み直す。記憶や本 Skill の要約で代用しない。
参照先が不在、読取不能、非一意、または期限後に条件成立が判明した場合は dispatcher どおり
fail-closed に停止または巻き戻す。

## Codex 向けに適合する

- `.claude/commands/dev-wave.md` の `$ARGUMENTS` はユーザーが本 Skill に渡した対象と読み替える。
  `/dev-wave` の次回起動案内は `$dev-wave` の新しい Codex turn と読み替える。
- 「親」は現在の Codex manager とする。ただし実装面では manager 自身を D95 の author 子に数えない。
  軽量版でも `docs/dev-wave/workers.md` と `docs/dev-wave/operations.md` に従う別の Codex 実装 worker に
  コードとテストを書かせ、manager は実装面を直接編集しない。
- worker は `DW-O01` の隔離された `codex exec` subprocess として起動する。read-only と
  workspace-write の sandbox 契約を普通の collaboration child や prompt 上の自己申告で代替しない。
- `.codex/role-adapters/*.json` と native profile は runtime blocked のまま起動しない。
  `role=author` は provenance 上の帰属であり、隔離済み native role の有効化を意味しない。
- Claude の PreToolUse hook が Codex で発火したと主張しない。`hooks/README.md` の保護契約を読み、
  Codex に未配線の防壁を手動で守る。
- `tools/dev_waves` の real supervisor は Codex Skill の実行面ではない。supervised manifest を渡されたら、
  明示的な Codex 対応が実装されるまで互換を装わず停止する。

## 1 wave を閉じる

dispatcher の段 1〜9 を順に実行し、自己再帰や次 wave の開始をしない。commit 前後の provenance 検査、
関連テスト、`python3 tools/check_codex_agents.py`、`python3 tools/check_docs.py` を省略しない。
push と remote branch 操作は人間に残す。

段 9 は dispatcher が指定する共通 land 契約だけに従い、Codex 固有の取り込み手順を重ねない。
成功しなければ main HEAD、停止理由、次タスク、再開用の `$dev-wave <対象>` を報告して終了する。
次 wave と race 後の再開は必ず新しい Codex context で始める。
