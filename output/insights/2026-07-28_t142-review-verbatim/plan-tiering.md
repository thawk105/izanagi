# [T-142] 進化探索ループ評価二層化 — 実装プラン v1

## 結論

推奨は案 (b) の限定形です。

```text
build → legacy verify → bench → S2 verify → COMMIT
```

ここで「良い候補」は、性能 floor ではなく、既存 COMMIT の安い必要条件である「legacy 緑かつ既存 full bench が正常完了した候補」と定義します。S2 はその候補にだけ実行します。

D58 の floor terminal 棄却を p3 loop にそのまま再利用する案は不採用です。現物では次の二重違反になります。

- 現行 D58 は `bench → floor 棄却 → legacy/S2` なので、screen 棄却候補では legacy が走らず、不変条件 3 に違反する。
- legacy を前へ移しても、floor 未満だが legacy/S2 と bench 自体は通る候補を terminal abort にするため、certified になり得る集合を縮める。

この推奨形で省略できる S2 は「legacy green だが bench が測定不能・CV 不定・admission 失敗等で、旧順序でも最終的に COMMIT 不能だった候補」に限られます。したがって受理集合は機械的に等値にできますが、単に遅いだけの候補には S2 を走らせる必要があり、想定する約 8 倍の高速化は保証できません。性能 floor でさらに絞るには別裁定が必要です。

## 1. 現物照合で確定した前提

- 通常経路は `pipeline.py:424-426,661-736` で `legacy → S2 → bench → COMMIT`。
- D58 screening は `pipeline.py:604-659` で `bench → floor 判定 → legacy/S2`。`test_campaign.py:1790-1806` も「screen reject なら verify 0 回」を固定している。
- `run_campaign()` は `loop.py:54-60` で `search_config["verify"] == "legacy+s2"` のときだけ S2 を組み立てるが、screening/evaluation-order の配線はない。
- 3 driver の verify 状態は異なる。

  - `p3_s4_loop.py:493-506`: legacy のみ。
  - `p3_s4_loop_sort.py:165-185`: legacy+S2。
  - `p3_s4_loop_trigger_gating.py:324-343`: legacy+S2。

- `p3_s4_loop.make_critic_digest()` (`p3_s4_loop.py:232-249`) は `load_screen_rejections()` を渡していない。現状で p3 に screen reject を入れると、`load_liveness_rejections()` も screen reason を除外するため、critic から完全に消える。
- D36 が要求した「共通 AND helper」は現物には完成形で存在しない。`wal.records_by_stage()` (`wal.py:586-601`) は最後勝ちの集約であり、docstring 自身が legacy/S2 の AND 判定には使えないと警告している。現在の保証は `evaluate()` のループ、COMMIT の `verify_configs`、AST テスト、一部 consumer の集合検査に分散している。

## 2. 設計選択肢

記号を次のように置きます。

- `L`: legacy verify が certified
- `S`: S2 verify が certified
- `B`: 現行 full bench が正常完了
- `F`: D58 の性能 floor 棄却条件に該当

現行の certified 集合は、論理的には次です。

```text
C0 = {v | L(v) ∧ S(v) ∧ B(v)}
```

### 案 A: D58 `ScreeningConfig` をそのまま p3 loop に配線

```text
build → bench → FならABORT → legacy → S2 → COMMIT
```

受理判定基準そのものは「COMMIT には L/S が必要」のままですが、certified になり得る集合は次へ縮みます。

```text
CA = {v | B(v) ∧ ¬F(v) ∧ L(v) ∧ S(v)}
   = C0 から floor 棄却候補を除いた集合
```

さらに `F` 候補で legacy が走らないため、不変条件 3にも違反します。

機械的な反例は簡単に作れます。

```text
legacy=緑、bench=正常だが floor 未満、S2=緑
```

- screening off: COMMIT
- screening on: `screen-slower-than-floor` で ABORT

したがって positive control「速い候補で S2 赤なら COMMIT 不能」は偽陽性防止しか示さず、集合等値の証明にはなりません。

**判定: 不採用。**

### 案 A′: D58 判定を legacy の後ろへ移す

```text
build → legacy → bench → FならABORT → S2 → COMMIT
```

legacy は毎 iteration 走るため不変条件 3は満たします。しかし集合は依然として `CA` であり、floor 未満だが S2 緑の候補を certified 不能にします。

