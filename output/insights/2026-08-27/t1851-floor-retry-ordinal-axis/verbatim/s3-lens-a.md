## 正しさ境界の所見

1. **阻止: terminal reason equality の例外が広すぎる。**

   現行 core は、観測後であっても terminal reason と pre-output classification reason の一致を要求する (`orchestrator/campaign/attempt_registry_core.py:1264-1279`)。plan は「観測後かつ S8B の閉集合内」なら不一致を許す (`s2-plan.md:96-97`)。

   具体例は、classification reason が `None`、`observation-start` が存在し、terminal reason が `competing_process` の行である。`competing_process` は閉集合内なので plan の条件では通るが、本来は launcher が post-probe から classification 前に確定する理由である (`orchestrator/campaign/s8b_floor_attempt_launcher.py:590-609`)。同様に `launch_failure` も pre-output classification 側である。throughput から導出できる理由は `nonfinite_or_partial_output` と `performance_anomaly` の二つだけである (`orchestrator/campaign/s8b_floor_stats.py:69-72,126-164`)。

   したがって D1007 の二条件は次の状態になる。

   - `require_previous_terminal`: previous terminal 自体は残るが、`terminal-failure` から secondary reservation で先へ進めるため意味を例外化する。
   - `require_terminal_reason_equals_classification`: 明示的に緩める。D1007 の条件を満たしたとは言えない。

   許すなら、上の throughput 由来二理由だけに限定し、canonical session bytes から `assess_session()` を再実行して一致を証明すべきである。単なる閉集合 membership では正しさ防壁にならない。

2. **阻止: 新理由は caller が作れる。authority として封印されていない。**

   現行 `FloorRetryAuthorization` は公開 dataclass で、`trigger_attempt_id` と `source` の型・集合しか検査しない (`orchestrator/campaign/s8b_holdout_admission.py:217-230`)。runner も exact 型ではなく `isinstance` だけを見る (`orchestrator/campaign/s8b_floor_campaign.py:5883-5887`)。plan はここへ `reason` と `evidence_sha256` を足し、さらに facade が四 field を raw 引数として受けるとしている (`s2-plan.md:106-120`)。

   具体例は、正当な admission identity を知る呼び手が `source="legacy-failed-session"`、`reason="performance_anomaly"`、任意の 64 hex digest を持つ authorization/reservation を構築する状態である。core が受けるのは digest だけで、canonical trigger session bytes 自体ではないため、digest が実 journal row に対応することを独立検査できない。plan の「reason を caller や campaign から自由入力させない」という主張と API 形が一致していない。

   admission 発行の opaque capability、または core が検証できる canonical evidence bytes と run identity が必要である。単なる frozen dataclass と inventory test は authority 境界ではない。

3. **阻止: campaign journal と registry の二台帳間に crash reconciliation がない。**

   現行順序は journal `session-start` の fsync (`orchestrator/campaign/s8b_floor_campaign.py:5929-5941`)、holdout ticket 消費 (`:5695-5709`)、launcher registry reservation (`orchestrator/campaign/s8b_floor_attempt_launcher.py:582-589`) である。

   具体例は retry ordinal 1 の `session-start` fsync 後、ticket または registry start より前に crash する状態である。resume では cut-6 証明が無いので `_replay_cut6_start()` は false を返す (`s8b_floor_campaign.py:6123-6151`)。runner はその start を再実行せず (`:6281-6292`)、ordinal 1 は `_authorized_retry_ordinals()` により消費済みになる (`:5820-5832`)。次に ordinal 2 を作ろうとしても、registry の primary attempt 1 に start/terminal が無いため前駆検査で止まる (`attempt_registry_core.py:1081-1119`)。

   逆順にしても、registry start 後かつ journal start 前の crash で逆向きの孤児ができる。plan には二台帳の prepare/commit 順序、孤児状態表、exact retry/reconciliation がない。`resume_attempt()` が既存 start の reason を読むだけでは、registry start 自体が無い側の状態を処理できない。

