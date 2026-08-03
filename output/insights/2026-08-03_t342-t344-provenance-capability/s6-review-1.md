静的読解のみ実施しました。`git diff HEAD` は空、pytest・build・実走は未実施で、緑・赤は主張しません。所見は Critical 2件、High 5件、Medium 1件です。

§1-A の capability 導出本体、legacy/v2 cache validator、S8b official core gate、T126 series identity/control pin については独立所見を起こしていません。§3 の禁止拡張も差分上は確認していません。

### 1. Critical — overlay は配置換えで完全に迂回できる

- claim: 台帳対象の `campaign.lock` と WAL を同一 bytes のまま、台帳の basename と repo-relative path の双方が異なる directory に配置すると、どの overlay 拒否分岐にも該当しない。
- evidence: 既知判定は ID または path だけです（[artifact_admission.py:314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/artifact_admission.py:314)）。一致しなければ、同一 lock/WAL SHA や件数を台帳と照合せず、policy key 欠落を歴史成果物として返します（[artifact_admission.py:350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/artifact_admission.py:350)）。その status は `admitted=True` です（[artifact_admission.py:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/artifact_admission.py:81)）。
- impact: §1-C の「3 campaign を consumer から除外」は file placement にしか効かず、裁定対象 bytes 自体には効いていない。
- 成果物変化: 旧 receiptless COMMIT が再び certified 集合・Layer 3 の variant/source reference・critic 材料へ入る。
- suggested_fix: ID/path に加え、lock SHA・WAL SHA・件数の不変 tuple でも既知 membership を検索する。同一 bytes の移設は overlay-denied、tuple の部分一致は mutation として拒否する。

### 2. Critical — 「新 schema 以後」は artifact 自身の申告で決まり、receipt 欠落が fail-open する

- claim: unlisted campaign の lock から `search_config.build_admission` を省く構文クラスは、実際の生成時期に関係なく pre-policy と判定される。新成果物が receipt を持たない場合ほど historical 扱いになる循環定義です。
- evidence: 境界は key の有無だけです（[artifact_admission.py:353](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/artifact_admission.py:353)）。独立した schema epoch、作成 commit、歴史 artifact index の照合なしに `historical-not-reclassified` を返し（[artifact_admission.py:355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/artifact_admission.py:355)）、`require_admitted_campaign` が通します（[artifact_admission.py:433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/artifact_admission.py:433)）。
- impact: 「新 schema 以後は positive receipt 必須」と「歴史成果物は一括拒否しない」の間に、生成時期を証明できない全面受理領域がある。
- 成果物変化: 新規 receiptless artifact が Layer 3・critic・prefix replay に入り、certified 受理集合と材料レポート参照を任意に増やせる。
- suggested_fix: historicity を信頼可能な pre-policy commit/index/hashで証明する。証明できない missing-key artifact は selection には渡さず、必要なら別の readable-only historical view に落とす。

### 3. High — receipt の genome/src-token と WAL variant が束縛されていない

- claim: BUILD_START の receipt、genome、src-token を内部整合させつつ、全 attempt record に別の一貫した variant 名を与える構文クラスが通る。
- evidence: topology は supplied `record.variant` で grouping するだけです（[wal.py:611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/wal.py:611)、[wal.py:649](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/wal.py:649)）。artifact validator は genome SHA、src-token、commit を見る一方、variant を再導出しません（[artifact_admission.py:382](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/artifact_admission.py:382)）。正本の導出式は [pipeline.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/pipeline.py:61) にあります。新規正例 fixture 自体も genome と無関係な placeholder variant を使っています（[test_artifact_admission.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_artifact_admission.py:61)）。
- impact: receipt が証明する source と、consumer が identity key として採用する variant を別物にできる。
- 成果物変化: Layer 3 の `variants[]`・source refs、critic の grouping、replay の certified key が、同じ receipt/source のまま別 ID へ変わる。
- suggested_fix: BUILD_START の canonical genome を parse し、共有 `variant_id(genome, src_token)` を再計算する。attempt の全 record に同じ再導出値を要求する。

### 4. Medium — `AdmittedCampaign` は immutable ではなく、検証後に内容を変えられる

- claim: `require_admitted_campaign` 発行後、内部 `WalRecord` の stage/payload を変更してから同じ view を loader に渡す呼び出し順では、再検証が一切発火しない。
- evidence: view は frozen ですが、保持するのは `tuple[Any, ...]` です（[artifact_admission.py:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/artifact_admission.py:109)）。要素の `WalRecord` と payload dict は mutable です（[model.py:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/model.py:89)）。critic 側は exact type だけ確認して同じ objects を返します（[digest.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/critic/digest.py:194)）。
- impact: validated-view barrier は浅い型タグに留まり、発行時に検証した records と消費時の records の同一性を保証しない。
- 成果物変化: COMMIT 集合や fitness/rejection 値を view 発行後に変え、critic digest・certified 選択値を WAL bytes と異なるものにできる。
- suggested_fix: record と payload を再帰的に immutable な専用 DTO に射影する。修正までは “Immutable validated raw-WAL view” という docstring を撤回する。

### 5. High — critic の主要 caller は validated view を受け渡しておらず、reflux-on 経路が dead

