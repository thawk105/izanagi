# 静的敵対レビュー

必須資料、`git status`、`git diff`、指定 consumer/runbook を read-only で確認した。pytest・build・各 checker は実走しておらず、緑は主張しない。静的検索上、意図的な「引数欠落」テストを除く in-repo Python caller には `admission` が配線されていたが、以下の閉包不全が残る。

## 重大所見

### 1. resume は現在の admission を検査するだけで、過去の測定へ束縛していない

- claim: `run_campaign()` は有効な admission を渡せば、receipt のない旧 WALや異なる admission で作られた terminal variant をそのまま再利用する。構文上は admission 必須でも、意味上の resume gate になっていない。
- evidence: admission 検査後、campaign identity は `cfg` だけから作られ、WAL replay は terminal 状態だけで skip する。[loop.py:55,63–64,88–108,143–156](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/loop.py:55)。実際、旧 S5 WAL は receipt のない `build_start` の後に COMMIT を持つ。[p3-s5 WAL:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d/runs/wal.jsonl:1)、[同:6](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d/runs/wal.jsonl:6)。
- impact: 新 gate 後の実行でも、containment 条件不明の旧測定や別分類の測定を「評価済み」として無検査で採用できる。
- suggested_fix: 新 campaign では admission receipt を campaign lock/identity に束縛し、resume 時に全既存 `build_start` と exact 一致を検査する。receipt 欠落または混在は、明示的な legacy policy がない限り fail-closed にする。

### 2. receipt は保存されるだけで、critic・レポート・qualification validator の判定材料になっていない

- claim: 実装者の「`.get()` なので consumer 変更不要」は parse 互換性しか示さない。receipt は実質 write-only である。
- evidence:
  - critic は `build_start` から `genome`/`src_token` だけを取り、COMMIT の有無だけで workload を採用する。[digest.py:192–218,222–254](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/critic/digest.py:192)。
  - Layer 3 は WAL payload を raw event 内へ保持するため receipt 自体は消えないが、variant の一級フィールドは `genome/src_token/events` のみで、schema も event を任意 object としている。[layer3_report.py:81–101,192–205](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/layer3_report.py:81)、[layer3_schema.json:11](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/layer3_schema.json:11)。completeness は fresh report との byte 比較だけなので、双方に receipt がなければ通る。[autonomous_trial_completeness.py:990–999](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/autonomous_trial_completeness.py:990)。
  - qualification event sink は payload 全体を保存する一方、validator は `decoded_payloads[0]` の `build_start` を検査せず `decoded_payloads[1]` から始める。[artifacts.py:868–905](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/qualification/artifacts.py:868)。
  - S6/S8 report は COMMIT の存在だけで `certified=True` とする。[s6_sort_sweep.py:396–419](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s6_sort_sweep.py:396)、[s8a_trigger_sweep.py:443–466](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s8a_trigger_sweep.py:443)。
- impact: 後から性能値を見ても、それが stock、machine sweep、human-reviewed、明示 opt-in coder のどの containment 条件で得られたか機械判別できない。
- suggested_fix: shared receipt parser を1か所に置き、critic・Layer 3・sweep reportへ `build_admission_status` を射影する。qualification は `STOCK_OR_PINNED/false` を exact 検証し、新規 artifact の欠落・不正 receipt を拒否する。

### 3. 既存 coder-derived artifact は未分類のまま、現在も選択材料になる

- claim: 旧 artifact は新 gate により再分類されず、正しさ上の COMMIT と T-316 admission 済みという別概念が混同されたままである。
- evidence: S4、S5、S8a の旧 `build_start` に receipt がない。[S4 WAL:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl:1)、[S5 WAL:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d/runs/wal.jsonl:1)、[S8a WAL:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/runs/wal.jsonl:1)。さらに known-axes freeze generator は既存 S6/S8 campaign ID を固定し、sort は COMMIT 行だけで候補化し、trigger は provenance の一致だけを読む。[s1_known_axes_freeze.py:45–59,336–358,471–528](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s1_known_axes_freeze.py:45)。
- impact: proof chain は「verifier-certified」までは示せても、「T-316 containment 下で admission された測定」とは証明できないまま、材料・選択に流入する。
- suggested_fix: frozen bytes は書き換えず、campaign/variant/WAL hash を鍵にした overlay 台帳で `legacy-unclassified` と明示する。新 admission を要求する選択では既定除外し、利用するなら exact artifact の人間 grandfather 裁定または再実走を要求する。

### 4. 3本の現行 runbook の実 build 手順はすべて即時失敗する

- claim: 記載コマンドには新しい opt-in がなく、`BuildAdmission` の生成時点で `BuildAdmissionError` になる。
- evidence: 手順はそれぞれ flag なしである。[S4 runbook:86–96](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/docs/phase3-s4b-runbook.md:86)、[S5 runbook:136–151](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/docs/phase3-s5-sort-runbook.md:136)、[S8a runbook:78–92](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/docs/phase3-s8a-trigger-runbook.md:78)。各 driver は flag 既定値 `False` で `CODER_DERIVED` を構築する。[p3_s4_loop.py:801–817](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop.py:801)、[p3_s4_loop_sort.py:364–392](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop_sort.py:364)、[p3_s4_loop_trigger_gating.py:557–591](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop_trigger_gating.py:557)。
- impact: runbook に従う通常運用が build・検疫・checkpoint より前で停止する。
- suggested_fix: 親が3本の実 build コマンドへ `--allow-coder-derived-build` を追加し、この opt-in が当該 CLI invocation 限定であることを明記する。`--no-build` と `--preview-diff` 手順には不要。

