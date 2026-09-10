# [T-2183] 知識水準と 2 段の知識源を材料レポートへ記録する — 材料と実測 (2026-09-03)

wave branch `worktree-dev-wave-t2183-knowledge-provenance`。
実装 commit `7963ff589765cd74843a2b74cbeb4230c58005c3` と
`3d513987cb915fed0c36be6c6052004a1d2293de`。変異本走の HEAD は後者。

## 一次資料

| file | 中身 |
|---|---|
| `verbatim/s2-plan.md` | 段 2 プラン (Codex read-only) の逐語 |
| `verbatim/s3-lens-a.md` | 段 3 敵対相談レンズ A (正しさ境界・受理集合) の逐語 |
| `verbatim/s3-lens-b.md` | 段 3 敵対相談レンズ B (scope・実効性) の逐語 |
| `verbatim/s5-author.md` | 段 5 実装子の報告の逐語 |
| `verbatim/s6-lens-c.md` | 段 6 敵対レビューレンズ C (実装・受理集合) の逐語 |
| `verbatim/s6-lens-d.md` | 段 6 敵対レビューレンズ D (テスト実効性・変異帰属) の逐語 |
| `verbatim/s6-fix.md` | 段 6 fix 子の報告の逐語 (所見対応表を含む) |
| `mutation-spec.json` | 本走の変異 spec (sha256 `92c89612f57f2322703bded3d435afeda83e1776d83b1e6528fad45b2aa604cf`) |
| `mutation-ledger.json` | 本走の結果台帳 |
| `mutation-probe-out.json` | probe 1 の結果 (node 採取と遮蔽の実測) |
| `mutation-probe2-out.json` | probe 2 の結果 (再照準 2 件の確認) |

## 相乗り可否の実測 (タスクが最初に要求した測定)

**機構は相乗りできる。欄は相乗りできない。**

- `orchestrator/campaign/layer3_report.py` の `policy_hint` は、campaign lock の `search_config` を
  出所として材料レポートの top-level へ名前付き欄を置く経路である。この**経路そのもの**は再利用できた。
- `policy_hint` の schema 型は `string` または `null` の単一スカラであり、2 段の source 集合を
  載せられない。**欄そのものの相乗りは不可**である。
- したがって新しい欄を 1 個だけ設計し、その足し方を既存経路と同型にした。

## 着手前から landed だった範囲 (本 wave は触っていない)

- 知識 manifest の parser / producer、受領証 (`knowledge-manifest-receipt/v1`)。
- campaign lock への束縛。実成果物で確認した:
  `p3-s4-loop-s4-autonomous-b6dde2ef` の lock の `identity_preimage` に
  `knowledge_level="K2"` と
  `knowledge_manifest_sha256=6d8674228d05e591a67047c4a098e077f427cb7dd6fdfa3b82d20da2000db406` が入り、
  受領証の digest と一致する。
- 試行台帳 BUILD_START の `knowledge_provenance` と、その書込時・replay 時の双方向検査。

**したがって純増は材料レポート側だけである。** 着手時点で `layer3_report.py`、`layer3_schema.json`、
`test_layer3_report.py` のいずれにも "knowledge" の出現は 0 件だった。

## 段 3 が訂正した親の誤り

親 brief は「材料レポートに記録経路が無い」と書いたが、これは誤りだった。
`layer3_report.py` の `_variant_rows` は WAL record を `dict(record)` で丸ごと `variants[].events` へ
入れるため、**BUILD_START の `knowledge_provenance` payload は既に材料レポートへ逐語で載っていた**。

純増は「名前が付き schema で拘束され受領証まで束縛された射影」であって、データの新規搬入ではない。
この訂正はレンズ B の所見 2・11 による。

## 2 段の関係についての実測

`orchestrator/campaign/wal.py` の受領証読み出しは
`verified_sources != canonical_sources` を fail-closed で拒否する。すなわち**現行コードは
「宣言した source 集合」と「解決・検証して投影した source 集合」の一致を既に強制している。**

したがって 2 段は**現在の producer では必ず一致する**。本 wave はこの一致を前提にせず、
受領証の 2 つの別々の欄からそれぞれ独立に射影する形にした。一致の保証は既存検査に委ね、
新しい検査を足していない。

**この一致は等価変異 `t2183.m02r` が SURVIVED したことで実測されている** (下表)。

## 変異結果 (本走、HEAD `3d513987c`、baseline 824 passed)

