## 判定

NO-GO

プランは自己申告3 field の信頼を減らす方向ではあるが、D156 の SC-02 を充足しないことを認めながら「機械化」と記載し、未知 kind の fail-closed が実 wire に届かず、SC-03c の対称性義務も落としている。さらに、P6 を `NOT_IMPLEMENTED` のまま V-12 を結線する構成は、確定済み [T-942] 裁定の理由と矛盾する。現状のまま実装へ進めてはならない。

## 所見 A1

- 所見 ID: A1
- 重大度: BLOCKER
- 対象: `brief.md:27-31`、`rulings-verbatim.md:14-16`、プラン「単位2」
- 何が問題か: [T-942] は「P6 不在のまま繋ぐと不完全な中間状態を読む」ため V-12 を P6 実装 wave に同梱した。一方、本 brief は P6 を `NOT_IMPLEMENTED` のままにして V-12 を結線する。これは同梱という名前だけを満たし、裁定理由を満たさない。
- **成果物影響**: certified selection は現状不変だが、材料レポートと `source_refs` が `P6Unavailable` の中間状態を正式材料として持ち、evidence-present 経路の受理集合も変わる。
- 直し方の提案: V-12 を真の P6 実装・認定まで保留するか、「部分実装でも結線可」をユーザー裁定へ戻す。現在の裁定から黙って後者を導かない。

## 所見 A2

- 所見 ID: A2
- 重大度: BLOCKER
- 対象: `brief.md:20-23`、`s2-plan.md:43-69,190-205,257`、`contract-v1.md:59-64`
- 何が問題か: SC-02 は4 adapter 各々の `P6Derived` 正例到達を合接要求する。プランは lock/write を一律 `witness-kind-unavailable` にし、cycle/permutation も full `P6Derived` に到達しないと認めている。それでも条項表と親 brief は SC-02 を「機械化」と名乗っている。
- **成果物影響**: candidate admission は変わらず、lock/write は材料レポート・試行台帳上 FC07 へ落ちるだけで、SC-02 による禁止集合や certified 選択は生成されない。
- 直し方の提案: 本単位を「既知 channel の fail-closed hardening」と改称し SC-02 機械化の主張を削るか、4 adapter と full positive calibration を実装可能な別単位へ再編する。

## 所見 A3

- 所見 ID: A3
- 重大度: BLOCKER
- 対象: `s2-plan.md:52-69,200,235`、`orchestrator/verifier/report.py:112-133`
- 何が問題か: 実 wire には witness の `kind` discriminator がない。adapter が既知 counter から内部的に kind を合成するため、C-08 の `kind="future-kind"` は dispatcher 直接呼出しでしか発火しない。現行の `lock_coverage_violations>0` / `write_intent_violations>0` は先に検出され FC07 へ閉じるので具体的回避を塞ぐが、例えば `integrity.future_candidate_violation=1` は dispatcher に渡らず、valid cycle と併存すれば CLASS_SET へ進みうる。
- **成果物影響**: 未知 integrity channel を含む ordered WAL が P6Unavailable 側へ入り、材料・試行台帳に candidate-attributable class として残る受理穴になる。
- 直し方の提案: wire schema に versioned な閉じた discriminator を設けるか、少なくとも `verify.integrity` の exact-key 検査で未知 field を production 経路から ContractError にする。直接 dispatcher の C-08 だけを証拠にしない。

## 所見 A4

- 所見 ID: A4
- 重大度: MAJOR
- 対象: `s2-plan.md:45-59,81-92`、`p6-design.md:171-180`
- 何が問題か: CycleWitness の成立条件である `verdict="non-serializable"` と integrity clean の再計算・照合がプランの validator、calibration、変異表に落ちていない。例えば valid G2 cycle に `orphan_reads=1` を併置した入力を false にする検査が記載されていない。
- **成果物影響**: integrity-dirty な cycle が CLASS_SET となり、FC07 で拒否すべき projection が P6Unavailable として材料・試行台帳へ入る。
- 直し方の提案: integrity の全構成 field から clean を再計算し、申告 `clean` と一致させる。verdict、clean、cycle、切詰めをそれぞれ単独変異で検査する。

## 所見 A5

