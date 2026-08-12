---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-freeze-hold-residual
seq: 1
title: 凍結チェーン保留の執行は既に land 済みだった — 残余の統合保留 inventory を実装し、公表台帳 4 件は保留せず返した (コード + docs、変異 6/6 KILLED、branch worktree-dev-wave-freeze-hold-residual)
---

## 本文

ユーザー依頼は「freeze-chain-hold (= [T-917] 凍結チェーン検証の保留執行) の wave」だった。
**着手前の実測で [T-917] は同日 land 済みと確定したため、同型の再実装は行わなかった。**

### 依頼の前提を実測で覆した (再実装を避けた根拠)

- 裁定 D328 は cherry-pick `68c83c2d` 経由で main に入り採番済み。
- production 実体 `orchestrator/campaign/freeze_verification_hold.py` が既に存在し、
  `HELD=True` / 保留 check_id 21 件 / `HELD_CHECK_IDS_SHA256` の自己 pin /
  機械可読 `REASON` (decision, ruling, authority, `release_condition`) を持つ。凍結 bytes は不変。
- 執行は t816-step4-impl wave が実施 (worklog 485)、受入で残った 4 件は `54018867` (18:24 JST) で解消。
- 成長比例テストの保留台帳 (30 entry) も land 済み (worklog 483)。

**よって scope を同じ裁定下の未実施残余 ([T-913] と [T-914]) へ移した。**

### 敵対 2 本が独立に [T-913] を止め、親が一次資料で裏を取って据置にした

段 3 の sol は **STOP 推奨**、luna は同じ点を BLOCKER にした。親が検算した結果すべて real だった。

1. **4 function は成長比例ではない。** `test_t793_publication_ledger.py:31-41` の `_init_repo` は
   `tmp_path` に `git init` した固定サイズ repo を作り、実 repo を走査しない。D335 の対象外。
2. **D328 の対象でもない。** 4 function が守るのは `ledger.py` の fail-closed 拒否境界
   (重複 identity `:228-252`、prefix-only 履歴、commit 済み delete/recreate 拒否 `:311-361`) で、
   いずれも唯一検出者。D328 は正しさゲートと防壁の自己完全性を対象外と明記している。
3. **D320 は撤去の授権ではない。** 本文に「live な検査を黙って外す授権ではない」
   「既存機構の撤去・緩和は個別裁定で行う」とあり、その個別裁定は存在しない。
   起票元 (worklog 478) は D320 を根拠にしていた。
4. **取引が成立しない。** 保留の利得は 0.14 秒 (4 件とも `@real-repo` 直列鎖の外)。
   受入 wall に対して実質ゼロで、失うのは唯一検出者の検出力。

第 4 束の「判定に迷う項は保留せず一覧でユーザーへ返す」に従い据置とした。
**段 6 のレビュー B が同じ裁定を再攻撃し、覆せなかった** (独立の裏付け)。
親の provisional 裁定 `correctness_gate: false` は **refuted** — `conftest.py:359-369` は flag の値を
見ずに skip するため、`False` は検出力を残さずユーザー向け一覧から隠すだけになる。

### [T-914] は実装したが、保証範囲を意図的に下げた

段 3 の luna と段 6 の A が独立に「source を import して source と比べる契約では、
未知の保留層が増えた壊れ方は原理的に捕まらない」と示した。**完全性を名乗らせない**方針にし、
`completeness=registered-layers-only` を持たせ、見出しと docstring に明記した。

段 6 の A は **禁止語 blacklist を実際に回避する完全性主張文を書いて素通りを実証**したため、
human は独立な期待 line sequence との exact 比較、json は top-level key の exact 集合検査へ変えた。

段 6 の B の指摘で `configured_status` と `effective_status` を分け、
`effective_status_assumption` に前提 (pytest が suite conftest を読み込む runner) を書き、
迂回経路 5 件 (素の runner、`--noconftest`、suite 下を指す `--confcutdir`、
test 関数の直接呼び出し、`PYTEST_ADDOPTS` transport) を機械可読に出す形にした。
**「全層で held」と無条件に主張しない。**

### 焦点走が緑でも全走が赤になる欠陥を、レビューだけが捕まえた

