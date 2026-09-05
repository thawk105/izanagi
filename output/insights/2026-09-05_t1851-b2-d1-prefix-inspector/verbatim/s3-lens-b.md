## blocker

### 所見 1 — current-generation proof が他世代の健全性へ誤って依存する

(a) [実測] plan は current protocol の path を選ぶ前に `_registry_generation_paths_locked()` で freeze 配下の全世代を列挙する。これは別 protocol の 64hex directory が欠損、symlink、非 directory であるだけで、検証対象の current generation が正しくても拒否する。brief の対象は current protocol generation であり、全世代 replay は予算更新側の責務である。

(b) [実測] `s2-plan.md:157-160`、`orchestrator/campaign/s8b_attempt_registry.py:649-724`、同 `:1392-1422`。後者だけが全世代予算 replay の既存用途である。

(c) [推測] 放置すると、自分の `{N, head_at_N}` が不変な v5 certified 成果物でも、無関係な別世代の破損や未完成 directory により後から参照不能になり、受理集合が縮む。

(d) [推測] inspector は `expected_binding.freeze_sha256/protocol_sha256` から exact 2 段 path を直接解決し、その file だけを no-follow で読む。全世代列挙は使わない。別世代の unsafe sibling を置いても current prefix が通る正例を追加する。全世代予算を再検証したいなら別の意味規則なので、B2 へ暗黙に混ぜず再裁定する。

(e) [実測] (P2) の API 配置には賛成するが、replay 対象の具体化は修正必須。(P3) にも波及する。

### 所見 2 — read-only API の root 解決が未指定で、既存 `_entry_paths()` は書込みを行う

(a) [実測] 新 API は `repo_root` を受けるが、plan は `root` の解決方法を固定していない。既存 `_entry_paths()` は `provision_shared_admission_root()` と fsync を必ず実行するため、これを再利用すると read-only inspector ではなくなる。予定された「write lock tripwire」だけではこの書込みを検出できない。

(b) [実測] `s2-plan.md:121-157,366-369`、`orchestrator/campaign/s8b_attempt_registry.py:520-543`、`orchestrator/campaign/s8b_holdout_admission.py:620-637,679-706,730-755`。

(c) [推測] 台帳不在の検証が directory と lock inode を新設し、後続 inspector が見る filesystem 状態と拒否 reason を変える。検証操作自体が台帳環境を変異させる。

(d) [推測] `admission.shared_admission_root(repo_root)` だけで root を解決し、既存 lock/root が無ければ作らず `unverifiable` にする。`provision_shared_admission_root`、`_entry_paths`、`_locked`、fsync helper を tripwire にした test と、「呼出し前後で tree が byte-for-byte 不変」の test を置く。

(e) [実測] (P2) の実装境界に対応する。

### 所見 3 — live proof と artifact の top-level identity が相互束縛されていない

(a) [実測] 現行 pure verifier は artifact の `protocol_sha256`、`freeze_sha256` を外部値と比較していない。plan は reported proof と independently replayed proof の全 7 field 比較を定めるが、proof の freeze/protocol と artifact top-level の同名 field の比較を明記していない。

(b) [実測] `s8b_floor_contract.py:81-87` に両 top-level key がある一方、`s8b_floor_stats.py:682-1033` には両 digest の照合がない。plan は `s2-plan.md:269-288`。

(c) [推測] live registry と proof は正しいまま artifact の `freeze_sha256` または `protocol_sha256` だけを変えた成果物が、pure verifier では空 error を返し得る。レポートの参照先と台帳 proof の参照先が分裂する。

(d) [推測] v5 では `reported.freeze_sha256 == artifact.freeze_sha256`、`reported.protocol_sha256 == artifact.protocol_sha256` を先に要求し、その後 external/live proof と比較する。artifact 側だけを改変する 2 node を追加する。schedule は artifact に同名 field がないため外部 schedule digest との比較だけでよい。

(e) [実測] (P1) の v5 契約に対応する。

### 所見 4 — 「1 wave、実装子 1 本、fix 3 巡以内」は支持できない