- 所見 ID: A5
- 重大度: BLOCKER
- 対象: `s2-plan.md:34-50,81-94`、`contract-v1.md:63`、`p6-design.md:197-205`
- 何が問題か: SC-03c は設計 §3.3 全体を参照し、key-renaming/version-shift 対称性を workload ごとに証明できなければ `symmetry-not-established` とする。プランの disposition code と条項対応表にこの義務がない。
- **成果物影響**: 対称性が成立しない workload の witness が同一 class に併合され、constraint SHA、FC07/P6Unavailable 判定、将来の禁止集合参照が変わる。
- 直し方の提案: workload-bound symmetry proof を evaluator 入力に加え、不在・不一致を `NOT_DERIVED(symmetry-not-established)` にする。証明 artifact を作らないなら SC-03c 機械化を名乗らない。

## 所見 A6

- 所見 ID: A6
- 重大度: MAJOR
- 対象: `s2-plan.md:6-7,113-120`、`orchestrator/campaign/reflux_result_evidence.py:629-668`
- 何が問題か: attempt の一意性を caller-selected `byte_start:byte_end` 内の records だけで判定する。source WAL 全体に同じ attempt の区間を2つ置き、projection を後半だけへ向ければ、digest と interval byte 一致を保ったまま前半を検査から隠せる。
- **成果物影響**: 本来 `ambiguous-wal-binding` となる evidence が CLASS_SET/P6Unavailable に入り、formal consumer の受理集合と試行台帳 reason が変わる。
- 直し方の提案: digest-bound source WAL 全体を走査するか、全 attempt frame を漏れなく束縛する非連続 range manifest と完全性検査を設ける。

## 所見 A7

- 所見 ID: A7
- 重大度: BLOCKER
- 対象: `s2-plan.md:71-79,204,291`、`p6-design.md:446,490`、`contract-v1.md:215`
- 何が問題か: sort/permutation witness の同値関係は規範上未決定なのに、プランは observation multiset を authoritative として class 化する案を実装面へ入れている。`unknown` observation の異なる raw reasons を同一 class に畳むことなども、現在の裁定からは正当化できない。
- **成果物影響**: permutation の class SHA と constraint reference が未裁定の規則で固定され、材料レポート・試行台帳・将来の禁止集合が裁定次第で変わる。
- 直し方の提案: プラン自身が挙げた permutation 同値関係を実装前の裁定事項に昇格する。未裁定なら permutation も known-unavailable に留める。

## 所見 A8

- 所見 ID: A8
- 重大度: MAJOR
- 対象: `s2-plan.md:81-94,188-218`
- 何が問題か: 各 rotation を txid/key/version relabel 後の完全な正準 bytes にしてから最小選択する順序が明記されていない。また C-02b〜e は同じ基準 fixture の一軸変異だけなので、`distinct-key数・version差分bit・fixture方向bit・reason総数` のような浅い特徴射影でも全件を通せる。
- **成果物影響**: class SHA が raw ID に依存したり、異なる key partition/version equivalence を併合し、formal consumer の受理 class と参照 digest が変わる。
- 直し方の提案: rotation ごとに8規則を完遂してから辞書式比較する順序を固定する。複数の非同型 witness、任意 rename、複合変異を使う metamorphic family を追加する。

## 所見 A9

- 所見 ID: A9
- 重大度: MAJOR
- 対象: `s2-plan.md:71-79`、`orchestrator/verifier/report.py:72-93`
- 何が問題か: genuine producer については `0..5 → sample=total`、`>5 → sample=5` なので誤判定しない。しかし計画の `permutation_violations > len(sample)` だけでは、`total=4/sample=5` や `total=6/sample=6` が非 truncated になる。後者は現 producer の5件上限にも違反する。
- **成果物影響**: malformed な permutation detail が完全 witness として class 化され、FC07 で拒否すべき evidence の受理と constraint SHA が変わる。
- 直し方の提案: `len(sample) == min(total, 5)`、`len(sample) <= 5`、`sum(counts)==total` を合接し、各 sample と counts の分類対応も検査する。

## 所見 A10