- claim: `make_critic_digest(layout, reflux=True)` は最初の green loader 内だけで view を発行して捨て、その後の全 red loader に生の layout を渡す。validator 経由の consumer 統合になっていない。
- evidence: `build_digest` の変換はローカル変数だけです（[digest.py:456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/critic/digest.py:456)）。続く呼び出しは全て raw layout です（[p3_s4_loop.py:258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/p3_s4_loop.py:258)）。loader は exact view 以外を `TypeError` にします（[digest.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/critic/digest.py:194)）。main、sort、red driver にも直接 raw 呼び出しが残っています（[p3_s4_loop.py:904](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/p3_s4_loop.py:904)、[p3_s4_loop_sort.py:481](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/p3_s4_loop_sort.py:481)、[p3_s4_red.py:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/p3_s4_red.py:169)）。
- impact: guard は存在するが、通常の reflux-on/red-material 経路はその API に追随していない。
- 成果物変化: red critic digest が生成されず、保存済み iteration に対応する rejection 参照が欠け、試行台帳と次 iteration の critic 入力が乖離する。
- suggested_fix: `make_critic_digest` 入口で view を一度発行し、green/red 全 loader に同じ view を渡す。main/sort/red の直接呼び出しも同様に置換する。

### 6. High — campaign identity API の必須引数移行が主要 producer に届いていない

- claim: S6/S8a の通常 run は policy を cfg に bind した後、必須 keyword を省いた形で `ensure_campaign_identity` を呼ぶため、validator 本体へ入れない。
- evidence: `admission_policy` は default のない keyword-only 引数です（[ident.py:199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/ident.py:199)）。S6 と S8a は省略しています（[s6_sort_sweep.py:275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/s6_sort_sweep.py:275)、[s8a_trigger_sweep.py:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/s8a_trigger_sweep.py:323)）。guided trial も policy を cfg に持たず（[guided.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/guided.py:88)）、start/resume 双方が旧署名です（[guided.py:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/guided.py:162)、[guided.py:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/guided.py:186)）。
- impact: identity validator が恒真なのではなく、呼び出し時の引数束縛で通常経路そのものが停止する。
- 成果物変化: 新しい S6/S8a WAL・certified rows・selection report が作られず、guided の試行台帳も開始／再開できない。
- suggested_fix: S6/S8a は `build_context.policy` を明示渡しする。guided は安定 policy を cfg に bind したうえで、start/resume に同じ policy を渡す。全 call-site の署名監査を追加する。

### 7. High — autonomous trial は no-build と build の双方で capability 配線が成立しない

- claim: `do_build=False` は context を落としてから campaign ID を導出するため policy 必須分岐で停止する。`do_build=True` の非-STOCK coder proposal は、generator ID だけの contextで coder authorityも generator/review receiptも渡さないため admission 導出で停止する。
- evidence: no-build では `_campaign_for` に `None` を渡し（[p3_autonomous_workload_trial.py:1238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/p3_autonomous_workload_trial.py:1238)）、直後に ID を導出します（[p3_autonomous_workload_trial.py:1249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/p3_autonomous_workload_trial.py:1249)）。ID は policy key を必須とします（[ident.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/ident.py:132)）。build context は authority 無しで生成され（[p3_autonomous_workload_trial.py:1569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/p3_autonomous_workload_trial.py:1569)）、drive には context しか渡しません（[p3_autonomous_workload_trial.py:1441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/p3_autonomous_workload_trial.py:1441)）。receipt/authority が無い非-STOCK source は [build_admission.py:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/build_admission.py:462) から拒否へ落ちます。
- impact: U4 が報告した「no-build exact decision」と「build cell の positive chain」は、通常引数のままでは意図した候補評価に到達しない。
- 成果物変化: no-build は canonical cell/台帳を生成できず、build は非-STOCK候補の certified 集合が空になり、trial ledger の harness outcome が pre-build admission rejection に変わる。
- suggested_fix: no-build にも identity 用の共有 policy contextを持たせる。build は parser-issued coder authorityを明示要求するか、実際の生成機構に対応した source-bound generator/review receiptを発行する。generator IDだけで権限化してはならない。

### 8. High — S8a の列挙空間を決める派生 artifact は、保存した build receipt を一度も検証しない

- claim: characterization producer は `build_admissions` を保存するが、`load_effective_reasons` は field の存在・canonicality・source/policy一致を全く確認しない。receipt を欠く characterization artifactも同じ受理分岐に入る。
- evidence: producer は receipt list を作り buildへ渡します（[s8a_trigger_freq.py:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/s8a_trigger_freq.py:129)）。consumer の検査は effective reasons・保存則・既知 reason だけです（[s8a_trigger_sweep.py:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/s8a_trigger_sweep.py:131)）。正例 fixture も receipt field を持ちません（[test_s8a_trigger_sweep.py:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_s8a_trigger_sweep.py:423)）。U3 報告自身が consumer の positive validation 必要性を明記しています（[u3-report.md:106](/work/1/SFC/tanab/dev-wave-jobs/70fa1240/wave-t342-344/u3-report.md:106)）。
- impact: S8a の候補空間を決める根拠は、registered generator receipt を保存しただけで consumer admission にはなっていない。
- 成果物変化: receiptless/mismatched characterization の `effective_reasons` が候補数・候補名・最終 certified 選択集合を変更する。
- suggested_fix: consumer で全 receipt の exact schema/policy/source/genome/commit を検証し、artifact fields と束縛する。また “Closed registry” は単一化する。現在は canonical registry（[materializer_admission.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/materializer_admission.py:20)）と、S8a を逆分類する別 registry（[s8b_materialization.py:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/s8b_materialization.py:43)）が併存し、AST closure test は後者だけを参照しています（[test_s8b_floor_campaign.py:1217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_s8b_floor_campaign.py:1217)）。

## 総括

最も危険な残存迂回路は、overlay 対象 bytes の配置換えと、policy key 欠落による自己申告 historical 化です。両者とも receiptless COMMIT を admission-aware consumer へ戻します。

撤回すべき主張は「overlay fall-through を禁止した」「post-policy artifact だけに positive receipt を要求できている」「一度だけ発行される immutable validated view」「autonomous no-build/build producer を配線済み」の4点です。