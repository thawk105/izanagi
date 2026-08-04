## 設計判断

結論は、親の (P1)・(P3) を採用、(P2) を限定付き採用、(P4) を修正採用とする。編集対象は新規 3 ファイルだけとし、既存 production への結線は行わない。

- 公開名乗りは「P4 用 batch-freeze commitment codec / 単一 session FSM prototype」まで。
- `MAX_APPROVED_GENERATIONS = 1`、cap-lift、origin ledger、proof chain、凍結成果物は不変。
- `reflux_ir.parse_wire()` → `encode_wire()`（`reflux_ir.py:99-114`）で member を正準化し、重複拒否後に辞書順へ並べる。batch を set と裁定した以上、入力順で commitment が変わってはならない。
- commitment は SHA-256 の単なる連結ではなく、domain-separated canonical JSON bytes とする。preimage の完全な key 集合は次とする。

```text
schema_id
member_schema_id
policy.minimum_cardinality
policy.maximum_disclosed_classes
cardinality
members
```

canonical JSON は `sort_keys=True`、`separators=(",", ":")`、ASCII、末尾改行なし。`cardinality` は `len(members)` と再照合する。

- `minimum_cardinality` と `maximum_disclosed_classes` (`Kmax`) は必須の immutable policy 注入とし、既定値を持たせない。
  - `minimum_cardinality > 1` は未裁定の具体値を決めるものではなく、「singleton batch は恒真」という既裁定を排除する構造条件である。実値は 2〜32 の範囲で注入する。
  - `Kmax >= 0`。値はハードコードしない。
  - `Imax/Qmax` は origin 全体の no-refund 予算であり、単一 batch leaf へ per-batch 値として偽装実装しない。
- member result と seal 後の class 公開を分離する。
  - member result は README §4③の閉じた二値 `"accepted" | "rejected"`。
  - seal 時に別引数として、公開対象 class の lowercase SHA-256 reference tuple を渡す。重複なし・件数 `<= Kmax` を検査する。
  - class の意味、referent の実在、公開すべき class の完全性は本 leaf の保証外。ここまで実装しないと Kmax は単なる未使用 field になり恒真化する。
- FSM は `open → frozen → sealed`。sealed の terminal kind は `complete | aborted`。
  - `freeze()` より前の結果投入は禁止。
  - frozen 後の member 追加・再 freeze は禁止。
  - 全 member の結果が揃った場合だけ complete seal。
  - `abort()` は frozen からのみ可能で、部分結果を破棄して aborted seal。
  - 結果は complete seal 後の `disclose()` からだけ返す。abort 後は返さない。
- 全 semantic rejection は `RefluxBatchError("invalid reflux batch operation")` の一型・一文言・`__cause__ is __context__ is None` に畳む。結果値によって例外 fingerprint を変えない。

U-D との結合面は `BatchCommitment.batch_commitment_sha256` 一本にする。

- U-D が batch 第一級の場合: 将来の origin ledger が canonical bytes、digest、cardinality、policy を `batch-committed` 相当 event へ格納し、結果・seal event を同 digest に束縛する。
- U-D が非第一級の場合: ledger 外の trusted control が同じ digest を先に固定し、P3 seam の `batch_commitment_sha256` だけを ledger slot へ渡す。
- どちらでも本 leaf は `origin_id`、event 文法、slot、root、lock、CAS、永続化を持たない。

テスト実測後に名乗れるのは次までである。

> 独立に先行凍結した literal golden と一致する正準 batch commitment codec、および単一 in-memory session 内で freeze 前結果投入・未登録 member・部分 seal・seal 前開示を拒否する FSM prototype。

次は名乗れない。

- D121 P4 充足
- origin 内の batch 一意性、全 query の事前 commit
- abort 後の別 batch 再開禁止
- origin-total の I/Q/K 予算、no-refund
- crash replay、CAS、cross-process 排他
- 同一 process 内の悪意ある introspection に対する秘匿
- class referent の正当性・完全性
- production 到達性、proof-chain 束縛、cap-lift 可

## file:line プラン

新規ファイルなので、行番号は予定 block であり、symbol 境界を正本とする。

