# [T-1226] 恒久保留 guard の call-only モード

- wave: `worktree-dev-wave-t1226-hold-guard-callonly`
- 日付: 2026-08-17 22:40 JST 開始
- 裁定: 2026-08-17 /rulings 全件 第 5 回 索引 7 (択 (a) + 選別条件)
- 起点 main: `2a3b5055`

## 何をしたか

`enforce_held_functions` に独立 kwarg `guard_mode` を足した。`"call-only"` では module の
読み込みを許し、held function の呼出だけを拒否する。既定 `"import-and-call"` は現行と同じ分岐を
通り、登録済み 13 面の binding は kwarg 無指定のまま受理される。

併せて「保留候補は guard binding を持てること」を契約テストで機械化した。

## 親が実装形を狭めた点と、その根拠

裁定は「読み込みを許す」だが、無条件に許すと D360 が実測で置いた費用層を失う。
D360 の実測値は、呼出時のみの拒否では `--noconftest` 経路が **38.01 秒**かけて実 repository
全走査を完走してから拒否する (読み込み時なら **2.33 秒**) というものである。

そこで call-only でも次の 2 つは拒否を残した。

1. 読み込みを駆動しているのが pytest である場合 (`--noconftest` / `--confcutdir`)。
   判定不能 (frame 取得不能) も拒否へ倒す。
2. `__name__ == "__main__"` かつ plain runner が pytest へ委譲しない場合
   (テスト 0 件で rc=0 になる偽緑を防ぐ)。

**この狭化が裁定を壊さない根拠は実測である。** 裁定が救う 2 経路はどちらも素の `python -c`
サブプロセスであり、pytest を通らない。

| 経路 | 場所 | pytest 経由か |
|---|---|---|
| 自己 `spec_from_file_location` | `orchestrator/tests/test_s8b_floor_campaign.py:7894-7910` | いいえ |
| package self-import | `orchestrator/tests/test_dev_waves_integration.py:2050-2058` | いいえ |

`sys.modules` に pytest があるかでは識別できない。guard は module 末尾で走るため、
その時点で module 自身の `import pytest` が既に済んでいるからである (親が実測)。

## この wave が達成していないこと

**実 registry 上で call-only を使う file はまだ無い。** 現行 13 held file はいずれも自己読込を
持たない。機構は出来たが、実際に発火させるには `test_s8b_floor_campaign.py` /
`test_dev_waves_integration.py` の成長比例 node を保留登録する必要があり、それは registry の
`count` (59) と `key_sha256` を動かすため別 wave とした。

## 閉じなかった迂回 (記録で処理)

- `module.test_x.__wrapped__()` / `inspect.getclosurevars` 経由で、解除 token 無しに本体へ到達
  できる。`@wraps` は `test_real_repo_serialization.py:1132-1171` の
  `inspect.getsource(inspect.unwrap(...))` が依存しており除去できない。
- pytest の test / plugin が別 thread から import する経路、`__name__` を `_pytest.*` に偽装する経路。

いずれも D347 の `bypass_surface` が扱う既知迂回と同じ系列として扱う。call-only を実際に使う
file を登録するときに `tools/hold_inventory.py` の `bypass_surface` へ書く。

## 変異 matrix

anchor commit `124cd8e8` の使い捨て worktree (`tools/mutation_worktree.py --runner-mode dispatch`)。
runner 範囲は `test_growth_test_holds_contract.py` + `test_hold_inventory.py`。

**baseline PASSED、11/11 KILLED、SURVIVED 0、MISMATCH 0。**

M1〜M10 は段 4 の事前登録に 1 対 1 で対応する。M11 (frame 判定不能を許可側へ倒す) は
段 6 レビュー由来の追加登録であり事前登録ではない。期待 node は probe 走行 (全件 SURVIVED 期待)
で観測した完全集合を使った。

| ID | 変異 | 期待 node 数 |
|---|---|---:|
| M1 | `guard_mode` の既定値を call-only へ | 3 |
| M2 | call-only の early return を wrap より前へ | 5 |
| M3 | pytest 駆動判定を外す | 2 |
| M4 | 非委譲 `__main__` の拒否を外す | 1 |
| M5 | nested source の二段 parse を外す | 1 |
| M6 | path 同一性比較を常に self へ | 7 |
| M7 | keyword 完全一致を緩める | 3 |
| M8 | pre-guard 参照検査を外す | 1 |
| M9 | `_GUARD_MODES` の literal 検査を外す | 3 |
| M10 | package self-import 検出を外す | 1 |
| M11 | frame 判定不能を許可側へ (追加登録) | 1 |

spec は `mutation-spec.json`、生結果は `mutation-out.json`。

## 親が撤回・訂正した主張

1. 段 1 の「`growth_test_holds.py` を規範化する docs は叙述のみ」は誤り。D347 が
   `hold_inventory.py` の exact 構造を、D360 が二層防壁を規範化している。親の主張は
   「live な source-byte pin が無い」に限って正しい (レンズ A が反証)。
2. 段 4 の不変条件「call-only でも呼出は必ず拒否する」は無条件には成り立たない。
   canonical 名についてのみ真である (レンズ A が反証)。
3. 親が書いた変異 spec builder が、段 4 の事前登録 M1〜M10 と対応していなかった
   (M5/M10 の意味が入れ替わり M10 が欠落)。焦点再レビューが blocker として突き、親が作り直した。

## レビューで閉じた主な所見

- pre-guard の別名退避を列挙で塞ぐ形は、`globals()["<held 名>"]` を取りこぼし、同時に
  `test_s8b_repo_scan_invariant.py` の `_run()` のような安全な関数内参照を過剰拒否していた。
  **「import 時に評価される位置に held 名が名前としても文字列としても現れてはならない」**という
  閉じた規則へ置き換えて両方を閉じた。
- 実 consumer 2 file (約 557KB) の全量 parse は、その file が育つほど受入を遅くする。
  固定サイズの synthetic 複製へ置き換えた。
- 検出器が `if False:` 内や局所 shadow で self-load を誤認し、import 拒否を不当に解除できた。
- 関数内 `import runpy` を検出できず、判定不能にも倒れていなかった (fail-open)。

## 環境由来の非帰属赤

親セッションの `FORCE_COLOR=3` が subprocess へ漏れ、
`test_plain_pytest_delegating_runner_is_not_over_rejected` のサマリ正規表現を外していた。
色環境を外した単独再走で `1 passed` を実測し非帰属を確定した。`FORCE_COLOR` は dispatch の
env allowlist に無いため、計算ノードで走る変異 matrix と受入全走には現れない。