4. **阻止: 新 registry gate は最終 artifact 検査では legacy retry に効かない。**

   registry file が存在しないと reader は空 evidence を返す (`orchestrator/campaign/s8b_holdout_admission.py:4217-4223`)。legacy completion が一件あれば `_assert_retry_start_authorized_locked()` は registry の full replay をせず受理する (`:4586-4621`)。最終 inspector も同じ関数を使う (`:5306-5317`)。

   具体例は、launcher を通って legacy retry を完走した後、final inspection 前に registry file が欠落した状態である。journal、consume marker、session completion が残っていれば、現行 legacy branch は registry start の存在も reason/evidence も検査せず通る。

   plan は journal/result schema に第二軸を載せず (`s2-plan.md:154-155`)、ratified verifier も production edit 不要としている (`:158-162`)。このままでは gate は実走時の障害物にはなっても、certified artifact の proof chain にはならない。final inspector と historical verifier が registry を必須 replayするか、検査済み registry chain head を artifact に束縛する層が必要である。

5. **D880 の XOR は intended path では維持できるが、authority 点では保証されない。**

   plan が候補件数検査を残す点 (`s2-plan.md:187-193`) は正しい。通常の admission 経路だけなら新軸は第三の候補種別ではなく、既存二候補の選択結果を registry start へ写す形になる。

   しかし secondary reservation を受ける core/facade は D880 の候補件数を入力に持たない。上記の forged reservation 状態では、legacy/recovery が 0 件または 2 件でも、raw field が closed set を満たせば `terminal-failure` から primary attempt を開ける設計になる。これは XOR の外側にある第三の認可面である。

   さらに現行にも、registry parse が失敗した場合に legacy 一件を返す fallback がある (`s8b_holdout_admission.py:4594-4605,4704-4712`)。具体例は、一意な planned `valid=False` completion と truncated registry file が同時に存在する状態である。候補 recovery の件数を判定不能なのに legacy を受理するため、D880 の「候補 evidence 件数による XOR」を fail-closed には実装していない。

6. **「最後の一行が勝つ」型は registry では閉じている。**

   duplicate start は replay と reservation の双方で拒否され (`attempt_registry_core.py:1073-1076,1552-1557`)、adapter は旧 bytes の strict extension だけを許す (`s8b_attempt_registry.py:1013-1044`)。campaign completion の重複も trigger 選択と final inspection で拒否される (`s8b_holdout_admission.py:4670-4677,5257-5263`)。同じ slot へ別 reason の start を追記して後勝ちにする経路は見つからなかった。

   残る穴は追記上書きではなく、二台帳の片側欠落と、reason/evidence を raw 引数で選べる点である。

7. **恒真化している部分がある。**

   - legacy reason membership: trusted producer が作る `valid=False` session の `excluded_reason` は `_check_reason()` で frozen 四理由に限定される (`s8b_floor_campaign.py:5810-5816,6062-6098`)。protocol 自体も同じ四理由との完全一致を要求する (`s8b_floor_contract.py:523-528`)。したがって production producer から来た legacy candidate に対する「reason が legacy 四理由内」は常に真である。plan の負例 `legacy + node_failure` (`s2-plan.md:207-210`) は producer から構成できず、raw API の偽造または artifact 改変でしか作れない。
   - ordinal membership: runner は `authorized_retries < retry_slots` の間だけ次 ordinal を作る (`s8b_floor_campaign.py:6110-6117`)。同じ値から genesis `{1..retry_slots}` を作るなら、production candidate の membership は常に真である。ordinal 3、`retry_slots_per_cell=2` は runner から構成不能で、改変入力だけである。

   一方、duplicate、prefix 欠損、evidence digest 改変は永続 artifact の負例として構成できるので、gate 全体が恒真というわけではない。テストは「trusted producer の受理集合を実際に落とす負例」と「改変検出だけの負例」を分ける必要がある。