- 所見 ID: A10
- 重大度: MAJOR
- 対象: `brief.md:25`、`s2-plan.md:6-7,14,119`、`orchestrator/campaign/pipeline.py:1485-1491`
- 何が問題か: 親 brief の「verify_done に attempt ID が無い」という実測は現 checkout では偽で、`verify_done.payload.build_attempt_id` が存在する。プランは現状を認識しながら欠落を許可するため、現在 resolver が拒否する projection を新たに受理する。この受理拡大は D96 表にも記載されていない。
- **成果物影響**: attempt ID を削った verify_done が resolver を通り、formal consumer の受理集合と材料・試行台帳 reason が拡大する。
- 直し方の提案: 現 schema では ID 一致を保持し、区間一意性を追加防壁にする。旧データ互換が必要なら schema version と受理集合変更を明示する。

## 所見 A11

- 所見 ID: A11
- 重大度: MAJOR
- 対象: `s2-plan.md:222-257`、`contract-v1.md:118-139`
- 何が問題か: 変異表は必須の「検査者」列を欠く。`SC-01/attempt` の last-wins 置換は ordering と ambiguity を同時に壊し、`SC-03a/reason-type` の allowlist 削除は phenomenon 再導出でも拒否されるため単一理由 kill にならない。さらに C-01/C-02/C-10P を含む WitnessDisposition の反転は P6 の4値 calibration verdict ではなく driver-local な見かけの kill である。
- **成果物影響**: 将来の認定記録が非単一理由または局所的な PASS→FAIL を KILLED と誤記し、certified selection/cap-lift の参照根拠を偽る。
- 直し方の提案: `SC-01/attempt` と reason-type の変異を単一 conjunct に作り直す。SC-02の4 positive conjunct と全 witness-only kill は「accreditation 用 KILLED 不可」と明記し、検査者列を追加する。

## 総括

- BLOCKER: 5件
- MAJOR: 6件

規律2について、今回の変更面は formal consumer、evidence reader、材料 renderer であり、candidate admission や通常 verifier 呼出しを直接変更しない。したがって設計 §3.6 を緩める変更は見当たらず、方向は中立である。ただし admission 結線自体も未実装なので、締めてもいない。

4値型については、`WitnessDisposition` を P6結果そのものと名乗らず、`NOT_IMPLEMENTED` / `NOT_CLAIMED` を状態語として分離しており、混同は認められない。

自己申告3 field の再導出には、class不一致、cycle長不一致、count/sample不一致という false 入力があり、構想自体は恒真ではない。ただし A3・A4・A6の穴を残すと、未知 channel、dirty cycle、切り取られた attempt で検査を迂回できる。

親の実測監査では、自己申告3 field、fixture定数、permutation detailと5件cap、`FROZEN_MANIFEST` 23件かつ layer3/reflux bytes不在、参照された主要 `file:line` は確認できた。T-2191の4ファイルとT-524の2ファイルも各 branch の差分には存在する。ただし現在は63 worktreeが登録され、該当 worktreeは clean なので、「40 worktreeの未commit差分」は当時限りの測定であり現在状態へ一般化できない。permutationについても「構造化 field がある」までは支持できるが、「P6 class に十分な意味契約がある」までは支持できない。

- (P1): 狭い意味では支持。`evaluate_formal_origin()` の live caller があり、FC07/P6Unavailable の受理集合と台帳値は変わる。ただし generalized cut・candidate admission・certified selectionは変わらない。
- (P2): 条件付き支持。深い検査を新 verifier に置く構成は [T-326](b) と整合しうるが、A1の [T-942] 問題は別に残る。
- (P3): 部分支持。現行 lock/write counter を既知 kind として先に拒否する経路は回避を塞ぐ。一方、実 wire の未知 kind、4 adapter positive、permutation同値関係が閉じていないため、閉じた和またはSC-02充足としては不支持。
- (P4): 不支持。現プランだけでも上限寄りであり、必須修正には wire discriminator、symmetry binding、schema/version境界、calibration・変異の再設計が加わる。

裁定パッケージ候補は、(1) P6 `NOT_IMPLEMENTED` 中の V-12 結線を許すか、(2) 本単位を「SC機械化」でなく fail-closed hardening と位置付けるか、それとも4 adapterまでT-941に戻すか、(3) permutation witness の同値関係、(4) attempt ID 欠落を旧schema互換として受理するか、の4件である。帰納段・admission・認定をscope外に置くこと自体は、`NOT_IMPLEMENTED` を維持する限り直ちに偽装ではないが、それらを欠いた成果を「P6またはSC-02を機械化した」と呼ぶことは実装したふりになる。