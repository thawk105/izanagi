---
description: 開発標準ループ (ハイブリッド) を 1 wave 実行 — brief → codex プラン起草 → 敵対相談 → 並列実行 → レビュー → fix → 記録
argument-hint: [任意: 対象タスク。省略時は worklog 末尾の「次の一手」から選ぶ]
disable-model-invocation: true
---

あなたは izanagi の開発 wave の manager である。これは開発作業のループであり、
CC 合成 campaign の実行ループではない。

## 入力と開始

- 第一声から進捗、裁定、最終報告、`result:` まで、ユーザー向け出力はすべて日本語にする。
- `CLAUDE.md` のクラス 3 起動手順を実行し、引数があれば対象にする: $ARGUMENTS
- wave 開始時に `docs/skill-self-improvement.md` の「発火 gate」と「dev-wave」を読み、
  専用 handoff に「dev-wave 改善候補」節を作る。
- 無人継続の外部 supervisor は、最初の `claude -p` spawn 前に
  `docs/dev-wave/core.md` の `DW-CTX` を読む。

## 読み込み契約

以下の参照節は command の命令の一部である。wave 開始時、段 1〜9 の各段へ入る直前、
および条件を成立させる操作の直前に条件を再評価し、表で指定した節を読む。
前段の推測や F/D 番号の記憶で代用してはならない。参照先が不在・読めない・節が一意でない場合、
期限までに読了していない場合は、その段や操作へ進まず fail-closed で停止する。

条件には最遅読了段がある。`DW-O08`、`DW-O09`、`DW-O10` は段 1 brief 前、
`DW-O13` は段 2 プラン前が期限である。期限後に成立が判明したら、それまでの成果物を invalidate し、
前者は段 1 brief、後者は段 2 から再実行する。巻き戻し後も段・条件を再評価し、旧 brief、plan、
review を流用してはならない。

## 凍結境界

- 状態機械は段 1〜9。通常遷移は `1→2→3→4→5→6→7→8→9` とする。
- 実装子はコードとテストだけを編集し、docs 編集と commit をしない。親だけが統合 commit、
  変異 matrix、受入全走、記録、local main 取り込みを行う。
- push と remote branch 操作はしない。local main 取り込みは全条件成立時の `--ff-only` だけとする。
- 規定の停止条件、検査赤、権限・scope・参照の不整合を迂回しない。
- 1 wave は 1 fresh context とし、command を自己再帰させず、段 9 後に新しい wave を始めない。

## 9 段状態機械

1. **brief (親):** scope、裁定、不変条件、成果物、分割方針を確定する。
2. **プラン起草 (codex):** read-only codex に file:line 粒度の案を作らせる。
3. **敵対相談 (codex 並列):** plan と親 brief を異なるレンズで攻撃させる。
4. **裁定 (親):** real/refuted、採否、scope、plan v2、変異事前登録を確定する。
   「実装しない」と裁定した場合だけ段 5・6 を飛ばし、`4→7→8→9` とする。
5. **実装 (codex 並列):** 所有を分離し、実装子の権限境界を守って実装する。
6. **レビュー・fix (codex 並列):** 敵対レビュー 2 本、fix、変異 matrix、受入再走を行う。
7. **記録 (親):** worklog、insights、decisions、commit、記録後検査を完了する。
8. **スキル自己改善 (親):** 共有契約で候補を routing する。候補ゼロなら無言で通過する。
9. **終端・local main (親):** 監査済み成果だけを条件付きで ff-only 取り込みして終了する。

## 段 dispatch

| 入る直前 | 必ず読む節 |
|---|---|
| wave 開始 | `docs/dev-wave/core.md`: `DW-C00`, `DW-CTX`, `DW-STOP` |
| 段 1 | `docs/dev-wave/core.md`: `DW-S01`, `DW-G01`, `DW-G02`, `DW-G03`, `DW-G04`, `DW-G05` |
| 段 2 preflight | `docs/dev-wave/workers.md`: `DW-S02`; `docs/dev-wave/operations.md`: `DW-O01`, `DW-O02`, `DW-O03`, `DW-O05` |
| 段 3 preflight | `docs/dev-wave/workers.md`: `DW-S03`; `docs/dev-wave/operations.md`: `DW-O01`, `DW-O02`, `DW-O03`, `DW-O05`, `DW-O13` |
| 段 4 | `docs/dev-wave/core.md`: `DW-S04`, `DW-G01`, `DW-G02`, `DW-G03`, `DW-G04`, `DW-G05`; `docs/dev-wave/mutation.md`: `DW-M01` |
| 段 5 | `docs/dev-wave/workers.md`: `DW-S05-A`, `DW-S05-B`, `DW-S05-C`; 成立した条件の `docs/dev-wave/operations.md`: `DW-O01`〜`DW-O20` |
| 段 6 | `docs/dev-wave/workers.md`: `DW-S05-A`, `DW-S05-B`, `DW-S05-C` |
| 段 6 | `docs/dev-wave/workers.md`: `DW-S06-A`, `DW-S06-B`, `DW-S06-C` |
| 段 6 | `docs/dev-wave/core.md`: `DW-G05` |
| 段 6 | `docs/dev-wave/mutation.md`: `DW-M02`, `DW-M03`, `DW-M04`, `DW-M05`, `DW-M06`, `DW-M07`, `DW-M08` |
| 段 6 | 成立した全 `docs/dev-wave/operations.md`: `DW-O01`〜`DW-O20` |
| 段 7 | `docs/dev-wave/core.md`: `DW-S07`; 成立した条件の `docs/dev-wave/operations.md`: `DW-O12`, `DW-O17`, `DW-O18`, `DW-O19` |
| 段 8 preflight | `docs/dev-wave/core.md`: `DW-S08`; `docs/skill-self-improvement.md` の全節 |
| 段 8 preflight | commit するなら `docs/dev-wave/operations.md`: `DW-O17`; 防護パス message なら `DW-O04` |
| 段 9 | `docs/dev-wave/core.md`: `DW-S09`, `DW-CTX`, `DW-STOP` |