**判定: T-142 の現裁定条件では不採用。**  
性能 floor を正式な受理条件へ昇格する別裁定がある場合だけ再検討できます。

### 案 B: 既存必要条件だけで short-circuit する

```text
build → legacy → bench → S2 → COMMIT
```

「良い候補」は `L ∧ B` とし、`B` に性能 floor を含めません。遅くても full bench が正常なら S2 へ送ります。

```text
CB = {v | L(v) ∧ B(v) ∧ S(v)} = C0
```

検査順を交換しただけなので、固定された `L/B/S` の結果に対する受理集合は等値です。新順序で S2 を省略するのは `B=false` の候補だけで、これは旧順序でも最終 COMMIT 不能です。

| L | B | S | 旧順序 | 新順序 | 新順序で S2 |
|---|---|---|---|---|---|
| false | * | * | reject | reject | 実行しない |
| true | false | * | reject | reject | 実行しない |
| true | true | false | reject | reject | 実行 |
| true | true | true | COMMIT | COMMIT | 実行 |

**判定: 推奨。**

### 案 C: floor 未満を非 terminal の S2-deferred にする

floor 未満を ABORT せず、明示 promotion 時に S2 を走らせられる状態として残す案です。潜在的な certified 集合は維持できますが、次が必要です。

- 新 WAL stage と `EvalState.deferred`
- 通常 resume と明示 promotion の区別
- duplicate 提案処理
- deferred bench 値の全 consumer 監査
- promotion API と最終 drain 条件
- p3 checkpoint/whiteboard の新 outcome

D58 設計は非 terminal screen reject を D13/D25 との衝突から明示的に却下しており、現在の状態機械には受け皿がありません。また promotion されない候補を「certified になり得る集合に残った」と数えてよいかはユーザー裁定の解釈を要します。

**判定: T-142 v1 には採らない。性能 floor による本格削減が必要なら別設計・別裁定。**

## 3. 推奨案の file:line 実装計画

以下の名称は提案名です。

### 共通 verify 方針 helper

- `orchestrator/campaign/verification_policy.py:1` 新設

  `LEGACY_TAG`、`S2_TAG`、`VERIFY_LEGACY_PLUS_S2` と、`required_verify_tags(search_config)`、`all_required_passed(required, observed)`、`commit_payload_covers(payload, required)` を単一化します。既存 import を壊さないよう `pipeline.py` から当面 re-exportします。

- `orchestrator/campaign/wal.py:586-606`

  `records_by_stage()` とは別に、提案名 `certified_commit_payload(layout, variant, required_tags)` を追加します。COMMIT の存在だけでなく `verify_configs` が必要タグを覆うことを確認し、p3 の duplicate 復元と tiered consumer が同じ AND 判定を使うようにします。

### `evaluate()`

- `orchestrator/campaign/pipeline.py:70-77`

  D58 の `SCREEN_REJECTION_REASON` と混同しない別キーを定義します。

  ```python
  SEARCH_CONFIG_EVALUATION_ORDER_KEY = "evaluation_order"
  EVALUATION_ORDER_LEGACY_BENCH_S2 = "legacy-bench-s2-v1"
  ```

- `orchestrator/campaign/pipeline.py:363-434` — `evaluate()`

  opt-in 引数 `evaluation_order: Optional[str] = None` を追加します。`screening` との同時指定、`do_bench=False`、S2 のない構成、未知 mode は WAL/build 前に ValueError とします。tiered runtime と campaign.lock の方針・必須 verify タグもここで照合します。

- `orchestrator/campaign/pipeline.py:424-426,539-603`

  `passes` を legacy と extra に分けます。`_run_one_pass()` は維持し、通常 off 経路は現在の `legacy → extras → bench` を変えません。

- `orchestrator/campaign/pipeline.py:604-699`

  新 opt-in 分岐だけを `legacy → _run_bench() → extras(S2)` とします。bench 開始前に legacy の `res.verdict` を消し、S2 未実行の bench abort に legacy の `"serializable"` が残らないようにします。

- `orchestrator/campaign/pipeline.py:700-736`

  `res.certified = True` の直書きをやめ、必須タグと通過タグの完全一致からだけ certified を作ります。2 箇所ある COMMIT 書き込みを nested `_commit()` へ集約し、その中で AND helper を必ず通して `verify_configs` を焼き込みます。

