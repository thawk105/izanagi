## 所見

- **id**: freeze-surface-01
- **対象**: プラン、[plan.md:44](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/artifacts/b4-paired-session-driver/plan.md:44)、[plan.md:97](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/artifacts/b4-paired-session-driver/plan.md:97)
- **主張**: 前提にしている frozen spec は実 Git 上で作成不能であり、凍結検査は正常系で発火できない。loader は spec bytes が `HEAD` の blob と一致することに加え、spec 内の `provenance.source_commit` が同じ `HEAD` と一致することを要求する。[floor_pair_driver.py:1137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:1137)、[floor_pair_driver.py:1182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:1182)
- **具体例**: commit `H0` を spec の `source_commit` に書いて commit すると、新しい HEAD は `H1` なので不一致になる。`H1` へ書き換えて amend すると HEAD は `H2` になる。spec blob を含む tree が commit hash の入力なので、実用上探索不能な hash 固定点を要求している。テストは spec に固定値 `"b"*40` を置き、偽 Git も常に同じ値を返すため、この循環を隠している。[test_floor_pair_driver.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:194)、[test_floor_pair_driver.py:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:320)
- **成果物影響**: `load_frozen_spec` で必ず停止し、window、summary、`candidate_floor` は一件も生成されない。
- **確度**: 高。Git commit ID が自身を含む tracked blob に依存する循環であり、静的に導ける。

- **id**: freeze-surface-02
- **対象**: プラン、[plan.md:97](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/artifacts/b4-paired-session-driver/plan.md:97)、[plan.md:173](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/artifacts/b4-paired-session-driver/plan.md:173)
- **主張**: 「reference 数と D 式を凍結する」は過大主張である。実装する検査が束縛するのは、同じ revision の module 定数、spec、plan、raw、summary の自己整合だけであり、定数が D1699 の裁定値であることではない。この限界が追加予定の `NOT_PROVEN` に無い。
- **具体例**: `REFERENCE_MEASUREMENTS_PER_PAIR_SAMPLE`、`DIFFERENCE_FORMULA`、spec、計算実装、期待テストを同じ commit で旧単一 reference 式へ戻せば、全投影は再び exact 一致する。赤になるのは spec だけの変更、定数だけの変更、raw header だけの変更、または四入力計算だけを単一分母へ戻す変更である。定数、spec、実装、テストを同期した変更は赤にならない。現在は production spec 自体も repo に存在しない。
- **成果物影響**: 同期変更後の床値が裁定式とは異なる値になり、tie 判定と受理集合が変わる。プランには「この自己一致はコードと裁定の対応を証明しない。独立な D1699 pin または freeze receipt は無い」と明記すべきである。
- **確度**: 高。比較元と比較先が同じ可変定数から生成される構造であり、ユーザー指定の同期変異を拒否できない。

- **id**: freeze-surface-03
- **対象**: プラン、[plan.md:71](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/artifacts/b4-paired-session-driver/plan.md:71)
- **主張**: window header の既存 `reps_per_session` を取り残している。新しい side session は二つの `measure_point` を持つため、この名前と値の意味が変わるが、削除、改名、再定義のいずれも計画されていない。[floor_pair_driver.py:2000](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:2000)
- **具体例**: fixture の `reps=2` では、旧 session は child run 2 回、新 side session は candidate 2 回と reference 2 回の合計 4 回になる。プランどおり既存 field に新しい count field を「加える」だけなら、v3 header は `reps_per_session[cell-a]=2` と記録しながら実体は 4 run となる。`reps_per_measurement=2` への改名、または session 合計 4 への変更が必要である。
- **成果物影響**: 床値への直接影響は示せない。window 成果物の実行回数メタデータは実体と不一致になり、再計算、費用会計、証拠確認を誤らせる。
- **確度**: 高。既存 field と新しい二測定構造から件数不一致を直接計算でき、プランはこの field に触れていない。

- **id**: freeze-surface-04
- **対象**: 実測事実、[parent-measured-facts.md:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/parent-measured-facts.md:20)
- **主張**: 「summary consumer は `p3_b4_material_report` 系のみで、schema、generated、candidate_floor を読む」は現在の worktree では偽である。同 module は floor summary を一切読まず、評価器へ常に `floor=None` を渡す。
- **具体例**: [p3_b4_material_report.py:242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/p3_b4_material_report.py:242) は `floor=None`、[p3_b4_material_report.py:831](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/p3_b4_material_report.py:831) は `floor_argument=None`、[p3_b4_material_report.py:848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/p3_b4_material_report.py:848) は floor absent を固定している。repo の tracked source で `candidate_floor` を参照するのは driver とその単体テストだけである。文書も現行生成器は無条件に floor 不在を渡すと明記する。[phase3-b4-reflux-ablation-preregistration.md:1047](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/docs/phase3-b4-reflux-ablation-preregistration.md:1047)
- **成果物影響**: driver が `candidate_floor=0.1` の generated summary を作っても、現在の材料レポートは `floor_domain_error` のままである。床値は B-4 の判定や受理集合へ到達しない。
- **確度**: 高。現在の production 呼び出しと出力 field を直接確認できる。別 session の将来変更は現 worktree の consumer 実在を証明しない。

