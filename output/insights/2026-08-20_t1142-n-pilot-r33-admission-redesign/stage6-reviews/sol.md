差分・指定資料を read-only で突合した結果です。実装変更は行っていません。

## Real

1. **[real] [must-fix] 本番 R33 reserve が digest mismatch で必ず拒否される**

`canonical_result_bytes()` は末尾改行を含めてハッシュする一方、admission 側は改行なし canonical bytes をハッシュしています。

根拠: `orchestrator/campaign/s8b_oracle_n_pilot.py:1833`, `:497`、`orchestrator/campaign/s8b_holdout_admission.py:1894`, `:1895`。freeze も driver は raw file hash (`s8b_oracle_n_pilot.py:597`, `:600`)、admission は canonical hash (`s8b_holdout_admission.py:1903`, `:1904`) を比較しています。consume 側も同じ検証を通ります (`s8b_holdout_admission.py:3464`, `:3478`)。

テスト fixture は改行なし hash を使っており (`orchestrator/tests/test_s8b_holdout_admission.py:433`)、本番経路を隠しています。

2. **[real] [must-fix] CLI の外部 manifest が public projection ではなく authoritative receipt を書く**

public manifest の定義は `authoritative_receipt_sha256` と private field を除いた cell projection です (`s8b_holdout_admission.py:2357`, `:2360`, `:2369`)。しかし reserve CLI は receipt 本体をそのまま指定 path に書いています (`s8b_oracle_n_pilot.py:2870`, `:2872`)。

さらに loader は `receipt_sha256` しか認識せず (`s8b_oracle_n_pilot.py:2159`, `:2162`)、public manifest の `authoritative_receipt_sha256` を認識しません。正しい public manifest を consume に渡すと authoritative receipt として解釈できず、`receipts/<hash>.json` 検証に失敗します (`s8b_holdout_admission.py:3437`, `:3442`)。

既存テストも reserve 出力を `{"receipt": "ok"}` と期待しており、誤配線を固定化しています (`orchestrator/tests/test_s8b_oracle_n_pilot.py:487`, `:499`)。

3. **[real] [must-fix] 文書化された aggregate 手順が必ず duplicate manifest で失敗する**

手順は同一 `admission.json` を3回渡しています (`output/insights/2026-08-16_t1142-n-pilot-prereg/r33-qsub-procedure.md:73`, `:74`, `:75`, `:76`)。

しかし aggregate は同一 manifest hash を即時拒否します (`s8b_oracle_n_pilot.py:2189`)。後段でも同一 manifest の再利用を拒否します (`s8b_oracle_n_pilot.py:2322`)。

テストは3個の異なる fixture manifest を作っているため、この実運用矛盾を検出しません (`orchestrator/tests/test_s8b_oracle_n_pilot.py:1627`, `:1668`)。

4. **[real] [must-fix] recovery が既存 ledger の同一 identity 重複を見逃す**

current ledger の duplicate は、異なる row の場合だけ拒否されます (`s8b_holdout_admission.py:2682`, `:2683`)。完全一致する同一 row は dict に上書きされ、重複したまま recovery が続きます。

一方、staged append 内の duplicate は commit validation で拒否されるため (`s8b_holdout_admission.py:2455`)、問題は既存 shared ledger 側です。base prefix と他 role の append 自体は正しく処理されています (`s8b_holdout_admission.py:2673`, `:2707`)。

5. **[real] [must-fix] decision pin checker に decoy/file-binding の抜け穴がある**

source 側は AST ではなく、ファイル全体から `"n_pilot_r33": {...}` を正規表現で探しています (`tools/check_docs.py:1453`, `:1454`)。実際の `_OBSERVATION_ROLES` と無関係な dead dictionary でも通せます。

pending decision 側も固定ファイル名を確認せず、`docs/spool/decisions/*.md` の任意ファイルに slug があれば候補にします (`tools/check_docs.py:1567`, `:1578`)。また最初に一致した section で成功し、exact-one 検証がありません (`tools/check_docs.py:1511`, `:1554`)。

したがって、正規 fragment を別名の decoy に置換する、実際の role entry を変更して dead entry を残す、決定本文だけを書き換えて機械 pin を残す、といった迂回が可能です。

6. **[real] [nit/backlog] R33 判定が role ではなく形状にも依存し、将来の legacy protocol を誤分岐し得る**

`observation_role` がなくても、33 rounds・3 allocations・primary-segment・12 cells・396 rows だけで R33 と判定します (`s8b_holdout_admission.py:1870`, `:1876`)。その結果、reserve は legacy branch ではなく R33 branch に入ります (`s8b_holdout_admission.py:3059`)。

現存の R=11 データには影響しませんが、同じ形状の legacy `n_pilot` protocol を将来許すなら role 分離が崩れます。

