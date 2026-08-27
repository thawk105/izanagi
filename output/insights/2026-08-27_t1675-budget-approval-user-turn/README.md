# [T-1675] 予算承認のユーザー手番 — 承認を発行しない preflight の設計と根拠

```text
authority: none
default_effect: no-state-change
STATUS: NOT AN APPROVAL / NON-CANONICAL / NON-OPERATIONAL
```

本 package は開発過程の監査資料である。予算承認そのものでも、proof chain でもない。

## 結論

床値 official の予算承認について、**承認 artifact を発行する経路は作らなかった。**
作ったのは骨組みの生成 (`skeleton`) と read-only の検証 (`verify`) だけである。

依頼は「ユーザーが中身を読んで 1 コマンドで確定できる形」だったが、
**確定の部分は既裁定と衝突するため実装せず、裁定パッケージとして返した。**

## 1. なぜ確定を作らなかったか

| 裁定 | 内容 | 本 wave への効き方 |
|---|---|---|
| D287 | approval を発行する CLI・API・`--approver` 引数・既定補完は作らない。pinned literal なら AI が承認者になるには人間がコード diff をレビューして定数を置くしかない | 本 pin を作った wave 自身の裁定。未 supersede。ratify 案と正面衝突 |
| D526 | 批准台帳へ追記 API・CLI・自動更新処理を作らない。批准値を wave 側で作って land するのは弱化した本人が批准する形 | 同型 |
| D905 | 批准の執行は成りすませない実行主体の新設だけを採る。平文承認へ移す案は採らない。設計が着地するまで批准は進めない | 段 2 の TTY 案が却下済みの形と同型 |
| D758 | 承認 (authority) は人間手番、機械的実行は機構へ。ただし承認を AI が合成できない入力として受け取る経路を設計してから移す | 発行しない範囲でだけ機械化してよい根拠 |
| D1161 | AI が起草しユーザーが確認する。AI は自分を承認者にしない | 本 wave の直接の拘束 |

段 3 のレンズ A が D287 との衝突を独立に摘発し、同時に
「対話端末は人間と機械を区別しないため承認境界の防壁にならない」と結論した。
親は段 4 で ratify を不採用と裁定した。

## 2. 依頼文の前提のうち、実測で訂正した点

1. **裁定は未 land ではなく着地済み**だった。D1161 として `docs/decisions.md` に在る。
2. **閂は 1 つでなく 2 つ**である。承認 JSON の不在に加えて
   `BUDGET_APPROVAL_SHA256 = None` が入力を読む前に `budget-approval-not-ratified` で落とす。
   したがって「草案だけでは gate が開かない」は現行実装で既に構造的に真であり、
   本 wave の負例は新しい防壁ではなくこの性質の固定である。単一理由の gate としては主張しない。
3. **予算数値は未裁定**である。「(b)(c) は D964 / D979 で裁定済み」は D1161 本文の引き写しで、
   D964 は staged 運搬の適格性、D979 は役割横断の生涯観測上限であり、数値を承認していない。
   ユーザー手番の中身は「名前を書くこと」ではなく「数値を決めること」である。
4. **承認だけでは v2 candidate は通らない。**`BUDGET_APPROVAL_REL` の consumer は
   `build_v2_g1_candidate` ただ 1 つで、床値 campaign の起動側は読まない。
   同 builder は official の `result.json` と同一 run の `manifest.json` / `journal.jsonl` も
   要求し、`output/env/*/calibration/s8b-floor-official/` は現物に存在しない。

## 3. 作ったもの

`tools/s8b_budget_approval_preflight.py`

- `skeleton --out <repo 外の絶対パス>` — 承認者・日時・予算値を持たない骨組みを
  create-only で書く。repo 内・既存 leaf・symlink は拒否する。
- `verify --candidate <path>` — 人間が書いた承認 JSON を検証し、raw の sha256 と pin 行を
  表示する。**file を 1 つも書かない。**
