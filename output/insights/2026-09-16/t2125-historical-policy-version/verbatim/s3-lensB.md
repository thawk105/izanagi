## 致命的な所見

**1. 【real・資料読解】DW-G04 の通過根拠がない。現状の提出資料では設計メモに留めるべき。**

[DW-G04](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2125-historical-policy-version/docs/dev-wave/core.md:75>) は、発火条件を満たす既存 artifact path／計測 ID を要求している。`measured-facts.md:56` の M4 は該当例を提示せず、旧 pin の二件も WAL 不在で別理由の拒否になると明記している。`s2-plan.md:190` の「発行後にテスト内の現行 policy を進める」は回帰テストとして有効だが、既存 artifact の発火証拠にはならない。

実装の明示指示があっても、「DW-G04 を満たした」という判定には変更できない。指示による実装と gate の充足は別の事実である。

**成果物影響:** 現在の図・材料レポートの受理集合を回復する実例が未提示で、将来の効果を現在の研究前進として計上している。

以下、挙動についてはすべて静的読解である。pytest・変異実行は行っていない。ファイルの作成・変更、commit、Git 状態変更も行っていない。

## 重い所見

**2. 【real・読解】「読める」の範囲には、policy 以外の具体的な閉塞が残る。**

中央 admission の改善を、歴史成果物の再生成全体の成功と扱ってはいけない。残る条件は次のとおり。

| 検査 | 実際の比較対象と残る閉塞 |
|---|---|
| lock grammar | `campaign_lock.py:568,593,603` は現行 ordered path 集合と pre-T733 exact-24 だけを受理する。exact-62 は本 wave では通らない。 |
| contract loader blob | `artifact_admission.py:1051` → `contract_loader_binding.py:558,577`。記録 digest と**記録 commit の blob**を比較する。現行 disk bytes との一致要求ではない。ただし記録 commit/blob が取得できなければ停止する。 |
| current closure | `artifact_admission.py:1109` で historical は戻る。`:1118` の現行 closure capture は historical の停止点ではない。 |
| activation | `artifact_admission.py:1168` から current head と記録 prefix を検証する。`env_contract.py:672` は現行の head 定数・登録 catalog、`:643` は generation registry と calibration を検証する。古い serial と現行 serial の**一致**は要求しないが、現在の authority 資料が有効であることには依存する。 |
| COMMIT contract | `artifact_admission.py:1200` → `env_contract.py:881`。記録 H が現行 index で一意に解決でき、chain 上で ever-active、校正資料も検証可能である必要がある。現行 active H との一致要求ではない。 |
| stock／generator／review／authority | `build_admission.py:687,709,718,727,734`。policy SHA だけでなく現行 pin・登録簿・authority literal の照合がある。プランの歴史専用 validator はここを対象にしている。 |
| trigger grammar／predicate | `wal.py:1921` は現行 binding schema、`trigger_gate_binding.py:215` は現行 schema／IR schema と照合する。さらに `:159` → `:78` は記録 predicate SHA を**現行 emitter の生成結果**と比較する。policy を直しても emitter 差で停止し得る。 |
| trigger provenance | `artifact_admission.py:927` は provenance の attempt／commitment と WAL の一致。現行 policy との比較ではない。`wal.py:1993` の commitment 再計算と source 束縛も残る。 |
| その他の内部整合 | `wal.py:1096,1786` の knowledge／backoff grammar、`artifact_admission.py:1413,1422,1430` の source・variant・bytes 再読は残る。これらを「現行 policy 差」と混同して撤去できない。 |

さらに **Layer 3 は中央 admission の後でも通常 decoder を使う**。
[ `layer3_report.py:112` ](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2125-historical-policy-version/orchestrator/campaign/layer3_report.py:112>) の `_read_campaign_lock` は `decode_campaign_lock` を呼ぶ。`build_report` は歴史 admission 後にこれを再度呼ぶ。このため、中央で許された exact-24 の v2 campaign でも report 投影時に通常 grammar で拒否される。policy 差だけを直してこの経路全体が通るとは言えない。

完了範囲は、**対応済み lock／receipt grammar、取得可能な記録 blob、有効な activation／contract 資料、既存の構造検査を満たす campaign に対して、build policy の値差による拒否を除くところまで**である。Layer 3 完成には通常 decoder を含む追加条件がある。ここで scope を広げる推奨はしない。

