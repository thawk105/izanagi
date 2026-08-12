NO-GO

## 総括

現行 brief / plan のまま解除 decision を land してはならない。

`a09`/`a12` の正例が実在せず、否定テストだけでは「正しい gate」と「常時拒否」を区別できない。さらに、D308 の同一 land 執行、直接 qsub の保証境界、retry/crash の状態遷移、report consumer の閉包が未検査である。

## 所見 (real/refuted・成果物影響つき)

- **real — 恒真な束縛検査。** brief は `a12` 実装・成果物 0 件、plan は通る正例が現在構成不能と認めている。[s2-plan.md:143](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2-s4/s2-plan.md:143>) の全負例は、gate が最初に常時拒否しても通る。これは「検査済み」ではなく「受理集合が空」である。  
  成果物影響: 直近は pilot を止めるが、valid pilot の受理・台帳・report 生成を一切検証できない。

- **refuted（狭い主張）／real（設計全体）— HEAD 権威の混入。** 現行 [report.py:114](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/publication/report.py:114>) は `git show HEAD:docs/decisions.md` を使うため、worktree・spool fragment・handoff の変更だけで現 report が解除する経路はない。  
  ただし予定 gate は `repository_root` を caller から受け、環境には `PATH` を残す。shadow `git`、別 clone、HEAD 移動の競合、HEAD の decision と dirty worktree の実装の不一致が未閉鎖である。decision bytes だけ HEAD 由来でも、実行される driver bytes は worktree 由来になり得る。  
  成果物影響: 偽の canonical release が受理されれば、未束縛の 288 run が投入可能になる。

- **real — release marker の誤検出。** D316 は「集合を literal 固定しない」ことを、任意の散文を release と認めることとは定めていない。[report.py:75](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/publication/report.py:75>) の既存 scan は、後続 decision に参照が一度でもあれば保守的に `possible_supersession` とする。T-139 の marker を単なる `D292`、`pilot`、または prose token として動的検索すると、無関係な decision の引用が解除 marker に見える。  
  成果物影響: false positive は投入禁止を解除し、false negative は pilot を止める。

- **real — producer 自己申告。** `a09` の schedule hash、`a12_passed`、verifier result を evidence file や intent の field から読むだけなら、bool/hash の自己申告である。hash を generator と同じ mutable source から再生成しても独立検査ではない。  
  成果物影響: 未検証 schedule / stress 結果に基づく raw run が作られ、後段 consumer が provenance と誤読する。

- **real — qsub 後 crash と retry の穴。** [qsub_binding.py:68](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/qualification/qsub_binding.py:68>) の `retry_index` 検査は 0/1 の型・値だけで、retry の正当な遷移、失敗理由、同一 intent に対する再投入禁止までは束縛しない。binding 前 crash 後に invocation claim を見ず `retry_index=1` を作れば二重投入になる。  
  また [submission.py:150](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/qualification/submission.py:150>) は単発 `os.write` で read-back も short-write 検査もない。  
  成果物影響: slot の重複・欠落、PBS request の二重化、試行台帳 identity の破損を招く。

- **real（P4(iii) の過大主張）／refuted（狭い B4 境界）— 直接 qsub。** [dispatch_compute.py:1475](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/tools/pegasus/dispatch_compute.py:1475>) は一般 qsub を実行し、qstat と request ID を確認するが、T-139 intent/binding は要求しない。driver preflight を通らず benchmark binary や別 PBS wrapper を直接起動する経路も残る。  
  「raw qsub で起動した公式 T-139 driver が bound intent なしでは benchmark 前に止まる」という B4 の境界は正しい。一方、「投入は `submit_pilot` 経由でしか起こせない」は、構造化ファイルを直接作った caller や別 wrapper を区別できず、機械的には保証できない。`pbs_job_id` も caller 引数で受けるだけでは scheduler identity の証明にならない。  
  成果物影響: 公式 driver 外の raw output が T-139 evidence として混入し得る。

- **real — D308 の同一 land は願望のまま。** plan は「fragment・実装・束縛検査を同一 land」と書くが、予定署名 3 本のどれにも、release decision の fold commit と driver / binding / tests の commit が同一 land であることを検査するものがない。canonical HEAD に release decision があれば、後から dirty / 別 commit の実装で gate を動かせる。  
  成果物影響: 認可だけ先に有効になり、未完成 gate の窓で pilot を投入できる。