8. **P1 の判定: 親の狭い読みの方が文脈上はやや強い。ただし plan 全体の免罪にはならない。**

   支持証拠は、D880 が旧 `valid=False` 経路を維持し、空集合問題を registry の既知不整合として別裁定へ送っていること (`d1032.md:20-35`)、D1007 が阻害要因を明示的に `S8B_RETRYABLE_FAILURE_REASONS` と二つの transition policy に置いていること (`docs/decisions.md:35273-35283`)、その直後の D1032 が解法として「別の試行番号軸」を選んだこと (`docs/decisions.md:35995-36009`) である。逆に読むと D1032 が統計的測り直し問題を何も解かないため、親の「外部 scheduler 限定は既存 primary retry/recovery 集合に掛かる」という読みが文脈上は優勢である。

   否定証拠は、D1032 の文法が対象集合を限定せず、「受理する理由の集合を広げる場合も外部 scheduler 証拠に限る」と書いていること (`d1032.md:41-49`) である。plan は実際に新しい `legacy-failed-session` 四理由表を genesis に追加する (`s2-plan.md:43-60`)。逐語単体では新軸も対象と読む余地が残る。

   逆読みを採る場合、plan は `legacy-failed-session` を新軸から除き、scheduler receipt で検証された `node_failure` / `scheduler_external_interruption` だけを受理すべきだった。authority 集合が空の現状では production 発火は 0 となり、T-1851 は追加裁定待ちになる。

## 整合・実効性の所見

- **file:line は概ね実在する。** 主な関数名・範囲は存在する。軽微なずれは、`assess_session` 呼出しが plan の `:6017` ではなく実際は `:6018`、`_launch_floor_attempt():582-590` は関数定義位置ではなく、定義 `:548` 内の支配順序部分であること。意味を失う架空 anchor は見つからなかった。

- **terminal reason の data path が plan に欠落している。** `FloorAttemptTerminal` に failure reason がなく (`s8b_floor_attempt_launcher.py:125-141`)、launcher の terminal call も渡さず (`:628-644`)、adapter は core へ `failure_reason=None` を固定している (`s8b_attempt_registry.py:1620-1663`)。具体的に `performance_anomaly` session を registry terminal に残すには、どこが canonical session bytes を検証し、誰が reason を渡すかを新たに決める必要がある。段 5 子は plan だけでは安全に決められない。

- **規模見積もり 1,360-2,075 行は、記載された設計だけなら下限としてありうるが、正しい閉包には不足する。** crash reconciliation、opaque authorization、output-derived reason の独立再導出、final/historical verifier、multi-protocol namespace が見積もり外である。対象 11 ファイルは現時点で合計約 39,250 行あり、campaign と holdout の状態機械変更量を 180-300 行、90-150 行に収める見積もりは楽観的である。

- **安全な分割は一つある。**

  1. 前半を legacy `valid=False` の完全な vertical slice とする。registry v2、opaque reason authority、terminal 再導出、二台帳 crash reconciliation、launcher/campaign 配線、final inspector までを同時に land する。これは production caller を持つため死んだ gate にならない。
  2. `verified-registry-recovery` source、receipt 単回使用、scheduler accounting 拡張は authority 登録と同じ後半へ分ける。現行 authority が空なので、前半が recovery source を fail-closed にしても production 受理集合は変わらない。

  core/profile だけを先に land する分割は production caller 0 件の死んだ gateになり、D1007 の問題も残るため不可である。

## 親 brief の実測値の検算

- **(a) commit 済み 8b floor campaign run artifact 0 件: 結論は支持。** 実際の run path は `output/env/<env>/calibration/s8b-floor-<mode>/<run-id>` (`s8b_floor_campaign.py:7128-7132`)、主要成果物は同 run dir の `journal.jsonl` / `manifest.json` (`:7278-7279`) だが、この形の tracked file は 0 件だった。

  ただし親が補助証拠にした `output/campaigns/*/runs/wal.jsonl` は floor campaign の保存面ではない。そこで `event=session` が 0 件でも、本主張の直接証拠にはならない。正しい path を調べ直した結果、結論だけは維持された。

