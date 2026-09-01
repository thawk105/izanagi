## 所見

所見 1: reason 全体と scope 文字列の literal 固定は要求外で、稼働中の T-733 と具体的に衝突する  
重大度: must-fix  
何が証明されていないか / どこで壊れるか: この強化は E0 局所拒否や WAL 非読取を追加で証明しない。既存 node はすでに projection の全 field を exact 比較している。一方、T-733 の稼働 worktree は scope を 24 path から 62 path へ変更しており、正しい S-1 実装でも旧文字列 literal により本 node が落ちる。  
実物の根拠: [plan.md:68](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2124-s1-epoch-historical/artifacts/dev-wave-t2124-s1-epoch-historical/plan.md:68)、[test_s1_report.py:538](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:538)、[現行 artifact_admission.py:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/artifact_admission.py:72)、[T-733 artifact_admission.py:72](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/campaign/artifact_admission.py:72)。同じ変更は [t733-author:72](/work/1/SFC/tanab/izanagi/.codex/worktrees/t733-author/orchestrator/campaign/artifact_admission.py:72) にもある。  
親 brief / プランのどちらの誤りか: 主にプランの scope 逸脱。親 brief も T-733 の文字列変更を把握しながら、test literal の意味的衝突を編集面非重複として見落としている。

所見 2: 「既存 30 件の S-1 出力が 1 byte も変わらない」は成果物主張として成立していない  
重大度: must-fix  
何が証明されていないか / どこで壊れるか: 30 は全 campaign directory 数であり、S-1 report が読む role は4つである。また通常の再生成では `generated_at_head` が新しい HEAD になるため、実装差分が無関係でも JSON と Markdown の bytes は変わる。producer を走らせないため tracked artifact が変更されない、という作業範囲の事実と、再生成結果が byte-identical という成果物影響を混同している。  
実物の根拠: [brief.md:54](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2124-s1-epoch-historical/brief.md:54)、[s1_report.py:59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_report.py:59)、[s1_report.py:942](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_report.py:942)、[s1_report.py:1018](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_report.py:1018)、[report.json:4912](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/output/reports/s1_direct_comparison/report.json:4912)。  
親 brief / プランのどちらの誤りか: 親 brief の誤りで、プランも [plan.md:153](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2124-s1-epoch-historical/artifacts/dev-wave-t2124-s1-epoch-historical/plan.md:153) で引き継いでいる。

所見 3: 焦点走の参照閉包から構造 inventory test が漏れている  
重大度: must-fix  
何が証明されていないか / どこで壊れるか: `test_s1_report.py` だけでは、変更対象 file が既存の process-site inventory と整合することを確認しない。`test_ccbench_spawn_sites.py` は `s1_report.py` を明示的な allowlist entryとして持ち、campaign 全 Python file を AST parse する直接 consumer である。  
実物の根拠: [test_ccbench_spawn_sites.py:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_ccbench_spawn_sites.py:147)、[test_ccbench_spawn_sites.py:324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_ccbench_spawn_sites.py:324)、[test_ccbench_spawn_sites.py:1927](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_ccbench_spawn_sites.py:1927)。  
親 brief / プランのどちらの誤りか: プランの焦点走選定漏れ。親 brief にもこの consumer 閉包は記載されていない。

## 変異 5 件の帰属判定 (1 件ずつ、殺せる / 殺せない / 帰属不成立)

1. E0 の局所 `raise` を削除する — 殺せる。schema-less fixture は v1 として decode され、recorded E0 を得る。`HISTORICAL_RAW` は E0 をそのまま返すため WAL 読取まで進み、拒否 reason と `len(read_roots) == 3` の両方が崩れる。[campaign_lock.py:334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/campaign_lock.py:334)、[artifact_admission.py:909](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/artifact_admission.py:909)、[test_s1_report.py:512](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:512)。

2. purpose を `CERTIFIED_ACCEPTANCE` に戻す — 殺せる。helper は HEAD commit の実 blob digest を記録し、検証側も同じ commit blob を照合するため `_verify_committed_loader_binding` を通る。その後 patched `capture_contract_loader_binding` が失敗し、正例は assert 前の S-1 callee 呼出しで拒否される。[campaign_lock_test_support.py:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/campaign_lock_test_support.py:10)、[contract_loader_binding.py:386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/contract_loader_binding.py:386)、[artifact_admission.py:967](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/artifact_admission.py:967)。

