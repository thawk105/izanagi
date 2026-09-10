# 段 4 裁定 — [T-2008] D1163 plan v2

## 前提と補正

- ユーザー裁定 D1163 の実装方向は不変。certified acceptance で recorded/current closure map の不一致を
  `recorded-current-closure-mismatch` で拒否する 1 条件だけを撤去する。
- 親実測の「repo 内の既存成果物 0 件が対象」は撤回する。repo 内 32 lock は E0 だが、
  外部永続 official root に現行 24-path map と一致する v2 campaign が 5 件ある。
- `FROZEN_MANIFEST` 23 件の bytes は変えない。ただし code 変更により今後生成する admission validator SHA、
  Layer3 generator SHA、historical report JSON bytes は変わる。「producer bytes 全般が変わらない」とは主張しない。

## 所見裁定

| ID | 真偽 | scope / 採否 | 裁定 |
|---|---|---|---|
| A-01/A-03 | real | scope 外、不実装 | persisted WAL の verdict/receipt を全 certified consumer が再検査する共通 gate は無い。これは現行 closure と一致する campaign でも既存の面で、map mismatch 1 条件の撤去と非同値な新 gate 追加になる。規律 2 の live anomaly 即 reject は実装・検査とも不変とし、新規制度は別裁定へ返す。 |
| A-02/B1 | real | scope 内、採用 | historical view の marker を Layer3 だけでなく、P2-2 report、critic digest/online digest、backoff plot provenance、S1 9-pair plot provenance へ投影する。 |
| A-04/B5 | real | scope 外、不実装 | `current-closure-unavailable` は残す。撤去すると D1163 が指定した 1 条件を超える。 |
| A-05 | real | scope 外、不実装 | module-private token が Python 上参照可能な既存限界。今回の type separation を悪化させないが、新しい capability 化はしない。 |
| A-06 | real | scope 内、採用 | prereg manifest SHA 単独削除の変異は後続検査に mask される。予備登録の変異候補から外し、既存正負テストの baseline 保持検査にする。 |
| A-07/B6 | real | scope 内、採用 | 凍結 bytes 不変と新生成 bytes/SHA 変化を分けて記録する。永続成果物は書き換えない。 |
| B2 | real | scope 内、採用 | 外部 official 5 campaign を受理集合変更の実例として記録する。外部 bytes は変えない。 |
| B3 | real | scope 内、採用 | schema は marker を optional で受理して旧 v3 を読めるようにする一方、`certifying_input=true` で marker ありを拒否する。新 historical producer は marker を必ず出す。 |
| B4 | real | scope 内、テストで採用 | reason enum 3 面は削らず、dataclass/schema/oracle legacy reader の各受理を名指して走らせる。共通 constant へのリファクタはしない。 |
| B7 | real | scope 内、採用 | 焦点走は変更 production を直接・間接に参照する test へ拡張する。30 module だけを悉皆とは記録しない。 |
| B8 | real な事実補正 | nit、現行案維持 | test 改名は受入自体を赤にするとは限らないが cost ledger を stale/unknown にする。既存 node id は改名しない。 |

## plan v2 — 実装面

1. `artifact_admission.py`
   - recorded/current blob map 比較と `recorded-current-closure-mismatch` raise だけを撤去。
   - `capture_contract_loader_binding()` と `current-closure-unavailable` 変換、recorded blob 束縛、reason enum を維持。
   - `HistoricalCampaignView.verifier_assessment_basis` を exact literal
     `recorded-at-original-verifier-epoch` として追加。certified view には追加しない。
   - docstring から current exact equality の主張を除く。
2. historical producer
   - `layer3_report.py`、`p2_2_report.py`、`critic/digest.py`、`plot_backoff.py`、
     `plot_s1_9pair.py` の historical projection/rendering へ marker を出す。
   - `online_digest.py` は digest の間接 consumer であり、別の手書き投影が無ければ編集しない。
3. schema
   - `layer3_schema.json` の epoch object に optional marker property + exact const を追加。
   - root conditional で `certifying_input=true` のとき marker を禁止。旧 historical v3 の marker 無しは読み続ける。
4. tests
   - committed closure drift は E1 certified view で受理、uncommitted drift は `current-closure-unavailable` のまま。
   - historical view marker、各5 producer の投影、certified view の marker 不在、certified Layer3 への marker 混入拒否。
   - legacy `recorded-current-closure-mismatch` を schema/dataclass/oracle reader が依然受理。
   - D1163 が列挙した束縛の既存正負テストを走らせ、テストの期待値や fixture hash は甘くしない。

## 変異事前登録 (DW-M01)

1. 撤去した recorded/current map 比較を復活。committed mismatch 受理 8 node だけが
   `recorded-current-closure-mismatch` で赤。uncommitted 拒否は緑のまま。
2. `verifier_assessment_basis` の literal を変更。historical view と各 projection の exact 検査が赤。
3. historical producer 1 面ごとに marker 伝搬を落とす。対応 producer test だけが赤。
4. certified Layer3 marker 禁止の schema conditional を無効化。混入負例だけが赤。
5. `_verify_committed_loader_binding()` を迂回。記録 commit blob/digest 不一致の 24 parameter node が赤。
6. freeze closure G-blob SHA 照合を無効化。`test_closure_bytes_sha_mismatch_rejected` が赤。
7. verifier capability の operation 束縛比較を無効化。operation-only 負例が赤。
8. 8b live launch の current resolver を historical resolver へ変更。live meaning-compatibility 負例が赤。

変異 5〜8 は今回変更する gate ではなく、D1163 が撤去対象外とした束縛が残ることの独立保持検査である。
prereg manifest SHA 単独変異は過剰決定のため登録しない。

## scope 外の裁定パッケージ

1. `current-closure-unavailable` を撤去するか。推奨は規律 7 との整合から撤去だが、D1163 の exact scope を超える。
2. persisted WAL の certified 意味を共通 admission 層で verdict/receipt へ束縛するか。推奨は別 wave で受理集合と
   legacy migration を先に裁定すること。
3. `_CERTIFIED_VIEW_TOKEN` の Python module-private 限界を外部 capability へ移すか。現行の型分離を維持するが、今回強化しない。
4. D956/D967 の後継 supersession を記録するか。依頼指示どおり今回は docs/decisions を改訂しない。

## 成果物影響

- 実装しなければ、code closure 進行後の external official 5 campaign は mismatch 単独で certified 読み出し不能になる。
- historical marker の取り残しを放置すると、P2-2/critic/figure provenance が当時判定と現行再検証を見分けられない。
- scope 外の新 gate を今回混ぜると、D1163 の「撤去 1 条件」を超えて受理集合を別方向へ変える。
