# 段 1 brief — [T-1675] 床値 official の予算承認をユーザー手番として成立させる

wave: dev-wave-t1675-budget-approval-user-turn / base main: 343b8f5a5
実行環境: login node (docs のみ + 単体テスト。計算ノードへの投入なし、性能計測なし)

## 確定済みユーザー裁定 (蒸し返さない)

- D1161: 床値 official の残る閂は承認文書であり、AI が起草しユーザーが確認する。
  **AI は自分を承認者にしない。**
- D964 / D979 / D926 は既裁定。依頼文どおり再検討しない。

## brief 前の実測で判明した、依頼文の前提を覆す新事実 (段 4 で再裁定する)

1. **裁定は既に land 済み。** D1161 として `docs/decisions.md` に在る。依頼文の「未 land・
   branch worktree-rulings-all-20260827」は執筆時点の状態で、その後 main へ入った。
   → 未 land 前提の迂回策 (branch から逐語を取り出す等) は不要。
2. **閂は 1 つでなく 2 つ。** (i) 承認 JSON が固定 path に不在、(ii)
   `BUDGET_APPROVAL_SHA256 = None` (`s8b_holdout_freeze.py:52`)。後者は
   `_budget_approval_authority()` (:1296-1302) が入力を読む前に
   `budget-approval-not-ratified` で落とす。
   → 「草案だけでは gate が開かない」は**現行実装で既に構造的に真**。本 wave の負例テストは
   新しい防壁を作るのではなく、この性質を変異で殺せる形に pin するもの。恒真 gate を
   足さないよう段 3 で攻撃させる。
3. **承認 JSON だけでは足りない。** `build_v2_g1_candidate` (:1717-1719) は別の budget 文書を
   `--budget <path>` で要求し、`approval["budget"]` と canonical bytes 一致を課す。
4. **予算の数値はまだ裁定されていない。** 依頼文の「(b)(c) は D964 / D979 で裁定済み」は
   D1161 本文の引き写しで、D964 は staged 運搬の適格性、D979 は観測役割の生涯上限であり、
   T-986 dossier §10 の数値択 (b) 2592/1296・(c) 2400/1200 とは別物。
   → **ユーザー手番の中身は「名前を書くこと」ではなく「数値を決めること」。**
   AI は推奨値と根拠と限界までを作り、数値欄を自分で確定しない。

## scope

作る: (a) 承認草案と budget 文書を生成する CLI、(b) その根拠と限界を読める形にした文書、
(c) ユーザーが 1 コマンドで確定するための `ratify` 経路、(d) 負例テスト。

作らない: v2 candidate の発行、official launch、floor campaign の起動、数値の確定、
D964 / D979 / D926 の再検討、`output/s8b-freeze/` 配下への書き込み。

## 不変条件 (破ったら停止)

- 承認 JSON の `approver` を AI が書かない。草案は承認者欄を**構造的に持てない**形にする
  (sentinel 文字列を置くだけでは「AI が書いた値」になる)。
- 草案を canonical path (`BUDGET_APPROVAL_REL`) へ置かない。
- `BUDGET_APPROVAL_SHA256` を本 wave の commit で `None` 以外にしない。
- loader (`_load_budget_approval` :1307-1339) の受理条件を 1 つも緩めない。
- `per_holdout_bench_s` の key 集合は active v1 freeze の holdouts (`rr20`, `rr80`) と完全一致。

## 判断が割れうる前提 (親の provisional 裁定であり攻撃対象)

- **(P1)** `ratify` が `s8b_holdout_freeze.py:52` の pin 定数を書き換えてよいか。
  provisional: 書き換える (occurrence 一意・現値 `None` を確認して exact 置換、commit はしない)。
  反対論: 生成物が trust root を自己改変する形になり、tool を書き換えれば承認を偽装できる。
  代案: pin を別 data file へ出す (trust root 設計の変更 = 裁定パッケージ行き)、
  あるいは tool は pin 行を印字するだけにする (「1 コマンド」を満たさない)。
- **(P2)** 草案の置き場所。provisional: repo へ commit せず `--out` で job dir 等へ出す
  (tracked 化すると `output/` snapshot 検査の母集合が動く)。
  反対論: 読めるものが repo に残らないと「ユーザーが中身を読む」導線が弱い。
- **(P3)** 数値をどうユーザーへ束縛するか。provisional: `ratify` は数値を引数で明示要求し、
  既定値を持たない (既定値があると AI が数値を決めたことになる)。

## 成果物影響 (DW-G05)

実装しない場合、`build_v2_g1_candidate` は `budget-approval-not-ratified` で拒否され続け、
v2 g1 candidate が発行できない。結果として床値 official の result も v2 世代も台帳に載らず、
certified 選択の proof chain に床値の枝が永久に欠ける。

## 変更面 (実アンカー)

| path | 種別 | 所有 |
|---|---|---|
| `tools/s8b_budget_approval.py` | 新規 CLI | 単位 A |
| `orchestrator/tests/test_s8b_budget_approval.py` | 新規テスト | 単位 A |
| `orchestrator/campaign/s8b_holdout_freeze.py` | (P1) 次第。既定は無変更 | 単位 A |
| `docs/` の手順・根拠文書 | 親が書く (docs は実装子の編集面外) | 親 |

既存資産: `orchestrator/tests/s8b_v2_freeze_fixture.py:474-477` が受理される承認 JSON を既に
組み立てており、生死確認 (DW-G01) はこの既存 fixture で足りる。使い捨て driver を作らない。

## 波及先 (DW-O26 の consumer 拡張候補)

- `orchestrator/tests/test_s8b_holdout_freeze.py` (承認 loader の既存負例 :1599, :1959)
- `orchestrator/tests/s8b_v2_freeze_fixture.py`
- `orchestrator/tests/test_real_repo_serialization.py` +
  `orchestrator/tests/output_snapshot_ignores.py` (`output/` を実 repo で走査する。
  (P2) で tracked file を足すと母集合が動く)
- `orchestrator/tests/test_frozen_artifacts.py` (`FROZEN_MANIFEST` に承認 path は**不在**。
  本 wave で追加しない)

## 分割方針

実装面は 1 単位 (CLI + テストは所有が同じで依存も一枚)。段 3 の敵対相談だけ 2 レンズ並列。
