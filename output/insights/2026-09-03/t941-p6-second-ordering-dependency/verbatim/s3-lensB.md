## 判定

NO-GO

単位 1 は production の発火 artifact・producer がなく、帰納段と admission 結線もないため P6 の受理集合を変えない。単位 2 は P6 を `NOT_IMPLEMENTED` のまま V-12 を繋ぐため [T-942] の禁止した中間状態そのものであり、さらに Layer3 の live caller・completeness・trial registry への capability 結線が scope から落ちている。現プランのまま実装しても、fixture 上の FC07 厳格化は得られるが、P6 実装または V-12 の end-to-end 結線とは認められない。

## 所見 B1

- 所見 ID: B1
- 重大度: BLOCKER
- 対象: [brief.md:13](/work/1/SFC/tanab/dev-wave-jobs/t941-p6/brief.md:13)、[s2-plan.md:32](/work/1/SFC/tanab/dev-wave-jobs/t941-p6/artifacts/t941-p6/s2-plan.md:32)、[p3_autonomous_workload_trial.py:5016](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/p3_autonomous_workload_trial.py:5016)
- 何が問題か: `evaluate_formal_origin()` への関数内 caller はあるが、評価可能な production 経路はない。`run_origin_trial()` は `OriginBindingRequest` と完成済み `OriginProducerInputs` を外部 caller に要求し、repo 内の非 test caller は 0 件。CLI は origin 入力を渡さない ([p3_autonomous_workload_trial.py:5201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/p3_autonomous_workload_trial.py:5201))。production runtime 初期化は禁止されたまま ([reflux_origin_ledger.py:2914](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/reflux_origin_ledger.py:2914))、authority は `origins: []`、result-evidence artifact は 0 件である。入力を組み立てる実例は fixture test だけ ([test_p3_autonomous_workload_trial.py:10612](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/tests/test_p3_autonomous_workload_trial.py:10612))。DW-G04 の production 発火 gate を満たさない。
- **成果物影響**: certified 選択、材料レポート、試行台帳、production 受理集合の値・参照は変わらず、新 evaluator は fixture でしか評価されない。
- 直し方の提案: production provisioning・result-evidence producer・公開 caller と、発火する origin/artifact ID を scope に入れる。できなければ単位 1 を「fixture-calibrated witness evaluator の準備」に改名して land を延期する。

## 所見 B2

- 所見 ID: B2
- 重大度: BLOCKER
- 対象: [p6-design.md:71](/work/1/SFC/tanab/dev-wave-jobs/t941-p6/materials/p6-design.md:71)、[brief.md:29](/work/1/SFC/tanab/dev-wave-jobs/t941-p6/brief.md:29)、[s2-plan.md:186](/work/1/SFC/tanab/dev-wave-jobs/t941-p6/artifacts/t941-p6/s2-plan.md:186)
- 何が問題か: §2 の中心定理は本 wave の P6 成果にそのまま当てはまる。帰納段、`derive_p6_cut`、非空 `marginal_keys`、install、SC-12 admission がすべて scope 外なので、未実測候補を禁止できない。単位 1 は formal-consumer 入力を厳格化し得るが、P6 の候補受理集合には効果ゼロである。さらに `P6Unavailable` と FC07 のどちらも client は同じ `OriginSealed(aborted=True, constraint_class_sha256s=())` に写す ([reflux_origin_client.py:247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/reflux_origin_client.py:247))。よって (P1) は否定される。
- **成果物影響**: 仮に origin が発火しても試行台帳の terminal/counter と candidate admission は同じで、変わるのは projection の reason と receipt/evidence ref の有無だけである。
- 直し方の提案: P6 と名乗る最小 scope は、4 adapter の正例、事前登録仮説、4 値 `derive_p6_cut`、非空 marginal set、atomic install、次 admission の A/B 対まで通る一つの production vertical slice。そうしない場合は「formal-consumer witness provenance hardening」と名乗る。

## 所見 B3

- 所見 ID: B3
- 重大度: BLOCKER
- 対象: [s2-plan.md:11](/work/1/SFC/tanab/dev-wave-jobs/t941-p6/artifacts/t941-p6/s2-plan.md:11)、[reflux_formal_consumer.py:722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/reflux_formal_consumer.py:722)、[pipeline.py:1485](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/pipeline.py:1485)
- 何が問題か: 現 fixture は `kind` と root field を持つ合成 record だが、production WAL は `stage` と `payload` を持つ。プランは fixture を production 形状へ変える一方、`_wal_trigger()` は依然 `record["kind"] == "TriggerGateBinding"` と root `trigger_binding` を要求する。実 WAL の trigger binding は `stage="trigger_binding"`、値は payload 内 ([wal.py:1344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/wal.py:1344))。プランの変更面にはこの reader 修正がなく、新 fixture/実 WAL は新 evaluator より前に FC05c で落ちる。
- **成果物影響**: production 形状の入力は新 witness 検査へ到達せず、材料レポート・terminal projection・試行台帳に意図した FC07 差分が現れない。
- 直し方の提案: `_wal_trigger`、terminal stage 判定、payload 読出しをすべて stage-qualified record に統一し、public origin path の production-shaped end-to-end caseを追加する。fixture のみでは DW-G04 の証拠には数えない。

