## 所見一覧

### [重大度 must-fix] 実測データが、プランの fingerprint と親の終端 usage 規則をともに破っている

- どこ: `s1-brief.md:42-46,73-75`、`s2-plan.md:80-103,122-130`、`measure-evidence/run-0:908392.nqsv/ledger-1.stderr:1-3`、`agent-a0b83dd5881836518.jsonl:5-7,13-18`、`agent-a608af4fc1adbdd1c.jsonl:4-6,14`、`agent-ab83a32f02e59e6ab.jsonl:4-6,14`、`agent-adeb0502381cc3026.jsonl:4-6,14`
- 何が壊れるか: brief の「4 ファイルは `parentUuid` も同一で `agentId` だけが異なる」は誤り。最初の対象では `agent-a0...` の終端 `parentUuid` が `c9d226...`、他 3 本は `719f7b...` であり、プランの `parentUuid` 集合完全一致では実測対象を拒否する。さらに 3 番目の衝突 `msg_011Cd9iWwXUEMz9erCs7xbA7` は、同一 `message.id`・`requestId`・`sessionId` で、最大 transcript に現れる Agent tool ID が他 transcript の部分 snapshot に対応する一方、終端 `output_tokens` が `10933` と `3` に分かれる。同一応答の異なる streaming／fork snapshot と整合し、親の「終端 usage 不一致なら fatal」でも実測 rc=2 が残る。
- 再現条件: 上記 4 transcript をそのまま入力する。第一群は fingerprint 不一致、第三群は終端 usage 不一致になる。なお stderr には message collision が 1 件ではなく 30 件あり、`stderr:4-30` には root-root 複製もある。
- 塞ぎ方の案: 実装前に同一性証拠を二種類へ分ける。①同じ record UUID／content digest を持つ exact clone、②同一 session 内で content/tool 集合が一意な最大 replica の prefix／subset と証明できる partial snapshot。どちらにも該当しないものだけ fatal とする。終端 usage 一致だけを同一性証拠にしてはならない。

### [重大度 must-fix] `message.id` 単独では別 call の誤統合と同一 call の二重計上を防げない

- どこ: `tools/claude_session_ledger.py:433-508`、`s2-plan.md:85-108`
- 何が壊れるか: `message.id` と `requestId` は「非空文字列」しか検査されない。空文字・型不正は anomaly にならず欠落扱い、空白、非 ASCII、極端に長い値、形式不正はそのまま alias になる。切り詰め処理はない。ローカル正本には `message.id` の全 session・全 call にわたる一意性契約もない。これを dedup の唯一の根拠にすると過小計上できる。
- 再現条件:
  - 別 call A/B に同じ `message.id`、同じ終端 usage、異なる `requestId` を与える。親の終端 usage 規則では 1 call に落ち、各 requestId group は singleton なので `request_id_collision` も発火しない。
  - 同一 call の一方を message ID のみ、他方を request ID のみにする。共有 alias がなく 2 call として通り、過大計上になる。
  - 一方が両 ID、他方が message ID のみなら dedup、他方が request ID のみなら request collision になる。同じ欠落が左右で異なる結果を生む。
- 塞ぎ方の案: cross-file 緩和を利用できる ID を、長さ上限付きの canonical ASCII 形式へ限定する。不正 ID は黙って欠落扱いせず anomaly にする。両 ID がある member 間では request ID 一致も必要条件にし、欠落を許す場合は record UUID／content digest など独立した証拠を必須にする。

### [重大度 must-fix] requestId の条件付き抑止が、本来 fatal な再利用を隠せる

