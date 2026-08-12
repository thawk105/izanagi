## 所見一覧

### [重大度 must-fix] replica の selector 判定が代表 member の cwd／時刻に依存し、wave 帰属を誤る

- どこ: `tools/claude_session_ledger.py:896-905,1213-1229`、`orchestrator/tests/test_claude_session_ledger.py:839-872`
- 何が壊れるか: root member の存在で root 帰属を決める一方、`--cwd-under`／時間窓は支配 representative の `terminal_meta` だけで判定する。member 間の cwd／時刻一致は検証していない。
- **成果物影響:** 選択対象内の call が台帳から欠落するか、対象外の call が root 使用量へ混入し、`model_calls` と全 token 値が変わる。
- 再現条件: root replica を `cwd=/wave`, output=3、sidechain replica を `cwd=/other`, output=100 とし、同一 message/request/model/tool、`--cwd-under=/wave` を与える。sidechain が唯一の支配 member になり、call 全体が欠落する。cwd を逆転すると対象外 root に由来する call が root へ計上される。別の正常 call があれば collector は `complete` にもなり得る。
- 塞ぎ方の案: group 全 member の selector 結果を相 2 で比較し、不一致なら fatal にする。usage の採用元、root/sidechain 帰属、selector metadata を別々に決めず、検証済み group record を相 3 で構築する。cwd と時間窓が異なる正負 fixture を追加する。

### [重大度 must-fix] message-only replica と request-only replica は同じ call でも二重計上される

- どこ: `tools/claude_session_ledger.py:454-519,847-917`、`orchestrator/tests/test_claude_session_ledger.py:472-911`
- 何が壊れるか: cross-file resolver の候補群は共有 raw alias からしか作られない。同じ top-level UUID／内容／usage を持っていても、一方が `message.id` のみ、他方が `requestId` のみなら接続成分が作られず、独立した 2 call として集計される。この s3-lensA の具体例に対応するテストも追加されていない。
- **成果物影響:** 同じ model call の `model_calls`、入力 token、出力 token、tool call が最大 2 倍になる。
- 再現条件: 二つのファイルに同じ record UUID、content、usage、model、cwd、timestamp を置き、A は canonical message ID だけ、B は request ID だけを持たせる。collision も issue も発生せず両方が計上される。
- 塞ぎ方の案: raw alias が片側欠落でも、同一 record UUID と正規化 content digest など独立証拠が完全一致する exact clone を結合する。証明できない replica 疑いは silent 二重計上せず incomplete/fatal に倒す。s3-lensA が指定した `test_message_only_and_request_only_replicas_do_not_double_count` を追加する。

### [重大度 should-fix] 「canonical message ID」が任意の短い ASCII 文字列を許し、等値 dominance で別 call を潰せる

- どこ: `tools/claude_session_ledger.py:440-441,856-898`、`orchestrator/tests/test_claude_session_ledger.py:718-748`
- 何が壊れるか: `_is_canonical_message_id()` は非空・ASCII・256 文字以下しか確認せず、`"x"`、空白、制御文字も canonical になる。異なる UUID／text content の 2 call に同じ短い ID、request ID、usage、model、tool 集合を与えると、等値 candidate の辞書順最小を代表にして 1 call へ潰す。
- **成果物影響:** 2 call 分の token と model call 数が 1 call 分へ過小計上され、受理集合には API 形式でない ID も入る。
- 再現条件: 二つの root ファイルへ `message.id="x"`、`requestId="r"`、同じ usage/model、異なる UUID と text content を置く。
- 塞ぎ方の案: 観測済み API ID grammar を canonical 条件へ含め、さらに record UUID／content lineage など別の同一性証拠を要求する。段 4 の message-ID 一意性公理を維持するなら、外部 transcript がその公理を満たすことを検証できない限界を schema に明記する。

### [重大度 must-fix] 実データの大半を占める root-root replica が受入テストに存在しない

- どこ: `orchestrator/tests/test_claude_session_ledger.py:472-560,839-872`、`measure-evidence/run-0:908392.nqsv/ledger-1.stderr:1-30`
- 何が壊れるか: 正例は sidechain-sidechain 2 種と root-sidechain 1 種だけで、純粋な root-root 正例がない。「sidechain member が一つでもある群だけ解決する」という退行でも、新規正例と既存の incomparable 負例を満たせる。
- **成果物影響:** その退行を受理すると実測 30 群中 27 群が再び fatal となり、該当 model call/token 値が成果物から失われる。
- 再現条件: stderr 1〜2 は sidechain-sidechain の等値群、3 は sidechain-sidechain の一意 dominance 群、4〜30 はすべて 2 root file 間の等値 replica 群である。後者 27 群を模した正例はない。また新 fixture は各 file 1 record で、実入力の 1〜5 record と intra-file dedup の合成も固定していない。
- 塞ぎ方の案: stderr 4〜30 から root file 2 本、同一 request/message/model、複数 streaming record を保った最小 fixture を作り、1 call 計上、root 帰属、両 collision 消失を固定する。

### [重大度 should-fix] canonical 境界テストの一部が新しい canonical gate を通っていない

