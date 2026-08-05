# 段 4 裁定 — [T-495]

## 総括

段 3 の 2 レンズが出した所見は**すべて real**、refuted はゼロ。**すべて採用**する。
親の中核結論 (経路 = 対話セッションの `git branch -D` + 直前のユーザー明示承認) は
両レンズとも崩せなかったが、**周辺の断定 4 か所と provisional 裁定 2 件は書き直しが必要**である。

## 所見の裁定

| # | 所見 | 出所 | 判定 | 措置 |
|---|---|---|---|---|
| 1 | 「唯一の経路」と断定できない。同名 ref の再作成→再削除は同じ最終状態を作れ、削除で当該 ref の reflog も消えるため排除不能 | A | real | 表現を「直接観測された元 ref の削除経路」に限定 |
| 2 | 観測窓は 22:58 JST でなく **22:55 JST 存在 (13:55:33Z) → 08:07 JST 不在 (23:07:42Z)** | A | real | 一次資料の値へ訂正 |
| 3 | 親は「検査があった」をセッションの自己申告だけで支えていた。**一次資料は `output/insights/2026-07-30_dev-wave-improve-wave/s9-t193-ruling.md`** で、2026-08-01 のユーザー裁定が「main を正本にする。branch の実装 (50 path) は land せず廃棄する」と明記 | A | real | 根拠を一次資料へ差し替え。**削除は裁定済みの廃棄の執行だった**と書ける |
| 4 | 「コード 3 ファイル」は不正確。main 不在は **7 path** (実装・補助 5 + テスト 2)。内容差 16、同一 37 | A | real | 数値を訂正 (現 main `18149bcf` で再実測して一致) |
| 5 | 「拾う中身ゼロ」は言い過ぎ。`Group Name` 束縛の知見は [T-222] へ分離され未移植 (`_accounting_present` は今も Request ID / Started / Ended / Elapse だけ) | A | real | 「直接 land / cherry-pick すべき実装はない」へ限定 |
| 6 | **(P1) の「発火余地がなかった」は誤り。** `77db32c` は削除時点で durable ref から到達不能になった (`rescue-t213` 作成は **32 時間 37 分後**の 2026-08-05 07:49:10 JST)。到達性ベースの防壁なら本件でも発火した | A/B | real | (P1) を書き直す |
| 7 | **(P4) の「未承認 0 件だから不要」は成立しない。** 母集団は surviving transcript のみで、手動 shell・別 clone・別ホスト・削除済み reflog・GC 後 object を覆わない。欠測はランダムでもない | B | real | 裁定語を「却下」→「証拠不足で保留、rescue-first 案を保持」へ |
| 8 | 事後監査の穴を確定: 既存ファイルの編集のみ・削除・同名別内容・GC prune 後はいずれも**検出不能**。既定除外は `docs/spool/` と `docs/archive/`。入口は `/cleanup-branches` の 1 か所だけで定期実行はない | B | real | 裁定パッケージの根拠に採用 |
| 9 | 親の「22 件すべてで警告が鳴った」は不正確。**22 は override 成功 call 数**で、実際の count 警告は現 repo 5 件 (旧 repo 3 件を足して 8 件)。8 件すべて tip が main と同一か ancestor = 偽陽性で、救った例はゼロ | B | real | (P2) の数値を訂正。警告疲労の懸念自体は崩れず (rulings session は初回警告後、後続 17 worktree を最初から `discard_changes:true` で除去していた) |
| 10 | `git branch -D` が guard を通るのは `_GIT_READ_SUBS` のためではなく、**防護パス語を含まないコマンドが `decide()` の fast path で即許可されるため** (`hooks/guard_bash.py:1532-1543`)。集合から `branch` を外しても直らない | s2 | real | 機序の記述を訂正 |
| 11 | 一律の ref 削除禁止は `tools/codex_reasoning_ab.py` の隔離 snapshot sealing (`update-ref -d` + prune) を偽陽性にする。保護は canonical common-dir の `refs/heads/*` に絞る必要がある | s2 | real | 裁定パッケージの設計制約に採用 |
| 12 | `reference-transaction` hook が最も広い設置面だが、`.git/config` は tracked でなく、dev-wave の helper が `core.hooksPath=/dev/null` を明示するため repo 内から強制できない | s2/B | real | scope 外 (環境 owner) として明示 |
| 13 | supervised dev-wave (`tools/dev_waves/git_state.py`) は Git allowlist に branch 削除 API を持たず既に閉じている | s2 | real | 現状追加対応不要と記録 |

## 実装の裁定

**実装しない。** 根拠は 3 つ。

1. T-495 の起票文が「防壁の要否と形を**裁定へ返す**」と定めている。
2. `DW-G03` の独立 2 例が無い (所見 7 は「0 件を根拠にするな」であって「2 例目がある」ではない。
   両レンズとも 2 例目を見つけられなかった)。
3. 所見 12 と B の scope 表により、実効性のある防壁は **repo / harness / 環境の 3 owner** に跨る。
   repo 層だけを実装して「branch 削除を保護した」と書くのは実装したふりになる。

したがって `4→7→8→9` とする。**実装差分がないため、変異事前登録 (`DW-M01`) の対象は無く、
変異 matrix と受入全走は対象外**である。

## 成果物影響 (DW-G05)

本 wave は成果物 (certified 選択、材料レポート、試行台帳) の値・受理集合・参照を一切変えない。
台帳に入るのは [T-495] の完了と経路特定の結論だけである。実装しないことによる成果物の劣化もない —
消えた `77db32c` は `rescue-t213` に保護され、その内容は 2026-08-01 のユーザー裁定で
既に廃棄対象と決まっていたため、成果物のどの値にも到達しない。

## 裁定パッケージへ回す scope 外の real 所見

所見 6・7・8・11・12 を束ねて「消す前に止める防壁の要否と形」としてユーザーへ返す (別紙)。
