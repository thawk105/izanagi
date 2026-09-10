# 段 4 裁定 — [T-1226] 恒久保留 guard の call-only モード

親裁定。real/refuted、採否、scope、プラン v2、変異事前登録。

## 所見の裁定

| # | 出所 | 主張 | 判定 | 採否 |
|---|---|---|---|---|
| 1 | sol#1 | call-only の無条件 return は D360 の費用層 (fixture 先払い防止 38.01→2.33 秒) と plain runner の非ゼロ終端を失う | **real** | 採用。プラン v2 の狭化で対応 |
| 2 | sol#2 / luna#3 | canonical global の wrap だけでは、guard 前に別名へ逃がした参照から本体へ入れる | **real** | 採用。exact 述語へ pre-guard alias 禁止を足す |
| 3 | sol#3 | 新規受理集合は manual 1 形でなく runner 3 族 | **real** | 採用。契約表を 3 族で書き直す |
| 4 | sol#4 / luna#1 | detector が package self-import と `runpy.run_module` を取りこぼす | **real** | 採用。検出規則を拡張 |
| 5 | luna#4 | 現行 13 file に自己読込が無く、call-only 分岐は実 registry 上で発火しない | **real** | 採用 (限界として記録)。scope 外の解決 |
| 6 | luna#5 | held source 総量 (約 1.38MB) に比例する parse 費用が残る | real (nit) | 採用。単一 parse へ統合し追加走査を作らない |
| 7 | luna#6 | 変異帰属に重複がある (default 変更・wrapper 削除は既存 test が先に落とす) | **real** | 採用。新変異は mode 分岐・import 成功・body 未到達へ限定 |
| 8 | sol 反証 | 親 brief の「docs は叙述のみ」は誤り。D347 が `hold_inventory.py` の exact 構造を、D360 が二層防壁を規範化している | **real** | 採用。親の一般化を訂正する (親の主張は「bytes pin が無い」に限って正しい) |

## 決定的な実測 (親、23:40 JST)

裁定 1 の狭化が成立するかは、実在する 2 つの自己読込 consumer が pytest 経由かどうかで決まる。
実コードで確認した。

- `test_s8b_floor_campaign.py:7894-7910`: `python -c` の素のサブプロセスが
  `spec_from_file_location` で当該 file を読む。pytest は関与しない。
- `test_dev_waves_integration.py:2050-2058`: `python -c "from orchestrator.tests import
  test_dev_waves_integration as target; ..."` の素のサブプロセス package import。pytest は関与しない。

**したがって「pytest が駆動する読み込みは call-only でも拒否し続ける」狭化は、
裁定 (a) が救おうとしている 2 経路をどちらも壊さない。**

## プラン v2 (段 2 プランからの差分)

段 2 プランを基礎として採用する。次の 4 点を上書きする。

1. **call-only の import 許可は無条件でない。** wrap 完了後、次のいずれかなら現行どおり
   `GrowthTestHoldBypassRefused` を送出する。
   - 読み込みを駆動しているのが pytest である (enforcement を持たない session の
     `--noconftest` / `--confcutdir` 経路)。判定は import 時の call stack に `_pytest` 由来の
     frame があるかで行い、env や `sys.modules` の在否では判定しない
     (module 自身が `import pytest` 済みのため在否は識別力を持たない — 親が実測)。
   - `__name__ == "__main__"` かつ `plain_runner != "pytest-delegating"`。
     委譲先の無い直接実行が「テスト 0 件で rc=0」という偽緑になるのを防ぐ。
   これにより D360 の費用層は pytest 経路について保存され、緩むのは
   「素の loader / package import」だけになる。
2. **exact 述語へ pre-guard alias 禁止を足す。** call-only を宣言する file では、guard 呼出より
   前に held function 名を別名へ束縛する代入 (`saved = test_held` 型) を binding error とする。
   call-only では canonical 名の wrapper だけが唯一の防壁だからである。