**成果物影響:** 中央 admission の成功を数えても、旧 grammar や trigger emitter 差を持つ入力の材料レポートは生成されない。

**3. 【real・読解】consumer 表の `plot_s1_9pair.py` は成果物到達を誤記している。**

`s2-plan.md:155` は旧 policy の v2 について「`:593` の decision receipt に識別子が入る」とする。しかし [同 consumer の `:589`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2125-historical-policy-version/tools/plotting/plot_s1_9pair.py:589>) は、receipt を取得する前に次を要求する。

- purpose が `HISTORICAL_RAW`
- epoch が `E0`
- reason が `v1-authority-absent`

有効な v2 authority は `artifact_admission.py:1065` 以降で E1 になるため、今回対象の v2 はここで必ず拒否される。canonical campaign 名・件数等の制約も別にある。既存 v1 入力には今回の policy 分岐は効かない。

**成果物影響:** この図の再生成回復と新識別子の出力を本 wave の成果に数えられない。

**4. 【real・資料読解】M4 の「現 corpus では潜在」は、記載された観測だけでは証明できない。**

`measured-facts.md:58` が外部二十件について示すのは `repo_stock_pin == 511c953` である。一方、拒否条件は `artifact_admission.py:1365` の **preimage 全体の不一致**。同じ pin でも generator／review registry や authority が異なれば発火する。

外部 root は今回の探索許可範囲外なので再検証していない。「発火例を提示できていない」は確定するが、「発火例が存在しない」まで一般化できない。

**成果物影響:** 現在停止している材料レポートの有無・回復件数を、pin 一致だけでゼロと数えてしまう。

## 軽い所見

**5. 【refuted・読解】`wal._replay` の第2比較を直さないと歴史経路が止まる、という疑いは成立しない。ただし caller 表に一行抜けがある。**

`wal.py:2821,2829` → `_replay:2750` → `admission_policy is None:2767` を辿った。production の呼出箇所は以下。

| 呼出箇所 | 渡す値 |
|---|---|
| `backoff_sweep.py:541` | `main` 内の `unexpected_abort` → `:535` で発行した `replay_policy` |
| `s6_sort_sweep.py:432` | `build_context.policy` |
| `s8a_trigger_sweep.py:534` | `build_context.policy` |
| `screening_driver.py:592,649` | 両方 `build_context.policy` |
| `b10_backoff_shape_sweep.py:3562` | `_certification_attempts` の context。上流 `:4415,4499` で発行・伝達 |
| `loop.py:579` | wrapper alias に `build_context.policy` |
| **`loop.py:800`** | **同じ alias に `build_context.policy`。プラン表から抜けている** |
| `paper_story_a1_paired.py:5784` | `collect_workload` の必須引数 `admission_policy` |

`collect_workload` の production 呼出は、許可された木の参照検索と本体読解では **三箇所**だった。`:7197`、`:7446`、`:7653` はそれぞれ `:7058`、`:7333`、`:7623` で発行した context の policy を渡す。

指定された歴史 consumer も、helper 経由を確認した。

- `online_digest:42` → `digest.build_digest:1199` → `load_workload:735` → `_committed_projection:730` → `wal.replay_admitted_records:2690`
- `digest.load_p2_2_digests:1236` → `replay.discover_p2_2_dir:168` → `discover_campaign_dir:129` → 中央 admission
- `p2_2_report:132` → 同 discover → `_collect:71` で view.records を走査
- `layer3_report:733` → 中央 admission → `_read_wal:129`
- `s1_report:429` → epoch helper、`:465` → `read_records_collected`
- `b10_backoff_static_tail_formal:352` → 歴史 admission、formal 側 `:393,404` は certified view → records 投影
- `plot_s1_9pair:562` → 歴史 admission → `_segments(view.records)`

いずれも第2比較を `None` で叩かない。`replay_admitted_records` は `_replay` を呼ばない。

**成果物影響:** 第2比較の据置きによる取り残しは確認されない。`:800` の表への追記だけなら **nit**。

**6. 【refuted・読解】`s1_report.py:302` と `replay.py:179` の「変わらない」は正しい。**

`s1_report` は通常 decoder → 記録 epoch → E0 拒否 → historical epoch gate であり、policy admission を呼ばない。保存済み COMMIT 証拠検査は別途 `:354` にある。