- `--approver` を持たない。承認者を環境変数・git 設定・既存の凍結記録・骨組みから補わない。

手順と数値の根拠は `docs/s8b-budget-approval-user-turn.md`。
数値の一次資料は `output/insights/2026-08-24_t986-budget-approval-package/README.md`。

## 4. 検査

`orchestrator/tests/test_s8b_budget_approval_preflight.py` (33 node)。

- **N1** 承認者の流入経路が無いこと。CLI の option 集合・骨組みの bytes・import 対象を
  exact allowlist で固定し、承認者らしき環境変数を設定しても補完されないことを負例で示す。
  当初は denylist だったが、段 6 の両レビューが `from os import environ as source` 等で
  迂回可能だと指摘したため allowlist へ変えた。
- **N2** 骨組みを canonical path へ置き正しい sha256 を pin に与えても loader が拒否すること。
  **過剰決定であり、単一理由の gate としては主張しない契約テストである。**
- **差分テスト** 同一 raw を `verify` と `_load_budget_approval` の双方へ渡し、
  正例と 9 種の違反で受理・拒否が一致することを固定する。
  pin・path・caller holdout の意図的な非対称は別 node で明示する。
  `verify` が loader の条件を書き写しているため、将来の乖離を検出する目的で置いた。

## 5. 変異 matrix

固定 commit へ束縛し、隔離 worktree で計算ノードへ dispatch した。

```text
baseline PASSED (33 passed)
KILLED 6 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0 / PARSE_ERROR 0
```

| ID | 変異 | 殺した node 数 |
|---|---|---:|
| MU-1 | canonical bytes 一致の検査を外す | 1 |
| MU-2 | scope 固定値の比較を外す | 2 |
| MU-3 | holdout 集合の判定を候補側の keys に緩める | 3 |
| MU-4 | 骨組みの repo 外制約を外す | 1 |
| MU-5 | 骨組みへ承認者欄を足す | 1 |
| MU-6 | verify が canonical path へ書くようにする | 2 |

MU-3 は当初「verify の集合比較を緩める」として登録したが、`verify` に集合比較は無く
production の `_validate_budget` へ委譲しており**注入位置が存在しなかった**。
段 6 のレビュー B が摘発し、tool が渡す `holdout_ids` を候補側の部分集合へ差し替える位置へ
再照準した。登録どおりのまま走らせていれば、殺せない変異を matrix に載せていた。

**登録しなかった変異:** `_validate_budget` 側の数値・holdout 検査は loader が同じ入力を
拒否するため過剰決定であり、単一理由性が成り立たない。N2 の経路も同じ理由で登録していない。

## 6. 主張の上限

固定できるのは、承認者が非対話経路から流入しないこと、予算数値に既定値が無いこと、
置かれた内容が canonical loader の条件を満たすことまでである。
検証 tool と被検証対象を同じ主体が変更できる以上、意図的な改変への完全な防壁ではない
(D387、D1128)。事故的な誤りは検出する、とだけ書く。

## 7. ユーザーへ返す裁定

1. **承認 bytes を誰が置くか。** D287 は本 pin について人間の reviewed diff を要求し、
   D758 決定 2 と D905 は enforcement closure 批准について
   「行の貼り付け・コマンドの実行を人間手番に置く設計は採らない」としている。射程が違う。
   択一は (a) D287 を本 pin について維持する (現状)、
   (b) D905 の「成りすませない実行主体」を本 pin へも設計する別 wave を起こす。
2. **予算数値。** 保留 / 2592・1296 / 2400・1200。現証拠の推奨は保留。
3. **順序。** 承認は official floor campaign の起動を塞いでいない。

## 8. 検証資料

`verbatim/` に段 1 brief、段 2 plan、段 3 の 2 レンズ、段 4 裁定、段 5 実装報告、
段 6 の 2 レビューと fix 報告を置く。`mutation-spec.json` と `mutation-report.json` は
変異 matrix の事前登録と結果である。いずれも開発過程の監査資料であり、承認ではない。