3. **検出規則を拡張する。** 自己読込は次を含む。(a) `spec_from_file_location` 系に自 path を
   渡す形、(b) `runpy.run_path` / `runpy.run_module` に自 path / 自 module 名を渡す形、
   (c) nested subprocess source 内の自 package import (`from <own package> import <own module>`)、
   (d) `exec(open(<self>).read())` 系。静的に解決できない loader は「self-load なし」へ倒さず
   binding error とする (fail-closed)。判定は最終 loader path / module 名と当該 file の同一性で
   行い、`__file__` の出現や API 名の出現では発火させない。
4. **契約表は runner 3 族で書く。** `"none"` / `"manual"` / `"pytest-delegating"` のいずれとも
   call-only を組めるが、1 の (b) により `"none"` と `"manual"` は直接実行時に拒否が残る。

## scope

- in: 上記 1〜4 と、選別条件の decisions fragment。
- out (real だが実装しない): 所見 5 の解決 = `test_s8b_floor_campaign.py` /
  `test_dev_waves_integration.py` の成長比例 node を実際に保留登録すること。
  registry の `count` (59) と `key_sha256` を動かし、各 node の費用実測と D451 判定を要するため
  別 wave とする。**本 wave の成果は「登録できる機構が出来た」までであり、
  実 registry 上の発火はまだ無い。**これを worklog へ明記し、次タスクとして起票する。
- out: 保留の解除 (D499 決定 2 によりユーザー明示命令に限る)、helper 閉包の切り出し (裁定で不採用)。

## 不変条件 (実装子への必須条件)

- registry: `count == 59`、`key_sha256 == 30e646a80e6dfc7c04ec2e249462789ac7cb10f1afaa6979491a3312d5d6508c`、
  held file 13 が wave 前後で同値。
- `@wraps` の `__wrapped__` を保つ (`test_growth_test_holds_contract.py:683-699` と
  `test_real_repo_serialization.py:1132-1171` が `inspect.unwrap` に依存)。
- 解除口は `IZANAGI_RUN_GROWTH_HELD_TESTS` の exact token 1 本のまま。`guard_mode` は解除口でない。
- 現行 13 面の binding は kwarg 無指定のまま受理され続ける。
- 標準 pytest 経路 (conftest collection skip) の受理集合は不変。

## 変異事前登録 (DW-M01)

anchor 逐語は実装後に確定し、`DW-M07` に従い本走前へ再検証する。

| ID | 変異 | 期待 | 単一理由性 |
|---|---|---|---|
| M1 | `guard_mode` の既定値を `"call-only"` へ | KILLED | 既存 import 拒否 test が先に落とすため、期待 node は完全集合で登録する (luna#6) |
| M2 | call-only の early return を wrap ループより前へ移す | KILLED | 新 positive control のみが落とす (現行 13 file は call-only を使わない) |
| M3 | pytest 駆動判定を外し call-only で常に import を許す | KILLED | 新 `--noconftest` 拒否 test のみ |
| M4 | `__main__` + 非委譲 runner の拒否を外す | KILLED | 新 偽緑 test のみ |
| M5 | nested source の二段 parse を外す | KILLED | 新 f-string 検出 test のみ |
| M6 | path 同一性比較を API 名出現へ緩める | KILLED | foreign path negative control (test_check_docs 型) のみ |
| M7 | exact 述語を `len(keywords) in (1, 2)` へ緩める | KILLED | 未知 kwarg / 重複 / 逆順 拒否 test |
| M8 | pre-guard alias 禁止検査を外す | KILLED | alias negative control のみ |
| M9 | `_GUARD_MODES` の literal 検査を外す | KILLED | runtime 未知 literal 拒否 test |
| M10 | package self-import 検出を外す | KILLED | 新 package import 検出 test のみ |

受理集合を縮小する側 (self-load ありで kwarg 無指定を拒否する) には、過剰拒否を検出する正例として
「現行 13 file が今も受理される」既存 meta-test を対にする。
