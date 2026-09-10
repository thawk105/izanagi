## 所見

[A-1] 主張: `run_trial` 前置だけでは campaign launch の支配性が成立しない。  
根拠: `p3_s4_loop_trigger_gating.py:640-648` は直接 `loop.run_campaign` を呼び、CLI も `:896-976` で `drive_iteration` を直接起動する。`loop.py:123-180` に予約検査はない。  
成果物影響: 予約期限切れや別 job の測定が WAL へ入り、C12 の受理集合と certified 選択へ混入し得る。  
最小是正: 共通 launch 点で admission を強制するか、直接 driver を正式に禁止し、その経路テストを追加する。  
自信度: high

[A-2] 主張: `reject_started_trial` は定義予定だが、実行経路と機械評価へ接続されていない。  
根拠: 計画は `trial_registry.py` の関数追加だけを示す (`s2-plan.md:32-37`)。C04 evaluator は `mark_experiment_indeterminate` と `forbid_trial_restart` だけを要求する (`s8c_preregistration_evidence.py:1601-1624`)。契約は preflight から reject への到達も要求する (`s8c_preregistration_evidence_contract.v1.json:168-183`)。  
成果物影響: restart 拒否を実際に通らなくても C04 の判定が進み、台帳上の受理可能集合が誤って広がる。  
最小是正: `run_trial` の start 前に必ず呼び、evaluator と negative test で呼出し・順序を要求する。  
自信度: high

[A-3] 主張: `forbid_trial_restart` 先行順は failure-atomic ではない。  
根拠: 計画は forbid 後に terminal 記録を行う (`s2-plan.md:53-58`)。forbid 失敗時は記録されず、逆順では記録失敗時に拒否が残らない。現行 terminal 処理も append 失敗を別例外へ変換する (`p3_autonomous_workload_trial.py:3212-3241`, `trial_registry.py:1928-2014`)。  
成果物影響: indeterminate 行、restart 拒否、元 crash の三者が不整合となり、レポートと台帳の状態値が食い違う。  
最小是正: 両操作を独立して試行し、両方の失敗を集約して元例外を再送出する。各失敗注入を検査する。  
自信度: high

[A-4] 主張: `remaining_cells` の計算主体と永続的な記録先が計画にない。  
根拠: 現在の cell 集合は `_finish_trial` 内の局所変数である (`p3_autonomous_workload_trial.py:2435-2473`)。crash handler はそこへ接続されず (`:3524-3641`)、lifecycle schema にも該当キーがない (`trial_registry.py:81-88,1976-1986`)。契約はこの値を必須としている (`s8c_preregistration_evidence_contract.v1.json:158-164`)。  
成果物影響: indeterminate 行が残存 cell を区別できず、部分実行のレポート・受理集合・監査参照が不正確になる。  
最小是正: cell 選択と terminal 化を durable progress として記録し、crash 時に `selected - terminalized` を計算して台帳または束縛済み sidecar に保存する。  
自信度: high

[A-5] 主張: `_finish_trial` の `Exception -> partial` 維持は C04 の全体 indeterminate 要件を骨抜きにする。  
根拠: 任意の `Exception` を捕捉して partial cell を生成する (`p3_autonomous_workload_trial.py:2473-2506,2601-2619`)。既存テストも `RuntimeError -> partial` を固定している (`orchestrator/tests/test_p3_autonomous_workload_trial.py:4473-4505,6124-6173`)。契約は caught production crash 全体を indeterminate と要求する (`s8c_preregistration_evidence_contract.v1.json:183`)。  
成果物影響: 通常の production crash が partial として report hash 付きで台帳化され、失敗 cell を含む候補が certified 選択へ残る。  
最小是正: partial を明示的な回復可能エラーに限定し、予期しない `Exception` は C04 helper へ送る。`run_origin_trial` の partial 変換 (`p3_autonomous_workload_trial.py:3667-3715`) も整合させる。  
自信度: high