### `orchestrator/campaign/reflux_batch.py`

- `new:L1-L23`: module docstring。prototype の射程、production 未結線、origin/P3/P7 非実装、同一 process 秘匿を主張しないことを明記。
- `new:L25-L48`: imports、`__all__`、`SCHEMA_ID`、phase/outcome/terminal token、固定 rejection fingerprint。`reflux_ir.SCHEMA_ID`、`parse_wire`、`encode_wire` だけを利用する。
- `new:L50-L88`: `_reject()`、exact-int、lowercase-64hex、outcome、policy、peer-import 型の validator。下位例外を捕捉した場合は handler を出てから固定例外を送出する。
- `new:L90-L127`: frozen/slots の `BatchPolicy`。`minimum_cardinality` と `maximum_disclosed_classes` に default を置かず、exact int、`1 < minimum_cardinality <= 32`、`Kmax >= 0` を強制。二重 import の peer policy は値を再検証して local copy 化。
- `new:L129-L176`: frozen value types:
  - `BatchCommitment`
  - `BatchTerminalReceipt`
  - `BatchDisclosure`
  
  これらは authority proof ではないことを docstring に明記し、どの mutating API も外部生成 DTO を信用しない。
- `new:L178-L216`: `_canonicalize_members()` と `_commitment_bytes()`。
  - exact tuple だけ受理
  - 各要素を `parse_wire`→`encode_wire`
  - 正準化後の重複拒否
  - injected floor 検査
  - 辞書順 sort
  - exact canonical JSON bytes と SHA-256 の生成
- `new:L218-L257`: `BatchSession.__init__`、`phase`、`commitment`、結果を含めない `__repr__`。内部 policy は再検証済み local frozen copy。open では commitment 取得を拒否。
- `new:L259-L291`: `BatchSession.freeze(members)`。open 限定。成功時だけ一括して frozen へ遷移し、失敗時は open のまま。
- `new:L293-L326`: `record_result(*, batch_commitment_sha256, member, outcome)`。
  - frozen 限定
  - digest exact 一致
  - member が commitment 集合内
  - member ごとに一回だけ
  - outcome は exact `"accepted"` / `"rejected"`
  - 成功返値は常に `None`
- `new:L328-L361`: `seal(*, batch_commitment_sha256, disclosure_class_sha256s)`。
  - class tuple も必須引数で、暗黙の空 tuple default を置かない
  - 全 member 結果の完全一致
  - class reference の正準性・一意性・`len <= Kmax`
  - 成功時だけ sealed/complete。返す receipt に結果を含めない
- `new:L363-L380`: `abort(*, batch_commitment_sha256)`。frozen 限定、理由文字列を受け取らず、部分結果を破棄して sealed/aborted。
- `new:L382-L414`: `terminal_receipt()` と `disclose()`。
  - receipt は sealed のみ
  - disclosure は complete のみ
  - member 順・class 順を正準 sort
  - aborted、open、frozen は固定拒否
- `new:L416-L438`: sink ごとの内部整合再検査。cardinality、member set、policy、commitment digest の drift を `assert` でなく通常分岐で fail-closed にする。

### `orchestrator/tests/reflux_batch_expected_goldens.py`

- `new:L1-L20`: test-only、production import 禁止、runtime 導出禁止、production を緑にするための追随更新禁止を明記。
- `new:L22-L32`: error、phase、outcome、terminal token の literal fingerprint。
- `new:L34-L112`: `EXPECTED_COMMITMENT_CASES`。各 row は
  `(policy, submitted_members, canonical_members, canonical_bytes, sha256)`。
  次の 4 vector を literal 化する。
  - floor=2/K=0 の二 member、逆順入力
  - 同一 member・同一 floor・K だけ変更
  - floor 境界と sort を同時に撃つ三 member
  - 32 wire 全集合
- `new:L114-L150`: complete seal と abort の期待 public transcript。結果投入中の返値、receipt、complete disclosure、abort 後拒否を literal だけで置く。
- import、関数呼出し、comprehension、hash の実行時導出は置かない。

ここで使う 0/1/2/32 は golden の fault-class vector であって、production policy の default や推奨値ではない。

