# 段 4 裁定 — freeze-hold residual

2026-08-12 20:40 JST 頃。親 = claude opus-5-1m。入力 = brief / s2-plan / s3-sol / s3-luna /
親の独立検算。

## 裁定 1 (最重要): [T-913] は実装しない。4 function は保留せず、一覧でユーザーへ返す

**両レンズが独立に BLOCKER を出し、親が一次資料で裏を取った結果、real と裁定する。**
プランの A 節 (第 4 束 4 行の台帳投入) は**破棄**する。

根拠 (すべて親が一次資料で確認):

1. **4 function は成長比例ではない。** `test_t793_publication_ledger.py:31-41` の `_init_repo` は
   `tmp_path` に `git init` した固定サイズの一時 repo を作る。実 repo の commit 数・file 数を
   走査しない。**D335 (成長比例コストのテスト) の対象に入っていない。**
2. **D328 (凍結検証保留) の対象でもない。** D328 が保留するのは実装↔測定の同一性検証であり、
   正しさゲートと防壁の自己完全性は本文が明示的に対象外としている。4 function が守るのは
   `ledger.py` の fail-closed 拒否境界 — 重複 identity 拒否 (`:228-252`)、prefix-only 履歴、
   commit 済み delete/recreate 拒否 (`:311-361`) — であり、いずれも唯一検出者である
   (sol が性質検索で同型検査の不在を確認、親は非 test caller ゼロを独立検算)。
3. **D320 は撤去の授権ではない。** D320 本文に「本決定は新設と維持コストの既定を変えるだけで、
   **live な検査を黙って外す授権ではない**」「既存機構の撤去・緩和は個別裁定で行う」と明記がある。
   worklog 478 は D320 を保留の根拠にしていたが、**その個別裁定は存在しない。**
4. **取引が成立しない。** 保留の利得は 0.14 秒 (4 件はいずれも `@real-repo` 直列鎖の外で、
   wall = 直列鎖 + 定数)。受入 wall 186 秒に対して実質ゼロ。失うのは唯一検出者の検出力。
5. **ユーザー指示そのもの。** 第 4 束は「対象外 = 正しさゲート・規律 1・防壁の自己完全性 —
   **判定に迷う項は保留せず一覧でユーザーへ返す**」と書いている。本件はまさに判定が割れた項である。

**代替案の検討と却下:** `correctness_gate=True` で保留すれば第 3 束の「正しさゲートは保留一覧へ
出す」機構に乗る。しかしその機構は D335 (成長比例) 用であり、4 件は成長比例ではない。
第 4 束はより新しく、かつ「保留せず返す」と明示している。よって採らない。

## 裁定 2: (P1) `correctness_gate: false` は refuted

luna BLOCKER-1 と sol B2 が独立に同じ結論。`conftest.py:359-369` は flag の値を見ずに skip するため、
`False` は検出力を残さず**ユーザー向け一覧から隠すだけ**になる。裁定 1 により moot だが記録する。
親の provisional 裁定 (P1) は誤りだった。

## 裁定 3: (P2) `measured_seconds` 投入は moot、(P4) 置き場所は採用

- (P2) は裁定 1 で消える。luna MAJOR-3 / sol N1 の指摘 (測定範囲・node 数・aggregation を
  持たない scalar の二義性) は正当で、将来第 4 束以外の行を入れる際の必須条件として記録する。
- (P4) `tools/hold_inventory.py` は採用。sol・luna・親の 3 者が独立に import 規約への
  抵触なしを確認した (`test_campaign_import_invariant` の相対 import 検査は
  `orchestrator/campaign/*.py` 限定、`testpaths` は `orchestrator/tests` のみ)。

## 裁定 4: [T-914] は実装する。ただし保証範囲を正直に下げる

luna MAJOR-2 / sol M1 は real — 「新しい保留層が増えたのに inventory が無視する」壊れ方は、
source を import して source と比べる契約では原理的に捕まらない。**完全性を名乗らない。**

実装する形 (プラン B 節を次のとおり改める):

- **名乗りを下げる。** schema・docstring・human 出力の見出しに「現行 2 層の snapshot であり、
  未知の保留層の自動発見は保証しない」を明記する。`izanagi-hold-inventory/v1` の
  `completeness` field に `"registered-layers-only"` を入れる。