- `orchestrator/campaign/pipeline.py:604-659`

  既存 D58 screening の順序・floor・freshness・reason は変更しません。T142 mode と相互排他にして意味の混在を防ぎます。

### `run_campaign`

- `orchestrator/campaign/loop.py:43-60` — `run_campaign()`

  関数へ自由な runtime boolean は増やさず、`cfg.search_config` から evaluation order を導出します。tiered mode なのに `verify != legacy+s2` なら layout/WAL 作成前に拒否します。

- `orchestrator/campaign/loop.py:94-160`

  `evaluate()` へ `evaluation_order=` を opt-in 時だけ渡します。`CampaignSummary` に deferred/screened 状態は追加しません。`first_bench` は、S2-red 前に bench が成功した場合も次候補で再 settle する現状になるため、安全側のまま維持し、余分な settle は既知の小コストとして残します。

### campaign identity

- `orchestrator/campaign/ident.py:26-73`

  D58 の `screening_*` とは別に、提案名 `evaluation_order_search_config(enabled)` と `verify_evaluation_order_preimage()` を追加します。off はキーを完全に省略し、歴史的 campaign ID を温存します。

- `orchestrator/campaign/ident.py:76-103`

  `canonical_preimage()` / `campaign_id()` は既に全 `search_config` をハッシュするためアルゴリズム変更不要です。新 helper のテストで off/on の ID 分離を固定します。

### p3 loop 系 3 driver

- `orchestrator/campaign/p3_s4_loop.py:493-506` — `default_cfg()`

  `s2_verify=False` と `tiered_evaluation=False` の明示引数を追加します。既定は現状の legacy-only。tiered opt-in には S2 も必要とし、CLI では両方を明示して新 campaign にします。受理集合比較テストは「S2 on・順序 off」と「S2 on・順序 on」の間で行い、legacy-only と混同しません。

- `orchestrator/campaign/p3_s4_loop.py:590-664` — `run_one_iteration()`

  呼び出し形自体は `cfg` を `run_campaign()` に渡すだけで足ります。返却 outcome は従来の certified/aborted のままで、新しい screen/deferred outcome は増やしません。

- `orchestrator/campaign/p3_s4_loop.py:761-812` — `main()`

  `--tiered-evaluation` を追加し、既定 off を維持します。on 時は `verify=legacy+s2` と evaluation-order の両キーが ID に入ることを起動ログへ表示します。

- `orchestrator/campaign/p3_s4_loop_sort.py:165-185,200-242,338-393`

  `default_cfg(..., tiered_evaluation=False)` と CLI opt-in を追加します。既存 `verify=legacy+s2` は不変で、on 時に evaluation-order キーだけを追加します。

- `orchestrator/campaign/p3_s4_loop_trigger_gating.py:324-343,355-397,501-566`

  sort と同じ配線にします。既存 axis/provenance 契約には触れません。

### critic と consumer

- `orchestrator/critic/digest.py:192-217,446-452`

  tiered campaign の COMMIT を緑 LI に載せるときは共通 AND helper も確認します。S2-red 前に記録された BENCH_DONE は COMMIT がないため、従来どおり探索射影に入りません。

- `orchestrator/campaign/p3_s4_loop.py:232-249` — `make_critic_digest()`

  推奨案は `SCREEN_REJECTION_REASON` を一切生成しないため、`load_screen_rejections()` は配線しません。D58 の正常棄却を T142 の失敗分類へ混ぜないことをコメントとテストで固定します。

  案 A を選ぶ場合だけ、ここへ `screen_rejections=load_screen_rejections(layout)` を渡す必要があります。既存 `ScreenRejection` は identity+reason だけなので数値漏洩は防げますが、案 A 自体が受理集合条件を満たしません。

- `orchestrator/campaign/p3_s4_loop.py:558-587` — `_resolve_duplicate()`

  tiered campaign の既存 COMMIT を success と復元する際は、COMMIT 存在だけでなく共通 AND helper を使います。sort/trigger は同一関数オブジェクトを共有しているため、1 箇所の修正で3 driverを覆います。

### docs

- `docs/decisions.md:869` D36

  `records_by_stage()` が AND helper ではない現状と、新設 helper の責務を追補します。S2 構成・閾値は変更しません。

