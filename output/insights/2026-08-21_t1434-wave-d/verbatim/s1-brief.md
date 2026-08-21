# [T-1434](4) Wave D — codex_reasoning_ab.py 所有面の完成 (段1 brief 確定版)

## scope

`tools/codex_reasoning_ab.py` の Wave D 所有面 (`_validate_schedule`/`_load_adjudication`/
`_aggregate_verified`/`_validate_supervisor_ledger`/`make_packets`、D603 が定めた所有区分) のうち、
command 引数が指定する4面だけを対象とする。

1. `_validate_schedule` (5085-5156) の schema を task/cache_condition/price_version/
   requested_model へ拡張する。
2. task-specific oracle/adjudication の一般化。ただし `_load_adjudication` (5159-5375) は全文実読の
   結果 **task 非依存であることを確認済み** (packet/verdict/mapping の bijection・freeze・hash
   整合性だけを見る。POS/NEG/case/arm への参照は一切ない) — 変更不要。焦点は
   `_aggregate_verified` (5515-5697) のPOS/NEGハードコード意味論の一般化。
3. `aggregate`/`verify`/`replay` の task・stage・model・cache 軸拡張
   (`_aggregate_verified` の `resources` 辞書、`_replay_manifest` の `identities` 辞書)。
4. `make_packets` (6298-6390) の動的 task count 化と public/private binding の維持。

D614 が許す Wave C→D 境界の越境は `_replay_manifest` 内 `collect_run` 呼出し1行
(`expected_requested_model=slot.get("requested_model", MODEL)`, 6145行) だけであり、これは
Wave C 側で既に land 済み。それ以外の Wave C 所有面 (`supervise_pair`/`_supervise_one`/
`_verify_launch_receipt`/`collect_run`/launch dict構築/CLI `--expected-model` dest) は無改修。

## 確定済みユーザー裁定・設計判断

- **T-1146 ルーリング** (2026-08-16、ユーザー、AskUserQuestion経由、一次資料
  `dev-wave-jobs/rulings-inbox/2026-08-16-t1146-model-routing-luna-ruling.md` 全文読了):
  択(a) — T-189 (model-routing比較実験) を正式起票し、paired・blind・held-out複数task・独立oracle・
  block randomization・cache分離・価格version・事前登録済み非劣性marginを備えた実験を設計・実行
  してから判断する。択(b) 証拠なしmodel-only swap・択(c) 現状維持は不採用。本裁定はT-189着手の
  指示ではなく「次の新しい/dev-waveが改めてbriefから起票する」ことを明記 — 本waveがその起票。
  T-1146自体は台帳側でまだ「要裁定」表記 (canonical decisions.mdへの正式反映は未実施、下記
  「scope外注記」参照、本waveのscopeではない)。
- **D423** (decisions.md:17588、全文読了): 段2/5のmodel routing拡張 (sol→luna) を「下流検査で
  安全」論法だけでは採用しない。射程は「証拠なしでmodelを変えてよいか」への回答のみ — 妥当な
  比較実験 (T-189) がpaired・blind・事前登録済み非劣性margin付きの証拠を出せば再訪可能。
- **D514** (decisions.md:21397、全文読了、2026-08-18): dev-wave自身のcodex modelは全段
  `gpt-5.6-luna@max`へ、**ユーザーが明示的に運用選好 (費用) として指示済み** (「品質同等性の
  証拠ではない」と自ら明記、D423が留保した「supersedeはユーザー裁定にだけ属する」権限の行使)。
  **これはT-189が要求する証拠とは別物であり、本waveは変更しない・変更を正当化する根拠にもしない**
  (command引数の「現在のdev-wave model変更は行わない」と整合)。
- **D603** (decisions.md:24241、全文読了): Wave A→B→C→D 4分割のうちA+Bのみ先行実装・land済み
  (branch worktree-lively-juggling-ripple、292 passed・変異9/9 KILLED、commit
  12712fd7→d8fbdb9d→031e0018→merge91288053→fold3ae42a1c)。却下した選択肢に
  「Wave Dの`_validate_schedule`本体だけを先に配線する」があり、理由は「Wave Cのpair検証拡張
  (stage/task_type/oracle_kind/oracle_sha256/price_snapshot_sha256) が前提」——
  **実際に land したWave Cはこの拡張を`supervise_pair`へ実装しなかった** (Wave C handoffのP2:
  「実在するschedule fixtureが無い」ため見送り、`_supervise_one`/`collect_run`配線のみに限定)。
  よって`_validate_schedule`側のschema拡張は`supervise_pair`側runtime検査の対称拡張を伴わない
  非対称が残るが、これはWave Cで既に裁定済みの意図的な状態であり、D614境界により本waveでは
  是正しない (schedule.json自体のschema検査はWave D所有の`_validate_schedule`が単独で行える)。
- **D604** (decisions.md:24271): task一般化フィールド名は`benchmark_task_id`。
- **D614** (decisions.md:24628、全文読了、2026-08-21): 上記のとおり。
- **D95** (decisions.md:4235、全文読了): 実装面のある wave は軽量版でも段5 Codex `role=author`
  実装子を必須とする。親は直接実装しない。

