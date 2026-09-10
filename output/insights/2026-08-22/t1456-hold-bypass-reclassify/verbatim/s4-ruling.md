# 段4 裁定 — T-1456 plan v2

## 段3所見の裁定

- **sol P1: real (採用)。** `known-resolved-bypass`/`rejected-by-hold-guard` は guard の
  保証範囲を越えて一般化していた。具体的に:
  - `plain_runner="pytest-delegating"` の `__main__` 実行は import-time raise ではなく
    `pytest.main(...)` へ委譲され、通常 conftest 経由の enforcing session による
    graceful skip になる (親が「control」実測で観測した挙動と同型)。従って
    「import-time guard が一律に拒否する」と書くと不正確。
  - D360 自身が明記する適用範囲外 (同一 process 内の `__wrapped__` 直呼び・guard 再束縛) を
    「解決済み」という語が誤読させる懸念は real。
  - 対応: 4 entry 共通で、機序を過度に断定しない **outcome 指向**の文言に改める。
    per-entry の `reason` は「どの操作が」「トークン無しでは通らない」かを短く述べ、
    「入力によっては呼び出し時point経由」等の断定を避ける。共通 tail 節として
    「D360 の対象範囲は登録 runner 経路であり、in-process の `__wrapped__` 直呼び・
    guard 再束縛は対象外」を短く含める (4 entry 全部に重複させず、実装子の裁量で
    簡潔な統一文にしてよい)。
  - classification は `known-resolved-bypass` ではなく **`known-guarded-bypass`** を採用
    (「解決済み=もう起こり得ない」という誤読より、「既知の経路だが現在guardされている」の
    方が正確)。
  - effect は `rejected-by-hold-guard` ではなく **`blocked-by-hold-guard`** を採用
    (元の `bypasses-test-hold` と対になる自然な対義語)。
- **sol P2 (`tracking: "T-930"` フィールド改名): 部分採用せず、軽量代替を採用。**
  フィールド名 (`tracking`) の改名は dict の**構造** (key 集合) を変え、
  `test_hold_inventory.py` 側の構造検査 (`assert set(...) == {...}` 系) の対象を広げる
  ため、今回の scope (報告メタデータの正確性回復) に対して過剰。`tracking: "T-930"` は
  維持し、意味の曖昧さは `reason` 文言側で「T-930 により解決済み」を明示することで
  吸収する。読者が誤解する余地は `reason` を読めば解消される。
- **luna P1 (T-1267): real (採用、記録面)。** T-1267 (2026-08-16 起票、entry 606) は
  T-1456 と同一事案であり、現worklogでも別途持ち越されている
  (`docs/worklog.md` 内 `[T-1267] (826)` — 直近tail)。段7の記録で **T-1267 と T-1456 の
  両方**を持ち越しリストから外す必要がある。
- **luna P1 (grep範囲の言い回し): 記録済み・実装への影響なし。** 「実行系consumerは
  2fileのみ、archive/insightsは履歴でconsumerでない」という理解こそが正しく、brief の
  言い回しを精緻化する必要は次wave記録では不要 (brief自体は既にこの段で役目を終える)。
- **luna P1 (entry5/6整合): 採用 (軽微)。** 実装子の裁量で、`bypass_surface` 配列の
  コメント (docstring等、もし自然に書ける場所があれば) に1文添えてよいが必須にはしない
  (成果物影響を書けないnit — DW-G05によりmust-fixにしない)。
- **両レンズ P2 (D347抵触): refuted (確定)。** decisions.md への追記は行わない。

## plan v2 (段5実装子への指示)

対象2 file、対象4 entry (`plain-python-runner`/`pytest-noconftest`/
`pytest-confcutdir-below-suite`/`direct-test-function-call`) の
`classification`・`effect`・`reason` を書き換える。

- `classification: "known-unresolved-bypass"` → `"known-guarded-bypass"` (4箇所 × 2file = 8箇所)
- `effect: "bypasses-test-hold"` → `"blocked-by-hold-guard"` (4箇所 × 2file = 8箇所)
- `reason`: 各entry、「トークン無しでは通らない」ことを簡潔に述べ、機序を断定しすぎない
  文言へ実装子が起案する。少なくとも1箇所 (どの entry でもよい) に D360 を根拠として
  引用し、「in-process の `__wrapped__` 直呼び・guard 再束縛は対象外」を含める。
  4 entry 全部に同じ長い tail を複製する必要はない (簡潔性を優先)。
- `tracking: "T-930"` は変更しない。
- `id`・`command_pattern`/`option`/`option_pattern`/`invocation` は変更しない。
- entry 5/6 (`pegasus-dispatch-env-allowlist`/`pegasus-pytest-addopts-transport`) は
  変更しない。
- `orchestrator/tests/growth_test_holds.py` (`enforce_held_functions`/`_wrap_held_function`)
  は1バイトも変更しない。
- `orchestrator/tests/test_hold_inventory.py` の `_expected_inventory()` と
  `test_inventory_projects_exact_registered_source_sets` 内 `bypass_by_id` assertion
  (brief の変更面アンカー表参照) を、上記と完全一致するよう追随させる。

## 変異事前登録 (DW-M01)

- **MUT-1**: `tools/hold_inventory.py` の `plain-python-runner` entry の `classification`
  を旧値 `"known-unresolved-bypass"` へ差し戻す。期待: `test_hold_inventory.py::
  test_inventory_projects_exact_registered_source_sets` のみ KILLED (golden-copy
  完全一致と `bypass_by_id` 個別assertionの両方が同一テスト関数内で失敗するが検出node
  は1つ)。他テスト (`test_main_dispatches_human_and_json` 等) は live self-reference
  比較のため無反応と予想 — 事前確認: 該当テストは `hold_inventory()` の実際の返り値と
  自己比較するだけなので反応しない。
- **MUT-2**: `tools/hold_inventory.py` の `direct-test-function-call` entry の `reason`
  文字列を1文字改変する。期待: 同じく `test_inventory_projects_exact_registered_source_sets`
  のみ KILLED。
- 両変異とも、無効化時の赤理由は「golden copy 不一致」の1つに絞れる
  (他に同じ入力を拒否する層は存在しない — `hold_inventory()` は他のtestから
  literal比較されない)。

## 実装単位

単一 Codex `role=author` unit (2 file、非重複所有、依存順不要)。