3. 中央 gate を削除して `return recorded.diagnostic` にする — 殺せる。透明 spy が呼ばれず `observed_purposes` が空になる。`_validate_read_purpose` も飛ぶが、S-1 wrapper は外部 purpose を受けず exact enum を内部で固定するため、この変異に対して正例以外の malformed-purpose node は不要である。[artifact_admission.py:939](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/artifact_admission.py:939)、[plan.md:118](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2124-s1-epoch-historical/artifacts/dev-wave-t2124-s1-epoch-historical/plan.md:118)。

4. E0 で `CampaignVerifierEpochRejected` 以外を投げる — 殺せる。`_assess_campaign` は当該型だけを rejection envelope にし、それ以外の `ArtifactAdmissionError` は validation failure にする。非 `ArtifactAdmissionError` なら node 自体が例外終了する。[s1_report.py:429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_report.py:429)、[s1_report.py:447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_report.py:447)。

5. `_rejected_epoch_projection` の field を削除または値変更する — 殺せる。ただし新規 reason exact 比較への帰属は不成立である。現行 node の `campaign_verifier_epochs["block1"]` exact dict がすでに同じ変異を殺すため、提案された強化は mutation power を増やしていない。[s1_report.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_report.py:127)、[test_s1_report.py:538](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:538)。

## 正例 4 assert の分類 (存在証明 / 回帰 pin)

プラン本文には4本ではなく5本の assert がある。[plan.md:117](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2124-s1-epoch-historical/artifacts/dev-wave-t2124-s1-epoch-historical/plan.md:117)

- `observed_purposes == [HISTORICAL_RAW]`: 回帰 pin。中央 gate の呼出しと引数を固定するが、単独では可用性 seam が呼ばれないことを証明しない。

- `capture_call_count == 1`: 存在証明。前提確認の1回以外に gate から呼ばれなかったことを示す。これと S-1 callee が正常復帰した事実が「可用性 gate が外れた」の実証部分である。

- `epoch.state == "E1"`: 回帰 pin。実 v2 recorded path を通ったことの確認であり、可用性 gate 不在の証明ではない。

- `epoch.reason_code == "recorded-closure"`: 回帰 pin。

- `epoch.campaign_verifier_epoch.startswith("E1:")`: 回帰 pin。`CampaignVerifierEpoch` constructor 自身も E1 prefix を検証しており、特に冗長である。[artifact_admission.py:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/artifact_admission.py:186)。

## scope 逸脱の判定

既存負例を実 callee 経由へ変える部分は D1387 の必要範囲である。reason envelope 全体と scope 文字列を literal 固定する部分は追加防壁であり scope 外である。現行 exact projection と部分 reason、WAL 非読取だけで局所 E0 拒否は証明できる。

「30件 byte 不変」のための新しい product test も scope 外である。静的 censusでは全30 lock が v1であり、新たな受理対象がないことは確認できるが、これは byte identity ではない。通常再生成は HEAD fieldを変えるため、主張自体を成果物 bytes ではなく「保存済み v1 lock の拒否挙動は不変」と狭める必要がある。

`s1_direct_comparison.py` に epoch 判断はない。非 dry-run の producer 再開は `_ensure_campaign` から live binding 検証を通すが、これは現在の certified producer admission であり、歴史 report reader の purpose と矛盾しない。[s1_direct_comparison.py:493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_direct_comparison.py:493)、[ident.py:388](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/ident.py:388)。dry-run は ledger の schedule prefix だけを読むため、別形の epoch 判断でもない。[s1_direct_comparison.py:1015](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_direct_comparison.py:1015)。

## 焦点走に含めるべき test file

- [test_s1_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:16): production module の直接 importと全意味テスト。

- [test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_ccbench_spawn_sites.py:147): `s1_report.py` を明示参照する再帰 AST inventory。

[test_s1_9pair_figure_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_9pair_figure_provenance.py:31) は frozen report artifact を読むだけで `s1_report.py` を import・再生成しないため、この production 差分の焦点走には含めない。

## 未確認事項

pytest、build、producer、mutation の実走はしていない。緑とは報告しない。v2 helper の到達性と各変異の失敗点は静的に追跡した。T-733 の稼働判定は検査時点の locked worktree metadata に基づく。file は編集していない。

## 総括

最も重い破れは、要求外の scope 文字列 literal 固定が稼働中の T-733 と確実に衝突する点である。  
正例は恒真ではなく、v2 helper は committed-binding 検査を通り、purpose 復帰変異を殺せる。  
一方「30件の S-1 出力が byte 不変」は、対象数と `generated_at_head` の両面で成立しない。  
焦点走には直接意味テストに加え、`s1_report.py` を明示参照する process inventory test が必要である。