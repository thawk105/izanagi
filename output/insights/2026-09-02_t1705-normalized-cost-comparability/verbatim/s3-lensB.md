## 検証した範囲

- 親 brief、段 2 プラン、D932、D831、事前登録 §10、現行 cost 計算層の逐語資料を全文確認した。
- `tools/codex_reasoning_ab.py` の schedule 軸、paired identity、三分類、cost 集約、成果物書込を静的に照合した。
- `tools/t189_price_snapshot.py` の SKU、receipt token mapping、closed schema を確認した。
- 既存 cost fixture と段 2 のテスト変更案を照合した。
- pytest は実行しておらず、以下は静的検査結果である。

## 所見 (重大な順)

1. **重大・正しさ境界: 二つの key の完全一致は、paired protocol 上の比較可能性に十分ではない。** 例えば pair unit を `u1=(b01, attempt 1)`、`u2=(b02, attempt 1)` とし、arm A が `u1=observed, u2=unavailable`、arm B が `u1=unavailable, u2=observed` なら、両 axis の vector はともに `(1,1,0,2)` で key は完全一致するが、合計は別々の pair unit から得た値であり paired 差として読めない。per-attempt 行も、別 block の observed 行同士が `(1,0,0,1)` で一致する。プラン自身がこの問題を認識しながら残余リスク扱いにしているが、これは選択性を補正できないという限界だけでなく、`must-match` 規則の偽陽性である。第二段には count だけでなく、少なくとも status ごとに分割した arm-neutral な pair identity `(block_id, attempt)` の集合が必要である。
根拠: `brief.md:39-45`、`s2-plan.md:16-20,47-52,72-81,175-179`、`tools/codex_reasoning_ab.py:9732-9742,10644-10663,10960-10995`
影響: `accounted_amount` と受理集合は変わらないが、成果物が比較可能として参照する相手集合が過大になり、下流の arm 差が対応のない試行を paired 値として引く可能性がある。

2. **高・正しさ境界: `basis_key` は比較する実験世代を識別せず、別成果物間で衝突する。** `benchmark_task_id`、`stage`、`cache_condition` は同じ登録を反復すれば再利用されるため、独立した二つの aggregate が同じ価格基盤と count を持つだけで key が一致する。親 brief は「行自身から判定」を要求する一方、プランには「同一 result 内だけで比較する」という制約も、既に生成されている `manifest_sha256` もない。同一成果物内限定なら明示的な rule にすべきであり、抽出した行同士も比較対象にするなら comparison universe の identity が必要である。
根拠: `brief.md:34-37`、`s2-plan.md:28-45,83-98`、`tools/codex_reasoning_ab.py:10763-10769`
影響: 同一成果物内の値と受理集合は変わらないが、別実験・別登録世代の行が誤って同じ比較集合を参照するため、再実験間差を arm 間差として読む偽陽性が生じる。

3. **中・整合・実効性: 予定テストは上記の意味論を証明せず、実際の異なる arm も十分に覆わない。** 提案されているのは単一 block、単一 generation の observed/unavailable/not-incurred の count 検査であり、equal-count/different-identity の反例がない。さらに既存 `_bound_price_schedule` の二行は model が異なる一方で `arm` は双方 `"max"` なので、そのまま使う sol/luna equality は異なる arm 間比較の実例にならない。
根拠: `s2-plan.md:116-139`、`orchestrator/tests/test_codex_reasoning_ab.py:6519-6554,15587-15617,15680-15832`
影響: 値と受理集合は変わらないが、テストが通っても主要な偽陽性と実 arm 間参照を検出できず、比較可能性を検証済みと誤認する。

## プランのうち妥当と確認できた点

- `basis_key` と分母情報を分離する二段構造自体は妥当である。ただし `accounted_total_key` は count summary に留めず、paired identity を含める必要がある。
- `requested_model` と `unit_prices` の除外は妥当である。§10 は model 別公表単価を同じ USD 単位へ正規化することを目的としている。receipt 対応は、入力=`input_tokens-cached_input_tokens`、cached input=`cached_input_tokens`、出力=`output_tokens`、cache write=数量なし、と全 SKU で完全一致するよう closed validation されている。`price_version` が同じなら、この mapping と tier/context band も同じ凍結 snapshot に束縛される。
- `arm` は比較対象なので除外が正しい。`accounted_amount` と `components` も測定値そのものなので key へ含めるべきでない。
- `certification_status` の除外は現在の D932 と整合する。これは数値の定義ではなく利用政策であり、top-level の `not-certified` を維持すればよい。
- 四 count には、各 axis について `scheduled_attempt_count = attempt_count + unavailable_count + not_incurred_count` が成立する。per-attempt では三状態のいずれかが一つだけ 1 になる。現行ループは各 mapped attempt で scheduled を一度増やし、その後ちょうど一分類だけを増やすため、D932 の「黙って分母から外さない」という文字どおりの要求は満たす。
- `not-incurred` と `unavailable` の区別は意味を持つ。前者は launch 前か paired mate 非起動で exact zero を確認した非発生、後者は receipt replay failure または観測根拠のない zero である。これは §10 と D932 の「観測済み・観測不能・非発生」に対応する。
- partial 性について、`coverage_status` と `unaccounted_token_categories`、凍結された receipt mapping が保証するのは「全 arm が cache write を同じ規則で未計上にすること」までである。arm ごとの未計上 cache-write 数量が同程度であることは保証しないため、数量が系統的に違っても二つの key は一致する。これは partial な accounted subtotal の比較としてのみ妥当であり、完全費用や実請求額の比較とは読めない。プランが `partial`、`not-certified`、記述統計を維持する点は正しい。
- 宣言を gate にしない設計は malformed 入力の拒否と矛盾しない。比較 metadata の helper が新しい例外や理由を発生させなくても、負値、型違反、token 関係矛盾は既存経路で `failure_reasons` に入り `valid=false` になる。

## 判断できなかった点と、その理由

- cache write の未計上量が実際に arm 間で系統的に違うかは判断できない。§10 が述べるとおり正規 receipt に数量 field がないためである。完全費用まで比較対象にするなら新しい receipt schema と登録世代が必要で、本 wave の計算層 scope を越えるユーザー裁定候補である。
- 比較可能性を同一 aggregate 内だけに限定する意図か、別成果物間にも適用する意図かは brief とプランから確定できない。前者なら rule に locality を明記すれば所見 2 は解消し、後者なら manifest または登録世代 identity を key に含める必要がある。
- axis の `accounted_amount` は観測済み試行の合計である。現在の二段構造が保証しようとしているのは等しい件数構成の合計であり、試行あたり平均ではない。異なる観測数の unpaired descriptive mean は比較できる場合があるため、同じ key 規則を平均へ流用すると偽陰性になる。一方、paired mean には件数一致ではなく共通 pair identity が必要である。平均を成果物へ追加するかは本 wave の要件から判断できず、追加するなら別の estimand と比較規則が必要である。

## 総括

親 brief の (P1) を「二つの key が完全一致すれば比較可能」という十分条件としては支持できない。二段構造、field 除外、D932 の三分類、非 gate 化は妥当だが、第二段が count だけでは paired identity の入れ替わりを検出できない。

最小限の意味修正は、比較 universe を同一成果物に限定するか identity を key に追加し、axis では `(block_id, attempt)` を status 別に保持して paired membership を一致条件にすることである。四 count は D932 の可視化として残す。規則は「partial な accounted component total の比較」に限定し、平均、完全費用、実請求額まで保証する表現にはしない。