- **real（将来）／refuted（現時点）— `report_scope` の additive 追加。** 現在の production consumer が 0 件という brief の測定の範囲では、直ちに report を誤読する consumer は確認されていない。しかし `report_scope` は旧 consumer に強制されず、未知 field を無視する parser は `pilot_submission="forbidden"` だけを読み続ける。逆に新 consumer が `kind` だけを読み、canonical release や `current_submission_authority` を確認しない経路も残る。  
  成果物影響: 旧 consumer は false reject、新 consumer は誤った live authority として false accept し得る。

- **real — wave 前の同型。** 次の形は本 wave の禁止対象と同型であり、変異登録が必要である。

  - [report.py:230](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/publication/report.py:230>) の deny-only `"forbidden"` を live authority として読む形。
  - [qsub_binding.py:55](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/qualification/qsub_binding.py:55>) の T-126 schema literal を T-139 にそのままコピーする形。
  - [submission.py:150](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/qualification/submission.py:150>) の unchecked single write。
  - [dispatch_compute.py:1475](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/tools/pegasus/dispatch_compute.py:1475>) の T-139 binding なし一般 qsub。

  `preregistration` の docstring に `submit_pilot` が現れること自体は実装ではなく、既存の export 禁止テストもあるため、そこが現行 bypass だという主張は **refuted**。  
  成果物影響: 上記形を変異で殺さないと、禁止を文書化しただけで受理集合は変わらない。

過去失敗型の再発検査も real である。

- F15: 実出力を含まない mock 母集団。a09/a12/PBS の実正例なしに positive control を作ると再発する。成果物影響: 常時拒否を正常 gate と誤認する。
- F21: 配線・設定だけを live 発火と誤認。AST qsub 検査だけでは driver / wrapper / binary の実到達を証明しない。成果物影響: bypass が残ったまま緑になる。
- F47/F49: qsub の印字成功または有効 request を authority と誤認。request ID・receipt・scheduler identity の束縛不足と同型。成果物影響: 非永続・非 T-139 の raw output が混入する。
- F60: 期待 node が新設 gate を実際には通らない。先行する常時拒否で binding test が未到達でも緑になる。成果物影響: binding 防壁の未検査が隠れる。
- F69: 値が同じ positive control。schedule generator と hash を同じ source から作ると、generator を無視する変異が生き残る。成果物影響: schedule の独立再導出を謳っても自己整合だけになる。

## 恒真な保証の検査

現状の受理集合では、次の実装がすべて同じ観測結果になる。

1. canonical release が無いので拒否する正しい実装。
2. `a09`/`a12` が無いので拒否する正しい実装。
3. binding を一度も検査せず常に拒否する実装。
4. どの入力も読まず `raise Reject` する実装。

したがって、`missing_a09`、`missing_a12`、duplicate marker、direct qsub の負例は、検査が発火した証拠にならない。これは「恒真な gate が既にコード化されている」と断定する根拠ではないが、「束縛検査を land した」と主張できないことを意味する。

絶対規律 2 の観点では、常時拒否そのものは直ちに fail-open ではない。しかし、それを正しさ防壁として land すると、後続で正例を通すために gate を緩める圧力だけを残す。実正例が構成できるまで、解除 decision としての成果物は未完成である。

## blocker

- **B1 real:** `a12` producer / verifier / 実成果物がない。
- **B2 real:** `a09` の authoritative source と独立再導出 API が未定義。
- **B3 real:** `coarse-provenance-standard` は canonical decision に存在せず、P5 の根拠が自己矛盾する。
- **B4 real（境界修正が必要）:** 公式 driver の preflight 保証は可能だが、「全 qsub を submit_pilot のみに制限する」とは書けない。
- **B5 real:** 実正例がなく、3 本の検査が恒真な拒否と区別不能。
- **B6 real:** release marker の exact grammar、HEAD/code digest、PATH shadow、HEAD race が未閉鎖。
- **B7 real:** release decision と mechanism の同一 land を執行する機械検査がない。
- **B8 real:** crash / retry / partial durable intent の状態機械が T-139 として未確定。
- **B9 real:** additive `report_scope` に consumer-level enforcement がない。