(a) [実測] plan 自身の結論は実装子 2 本であり、検査条件の「実装子 1 本」と一致しない。既存 symbol の長さは plan どおり 76、91、24、352、47、10 行だが、314〜502 production changed LOC は未実装コードの見積りであって実測値ではない。必須追加 test を補うと新設は 38 でなく少なくとも 46 nodeになる。

(b) [実測] `s2-plan.md:13-22,52-58,99-103,444-451`。過去実績は `a1-README.md:28-38` と `a2alpha-README.md:171-179`。A2alpha は fix 5 巡、最終 1,768 changed LOC だった。

(c) [推測] 一括実装すると、read-only 書込み、identity 分裂、変異の誤帰属のいずれかが受入全走まで遅れて出て、proof の受理集合を誤ったまま checkpoint 化する危険が高い。

(d) [推測] plan の予備境界をそのまま採用する。第 1 wave は `D1-b + B2-a`、第 2 wave は `D1-a + D1-c + D1-d`。両方とも unlanded checkpoint とし、D1341 の最終 1 commit 条件は維持する。第三案へ分け直す必要はない。

(e) [実測] (P5) は却下、(P6) はこの 2 wave 境界へ修正する。

## must-fix

### 所見 5 — 直接件数は正しいが、回帰 consumer 閉包を 84 node と一般化できない

(a) [実測] `result_keys_for_mode` は plan の訂正どおり 12 call expression、production 3、test 9 で、漏れはない。`RESULT_SCHEMA` も raw search は production 7 file / test 5 file、意味上の S8B 閉包は production 5 / test-support 4 で正しい。一方、plan の「unique 84」は選んだ直接 node の数であり、transitive consumer 全体ではない。

(b) [実測] 直接 call は `s8b_floor_stats.py:734`、`s8b_holdout_freeze.py:1429`、`s8b_ratified_freeze.py:2360`、test は plan `:33-35` の 9 件。live verifier の production caller は `s8b_floor_campaign.py:6684`、`s8b_holdout_freeze.py:1620`、`s8b_ratified_freeze.py:3281`、pure verifier への委譲は `s8b_floor_stats.py:1078`。

[実測] plan が回帰閉包として数えなかった主な fixture family は次の全件である。

- `test_s8b_floor_campaign.py` の `_run_campaign()` call expression 105 件。production verifier 入口は `s8b_floor_campaign.py:7812,7974`。
- `test_s8b_holdout_freeze.py:1772-2851` の `candidate_repository()` 31 件。
- `test_s8b_ratified_verify.py:1182-2752` の `_build_independent_launch_repo()` 9 件。
- `test_s8b_ratified_freeze.py:1200,1443,1488` の G1 emitter 3 件。
- `build_floor_admission_evidence()` の外部 call 8 件。`test_s8b_holdout_freeze.py:167,1732`、`test_s8b_holdout_admission.py:1243,3646`、`s8b_v2_freeze_fixture.py:454`、`test_s8b_ratified_freeze.py:1072,1254`、`test_s8b_ratified_verify.py:609`。

(c) [推測] v4 short-circuit が正しければ成果物値は変わらないが、分岐順や schema default の退行はこの広い閉包を赤にし、candidate・ratified の受理集合まで変える。

(d) [推測] 84 を「選択した直接 focus node」と書き換え、上記 fixture family を回帰閉包として別計上する。変更 file は現在の production 4 / test 4 に保ち、C/D2 file を修正して緑化してはならない。

(e) [実測] (P4)、(P5)、(P6) に対応する。

### 所見 6 — supersede 禁止 pin の列挙が A2alpha S5 と A1' pin を落としている

(a) [実測] 直接赤 0、fixture 経由赤 0、supersede 可 0 という判定自体は正しい。しかし plan の禁止リストは adapter 側 S6 しか具体的に列挙せず、core 側 S5 と v2 retryable 空集合 pin を落としている。

(b) [実測] 保持対象は `test_attempt_registry_core_s8b_profile.py:2206`、同 `:2251-2294`、`test_s8b_attempt_registry.py:3000-3104`。加えて plan 記載済みの `test_s8b_floor_contract.py:180`、`test_s8b_floor_stats.py:596,1321-1325`。