## 正本 — `docs/phase3-t189-model-routing-preregistration.md` (全707行、全文読了)

- **§5.2 変更点表** (155-180行、17行): 本wave対象4面は次の4行に対応する
  (旧行番号は着手当時のもの、現在の行番号は上記アンカー表参照)。
  - 「`_validate_schedule`の固定されたPOS/NEG×max/high検査を、task、cache condition、
    `requested_model`、`price_version`のpaired schemaへ拡張する」
  - 「adjudication層をtask-specific oracle (§5.3) に対応させる」
  - 「`aggregate`/`verify`・manifest replayをtask、stage、requested model、cache conditionごとに
    集計できるようにする。10 slot、max/highのhard-codeを残さない」
  - 「`make_packets`の10 slot固定を廃止し、task数をmanifestから取得する。**public packetに
    model、stage、task_id、price versionを出さない**」— 盲検性の根幹、実装時の必須制約。
- **§5.3 装置以外に必要な仕組み** (182-213行): 以下6項目は明示的に「実装は本wave scope外」。
  本waveの完成後もこれらは未着手のまま:
  stage2/5 downstream replayer契約 (§5.3: 未登録ならfix gateが`inconclusive`確定)、
  task-specific oracle manifest実データ (POS/NEG以外)、task catalog・task type層別器、
  task毎snapshot/prompt/oracle hashの実固定、独立oracle ledgerの作成・凍結、
  cache context cold/warm管理・記録、price snapshotの保存、実験実施者から隔離されたmapping
  custodian。served model attest経路も存在しない (F56)。
- **§7 blind gate blocker** (347-358行): 現行装置の custodian隔離 (`make_packets`) は
  同一プロセス・同一Unix identityが読める `same-owner-advisory` に過ぎない (実装済みコードの
  自己申告 `"mask_strength": "same-owner-advisory"` と一致、6366/6377/6385行、かつ
  `_load_adjudication`5187-5188行がこの値を検査要件として**pin**している——独立custodian化は
  make_packets単体でなく adjudication層も連動改修が要る規模だと判明)。**独立Unix
  user/担当者・UID・handoff・ACLを事前登録できない限り`routing_evidence_status`は確定せず、
  same-ownerの結果は`apparatus_diagnostic`に限定** (§12.1: 装置動作確認・効果量粗見積りにのみ
  使用、品質証拠・rollback材料にしない) — **これが command 引数の
  `apparatus_diagnostic` という語の一次資料上の出所**。
- **§9 cache gate blocker** (398-427行): provider側cache制御・attestation手段が現行装置に無い
  (実装済みコード確認: `_codex_exec_argv`にcache制御引数なし)。**cache gate不成立はresource-overall
  にのみ影響し、quality-overallには影響しない** (§12.3) — cache不成立は全体を自動的に
  `inconclusive`にはしない。
- **§10 price version**: 実price snapshot (公式原表・SKU・取得コマンド・hash・version) の凍結が
  必須。欠落時はschedule自体をfail-closedで無効化する。実データ取得は本wave scope外だが、
  schema上「明示的に欠測でありうるfield」として扱う設計 (Wave Aが`validate_nullable_dimensions`で
  既に実装、null以外を明示的に拒否するfail-closed)。
- **§11 非劣性margin / §12 判定表**: `routing_evidence_status`は
  `confirmatory-go`/`confirmatory-no-go`/`inconclusive`の3値のみが routing判断・D423証拠・
  rollback材料として引用可能。標本数不足 (`N_positive_min`/`N_negative_min`、power simulation
  未実施)・custodian未実現・cache未制御・provenance無効のいずれか1つでも欠ければ
  `inconclusive`固定 (§12.1)。ITT (§4.1: 技術失敗はpost-treatmentと区別し予定通り分母に残す)
  自体は解析規約でありWave D所有範囲内だが、これを実質化するreplayer契約 (§5.3) が無ければ
  fix gateは`inconclusive`確定 (§12.3)。task catalog・独立分類者2名・power simulationはすべて
  scope外 (§6.1/§6.2/§11.4)。

## (P1) 6条件の成立可否判定 — 段3の最重要攻撃対象

独立custodian・oracle凍結・cache分離・price version・ITT・非劣性marginのいずれも、
**本wave完成後も成立しない** (真データ・独立第三者・実測実施を要する§5.3の6項目が理由、上記参照)。
これは本waveが生む新しい欠陥ではなく、preregistration文書が着手前から明記していた既知の限界
(§14 limitation) であり、Wave A/B/Cも同一の前提で作業した。

