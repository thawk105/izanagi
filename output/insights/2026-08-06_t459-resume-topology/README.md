# [T-459] crash 後 resume の二重 build_start — dev-wave 逐語凍結

wave: `dev-wave-t459-resume-topology` / branch `worktree-dev-wave-t459-resume-topology`
anchor: 実装 commit `087295b9`、main 取り込み `d575021f`

## 1. 何を直したか

`build_start` 済みで terminal に達しないまま process が死んだ variant を、次 run が再評価して
二つ目の `build_start` を追記し、以後の replay と artifact admission が attempt topology 違反で
**campaign 全体を拒否**する欠陥。identity 照合済みの resume seam で、未終端 attempt を exact な
recovery-abort record で終端してから再評価する形に変えた。設計の正本は decisions の
「中断 attempt は identity 照合済み seam で recovery-abort し、自動回復は build 完了前の crash に限る」。

## 2. 射程 (何を直していないか)

- 自動回復するのは **`build_start` 直後〜build 完了前に落ちた attempt だけ**。
- 次は 1 byte も書かずに停止する: build 完了後の crash / trigger 系 campaign / 回復回数上限 /
  既存 topology 違反 / 単一 variant の複数 active / truncated tail と active attempt の併存。
- **campaign 全体の実行所有権 (lease) は導入していない。** 「resume は旧 evaluator の終了確認後」は
  機械強制でない運用契約である。
- `wal.replay` の現行挙動、`pipeline` の `build_start` emit、artifact admission 本体は変更していない。
  attempt topology の validator は recovery reason を持つ abort の exact key 集合を要求する方向
  (受理集合の縮小) にだけ変更した。

## 3. 実測

| 項目 | 値 |
|---|---|
| 受入全走 (確定、main 取り込み後) | 6512 passed / 20 skipped / 0 failed |
| 受入全走 (実装時点) | 6467 passed / 20 skipped (request `891865`) |
| 変異 matrix | 14/14 KILLED、baseline PASSED (spec sha `eeb4d99c…`、`repo_head=d575021f`) |
| 既存 WAL の被害 | repo `output/` の 30 本に未終端 attempt 0 件・`build_attempt_id` 0 件 (外部 root は未走査) |

## 4. 段の逐語

| 段 | ファイル |
|---|---|
| 1 brief | `s1-brief.md` |
| 2 plan (codex, max) | `s2-plan.md` |
| 3 敵対レンズ A (正しさ境界) | `s3-lensA.md` |
| 3 敵対レンズ B (全層被覆・scope) | `s3-lensB.md` |
| 4 裁定 | `s4-ruling.md` |
| 5 実装報告 | `s5-impl.md` |
| 6 レビュー 1 / 2 | `s6-rev1.md` / `s6-rev2.md` |
| 6 fix 裁定 | `s6-fix-ruling.md` |
| 6 fix 1 巡目 / 2 巡目 | `s6-fix.md` / `s6-fix2.md` |
| 6 焦点再レビュー | `s6-refocus.md` |
| 変異 spec / 台帳 / 初回 erratum | `mutation-spec.json` / `mutation-ledger.json` / `mutation-ledger-run1-erratum.json` |

## 5. 段 4 裁定の反証 (手戻りの記録)

段 4 で親は「並行実行が起きても生存 peer の後続 record は topology が loud に拒否する」と書いた。
段 6 レビュー 1 がこれを反証した — `verify_done` / `bench_done` は attempt に束縛されないため、
回復後に peer の RED signal だけが静かに受理される列が作れる。対応は lease の新設ではなく
**自動回復の対象を build 完了前に狭めること**とした (`s6-fix-ruling.md` の FIX-2)。
逐語は `s6-rev1.md` の所見 2 と `s6-fix-ruling.md` の該当行。

## 6. 変異 matrix の erratum

初回走行では MU-1 / MU-2 / MU-4 / MU-5 / MU-7 が MISMATCH だった。**事前登録した killer node は
すべて実際に赤くなっており、生存はゼロ**。実赤 node が登録の上位集合だった (登録が過少) ことが原因で、
初回台帳を `mutation-ledger-run1-erratum.json` に残したうえで実測 node へ再登録し確定走行した。
MU-1 / MU-2 は生成側と suffix 検査の二層が同じ入力を拒否するため **冗長 gate** であり、
単一 gate の証拠には数えない。

## 7. 裁定パッケージ (ユーザーへ返す)

1. campaign 全体の実行所有権 (lease) の要否と形。
2. recovery 済み campaign を certifying とみなすか。
3. `verify_done` / `bench_done` の attempt 束縛と consumer 射影 (本 wave は回避のみ)。
4. trigger proposal provenance への回復済み attempt の記録。
5. guided の no-build pseudo-WAL / 作図系の admission 非経由 / `wal.replay` の read-only 化。

詳細は `s4-ruling.md` の「裁定パッケージ」と `s6-fix-ruling.md` の裁定表。
