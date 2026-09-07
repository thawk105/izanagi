# [T-1851] C1b 未裁定 4 件の裁定 (codex 2 本に諮り、親が決定)

ユーザー指示「codex に相談して決めて」により、`s4-adjudication.md` 3 節の 4 件を codex 2 本
(lane sol / luna、reasoning=xhigh、read-only) へ諮り、両者の推奨を突き合わせて親が決めた。
逐語は `verbatim/rulings-lensA.md` / `verbatim/rulings-lensB.md`、prompt は `prompts/` にある。
base は `68573078e`。

- レンズ A: 「v2 terminal が実際に書けるようになる最小の設計を 1 本決めろ」
- レンズ B: 「そもそもこの機構は要るのか」から疑わせ、封印が無いときの偽装手順と伝播経路を追わせた

## 0. 機構は必要か (レンズ B が先に答えた前提の再検査)

**必要である。** ただし守る対象は「試行 proof chain に虚偽の terminal 事実が入ること」だけで、
数値の選択ではない。数値は既存の verifier が守っている。

レンズ B が具体的な偽装手順を出した。正当な reservation / classification / observation-start までを
通常経路で作り、**terminal builder だけが任意の出力 bytes・status・digest・primary・測り直し理由を
返す**。core は形と相互整合しか見ないので、その行が hash chain に載る。
`capture_attempt_registry_prefix()` がその chain head を result v5 に載せ、live verifier /
holdout freeze / ratified freeze が同じ prefix を受理する。**床値の数値は journal から再計算される
ので変わらないが、「この attempt はこの理由・結果だった」という proof chain が偽装される。**

既存の防壁がここを塞いでいないことも実測で確認された。classification receipt は観測前理由と
authority を固定するが観測後の実測を持たない。observation-start は phase 順を束縛するだけ。
deferred reader は `raw_output_sha256` を再計算するが、**hash 対象の bytes 自体を terminal builder が
供給する**。admission claim は generation / slot / attempt / manifest を閉じるが terminal outcome を
閉じない。

**現時点で certified 成果物への到達経路は 0 件である** (`assemble_result()` は v4 を出し、
holdout / ratified の top-level 検査も既定 v4 を要求する)。したがって C1b 単独では有効化されない。

## 1. core の等値検査と E2 語彙の衝突 — **レンズ B 案を採用**

**決定: `failure_reason` は観測前 classification の exact echo のままとし、E2 の 4 語は
v2 専用の新 field `measurement_retry_reason` に載せる。`_assert_null_matrix` に
`retryable_reason_field` を渡し、retryable 集合の照合先を profile が選べるようにする。**

`DomainProfile` に `retryable_reason_field: str = "failure_reason"` (keyword-only、既定は現行) を
足し、v2 profile だけ `"measurement_retry_reason"` を指す。

**なぜ A 案でなく B 案か。** レンズ A は「validated capability があるときだけ
`failure_reason` と分類理由の直接等値を飛ばす」policy flag を提案した。これは**既存の正しさ検査に
条件付きの迂回路を新設する**形であり、契約 v2 の A4 (「core では外さない」) の趣旨に反する。
B 案は既存の等値検査を 1 行も変えない。新しい情報を新しい field へ載せるだけなので、
capability を持たない呼び手は迂回路そのものに到達できない。**規律 2 に対して厳密に強い。**

現行 `_assert_null_matrix` (`attempt_registry_core.py:1050-1090`) と矛盾しないことを親が確認した。

- `observed` は `failure_reason is None` を要求する (`:1066`)。observed のとき分類理由は null なので通る
- 観測**前**の失敗 (競合・起動失敗) は `failure_reason` = 分類理由の echo、
  `measurement_retry_reason` = 対応する E2 語。等値検査も null matrix も通る
- 観測**後**の失敗 (標本不足・分散超過) は分類理由が null なので `failure_reason` = null、
  `measurement_retry_reason` = E2 語。等値検査は null == null で通る
- `retryable-failure` が要求する `report_sha256` 非 null / `observation_sha256` null /
  `primary_value` null は契約 3 節の導出規則と一致する

**A 案から採るもの (配線の規律):**

- capability を渡せる入口を **1 本に限定**する。core の全 load API へ keyword を伝播しない
  (レンズ B の B06 と同じ結論)
- launcher は core の capability を受け取らない。`seal_terminal_evidence(reservation, opened, terminal)`
  は未完成の draft を返し、**adapter が exact な `CapturedObservation` から 3 digest を補って**
  validated capability を発行する
- A が列挙した **7 組の (観測前理由, 観測後理由)** を正例・負例の対照表として事前登録する。
  B 案では `(failure_reason, measurement_retry_reason)` の組として読み替える。
  `terminal-failure` / `not-consumed` / echo 改変 / E1 と異なる後理由 / digest 不一致は増加集合に入らない

