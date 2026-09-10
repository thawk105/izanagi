## GO/NO-GO

GO（静的レビュー）。

fix3 はレビュー A の must-fix とテスト名 nit を閉じており、対象外への変更や既存期待値の変更もありません。pytest は実走しておらず、fix3 後の緑は主張しません。

## 所見対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| レビュー A must-fix: outer 値の型契約 | closed | `variant` / `env_tag` の exact str 検査と、`ts` の exact int/float・finite 検査が追加されています。[reflux_formal_consumer.py:735](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2257-formal-consumer-wal-shape/orchestrator/campaign/reflux_formal_consumer.py:735) |
| レビュー A nit: P-3 のテスト名 | closed | `sequence` が `records` に改名され、consumer は trigger だけを読み、build_start は独立 pin であることが docstring に明記されています。[test_reflux_formal_consumer.py:664](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2257-formal-consumer-wal-shape/orchestrator/tests/test_reflux_formal_consumer.py:664) |
| 他の挙動への退行 | closed | fix3 差分は指定された2 pathだけです。既存テストは P-3 の名前・docstring以外に変更がなく、既存 assertion や期待 reason は不変です。 |

## must-fix

なし。

型契約は JSON 値の範囲で `wal.py` と意味的に一致します。

- `wal.py` は `variant` / `env_tag` に `isinstance(..., str)`、`ts` に bool でない int/floatかつ有限値を要求します。[wal.py:386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2257-formal-consumer-wal-shape/orchestrator/campaign/wal.py:386)
- consumer の exact 検査は、任意の Python オブジェクトについては str/int/float のサブクラスも拒否するため、`isinstance` より狭いです。ただし JSON decode は組み込み型を返し、サブクラス情報を運べないため、JSON 境界では差になりません。
- P-1/P-2 の production record と P-3 literal の float `ts`、fixture の int `ts=0` はいずれも受理されます。[test_reflux_formal_consumer.py:618](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2257-formal-consumer-wal-shape/orchestrator/tests/test_reflux_formal_consumer.py:618) [reflux_origin_fixture_builder.py:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2257-formal-consumer-wal-shape/orchestrator/tests/reflux_origin_fixture_builder.py:369)
- bool は int のサブクラスですが、JSON の `true` から exact bool として到達可能です。`type(True) not in (int, float)` により正しく拒否されます。
- NaN/Infinity は正規 JSON writer からは生成されず、テストの canonicalizer も `allow_nan=False` です。[test_reflux_formal_consumer.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2257-formal-consumer-wal-shape/orchestrator/tests/test_reflux_formal_consumer.py:60) 一方、非標準 JSON tokenを許す decoderや巨大指数の float 化では非有限値が生じ得ます。canonical-list 経路は `wal.parse_line()` を通らないため、consumer 自身の `math.isfinite()` は妥当な防御です。

N-11〜N-13はいずれも baseline WAL の1 fieldだけを変更しています。[test_reflux_formal_consumer.py:783](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2257-formal-consumer-wal-shape/orchestrator/tests/test_reflux_formal_consumer.py:783)

- `_rewrite_wal()` が source、projection、参照 digest、ledger member digestを同期するため、参照整合性を理由とする FC05B/FC04には先取されません。[test_reflux_formal_consumer.py:303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2257-formal-consumer-wal-shape/orchestrator/tests/test_reflux_formal_consumer.py:303)
- candidate wire、physical result、ledger binding、execution provenanceはいずれも不変なので FC04および provenance FC03を通過します。[reflux_formal_consumer.py:643](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2257-formal-consumer-wal-shape/orchestrator/campaign/reflux_formal_consumer.py:643) [reflux_formal_consumer.py:686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2257-formal-consumer-wal-shape/orchestrator/campaign/reflux_formal_consumer.py:686)
- 最終的に `_wal_trigger()` の型検査だけが None を返し、比較箇所で FC05Cになります。[reflux_formal_consumer.py:767](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2257-formal-consumer-wal-shape/orchestrator/campaign/reflux_formal_consumer.py:767)

変異の殺傷関係は次のとおりです。

| 変異 | 殺すテスト |
|---|---|
| M13: 型検査ブロック全体を除去 | N-11、N-12、N-13 |
| M14: bool 除外だけを除去 | N-11 |
| M15: `ts` に str を許可 | N-12 |

M14 と M15 はそれぞれ N-11、N-12で殺され、同じテストに重なっていません。N-13は M13 の独立な variant 側 killer です。

## nit

- 非阻害: optional の N-14はありません。そのため `env_tag` 条件だけを削除する未登録変異の専用 killer はありませんが、現実装の検査は存在し、親が登録した M13〜M15の検査要件は満たしています。

## 総括

fix3 の2所見は closed、partial / regressed はありません。  
型契約は JSON 境界で `wal.py` と整合し、production の float と fixture の int を拒否しません。  
N-11〜N-13は単一理由で FC05Cへ到達し、M13〜M15を予定どおり殺します。  
変更は指定2 pathだけで、既存テストの期待値は不変です。