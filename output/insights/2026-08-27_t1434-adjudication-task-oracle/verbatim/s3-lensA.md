静的検査のみ実施した。pytest は実走しておらず、Web も使用していない。

### A1 — 親 brief の join 前提は成立しない

- 一次資料: `context/s1-brief.md:12-17`、`tools/codex_reasoning_ab.py:9322-9341,9366-9371,9419-9426`、`s2-plan.md:13-25`
- 主張: 親 brief の「`_load_adjudication` の検査時点で packet ごとの task が同定済み」は誤り。union 検査は `mapping` の辞書化と `slot_by_run` の構築より前に走り、実際の run-to-slot join は `:9419` で初めて成立する。段 2 プランの post-join 第 2 検査はこの誤りを正しく補正している。
- **成果物影響:** brief の位置へそのまま per-task 引数を足す実装では task が得られず、union fallback または検査不能となり、cross-task ID を含む材料レポートの `valid` 受理集合が狭まらない。
- 修正案: brief を「revealed bytes は読了済みだが task join は未成立」に直し、段 2 の二段検査を唯一の実装方針にする。

### A2 — 「真部分集合」は一般には偽

- 一次資料: `context/s1-brief.md:47-50,70-75`、`s2-plan.md:78-83,159-162`、`tools/codex_reasoning_ab.py:229-270,3017-3042`
- 主張: task 別集合は union の部分集合だが、常に真部分集合ではない。組込み POS/NEG は同じ `_LEGACY_KNOWN_FINDINGS` を持つため等しく、外部 manifest でも 1 task、全 task 同一集合、または対象 task が union 全体を持つ場合は等しい。brief とプランは後段でこの反例を認識しながら、前段では「真部分集合」と断定している。
- **成果物影響:** 組込み manifest などでは certified `valid` の受理集合もレポート値も一切変わらないのに、成果物説明だけが「必ず狭まった」と誤記される。
- 修正案: 全箇所を「部分集合であり、task 間に finding 差がある場合だけ真部分集合」に統一する。

### A3 — join 失敗時の fail-closed は段 2 プランで保存される

- 一次資料: `s2-plan.md:23-36`、`tools/codex_reasoning_ab.py:9424-9426,10243-10252,10452-10464,10509-10512`
- 主張: プランは slot または dimensions が得られないと reason を追加して `joined` へ入れない。公開経路では reason が 1 件でも `valid=false`、`experiment_complete=false` となるため、task 不明時に union 受理へ戻る certified 経路は見つからない。
- **成果物影響:** join 不能入力は品質台帳、decision、reader agreement が null となり、受理集合は元へ戻らない。
- 修正案: 実装時に「reason 追加前の `continue`」を作らないことを負例で固定する。

### A4 — `_validate_verdict_row` の呼び出し全数と blind 境界

- 一次資料: `tools/codex_reasoning_ab.py:9327-9329,11560-11564,11577-11585,11635-11637,11742-11744`、`orchestrator/tests/test_codex_reasoning_ab.py:6906-6910`、`s2-plan.md:23-36,48`
- 主張: production の call expression は 5 箇所で、内訳は `_load_adjudication` 1、`append_verdicts` 2、`freeze_verdicts` 1、`reveal_mapping` 1。加えて直接 unit test が 1 箇所ある。段 2 は関数 signature と union 動作を全 5 箇所で維持し、per-task 化を post-reveal の `_load_adjudication` 内の別検査だけへ限定している。
- **成果物影響:** blind verdict 追記、freeze、reveal 前検査の受理集合は manifest union のままで、task identity が reader 側へ漏れない。
- 修正案: なし。この分離は成立している。

### A5 — D931 の production digest 連鎖は緩めていない

- 一次資料: `context/D931.md:3-19`、`s2-plan.md:102-116`、`tools/codex_reasoning_ab.py:9266-9273,10749-10763,11487-11492`、`orchestrator/tests/test_codex_reasoning_ab.py:12945-12963,13042-13111`
- 主張: プランは同じ external manifest を packet、verdict、freeze、reveal へ渡し、全 digest を `d` に揃える。production では material manifest、schedule、adjudication artifacts、各 verdict row が exact digest を要求し、検査緩和案はない。
- **成果物影響:** manifest を途中交換すると certified entrypoint は `valid=false` となり、別 manifest の受理集合や positive/negative 分類は採用されない。
- 修正案: 新 fixture が `_load_adjudication` を直接呼ぶ場合、material manifest 自身の exact 検査はその関数では発火しない点だけ明記する。既存 entrypoint 負例 `:12945-12963` がこの辺を被覆している。

### A6 — D767 の `unbound` は保存される

- 一次資料: `context/D767.md:3-17`、`s2-plan.md:67-72,181-185`、`tools/codex_reasoning_ab.py:5497-5527,6241-6249`
- 主張: プランは stage5 の `task_acceptance_status`、`fix_gate_eligible`、`routing_evidence_eligible` に触れない。新しい `oracle_kind` は control 分類であり、semantic acceptance を表す値ではない。
- **成果物影響:** stage5 receipt は引き続き exact `unbound`、false、false で、fix gate や routing evidence の受理集合は広がらない。
- 修正案: なし。

