# [T-925] docs/dev-wave 予算棚卸し wave — 逐語と裁定パッケージ

wave branch = `worktree-dev-wave-t925-l15-inventory`。base = main `6331284e`。
**裁定 = 実装しない (段 4 で `4→7→8→9`)。`docs/dev-wave/**` の差分はゼロ。**

## 何をした wave か

`docs/dev-wave/**` の L1 / L1.5 と入口 (L0) について、陳腐化した規範節を実測で特定し、
削除またはテスト化で予算を空けて、堰き止められた 4 系統の契約 ([T-925](1)〜(4)、[T-916](c)、
[T-934](a)) を反映することを目指した。

結果は **削除して安全と確定できた節がゼロ件**。台帳 [T-925] の裁定
「削除候補の一覧を 1 回の裁定パッケージでユーザーへ返す」に従い、`verbatim/package.md` を返す。

## 実測

| 層 | 実測 | 上限 | 余白 |
|---|---:|---:|---:|
| L0 入口 `.claude/commands/dev-wave.md` | 9,500 | 9,500 | 0 |
| L1 (常時段の U 節) | 10,624 | 10,625 | 1 |
| L1.5 (クラス依存段の U 節) | 9,564 | 9,566 | 2 |
| L2 単節最大 (`DW-O09`) | 997 | 1,000 | 3 |

予算値の定数は 1 bytes も変更していない ([T-127])。

## 削除候補 8 件の判定

親と段 2 の codex 子が**独立に 4 件ずつ**挙げ、両者の候補は **1 件も一致しなかった**。
段 3 の敵対 2 レンズ (lane sol / luna、`reasoning=max`) は両方とも NO-GO を返した。

- 親案 4 件: `DW-O01` prompt 非空 (34) / `DW-M05` pgrep 段落 (201) /
  入口 fail-closed 文 (170) / 入口 停止条件文 (95)
- 子案 4 件: `DW-M04` (201) / `DW-M06` (139) / `DW-O23` (333) / reasoning 散文のテスト化 (163)

**7 件が refuted、1 件 (入口 `:116-117`、174 bytes) で両レンズが対立。**
判定の決め手は `verbatim/package.md` §2 が正本。

## この wave で得た知見

1. **「機械検査があるから散文は不要」はほとんど成立しない。** dev-wave の散文の大半は
   「この機械検査を回せ」という起動指示であり、検査の実在は起動を強制しない。
   例: `tools/check_codex_output.py` は `## 総括` と 500 bytes 下限を確かに強制するが、
   親がそれを実行することは強制されない。判定 A (無条件削除可) が稀になる構造的理由である。
2. **機械代替の主張は「負例テストの実在」まで見ないと恒真になる。** 親 P-a は
   下流の実 launch が空 prompt を止めることを確認したが、段 3 が
   「空 prompt で rc≠0 になる負例テストが無い」ことを指摘して refuted になった。
3. **入口の重複には再帰の基底がある。** 入口の「参照が読めなければ fail-closed 停止」は
   `DW-STOP` と同内容だが、`core.md` 自身が読めないときに自分の読取失敗を止められないため、
   入口側の写しは冗長ではない。親と段 3 レンズ 1 が独立に同じ結論へ到達した。
4. **L2 には合計上限が無い (7,252 bytes の未使用枠)。** 層予算は L1 合計・L1.5 合計・
   L2 の単節 1,000 bytes の 3 つだけで、ファイル単位の上限も L2 合計の上限も存在しない。
   新規 L2 節 1 つの費用は入口の条件 dispatch 表 1 行 (最短 79 bytes)。
   **L0 を 180〜280 bytes 空けるだけで堰き止め 4 件すべてを収容できる**見込みで、
   L1.5 / L1 を個別に空ける従来の枠組みより桁違いに安い。次 wave の候補。
5. **棚卸しという手段は尽きた。** [T-786] (2026-08-11) が完全 9 段 + 変異 6/6 KILLED で
   同じ結論 (削除候補ゼロ件・等価縮約を出し切った) に到達しており、本 wave が独立に再現した。
   `DW-G03` の族一般化条件 (独立 2 例) を満たす。
6. **`operations.md` / `workers.md` の編集は codex 子を起動不能にする。**
   `tools/dev_waves/launch_authority.py` の `snapshot_authority` が live 実行時に
   working tree と authority commit を byte 比較して fail-closed するため。
   棚卸し wave では段 2・3 の子を編集前に投入する必要がある。

## 逐語

- `verbatim/s1-brief.md` — 段 1 brief
- `verbatim/s1-parent-inventory.md` — 親が段 2 の子成果物を読む前に独立導出した棚卸し
  (**親案 P-a / P-b は段 3 で refuted**)
- `verbatim/s2-plan-prompt.md` / `s2-plan-out.md` — 段 2 プラン起草
- `verbatim/s3-lens1-prompt.md` / `s3-lens1-out.md` — 段 3 レンズ 1 (正しさ境界と機械代替の実在)。
  **blocker 7 件**
- `verbatim/s3-lens2-prompt.md` / `s3-lens2-out.md` — 段 3 レンズ 2 (収支・scope・認可境界)。
  **NO-GO**
- `verbatim/s4-adjudication.md` — 段 4 裁定 (実装しない)
- `verbatim/package.md` — 裁定パッケージ (Q1 = 入口 174 bytes の削除可否、Q2 = L2 経路の起票可否)

## 変異 matrix

**免除。** `DW-S04` の免除条件「『実装しない』裁定済みかつ実装差分ゼロの wave の変異 matrix」に
該当する。本 wave の diff は worklog fragment と本 insights のみで、コード・テストの差分はゼロ。

## 受入

docs-only だが実 repo の docs を読むテストが 10 file 実在するため免除しない。
受入全走 **10,085 passed / 65 skipped、rc=0** (tested tip `e7a9c8fb`)。
`python3 tools/check_docs.py` も rc=0 (違反なし)。
