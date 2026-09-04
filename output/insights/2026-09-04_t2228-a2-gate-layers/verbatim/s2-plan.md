## 総括

- 静的予測では層 4 は出ず、4 cell とも全 arm が family admission を通り、campaign へ到達する。
- 実 CCBench の stock 経路では、owner TU 自身が依存 closure に入り、`ERR` 内の `__FILE__` 差を T-2226 分類器が root-location-only と判定する見込みである。
- unit 正例は、`_SUPPLIED` を実 g++ / cmake で評価して得た実 record を、2 cell の driver 経路へ返し、実体の family と canonical receipt を検査する形を推奨する。
- 負例は `_issue_arm_record` 発行の赤 record と実体 family を使い、`CertificationError` の完全な detail を固定する。
- production は実走で真の層 4 が確認された場合だけ変更する。既存 source 形 pin と期待値は変更しない。
- campaign 失敗時、admission の canonical receipt は保存されず、後続の `job.stdout` log は間接証拠にしかならない。
- 本段では編集・pytest 実走とも行っていない。

## 実走の予測

policy の順序は `paper_story_a2_certification.v2.json:81-117`、各 workload 内の stock → adopted 固定は `paper_story_a2_certification.py:3071-3082` による。以下は unrelated な compiler/configure failure がない場合の予測である。

| cell | macro | supply `terminal_status / reason_code` | meaning `terminal_status / reason_code` |
|---|---|---|---|
| rr5-stock | BACKOFF_FIXED=-1 | `green / stock-inert-preprocess-root-location-only` | `green / declared-meaning-observed` |
| rr5-stock | BACKOFF_NOINLINE=0 | `green / stock-inert-preprocess-root-location-only` | `unestablished / meaning-witness-undeclared` |
| rr5-fixed10 | BACKOFF_FIXED=10 | `green / requested-default-preprocess-different` | `green / declared-meaning-observed` |
| rr5-fixed10 | BACKOFF_NOINLINE=0 | `green / stock-inert-preprocess-root-location-only` | `unestablished / meaning-witness-undeclared` |
| rr50-stock | BACKOFF_FIXED=-1 | `green / stock-inert-preprocess-root-location-only` | `green / declared-meaning-observed` |
| rr50-stock | BACKOFF_NOINLINE=0 | `green / stock-inert-preprocess-root-location-only` | `unestablished / meaning-witness-undeclared` |
| rr50-fixed5 | BACKOFF_FIXED=5 | `green / requested-default-preprocess-different` | `green / declared-meaning-observed` |
| rr50-fixed5 | BACKOFF_NOINLINE=0 | `green / stock-inert-preprocess-root-location-only` | `unestablished / meaning-witness-undeclared` |

根拠は次のとおり。

- driver は各 cell で両 macro を辞書順に選び、supply と meaning の双方を無条件に呼ぶ (`paper_story_a2_certification.py:613-668`)。固定値 -1 には stock branch declaration、非負値には binary64 declarationを作り (`:630-654`)、NOINLINE には declaration を作らない。
- `BACKOFF_FIXED=-1` と `BACKOFF_NOINLINE=0` はそれぞれ declared inert、default equality により inert になる (`condition_meaning_gate.py:892-900,2435-2449`)。これは adopted cell の NOINLINE にも当てはまる。
- 非 inert の fixed5/fixed10 は、build-root 文字列が前処理結果へ漏れず、closure が一致し、bytes が異なれば `requested-default-preprocess-different` となる (`condition_meaning_gate.py:2509-2545`)。
- NOINLINE の declaration は `None` なので、compiler を呼ぶ前に `meaning-witness-undeclared` を発行する (`condition_meaning_gate.py:3178-3184`)。
- supply が全て green、meaning が green または unestablished なら admission は `admitted=True` である (`condition_meaning_gate.py:3921-3947`)。

stock の実 CCBench について、分類器は発火すると予測する。