`replay.load_landscape` は [ `replay.py:184` ](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2125-historical-policy-version/orchestrator/campaign/replay.py:184>) で `CERTIFIED_ACCEPTANCE` と `require_certified_commit_evidence` を指定する。旧 policy は変更後も拒否される。

**成果物影響:** 両 consumer の受理集合の回復を、本 wave の効果に加えてはいけない。

**7. 【refuted／一部 real・読解】classification は届く。ただし全診断への配信ではない。**

`artifact_admission.py:314` の `as_receipt` → `layer3_report.py:884` の `admission_decision` に届く。`layer3_schema.json:293` の enum 追加は、その report を schema が落とさないために必要である。epoch に置く必要はない。

一方、`digest.py:1205` の `WorkloadDigest` 構築は decision を投影しない。online digest もこの経路である。成功した歴史閲覧で例外は発生せず、既存の policy 不一致例外にも新 classification は出ない。したがって「Layer 3 と view の decision に出る」は正しいが、「歴史閲覧の全診断に出る」は誤り。図への到達は所見3のとおり。

`CampaignAdmissionDecision.admitted` を読む production 箇所は、中央 `artifact_admission.py:1482` と `backoff_requested_us.py:521` を確認した。後者は `:518` の `classify_campaign`、つまり certified 指定の検査結果を使う。他の `.admitted` 検索ヒットは condition gate 等の別型で、historical decision の迂回消費ではなかった。

**成果物影響:** Layer 3 では版差を識別できるが、critic digest の出力だけからはこの識別子を確認できない。全 consumer への追加配線は今回推奨しない。

**8. 【real・読解】拒否テストの一部は未変更実装でも緑になる。変異 #3 の欠落 key ケースは検出力を過大評価し得る。**

`s2-plan.md:195,196,199,200` のうち、旧 policy 入力に対して単に拒否を確認するケースは、未変更実装でも `artifact_admission.py:1366` が先に拒否する。「形・構造検査が残った」証拠にするには、同じ旧 policy の無破損入力が成功し、破損入力が狙った検査で落ちたことを区別する必要がある。プランは receipt SHA 等の整合には触れているが、すべての構造負例について拒否地点までは固定していない。

変異候補の判定は次のとおり。

- **#1、#2、#5、#6、#7、#8:** dispatch、certified 分離、policy SHA、stock pin、記録 registry、診断という変更の要を狙っている。到達不能とする根拠はない。
- **#3:** exact-key 検査を消しても、欠落 key は後続の field 参照／型検査で拒否され得る。**欠落 key ケースを、この変異を必ず殺す根拠から外すべき**。余分 key ケースが主要な判別例になる。
- **#4:** schema 不一致以外が有効な入力なら有効。
- **#9:** schema 単体の補償検査を狙う変異。certifying builder 全体の検出力とは別に数える必要がある。他の historical marker を除くというプランの条件は必要。

「どんな実装でも必ず赤になる」テストは、記載だけからは確認できない。未変更で緑になる certified 拒否や既存回帰テスト自体は誤りではなく、**新機能の発火証拠には数えない**という区別が必要。

新 test file の作成案ではなく、既存 test file への追加案である。したがって新規 file 登録漏れは **refuted**。実装で新 file に分割するなら、自走 harness・所要台帳への登録と、`docs/dev-wave/operations.md:195` の file 集合メタテストが必要になる。

**成果物影響:** 別理由の拒否を検出成功に数えると、歴史入力の構造検査が欠落した実装を緑として受け入れる。

## 親 brief と実測への指摘

**9. 【real／refuted・読解および読取コマンド確認】M1〜M10 の評価。**