- どこ: `s2-plan.md:95-108`
- 何が壊れるか: fingerprint に request ID 自体が入っていないため、異なる request ID を持つ二つの call が誤って同じ message representative に写像される。その後は各 requestId group が 1 representative となり、`request_id_collision` では救済できない。逆に、同じ message/request ID が別 call で再利用され、usage・時刻・cwd・tool ID まで偶然一致した場合も両 collision が消える。
- 再現条件: 同一 `message.id` と terminal usage、同じ cwd/model/timestamp を持つ二 record に、`req_A` と `req_B`、異なる text content を与える。プランの tool identity は text content を含まず、tool がなければ fingerprint が一致し得る。
- 塞ぎ方の案: message group の検証、request group の検証、representative map の確定を三段階の読み取り専用計算にし、全検証後に一括適用する。request ID 集合、record UUID、全 content block の正規化 digest、`stop_reason` を照合対象にする。request collision 時は representative と全 loser を逆引きして component 全体を invalid にする。

### [重大度 must-fix] representative 選択後では既存 anomaly が消える

- どこ: `tools/claude_session_ledger.py:720-737,754-790,1016-1045`、`s2-plan.md:98-118`
- 何が壊れるか: `usage_final_below_prior_max` は `_add_request()` で初めて検出され、representative pruning より後である。プランの完全 fingerprint は maxima を含むため一定の防壁になるが、親が追加提案した「終端 usage のみ一致」へ緩めると、loser にしかない回帰・tool call・missing cwd・timestamp 不整合が消える。どの file が root／辞書順最小かで anomaly の有無と台帳値が変わる。
- 再現条件: winner は終端 output 428 の 1 record、loser は prior output 500、終端 output 428 とする。終端 usage は一致するため dedup され、winner を選べば `usage_final_below_prior_max` は発火しない。loser にだけ tool call を置けば tool 数も失われる。
- 塞ぎ方の案: dedup 前に member-local anomaly をすべて計算し、一件でもあれば group を benign 化しない。あるいは maxima・tool・selector metadata を group 単位で安全に統合し、統合規則を schema に固定する。`alias_conflict` と既存 `invalid_requests` についても、事前 invalid が一件あれば map を一切作らないテストが必要。

### [重大度 should-fix] root 優先は決定的でも、root／sidechain 台帳の意味を変える

- どこ: `s2-plan.md:99-102`、`tools/claude_session_ledger.py:1036-1045`
- 何が壊れるか: 固定 snapshot に対する root 優先と辞書順は概ね決定的だが、それは call の発生元を証明しない。同じ call が root と sidechain に複製されただけで root 使用量へ倒すため、root／sidechain 内訳が「実行主体」から「配置優先順位」へ変質する。親の terminal-only 規則では cwd・時刻が異なる replica を選ぶことで selector の受理結果まで変わる。
- 再現条件: 同一 call を root と sidechain に置き、sidechain 側だけが `--cwd-under` 内または時間範囲内になる入力。
- 塞ぎ方の案: total は 1 回計上しつつ、replica provenance を別フィールドで保持する。root／sidechain のどちらにも断定できないなら `replicated` bucket を設けるか、root 優先が「発生元」ではなく表示規則であることを schema と docs に明記する。走査前後の size/mtime 安定性も確認し、追記中 transcript は incomplete に倒す。

### [重大度 must-fix] 外側 argv 正規化が未知 option と argparse abbreviation を値として飲み込む

- どこ: `s2-plan.md:5-9,54-59`、`tools/collect_wave_usage.py:38-52`
- 何が壊れるか: 「既知 option の完全一致でなければ値」とすると、以前 parser error だった未知 option を project/root 値として受理する。argparse は現状 abbreviation 有効なので、完全一致一覧と parser の option 集合も一致しない。
- 再現条件:
  - `--project --cwd-uner=/bad --cwd-under=/good` は typo を project 値へ変換して通せる。
  - `--project --cwd-u=/bad --cwd-under=/good` は `--cwd-under` の有効な prefix abbreviation を値として飲む。
  - `--project -` や `--projects-root -` は、名前 `-` の directory 等があれば受理され得る。
  - normalizer が `--` で走査を停止しなければ、delimiter 後の token も書き換える。
