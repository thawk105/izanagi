# 段 6 焦点再レビュー（3 巡目・最終）

対象は commit `e87377b5`。現在の `HEAD` は後続 merge commit だが、対象 2 ファイルは `e87377b5` と同一である。pytest は実走せず、親提示の実測結果だけを前提とした。

## 所見対応表

| 起点・所見 | 判定 | 現在の判定理由 |
|---|---|---|
| レンズ A should-fix 1: fuse が M1 等の負例を mask | `closed` | fuse を含まない helper が構造・連番・key・hash・隣接を検査し、二世代の正負例は helper を直接呼ぶ。後段 fuse の診断文字列で kill する旧機序は除去済み。`orchestrator/campaign/env_contract.py:278-326`; `orchestrator/tests/test_env_contract.py:454-517` |
| レンズ A should-fix 2: M6 duplicate fixture が no-op successor と重なる | `closed` | 異なる env の一世代列二本を使い、property seam で hash だけを衝突させる。隣接検査と fuse は発火せず、一意性 guard だけが拒否理由になる。`orchestrator/campaign/env_contract.py:302-313`; `orchestrator/tests/test_env_contract.py:520-537` |
| レンズ A should-fix 3: import-time validation 呼出し削除が未検出 | `closed` | exact な module-level `validate_generations(GENERATIONS)` を一件要求し、index と `REGISTRY` より前であることを AST で固定している。`orchestrator/campaign/env_contract.py:344-352`; `orchestrator/tests/test_env_contract.py:557-589` |
| レンズ A nit 1: fuse は runtime activation authority ではない | `partial` | import-time bootstrap は防御されるが、index builder は未検証 mapping を受け取り、resolver は再束縛可能な module global index を読む。data-layer/source-bootstrap という裁定 scope 内では非 blocker。`orchestrator/campaign/env_contract.py:329-380`; `orchestrator/tests/test_env_contract.py:618-644` |
| レンズ A nit 2: env 固有「値」の不在という過大保証 | `closed` | 実装自身が保証を literal の不在に限定し、計算・連結・難読化した値は保証外と明記する。免除の有無を比較する positive control もある。`orchestrator/campaign/env_contract.py:29-31,412-425`; `orchestrator/tests/test_env_contract.py:1176-1227` |
| レンズ B nit 1: `REGISTRY` 順序・`lookup()` 完全 message が未固定 | `closed` | exact 順序を list で固定し、未知文字列・`None`・非 hashable list の完全 message を検査する。`orchestrator/campaign/env_contract.py:349-352,383-390`; `orchestrator/tests/test_env_contract.py:282-305,375-380` |
| レンズ B nit 2: s8c の `lookup` 反射依存は dormant | `partial` | `lookup()` は存在するが、C12 は `machine_checkable: false` なので通常 dispatch は `_evaluate_c12()` を呼ばない。scope 外の既知制限であり回帰ではない。`orchestrator/campaign/env_contract.py:383-390`; `orchestrator/campaign/s8c_preregistration_evidence.py:575-607,695-707`; `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:431-486` |
| 1 巡目 should-fix 1: public → private 委譲削除が未検出 | `closed` | public 関数が同一 mapping を一回 helper へ渡すことを spy が直接固定し、public 負例も維持されている。`orchestrator/campaign/env_contract.py:316-326`; `orchestrator/tests/test_env_contract.py:427-451` |
| 1 巡目 should-fix 2: M7 の三 node kill を単一理由と数える | `closed` | 共有 fixture による冗長性自体は残るが、親裁定により M7 は単独変異の単一理由性証拠から除外された。hash 値は共有 fixture 非依存の reference golden でも固定される。`orchestrator/tests/test_env_contract.py:69-76,341-348,592-615,1109-1138` |
| 1 巡目 nit 1: fuse は runtime authority ではない | `partial` | レンズ A nit 1 と同じ。source bootstrap 防壁は成立するが、runtime activation authority は実装していない。`orchestrator/campaign/env_contract.py:329-380`; `orchestrator/tests/test_env_contract.py:618-644` |
| 1 巡目 nit 2: s8c の反射依存は dormant | `partial` | レンズ B nit 2 と同じ。凍結参照互換は維持するが active gate ではない。`orchestrator/campaign/s8c_preregistration_evidence.py:575-607,695-707`; `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:431-486` |
| 2 巡目 should-fix: public 負例が M10 専用 witness ではない | `closed` | 新 spy は helper を置換した後に public 関数を呼ぶため、private の連番・key・hash・隣接検査の削除や緩和は test body で実行されない。M10 の委譲 no-op では `calls` が空になり、回数 assert が直接失敗する。`orchestrator/campaign/env_contract.py:316-326`; `orchestrator/tests/test_env_contract.py:427-441` |
| 2 巡目 nit: fuse は runtime authority ではない | `partial` | 未検証 mapping から index を構築できる seam は維持されるが、裁定済み scope 外である。`orchestrator/campaign/env_contract.py:329-380`; `orchestrator/tests/test_env_contract.py:618-644` |
| 2 巡目 nit: s8c の反射依存は dormant | `partial` | `lookup()` 削除回帰はないが、C12 の evaluator は通常経路では発火しない。`orchestrator/campaign/env_contract.py:383-390`; `orchestrator/campaign/s8c_preregistration_evidence.py:575-607,695-707` |

`regressed` は 0 件。

## 残所見