### `orchestrator/tests/test_reflux_batch.py`

- `new:L1-L42`: path、二重 import、golden/production path、plain runner 用 import。
- `new:L44-L124`: golden の closed AST validator。P1 実例 `test_reflux_ir.py:45-101` と同じく、実行前に literal-only を検査して `ast.literal_eval()` する。
- `new:L126-L180`: rejection fingerprint、session transcript、complete/abort fixture helper。
- `new:L182-L246`: public API、frozen policy/value types、no-default、exact-type、dual-import。
- `new:L248-L334`: commitment golden、順序不変、policy/member/cardinality binding、全 32 member。
- `new:L336-L424`: member parser、duplicate、floor、型・Unicode・mutable container の負例。
- `new:L426-L518`: lifecycle 正例、結果順序非依存、complete seal、Kmax 境界、abort。
- `new:L520-L602`: fail-closed transition、wrong digest、unknown/duplicate member、partial seal、over-Kmax、terminal 後 mutation。
- `new:L604-L660`: seal 前 noninterference、fixed repr/error、abort 後非開示。
- `new:L662-L714`: golden 非依存、production から golden import がないこと、二重 import の byte 一致。
- `new:L716-L742`:既存 `test_reflux_ir.py:479-502` と同型の plain runner。

既存ファイルは編集しない。特に `reflux_ir.py`、その golden/test、origin-ledger 設計物、cap-lift consumer は no-touch とする。

## 受理・拒否挙動の列挙

| API | 受理 | 拒否・失敗後状態 |
|---|---|---|
| `BatchPolicy(minimum_cardinality=..., maximum_disclosed_classes=...)` | exact int、`1 < floor <= 32`、`Kmax >= 0` | 引数欠落は Python signature で fail。bool/int subclass、範囲外は固定 `RefluxBatchError` |
| `BatchSession(policy)` | local または peer-import の正規 policy。値を再検証して local copy | forged/incomplete/不正 policy を拒否。session は生成しない |
| `phase` | 常時 `"open" | "frozen" | "sealed"` | 結果数・結果値・class 数は返さない |
| `commitment` | frozen/sealed で immutable commitment を返す | open は固定拒否 |
| `freeze(members)` | open、exact tuple、全 member が正準 wire、重複なし、件数が injected floor 以上 | under-floor、singleton、duplicate、invalid member、再 freeze を拒否。状態不変 |
| `record_result(...)` | frozen、digest 一致、登録済み batch member、未記録、二値 outcome | open/sealed、wrong digest、unknown/duplicate member、invalid outcome を同じ fingerprint で拒否。既存結果不変 |
| `seal(...)` | frozen、digest 一致、全 member の結果あり、class tuple 正準・一意、件数 `<= Kmax` | 部分結果、class 欠落、Kmax 超過、wrong digest を拒否。frozen のままで結果は返さない |
| `abort(...)` | frozen、digest 一致。結果の有無を問わず sealed/aborted | open/sealed/wrong digest を拒否。成功時は部分結果を破棄 |
| `terminal_receipt()` | sealed complete/aborted。digest と terminal kind のみ | open/frozen は拒否 |
| `disclose()` | sealed/complete のみ。正準順の member→outcome と class refs を返す | open/frozen/aborted は拒否。部分結果は一切返さない |

DTO を caller が直接構築しても authority にはならない。session が受け戻すのは文字列 digest/member/outcome だけで、外部 `BatchCommitment` や receipt object を信頼入力として受けない。

## golden 凍結手順

1. 段 4 で、canonical JSON の exact key 集合、schema ID、member sort、policy binding、outcome token、class-reference 文法、terminal token を裁定本文へ逐語固定する。ここが曖昧なまま golden を作らない。

2. golden 担当 G の所有を `reflux_batch_expected_goldens.py` 一点に限定する。入力は brief、D121/D150、上記の規範仕様だけとする。次は読ませない。
   - 未作成の `reflux_batch.py`
   - 未作成の `test_reflux_batch.py`
   - `reflux_ir.py`
   - `test_reflux_ir.py`
   - 既存 IR golden
   - campaign/freeze 成果物

