# T-1975 + T-1978 — 段階 Q と D987

## 結論

- launcher と land の tested-main / tested-tip runner blob 等値述語を exact 2 個だけ撤去した。
- 実行 bytes、実行後再読、全 shard binding report、receipt digest は tested main へ束縛したまま。
- forward-main receipt 再利用は、最終 incorporated main の runner blob が tested main から変わった場合だけ拒否する。
- schema v5、waiter/checker production、非 dispatch 経路、既定 shard 数、段階 R は変更していない。

実装 anchor は `71e0f3a4d4873f7bec5cc474db52bf15bdfb5ca3`、current main 取り込み後 tip は
`5168b59849a0b724dd167a50b38aad8c893b2abf`。

## 検査

- launcher file: 24 passed。
- land file: 299 passed / F57 exact node 1 skipped。
- flaky hold contract: 37 passed。
- 所要台帳 / docs consumer: 673 passed / growth hold 3 skipped。
- mutation (merge 後 tip): baseline 323 passed / 1 skipped、10/10 KILLED、SURVIVED / MISMATCH / TIMEOUT / PARSE_ERROR は 0。
- AI provenance: 新規違反 0。既知違反は既知台帳どおりで、本 wave 由来の追加は無い。

mutation probe は全件 `SURVIVED` 期待で観測 node 集合を採り、別 spec / ledger で KILLED 完全集合へ
再登録した。最終 spec SHA-256 は `c617c0a58844b28d6f48fac426cc32986d7d84f51d2523b55bb03c6fe0dda173`。

## F57 hold

`test_exploration_external_root_keeps_wave_clean` は計算ノード file 走と exact node 単独走で、F57 に既載の
authorization 本文と同じ赤を再現した。D873/D1144 に従い F57 / T-1079 へ exact node 1 件だけを登録し、
hold 後は land file 299 passed / 1 skipped、registry digest
`ed7b4d7e4e5eafe836f11397da6b596d2c04d227996a8a217aa5970b6e117be2` を実測した。

## 一次資料

- `verbatim/`: accepted plan/receipt、現 main plan、consult、裁定、author、review、focus。
- `mutation/`: probe spec/ledger、final spec、実装 anchor と merge 後 tip の final ledger。
- `tests/`: green JUnit 3 本。所要台帳は対象3 fileで 24 / 300 / 37 node exact、対象外17,278 key/value不変。

`verbatim/accepted-plan.md` は原文の可視文字を保ったまま行末 ASCII space 50 bytes だけを除去した。
原文は25,296 bytes、SHA-256 `eed95b6d396d5f825a0f537c49c4da93e2b219f4633c7c5b2245b29c311ea2a4`、
正規化後は25,246 bytes、SHA-256 `6effc600d439472833c2831c45a4846410699c18c2a62ef323022bed7e061dac`。
復元は accepted plan receipt の `output_sha256` とrepo外job artifactを照合して原文を再複製する。

## scope 外

- runner identity に Git mode を含めるかは runner blob 限定を越えるため未実装。
- bounded local / 非 dispatch receipt は段階 R の所有で、本 waveから起動していない。
- stale な non-attributable receipt 一般の再設計、schema拡張、既定 shard 数3への変更は行っていない。