- `docs/decisions.md:2268` D58

  履歴を書き換えず、T142 は「LLM loop への D58 floor terminal 棄却拡大」ではなく、受理集合不変な検査順序 short-circuit のみを採用した、と状態追補します。

- `output/insights/` 新規 T-142 設計記録

  集合式、D58 直接再利用の反例、期待削減量の限界、既存 WAL 実測 111 秒を記録します。

- `docs/phase3.md` 該当チェックと `docs/worklog.md` 末尾

  実装・テスト結果を親作業で反映します。

## 4. テストプラン

### 既存テストの意図的更新

- `orchestrator/tests/test_screening_opt_in.py:19-22`

  `test_autonomous_loop_has_no_screening_wiring` は削除せず、例えば次へ置換します。

  ```text
  test_autonomous_loop_evaluation_tiering_is_default_off_and_explicit_opt_in
  ```

  3 driver について以下を assert します。

  - 既定 cfg に `evaluation_order` キーがない。
  - opt-in cfg にだけ `legacy-bench-s2-v1` がある。
  - off/on の campaign ID が異なる。
  - D58 の `"screening"` キーは p3 cfg に入らない。
  - sort/trigger の S2 は on/off 双方で維持される。
  - base driver の比較は S2 on の対照同士で行う。

  同ファイルの偵察3 driver用 D58 CLI テスト `:31-114` は変更せず、D58 の適用範囲が残る番人にします。

- `orchestrator/tests/test_campaign.py:1905-1960`

  現在の「verify loop が certified assignment より前」という AST テストを、中央 `_commit()` と AND helper を固定する形へ更新します。COMMIT 文を増やす、helper を迂回する、`verify_configs` を legacy のみに縮める変異で赤になる形にします。

- `orchestrator/tests/test_campaign.py:2157-2278`

  既存 S2/numactl/workload-tag テストは通常 off 順序の回帰として残します。tiered mode 用の順序・短絡テストを別名で追加し、既存検査と役割を混ぜません。

### 新設する positive control

1. **受理集合の偽陽性防止**

   ```text
   legacy 緑 + bench 正常 + S2 赤
   ```

   `legacy → bench → S2` の順で実行され、S2 workload-tag 付き ABORT、COMMIT なし、`EvalResult.certified=False` を確認します。

2. **floor 混入の防止**

   ```text
   legacy 緑 + bench 正常だが D58 floor 未満 + S2 緑
   ```

   tiered modeでも COMMITできることを確認します。このテストが、後から floor terminal 棄却を忍び込ませる変異を殺します。

3. **安全な S2 省略**

   ```text
   legacy 緑 + bench 失敗 + 仮想 S2 緑/赤
   ```

   新順序では S2 呼び出し 0、旧順序では S2 後に同じ bench reason で reject、双方 COMMIT なしを確認します。

4. **順序イベント**

   - off: `legacy → s2 → bench`
   - on: `legacy → bench → s2`
   - legacy red: 両方 `legacy` だけ

5. **stale verdict 防止**

   legacy 緑の後に bench が abort した場合、S2 未実行結果の `verdict` が空であり、legacy の `"serializable"` を全構成 verdict として持ち越さないことを確認します。

6. **未認証 bench 値の遮断**

   BENCH_DONE に明示的な sentinel TPS を置き、その後 S2 を赤にします。WAL には sentinel が存在する正対照を先に assert し、`load_workload()`、p3 critic digest、duplicate success 復元のいずれにも現れないことを否定 assert します。

### campaign-id / lock 分離

- `evaluation_order` off はキー省略かつ既存 ID 不変。
- S2 on・order off と、S2 on・order on は別 ID。
- sort/trigger/base の3 driverすべてで確認。
- runtime order on を off の campaign.lock へ混ぜると、build/WAL 追加前に ValueError。
- order on だが lock の `verify` が legacy-only、または runtime extra passes に S2 がない場合も即拒否。
- `screening` と `evaluation_order` の同時指定は即拒否。

### 既存被覆と重複しない純増分

既存テストが既に覆うもの:

- D58 floor 境界・stale baseline・high-abort fallback
- screen rejection の未認証数値遮断
- legacy+S2 両緑/第二パス赤
- S2 numactl/bench_lock/admission
- S2 on/off campaign ID
- `run_campaign()` の S2 extra 配線

