---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: dev-wave-t1226-hold-guard-callonly
seq: 1
title: 恒久保留 guard に call-only モードを足し、選別条件を機械化した — 費用防壁を pytest 経路について保存する狭化を採り、実 registry 上の発火はまだ無いと明記する (コード + テスト、branch worktree-dev-wave-t1226-hold-guard-callonly、変異 matrix = baseline PASSED・11/11 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- ユーザー裁定 (2026-08-17 /rulings 全件 第 5 回 索引 7、択 (a) + 選別条件) を実装した。
  `enforce_held_functions` へ独立 kwarg `guard_mode` を足し、`"call-only"` では module の
  読み込みを許して held function の呼出だけを拒否する。既定は現行と同じ `"import-and-call"`。
- **親は裁定の実装形を狭めた。** call-only の import 許可を無条件にすると、D360 が実測で置いた
  費用層 (呼出時のみの拒否では `--noconftest` 経路が 38.01 秒かけて実 repository 全走査を
  完走してから拒否する。読み込み時なら 2.33 秒) を失う。両レンズが blocker として指摘した。
  親は「pytest が読み込みを駆動している場合」と「委譲先の無い `__main__` 直接実行」では
  call-only でも拒否を残す形を採った。**この狭化が裁定を壊さない根拠は実測である** —
  裁定 (a) が救う 2 経路 (`test_s8b_floor_campaign.py` の自己 `spec_from_file_location` と
  `test_dev_waves_integration.py` の package self-import) はどちらも素の `python -c`
  サブプロセスで、pytest を通らない。判定は call stack に `_pytest` 由来 frame があるかで行う。
  `sys.modules` の在否は識別力を持たない (guard は module 末尾で走るため、module 自身の
  `import pytest` が既に済んでいる)。
- **本 wave の成果は「登録できる機構」までであり、実 registry 上で call-only を使う file はまだ無い。**
  現行 13 held file はいずれも自己読込を持たない。実際に発火させるには
  `test_s8b_floor_campaign.py` / `test_dev_waves_integration.py` の成長比例 node を保留登録する
  必要があり、registry の `count` (59) と `key_sha256` を動かすため別 wave とした
  ({{T:register-call-only-holds}})。
- 選別条件「guard binding を持てるか」は契約テストで機械化した。母集合は登録済み held file だけで、
  repo 成長に比例させない。判定は最終 loader path / module 名の同一性で行い、API 名や `__file__` の
  出現では発火させない (現に保留中の `test_check_docs.py` が偽陽性になるため。同 file の
  `spec_from_file_location` 3 箇所はいずれも他 path を読む)。
- **親が撤回・訂正した自分の主張が 3 件ある。**
  1. 段 1 で「`growth_test_holds.py` を規範化する docs は failures/archive の叙述のみ」と書いたが、
     D347 が `hold_inventory.py` の exact 構造を、D360 が二層防壁を規範化している。
     親の主張は「live な source-byte pin が無い」に限って正しい (レンズ A が反証)。
  2. 段 4 の不変条件に「call-only でも held function の呼出は必ず拒否する」と無条件に書いたが、
     正しくは canonical 名についてのみ真である。`module.test_x.__wrapped__()` や
     `inspect.getclosurevars` 経由では token 無しで本体へ到達できる。`@wraps` は
     `test_real_repo_serialization.py` の `inspect.getsource(inspect.unwrap(...))` が依存しており
     除去できないため、**閉じずに残余として記録する** ({{D:call-only-hold-guard}})。
  3. 変異事前登録 (段 4 の M1〜M10) と、親が段 6 で書いた spec builder の対応が食い違っていた。
     M5 と M10 の意味が入れ替わり M10 が欠けていた。焦点再レビューが blocker として突き、
     親が spec を M1〜M10 と 1 対 1 対応する形へ作り直した。
     M11 (frame 判定不能を許可側へ倒す) は段 6 レビュー由来の**追加登録**であり事前登録ではない。
- 段 6 の敵対レビュー 2 本と焦点再レビューが real 所見を 11 件出し、fix 3 巡で閉じた。
  特に効いた 2 件:
  - pre-guard の別名退避を「列挙して塞ぐ」形にしていたため、`globals()["<held 名>"]` が素通りし、
    かつ `test_s8b_repo_scan_invariant.py` の `_run()` のような**安全な**関数内参照を過剰拒否して
    いた。**「import 時に評価される位置に held 名が名前としても文字列としても現れてはならない」**
    という閉じた規則へ置き換えて、穴と過剰拒否を同時に閉じた (関数本体の global 参照は呼出時に
    解決されるため必ず wrapper を引く)。
  - 実 consumer 2 file (合計約 557KB) を毎回まるごと parse していた。その file が育つほど受入が
    遅くなるため、固定サイズの synthetic 複製へ置き換えた (複製には由来の file:line を書く)。
    実データに対する保証は、既に全 held file を走査している既存 loop が担う。
- **セッション環境由来の非帰属赤を 1 件観測した。** 親のセッションに `FORCE_COLOR=3` が入っており、
  それが subprocess へ漏れて `test_plain_pytest_delegating_runner_is_not_over_rejected` の
  サマリ正規表現を外していた。色環境を外した単独再走で `1 passed` を実測して非帰属を確定した。
  `FORCE_COLOR` は dispatch の env allowlist に無いため、計算ノードで走る変異 matrix と受入全走には
  現れない。bounded local の焦点走でだけ起きる ({{F:force-color-leak}})。
- 工数: codex 子 8 本 (plan 1、consult 2、author 1、review 2、fix 3 のうち fix は 3 本で計 9 本)、
  すべて `check_codex_output.py` rc=0。待ち手が出力ゼロのまま「完了」通知を出す事象が 6 回起き、
  そのたび pid で producer の生存を確認して張り直した。段 6 の review 子 2 本は `--lane` を
  consult 段以外へ渡して rc=2 で落ち、投げ直した。

- 段 8 (スキル自己改善) の候補は 2 件。1 件 (待ち手の偽完了通知) は既存 F352 への再発追記で処理した。
  もう 1 件は `DW-O01` へ「`--lane` は consult 段だけに渡す」を書く是正で、本 wave で実際に
  踏んで review 子 2 本を rc=2 で失った実測がある。**実装できなかった。** 追記すると
  `docs/dev-wave/**` の L1.5 予算を 9608 > 9566 bytes で超過し、さらに `DW-O01` の
  model 権威行 exact 検査にも抵触する (実測)。予算を上げる変更は通常の自己改善に含めないため、
  DW-S08 に従い編集を戻して裁定パッケージへ送る ({{T:dw-o01-lane-constraint}})。

## 次の一手差分

### 完了

- [T-1226] guard の call-only モードと選別条件の機械化を実装し、変異 matrix
  (baseline PASSED、11/11 KILLED、SURVIVED 0、MISMATCH 0) で確認した。
  受入全走はこの記録を含む最終 tip で実行する (land はその緑の受領証に依る)。
  実 registry 上の発火は無く、保留登録は {{T:register-call-only-holds}} が引き継ぐ。
  remaining: none
  base: ee83f31728ecb8a9d57868773ad404dbb9269ac29fadf090c4e3a1c24e699af1

### 新規

- {{T:register-call-only-holds}} **P2・新規**: `test_s8b_floor_campaign.py` と
  `test_dev_waves_integration.py` の成長比例 node を、call-only binding を付けて実際に保留登録する。
  registry の `count` (59) と `key_sha256` が動くため、各 node の費用実測と D451 判定を伴う。
  登録時は `__wrapped__` 経由の到達を `tools/hold_inventory.py` の `bypass_surface` へ書く。
- {{T:dw-o01-lane-constraint}} **P2・ユーザー裁定待ち**: `DW-O01` へ「`--lane` は consult 段だけ」を
  書く是正が L1.5 予算 (9608 > 9566 bytes) と model 権威行の exact 検査で入らない。
  収容先 (新規 L2 節 / 既存節の縮約 / 予算の独立審査) を裁定する。