- 塞ぎ方の案: 最も安全なのは外側 split 互換を設けず、dash-leading 値は `--project=<slug>` を要求すること。互換が必須なら `allow_abbrev=False`、`--` で停止、全 `--*` と単独 `-` を値から除外し、実 project slug の明示 grammar に一致する token だけを書き換える。既知 option 一覧だけで判定してはならない。

### [重大度 must-fix] rc=3 は「既知の正常停止」と「site 証拠故障」を区別していない

- どこ: `tools/collect_wave_usage.py:187-220`、`orchestrator/campaign/site_policy.py:72-97`、`s2-plan.md:22-49,60-65`、`docs/dev-wave/core.md:107-123`
- 何が壊れるか: hostname／NQSV 証拠不足は `PEGASUS_SUSPECT` へ倒れ、既知 login と同じ `blocked`、rc=3 になる。したがって「規律により正当に走らなかった」と「分類証拠が壊れた」が rc だけでは区別不能。DW-S09 は `--help` 参照しか定めず、rc3 と fresh artifact を検証する呼び手がない。一方、外部 supervisor の一般契約は process 非 0 を fail-closed 停止としている。
- 再現条件: `current_site(require_evidence=True)` が hostname 不明または Pegasus 証拠不足を返す状態。既知 login と同じ rc3になる。
- 塞ぎ方の案: rc3 は証拠の揃った policy block のみに限定し、suspect／classification failure は rc1または別 status/rc とする。DW-S09 に「rc と、今回新規作成された artifact の wave_id/status/site を組で検証する」実装可能な契約を置く。

### [重大度 should-fix] create-only artifact と rc 変更の組合せで今回の失敗が保存されない

- どこ: `tools/collect_wave_usage.py:150-184,213-230`、`s2-plan.md:34-40`
- 何が壊れるか: `os.link` は上書きを防ぐが、既存 artifact がある場合は古い artifact が残り、今回の `FileExistsError` は rc/stderr にしか存在しない。parse error、保存先検証失敗、親 directory 不在も status artifact を作れない。rc1 が `collection.status=error` と publish failure の双方を表すため、古い artifact を誤読すると観測を取り違える。
- 再現条件: 同じ `--out` で二度実行し、二度目を失敗させる。二度目は rc1でも file は一度目の内容のまま。
- 塞ぎ方の案: caller は artifact の存在だけを受理せず、wave_id、attempt ID、作成時刻、今回の create-only 成功を検証する。publish 前失敗は別の監査ログへ必ず残す。`SystemExit(0)` の help 判定も parser 呼出し周辺に限定する。

### [重大度 must-fix] 新規テストが実測を単純化し、恒真に近い gate を残す

- どこ: `s2-plan.md:120-134`、`orchestrator/tests/test_claude_session_ledger.py:409-456,1223-1265`
- 何が壊れるか: 4-sidechain 正例は「同一 parent/message/request/usage」としており、実測の parent graph drift と partial snapshot を除去している。この fixture なら実測を一件も救えない実装でも通る。`test_strict_issue_matrix_covers_every_classification` は手で issue category を注入して exit code を見るため、resolver が実入力で collision を一度も発火させなくても通り得る。
- 再現条件: resolver を「fingerprint 完全一致だけ dedup、その他 fatal」のまま実装し、単純化した 4-file fixture を使う。正例は成立するが実測第一群・第三群は依然 fatal。
- 塞ぎ方の案: raw から最小化した parent drift、partial snapshot、root-root clone fixture を登録する。strict matrix とは別に、parser→resolver→issues→exit code の結線を通す negative test を置く。

既存 `test_raw_ids_do_not_merge_across_file_or_sidechain_provenance` の usage `1/2/3/4` 対 `10/20/30/40` は、親の終端 usage 規則でも fatal、rc2、両 metric 0という期待値を維持できる。ただしプランは node を分割・改名するため、「既存 node がそのまま残る」とは言えない。静的確認のみで、実走結果ではない。