**したがって段4裁定の暫定方向: 「実装しない」ではなく「装置面 (4対象) は完成させ、
`routing_evidence_status`が本wave完了後も`inconclusive`のまま (custodian関連は
`apparatus_diagnostic`) であることを decisions/worklog に明記する」。**
根拠: (a) command引数の主文が「完成させる」と定言している、(b) 「〜が成立しない場合は
apparatus_diagnostic/inconclusiveとして止め、model-only swap・現dev-wave model変更・実比較実験は
行わない」の構文は、"stop" の対象を3つの列挙項目 (model swap・dev-wave model変更・実比較実験の
実行) と並列に読むのが自然で、装置コードの完成自体を指していない、(c) §5.2表がこの4面の実装を
「実装時の申し送り」として最初から予定しており、DW-G04 (発火条件を満たす既存artifact path) を
満たす、(d) Wave A/B/Cが同型パターン (機構は一般化、実データはPOS/NEGのみ、cache/priceはnull専用
fail-closed) で3回実証済み。**この判断自体が(P1)であり、段3で正面から攻撃させる
(「実装しない」が正しい可能性を含め、両方向を検証させる)。**

## 不変条件

- 既存reasoning-axis (POS/NEG×max/high) の回帰・変異matrix (Wave A+B+Cで292 passed、
  変異合計17/17 KILLED実績) を非破壊のまま維持する。
- Wave D所有関数以外 (Wave C所有面) は無改修。D614の唯一の例外は既に land済みで再度触らない。
- public packet (`packet_dir`/`packet-state.json`) に model・stage・task_id・price_version を
  出さない (§5.2表の明示要求)。`mask_strength: "same-owner-advisory"` の自己申告ラベルは
  そのまま維持する (独立custodian化を偽装しない)。
- `cache_condition`/`price_version`はnull以外を受理しない (Wave Aの既存fail-closed設計を
  そのまま踏襲、新規の実制御・実データを持ち込まない)。
- 新規task/cache制御/価格データは持ち込まない。既存POS/NEGを唯一かつbyte同一のmanifest内容として
  維持する (Wave A/B/Cと同型)。
- 本waveはlive Codex A/B実走を一切行わない。model-only swap・現dev-wave model変更・実比較実験は
  行わない。

## 成果物の形

`tools/codex_reasoning_ab.py`:
1. `_validate_schedule`(5085-5156)を、既存の`normalize_schedule`/`normalize_legacy_schedule`/
   `validate_nullable_dimensions`/`expected_schedule_from_manifest`(2305-2487、Wave A実装済み・
   テスト済み・未配線) を呼ぶ形へ書き換え、task/cache_condition/price_version/requested_modelを
   検査対象に追加する。
2. `_aggregate_verified`(5515-5697) のPOS/NEGハードコード意味論 (arm loop 5545、
   `case=="POS"` 5547、decision dict 5603-5608、`identities`同型のNEG/POS前提) を
   `TASK_MANIFEST`の`oracle_kind`駆動へ一般化する。`resources`辞書(5630-5645)へ
   `requested_model`/`benchmark_task_id`/`cache_condition`を追加する。
3. `_replay_manifest`(5898-6264) の `identities` 辞書 (6243、`{"POS": set(), "NEG": set()}`) を
   task_id駆動へ一般化する。
4. `make_packets`(6298-6390) の `len(grouped) != 10` (6309) をmanifest/schedule由来の動的期待値へ
   変更し、public/privateの分離構造 (6311-6390) と `mask_strength` ラベルはそのまま維持する。

`orchestrator/tests/test_codex_reasoning_ab.py`: 既存全緑を維持しつつ、上記4面の新規/変更挙動
(schema拡張の受理・拒否、task汎用化後のaggregate集計、動的task countのmake_packets) を検査する
テストを追加する。既存カバレッジは統合的 (`test_verify_*`/`test_replay_*`経由) で対象4関数を
直接名指すテストは0件 — 新規テストがどの粒度で検査するかは段2プランが決める。

## 並列分割方針 (段2プランが最終決定)

暫定仮説: 4面は同一ファイル内で相互依存 (`_validate_schedule`のschema拡張が
`_aggregate_verified`/`_replay_manifest`/`make_packets`の入力形を変える) するため、Wave Cの前例
(1実装単位で完結) に倣い**単一実装単位**を既定とする。段2が規模 (対象行数・テスト行数) を実測し、
素集合分割が可能かつ有益と判断すれば見直す。

## DW-G05 (成果物影響、1行)

実装しない場合、Wave A (2026-07-30着手) が用意したtask汎用化基盤が永久に未配線のまま残り、
T-1434(4)の7論点のうち本論点も未完了のまま持ち越され、将来いつか着手する場合も同じ調査を
再度要する。放置してもPhase 3のcertified選択・proof chain・試行台帳には影響しない
(dev-wave内部tooling のrefactorのため)。

## DW-G01〜G04

本waveはPhase 3 campaign軸の新設ではなくdev-wave tooling (T-181装置) のrefactorのため、
G01 (生死実験先行)・G02 (初回cycle前blocker限定)・G03 (族一般化に独立2例) は不適用
(Wave A/B/C precedentと同じ判断)。G04 (条件付き機能の発火gate) は該当なし — 新規の条件付き機能を
追加するのではなく、既存フィールド (cache_condition/price_version、Wave A実装済み) の検査経路を
実路へ配線するだけであり、artifact pathは§5.2表そのもの。