1. `-MD -MF` で得た dependency list を `_dependency_closure` が走査し、source root 配下の `cc/silo/transaction.cc` を `source/cc/silo/transaction.cc` として登録する (`condition_meaning_gate.py:2021-2071`)。さらに owner TU が無ければ分類前に `owner-tu-unresolved` となるため (`:2176-2188`)、正常経路で classifier に到達する時点では owner identity は必ず集合内にある。
2. 実 owner は `ERR` を `transaction.cc:106,690` で使用する。`ERR` は `NNN` を展開し (`external/ccbench/include/debug.hh:54-65`)、その `NNN` に `__FILE__` がある (`:56-57`)。
3. `-P` により line marker は除かれる (`condition_meaning_gate.py:1991-1993`) が、展開結果には概ね `".../<root>/cc/silo/transaction.cc"` という文字列が残る。引用符は path-byte 集合外なので、classifier は root prefix と `cc/silo/transaction.cc` を抽出できる (`:2283-2329`)。
4. closure は raw bytes に `__FILE__` を持つ `source/include/debug.hh` も検出するため、`root_dependent_builtin_paths` は非空になる (`:2029-2064`)。従って置換が 1 件以上、残差なし、builtin ありの三条件 (`:2332-2345`) を満たす見込みである。
5. inert 時の patch 差は前処理で消える。BACKOFF_FIXED=-1 は stock 枝、NOINLINE=0 は属性なしとなる (`patches/silo-backoff-fixed.patch:52-74`) ため、残る差は source root の文字列だけと予測する。

親による読み方は以下とする。

- `jobs/rr5/scheduler/job.stdout` と `jobs/rr50/scheduler/job.stdout` の末尾 JSONを読み、各 workload 2 cell 分の `condition_gate_receipts` を確認する。これは `summary` への代入 (`paper_story_a2_certification.py:3140-3142`) と CLI 出力 (`:4199-4215`) に対応する。
- 各 receipt の supply/meaning record と admission を canonical JSON として照合し、表の status/reason、`admitted=true`、record ID の対応を確認する (`:686-695`)。
- `[campaign] ...`、`[campaign] evaluate ...` は admission 後の間接的な到達証拠である (`orchestrator/campaign/loop.py:410,529`)。両 workload の campaign 到達を別々に確認する。
- `job.stderr` に gate rejection があれば、最初の赤 cell で context が例外終了するため、後続 cell・receipt・campaign は未到達である (`paper_story_a2_certification.py:674-685`)。

campaign が admission 後に例外終了した場合、record と admission は context 内のメモリにあるだけで (`:669-696`)、`run_campaign` 成功後の代入 (`:3142`) と CLI 出力 (`:4208-4215`) には到達しない。`log=print` は campaign へ渡されるが (`:3013-3016,3127-3139`)、最初の log は `loop.py:410` なので、それ以前の失敗なら後続 log すらない。後続 log があっても「admission を通過した」間接証拠であり、admission 内容そのものではない。これは既存境界として記録し、scope 外の事前保存は追加しない。

予測に反して `stock-inert-mismatch` が出た場合は次の順で層 4 を扱う。

- `root_diff_replacement_count`、`root_diff_has_residual`、両 closure と builtin paths を先に読む。残差が本物なら赤を維持し、classifier を緩めず tree/patch 差を直す。
- root-only なのに lexical shape のため置換できない場合だけ、`condition_meaning_gate.py:2250-2346` を、requested/control 双方に共通する `source/<relative>` identity から作った完全な絶対 path 対だけを許す pairwise diff 検査へ狭く直す。call site `:2553-2568` から control closure も渡し、任意 prefix や regex は受理しない。
- owner が depfile から欠ける場合は `:2167-2188` で、選択済み owner を同じ stat/read/hash 規律で closure へ明示的に束縛する。単に `owner-tu-unresolved` を無効化しない。
- 実 `ERR` → `NNN` → `__FILE__` の形を模した正例を `test_condition_meaning_gate.py:621` 付近へ、意味残差の負例を `:662-698` 付近へ追加し、既存の closure 外 literal、path-byte prefix、builtin 不在の負例 (`:701-800`) も維持する。

## unit 検査の設計

`test_paper_story_a2_certification.py:17-26` で実体 module を `G` として importし、`:50` 付近に `_SUPPLIED` の fixture path と実 compiler 検出だけを追加する。正例・負例本体は既存 helper を変更せず、現在の `:563` 直前または直後へ独立テストとして追加する。

**推奨する正例**

