# 段4 裁定 — T-1434 Wave D

親が両レンズの所見を独立検証し、real/refuted/unclear を確定し、plan v2 を確定する。

## (P1) 実装可否の最終裁定

**実装する。** 両レンズとも「6条件不成立ゆえ絶対に実装しない」を refuted (Lens B #2 実測)、
一方で「plan の無条件実装にも同意しない」(Lens B 総合判定 unclear/major) と結論した。
親裁定: 具体的な blocker (下記) を plan v2 へ全て反映した上で実装する。**「実装しない」を
選ばない根拠は、両レンズが独立に「6条件が全部揃っていないから実装自体を止めるべき」という
強い主張を refuted としたこと、既存 Wave A 基盤の再利用便益は real (弱いが) と認めたこと、
scope 外6項目 (power simulation/独立custodian/cache制御/replayer/task catalog/price snapshot)
への黙示的越境は12件中10件 refuted で確認されなかったこと。**

累積複雑化・利用見込み不足 (Lens B 所見3, real/major) は正当な懸念だが、これは「本 wave を
止める」根拠ではなく「T-1434(4) 残り6論点の要否をユーザーへ確認する」という段7以降の申し送り
事項として扱う (下記「段7への申し送り」)。

## brief の是正 (段1 brief の誤り、plan v2・段5 prompt へ反映)

1. **§5.2 単独は実装許可の根拠にならない (Lens B 所見1, unclear/major → real の指摘として採用)。**
   実装の**許可**は D603 (Wave D を後続wave送りにした = 本 wave の起票を認めた) と D614
   (Wave D 境界の確定) にあり、§5.2 は実装の**仕様** (何を実装するか) を与えるだけである。
   決定・decisions.md では両者を明確に分けて引用する。
2. **「6条件が1つも成立しない」は過大 (Lens B 所見2, real/major)。** 正確には次のとおり
   区別する: ITT はすでに §4.1 の解析規約として固定され、`test_m9_post_treatment_failure_
   remains_in_denominator` 等が分母維持を検査済み。`_load_adjudication` の freeze/hash/
   bijection もオラクル整合性の一部を既に担保している。**未成立なのは「規約・整合性検査」では
   なく「実データ・独立第三者・実測」を要する部分** (独立 custodian の実現、provider cache の
   実制御・attest、実 price snapshot、実 task catalog + 独立分類者2名、power simulation による
   margin lock)。段7の decisions.md はこの精密な区別で書く。
3. **DW-G04 は「不適用」でなく「該当し、成立」(両レンズ、real/major)。** 既存 fail-closed
   gate (`validate_nullable_dimensions` 等) を live path へ配線することは受理集合を変える
   新しい実効 gate の新設であり、G04 の対象になる。発火条件を満たす既存 artifact path (§5.2
   表 + Wave A 実装済みコード) を brief に書けているため、G04 は「成立」と扱い実装を続行する
   (「不適用」への訂正、実質的な影響なし)。

## plan v2 (段2 plan からの変更点、段5 prompt の正本)

### 変更 1 — block/pair 検査を「2つの arm」でなく「(arm, requested_model) の非同一性」にする
(Lens B 所見12、**real/blocker、最重要の修正**)

`docs/phase3-t189-model-routing-preregistration.md` §6.3 (親が段1で全文読了済み) が明記する
とおり、`arm` は reasoning effort であり model ではない。T-189 の paired protocol は
**同一 task/stage/cache/price・同一 arm・異なる `requested_model`** の 2 slot を許す
(reference: sol、treatment: luna)。既存 reasoning-axis は逆に **同一 model (暗黙 sol)・
異なる arm** の 2 slot である。plan (`s2-plan.md:30`) の「block 内 arm 集合を schedule 由来の
2 つの arm と比較する」は、T-189 型の pair (arm 同一) を「arm 集合が1要素しかない」として
誤って拒否する。

**是正:** block 内の2 slot 検査を、`(task, stage, cache_condition, price_version)` が両 slot で
一致し、かつ `(arm, requested_model)` のタプルが2 slot 間で異なることを要求する形にする
(「両方同じなら拒否、片方だけ違う分には arm/model のどちらが違うかを問わない」)。
既存 reasoning-axis 回帰 fixture (同一 model・異なる arm) と、新規 T-189 型 fixture
(同一 arm・異なる model) の両方を synthetic テストで検査する。

### 変更 2 — `_validate_verdict_row`/`append_verdicts` を manifest 駆動にする
(Lens A 所見1 + Lens B 所見13、**独立に一致した real/blocker**)

親が直接 `tools/codex_reasoning_ab.py:6420-6458` を読み確認した。`_validate_verdict_row`
(6447 行) は `equivalent_to` を module 固定の `KNOWN_FINDINGS` (POS/NEG 11 件) でしか検査せず、
`append_verdicts` (blind 検証提出時、6460 行〜) と `_load_adjudication` (5237 行、aggregate
再検証時) の両方から呼ばれる。

**設計制約:** `append_verdicts` は盲検提出時点で呼ばれ、reader はどの task の packet かを知らない
(reveal 前)。したがって finding ID 検査は **task 固有の集合ではなく、manifest 全 task の
union** (`known_finding_ids_for_manifest(task_manifest)`、Wave A 実装済み・未配線) でなければ
盲検性と両立しない。task 固有の絞り込み検査 (この finding が実際にこの packet の task に
妥当か) は reveal 後の `_aggregate_verified` 側で行う。

**是正:** `_validate_verdict_row`/`append_verdicts`/`_load_adjudication` の `_validate_verdict_row`
呼出しへ `task_manifest=TASK_MANIFEST` を keyword-only で追加し、`equivalent_to` 検査を
`KNOWN_FINDINGS` から `known_finding_ids_for_manifest(task_manifest)` へ置換する。CLI
(`append-verdicts`) には新規 flag を追加しない (default で束縛)。**これは対象4面の外形だが、
`_load_adjudication` (Wave D 所有) の直接依存であり Wave C 境界を侵さないため、
「task-specific oracle/adjudication」scope の一部として実装範囲に含める。**

### 変更 3 — legacy 互換のための schema version 補完を明示する (Lens A 所見3, unclear/major)

`_validate_schedule` の先頭で、`schedule.get("schema_version")` が無ければ
`LEGACY_SCHEMA_VERSION` (2) を補った non-mutating copy を作ってから `normalize_schedule` を
呼ぶ。version が `{2,3}` 以外なら現状どおり拒否する。

### 変更 4 — legacy row/resource ledger の shape 変更を「非破壊」でなく「明示的な波及」として扱う
(Lens A 所見2/6/9、Lens B 所見16、real/blocker+major の複数所見が一致)

brief/plan の「既存テストへの波及なし」は誤りと確定する。少なくとも次を段5 prompt へ明記する。

- `_validate_schedule` の戻り値 dict は新規 canonical fields (`benchmark_task_id`/`stage`/
  `cache_condition`/`price_version` 等) を持つようになる。戻り値の exact key 集合や件数を
  assert している既存 nodeid ( `orchestrator/tests/test_codex_reasoning_ab.py` を
  `grep -n "_validate_schedule("` して洗い出す) は、**新 key の追加を許容する形へ改訂して
  よい** (assertion の対象を狭めて「必要な既存 key が変わらず存在する」に限定する、または
  新 key を明示的に許可リストへ足す)。ただし既存 key の**値**(POS/NEG の hash、slot 数等)
  は変更しない。
- `_aggregate_verified` の `resource_ledger` 行 shape・`_aggregate_token_usage_observations`
  の出力も同様。`orchestrator/tests/test_codex_reasoning_ab.py:6687-6695` 付近の exact
  equality assertion を実装子が実際に読み、影響があれば「値は同じ、shape は新 key を許容」に
  改訂する。
- `test_replay_passes_schedule_requested_model_to_collect_run` (6018 行付近) 等、
  `_validate_schedule`/`_replay_manifest` を monkeypatch/fake している既存テストは、
  新シグネチャ (`task_manifest=` keyword 追加) を受けられるよう fake 側も更新する
  (デフォルト値があるため、fake が `**kwargs` を無視するか明示的に受けるかのいずれかで足りる)。

**段4裁定として、DW-S05-B「意図的に赤になるテストをxfail化しない」を確認した上で、
上記のような shape 拡張に伴う既存 assertion の改訂は許可する (値を緩めるのではなく、
新規 field の追加を許容する方向の改訂に限る)。実装子は改訂した nodeid を完了報告に明記する。**

### 変更 5 — POS/NEG 専用の concentration/submodule 検査を task 汎用化する (Lens A 所見5, real/major)

`_validate_schedule` の `scheduled_cases <= {"POS", "NEG"}` ガード (5137-5154 行) を、
`benchmark_task_id` ごとにグループ化した concentration 検査 (各 task の prompt_sha256/
snapshot_manifest_sha256 が task 内で 1 つに定まる) へ一般化する。submodule state の
全体一致検査 (5147-5155 行) は task に関わらず維持する。

### 変更 6 — cache 非制御時の resource 抑止は本 wave の scope に含めない (P2、段4 の判断)

Lens B 所見15 (cache gate 未達時に token/wall を `not-applicable` とする §12.3 の要求が
未実装) は real/major だが、**本 wave では実装しない。** 理由: `cache_condition` を
resource ledger へ明示的に記録する (常に null) こと自体が「この行は cache 未制御である」と
読み取れる十分な情報であり、`not-applicable` への変換・抑止ロジックは gate 評価器
(§12.3 全体、本 wave の scope 外) の一部である。gate 評価器を作らない以上、抑止ロジックだけを
先取りして作ると「使われない飾り」になる (規律5)。decisions.md にこの理由を明記し、
将来 gate 評価器を作る wave への申し送りとする。

### 変更 7 — `routing_evidence_status`/`apparatus_diagnostic` は計算しない、と明記する
(Lens B 所見14、real/blocker だが是正はスコープ限定でなく**説明の是正**)

axis ledger (task/stage/model/cache 別の resource・primary・reliability) は**生データの構造化**
であり、3値判定の計算器ではない。decisions.md・worklog・commit message のいずれにも
「`routing_evidence_status` を計算できるようになった」等の記述をしない。「将来、§5.3 の
6項目が埋まったときに、この axis ledger を入力として使える形にした」とだけ書く。

### 変更 8 — 単一実装単位、内部で3段階に順序づける (Lens B 所見17, real/major)

分割はしない (helper 共有・相互依存のため素集合分割が困難、Lens A/B とも分割を積極的に
主張していない)。ただし規模 (対象約800行・新規テスト12件超) を踏まえ、段5 prompt は
実装順序を明示する: (1) `_validate_schedule` の schema 配線 + legacy 互換層、
(2) `_validate_verdict_row`/`_aggregate_verified`/`_replay_manifest` の axis 拡張、
(3) `make_packets` の動的化。各段階の後に対象範囲だけの pytest 実行を親が行う
(DW-O18 の file 単独走の精神を単一 unit 内でも踏襲する)。

## 変異事前登録 (DW-M01、実装前に意図を確定)

以下を段6 で具体化して登録する。各変異は単一理由性を実装確定後に確認する。

1. `_validate_schedule`: `EXPECTED_SCHEDULE`/`10 slot` の hardcode 復活 (dynamic count 検査が
   死んでいないか)。
2. `_validate_schedule`: block 内 `(arm, requested_model)` 非同一性検査の無効化 (変更1の検査が
   殺されていないか)。
3. `_validate_schedule`: `cache_condition`/`price_version` の non-null fail-closed 拒否の無効化。
4. `_aggregate_verified`: `oracle_kind` 判定を `case` 直接比較へ差し戻す変異。
5. `_validate_verdict_row`: `known_finding_ids_for_manifest` を `KNOWN_FINDINGS` へ差し戻す変異
   (変更2)。
6. `make_packets`: 動的 count 検査の無効化。
7. `make_packets`: public state への task/model/stage/price 漏洩を許す変異 (盲検性の正例)。
8. `_replay_manifest`: `identities` の task 単位分離を無効化する変異。

具体的な old/new テキストと期待 node は段5 実装確定後、段6 で親が事前登録する
(DW-M01: 実装前に意図、実装後に具体登録)。

## 段7への申し送り (T-1434(4) 残り6論点)

Lens B 所見3 (累積複雑化・利用見込み不足) を裁定パッケージとして記録する。本 wave の完了後、
T-1434(4) の "7 未解決点のうち (4) の全部" は完了するが、"他6点" (power simulation・
独立custodian実現方式・provider cache制御実測・stage2/5 downstream replayer実装・
task catalog実データ+独立分類者確保・price snapshot実データ取得) は未着手のまま残る。
これらは本 wave の scope 外であり続けるが、**着手時期・要否をユーザーが再確認すべき事項**として
worklog の次の一手または見送り台帳へ記録する (段7で実施)。
