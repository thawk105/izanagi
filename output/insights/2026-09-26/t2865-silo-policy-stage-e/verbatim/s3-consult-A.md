## 所見

1. **must-fix — 共有 `quarantine()` の引数追加が既存の診断経路を止める。** plan:29 は policy marker に compiler と scratch を必須とする一方、[silo_policy_coverage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/silo_policy_coverage.py:279) の既存 caller は両方を渡さない。brief:17 と plan:23,43 の「C/D の受理集合を変えない」と両立しない。**影響:** C/D の診断候補が検査前に失敗し、台帳の結果と受理集合が変わる。**代案:** この caller に既存の compiler/scratch を明示的に渡して実経路で確認するか、検査結果を受け渡す別の契約にする。二重 compile を残すなら、その両方が実際に走ることを確認する。

2. **must-fix — 自系列の境界が campaign 全体の digest と任意の入力引数で閉じていない。** plan:33,44 は `history_path` と `critic_diagnosis` を受け、plan:15 は既存 driver を型にする。しかし既存の `make_critic_digest` は admitted campaign 全体を読む（[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/p3_s4_loop.py:1185)）。同じ campaign に C++・IR や別系列が入れば、critic 診断から他系列の結果が次の coder に届く。`baseline` と `contract_spec` も plan の関数では不透明なままである。**影響:** 次候補と certified 選択が他系列・偵察情報に条件付けられ、レポートの系列比較の意味が変わる。**代案:** 形・系列ごとに campaign identity と履歴を分離し、履歴・診断はその campaign の WAL/receipt と候補 ID に束縛して生成する。coder 入力の全可変 field について許可元を固定し、実 producer からの入力 bytes を検査する。

3. **must-fix — `prior_critic_reverse` を proposal に置くと、実 critic 由来を機械的に保証できない。** plan:31,35 は top key を許し、plan:35,46 は「親が与える」とするだけである。既存 driver は proposal の値を読み、停止状態へ畳み込む（[p3_s4_loop_sort.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/p3_s4_loop_sort.py:508)、同:602）。反例は coder 側が `true` を記した JSON をそのまま渡す場合。**影響:** reverse 枯渇で系列が早期停止し、候補数と certified 選択が変わる。**代案:** proposal からこの key を外し、driver が自系列の確定 critic receipt から導出する。導出できなければ更新しない。

4. **must-fix — build admission の分類を実経路で固定する検査がない。** plan:53 は `CODER_AUTHORED` を選ぶと述べるが、[build_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/build_admission.py:656) は review receipt、generator receipt を coder authority より先に分類する。plan:63 のテスト案は cfg と CLI opt-in を見るだけで、実 candidate の admission receipt を見ない。**影響:** LLM 由来候補が `HUMAN_REVIEWED` または `MACHINE_GENERATED` と記帳され、受理根拠と参照が誤る。**代案:** driver の評価呼出しで両 receipt を渡さないことを固定し、C++・IR の各実材料化候補について発行された admission class と CLI opt-in 欠落時の拒否を検査する。

5. **should — preview、auditor、書込み、build の byte 束縛を一つの流れとして指定する必要がある。** plan:29 は全 pass 後にのみ書くとするが、型にした sort 経路は `quarantine(write=write)` で先に書く（[p3_s4_loop_sort.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/p3_s4_loop_sort.py:179)）。plan:37 は digest の対象を定めるが、preview と実走で再 render した本文、および build 直前の材料化 bytes の一致条件を定めていない。**影響:** 審査した diff と build した diff が異なれば、certified が未審査の本文を指す。**代案:** 両 CLI が同じ render・検疫関数を使い、auditor gate 後に書き、書いた本文から diff/digest と材料化 hash を再照合してから `pipeline.evaluate` へ進める。IR も render 後の C++ 本文に全 gate を通す。

6. **should — 変異 M-E4 は kill として登録できない。** plan:87–100 は subtype を `HOST_EFFECT` に変える M-E4 の赤を期待するが、候補の拒否自体は残る。これは診断表示の変化であり、[mutation.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/docs/dev-wave/mutation.md:16) の kill 定義では diagnostic sensitivity pin に属する。同:55 は期待失敗 node の完全集合も要求する。**影響:** gate の検出力を過大に記録し、台帳の kill 数が誤る。**代案:** M-E4 を診断 pin に分ける。M-E1〜E3 は前後の gate に遮られない実 caller の fixture で単一理由性を確認し、期待 node を実装後に確定する。

7. **should — auditor の免除は軸と候補由来を明記して限定する。** plan:19 は型17〜21を sort IR と機械生成 IR に限定する方針で正しい。ただし現行の冒頭文は一括免除の形である（[auditor.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/.claude/agents/auditor.md:68)）。LLM×C++ が補助関数を追加する例では型17の監査が必要になる。**影響:** 一括免除を残すと auditor が正当な違反を見落とし、受理集合が広がる。**代案:** 各型とチェックリストの両方に、免除される軸・由来を同じ条件で書き、LLM×C++ の監査を明記する。

## brief と plan の前提の判定

- **P1: 要修正。** 検査位置は妥当だが、既存 caller の引数が不足する（所見1）。
- **P2: 要修正。** 空 whiteboard で収束判定を避けられる点は real。ただし履歴・critic の自系列束縛と reverse の出所が未成立（所見2、3）。
- **P3: real。** 既存 IR 型、`validate_ir`、renderer がある。codec の閉包と render 後の共通 gate を条件とする。
- **P4: 要修正。** planner 不在は D2214 に合うが、proposal 内の reverse 値は除く必要がある。
- **P5: 要修正。** `binary`・`scope` の射影は妥当。任意の履歴・診断・baseline からの流入は key 集合テストだけでは閉じない。
- **P6: real。** legacy＋性能構成と較正済み write-heavy は設計 §3.2 に合う。実走で両 verify が候補ごとに走った receipt を確認する必要がある。
- **P7: 要修正。** 登録簿の追随範囲は概ね妥当。auditor 免除の軸・由来の限定を具体本文とテストに固定する。
- **P8: 要修正。** 非 LLM の二形による配線確認は有効だが、auditor 実 spawn と admission class の証拠を分けて記録する。投入見積りと確認は D2243 項1に従う。

## 再発しうる失敗の型

[failures.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/docs/failures.md:21) の **[恒真ゲート]、[テスト代表性]、[consumer 取り残し]、[変異帰属]、[防壁の射程誤認]、[ドリフト]** が該当する。具体的には F126/F127/F143 型の後段 gate による変異の mask、F255/F1020 型の caller・consumer の取り残し、F914 型の二重 gate の過剰決定が近い。driver、quarantine、pipeline、role、runbook を通る実経路で確認する必要がある。

## scope 外の層 (裁定パッケージ候補)

候補ごとの公平性機械観測、TRACE 計数、sanitizer、非 LLM IR arm と比較 harness は依頼どおり本 wave の scope 外。設計 §3.4 の発火条件を runbook と報告の限定に残し、実装済みの gate として扱わない。特に endpoint・勝ち候補の公平性目視と、verify と perf の分岐一致を主張しない表記は残す。

## 総括

**推奨: adopt_with_conditions。** 実装前の must-fix は、①既存診断 caller の引数契約、②自系列の campaign・履歴・診断の束縛、③reverse 値の確定 critic 由来への変更、④LLM 候補の実 admission class の固定である。これは指定資料と worktree の静的検査による判定であり、build・pytest は実施していない。