**v2 terminal 行の key はここで 2 つ増える** (`terminal_evidence_sha256` と
`measurement_retry_reason`)。v1 の key 集合と受理集合は 1 bit も変わらない。

## 2. `exec_failures` の出所 — **レンズ B の診断を採用、実装は C2 へ**

**決定: 契約 v2 の定義が誤り。`exec_failures` と `rep_integrity_failures` は別の量である。**

- `exec_failures` = runner が rep の `open()` で捕捉した**実行例外**の数 (`runner.py:953` 付近)
- `rep_integrity_failures` = return code / counter / schema / 欠損を独立に検査した**証跡不完備**の数
  (`s8b_floor_stats.py:471` 付近)

同じ rep で両方が立つことがある。契約が「非 zero rc または起動失敗をすべて `exec_failures` と
数える」と書いたのが誤りだった。レンズ A が提案した「契約を現行の notes regex 算出に合わせる」案は
**却下する** — それでは証拠が「campaign が自然文から何件と数えたか」しか証明せず、
自然文を信頼経路に残す。規律 3 の「正しさシグナルを後付けにしない」に照らして無価値に近い。

**ただし実装の割り当てを分ける。** レンズ B が提案した「runner の私有 rep sink へ構造化
`execution_failure` を足し、campaign と封印 validator の双方がそこから数える」形は、
**runner と campaign を変更するので C1b の所有面ではない。C2 が持つ。**

したがって C1b では次のとおりにする。

- 契約は上の 2 量の定義へ追記訂正する
- C1b の証拠は `exec_failures` を campaign record との**等値でのみ束縛**し、
  **「この値が各 rep の実行成否を証明する」とは主張しない。** 主張できないことを主張しない
  (規律 3)
- rep observation の 6 key → 7 key 化と、それに伴う凍結 gate の pin 閉包は C2 の scope とする

## 3. 封印の信頼境界 — **両レンズ一致。明文化する**

**脅威に含める:** 外部 CCBench と生成 variant が返す悪意ある bytes / return code / 出力、
通常の Python 操作による capability 内容の書き換え、誤った production caller。

**脅威から除外する (契約に明記する):** 任意の同一 process module 改変、private issuer の意図的な
直接呼出し、reflection 操作、同一 Unix uid による registry と validator の同時改変。

**別 process の issuer は作らない。** 同一 uid・同一 repository・同一の検証コードを使う限り
独立性は増えず、IPC と crash 状態だけが増える。これは D387 が既に述べている限界と同じであり、
**主張せず明記する**という CLAUDE.md 規律 7 の書き方に従う。

代わりに閉じる手段は 3 つ。
(a) capability の唯一の実データを immutable な canonical bytes にし、文書と射影は毎回そこから再生成する。
(b) adapter が再導出する。
(c) **test 用 capability と production 用 capability を型で分離し、
test 用 launcher が production の封印を発行できない構造にする。**

レンズ A が実測で示したとおり、発行台帳への membership を権威にしてはならない
(直接 insert・private 発行子の直呼び・`__reduce_ex__` がいずれも通る)。

## 4. C1b の単位 — **両レンズ一致。縦 1 単位、単独 land しない**

**決定: 契約 v3 確定後、leaf / launcher / profile / core / adapter を縦 1 単位で作る。
branch 上の checkpoint にはするが単独では land せず、C2 / D2 と同じ land 単位に置く (D1341)。**

production 効果のある分割は存在しない。leaf だけでも launcher だけでも v2 terminal は 1 行も増えない。

**改訂見積り: production 約 +1,000〜1,600 行、test 約 +1,500〜2,400 行。**
元 plan の +1,228〜1,717 / +1,775〜2,465 から、契約が要求していない自発的拡張 3 件
(durable claim の新 schema、handle state への mode 追加、core 公開 API 群への capability 伝播) を
落とし、v2 専用 reason field と null matrix の分離を足した値である。

実装子は**所有 file が素集合になる 3 本**に分ける。
(1) leaf + その test、(2) launcher + profile + その test、(3) core + adapter + その test。
(2) と (3) は (1) の完了後に並列で置く。

## 5. 次 wave の着手条件

- 契約 v3 を 1 節〜4 節の裁定で確定させてから段 1 を書く。**契約の各条項について、
  それが束縛する consumer に最小 probe を 1 本通してから固定する**
  ({{D:adjudicated-contracts-need-consumer-feasibility-probe}} と同じ規律。本件で登録済み)
- 段 2 / 段 3 の成果物は骨格が変わらない限り流用してよいが、
  **(1) の設計が A 案から B 案へ変わったので、変異候補は再照準が要る**
- C2 は runner の構造化 `execution_failure` と campaign の算出変更を持つ。これを C1b へ混ぜない