- **(b) registry artifact は FROZEN_MANIFEST / golden に pin されていない: tracked artifact について支持。** `FROZEN_MANIFEST` の 23 path は `orchestrator/tests/test_frozen_artifacts.py:41-88` に全列挙され、registry path は無い。tracked `floor-attempt-registries/**/registry.jsonl` 自体も 0 件だった。

  「golden にも無い」は、名前・path・schema literal の静的検索としては支持されたが、任意の導出 hash まで不存在と証明したわけではない。そもそも registry artifact が 0 件なので artifact pin 不在は実質的に空集合上の結論である。

- **(c) `performance_anomaly` は性能量由来: 支持。** `assess_session()` は完全・有限・正の throughput 群の CV が閾値を超えた場合に `performance_anomaly` を返す (`s8b_floor_stats.py:126-164`)。campaign は測定後にこれを呼び、`excluded_reason` へ写す (`s8b_floor_campaign.py:6012-6043`)。反例は見つからなかった。

## scope 外だが real な所見 (裁定パッケージ候補)

1. **D444 の理由語彙再利用は人間裁定が要る。**

   `retry_slots_per_cell` を profile に渡して `{1,2}` の同じ cell-wide 上限を作るだけなら、現行 runner の総 retry cap (`s8b_floor_campaign.py:5794-5797,6110-6117`) の読み取りであり、値や意味の変更とは言いにくい。

   一方、`allowed_excluded_reasons` は「session を除外する理由」であり (`s8b_floor_contract.py:523-528`)、plan は同じ四語を「次の remeasurement ordinal を開く authority」に再利用する。具体的に planned `performance_anomaly` が ordinal 1/2 の消費権へ変わる。bytes は不変でも field の権限意味を増やすため、D444 の人間手番に当たる。registry 専用語彙にするか、四語の再利用を明示承認する裁定が必要である。

2. **registry namespace が複数 protocol 世代を収容できない。**

   registry path は freeze SHA だけで決まる (`s8b_attempt_profile.py:378-385`) 一方、genesis binding は protocol SHA を含む (`:43-50`)。launcher は既存 genesis を同じ binding で読み直す (`s8b_floor_attempt_launcher.py:503-529`)。

   repo には同じ freeze SHA を使い、`ccbench_pin` が異なる二つの protocol が既にある (`output/s8b-freeze/floor_protocol.json:1` と `output/s8b-freeze/floor-protocols/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01--511c9538e4e8efa54b45cda62e72389ed3b706ec.json:1`)。一方で campaign を実行して registry を作ると、他方は同じ path で binding mismatch になる。registry を freeze-wide とするか protocol-generation-wide とするかの裁定が必要である。

3. **最終 artifact へ registry chain をどう束縛するかが未決定。**

   plan は result/journal schema を変えない (`s2-plan.md:154-155`) が、現行 historical verifier は registry を入力にしない。具体的に registry を削除した legacy run が final inspection を通れる状態を上で示した。chain head、start event hash、または registry identity をどの成果物へ pin するかは、凍結・historical reverify の受理面を変えるため裁定パッケージへ返すべきである。

## 根拠薄・未確認

- `/v1` registry の migration 不要という主張は tracked repo については支持されるが、repo 外の durable admission root や過去の未追跡実走物までは確認していない。
- 8c 漏れは、secondary policy `None` で分岐し既存 equivalence test を維持する設計なら防げる見込みである。ただし共通 core の実装がまだ無いため、実際に 8c bytes/signature が不変とは確認していない。
- pytest、build、checker、実 campaign は一切実走していない。全て静的検査である。

## 総括

P1 は文脈上、親の狭い読みの方がやや強い。しかし現 plan はその読みを超え、forgeable な secondary reservation と広すぎる terminal reason 例外で、D1007 の二防壁を実質的に迂回する。

特に阻止事項は、terminal reason の無検証例外、reason authority の未封印、journal/registry 間の crash 状態欠落、final verifier が legacy registry を要求しないことの四点である。加えて D444 の理由語彙と複数 protocol 世代の registry identity は人間裁定が必要である。現状の plan をそのまま段 5 へ渡すのは不可で、先にこれらを決めた改訂 plan が必要である。