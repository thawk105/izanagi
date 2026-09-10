# 段 1 brief — [T-1226] 恒久保留 guard に call-only モードを足す

裁定 = 2026-08-17 /rulings 全件 第 5 回 索引 7 の択 (a) + 選別条件追加
(控え `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-17-rulings-full5-36rulings.md:70-73`)。

## 実測した前提 (brief 前, 2026-08-17 23:00 JST)

- 裁定文「既に呼出時 wrap」は真。`orchestrator/tests/growth_test_holds.py:599-606` の
  `_wrap_held_function` が呼出時に `GrowthTestHoldBypassRefused` を投げ、
  同 `:646-655` の末尾が **module 読み込み自体**を一律拒否する。後者だけを条件付きにできる。
- 発火条件の実在 (DW-G04): `orchestrator/tests/test_s8b_floor_campaign.py` の
  `spec_from_file_location(..., Path(__file__))` 自己読込 (F351)、および
  `orchestrator/tests/test_dev_waves_integration.py` の subprocess package import。
- 凍結・pin 閉包なし: `growth_test_holds.py` / `hold_inventory.py` の bytes を pin する
  凍結成果物・normative docs は全件検索で 0 件 (docs は failures/archive の叙述のみ)。
  よって `DW-O08` / `DW-O09` / `DW-O10` は不成立。
- 既存被覆 (性質検索): 「held file が自身を loader へ渡すか」を静的に見る検査は 0 件。
  `test_growth_test_holds_contract.py:508-589` は call 形だけを見る。純増検出力 = F351 型の
  受入赤を、受入 lease を消費する前に静的に落とす。

## scope

- in: `enforce_held_functions` に「読み込みは許し held function の呼出だけ拒否する」モード。
- in: 契約テストの call 形 pin の拡張。現行 `:554` は `len(call.keywords) == 1` を要求し、
  新 kwarg を機械拒否するため、同時に直さないと発効しない。
- in: 選別条件「guard binding を持てるか」— decisions fragment + 静的検査 1 本。
- out: 保留の新規登録・再登録 (F351 で取り消した 2 件を含む) と解除。registry の
  `count` / `key_sha256` は wave 前後で不変。
- out: 択 (b) helper 閉包切り出し (裁定で不採用、8 依存で contained でない)。

## 不変条件

- pytest 経路 (conftest collection skip) の受理集合は不変。
- 解除は env exact token のみ。恒久保留を外す方向へ進めない (D499 決定 2)。
- 新モードでも held function の**呼出**は必ず拒否する。正例を 1 本必須にする。

## 親の provisional 裁定 (攻撃対象)

- (P1) 新モードは独立 kwarg とする。`plain_runner` の literal 拡張は採らない —
  同 literal は AST 由来 runner 種別との一致検査 (`:583-588`) を持ち、意味が衝突する。
- (P2) 静的検査は「自身の `__file__` を loader へ渡す」形だけを検出する。
  `spec_from_file_location` の出現だけで発火させると、現に held な
  `test_check_docs.py` が偽陽性になる (実測: 同 file は文字列として当該 API に触れる)。
- (P3) 新モードの正例は synthetic module (tmp_path) で作り、実 registry へ hold を足さない。

## 成果物影響 (DW-G05)

実装しなければ、自己読込を持つ file の成長比例テストは恒久に保留登録できず、
受入の比例費用がその分残る。さらに選別条件の欠落が F351 と同型の受入赤として再発し、
そのたび受入 lease を 1 本失う (= 緑 1 回分の land 窓)。

## 成果物の形・分割

コード + テスト + 記録 (worklog / decisions fragment, insights)。編集面は
`growth_test_holds.py` と `test_growth_test_holds_contract.py` の 2 file で密結合のため、
段 5 は実装子 1 本。段 2 プラン 1 本、段 3 敵対 2 レンズ、段 6 レビュー 2 本。
受入環境は Pegasus (`python3 tools/run_tests.py`)。