T142 で純増するもの:

- `legacy → bench → S2` の opt-in 順序
- bench failureだけでの S2 short-circuit
- 旧順序との受理真理値表の等値
- floor を受理条件へ混ぜない positive control
- 3 autonomous driver の既定 off/明示 on
- tiered campaignの共通 AND consumer
- S2-red 前 BENCH_DONE の p3 critic 非混入

## 5. 受理集合不変の機械的提示

証明は次の4層で構成します。

1. **純粋 helper の真理値表**

   `all_required_passed()` と `L∧S∧B == L∧B∧S` を全組合せで検査します。性能 floor は入力に存在させません。

2. **pipeline positive controls**

   - S2 赤なら、bench が良くても COMMIT 不能。
   - bench が正常なら、遅くても S2を省略しない。
   - bench 失敗で省略した S2 は、旧順序の最終 reject を変えない。

3. **中央 COMMIT helper + AST 番人**

   すべての COMMIT 書き込みを1関数へ集約し、必須タグと通過タグの一致を唯一の certified 決定点にします。構文検査で迂回 COMMITを禁止します。

4. **WAL consumer helper**

   tiered campaignでは、COMMIT レコードがあるだけでは certified と扱わず、campaign.lock の必要 verify タグと `verify_configs` を共通 helper で照合します。`records_by_stage()` の最後勝ちを AND 証明には使いません。

補助保証として、search_config/campaign.lock 分離と、COMMITのない BENCH_DONE を critic が読まない否定 assertを組み合わせます。

## 6. リスクと未決点

- **「良い候補」の意味:** 相対性能 floor を意味するなら推奨案では要件を満たしません。現行コードには「遅い候補は certified の対象外」という受理規則がなく、全 COMMIT が critic の緑集合と whiteboard success に入ります。floor を使うには別裁定が必要です。
- **期待効果:** 推奨案が新たに省く S2 は bench 失敗候補だけです。正常だが遅い候補が多数なら、約111秒は依然として毎 iteration 発生します。約8倍という見積もりをこの案へ流用してはいけません。
- **D58との関係:** T142 の採用裁定は D58 の「別裁定」条件を満たしても、「受理集合不変」の制限付きです。D58 自身が screening は生存集合を縮めると明記しているため、適用先拡大の許可だけで floor terminal 棄却まで自動許可されたとは読めません。
- **critic 信号:** bench failureとS2 redを同時に持つ候補では、新順序はS2構造化 redを観測しません。legacy redは毎 iteration維持されますが、規律3に対するS2診断機会の減少をT142裁定の範囲とみなすか、docsで明示する必要があります。
- **D58 baseline 鮮度:** 推奨案では baselineを使わないため問題を回避できます。floor案を採る場合、30分閾値に対して p3 loop は複数プロセス・長時間継続であり、現行 `prepare_screening_campaign()` の一回限りの in-memory `ScreeningConfig` では足りません。基準点の再測、最新 committed baseline の復元、再アンカー provenanceが別途必要です。
- **base driver の verify 差:** `p3_s4_loop` は現在 legacy-onlyです。tiering導入とS2追加を同じ差分に隠さず、`S2 on/order off` 対照を作って二軸を分離する必要があります。
- **bench 順序による実測差:** 論理式は等値でも、S2前後で熱状態・経時ドリフトが変わり、bench成功/失敗やfitness値が実機上同一とは限りません。campaign ID分離は必須です。新規重計測は本waveでは行わず、数値同一を主張しないのが安全です。
- **D36 helper の現物ギャップ:** briefの「既存共通 AND helper」をそのまま根拠にしてはいけません。現物の `records_by_stage()` は最後勝ちです。新 helper を実装対象に含めない場合、機械的提示は producer側AST保証に限定されると明記すべきです。
- **将来の floor-defer:** nonterminal deferを採るなら、D25の再開冪等性、duplicate処理、最終promotion責務、actual certified集合とpotential集合の定義を先に裁定する必要があります。

静的検査のみを実施し、pytest・ファイル編集・状態変更は行っていません。親実装時の受入は関連 pytest、`tools/run_tests.py`、`tools/check_codex_agents.py`、`tools/check_docs.py` と、commit後の provenance監査です。