# 段 6 焦点再レビュー（2 巡目）

対象 2 ファイルは現在の `b7046b8a` と一致し、`7dc3236e` からの差分は public 負例テスト 1 件だけである。pytest は実走せず、親提示の実測結果を前提とした。

## 所見対応表

| 起点・所見 | 判定 | 現在の判定理由 |
|---|---|---|
| 1 巡目 should-fix 1: public → private 委譲削除が未検出 | `partial` | 追加テストの入力は `generation=2` だけが不正で、dataclass は正整数として構築を許し、長さ 1 なので fuse も通る。したがって M10 の no-op では確かに「例外なし」で赤になる。ただし private の連番検査自体を削除しても同じテストが赤になるため、指定された厳密な単一理由性はない。`orchestrator/campaign/env_contract.py:170-179,293-296,316-326`; `orchestrator/tests/test_env_contract.py:427-434` |
| 1 巡目 should-fix 2: M7 の 3 node kill を単一理由と数えている | `closed` | 三テストは同じ fixture を共有しているため冗長であることは変わらないが、親の「M7 を単一理由性の証拠から外し、初回 MISMATCH と v2 KILLED を erratum として残す」裁定は十分。g1 hash 自体は fixture 非依存の reference test でも固定されているため、代替変異は不要。`orchestrator/tests/test_env_contract.py:69-76,341-348,575-598,1092-1121` |
| 1 巡目 nit 1: fuse は runtime authority ではない | `partial` | index builder は validation を要求せず、module global index は再束縛でき、テストもその seam を使う。source bootstrap 防壁としては成立するが runtime activation authority ではない。`orchestrator/campaign/env_contract.py:329-380`; `orchestrator/tests/test_env_contract.py:601-627` |
| 1 巡目 nit 2: s8c の `lookup` 反射依存は dormant | `partial` | `lookup()` は維持されている一方、C12 は `machine_checkable: false` なので通常 dispatch は `_evaluate_undefined()` を選び、`_evaluate_c12()` の反射検査は active gate にならない。`orchestrator/campaign/env_contract.py:383-390`; `orchestrator/campaign/s8c_preregistration_evidence.py:575-607,699-707`; `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:431-486` |
| レンズ A should-fix 1: fuse が M1 等の負例を mask | `closed` | 構造・連番・隣接検査は fuse なし helper に分離され、二世代の正負例は helper を直接検査する。後段 fuse の別拒否で message だけが変わる旧機序はない。`orchestrator/campaign/env_contract.py:278-326`; `orchestrator/tests/test_env_contract.py:454-500,523-537` |
| レンズ A should-fix 2: M6 duplicate fixture が no-op successor と重なる | `closed` | 異なる canonical object の一世代列二本を property seam で同一 hash にする。各列に隣接はなく、private helper のため fuse もなく、hash 一意性だけが拒否理由になる。`orchestrator/campaign/env_contract.py:302-313`; `orchestrator/tests/test_env_contract.py:503-520` |
| レンズ A should-fix 3: import-time validation 呼出し削除が未検出 | `closed` | module-level の exact call が index・`REGISTRY` より前に一件だけ存在することを AST で固定している。`orchestrator/campaign/env_contract.py:344-352`; `orchestrator/tests/test_env_contract.py:540-572` |
| レンズ A nit 1: fuse は runtime authority ではない | `partial` | 1 巡目 nit 1 と同じ。現在の scope では source bootstrap 防壁に限定され、resolver の production 結線はない。`orchestrator/campaign/env_contract.py:329-380`; `orchestrator/tests/test_env_contract.py:601-627` |
| レンズ A nit 2: env 固有「値」の不在という過大保証 | `closed` | 実装は保証を literal の不在に明示的に限定し、計算値・連結値・難読化は保証外と書く。positive control も残る。`orchestrator/campaign/env_contract.py:29-31,412-425`; `orchestrator/tests/test_env_contract.py:1159-1210` |
| レンズ B nit 1: `REGISTRY` 順序・例外 message が未固定 | `closed` | exact 反復順序と、未知文字列・`None`・非 hashable list の完全 message が固定されている。`orchestrator/campaign/env_contract.py:349-352,383-390`; `orchestrator/tests/test_env_contract.py:282-305,375-380` |
| レンズ B nit 2: s8c の反射依存は dormant | `partial` | `lookup()` 削除回帰は起きていないが、active 防壁化もされていない。裁定どおり scope 外である。`orchestrator/campaign/env_contract.py:383-390`; `orchestrator/campaign/s8c_preregistration_evidence.py:575-607,699-707` |

`regressed` は 0 件。

## M10 の攻撃結果

M10 の実測された kill 自体は fuse や dataclass に mask されていない。

- `GenerationEntry(generation=2, ...)` は「正整数」なので構築を通る。`orchestrator/campaign/env_contract.py:170-179`
- tuple、exact entry、key/env 一致、hash 一意性を満たし、一世代なので隣接検査は空である。`orchestrator/campaign/env_contract.py:283-313`
- 委譲を no-op にすると、長さ 1 は fuse を通り正常終了する。`orchestrator/campaign/env_contract.py:316-326`
- したがって親実測の `DID NOT RAISE` は M10 の直接効果である。

