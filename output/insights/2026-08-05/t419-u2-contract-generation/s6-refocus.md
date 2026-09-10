# 段 6 fix 後・焦点再レビュー

対象 2 ファイルは commit `7dc3236e` と同一であることを確認した。pytest は実走せず、提示された親の実測値だけを前提にした。

## 所見対応表

| 段 6 所見 | 判定 | 判定理由 |
|---|---|---|
| レンズ A should-fix 1: fuse が負例を mask し、M1 等の帰属が不成立 | `partial` | private validator の正例・負例は fuse から分離され、M1 の診断文字列だけによる kill は解消した。ただし全負例が private を直接呼び、public `validate_generations()` から private への委譲削除を検出しない。`orchestrator/campaign/env_contract.py:278-326`; `orchestrator/tests/test_env_contract.py:419-527` |
| レンズ A should-fix 2: M6 duplicate fixture が no-op successor 拒否と重なる | `closed` | 異なる canonical object の一世代列二本を同一 hash にするため、隣接検査も fuse も発火しない。一意性分岐を削除すれば private validator は受理する。`orchestrator/campaign/env_contract.py:282-314`; `orchestrator/tests/test_env_contract.py:493-510` |
| レンズ A should-fix 3: import-time validation 呼出しの削除が未検出 | `closed` | AST は exact な module-level 呼出しを一件だけ要求し、その行を index/`REGISTRY` の代入行と比較する。現在の順序は validate → index → registry。`orchestrator/campaign/env_contract.py:344-352`; `orchestrator/tests/test_env_contract.py:530-562` |
| レンズ A nit 1: fuse は runtime authority ではない | `partial` | fuse は source bootstrap には効くが、index builder は未検証 mapping も受け取り、global index は再束縛できる。テスト自身がその seam を使用する。production resolver consumer がない現 scope では非 blocker。`orchestrator/campaign/env_contract.py:329-380`; `orchestrator/tests/test_env_contract.py:591-617` |
| レンズ A nit 2: 「env 固有値の不在」という過大保証 | `closed` | 現在の記述は一貫して「literal の単一定義」に限定され、連結・計算値は保証しないと明記する。positive control も存在する。`orchestrator/campaign/env_contract.py:29-31,412-425`; `orchestrator/tests/test_env_contract.py:1149-1200` |
| レンズ B nit 1: `REGISTRY` 順序・`lookup()` 完全 message が未固定 | `closed` | 順序を exact list で固定し、未知文字列、`None`、非 hashable list の完全 message を固定した。`orchestrator/campaign/env_contract.py:349-352,383-390`; `orchestrator/tests/test_env_contract.py:282-305,375-380` |
| レンズ B nit 2: s8c の `lookup` 反射依存は dormant | `partial` | `lookup()` は温存されたが、C12 は引き続き `machine_checkable: false` で通常経路は `_evaluate_undefined()`。active 防壁化はしていないが裁定どおり scope 外で、回帰ではない。`orchestrator/campaign/env_contract.py:383-390`; `orchestrator/campaign/s8c_preregistration_evidence.py:575-607,699-707`; `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:431-485` |

`regressed` は 0 件。

## 残所見

[severity: should-fix] [攻撃シナリオ] `validate_generations()` の `_validate_generations_without_bootstrap_fuse(mapping)` 呼出しだけを削除しても、import-time 呼出しは残り、現行の一世代列は fuse を通過する。負例・collision・M1 は private を直接検査し、public の既存テストは有効な g1 と fuse に達する有効な g2 だけなので、この変異は検出されない。したがって「private 本体」と「module-level public 呼出し」の間に新しい未固定 seam がある。[根拠 `orchestrator/campaign/env_contract.py:316-326,344-352`; `orchestrator/tests/test_env_contract.py:419-562`] [提案] key 不一致など一世代の不正 mapping を public `validate_generations()` に渡す負例を追加し、委譲一行を no-op 化する単一変異を事前登録して kill する。これは land blocker。