| id | 位置 | 期待 | 実際 | 殺した node |
|---|---|---|---|---|
| `t2183.m01` | 材料レポートの欄を常に `null` にする | KILLED | KILLED | `test_knowledge_report_projects_verified_receipt_sources` |
| `t2183.m02r` | 投入欄を宣言欄で上書きする (等価変異) | SURVIVED | SURVIVED | — |
| `t2183.m03` | 新欄 object の未知 key 拒否を外す | KILLED | KILLED | `test_schema_rejects_unknown_nested_knowledge_key` |
| `t2183.m04` | 新欄 object の必須欄を 1 つ外す | KILLED | KILLED | `test_schema_rejects_missing_injected_sources` |
| `t2183.m06` | 比較 consumer の legacy 補正を外す | KILLED | KILLED | `test_campaign_chain_reads_legacy_layer3_without_knowledge_provenance` |
| `t2183.m07r` | 受領証を読まず検証済み台帳射影から作る | KILLED | KILLED | `test_report_rejects_receipt_replaced_after_build_start` |
| `t2183.m08` | 受領証 digest と参照一覧の束縛を外す | KILLED | KILLED | `test_artifact_refs_reject_receipt_changed_after_provenance_read` |

**6 KILLED + 等価変異 1 件。7/7 が期待と一致。** KILLED はいずれも**厳密に 1 node** で、
単一理由性を実測で確認した。等価変異は gate の証拠から除外する。

## 変異手法の制約 (probe 1 で実測)

当初 `t2183.m02` と `t2183.m07` は `orchestrator/campaign/wal.py` へ登録していた。probe 1 で
それぞれ 109 node / 111 node が赤くなり、理由はすべて `contract-loader-drift` だった。

`orchestrator/campaign/wal.py` は campaign lock の `contract_loader_blob_sha256s` の member であり、
**bytes を変えると campaign 作成が先に落ちる。** 変異の狙った関門へ到達する前に前段が全赤になるため、
この閉包の member へ打つ変異は帰属できない。

2 件を `orchestrator/campaign/layer3_report.py` (閉包の member ではない) へ再照準し、probe 2 で
`m02r` が SURVIVED (0 node)、`m07r` が 1 node で KILLED になることを確認してから本走した。
これは `docs/failures.md` の F357 と同じ機序の、変異帰属という別の活動での現れである。

## 親が実走した検査 (すべて緑)

| 検査 | 結果 |
|---|---|
| 焦点走 (変更した 3 test file) | 824 passed |
| consumer 焦点走 (参照関係で洗い出した 14 file) | 1370 passed, 11 skipped |
| AI provenance 全史監査 | 7900 件、新規違反なし |
| 変異本走 baseline | 824 passed |

実装子と fix 子はいずれも sandbox から pytest child を起動できず (`rc=16`)、実走は親が行った。
子の非実走を緑として数えていない。

## 主張の境界 (これを超えて書かない)

- **言える:** 宣言した知識水準と、harness が解決・検証して role 入力へ投影した知識源が、
  campaign identity・試行台帳・材料レポートの三者で束縛された形で記録されるようになった。
- **言える:** 記録された 2 段は、現在の producer では既存の一致検査により同じ集合になる。
- **言わない:** モデルが実際にその知識を読んだこと。planner context の書込みが成功したこと。
  知識の因果的寄与。K2 を条件とする certified な最終選択が主張してよい状態になったこと
  (それは本 wave の判断ではない)。
- **言わない:** Web 由来の知識源の取得内容 digest による再検証が成立したこと。manifest schema は
  全 kind に digest 欄を必須とするが、live 解決は未配線のままであり、本 wave は受理 kind を
  `repo_artifact` に固定した。

## 却下した設計 (一次資料は verbatim/ の各逐語)

段 2 プランと段 3・6 のレンズが提案したもののうち、次は本題の実装ではないと裁定して採らなかった。

- 受領証 `v2` schema の新設。記録される source identity は v1 と同じである。
- 実行経路が事前の受領証を要求して停止する新しい条件。
- 投入集合の独立 digest を campaign identity へ追加すること。既存 manifest digest と同じ集合を
  別形式で再 hash するだけで、既存 campaign と ID が分断される副作用だけが残る。
- lock の 3 状態分岐と downgrade 拒否。
- payload 本文の再 hash 検査。タスクが後続タスクまで先送りすると明示した境界を越える。
- schema の後段に semantic validation を新設すること。指摘された入力は内側の `wal.py` が既に
  拒否しており冗長である。
- 知識対応 legacy report の比較補正。発火する成果物が存在せず、提案された是正は provenance を
  欠いたレポートを黙って通すため主張の連鎖を弱める。
