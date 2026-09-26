---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-26
wave: dev-wave-t2847-mocc-run
seq: 2
---

## {{D:t2847-mocc-run}}. 検出期待表の mocc 6 行は pin C に壊し patch を単独で当てて実走し、「発火未確認の S」「停止」「対照正常」を五分類の外の状態として記録する

**決定:**
1. 既存の mocc 壊し patch 4 本 (lockskip-validation・permutation-erase・early-unlock・hot-update-unlock) は、計装 patch を重ねず pin C (`68106660`、mocc の X/P 計装を含む) に単独で当てる。既存 driver `s3_mocc_mutation_proof.py` の PIN 定数・計装 patch の適用・policy は変えず、repo 外の起動器が driver の build・verify 関数を呼ぶ。policy は `_load_policy` のまま読み (mocc_trace.new_oid = 旧 pin で driver と一致)、build だけ C を checkout する。これは既存の pin 候補経路 (`s3_mocc_lock_coverage._candidate_main`) と同じ扱いで、結果に policy の new_oid と build source の OID を両方記録する。
2. 新規 V25 (逆順 lock の正準順への復元を飛ばす) は、upgrade でなく、対象 tuple が保持中の lock に無く、再取得する key が保持中の suffix と重ならないときだけ復元を飛ばす限定 gate で作る。単純に飛ばすと同じ lock の再取得と二重解放が起き、狙った機構 (逆順の lock を持ったまま追加で取る) と別の停止を混ぜる。
3. D2239 の五分類 (期待した層で検出・別の層で検出・盲点として certified・未発生・誤検出) に当てはまらない cell を、次の状態として別に記録する: **発火未確認の S** (発火診断の無い既存 patch の S。未発生に数えない)、**停止** (run timeout。verdict を付けず、同 job の stock 同 cell の完走を対照に「変異 build で停止」と書き、原因は断定しない)、**対照正常** (stock と正しさを保つ対照の正常な S)、**帰属不能** (同 job の stock 同 cell が異常)。1 つの cell で複数の層が発火したときは、期待した層の counter が正なら「期待した層で検出」とし、併発した層は別欄に書く。
4. 停止した run の部分 trace は verify しない。停止時に診断を取り出す signal handler も patch に足さない。

**理由:**
- C の計装は旧計装 patch と同じ位置・理由で X/P を出す (段 3 相談 A)。旧来の経路は C では計装 patch が当たらず走らない。driver・policy を改めると旧 JSON と旧 check の束縛を動かすことになり、依頼の範囲を超える。
- 発火診断の無い S を「未発生」と数えると、変異が起きて捕まらなかった場合を取り違える (D2239 の理由と同じ)。既存 4 本に診断を足すのは依頼の範囲外だった。
- trace は worker の終了時に flush されるので、timeout で止めた run の trace は不完全で、verify しても判定の情報にならない。
- 実測 (2026-09-26): 34 cell = 期待した層で検出 20・盲点として certified 1・未発生 2・発火未確認の S 2・停止 3・対照正常 6、別の層・誤検出・帰属不能は 0 (`output/insights/2026-09-26/t2847-mocc-run/README.md`)。

**却下した選択肢:**
- driver の PIN 定数と計装 patch の適用を pin C 向けに書き換える — 旧 pin の記録 (`s3_mocc_mutation_proof.json`) と 32 check の束縛を動かす。
- 既存 4 本に発火診断だけの overlay patch を足す — patch 4 本・登録・build の追加が要り、依頼の「本題の実装だけ」を超える。
- V25 の停止時に SIGTERM handler で診断を出す — 新しい実行経路を patch に足すうえ、trace は得られず停止の原因も確定しない。
