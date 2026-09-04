# 段 6 裁定 — レンズ C / D の所見と親の判定

レンズ C は 4 件、レンズ D は 6 件の所見を返した。親の判定は次のとおり。

## 実装子へ出す修正 (real / 採用 / must-fix)

| # | 出所 | 所見 | 判定 |
|---|---|---|---|
| 1 | C1 | `main` が `--coder-role` 不在でも `knowledge_input` を渡すため、既存の K2 flattened 経路が片側指定として拒否される | **real・採用。** 親が `p3_s4_loop.py:2097`/`:2137` を実測して確認した。唯一実績のある K2 走行 (T-2182) の呼び方が停止する。段 4 の B3 裁定が守ろうとした受理集合を別の場所で壊している。 |
| 2 | C2 | proposal file を通常の `json.load` で読むため、duplicate key で anomaly の停止分岐を迂回できる | **real・採用。** 本 wave が新設した gate を無効化する経路であり scope 内。repo に既存の duplicate 拒否 parser があるので新設ではない。K2 経路だけに適用する。 |
| 3 | D2 | legacy v1 の bytes と digest に独立した golden が無く、中心的な互換性主張が未証明 | **real・採用。** 「旧 digest `6d8674…406` を 1 byte も変えない」は本 wave の設計目的そのもので、定数と producer を同時に変える実装でも緑になる状態は保護と数えられない。歴史的定数の literal 固定なので揮発 payload には当たらない。 |
| 4 | D3 | `test_main_passes_resolved_knowledge_projection_to_proposal_loader` が callee を stub し期待値も同じ producer から作るため恒真 | **real・採用。** F649 の型 (機構の正例が実体を名指ししない)。照合対象を literal で独立させる。 |

## 親が段 7 で行う (実装子へ出さない)

| # | 出所 | 所見 | 判定 |
|---|---|---|---|
| 5 | C3 | D1559 の再裁定が `docs/decisions.md` に無い | **real・採用 (親作業)。** `DW-S07` により 3 台帳は `docs/spool/` の fragment として書く。段 7 で行う。実装の欠陥ではない。 |
| 6 | C4 | `docs/agent-architecture.md` が「consumer: null・未配線」のまま。主張境界 5 点のうち 2 点が成果物に無い | **real・採用 (親作業)。** docs は親が編集する。残り 2 点 (既存 campaign の replay/resume 非主張、K2 wrapper の実成果物 0 件) は insight と worklog へ書く。 |
| 7 | D1 | 変異 9 件のうち 6 件で期待 node が完全集合でない | **real・採用 (親作業)。** `DW-M08` により期待 node は完全集合でなければならない。**`DW-M07` に従い、全件 SURVIVED 期待の probe を先に走らせて観測 node を集めてから本走 spec を確定する。** レンズ D の候補集合は probe の照合材料として使い、そのまま採らない。 |
| 8 | D4 | assertion-only test を「production が拒否した証拠」と記録すると主張が過大 | **real・採用 (親作業)。** レンズ D が各 node の実際の拒否点を file:line で示したので、insight にはその対応表を載せ、assertion-only の 4 node は契約単体テストとして別枠に書く。 |

## 不採用・無処置

| # | 出所 | 所見 | 判定 |
|---|---|---|---|
| 9 | D5 | review ledger の hash pin は本 wave の意味的正しさを証明しない | **real だが nit。無処置。** drift を止める pin としては正しく機能しており、意味の証明は敵対監査と変異が担う。checker 緑の意味を過大に書かないことだけ守る。 |
| 10 | D6 | 新規 27 nodeid が `acceptance_duration_ledger.json` に未登録 | **real だが nit。無処置。** collection からは落ちず、coverage メタテストの 90% 閾値も割らない。既存の繰り越しタスク [T-2250] が「実測なしに直さない」と定めた同型の作業であり、実測 JUnit が出てから足す。worklog に記録だけ残す。 |

## 焦点走の対象 file (レンズ D の指摘を採用して拡張)

親の grep ベースの 43 file に加え、次を明示的に含める。

- `orchestrator/tests/test_pytest_collection_config.py` (test file 集合を束縛するメタテスト)
- `orchestrator/tests/test_acceptance_schedule_order.py` (duration ledger の coverage consumer)
- `orchestrator/tests/test_campaign_import_invariant.py` (追加した cross-package import の consumer)

## レンズが親のために裏取りした事実 (採用)

- 旧 2-key manifest の canonical bytes と digest は byte 一致。digest は `6d867422…406` のまま
  (レンズ C が静的に確認)。**設計の中心目的が第三者検査でも確認された。**
- 拡張形の空 scope 配列・負値・bool・未知 status は producer / WAL / schema が拒否する。
- K0 / K1、sort、trigger-gating の loader 本体と正しさ・identity・性能ゲートに差分なし。
- 既存テストの反転・緩和・skip・削除・xfail 化なし。差分は追加のみ。
- `t2246.m05` と `t2246.m07` が互いに遮蔽しないという親の判断は正しい (レンズ D が独立に確認)。
  `t2246.m08` の単一帰属も静的に正しい。

## 冗長 gate として単独変異の証拠から外すもの (DW-M03)

- `wal.py` の scope / result 再検査 2 箇所 (前段の digest 検査と受領証検査が同じ値を先に見る)。
- 拡張 schema の内側 `required` (外側で既に required)。
- output schema の wrapper 2 階層の required / additionalProperties
  (`projection_guard` の exact key 検査が先に走る)。
  **ただし schema の型・enum・`knowledge_use` item 検査は恒真ではない**ので、
  `t2246.m07` は帰属可能なまま。