7. **[real] [nit/backlog] stable slug/current-tree pin では decision の先行性を証明できない**

decision fragment 自身が、role・decision・checker を同一 commit に揃える濫用と完全な時系列を検査しないことを明記しています (`docs/spool/decisions/2026-08-20-dev-wave-t1142-n-pilot-admission-redesign-1.md:32`, `:34`, `:36`)。

したがって、同一 commit で role と承認文書を新設しても受理できます。これは Unit0 で明示的に受け入れた制約ですが、authority の先行性が要件なら不十分です。

## Refuted

- **[refuted] legacy `n_pilot` / `oracle_driver` の通常経路が R33 に置換された、という所見**

  `_OBSERVATION_ROLES` の membership 判定は従来と同じです (`s8b_holdout_admission.py:104`, `:671`)。legacy reserve は R33 shape でない限り従来 branch に残り (`s8b_holdout_admission.py:3068`)、`n_pilot` key も従来 role のままです (`s8b_holdout_admission.py:3201`, `:3207`)。consume も Mapping receipt でない legacy token は従来 branch に入ります (`s8b_holdout_admission.py:3611`, `:3628`)。R=11 の durable test も通る構造です (`orchestrator/tests/test_s8b_holdout_admission.py:524`）。

- **[refuted] decision fragment の単純な削除・機械 pin 改変を検出できない、という所見**

  canonical section を削除して pending fragment も無ければ checker は違反にします (`tools/check_docs.py:1628`)。`pilot_rounds` 等の機械 pin 改変もテストされています (`orchestrator/tests/test_check_docs.py:5533`, `:5563`)。問題は上記の decoy/file-binding 回避です。

- **[refuted] 他 role の commit marker 後 append を recovery が壊す、という所見**

  base prefix を確認したうえで R33 row だけを抽出し、foreign row を保持して不足 suffix だけ追加します (`s8b_holdout_admission.py:2673`, `:2679`, `:2705`)。foreign append 後の13行化と idempotence もテスト済みです (`orchestrator/tests/test_s8b_holdout_admission.py:665`, `:700`)。empty append は transaction validation で拒否されます (`s8b_holdout_admission.py:2238`)。

- **[refuted] allocation cache が legacy/build-only に波及した、という所見**

  external directory、empty directory、device/inode identity を検証し (`s8b_oracle_n_pilot.py:713`, `:722`, `:733`, `:855`)、R33 allocation の cache hit を拒否します (`s8b_oracle_n_pilot.py:856`, `:956`)。legacy cache hit は保持され、テストもあります (`orchestrator/tests/test_s8b_oracle_n_pilot.py:813`, `:824`)。build-only は `allocation_mode=False` です (`s8b_oracle_n_pilot.py:2971`, `:2974`)。

- **[refuted] holdout unknownness と opaque reference が破られた、という所見**

  `secrets` の import と `cell_ref` / `receipt_ref` の token 化は実装されています (`s8b_holdout_admission.py:23`, `:2877`, `:2884`)。receipt/public manifest は forbidden workload fields を出力せず (`s8b_holdout_admission.py:2392`, `:2397`)、protocol と job argv に forbidden conjunction もありません (`protocol-r33.json:83`, `tools/pegasus/oracle_n_pilot.sh:337`)。

- **[refuted] CLI の既知3反例と副作用順序が未検証、という所見**

  reserve 複数 manifest、consume 複数 manifest、reserve の campaign/manifest 欠落はテスト済みです (`orchestrator/tests/test_s8b_oracle_n_pilot.py:391`, `:400`, `:410`, `:418`)。検証は protocol load/build より前です (`s8b_oracle_n_pilot.py:2929`, `:2931`)。

  新しい反例として、`--mode reserve --consume-only` は `_cli_mode()` で拒否され (`s8b_oracle_n_pilot.py:2741`, `:2745`)、aggregate に `--cache-root` を足す組合せも拒否されます (`s8b_oracle_n_pilot.py:2772`, `:2778`)。

- **[refuted] R=11 実測データを書き換える経路がある、という所見**

  diff の変更対象に既存 measured data はなく、R33 は key role 自体が `n_pilot_r33` と分離されています (`s8b_holdout_admission.py:2051`, `:2057`)。既存 `n_pilot` claim は従来 role のままです (`s8b_holdout_admission.py:3207`)。

- **[refuted] trace-disabled build が崩れた、という所見**

  build call は `trace=False` を渡し、receipt でも false を検査します (`s8b_oracle_n_pilot.py:943`, `:953`)。テストも全 build の false を確認しています (`orchestrator/tests/test_s8b_oracle_n_pilot.py:787`, `:791`)。

## 総括

(a) real 所見: **7件**
(b) must-fix: **5件**
(c) nit/backlog: **2件**