- どこ: `tools/claude_session_ledger.py:454-459,848-861`、`orchestrator/tests/test_claude_session_ledger.py:718-748`
- 何が壊れるか: 空 ID の parameter は `_request_identity()` で `None` に変換されるため、相 2 の `_is_canonical_message_id()` は絶対に呼ばれない。同じ request ID による `request_id_collision` だけで assertion が成立する。また上限ちょうど 256 文字の正例がなく、`<=` を `<` に狭める退行を検出できない。
- **成果物影響:** canonical validator を弱めても空 ID のテストが反応せず、逆に 256 文字の正当な replica を拒否する受理集合縮小も検出されない。
- 再現条件: `_is_canonical_message_id("")` を真にする変異では空 ID fixture の経路が変わらない。上限判定を `< 256` にしても現テストは 257 文字の負例しか持たない。
- 塞ぎ方の案: validator の純関数境界として 0、1、256、257、非 ASCII を直接固定し、parser→resolver の結線テストではどの issue category が発火したかを `message_id_collision` まで限定する。

### [重大度 should-fix] 実測一次資料が裁定後も誤った単位と admission 結論を残している

- どこ: `measure-evidence/README.md:1,14-18`、`tools/pegasus/admission_registry.json:4-8`、`s4-adjudication.md:122-130`
- 何が壊れるか: raw README は最大値を `20.6 MiB`、margin 込みを約 `149 MiB`、結論を `local-ok 相当` とする。実値は 20,635,648 B = 19.68 MiB、certified 147.68 MiB であり、測定も非 canonical なので registry は正しく `unknown` としている。
- **成果物影響:** 現在の admission class は変わらないが、同じ commit 内の一次参照が相反し、後続の class 判定が誤った値・測定資格を引用できる。
- 再現条件: `842317824 - 821682176` を MiB へ換算し、README 14〜18 行と registry evidence を比較する。
- 塞ぎ方の案: README を +19.7 MiB／147.7 MiB／非 canonical・`unknown` 据置へ同期し、見出しも canonical §7.0 実測と誤読できない名称へ変える。

### [重大度 nit] 「相 1・相 2では state を書かない」は字義どおりには成立しない

- どこ: `tools/claude_session_ledger.py:472,504,510,677-678,688-695,743-745,759-817,927-933`
- 何が壊れるか: final `representatives` と `invalid_requests` の代入は確かに相 3 だけだが、alias conflict は streaming 中に `state["identity_conflicts"]` へ、timestamp／usage anomaly は request 内の `member_anomaly` へ書かれる。相 1 はそれらを「計算」するのではなく読む。
- **成果物影響:** 現コードでは staging 状態が resolver 前に参照されないため値は変わらず nit だが、「検証完了まで invalid 相当 state を書かない」という保証の参照は不正確である。
- 再現条件: alias graph conflict または malformed usage を 1 件与えると、 `_member_local_validation()` に入る前に上記 state が更新される。
- 塞ぎ方の案: phase-local な不変構造へ分離するか、保証を「final representative map と final invalid set は相 3 まで書かない」へ正確に狭める。

## 実装子の自己申告のうち、コードで裏が取れなかったもの

- unit B の「相 1 が alias conflict と timestamp／usage anomaly を計算し、状態を書かない」はそのままでは裏が取れない。これらは streaming 中に staging state へ書かれている。ただし final representative／invalid の適用が相 3だけなのは確認できた。
- 「実測群 1 相当」の fixture は parent/agent drift と usage 値だけを保存し、実入力の複数 streaming record、root-root 27 群、intra-file dedup との合成を保存していない。
- 「過大計上と過小計上の双方を固定した」は、共有 alias がない message-only/request-only replicaと、bogus だが ASCII の等値 ID 再利用を覆っていない。
- unit A の rc 写像はコードで確認できた。`complete=0`、確証済み login block=3、suspect／incomplete／missing／error／未知 status=1、外側 argparse error=2であり、blocked 分岐では collector を呼ばない。publish 前後の例外も 0 にはならない。
- unit C の `class == unknown`、hook golden、runbook 投影は一致しており、admission 受理集合の拡大はない。
- `test_raw_ids_do_not_merge_across_file_or_sidechain_provenance` は fixture 未変更で、incomparable message usage と request 再利用の fatal 経路には引き続き効く。ただし名称どおりの「raw ID は一切 merge しない」保証ではなくなった。
- `test_strict_issue_matrix_covers_every_classification` は `STRICT_ISSUES`／`FATAL_ISSUES` と exit-code 写像を固定するが、issue が parser→resolver から実際に生成されることは検査しない。この限界は元からあり、fixture 自体の弱体化はない。
- `cache_creation` の内訳は top-level `cache_creation_input_tokens` の内訳であり、現成果物が集計する raw input token 合計には既に含まれる。内訳を出力 schema が持たない現状では、これ単独による token 過小計上は確認できなかった。
- pytest は実走していない。ここで述べた評価はコード、テスト、raw transcript の静的検査だけに基づく。

## 総括

現 resolver は、実測 30 件を静的にはすべて解決できる。分類は、stderr 1〜2 が sidechain 等値 replica、3 が一意 dominance の partial snapshot、4〜30 が root-root 等値 replicaであり、全群で canonical ID、同一 request set、同一 terminal model、tool subset、member-local anomaly なしを確認した。したがって「root-root をコードが扱えない」という直接欠陥はない。

ただし land を止めるべき欠陥が三つある。第一に replica 間で selector metadata が異なると wave 使用量が静かに増減する。第二に共有 alias のない exact clone は二重計上される。第三に実測の 27/30 を占める root-root 型が受入テストに存在せず、その処理を壊す実装を受理できる。さらに canonical ID の信頼境界と実測 README の矛盾も閉じるべきである。rc fail-closed、D233/F159 の blocked 非呼出、admission class `unknown` 据置には弱体化を確認しなかった。