3. G は各 vector について、key 順・member 順を規範仕様から手で展開し、exact canonical bytes を literal 化する。SHA-256 は production 実装ではなく、一回限りの独立計算で導出し、別の標準計算経路でも一致を照合する。golden には bytes と digest の双方を置くため、hash だけの転記誤りも検出できる。

4. golden 自体を closed AST で静的検査し、`python3 -m py_compile` まで実施する。その後、親がファイル全体の SHA-256 を wave job artifact に記録する。この時点では production leaf は存在してはならない。

5. 実装担当 E の所有は `reflux_batch.py` と `test_reflux_batch.py`。E には golden の symbol 名・row schema だけを渡し、golden bytes・digest・ファイル本文を読ませない。E は同じ規範仕様から独立に codec/FSM を実装する。

6. 実装・fix の各段階で、親が golden ファイルの SHA-256 が手順 4 の値と同一であることを先に確認する。不一致なら期待値を実装へ追随させず、golden 以降を invalidate する。

7. テストで数える独立系譜は「実装前に凍結した literal golden」一系譜である。4 case や 32 member を 4/32 本の独立 oracle と水増ししない。現行 batch 実装はないため、P1 のような旧実装との差分系譜は存在しない。

## テスト設計

主なテストは次のとおり。

| 区分 | テスト |
|---|---|
| 正例 | injected floor と同数の batch、全32 member、入力順を変えた同一 set、全結果を逆順投入、Kmax ちょうど、Kmax=0/空 class、complete disclosure、partial-result abort |
| 負例 | singleton、floor-1、33 floor、duplicate padding、invalid wire、list/generator、wrong digest、unknown member、二重 result、invalid outcome/class、partial seal、Kmax+1 |
| fail-closed 境界 | open で result、frozen 前 disclosure、seal 失敗後の状態不変、sealed 後 mutation、abort 後 disclosure、policy/dataclass forge、下位 parser 例外 context の除去 |
| API 誤用 | bool/int/str subclass、uppercase/短い digest、missing keyword、二重 import の policy/session、外部生成 DTO を proof と誤用 |
| 非公開 | 異なる outcome 配列を持つ二 session の seal 前 public transcript が byte 同一。`record_result` の返値、phase、commitment、repr、premature disclose の例外 fingerprint を比較 |
| positive control | 上記二 session を complete seal 後に disclose すると結果が異なることも検査し、「常に同じ固定値を返す偽実装」を落とす |
| golden purity | literal-only AST、production import/call 不在、production が golden を import していないこと、literal bytes の SHA と literal digest の一致 |
| dual import | `campaign.reflux_batch` と `orchestrator.campaign.reflux_batch` が同一入力から同一 commitment/disclosure bytes を作る |

恒真化しない根拠は以下である。

- reject-all 実装は、floor ちょうど、Kmax ちょうど、complete seal の正例で落ちる。
- accept-all 実装は、under-floor、duplicate、partial seal、preseal disclosure で落ちる。
- hash の自己比較ではなく、実装前に凍結した exact bytes/digest と比較する。
- 順序不変だけでなく、member・floor・Kmax のいずれか一つを変えた場合に commitment が変わる負の metamorphic control を置く。
- seal 前の「同じ」と seal 後の「異なる」を同じ二 session で検査するため、結果を常に捨てる実装も通らない。
- mutation の第一失敗 assert を事前登録し、正常入力点数ではなく fault class 単位で検出力を数える。

本回答では pytest を実行しておらず、上記は静的設計である。

## 変異事前登録候補