| 対象 | 判定 |
|---|---|
| M1 | **refuted：主要主張への反証なし。** 無条件比較は `artifact_admission.py:1364`。ただし policy を渡す行は `:1370` で、M1 の `:1372` ではない。行番号差は nit。 |
| M2 | **real：網羅性がない。** `build_admission.py:458` の preimage は schema／authority も含む。registry の削除・改名も hash を変える。「pin 前進と member 追加の二事象だけ」は成立しない。プランの訂正は必要。 |
| M3 | **refuted：履歴記載への反証なし。** 読取専用の `git show` で導入 commit の日付と `fb5e74a17` の `d706650 → 511c953` を確認した。ただし当時の v2＋WAL 発火例の証明ではない。 |
| M4 | **real：全 preimage の検査証拠が不足。** 所見4参照。欠損 WAL の拒否期待値は `test_artifact_admission.py:1034` に存在する。テストは未実行。 |
| M5 | **real：「module が別」から編集衝突なしとは言えない。** 別 worktree の未 commit 編集は今回も未確認。exact-62 の追加は `campaign_lock.py` に加えて、`artifact_admission.py:1009,1067` の grammar ごとの binding／epoch 分岐や共通テストと相互作用する。実際の衝突があるとまでは断定しない。 |
| M6 | **real：gate の検査が足りない。** decisions の検索で停止裁定が見つからなくても、`docs/dev-wave/core.md:75` の DW-G04 は残る。またプラン冒頭の「M6 が『純増は policy 層の1箇所だけ』とした」は逐語資料にない。後者は nit。 |
| M7 | **refuted：先例の引用は正しい。** `s8b_binary_admission.py:336` と `b4_binary_record.py:149` を確認。ただし記録 policy を現行 authority として使わず、lock↔receipt の整合に限って使う別型案まで、この sibling の契約が禁止するとは読めない。 |
| M8 | **refuted：内部整合になるという説明は正しい。** `wal.py:2157` → `build_admission.py:687`。lock と receipt の別々の値を比べるため恒真ではない。真正な発行者の認証にはならない。 |
| M9 | **real：列挙が不足。** 親は `paper_story_a1_paired` の helper 経路を落としている。プランは補ったが `loop.py:800` を省略した。None 分岐の到達性に関する結論は所見5の範囲で維持される。 |
| M10 | **real：十分条件への一般化が過大。** status が下流へ届くのは正しい。しかし `admitted` だけで certified 成果物に昇格する実経路を立証してはいない。`layer3_report.py:966` は再び certified admission を実行する。`autonomous_trial_completeness.py:233` も classification と status の両方を要求する。 |

M10 の非認証 status は意味のある出力区別だが、「これがなければ既存の認証境界を突破する」と断定する根拠には不足する。また `EXPECTED_CAMPAIGN_CLASSIFICATIONS` は v1 corpus の表であり、`:1013` は `classify_campaign` の結果を比較する。新 classification の追加だけでこの表が赤くなる、という親の懸念も成立しない。

**成果物影響:** 発火件数、認証への昇格可能性、並行 wave の独立性を過大・過小に評価し、受入対象と研究成果の説明を誤る。

**10. 【refuted・読解】編集面の膨張は、挙げられた範囲では本題に必要な部分を含む。単一 module という brief が誤っている。**

| 編集面 | 判定 |
|---|---|
| `artifact_admission.py` | 必要。purpose 分岐と decision の発行点。 |
| `build_admission.py` | 必要。`:709` の stock pin 等を残すと主比較だけ直しても旧 receipt が落ちる。 |
| `wal.py` | プランの別型方式では必要。`:2124` の exact 型を保ったまま歴史入口と検査本体を共有するため。**`:2767` の第2比較変更は不要**で、プランも除外している。 |
| `layer3_schema.json` | 必要。既存 field の enum が新 classification を拒否する。certified 条件下の旧 enum 維持は、今回増やした受理形だけを相殺する範囲。 |
| 既存テスト | 必要。ただし所見8の検出力の区別が必要。 |

落とせるのは「図まで回復する」という成果説明と、変異 #3 の欠落 key ケースへの過大な期待である。新 status literal、新 field、epoch reason の拡張は不要だが、プランは既に採っていない。

**成果物影響:** 単一 module に押し戻すと旧 stock receipt の拒否が残り、歴史 admission の受理集合を意図した範囲まで回復できない。

## 総括

**現資料では DW-G04 未充足であり、設計メモに留めるべきである。**

技術面では、第2の WAL policy 比較は取り残した歴史経路の停止点ではない。実際に訂正すべきなのは、**図への到達の誤記、Layer 3 の通常 decoder を含む「読める」範囲、M4 の pin 一致からの一般化、負例・変異の検出力の説明**である。

本案が主張できるのは、既存の grammar・authority・構造条件を満たす入力について、歴史 admission の build policy 値差を許すことまで。過去の v2 campaign 全般や列挙された全生成器の復旧ではない。