### [重大度 should-fix] 中間 record に関する親の解釈は観測単位を取り違えている

- どこ: `tools/claude_session_ledger.py:720-737,769-777`、第一群の各 `agent-*.jsonl:4-7`
- 何が壊れるか: 「`output_tokens` 出現が 4 個対 6 個」は JSON 内の top-level usage と nested `usage.iterations` の文字列出現数であり、そのまま usage record 数ではない。ledger は top-level `message.usage` を record ごとに 1 回読む。第一群では各 transcript とも usage-bearing assistant record は 3 件で、a0 の prior output は 6、終端は 428、他も maxima 428である。この実例では `usage_final_below_prior_max` は偽陽性にならない。
- 再現条件: `rg output_tokens` の出現数を record 数として数える。
- 塞ぎ方の案: evidence には JSON record 数、top-level usage 値列、nested iteration 値列を分けて保存する。「第一群で偽陽性なし」と「一般に terminal-only dedup が安全」は別命題として扱う。

### [重大度 must-fix] 親の測定は本番 collector の argv と入力集合を測っていない

- どこ: `s1-brief.md:33-48`、`measure-evidence/measure.sh:80-82`、`measure-evidence/measure2.sh:103-105`、`tools/collect_wave_usage.py:94-105`
- 何が壊れるか: 測定は ledger 既定 `--max-files=25`、本番 helper は既定上限 1000 を渡す。入力は 1045 files／1.40 GB なので、測定された約149 MiBを本番経路へ一般化できない。少なくとも同じ母集団を時間等で縮めなければ file cap に達し、collector は `incomplete` になる。
- 再現条件: captured 1045-file population に対し helper の既定 max-files 1000 を使う。
- 塞ぎ方の案: class は `unknown` のまま維持し、「既定 ledger argv の限定観測」と明記する。本番 helper 相当 argv の §7.0 測定がない限り local-ok の根拠にしない。性能測定をこの wave 内で追加実走してはならない。

### [重大度 should-fix] P1 据え置きでは防壁は広がらないが、collector の起動条件も改善しない

- どこ: `tools/pegasus_admission_registry.py:69-117`、`hooks/guard_bash.py:166-218,604-619,1195-1205`、`tools/collect_wave_usage.py:190-211`、`s2-plan.md:144-203`
- 何が壊れるか: class を `unknown` に据え置く限り registry／loader／hook の受理集合拡大は見つからない。`check_docs` の reason/evidence golden 更新も実行許可を増やさない。一方 collector は registry class を参照せず site だけで拒否するため、将来 class を変えても Pegasus login での収集は自動的には有効化されない。
- 再現条件: registry entry を仮に local-ok にしても、`site_policy.refuses_heavy_work(PEGASUS_LOGIN)` が真のまま。
- 塞ぎ方の案: 今回は unknown を維持する。将来の class flip は collector と admission registry の接続設計、hook の正例・負例、§7.0 証拠を含む別裁定にする。

### [重大度 should-fix] DW-S09 の短縮が fail-closed 文言を弱める

- どこ: `docs/dev-wave/core.md:109-112`、`s2-plan.md:44-50`
- 何が壊れるか: 現行の「`DW-O23` の成功結果以外」を「`DW-O23` 失敗時」へ変えると、結果欠落・曖昧・未完了を明示的 failure でないとして通す余地が生じる。rc 説明のために既存の受理境界を狭い表現へ置換している。
- 再現条件: DW-O23 が成功も明示 failure も返さない中断・不完全状態。
- 塞ぎ方の案: 「成功結果以外」の量化を保持する。byte 上限があるなら rc 契約は tool の help または別正本へ置き、既存安全文を削らない。

## プランに無いが必要な変更

最低限、次をプランへ追加しない限り段 4 へ進めない。