## 中程度の所見

### 5. T-126 の明示的 code identity 集合から新しい load-bearing module が漏れている

- claim: admission を執行する `build_admission.py` が T-126 の `REQUIRED_CODE_IDENTITY_PATHS` にない。
- evidence: `t126_driver` と `pipeline` は新 module を import・実行する。[t126_driver.py:27–31,542](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/qualification/t126_driver.py:27)、[pipeline.py:35–36,472](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/pipeline.py:35)。しかし exact 集合には `pipeline.py` と `t126_driver.py` だけが入り、新 module はない。[contract.py:38–65](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/qualification/contract.py:38)。tracking test もこの集合を列挙するだけなので欠落を検出しない。[test_t126_pegasus_tools.py:1286–1307](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_t126_pegasus_tools.py:1286)。
- impact: series の明示的な load-bearing code closure が admission 執行コードを列挙せず、監査者へ不完全な閉包を提示する。
- suggested_fix: `orchestrator/campaign/build_admission.py` を `REQUIRED_CODE_IDENTITY_PATHS` に追加し、import された admission module の存在を独立 assertion で固定する。なお全 tree/commit 自体は series ID と full archive に束縛されているため、未検出 byte drift ではなく「明示閉包の欠落」である。[t126_driver.py:392–405](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/qualification/t126_driver.py:392)、[t126_qualification.sh:442–445](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/tools/pegasus/t126_qualification.sh:442)。

### 6. 既存 public-entry test から zero-flag 経路が消え、置換テストがない

- claim: `p3_s4_red`/`p3_kickoff` の既存 `main()` test は opt-in 付き呼出しに変更され、既定 CLI の拒否を検査しなくなった。現在の negative CLI test は S6/S8 sweep だけである。
- evidence: public-entry test は `module.main(["--allow-coder-derived-build"])` に変更されている。[test_p3_exploration_namespace.py:197–234](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_p3_exploration_namespace.py:197)。追加された既定拒否 test の対象は `s6_sort_sweep` と `s8a_trigger_sweep` のみ。[test_campaign.py:1531–1549](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_campaign.py:1531)。AST gate も `admission` keyword の存在しか見ない。[test_p3_exploration_namespace.py:269–271](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_p3_exploration_namespace.py:269)。
- impact: runbook を壊した5つの coder driver の既定 CLI 回帰と、誤った provenance class 配線が赤にならない。
- suggested_fix: admitted namespace test は維持しつつ、coder driver 群を parameterize した「flag なしは build spy 前で拒否」「flag ありは exact `CODER_DERIVED/true`」testを別途追加し、resume の receipt 欠落・不一致も negative test 化する。

静的 diff では、新規 `xfail`/skip、現行 hash の期待値追加、揮発診断 payload の焼き込みは見つからなかった。receipt の二フィールド期待値は安定した契約である。ただし実走していないため、これをテスト緑の根拠にはしない。

### 7. `diff_quarantine.py` の訂正文は依然として実態を過大・過小表現する

- claim: 「coder-derived source を拒否」は実 provenance の検出を行うように読めるが、実装は caller が自己申告した enum と bool の型しか検査しない。また「auditor は advisory」は、sort/trigger で non-pass が build を機械停止する事実を落としている。
- evidence: 当該記述は [diff_quarantine.py:16–23](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/diff_quarantine.py:16)。実 admission 検査は source bytes を一切受け取らない。[build_admission.py:22–35](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/build_admission.py:22)。一方 auditor digest 不一致・non-pass は pre-build で停止/reject する。[p3_s4_loop_sort.py:151–160](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop_sort.py:151)。
- impact: 読者が自己申告 admission を provenance 検出器と誤認する一方、auditor の運用上の blocking 性を見落とす。
- suggested_fix: 「`CODER_DERIVED` と分類された build request を拒否」と限定し、「auditor verdict は機械的 pre-build gate だが、意味保証・security credit 上は advisory」と書き分ける。併せて「silo-backoff 単一マーカー」は「1 invocation につき caller 指定の単一 marker」へ直す。

## 凍結・pin 面の静的判定

`FROZEN_MANIFEST` の23対象と検査本体は変更されておらず、差分は対象 artifact bytesにも触れていない。[test_frozen_artifacts.py:38–85,125–153](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_frozen_artifacts.py:38)。4種の role review pin、`manifest.json`、`.codex/role-adapters/*.json` にも差分はないため、これらに直接由来する赤要因は静的には見つからない。[review_ledger.py:15–127,148–239](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/codex_roles/review_ledger.py:15)。

`tools/check_docs.py` の予算対象にも変更はない。[check_docs.py:163–190](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/tools/check_docs.py:163)。ただし checker 自体は実走していない。また、既存 artifact の地位を直すため frozen JSON を直接編集すれば `FROZEN_MANIFEST` が赤になるので、overlay/migration で扱うべきである。

## 総括

- must-fix: resume 時に historical receipt を current admission と照合し、receipt を critic・Layer 3・sweep・qualification の一級検証対象にする。T-126 の明示 code identity 集合にも `build_admission.py` を追加する。
- 親が docs 側で直すべき食い違い: S4/S5/S8a の3 runbook の実 build コマンドへ `--allow-coder-derived-build` を追加する。preview/no-build 手順は変更不要。
- 既存 artifact: verifier-certified という歴史的地位は残るが、T-316 admission 状態は `legacy-unclassified` である。frozen bytes は触らず、exact artifact overlay により新しい admission-aware 選択から既定除外または明示 grandfather する。