- **sol M2 を採用。** `configured_status` (台帳がどう定義しているか) と `effective_status`
  (今この環境・この runner で実際に保留されるか) を分離する。
- **bypass surface を出力に含める。** 素の runner (`python3 test_*.py`) が conftest hook を
  通らず保留を迂回する既知限界 ([T-930] 未解決) と、Pegasus の env transport allowlist が
  解除経路の一部であることを機械可読に出す。**「全層で held」と主張しない。**
- **契約テストは `main()` を実際に呼ぶ。** renderer 関数だけを呼ぶと CLI wiring の破損が緑になる
  (luna MAJOR-2)。`--format human` / `--format json` の両 dispatch を実際に通す。
- 解除条件 literal はメタテスト側でハードコードし、production と同じ定数を参照しない
  (自己参照で一斉に追随する既知の罠)。

**成果物影響 (DW-G05):** 実装しない場合、恒久保留の解除がユーザー明示命令のみであるのに、
ユーザーは「今なにが止まっているか」を 1 箇所で読めない。現に production 21 check ID と
test 30 function が別機構・別解除経路で散っている。解除判断の入力が欠けたままになる。

## 裁定 5: luna MAJOR-4 (wall の一般化) を採用

「鎖外だから wall は動かない」は測定条件つきでしか言えない。before/after の受入全走には
HEAD / submodule SHA / 機体 / worker 数 / command / 並行 wave の有無を併記し、
0.14 秒の合計と wall を別値として報告する。**1 走の差を効果と断じない。**

## 段 5 へ渡す scope

**実装は [T-914] のみ。** 編集してよい file =
`tools/hold_inventory.py` (新規) と `orchestrator/tests/test_hold_inventory.py` (新規)。
**`growth_test_holds.py` は 1 byte も触らない** (裁定 1 で第 4 束の行を入れないため)。
**編集禁止** = `conftest.py` / `test_t793_publication_ledger.py` / `ledger.py` /
`freeze_verification_hold.py` / `test_growth_test_holds_contract.py` / 凍結 artifact 全般。

## 変異事前登録 (DW-M01) — [T-914] に対して 7 件

| # | 変異 | 期待 | 単一理由性 |
|---|---|---|---|
| 1 | inventory から production layer を丸ごと落とす | KILLED | 前後に同じ入力を拒否する層なし |
| 2 | test layer の item を 1 件落とす (exact key set 比較を通さない) | KILLED | 同上 |
| 3 | `effective_status` を env を見ずに常に `held` へ固定 | KILLED | 同上 |
| 4 | bypass surface (plain runner) の記載を出力から落とす | KILLED | 同上 |
| 5 | `main()` の `--format json` dispatch を壊す | KILLED | renderer 単体検査では通るため CLI 契約でのみ発火 |
| 6 | 解除条件 literal を書き換える (production 側定数) | KILLED | メタテストが literal をハードコードしていれば発火 |
| 7 | **正例**: 正しい inventory がそのまま受理される | 変異なしで緑 | 過剰拒否の検出 |

変異 6 は「wave 前の実コードの形」に相当する自己参照の罠を狙う登録である。
期待 node は fix 後の最終 commit で完全集合として再導出する (DW-M07)。

## ユーザーへ返す一覧 (段 7 で裁定パッケージ化)

1. **[T-913] の 4 function** — 保留せず据置。上記根拠つきで再裁定を仰ぐ。
2. **worklog 478 §4 の 4 件** (判定に迷い保留しなかったもの) — 未裁定のまま。再掲。
3. **[T-915] / [T-902] の裁定衝突** — 依頼文「holdout live scan は保留対象そのもの」と
   worklog 478 §5「測定の公正側なので保留対象外、正解は最適化」の食い違い。親は倒さない。
4. **[T-930] 素の runner による保留の迂回** — 未解決。inventory は事実を出すだけで解決しない。
5. **`ledger.py:377-382` の working-tree strict-extension が未被覆** (sol B2 の追加所見)。
   保留の可否以前に、そもそも直接検査が無い。
