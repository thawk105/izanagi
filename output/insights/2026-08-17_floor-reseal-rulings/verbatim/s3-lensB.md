指定資料は読めました。read-only 静的検査のみで、pytest は未実行です。判定対象は段 3 のプランであり、現在の HEAD はまだ実装前です。

### 所見 1 — contract 単位 gate の撤去範囲

深刻度: blocker（撤去しないまま land する場合）

file:line: `orchestrator/campaign/s8b_floor_campaign.py:753-762`, `:966-975`, `:906-910`

失敗筋: index 側または issuer 側の gate が残ると、同じ `contract_sha256` で pin だけ進めた二件目が拒否される。片方だけ撤去しても、resolver の `count=2` 拒否から `certified_writer_admission.py:201-224` が全面停止する。

提案する修正: s2-plan の通り二つの contract gate だけを削除する。`_index_protocol_record:748-752` の組単位一意性、`_write_protocol_document_create_only:1192-1228`、発行後の全 index 検査 `:1060-1074` は維持する。

判定: プランは撤去対象を正しく限定している。

### 所見 2 — P1 resolver の exact 件数を明文化すべき

深刻度: minor

file:line: `s2-plan.md:27-30`, `orchestrator/campaign/s8b_floor_campaign.py:892-911`

失敗筋: 「exact があれば返す」だけを実装すると、異常な index や将来の invariant 変更時に複数の HEAD 一致候補から辞書順の先頭を選ぶ余地が残る。現状は組単位 guard `:748-752` が同一組を拒否するため、正規 scan では到達困難であり blocker ではない。

提案する修正: exact 候補は `exact 1 件` の場合だけ返す、とプランとテストに明記する。複数なら fail-closed。新しい発行制約や世代単位制約は追加しない。

### 案 3 の実効性確認

同じ contract で pin を進めた二件目は、計画どおりなら次の経路で通る。

- target contract と HEAD gitlink pin を取得: `s8b_floor_campaign.py:949-965`
- contract 単位の issuer gate を通過
- 16 field を anchor から継承: `:977-996`
- 組から導出した path へ create-only 発行: `:1003-1015`, `:1192-1228`
- HEAD 移動、read-back、全 index を再検査: `:1031-1074`
- 組が異なるため pair guard は通過し、同じ contract でも index に二件入る

残る scan 障害はない。`_CHAIN_RECORD_PATTERNS` は既に `:265-272` にあり、freeze allowlist は `:3817-3891` で chain record として扱い、`clean_scan_digest` は path と hash を `:3911-3925` で取り込む。正例も `test_s8b_protocol_builder.py:1309-1315` にある。

### FROZEN_MANIFEST 非登録

問題なし。

`test_frozen_artifacts.py:41-88` は明示的な 23 key だけを持ち、検査も `:162-184` の manifest key 集合に限定される。23 件と exact key-set の assert `:227-248` は mapping 自体を検査するだけで、`floor-protocols` の directory scan はない。

oracle manifest `s8b_oracle_manifest.py:814-841`, `:990-1027` も active freeze の明示 path を射影するだけで、versioned artifact の inventory 登録を要求しない。active な tools/checker にも該当する逆向き検査は見つからなかった。

なお、未コミットの artifact は `s8b_ratified_freeze.py:347-357`, `:1223-1228` の namespace-dirty gate で拒否される。これは FROZEN_MANIFEST 登録要求ではなく、freeze namespace を commit 済みに限定する既存規律である。artifact を commit した後は非該当 file として `:1161-1165` の resolution 対象外になる。

### 所見 3 — 実発行と consumer 結線

深刻度: minor（backlog）

file:line: `s4-adjudication.md:63-66`, `s1-brief.md:55-57`, `certified_writer_admission.py:201-224`, `test_s8b_protocol_builder.py:998-1027`

失敗筋: 後続 wave で結線を忘れると、固定 path consumer、レポート、台帳に versioned protocol の path、protocol SHA、`contract_sha256`、`ccbench_pin` が反映されず、legacy 値を参照し続ける。

提案する修正: この wave では変更しない。D6 の通り g2 活性化 chain で実発行と六 consumer の結線を行い、現在の path literal sentinel を赤にする。P2 の先送り自体は一次資料と整合する。

### 所見 4 — D444 の記録方法

深刻度: minor（記録上の land 条件）

file:line: `docs/decisions.md:18656-18658`, `docs/decisions.md:7473-7474`, `docs/spool/README.md:3-5,51-63`, `docs/spool/decisions/README.md:5-34`

失敗筋: D444 本文を in-place 編集すると、既存 decision の不変性と fragment + fold 運用に反する。また決定 5 を限定せず D444 全体を上書きすると、pair 一意性、create-only、決定 1-4・6・7まで誤って失われる。

提案する修正: 新しい decision fragment として、D444 の決定 5だけを限定 supersede する。pair 一意性、create-only、chain pattern、16 field 継承、HEAD 移動検査、失敗 artifact 保持、FROZEN_MANIFEST 非登録は明記して維持する。

## 判定

GO。段 3 のプランは裁定と整合し、実装着手可能です。  
blocker はありませんが、P1 の exact 件数を明記してから実装してください。  
現在の HEAD をそのまま land できる、という判定ではありません。  
二つの contract gate が残った場合は即 NO-GO です。

## 総括

案 3 の「pin 前進による新しい組」は、pair guard と create-only を残したまま実現できる。  
resolver は HEAD 一致を優先し、単独 legacy のみ fallback するため、現在の admission は維持される。  
FROZEN_MANIFEST、oracle manifest、launch allowlist に versioned artifact 登録を強制する経路はない。  
実発行と六 consumer の結線は D6 に従う後続 wave の backlog である。