(c) [推測] 誤って supersede すると、単位 C より前に v2 terminal または retryable terminal の受理面を開き、台帳行集合が変わる。

(d) [推測] S5、S6、v2 空集合を nodeid 単位で不変 pin 表へ追加する。D1-b の test 追加時にも既存 assertion を移動・緩和しない。

(e) [実測] (P1)、(P3)、(P6) に対応する。

### 所見 7 — proof validator が `registry_schema` の literal を閉じていない

(a) [実測] plan は proof の `schema` を literal とする一方、`registry_schema` は bounded nonempty string だけとしている。v5 proof の型定義と例示は registry schema を v2 に固定しているため、core validator の契約が一段弱い。wrong-but-well-typed schema literal の直接 test も無い。

(b) [実測] `s2-plan.md:183-208,371-374`。固定される production literal は `s8b_attempt_profile.py:21-22`。

(c) [推測] malformed proof は最終 pure verifierでは拒否されても、D1-b の「検証済み proof」として下層 API から返り得る。下層の保証が上流拒否に隠れる。

(d) [推測] core validator で proof schema と registry schema の双方を exact literal にする。wrong proof schema、wrong registry schema、v5 で `expected_attempt_registry=None`、v4 で expected proof 非 None の直接 node を追加する。

(e) [実測] (P1)、(P6) に対応する。

### 所見 8 — (P3) の結論は正しいが、到達可能な row 列が過小記述されている

(a) [実測] v2 正例は genesis-only に退化しない。`_reserve_v2()` は genesis の後に `start` と `pre-observation-seal` を積むので N=3、`_classify()` で N=4、`begin_attempt_observation()` で N=5 まで現在の production adapter で到達できる。consumption marker は registry row ではなく admission-owned capability/file である。

(b) [実測] `test_s8b_attempt_registry.py:243-313`、`attempt_registry_core.py:1615-1667,1731-1829,1832-1870`、`s8b_attempt_profile.py:405-450,490-503`、`s8b_holdout_admission.py:303-345`。plan の過小記述は `s2-plan.md:411-418`。

(c) [推測] genesis-only しか正例に使わないと chain/tail 変異の観測が弱くなるが、現物経路で N=3〜5 を使えば M-chain 系は実際に KILL 可能である。単位 C/E1 は不要である。

(d) [推測] 正例を N=1、N=3、N=4 の三状態で固定し、valid append は N=3 proof の後に classification を積んで検査する。marker を「行」と数えない。

(e) [実測] (P3) は採用するが、値域記述を訂正する。

### 所見 9 — 変異候補 4 組は現状のままでは帰属が成立しない

(a) [実測] 次の遮蔽がある。

- M1: exact-key 検査を消しても missing field は後続 field validator が拒否する。受理集合を動かすのは extra-key case だけ。
- M7: 長さ検査だけを消しても直後の `rows[N-1]` が `IndexError` になる。拒否は残るため、赤でも実効 KILL ではない。
- M10: expected protocol の 2 段 path を選ぶ設計では canonical 1 段 v1 は path 選択前に脱落し、schema guard に届かない。
- M14: proof の binding を変えるだけでは absent path、path/genesis 検査、core expected-binding が先に拒否し得る。

(b) [実測] `s2-plan.md:424-437`、予定された prefix 順序は同 `:157,175-179`。現物の path/profile gate は `s8b_attempt_registry.py:649-817`、chain access は plan `:176`。

(c) [推測] 放置すると「KILLED」と記録されても、対象 gate を消した受理集合が変わっておらず、台帳 proof の防壁を観測したことにならない。

(d) [推測] 再照準は次のとおり。

- M1 は extra-key nodeだけを KILL 期待にし、missing-key nodeは別 gate の診断とする。
- M7 は short-prefix を実際に受理する複合 mutantへ変えるか、単独変異から外す。
- M10 は expected protocol の exact 2 段 pathへ置いた合成 v1 を使う。
- M12 は live wrapperを通さず pure verifierを直接呼び、reported/live equalityだけを見る。
- M14 は inspector fake が受け取った `expected_binding` から proof を組み、呼出し確認と正常な正例対照を置く。正しい実装は external binding Aを渡して reported Bを拒否し、mutantだけが Bを渡して受理する形にする。