### A7 — 「bytes pin 台帳・trust root は存在しない」は偽

- 一次資料: `context/s1-brief.md:56-59`、`output/insights/2026-08-09_t181-certified-rerun/apparatus-pin.json:3-5`、同 `README.md:47-53,148-157`、同 `erratum-f176.md:9-14,70-81,91`
- 主張: 現行 bytes の exact SHA-256 を参照する consumer は静的検索で 0 件だったため、今回の更新閉包が 0 という結論自体は支持できる。しかし「bytes で pin する台帳・trust root は存在しない」は明白に偽で、T-181 の歴史的 `apparatus-pin.json` が旧装置 SHA を認証の trust root として固定している。
- **成果物影響:** この pin を現行 bytes に追随更新すると、過去の `aggregate.json` / `verify.json` がどの装置で certified だったかという参照が改変される。更新しなければ今回の受理集合は変わらない。
- 修正案: 「現行 bytes を pin する live consumer は 0 件。旧 T-181 の歴史 pin は存在し、更新対象外」と書き分ける。

### A8 — 「run 未開始なので §13 の変更禁止は未発火」は成立する

- 一次資料: `docs/phase3-t189-model-routing-preregistration.md:819-829,930-938,971-972`、`docs/decisions.md:26673-26680`
- 主張: 文書は power simulation を実施しない裁定により lock が完了不能で、実走自体が成立しないと明記する。したがって「run 開始後」の変更禁止は本 wave にはまだ発火していない。
- **成果物影響:** 本 wave の事前変更によって既開始 run の oracle 参照が後付けで変わることはない。
- 修正案: なし。

### A9 — 親 brief の成果物影響は実コードと一致しない

- 一次資料: `context/s1-brief.md:87-94`、`tools/codex_reasoning_ab.py:10164-10174,10175-10204,10452-10464`
- 主張: brief は cross-task `equivalent_to` により finding coverage の分子が増えて quality が良く見えるとするが、primary の `k` は `r1_detected` だけから増える。finding の `equivalent_to` は coverage 分子に使われず、negative task の real、高 severity、must-fix finding なら false-finding count を増やして結果を悪化させる。プランの負例のように一方の reader だけが finding を出す場合は conservative intersection から消え、現状の統計値は変わらない。
- **成果物影響:** 新ゲートが実際に変える主要値は、不正 raw row がある材料レポートの `valid` を false にし、品質台帳と `decision` を null にすること。brief が主張する coverage 分子の増加ではない。
- 修正案: DW-G05 を「仕様外 ID が raw verdict で受理される。negative で両 reader に残れば false-finding/exclusion を汚染し、一方だけなら統計には出ないが `valid=true` のままになる」へ修正する。

### A10 — aggregate の「独立照合」は live 経路では冗長

- 一次資料: `s2-plan.md:37-46,50-65`、`tools/codex_reasoning_ab.py:11166-11174,11250-11256`
- 主張: live 経路では `_load_adjudication` が schedule-derived dimensions から `oracle_kind` を verdict に入れ、その verdict を直後に `_aggregate_verified` へ渡す。aggregate も同じ slots と task manifest から再導出するため、exact 比較は独立した情報源の照合ではなく、同じ authority の再計算である。実効的な束縛は `oracle_kind` を `combined_verdict_sha256` の計算前に入れる点にある。
- **成果物影響:** loader 生成 verdict に対する certified 受理集合は hash 束縛で狭まるが、aggregate 比較を「第 2 の独立ゲート」と数えると保証の参照数だけが過大になる。値そのものへの追加効果はないため、この所見は nit。
- 修正案: 「独立照合」ではなく「in-memory handoff の冗長 invariant」と記述し、stale combined hash を loader が拒否する負例を主証拠にする。

### A11 — 「外部 v3 manifest でしかテストできない」は踏み込みすぎ

- 一次資料: `context/s1-brief.md:70-75`、`s2-plan.md:100-116`、`orchestrator/tests/test_codex_reasoning_ab.py:6089-6107,6870-6910`
- 主張: 必要なのは task ごとに異なる集合を持つ manifest であり、外部ファイルという transport は論理上必須ではない。既存 test は in-memory の `_synthetic_task_manifest` を内部 API に渡し、異なる union をすでに作っている。CLI と D931 の連鎖まで証明する場合に外部ロードが必要、という限定なら正しい。
- **成果物影響:** production の受理集合は変わらず、テスト fixture の構築範囲だけを不要に限定するため nit。
- 修正案: 「内部 predicate の単体検査は synthetic dict でも可能。CLI/digest 連鎖を同時に証明する fixture は外部 v3 file を使う」と限定する。

## 総括

must-fix は **A1、A2、A7、A9**。

実装方向そのものは、既存 union 検査を残した上で post-join の task 別検査を AND し、join 不能を reason 化するため、certified な受理集合を広げない。最大の問題は、親 brief の join 前提、真部分集合の断定、pin inventory、成果物影響の説明が実コードと食い違っている点である。pytest は実走していないため、テストの緑は主張しない。