- replica resolver を「exact clone」と「一意な最大 partial snapshot」の二つの証明方式に分ける。
- resolver を二相または三相にし、検証完了前に representative map や invalid 状態を部分更新しない。
- ID 形式・長さ・欠落の契約を定義し、cross-file 緩和へ使えない ID は fail-closed にする。
- `population.request_identity` だけでなく schema または dedup algorithm version を更新し、旧台帳との比較不能を明示する。
- rc3 の受理には fresh artifact の検証を必須にし、suspect site と既知 policy block を分離する。
- outer normalizer は削除するか、`allow_abbrev=False` と slug grammar を含む狭い受理器にする。

必要な具体的 nodeid 案:

- `test_real_four_sidechain_replica_with_parent_graph_drift_counts_once`
- `test_partial_sidechain_snapshots_of_one_call_choose_unique_maximal_replica`
- `test_same_message_and_usage_with_different_request_ids_remains_fatal`
- `test_same_message_and_usage_with_different_text_content_remains_fatal`
- `test_replica_loser_usage_regression_is_not_hidden_by_representative`
- `test_request_collision_invalidates_representative_and_all_losers`
- `test_replica_resolution_is_input_order_independent`
- `test_noncanonical_message_id_never_enables_cross_file_dedup`
- `test_message_only_and_request_only_replicas_do_not_double_count`
- `test_cross_root_sidechain_replica_filter_and_attribution_are_order_independent`
- `test_split_project_rejects_unknown_long_option_as_value`
- `test_split_project_rejects_abbreviated_option_as_value`
- `test_split_project_rejects_bare_dash_and_stops_at_double_dash`
- `test_split_leading_dash_projects_root_is_normalized_without_widening_options`
- `test_dw_s09_accepts_rc3_only_with_fresh_policy_blocked_artifact`
- `test_suspect_site_is_collection_error_not_normal_policy_block`

F161 対策として、拒否例だけでなく、canonical な両 IDを持つ exact clone、request ID だけが正当に欠ける単一 file record、既存 `test_output_below_empty_git_directory_is_accepted`、正当な dash-leading project/root の正例を残す必要がある。

## 親 brief への反論 (P1〜P5 のどれに、なぜ)

- P1: `unknown` 据え置きには賛成する。ただし測定は本番 helper の max-files 1000を測っておらず、class 判定の一般化はできない。また registry class と collector の site block が未接続なので、P1だけでは usage 欠落を解消しない。
- P2: 非 canonical evidence として扱う方向は妥当。ただし exact sentinel 文字列検査は、測定の真正性を保証する gate ではない。表現を少し変えた同義の過大主張は検出できないため、class unknown が本体の防壁である。
- P3: 反対。同じ `message.id` と終端 usage 一致だけでは別 call を誤統合でき、実測第三群の同一 call partial snapshotは終端 usage が不一致である。message ID は候補抽出キーであって、同一性証明ではない。
- P4: 状態別 rc の方向は妥当だが、rc3 が login policy block と suspect evidence failure を兼ね、DW-S09 に fresh artifact 検証がない。現状案では「壊れた」を「正当に走らなかった」と誤認できる。
- P5: 内側の機械生成 argv を全て等号形にする変更は安全で、実欠陥も直す。外側 split 正規化は別の受理集合拡大であり、未知 option・abbreviation・単独 `-` を飲むため、そのまま採ってはならない。

## 総括

このプランは現状のまま実装へ進めてはならない。最大の停止理由は、実測第一群がプランの `parentUuid` fingerprint を破り、実測第三群が親の終端 usage 一致規則を破ること、さらに条件付き requestId 抑止が別 call の誤統合を隠せることの三点である。registry／hook／loader は class unknown 据え置きなら受理集合を広げないが、collector argv と ledger dedup には新たな穴がある。Web 検索と pytest 実走は行わず、必読資料・raw transcript・実装・テストの静的検査だけに基づく所見である。