- `_SUPPLIED` と `_SUPPLIED/stock` を `G.capture_define_inputs` に渡す。
- `driver_id` を driver が生成する exact 値、すなわち `...paper_story_a2_certification:cell-0` と `cell-1` にして、BACKOFF_FIXED=-1 と 10 の request を作る。
- 実 `evaluate_define_supply_effectuation` と実 `evaluate_define_runtime_meaning` を g++ / cmake fixture 上で事前実行する。想定は cell-0 が stock-identical/declared-meaning-observed、cell-1 が requested-default-different/declared-meaning-observed。
- 各 record が exact `ConditionArmRecord` であり、`G._validate_arm_record_integrity(record)` を issuer 必須のまま通ることを確認する。green supply はこれにより `_validate_supply_green_evidence` の exact schema (`condition_meaning_gate.py:3429-3590`) を必ず通る。
- `_REAL_CONDITION_GATE_FAMILY` へ 2 genome を渡す。patch checkout/applied、prebuild、temporary directory、capture、2 評価関数だけを leaf seam で差し替え、評価関数から上記の実 record を返す。`require_condition_gate_family` は差し替えない。
- `receipts` が 2 件であること、および各 `supply_records`、`meaning_records` が `json.loads(record.canonical_json())` と完全一致し、`admission` が実体 family の `json.loads(admission.canonical_json())` と完全一致することを検査する。
- call assertion は `checkout=1`、`applied=1`、`TemporaryDirectory=1`、prebuild=1、capture=1、supply evaluator=2、meaning evaluator=2 とし、cell-0 → cell-1 の request 順も固定する。これが D1522 の実効発火証拠になる。

**検討したが採らない正例**

`_issue_arm_record` へ `_validate_supply_green_evidence` の全 field を手組みする方法も可能である。しかし `condition_meaning_gate.py:3431-3443` の exact key 群に加え、compiler/CMake identity、argv、closure digest、owner digest、root evidence を `:3461-3590` と同じ形で再実装することになる。高速ではあるが、実 evaluator がその schema を生成する保証にならず、validator と同じ誤りを複製しやすい。従って実 fixture record を推奨する。

**負例**

- BACKOFF_FIXED=10 の exact request と digest を作り、`G._issue_arm_record` (`condition_meaning_gate.py:963-988`) から `red / configure-failed`、`detail="cmake emitted an unused-variable warning"` の supply record を発行する。
- 対になる meaning は同じ request に対する実 fixture の green recordを使う。両 record を `_validate_arm_record_integrity` に通す。
- 先に実体 `G.require_condition_gate_family(..., use_class="paper")` を直接呼び、`admitted is False` を固定する。
- driver context では両 evaluatorだけを差し替えてその record を返し、family は実体のままにする。
- `CertificationError` が次の exact substring を含むことを検査する。根拠は `paper_story_a2_certification.py:675-685`。

```text
BACKOFF_FIXED:supply-effectuation:configure-failed:detail='cmake emitted an unused-variable warning'
```

- 負例側も各 leaf の call count を 1 に固定する。赤 record を返した supply evaluator、対になる meaning evaluator、capture、patch/prebuild のどれかが未発火なら失敗させる。

実 fixture は小さな owner TU で、正例は CMake configure 4 回と少数の preprocess/compile、負例は meaning compile 1 回程度である。追加時間は概ね 5〜15 秒と見積もる。5 分上限には十分収まる見込みだが、親が `tools/run_tests.py` 経由で対象 file の実時間を確認する。上限へ近づく場合も、green evidence の手組みへ退行せず、負例 meaning を issuer 付き unestablished record にして compiler 1 回だけ削る。

既存の `test_paper_story_a2_certification.py:124-252,254-497,500-562` は編集せず、期待値も変えない。従って次も不変である。

- `run_source` の gate-before-campaign assertion (`:62-66`)
- `patchharness.checkout(` の count 1 (`:67-78`)
- variant root を campaign へ渡す AST pin (`:81-119`)
- toolchain manifest の `count(passed) == 2` (`:3242-3258`)

## 4-cell reject の位置づけ

- 新 attempt が全 admission を通って同じ reject なら、T-2022 は当時の事実として残し、現行経路による独立した追認を別に記録する。
- gate が赤なら、T-2022 の歴史的 reject は維持するが、関門配線後の現行正しさを支える材料にはしない。
- admission 後に非 reject または不確定なら、旧測定を無効化せず、現行主張との差または未確定結果として分離する。

## (P) への賛否

