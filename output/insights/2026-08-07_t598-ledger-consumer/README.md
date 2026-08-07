# dev-wave t598-ledger-consumer の逐語 (2026-08-07)

依頼: 「[T-598] — claude_session_ledger の consumer 結線先の設計。結線が決まるまで削減施策は
起票しない、の前段」

branch `worktree-dev-wave-t598-ledger-consumer`、開始 local main `9cb0f24b`。

## 何を land したか

**実装差分はゼロ。** 結線先の設計判断 (decisions) と記録、および
`docs/README.md` の tools 地図への 1 行だけである。

段 4 で「実装しない」と裁定したため段 5・6 を飛ばし、`4→7→8→9` とした。
**実装差分が無いため変異 matrix と受入全走は対象外**である。

## ファイル

| ファイル | 中身 |
|---|---|
| `brief.md` | 段 1 の親 brief。実測 M1〜M13 と provisional 裁定 P1〜P5 |
| `prompt-s2-plan.txt` / `s2-plan-out.md` | 段 2 プラン起草 (codex `gpt-5.6-sol`、`reasoning=max`、read-only) |
| `prompt-s3-lensA.txt` / `s3-lensA-out.md` | 段 3 レンズ A = 測定妥当性への攻撃 |
| `prompt-s3-lensB.txt` / `s3-lensB-out.md` | 段 3 レンズ B = 規約・凍結・予算・scope 肥大への攻撃 |
| `s4-ruling.md` | 段 4 の親裁定。real/refuted、採否、ユーザー裁定 4 件 |

## 親の主張のうち反証されたもの (erratum を消さない)

| 親の主張 (段 1 brief) | 判定 | 反証の内容 |
|---|---|---|
| 開発観測台帳の token 4 区分の欄は producer 不在で空いており、claude 台帳を差せば埋まる (M4) | **refuted** | `tokens` は agent 実行 event 専用 field。task 単位の欄は存在しない。最終 report の `0/0` は「欄が空」ではなく「agent event 自体が無い」 |
| worktree ごとに claude の保存先が分かれるので wave 単位に帰属できる (M6 / M11) | **限定付き** | transcript 305 件の集計で、145 件が別保存先の下に当該 worktree の記録を持ち、37 件が 1 file 内で作業場所を混在、3 件が worktree 間を移動。本 wave 自身の transcript も混在していた |
| 別 root でも新規記録はコード変更なしに作れない (M13) | **限定付き** | 現行 CLI だけで別世代を開始できる。コード変更が要るのは task 単位 event を持つ新 schema 世代だけ |
| ID 衝突は strict 指定時の問題 (M12) | **親より強い形で real** | 衝突は fatal 分類にも入り、strict でなくても失敗する |

親の推奨 (P1) は、その動機付け (M4) が段 2 に訂正された後も推奨として残り、段 3 で改めて棄却された。
**崩れた動機付けの上に残った推奨を、段 3 が独立に潰した**のが本 wave の構造である。

## 段 3 の判定

- レンズ A: **測定として不成立**。blocker 6 件 + must-fix 1 件。
- レンズ B: **D205 に照らして過大、NO-GO**。blocker 3 件 + must-fix 3 件 + nit 1 件。

両者は独立に走り、互いの出力を見ていない。にもかかわらず結論が一致した。

## 本 wave の最重要の発見

[T-598] の但し書き「結線先が決まるまで削減施策は起票しない — before/after を測れないため」は、
**結線を決めても解除されない。** 前後比較の成立には結線に加えて 4 条件が要り、うち
「施策より前に前向き baseline を貯め終える」は遡及不能なので時間依存である。
この点は decisions の決定 (5) として記録し、ユーザー裁定 (U-4) へ返した。

## 子の実行記録

| 段 | 子 | model / effort / sandbox | exit |
|---|---|---|---|
| 2 | plan 起草 1 本 | `gpt-5.6-sol` / max / read-only | 0 |
| 3 | 敵対 2 本 (並列) | `gpt-5.6-sol` / max / read-only | 0 / 0 |
| 5 | 起動せず (実装しないと裁定) | — | — |
| 6 | 起動せず | — | — |

3 本とも `tools/check_codex_output.py` の rc=0 を確認して採用した。