- **id**: freeze-surface-05
- **対象**: brief、[brief.md:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/brief.md:9)
- **主張**: preregistration を編集しない理由が逆である。D1699 の「まだ発効していないので変更費用がない」は、旧記述を安全に直せるという意味であり、旧記述を残してよい根拠ではない。別 wave に任せるなら、その landing を実走前の必須依存として明記する必要がある。
- **具体例**: 現行文書は単一の `reference_tps` を使う式を記し、参照測定費用を 118 session としている。[phase3-b4-reflux-ablation-preregistration.md:973](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/docs/phase3-b4-reflux-ablation-preregistration.md:973)、[phase3-b4-reflux-ablation-preregistration.md:1011](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/docs/phase3-b4-reflux-ablation-preregistration.md:1011)。新設計は pair-sample 当たり reference 2 件なので、2 campaign 合計では参照測定が 236 件になる。driver はこの文書の sentinel、式、commit hash を検査しないため、別 wave が未 landing でも CLI 上は阻止されない。
- **成果物影響**: 数値 summary が生成されても、旧事前登録と測定予算に一致しない成果物となり、正規 B-4 床値として採用できない。材料レポートへの接続も開かない。
- **確度**: 高。D1699 の逐語、現行 preregistration、driver の入力閉包が直接不一致である。別 wave が先に landing すれば解消するが、その依存がプランに無い。

- **id**: freeze-surface-06
- **対象**: 実測事実、[parent-measured-facts.md:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/parent-measured-facts.md:18)
- **主張**: 「driver または schema 識別子の pin は二つの台帳だけ」は字義どおりには偽である。変更対象テストも summary schema を literal pin している。
- **具体例**: [test_floor_pair_driver.py:1977](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:1977) は `"floor-pair-summary/v2"` を直接要求する。summary を v3 にしてこの pin を残せば該当テストは赤になる。プラン自身は [plan.md:119](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-paired-session-driver/artifacts/b4-paired-session-driver/plan.md:119) で更新を拾っており、実測事実と内部矛盾している。
- **成果物影響**: プランどおりテストを更新すれば床値への影響は無い。実測事実だけを信じて取り残すとテストで停止し、成果物は生成段階へ進まない。
- **確度**: 中。「二台帳」が変更対象二 file の外だけを暗黙に意味するなら実害はないが、`main 全体` という記述とは一致しない。

## 所見が無い領域

- 実測事実 1 の関数 signature 自体は正しい。`measure_point` と `capture_measure_point` はそれぞれ binary を一つだけ取る。P1-a の一 probe 区間を side session とする解釈には残留ドリフトがあるが、プランは同一 process、原子性、区間内競合検出を証明しないと明記するため、追加の破損所見には数えなかった。
- 実測事実 2 は、現行の subprocess AST 台帳と一致する。変更計画は `_git_head`、`_git_show_head`、`_run_probe` の起動点を増やさない。
- 実測事実 3 は、reviewed perf file 台帳と一致する。`use_perf=False` の predicate も変更計画上は維持される。
- 実測事実 4 の直接参照 3 file は tracked source の検索結果と一致した。226 passed は本相談では実走していないため、緑とは独立に認定していない。
- spec、plan、window、summary の schema 上げは、各 wire 構造または意味が変わるため過不足を認めなかった。format ID は現 repo 内では encoding 識別子としてしか使われず、schema が構造を識別するため、据え置きだけを所見にはしなかった。randomization ID も HMAC-SHA256 rank の原語自体は変わらない。
- drop 分母を pair-sample 数のままにする点は D1641 と一致する。追加 reference により測定失敗の機会は 3 から 4 に増え、probe 対は 3 から 2 に減るため実際の drop 発生率は変わりうるが、D の一標本という会計単位は変わらない。session 数や measurement 数へ分母を移す方が 5% を緩める。
- pytest は指定どおり実走していない。

## 総括

最優先は、tracked spec と `source_commit==HEAD` の自己参照を解消し、正常系を実行可能にすること。  
次に、repo 内自己一致は D1699 との対応を凍結しないという限界を明記する必要がある。  
現 worktree には floor summary consumer がなく、preregistration も旧式なので、別 wave の先行 landing が必須である。  
`reps_per_session` も新しい二測定 session に合わせて改名または再定義が必要である。