(e) [実測] (P3)、(P6) に対応する。

### 所見 10 — 親 brief の実アンカーと merge 主張は正しいが、件数の一般化は誤り

(a) [実測] 実アンカー表 `s1-brief.md:71-81` の symbol 行番号はすべて現 HEAD と一致する。`50dbf9158` の両親は `fd814b2f0` と `61bc6ac69`、merge-base `1b7822110` から両親が変更した file の積集合は 0 件である。main 側変更と本 wave の production/test 編集面 10 file の積集合も 0 件である。

(b) [実測] merge 主張は `s1-brief.md:3-4`、以前の main 非交差主張は `a2beta-README.md:36-48`。誤りは `s1-brief.md:63-65,83-91`。

(c) [実測] merge 由来で現在の成果物値や受理集合が変質した証拠はない。一方、22 call の一般化は規模判断だけを過大化している。

(d) [実測] 親 brief の P4 は「12 call expression、production 3 / test 9」へ訂正する。DW-O09 は raw word が production 7 / test 5、定義元を含む意味的 S8B production 閉包が 5、test/support が 4 と区別する。「両親 0」「main 非交差」は維持する。

(e) [実測] (P4)、(P5) に対応する。

## nit

### 所見 11 — import graph の説明は結論が正しいが、辺を正確に書くべき

(a) [実測] 実際の top-level graph は `s8b_attempt_registry -> s8b_holdout_admission -> s8b_ratified_freeze -> s8b_floor_stats` であり、admission から stats への直接 import ではない。stats から attempt registry を top-level importすると循環する。plan の局所 import 結論は正しい。

(b) [実測] `s8b_attempt_registry.py:32-35`、`s8b_holdout_admission.py:40-45`、`s8b_ratified_freeze.py:44-48`。admission の直接 import 禁止 meta-test は `test_s8b_attempt_registry.py:1729-1775`。

(c) [推測] top-level importなら module の部分初期化で全 consumer が import failure になる。局所 importなら成果物値・受理集合は変わらない。

(d) [推測] stats wrapper 内で module を局所 importし、test は `s8b_attempt_registry.inspect_attempt_registry_prefix` を monkeypatchして「1 回呼ばれた」ことも assertする。admission には importを追加しない。

(e) [実測] (P2) に対応する。

## 裁定パッケージ候補

- [実測] D2 が candidate を v5-only にした時点では、`s8b_v2_freeze_fixture.py:340-454` と `s8b_floor_evidence_fixture.py:192-351` は v4 resultと admission ledgerしか作らず、attempt registryを作らない。31 candidate call、9 independent ratified callなどがそこで transitive に赤になる。[推測] これは real だが既に D2 所有へ割り当て済みなので、本 waveへ fixture変更を取り込まない。放置したままD2だけ切り替えるとcandidate/ratified受理集合が空になる。
- [実測] `s8b_floor_campaign.py` とその test は main 側で変更されているが、本 wave の編集面とは交差しない。[推測] 単位 C の開始時には改めて基準 hunkを取り直す必要があるが、今回の分割を変える新しいユーザー裁定は不要である。

## 総括

- blocker 4、must-fix 6、nit 1。
- 規模判定: production 素面は収まり得るが、実装子1本・fix 3巡の1 waveには収まらない。2 checkpointへ分割する。
- (P1): producerをv4に保つ判断は採用。v5 proofとartifact headerの相互束縛を追加する。
- (P2): APIをattempt registryへ置く判断は採用。全世代列挙と書込みroot解決は却下する。
- (P3): 到達可能性は採用。実際はN=1、3、4、5まで構成できる。
- (P4): v4 defaultは採用。22 callは12 callへ訂正する。
- (P5): 1 wave判定は却下する。
- (P6): file所有は維持し、`D1-b+B2-a` と `D1-a+c+d` の2 waveへ分ける。