| # | operator | 対象予定位置 | 期待 KILL |
|---:|---|---|---|
| M01 | policy の `floor <= 1` を `< 1` へ変更 | `reflux_batch.py:new:L98-L110` | singleton floor が受理され、`test_policy_requires_nontrivial_explicit_floor` が最初に落ちる |
| M02 | duplicate 検査を削除し raw length だけで floor 判定 | `new:L188-L199` | 同じ wire の水増し batch が通り、`test_duplicate_members_cannot_satisfy_floor` が落ちる |
| M03 | canonical member の `sorted(...)` を入力順保持へ変更 | `new:L198-L205` | 逆順の同一 set で golden digest が変わり、order-invariance 検査が落ちる |
| M04 | commitment preimage から `maximum_disclosed_classes` を削除 | `new:L202-L216` | member/floor 同一・Kだけ違う golden が同 digest になり、policy-binding 検査が落ちる |
| M05 | preimage から `cardinality` または `minimum_cardinality` を削除 | `new:L202-L216` | literal golden byte 比較、floor-binding metamorphic control が落ちる |
| M06 | `record_result` の digest 一致検査を削除 | `new:L300-L307` | 他 batch digest の結果が受理され、`test_result_requires_exact_batch_commitment` が落ちる |
| M07 | member 集合所属検査を削除 | `new:L307-L314` | 正準だが未登録の wire が受理され、unknown-member 負例が落ちる |
| M08 | duplicate result を上書き可能にする | `new:L313-L320` | 二回目が拒否されず、duplicate-result 検査と postseal original-value control が落ちる |
| M09 | complete 条件を `result_keys == member_set` から subset/非空へ弱化 | `new:L337-L344` | 部分 batch が seal され、`test_partial_batch_cannot_seal` が落ちる |
| M10 | Kmax 比較 `len(classes) > Kmax` を `>=` に変更 | `new:L344-L351` | Kmax ちょうどの正例が拒否され、boundary positive が落ちる |
| M11 | Kmax 検査を削除 | `new:L344-L351` | Kmax+1 が seal され、over-budget 負例が落ちる |
| M12 | `disclose()` の complete-sealed guard を frozen/aborted にも許可 | `new:L397-L414` | seal 前または abort 後に結果が取得でき、noninterference/abort 検査が落ちる |
| M13 | outcome validator を「任意の str」へ緩和 | `new:L72-L80` | `"timeout"` 等が結果として受理され、closed-binary-alphabet 検査が落ちる |
| M14 | parser 例外 handler 内から固定例外を送出して `__context__` を残す | `new:L50-L88` | rejection fingerprint の `__context__ is None` が落ちる |

## brief への反論 (あれば)

1. 「U-D は裁定待ち」は現在の canonical state と一致しない。[docs/worklog.md:1333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/worklog.md:1333) は U-A〜U-G を全件裁定済み、U-D を「batch 第一級」と記録している。指定された archive (165) は裁定前の履歴である。  
   ただし、leaf を ledger 文法から独立させる設計は採用済み U-D と矛盾せず、将来の裁定変更にも耐えるため維持する。

2. 親 (P4) の「結果」は型が未定義であり、そのままでは受理/拒否集合も Kmax の計数対象も実装不能である。本案は `"accepted" | "rejected"` と、別の class SHA reference tuple に分離した。段 4 がこの閉じた schema を採用しない場合、実装へ進んではならない。

3. member を wire string の set に限定すると最大 cardinality は32であり、反復測定・同一候補の複数 query・`Q >= 1 + 32R + E_min` の query ledger を表せない。本 leaf の batch は「distinct candidate set」であり、「origin の全 query slot」とは名乗れない。後者が要求なら member identity に replicate/query ordinal を加える別裁定が必要である。

4. explicit abort 後に caller が新しい `BatchSession` を作ること、本質的に同一 commitment の session を複数作ることは leaf 単体では防げない。したがって adaptive oracle を end-to-end で閉じるには、origin 層の batch 一意性・no-refund・terminal binding が必須であり、prototype を P4 充足として数えてはならない。

5. Python の public API が seal 前に結果を返さなくても、同一 process の caller は private field や memory を観測できる。保証は協調 caller に対する API-level non-disclosure までであり、recipient projection や process isolation の代替にはならない。

## 総括

新規 3 ファイルだけで、正準 member set・cardinality・injected floor/Kmax を束縛する commitment codecと、`open→frozen→sealed` の単一 session FSMを作る。golden は leaf 実装前に literal bytes/digest と public transcriptを独立凍結し、実装担当には読ませない。

この wave で得られるのは P4 用 prototype であり、P4 充足ではない。特に origin 内の batch 一意性、全 query の事前 commit、永続化、no-refund、production/consumer 結線は後続層に残る。