ただし、現在のテストは private の連番検査にも依存する。`entry.generation != expected_generation` の分岐だけを削除しても、同じ入力は受理されて同じテストが赤になる。よって、依頼で指定された「委譲削除以外の変異では赤にならない」という単一理由性は満たさない。

## M7 裁定

親の裁定は妥当であり、別の単一理由変異は不要である。

M7 は test-side の共有 fixture を変えるため、直接 golden、resolver、wrong-env の三経路が派生的に失敗する。これを三つの独立 gate と数えず、両 ledger を erratum として保持すれば過大主張は解消する。さらに linux-baremetal と Pegasus の g1 hash は、共有 fixture を使わない独立 reference testでもそれぞれ固定されている。`orchestrator/tests/test_env_contract.py:1092-1121`

段 7 で予定した除外記録が欠けた場合だけ、この行は `partial` に戻すべきである。

## 回帰再確認

| 性質 | 現在の機序 | 判定 |
|---|---|---|
| `lookup()` の object identity | `REGISTRY` は `sequence[-1].contract` を直接保持し、`lookup()` はその値を無包装で返す。identity test もある。`orchestrator/campaign/env_contract.py:349-352,383-386`; `orchestrator/tests/test_env_contract.py:375-380` | 回帰なし |
| 例外 message | `KeyError` と `TypeError` を同じ完全 message の `EnvContractError` に変換し、三入力形で固定。`orchestrator/campaign/env_contract.py:383-390`; `orchestrator/tests/test_env_contract.py:282-305` | 回帰なし |
| `REGISTRY` 反復順序 | `_build_registry()` の linux-baremetal → Pegasus の挿入順を二つの内包表記が保存し、exact list で検査する。`orchestrator/campaign/env_contract.py:236-275,344-352`; `orchestrator/tests/test_env_contract.py:375-380` | 回帰なし |
| leaf 性 | import は stdlib のみで campaign 内 import はない。`orchestrator/campaign/env_contract.py:19-27` | 回帰なし |
| 受理集合 | fix 2 はテスト追加だけ。構造・連番・key・hash・隣接検査の後に fuse が動く現行順序は不変。`orchestrator/campaign/env_contract.py:278-326` | 回帰なし |
| g1 `contract_sha256` | linux-baremetal は `1b2ee853…1dc7`、Pegasus は `e576e9cd…2c01`。registry literal、canonical 計算、独立 reference golden が一致して固定する。`orchestrator/campaign/env_contract.py:145-160,236-275`; `orchestrator/tests/test_env_contract.py:1092-1121` | 回帰なし |

## 残所見

[severity: should-fix] [攻撃シナリオ] public 負例は M10 の委譲 no-op だけでなく、private の連番検査削除でも「例外なし」となって赤になる。M10 の既知の一行差分に対する kill は実在するが、このテストを委譲専用の単一理由 witness とする帰属は成立しない。[根拠 `orchestrator/campaign/env_contract.py:293-296,316-326`; `orchestrator/tests/test_env_contract.py:427-434`] [提案] 有効な一世代 mapping を使い、private helper を monkeypatch の spy に置換して「同一 mapping で一回呼ばれた」と直接 assert する委譲テストを追加する。private の連番実装を spy で遮断し、M10 の期待 node はその専用テストにする。現行負例は public の機能テストとして残す。これは mutation 証拠の land blocker。

[severity: nit] [攻撃シナリオ] `_build_contract_sha256_index()` は未検証 mapping を受け取り、global index は再束縛できるため、bootstrap fuse を runtime activation authority と呼ぶと迂回可能になる。[根拠 `orchestrator/campaign/env_contract.py:329-380`; `orchestrator/tests/test_env_contract.py:601-627`] [提案] 本 wave の保証を source bootstrap に限定し、resolver の production 結線時に activation authority を設計する。

[severity: nit] [攻撃シナリオ] s8c の C12 は `lookup` の反射条件を記述するが `machine_checkable: false` であり、通常評価では当該述語を実行しない。[根拠 `orchestrator/campaign/s8c_preregistration_evidence.py:575-607,699-707`; `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:431-486`] [提案] `lookup()` 温存理由を凍結参照互換に限定し、active gate 化は別 wave とする。

## 総括

- **NO-GO**。
- must-fix は 0、regressed は 0。
- M10 の実測 kill は fuse・dataclass の別拒否による偽 kill ではない。
- ただし追加テストは private 連番検査削除でも赤になり、指定された単一理由性を満たさない。
- M7 を冗長 gate として除外する親裁定は妥当で、代替変異は不要。
- 成果物値、受理集合、identity、message、順序、leaf 性、g1 hash に回帰はない。
- land を止める所見は M10 専用 witness の不足 1 件。
- pytest は実走せず、親提示の実測結果だけを前提とした。