[severity: nit] [攻撃シナリオ] `_build_contract_sha256_index()` は未検証 mapping を受け取り、module global index も再束縛できるため、bootstrap fuse を runtime activation authority と呼ぶと迂回可能になる。[根拠 `orchestrator/campaign/env_contract.py:329-380`; `orchestrator/tests/test_env_contract.py:618-644`] [提案] 本 wave の保証を source bootstrap 防壁に限定し、resolver の production 結線時に activation authority を別設計する。

[severity: nit] [攻撃シナリオ] s8c C12 は `lookup` の実在を記述するが `machine_checkable: false` であり、通常評価では反射述語を実行しない。[根拠 `orchestrator/campaign/s8c_preregistration_evidence.py:575-607,695-707`; `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:431-486`] [提案] 温存理由を凍結参照互換に限定し、active gate 化は別 wave とする。

[severity: nit] [攻撃シナリオ] spy は `def spy(candidate)` なので、意味が同じキーワード呼出し `_validate_generations_without_bootstrap_fuse(mapping=mapping)` へ内部 refactor すると `TypeError` になる。「委譲削除だけで赤」を文字どおりには満たさないが、M10 の no-op 帰属や成果物には影響しない。[根拠 `orchestrator/campaign/env_contract.py:278-280,316-320`; `orchestrator/tests/test_env_contract.py:435-441`] [提案] 将来触る場合は positional/keyword を正規化する spy にする。

[severity: nit] [攻撃シナリオ] helper 呼出しを fuse loop の後へ移しても、現行 spy の一世代正例、public 一世代負例、二世代 fuse 正例はすべて期待どおりになり得る。この場合、不正な二世代入力は構造検査より先に fuse の診断で拒否され、旧 mask が診断面だけ再発する。[根拠 `orchestrator/campaign/env_contract.py:316-326`; `orchestrator/tests/test_env_contract.py:427-451,540-554`] [提案] 現 scope では受理集合が変わらないため非 blocker。順序を保証として掲げる場合だけ、二世代入力で「spy 呼出し後に fuse」となることを固定する。

## spy witness の帰属

M10 で `orchestrator/campaign/env_contract.py:320` を no-op にすると、spy は一度も呼ばれず `orchestrator/tests/test_env_contract.py:440` だけを直接理由に当該 spy test が失敗する。

private helper 内の連番・key・hash・隣接 guard（`orchestrator/campaign/env_contract.py:293-313`）を削除・緩和しても、test body では line 438 の spy に置換されるため当該 test は影響を受けない。実 helper は module import 時の `orchestrator/campaign/env_contract.py:344-348` では一度動くが、これらの弱化変異は有効な production g1 を拒否しない。無条件 raise など import 自体を壊す変異は collection 全体の破断であり、spy node による M10 の誤帰属ではない。

既存 public 負例（`orchestrator/tests/test_env_contract.py:444-451`）は private 連番 guard 削除でも失敗するため、単独では引き続き非専用である。しかし現在は専用 spy が別に存在し、親の再登録どおり M10 の実測二 node を「専用 witness 1 件＋public 機能負例 1 件」と説明できる。

`monkeypatch` は test 関数の fixture 引数として取得され、line 438 の属性置換は関数終了時に復元される。repo 内に同名 fixture の上書きはなく、他テストへ残る手動代入もない。

## 回帰再確認

| 性質 | 静的確認 |
|---|---|
| `lookup()` の同一性 | `REGISTRY` は列末尾 contract をコピーせず保持し、`lookup()` はその object を直接返す。identity test も exact `is`。`orchestrator/campaign/env_contract.py:349-352,383-386`; `orchestrator/tests/test_env_contract.py:375-380` |
| 例外 message | `KeyError` と `TypeError` を同じ完全 message へ変換し、未知文字列・`None`・list で固定。`orchestrator/campaign/env_contract.py:383-390`; `orchestrator/tests/test_env_contract.py:282-305` |
| `REGISTRY` 反復順序 | `_build_registry()` の linux-baremetal → pegasus 挿入順を二段の内包表記が保存し、exact list で固定。`orchestrator/campaign/env_contract.py:236-275,344-352`; `orchestrator/tests/test_env_contract.py:375-380` |
| leaf 性 | import は stdlib のみで campaign 内 import はない。`orchestrator/campaign/env_contract.py:19-27` |
| 受理集合 | fix 3 はテスト 1 件のみの追加。production は構造・連番・key・hash・隣接検査の後に fuse を適用し、`lookup()` の成功・拒否経路も不変。`orchestrator/campaign/env_contract.py:278-326,383-390` |
| g1 `contract_sha256` | linux-baremetal は `1b2ee85346a4…1dc7`、Pegasus は `e576e9cd1369…2c01`。現行 literal と canonical 計算に加え、独立 reference calculator が両値を固定する。`orchestrator/campaign/env_contract.py:145-160,236-275`; `orchestrator/tests/test_env_contract.py:69-76,1109-1138` |

## 総括

- **GO**。
- must-fix / should-fix / regressed は 0 件。
- M10 の委譲 no-op は専用 spy の未呼出しで直接検出される。
- private helper 内の削除・緩和変異は spy に遮断され、M10 の kill 理由へ混入しない。
- monkeypatch の test 間漏洩経路はない。
- M7 は親裁定どおり冗長 gate として単独変異証拠から除外されている。
- production 値・受理集合・identity・message・順序・leaf 性・g1 hash に回帰はない。
- 残る 4 件は scope 外または診断・テスト堅牢性の nit で、land blocker ではない。