新規 test file に自走経路が無く、`test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
が **1 failed** になる状態だった (計算ノード実測 `907714.nqsv`)。
**親の焦点走 4 passed はこの検査を含んでいなかったため緑に見えていた。**
子の実走が親の全走を代替しないことの実例。素の script 起動も `rc=1`
(`ModuleNotFoundError`) で、module 起動だけが通っていた。いずれも fix で閉じた。

### 焦点再レビューが更に 2 件を掘り、fix を 2 巡した

1 巡目の後、焦点再レビューが **land 不可** と判定した。いずれもテスト側の穴で実装は無傷だった。

- **入れ子 field から完全性の過剰保証を再導入できた。** top-level と layer の key 集合は exact に
  なっていたが、`what` の key 集合と `reason` の内容が固定されておらず、production の `reason` へ
  完全性を主張する 1 対を足す変異が禁止語に当たらない。**human 期待値も JSON 期待値も同じ
  mutated 値へ追随する**ため両方が緑になる。全 nested object の key と、source から導けない値を
  メタテスト側の canonical literal で固定して閉じた。
- **空文字 env の分岐が conftest 照合から抜けていた。** `_test_effective_status` の条件を
  `value is None` だけへ弱めると空文字だけが誤分類されるが検出されない。分岐を足して閉じた。

### 変異は初回 3 件 MISMATCH → 再導出して 6/6 KILLED

初回走 (probe、`mutation-out-probe1.json` に保存) では M1 と M2 が**期待より多くの node を発火**させ
(検出力が想定超過)、M5 は逆に 1 node だった。観測された完全集合で再登録し **6/6 KILLED、
生存ゼロ、MISMATCH ゼロ** (HEAD `7f78c40b`)。

**M5 の縮小は構造の発見でもある。** fix で human 検査を「inventory から作った期待値との exact 比較」に
変えたため、human 側は source の改竄に追随して発火しない。source 集合比較の側だけが捕まえる。
検出力は失われていないが、**human 比較は renderer の壊れ方だけを見ている** (M1 が実証)。

### 実測 (すべて Pegasus 計算ノード dispatch)

- 焦点走 (fix 前) 4 passed / 2.63 秒 / rc=0 — `907707.nqsv`
- 自走経路検査 (fix 前) **1 failed, 2 passed** — `907714.nqsv`
- 焦点走 (fix 1 巡目後) **54 passed / 6 skipped / rc=0** — 4 file
- 焦点走 (fix 2 巡目後、最終) **9 passed / 2.49 秒 / rc=0** —
  `test_hold_inventory` (6 node) と `test_plain_runner_coverage` (3 node)
- 変異 **6/6 KILLED / SURVIVED 0 / MISMATCH 0** (最終 HEAD `aaa4de0c`)
- 全史 provenance rc=0 (2975 件、新規違反なし)
- **受入全走 before = 9994 passed / 65 skipped / 129.50 秒 / rc=0** (tip `ff97b574`、nproc 96、
  ccbench `511c9538`、lease 内)
- 受入全走 after = 本エントリの記録 commit 込みの最終 tip で実施 (下の「受入 after」参照)

**保留導入前の記録 186.38 秒 (worklog 478、tip `7b6f91a8`) と比べると 129.50 秒は約 30% 短い。**
ただし別日・別 tip の比較であり、並行 wave の land と queue 状態の交絡が残る。
本 wave の追加分 (新規 4 node、いずれも直列鎖の外) は before/after の差として測る。

### 待ち手の偽完了を 2 度観測した

背景の待ち手が `exit 0` を返したのに、成果物も `.done` も無く producer が生存している事象が
段 6 の review A と fix で 1 度ずつ起きた。待ち手自身の出力は 0 bytes だった。
**3 点照合 (成果物実在 + `.done` + producer 死) で偽と判定し、破壊的操作をせず再武装した。**
fix では前景待機へ切り替えて解決した。

## 次の一手差分

### carry

- [T-930]

### 完了

- [T-914] 保留を 1 箇所で読める統合 inventory を `tools/hold_inventory.py` として実装した。
  production 層 (check ID 21 件) と test 層 (30 function) を読み取り専用で射影し、
  human と json の 2 形式で出す。**完全性は名乗らない** (`registered-layers-only`)。
  変異 6/6 KILLED。
  remaining: none
  base: c470115331d6b95662848c44143ccaa89a58f1eafdce365bc38cf34c8a0a4395

### 更新

- [T-913] **P2・据置。ユーザー再裁定待ち**: 公表台帳 R2 番人 4 function を保留台帳へ投入する案は
  **実装しなかった**。敵対 2 本が独立に BLOCKER とし、親が一次資料で裏を取った —
  (1) 4 件は `tmp_path` の固定サイズ repo を使い実 repo を走査しないので D335 の対象外、
  (2) `ledger.py` の fail-closed 拒否境界の唯一検出者で D328 が対象外と明記した側、
  (3) 起票根拠の D320 は本文で「live な検査を黙って外す授権ではない」と述べており個別裁定は不在、
  (4) 利得は 0.14 秒で失うのは唯一検出者。第 4 束の「判定に迷う項は保留せず返す」に従う。
  **保留するなら D320 とは別の個別裁定が要る。**
  base: 731c81a86818cdf8b6aae731201e7cd5cb1dd185db39ee68629ea328af1d20dc
- [T-915] **P1・裁定の食い違いを再提示**: 依頼文は「[T-902] の holdout live scan は保留対象そのもの」
  だが、worklog 478 §5 は実測に基づき「これは実験の妥当性 = 測定の公正であり、同じ裁定が対象外と
  明記した側。正解は保留でも除去でもなく最適化」と判定して裁定へ返している。
  **親は倒さず両論を併記して返す。** 前提だった t816 の保留 land は済んでいる。
  base: d251f0b41e833111609b8fd1dbcb68c14bd5909784aadb31fe1db62115e4a3ac
- [T-917] **完了済みと確認**: 本 wave の着手前実測で、凍結チェーン検証の保留執行は
  t816-step4-impl wave が実施済みと確定した (production 実体・受入残 4 件の解消 `54018867` とも実在)。
  重複実装はしていない。
  base: 0ac061ef93c73bde9ff911aa149c3ec8d7af57ac045cb9ba2f8607e707a7af9f

### 新規

- {{T:runner-rejects-conftest-suppression}} **P2・新規**: `tools/run_tests.py` が
  `--noconftest` と suite 下を指す `--confcutdir` を fail-closed で拒否する案。
  現状これらは未知 option として通り、**保留を無音で迂回できる**
  (段 6 レビュー B が `run_tests.py:76-94,390-428` で実証)。
  `tools/hold_inventory.py` は事実を `bypass_surface` に出すだけで解決しない。
  **共有 runner の受理集合を変えるため独立の敵対検証を受入条件とする。**
- {{T:publication-ledger-strict-extension-uncovered}} **P3・新規**:
  `orchestrator/publication/ledger.py:377-382` の「working tree が commit 済み tip の
  strict extension である」保証に**直接テストが無い**。段 6 レビュー B (段 3 sol の追加所見) が
  性質検索で確認。[T-913] の 4 function はこの範囲を覆っていない。