- **P1: 賛成。** 実 CCBench、production entry、計算ノードという実体を名指しできる唯一の scope 内証拠である。専用 probe は registry と inventory を増やし、本命令の範囲外になる。採らない場合の代案は fixture unit だけだが、実 CCBench と campaign 到達を証明できないため代替にはならない。
- **P2: 賛成。** 赤 record は `_issue_arm_record`、判定は実 `require_condition_gate_family` とし、`SimpleNamespace` を使わない。代案の実 `_F707` configure failure はさらに強いが、負例の目的に対して遅く、driver wiring の検査を不必要に compiler failure へ結合する。
- **P3: 条件付き賛成。** 間違った root/tree を渡したなら driver `paper_story_a2_certification.py:589-612`、root-only diff の分類漏れなら gate `condition_meaning_gate.py:2250-2346` が修正先である。単なる通過目的で driver を迂回させる案には反対する。意味残差があれば修正せず赤を維持し、受理集合変更が必要なら裁定へ返す。
- **P4: 賛成。** supply → meaning の順序問題ではなく、cell-0 の例外により cell-1、admission、receipts、campaign が未到達だった問題である。両 arm 自体は各 cell で無条件に呼ばれる (`paper_story_a2_certification.py:655-668`)。別解釈を採ると、2 cell 正例を欠き元欠陥を直接検査できない。

## 影響一覧

| 対象 | 変更判定 | 理由 |
|---|---|---|
| `orchestrator/tests/test_paper_story_a2_certification.py:17-50,563` | 変更 | 実 family/record の正例・負例と fixture binding を追加する唯一の無条件編集面。 |
| `orchestrator/campaign/paper_story_a2_certification.py:577-697` | 変更なし | driver wiring、receipt schema、detail message をそのまま実体検査する。 |
| 同 file `:3111-3142,4199-4215` | 変更なし | gate-before-campaign と stdout receipt 境界を維持する。 |
| `orchestrator/campaign/condition_meaning_gate.py:2250-2589` | 条件付き | 実走が root-only の分類漏れを示した場合だけ、closure-bound exact path 対へ修正する。 |
| `orchestrator/tests/test_condition_meaning_gate.py:600-940` | 原則変更なし、層 4 時のみ追加 | 既存 root-only 正例、意味残差・closure 外・builtin 不在負例の期待値は変えない。 |
| 同 file `:1524-1722` | 変更なし | record ID、family admission、issuer、green evidence schema の既存防壁を維持する。 |
| `orchestrator/tests/condition_gate_test_support.py:126-191` | 変更なし | compiler 検出と fixture 構築を再利用するだけ。 |
| `orchestrator/campaign/backoff_sweep.py:105-165` | 変更なし | 同 supply evaluator の consumer。層 4 修正時も既存受理集合を保つ。 |
| `orchestrator/campaign/backoff_repro.py:63-84` | 変更なし | 上記 helper 経由の consumer。本 wave では実走しない。 |
| `orchestrator/campaign/s1_direct_comparison.py:266-304,307-345` | 変更なし | 同 gate と returned-record validator の consumer。本 wave では実走しない。 |
| `orchestrator/tests/test_backoff_sweep.py:126-171` | 変更なし | requested/default と stock-identical の既存実体正例を維持する。 |
| `paper_story_a2_certification.v2.json:81-117` | 変更なし | 4 cell と genome は固定。 |
| T-2022 attempt と凍結成果物 | 変更なし | 新 attempt は別 leaf。規律 7 により旧 reject を上書きしない。 |
| `output/insights/2026-09-04_t2228-a2-gate-layers/README.md:new` | 親が追加 | 実測表、ログ位置、層 4 判定、旧 reject の条件付き位置づけを記録する。 |

## 変異候補

| 変異 | 落とす assertion |
|---|---|
| `condition_meaning_gate.py:3921` の supply green 条件を red も受理するよう緩める | `test_paper_story_a2_certification.py:563` 追加負例の `admission.admitted is False` と `CertificationError` assertion。 |
| `paper_story_a2_certification.py:669-673` で実 family 呼出しを fabricated admission に置換する | `test_paper_story_a2_certification.py:563` 追加正例の admission canonical JSON/record IDs 一致、または追加負例の拒否 assertion。 |
| `paper_story_a2_certification.py:686-695` で record/admission の canonical serialization を省略または別 payload にする | `test_paper_story_a2_certification.py:563` 追加正例の `json.loads(record.canonical_json())`、`json.loads(admission.canonical_json())` 完全一致。 |
| `paper_story_a2_certification.py:675-684` から `evidence["detail"]` の伝搬を除く | `test_paper_story_a2_certification.py:563` 追加負例の完全な `macro:arm:reason_code:detail=` substring assertion。 |
| `paper_story_a2_certification.py:613-668` で cell-1 または片 arm の評価を飛ばす | `test_paper_story_a2_certification.py:563` 追加正例の `receipts == 2`、supply evaluator 2 回、meaning evaluator 2 回、および cell 順 assertion。 |