## 所見 B4

- 所見 ID: B4
- 重大度: BLOCKER
- 対象: [rulings-verbatim.md:11](/work/1/SFC/tanab/dev-wave-jobs/t941-p6/materials/rulings-verbatim.md:11)、[brief.md:27](/work/1/SFC/tanab/dev-wave-jobs/t941-p6/brief.md:27)、[s2-plan.md:122](/work/1/SFC/tanab/dev-wave-jobs/t941-p6/artifacts/t941-p6/s2-plan.md:122)
- 何が問題か: [T-942] は「P6 不在のまま繋ぐと完全性を主張できない中間状態を読む結線になる」ため V-12 を P6 実装 wave と同梱した。本 wave は明示的に P6 を `NOT_IMPLEMENTED` のまま残すので、独立 reader/verifier に隔離してもこの懸念は解消しない。[T-326] (b) との技術的両立は支持できるが、それは [T-942] の時間順序制約を上書きしない。
- **成果物影響**: Layer3 は P6 完全性のない ledger/evidence を正式参照として表示し、proof chain が「検証済み P6 材料」を含むように見える一方、candidate admission と認定結果は存在しない。
- 直し方の提案: V-12 は accredited end-to-end P6 まで延期する。先行するなら「非完全・診断専用 projection を P6 不在でも許すか」をユーザー裁定へ返し、既存 V-12 完了とは名乗らない。

## 所見 B5

- 所見 ID: B5
- 重大度: BLOCKER
- 対象: [s2-plan.md:122](/work/1/SFC/tanab/dev-wave-jobs/t941-p6/artifacts/t941-p6/s2-plan.md:122)、[p3_autonomous_workload_trial.py:2827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/p3_autonomous_workload_trial.py:2827)、[autonomous_trial_completeness.py:4652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/autonomous_trial_completeness.py:4652)
- 何が問題か: V-12 の live consumer chain が scope から落ちている。p3 は `layer3_report.render()` に capability/client を渡さない。completeness の fresh rebuild も `build_report()` を無引数で呼び、cross-binding は `source_refs` を WAL/whiteboard だけから再計算する ([autonomous_trial_completeness.py:4524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/autonomous_trial_completeness.py:4524))。trial registry はこの campaign-chain/completeness を必須実行する。加えて formal consumer が読む `OriginProducerInputs.evidence_root` は caller 選択で campaign root に束縛されていない ([p3_autonomous_workload_trial.py:429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/p3_autonomous_workload_trial.py:429)) のに、V-12 reader は `campaign_dir/reports/...` を読むため、別 evidence 集合を表示し得る。
- **成果物影響**: evidence-present trial は Layer3 作成または fresh rebuild/trial-registry acceptance で落ちるか、scan path が違えば reflux 区画が黙って欠落し、「結線済み」の材料レポートを生成できない。
- 直し方の提案: p3 から exact issued capability/client/evidence root を forwardし、root を campaign identity に束縛する。同じ変更単位で completeness の fresh rebuild、cross-binding `source_refs`、trial-registry 再検証を更新する。

## 所見 B6

- 所見 ID: B6
- 重大度: MAJOR
- 対象: [brief.md:25](/work/1/SFC/tanab/dev-wave-jobs/t941-p6/brief.md:25)、[s2-plan.md:171](/work/1/SFC/tanab/dev-wave-jobs/t941-p6/artifacts/t941-p6/s2-plan.md:171)、[reflux_result_evidence.py:629](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/reflux_result_evidence.py:629)
- 何が問題か: D96 表の最初の 7 群は production artifact ではなく、fixture/synthetic accepted-input mutations である。production-shaped WAL は B3 の先行 gate で落ちるため、「他の検査はすべて緑」という反実仮想も成立していない。また brief の「`verify_done` に attempt ID がない実測」は現行 producerでは偽で、現在は明示的に ID を書く ([pipeline.py:1485](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/pipeline.py:1485))。resolver 緩和は missing-ID projection を新たに受け入れる拡張なのに、D96 節は拒否群だけを列挙している。
- **成果物影響**: production 受理集合の純減は証明されず、低層 API では missing-ID projection の受理集合が逆に広がる一方、列挙された拒否群の現行成果物差分はゼロである。
- 直し方の提案: production 形状の全 gate 通過 A/B artifact を固定し、各行について対象 gate だけを外した反実仮想を示す。resolver 緩和による新規受理群も D96 に明記する。