## 変異候補

以下は nodeid 名を維持しても、現状の plan だけでは対応変異を殺せない。

- `test_release_is_read_from_head_not_worktree_or_spool`  
  直接の worktree read は殺せるが、`PATH` による fake `git`、HEAD の TOCTOU、dirty driver bytes の使用は殺せない。正例が無ければ常時拒否も生き残る。

- `test_release_accepts_unrelated_later_decisions_without_literal_id_set`  
  literal ID 集合の固定は検査できるが、marker を別 decision の散文へコピーする変異、または D316 と衝突する「D292 参照を unrelated として accept」する変異は殺せない。

- `test_release_rejects_duplicate_marker_and_later_reference`  
  否定専用なので常時拒否が生き残る。canonical positive fixture と他 gate の充足を分離しない限り、重複検査の発火を証明できない。

- `test_missing_a09_rejects_before_intent_and_qsub` / `test_missing_a12_rejects_before_intent_and_qsub`  
  別の未充足 gate が先に拒否するため、gate 削除・producer bool 穴埋め・qsub 先行の変異を殺せない。

- `test_all_eight_intents_are_durable_before_first_qsub`  
  現在 qsub に到達できないので、qsub を一度も呼ばない実装が通る。一部 intent 後の qsub を検出できない。

- `test_unbound_invocation_is_never_automatically_resubmitted`  
  binding 前 crash の実経路に到達しない。`retry_index=1` の不正な再投入、qsub rc 不確定、既存 invocation claim の再利用も未検査。

- `test_t139_binding_has_exact_keys_schema_and_stdout_job_id`  
  exact key / stdout parser は検査できるが、caller が `qsub_returncode`、`pbs_job_id`、invocation hash を自己生成する変異、構造化 binding の偽造は殺せない。

- `test_all_t139_qsub_sites_are_discovered_and_only_submit_pilot_is_authorized`  
  T-139 production file の glob/AST だけでは、既存の一般 dispatcher、shell の動的 qsub、PBS wrapper からの直接 binary 起動、別 import alias を検出できない。「only submit_pilot」は証明できない。

- `test_direct_qsub_without_bound_intent_stops_before_run`  
  公式 driver に intent が無いケースだけであり、別 wrapper / benchmark binary の直接起動、または偽の intent・binding を作った raw qsub は殺せない。

- `test_bound_positive_executes_36_runs_per_slot_and_288_total`  
  現在の実 repo では正例不能。mock だけなら、実 PBS slot、gate 前の output 作成、実 driver の run order、slot 間重複を殺せない。

- `test_schedule_hash_and_independent_rederivation_are_both_required`  
  generator と比較対象を同じ fixture/source から作ると、両方を同時に変更する変異が生き残る。独立 frozen input が必要。

- `test_collection_is_operational_only_and_preserves_raw_bytes`  
  empty collector や常時 reject が通る。raw bytes を実際に回収する positive path、symlink/path traversal、consumer の authority 昇格は未検査。

- `test_collection_never_emits_receipt_or_certified_entry`  
  collector が何も回収しない実装でも通る。P5 の禁止だけで collection の生存性は証明できない。

- `test_t793_report.py` の historical scope pin  
  report の JSON shape だけを pin し、`report_scope` を無視する consumer、`pilot_submission` を current authority と読む consumer は殺せない。

- 「T-126 回帰の short-write 拒否」  
  nodeid と `_durable_json` 到達が未指定で、既存 qsub binding test だけでは [submission.py:150](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/qualification/submission.py:150>) の single-write mutation を殺せない。

## 未読・未確認

- 必読の brief、plan、D292/D308/D316、`qsub_binding.py` 全体、`submission.py` 143〜195 行、`t126_driver.py` 960〜1120 行、`dispatch_compute.py` の qsub 周辺、`report.py` 全体は読了。
- failures は F15、F21、F47、F49、F60、F69 の本文だけを再発検査した。
- a09 の逐語 generator、a12 の verifier/schema/実成果物、実 PBS 上の allocation 順は未確認。
- pytest、build、qsub、mutation 実走はしていない。緑は確認していない。
- read-only のためファイル変更はない。