[A-6] 主張: 予約検査が一度だけで、実際の launch 時点の期限を保証しない。  
根拠: 計画は preflight で `safety_margin_s=0` の検査結果を保持する (`s2-plan.md:39-51`)。実 launch は後段の `p3_autonomous_workload_trial.py:3153-3168` から trigger、loop へ進む。再検査 API は既にある (`reservation.py:74-117`)。  
成果物影響: preflight では有効だった binding が launch 前に期限切れとなっても測定が実行され、予約済み certified 集合へ入る。  
最小是正: 各 campaign launch 直前に残り workload と余裕を再計算し、再検査結果を記録する。  
自信度: high

[A-7] 主張: C12 の reservation 事実を report と lifecycle に結び付ける永続証拠が不足している。  
根拠: 計画の sealed admission はメモリ上の受け渡しに留まる (`s2-plan.md:39-51`)。現行 report/start/terminal の項目に job、boot、deadline の束縛はない (`p3_autonomous_workload_trial.py:2637-2708,3494-3523`, `trial_registry.py:81-88`)。  
成果物影響: certified 選択がどの予約事実に基づくか再検証できず、台帳の監査参照が欠落する。  
最小是正: canonical reservation receipt を report または sidecar に保存し、その hash を start/terminal へ束縛する。  
自信度: medium

なお、`ReservationError` は `ValueError` (`reservation.py:17-19`) なので、計画どおり `run_trial` の outer `try` 開始 (`p3_autonomous_workload_trial.py:3444`) と lifecycle start より前に置けば、既存の `except BaseException` には捕捉されない。この順序をテストで固定しなければ安全性は保証できない。

条件付き読込については、現在の site は `site_policy.current_site` の hostname と NQSV 証拠で決まり (`site_policy.py:30-84`)、CLI の env tag 選択ではない。Pegasus compute は `single_process=True` (`env_contract.py:253-268`)、Linux は false (`:292-309`) であり、現状の production CLI に site 選択引数はない。従ってこの経路自体の迂回は確認できないが、直接 driver の bypass は別問題である。

## 親 brief への反証

- **M3（限定付き）**: env/guard の到達性は `p3_s4_loop_trigger_gating.py:320-331` と `loop.py:92-120,168-180` で支持できる。しかし予約 gate は `run_trial` 内だけで、直接 `run_campaign` 経路が残るため「C12 は allocation gate だけが欠落」という一般化は成立しない。
- **M4（部分）**: mark/forbid の production consumer 不在は確認できるが、契約上は `reject_started_trial` も第三の consumer である (`s8c_preregistration_evidence_contract.v1.json:168-183`)。brief の「二つ」は過少である。
- **M6**: brief の三箇所だけではなく、predicate helper tripwire も対象である (`orchestrator/tests/test_s8c_preregistration_predicates.py:196-220`)。計画はこれを補正している。
- **P3（payload 面）**: 既存 lifecycle row は terminal の格納先として存在する (`trial_registry.py:1959-1986`)が、`remaining_cells` を表現できないため C04 全要件の destination にはなっていない。
- **P4**: `run_trial` 内では preflight が launch より前 (`p3_autonomous_workload_trial.py:3296-3443`)だが、全 production launch の支配性ではない。
- **反証できないもの**: M1 は `SATISFIABLE_CONDITION_IDS=frozenset()` (`s8c_preregistration_evidence.py:1806-1818`)、M2/P1 は generation cap と critic runtime test、M5 は凍結 bytes の pin 不在、P2 は `check_reservation` の実装、P5 は現行 site policy の実測で支持される。

## 総括

予約検査を `run_trial` へ置く案は、単一経路内の順序としては妥当だが、全 launch の dominance には届かない。  
C04 は `reject_started_trial` の未接続、`remaining_cells` の未永続化、通常 `Exception` の partial 化で false positive になり得る。  
forbid と terminal 記録は片方の失敗で壊れない failure-atomic 手順が必要である。  
M1/M2/M5/P1/P2/P5 は静的に支持し、M3/M4/M6/P3/P4 は上記の限定で反証した。  
pytest は実行していない。計画はこのまま本番実装へ進めるべきではない。