段 6 で fix を codex へ再投する子は、段 5 の実装子契約 `DW-S05-A`、`DW-S05-B`、`DW-S05-C` を
全文継承する。段 6 時点で成立している全条件の `DW-Oxx` も、fix 操作の直前に読む。

## 条件 dispatch

| # | 発火条件 | 読む節 |
|---|---|---|
| 01 | codex subprocess を起動する直前 | `docs/dev-wave/operations.md`: `DW-O01`（F23/F24） |
| 02 | prompt・log・patch を作る直前 | `docs/dev-wave/operations.md`: `DW-O02` |
| 03 | prompt に防護パス文字列を含めて作る直前 | `docs/dev-wave/operations.md`: `DW-O03` |
| 04 | commit message に防護パス文字列を含めて作る直前 | `docs/dev-wave/operations.md`: `DW-O04` |
| 05 | read-only codex に相談・レビューさせる直前 | `docs/dev-wave/operations.md`: `DW-O05` |
| 06 | workspace-write 子で submodule 系テストを扱う直前 | `docs/dev-wave/operations.md`: `DW-O06` |
| 07 | task-run pilot が有効な wave の開始前 | `docs/dev-wave/operations.md`: `DW-O07` |
| 08 | freeze / oracle gate / proof chain に触る可能性が判明 | `docs/dev-wave/operations.md`: `DW-O08`（最遅: 段 1 前） |
| 09 | 凍結成果物の bytes を変えうる可能性が判明 | `docs/dev-wave/operations.md`: `DW-O09`（最遅: 段 1 前） |
| 10 | 09 が成立し producer の出力 bytes が変わりうる | `docs/dev-wave/operations.md`: `DW-O10`（最遅: 段 1 前） |
| 11 | ファイル削除を伴うと判明 | `docs/dev-wave/operations.md`: `DW-O11` |
| 12 | 裁定手順と実行手順が食い違った時点 | `docs/dev-wave/operations.md`: `DW-O12` |
| 13 | gate・検証を新設する可能性が生じた時点 | `docs/dev-wave/operations.md`: `DW-O13`（最遅: 段 2 前） |
| 14 | no-touch 対象へ monkeypatch を検討する直前 | `docs/dev-wave/operations.md`: `DW-O14` |
| 15 | fix 後に変異を走らせる直前 | `docs/dev-wave/operations.md`: `DW-O15`; `docs/dev-wave/mutation.md`: `DW-M07` |
| 16 | fix 後の焦点再レビューを行う直前 | `docs/dev-wave/operations.md`: `DW-O16` |
| 17 | commit を作る直前 | `docs/dev-wave/operations.md`: `DW-O17` |
| 18 | 親がテスト・受入を走らせる直前 | `docs/dev-wave/operations.md`: `DW-O18` |
| 19 | tracked file を一時変異する直前 | `docs/dev-wave/operations.md`: `DW-O19` |
| 20 | clean-tree gate を worktree で走らせる直前 | `docs/dev-wave/operations.md`: `DW-O20` |
| 21 | 無人継続を構成し最初の process を起動する前 | `docs/dev-wave/core.md`: `DW-CTX` |
| 22 | supervisor を使用する前 | `docs/dev-wave/core.md`: `DW-CTX` |

各条件の詳細は参照節だけを正本とし、事故の物語は `docs/failures.md` の F 番号へ置く。
入口や reference へ同じ物語を再掲しない。

## 終端

段 8 で許される自動修正も、専用 commit、予算検査、関連検査を完了してから段 9 の
「本 wave の監査済み commit 集合」に含める。段 9 の条件が一つでも欠ければ rebase、force、
他 session 差分の巻き込みをせず停止し、main HEAD、次タスク、停止理由、再開コマンドを報告する。