[severity: should-fix] [攻撃シナリオ] M7 は同じ `EXPECTED_GENERATION_HASHES` を三テストが共有するため過剰決定である。直接 golden mismatch のほか、resolver の未知 hash と、wrong-env テストの message mismatch が同時に生じる。v2 の三 node 一致は再現性の証拠にはなるが、事後に期待 node を合わせても単一理由性の証拠にはならない。[根拠 `orchestrator/tests/test_env_contract.py:69-76,341-348,565-588`] [提案] 初回 `MISMATCH` と v2 `KILLED` は履歴として維持しつつ、M7 を「冗長 gate」と明記して単独変異の単一理由性集計から外す。三つの独立 kill と数えない。

[severity: nit] [攻撃シナリオ] `_build_contract_sha256_index()` と module global の再束縛 seam は bootstrap fuse を runtime activation authority として扱うと迂回になる。[根拠 `orchestrator/campaign/env_contract.py:329-380`; `orchestrator/tests/test_env_contract.py:591-617`] [提案] 現 wave では source-bootstrap 防壁という射程を維持し、resolver を production 結線する wave で authority を別途設計する。

[severity: nit] [攻撃シナリオ] s8c の凍結 evidence contract は `lookup` を参照するが、現 evaluator dispatch は C12 の反射述語を実行しない。[根拠 `orchestrator/campaign/s8c_preregistration_evidence.py:575-607,699-707`; `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:431-485`] [提案] 温存理由を「凍結参照互換」に限定し、active gate 化は別 wave とする。

## 個別攻撃の結論

1. 現コードの production 経路自体は弱化していない。構造・連番・key、hash、隣接検査の後に fuse が動き、唯一の module-level 構築は `GENERATIONS` → validate → index → `REGISTRY` である。repo 内に別の production 構築・代入経路もない。ただし、上記の public→private 委譲削除は未検出である。
2. M6 seam は本物である。class property の差し替えは canonical object や dataclass 構築を壊さず、各列が長さ一なので他の拒否理由がない。これは実 collision の生成ではなく「collision 時に guard が拒否する」性質の正当な seam である。
3. fix-3 の AST テストは恒真ではない。index と validation を直接入れ替えれば `validation_line < index_line` が偽になる。M9 は呼出し削除を実測しており、順序入替え自体は静的な不等式で検出される。
4. M7 は raw な意味では KILLED だが、単一理由性の証拠には数えない。直接 golden テスト一件は load-bearing だが、残る二件は共有 fixture の派生失敗であり、三つの独立 gate ではない。

## 回帰再確認

| 性質 | 現在の機序 | 判定 |
|---|---|---|
| `lookup()` の object identity | `REGISTRY` は世代列末尾の contract をコピーせず参照し、`lookup()` はその値を返す。`orchestrator/campaign/env_contract.py:349-352,383-386`; `orchestrator/tests/test_env_contract.py:375-380` | 回帰なし |
| 例外 message | `KeyError`/`TypeError` を同一の `EnvContractError` と完全 message に変換し、三入力種で固定。`orchestrator/campaign/env_contract.py:383-390`; `orchestrator/tests/test_env_contract.py:282-305` | 回帰なし |
| `REGISTRY` 反復順序 | `_build_registry()` の linux → pegasus 挿入順を二つの内包表記が保存し、exact list で固定。`orchestrator/campaign/env_contract.py:236-275,344-352`; `orchestrator/tests/test_env_contract.py:375-380` | 回帰なし |
| leaf 性 | production module の import は stdlib のみ。`orchestrator/campaign/env_contract.py:19-27` | 回帰なし |
| 受理集合・g1 値 | contract/canonical hash と registry literal は不変。抽出後も同じ構造検査の後に fuse が動き、loader 非対称性も固定される。`orchestrator/campaign/env_contract.py:82-160,278-326`; `orchestrator/tests/test_env_contract.py:341-348,791-804` | 回帰なし |

## 総括

- **NO-GO**。
- must-fix は 0、land を止める should-fix は 2 件。
- 現行 production コードの受理集合とレンズ B の互換性に回帰はない。
- ただし public→private validator 委譲削除が生存し、production 検査の証拠鎖が一段欠ける。
- M7 の三 node kill は冗長 gate として扱い、単一理由性の証拠から外す必要がある。
- 上記二点を是正してから焦点再レビューを再実施すべきである。
- pytest は実走しておらず、親提示の実測結果だけを前提にした。