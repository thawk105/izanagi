## 総括

必読資料と全 record を読了し、書き込み・pytest は行っていない。`validate_condition_freeze_at` の実走は利用可能な一時領域がなく失敗したため、以下は bytes hash の独立再計算とコード経路による静的判定である。

g6 の主要数値は整合している。

- g5 bytes hash と `supersedes_sha256`: `8980803794d858d81e69325e98a8bce6ef9c4da7d65cbab89680dbfd09b7466b`
- evidence 契約 hash: `6944a0b0eed75917c9d489dd43c3b58e637f3d85b97203d1dc60d2cf96fbdf29`
- 12 条件の集合 hash: `817da62a4fc1fd2fad5bbb17c29300e0c24a6813f5c9f7d49c5688723b115a63`
- protected hash の独立導出値: `f71c04ba710a2bd5aee71c441f6e4bea03157a5b7d4f33b99e73b25388c44892`
- g5 protected hash は `4b610022...` で異なるため、空改訂ではない。
- 変化した条件 hash は 2・4・7。連番、schema、source path、normalization、canonical JSON、改行なしも整合した。

`DECIDER_VERSION` を v2 に据え置く親判断は正しい。改訂手続きは判定器・評価器・射影の受理意味を変更した場合だけ bump を要求し、この diff はそれらを変更していない。証拠は `docs/phase3-8c-preregistration.md:272-280`、`orchestrator/campaign/s8c_preregistration.py:45-53`。

### RB-1

- **主張**: g6 の `ruling_reference=D496` は形式検査には通るが、今回の「落ちた構成だけを測り直す」裁定を承認する決定ではない。
- **証拠**: `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g6.json:1`、`docs/decisions.md:20614-20624`、`docs/phase3-8c-preregistration.md:311-316`、`orchestrator/campaign/s8c_preregistration.py:1381-1403`
- **深刻度**: blocker
- **成果物影響**: g6 は「裁定参照あり」と機械認証される一方、参照先は今回の再走単位を承認しておらず、凍結 record から改訂権限を証明できない。
- **推奨**: 今回の裁定を canonical decision として g6 導入 commit に先に含め、その新しい決定番号で g6 を再生成する。後続 commit への決定追加では、導入 commit 時点を検査する `validate_condition_freeze_at` を満たさない。

### RB-2

- **主張**: §5 の既存 JSON は新しい検定再開条件と矛盾し、旧床値再測定と旧節への報告を引き続き要求している。
- **証拠**: 新規則は `docs/phase3-8c-preregistration.md:120-126,153-160`、残存値は同 `:184`。§5 値が保護対象外なのは同 `:268-270`、activation が型や意味でなく記入済みだけを見るのは `orchestrator/campaign/s8c_preregistration.py:1727-1728`。
- **深刻度**: must-fix
- **成果物影響**: 将来の事前登録 metadata または consumer が旧解除条件を読み、正しい新計画を拒否するか、旧規則の成果物として表示する。
- **推奨**: `reopen_requires` と `reporting` を新規則へ追随させるか、解除条件を保護済み本文だけに一本化して値セルから削除する。未保護変更になるため、逐語テストまたは別の束縛も追加する。

### RB-3

- **主張**: g6 の stale 検出は保護対象の 8c 本文には効くが、同じ改訂理由が依存する 8b §10 と §5 値には効かない。
- **証拠**: record 照合対象は 8c source と evidence 契約だけである `orchestrator/campaign/s8c_preregistration.py:1272-1285,1420-1423`。8b 自身も機械 record 不在を認める `docs/phase3-8b-descriptor-design.md:539-546`。既存 pin は `output/s8b-freeze/holdout_freeze.json:5-7`、検査は現在 held `orchestrator/campaign/freeze_verification_hold.py:14-23`。
- **深刻度**: must-fix
- **成果物影響**: g6 生成後に 8b を変更しても g6 は stale にならず、今回の record が説明する規則と実際の 8b bytes の一致を機械証明できない。
- **推奨**: 8b digest を保護 preimage または別の世代 record に束縛する。現行 schema のまま進めるなら、8b と8cを最終化後に g6を生成し、候補 commit 検査に加えて8b hashを明示検査する。ただしこれは完全な機械閉包の代替ではない。

## consumer と証拠契約

正式系列で旧床値を消費する現用経路は、最終判定器の pair 閾値と scale gate である。`orchestrator/campaign/s8b_verdict.py:693-812,929-967,1177-1198`。文書はこの実装を変更しないことを明記しており、ここは正直である `docs/phase3-8b-descriptor-design.md:527-537`。

性質検索では、別系列の Phase 1 報告と opt-in screening にも床値による判断が残る。後者は `orchestrator/campaign/screening_driver.py:38-61,99-102` から `orchestrator/campaign/pipeline.py:1179-1185` へ到達する。ただし今回の上書き範囲は最終判定であり、screening は「それ以外は不変」に含まれるため、今回の consumer 取り残しとは判定しない。

条件 4 の旧評価器は非充足または評価不能しか返さず、条件 7 は `machine_checkable=false` のため常に評価不能である。`orchestrator/campaign/s8c_preregistration_evidence.py:1448-1471,1648-1659,1695-1697`。core・評価器・射影・証拠契約が不変なので、充足側への 1 bit 移動は静的にはない。候補 commit の invariant もゼロを要求する `orchestrator/tests/test_s8c_preregistration_invariant.py:275-288`。実走確認は未実施である。

テストの2逐語は実文書と一致し、固定集合照合と固定 corpus hash を維持しているため緩和ではない。`orchestrator/tests/test_s8c_preregistration_core.py:53-63,439-445,555-603`。全件検索上、追加追随が必要な現用逐語は見つからず、旧 hash は歴史 record と過去資料だけに残る。

## land 前関門の予測

- `check_docs.py`: diff 由来の明白な赤は予測しない。`git diff --check` は成功し、追加行の結合文字と禁止綴りはゼロ。ただし RB-1〜RB-3 は検出しない。
- `spool_fold.py --dry-run`: 現 diff には fragment がないため差分由来の赤はない。新決定を採番する段階で RB-1 を直す必要がある。
- 全史 provenance: Python test を含むため Codex author trailer がなければ赤。正しい author と親の manager/integrator trailer があれば差分由来の赤は予測しない。
- 受入全走: g6・逐語・候補 invariant は静的には通る見込み。8b pin は held のため赤にならないが、これは健全性証明ではなく、hold 解除時は source mismatch が赤になる。

## NO-GO

g6 の hash 鎖、非空改訂、v2 据え置き、充足 bit 不変は整合している。  
ただし裁定参照が改訂を承認しておらず、未保護の旧 §5 値と8b binding 欠落も残る。RB-1を解消してg6を再生成するまで land 不可。