## 所見 B7

- 所見 ID: B7
- 重大度: MAJOR
- 対象: [s2-plan.md:259](/work/1/SFC/tanab/dev-wave-jobs/t941-p6/artifacts/t941-p6/s2-plan.md:259)、[s2-plan.md:275](/work/1/SFC/tanab/dev-wave-jobs/t941-p6/artifacts/t941-p6/s2-plan.md:275)
- 何が問題か: 1,300〜1,800 行見積りは、記載された新規 4 ファイルだけで 450+500+280+350=1,580 行に達し、既存 12 面前後の変更余地を約220行しか残さない。B3/B5 の必須 consumer 修正も未算入である。さらに P6 と名乗れる vertical slice は帰納・handler・install・全入口 admission・4 adapter・consumer 非干渉まで必要で、テスト込み数千行規模になる。
- **成果物影響**: 見積りを前提に一 wave へ押し込むと、production callerまたはcompletenessを落とした部分実装が land し、P6/V-12 の成果物値は変わらない。
- 直し方の提案: 現プランだけでも約2,000〜3,000行へ再見積りする。P6 vertical slice は概算4,000〜8,000行級として別 wave 群にし、V-12 は裁定後に consumer chain 単位で分ける。

## 所見 B8

- 所見 ID: B8
- 重大度: MINOR
- 対象: [brief.md:15](/work/1/SFC/tanab/dev-wave-jobs/t941-p6/brief.md:15)、[brief.md:16](/work/1/SFC/tanab/dev-wave-jobs/t941-p6/brief.md:16)、[brief.md:45](/work/1/SFC/tanab/dev-wave-jobs/t941-p6/brief.md:45)
- 何が問題か: permutation detail の構造化、`sample` 5 件上限、`FROZEN_MANIFEST` 23 key に layer3/reflux が無いことは現物と一致した。ただしそれらは「P6 origin に束縛された production 発火」を示さない。編集面走査も時点限定で、現在の worktree 数は62、今回の未commit対象面走査は該当0件であり、「40 worktreeで無重複」を author 段まで一般化できない。
- **成果物影響**: raw schema 実在を発火証拠に数えると fixture-only adapter を production 結線済みと誤認し、編集面の陳腐化は統合時の欠落・衝突を見逃す。
- 直し方の提案: raw field 実在と origin-bound firing artifact を別表にする。worktree scan は時刻・HEAD・コマンドを記録し、author 開始直前に再実行する。

## 総括

- BLOCKER: 5件
- MAJOR: 2件

親 brief の前提判定:

- (P1): **支持しない。** §2 の中心定理が適用され、candidate admission は不変。production 発火 artifact もないため、FC07 の仮想差分だけでは DW-G04/G05 を満たさない。
- (P2): **[T-326] についてだけ支持。** 深い照合を新 verifier に隔離し Layer3 を shallow projection にする読みは裁定 (b) と両立する。ただし P6 不在の V-12 を禁じた [T-942] と、欠落した consumer chain は別の BLOCKER である。
- (P3): **raw 実測は支持、実装効果への一般化は支持しない。** permutation structure と sample cap は実在する。lock/write の fail-closed は仮想的な channel 回避を塞ぐが、D156 が要求する各 adapter の `P6Derived` 正例も production 発火も作らない。
- (P4): **支持しない。** 記載済み新規ファイルだけで1,580行あり、必須 consumer 層を含めると現見積りを超える。

本 wave が正直に名乗ってよい成果は、**「P6 の前処理候補となる witness 正規化器を設計し、fixture 上の reflux formal-consumer 自己申告検査を fail-closed に厳格化する準備」**である。

名乗ってはいけないのは、**「P6 の機械実装を進めた」「production 受理集合を狭めた」「V-12 を結線した」**である。

裁定パッケージ候補:

- [T-942] を維持して V-12 を full P6 後へ延期するか、P6 不在の「診断専用・非完全 projection」を新たに許すか。推奨は延期。
- [T-326] (b) が新 verifier の shallow call を許すことの確認。推奨は許可。ただし p3/completeness/trial_registry を同一変更単位に含める。
- lock/write の構造化正例が揃うまで SC-02 実装を保留するか。推奨は保留し、counter→一律 error を P6 実装と数えない。
- permutation witness の同値関係と thread-hint 除外を確定するか。未裁定なら permutation も known-unavailable に倒す。
- P6 validation を実装する wave では、`critic/digest.py` の validation-event 分離、Layer3 集計、completeness、trial registry、p3 producer を一つの consumer-closure として所有するか。

検査は指定どおり静的読解のみで、pytest は実走しておらず、緑は主張しない。