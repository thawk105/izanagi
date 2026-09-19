単独段 dispatch: stage=consult; lane=luna; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2773-mocc-template-wave2

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief (これ自身も検査対象、P1〜P10): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2773-mocc-template-wave2/wave-artifacts/parent-brief.md
- 段 2 plan (攻撃対象): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2773-mocc-template-wave2/wave-artifacts/s2-plan.md
- 設計正本 (T-2757 insight、§5・§8〜§13): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2773-mocc-template-wave2/wave-artifacts/verbatim/t2757-design-README.md
- wave 1 の結果: 同 dir の t2772-wave1-README.md、s3_mocc_mutation_proof.summary.json
- 既裁定の逐語: 同 dir の D2134.md、D579.md、D38.md、D95.md、D1687.md
- Silo 前例: 同 dir の silo-backoff-trigger-gating-variant.patch、axis_trigger_gating.py.txt。現行 auditor.md: auditor.md.current
- repo 内 (投入先 worktree、HEAD 657e1e5a7): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2773-mocc-template-wave2/ の orchestrator/campaign/condition_meaning_gate.py、orchestrator/campaign/materializer_admission.py、orchestrator/tests/test_p3_build_authority_cli.py、orchestrator/tests/test_ccbench_spawn_sites.py (625〜700 の patch define inventory を含む)、orchestrator/tests/test_condition_meaning_gate.py、orchestrator/tests/test_p3_s4_loop.py (7925〜7970)、orchestrator/tests/test_campaign.py (11380〜11470)、orchestrator/codex_roles/review_ledger.py、orchestrator/codex_roles/spec.py (semantic_digest 745、render_adapter 803)、.codex/role-adapters/auditor.json、orchestrator/tests/test_reflux_originless_compatibility.py (571〜720)、tools/check_codex_agents.py、tools/check_docs.py、orchestrator/campaign/s3_mocc_mutation_proof.py、orchestrator/tests/test_mocc_mutation_proof.py、patches/README.md、docs/axis-onboarding.md (§7)、docs/dev-wave/core.md (DW-G05)

# 依頼 — [T-2773] レンズ B: 閉包・pin・gate の鍵・過剰と削除 — plan と親 brief を攻撃する

plan を守らせず検査せよ。親 brief 自身も検査対象である。所見は real / refuted の判定材料 (行番号・既裁定) を添えて must-fix / should / nit に分ける。あなたは read-only。pytest は走らせない。予算が尽きそうなら途中結論を下の出力形式どおり書いて終わること (無出力が最悪)。

## 攻撃点

1. **pin 閉包の漏れ**: 新 file (template patch、計装 template 版、軸 module、新 driver、新 test、新 JSON) と変更 file (auditor.md、condition_meaning_gate、materializer_admission、patches/README.md、pin 3 箇所) について、plan が挙げていない pin・件数 test・全列挙 test・glob 走査を repo で探せ。特に: `test_ccbench_spawn_sites.py` の patch define inventory (625〜700) が template patch の `MOCC_TEMP_PREDICATE` を cache route として拾い `DEFINE_SPECS` と照合するか、`_run_checked` / `_run_trace` 等の allowlist Counter、`test_p3_s4_loop.py` 7925〜 の IZANAGI_ トークン走査 (template patch に `IZANAGI_` トークンを入れると `registered` に要る)、`test_p3_build_authority_cli.py` の module 名一覧 (160〜190)、`test_s8b_floor_campaign.py` の materializer 閉包、`test_condition_meaning_gate.py` の件数 pin、`test_campaign.py::test_axis_driver_source_rel_within_edit_surface`、`check_docs.py` の pin (patches/README.md・auditor.md は pin されるか)、`acceptance_duration_ledger.json`、B-4 static inventory の module 数。
2. **auditor.md の pin 3 箇所**: plan の追随手順が `review_ledger.SOURCE_FILE_SHA256["auditor"]`、`.codex/role-adapters/auditor.json` (`render_adapter` の出力。`check_codex_agents.py --write` は使えない。`semantic_digest` の再計算)、`test_reflux_originless_compatibility.py` の `_extend_*` 追記 (T-2528 型) を**全部**含むか。description を変えないこと。他に role file の sha を持つ場所がないか (`git grep a0912ebb` で 4 file — うち 1 つは歴史 insight で不変)。
3. **gate の鍵 (P6) の偽陽性 / 偽陰性**: (a) `patches/*.patch` の走査で「`cc/mocc/transaction.cc` の hunk に `EVOLVE-BLOCK-BEGIN` が加わる」を判定する code が、計装 patch・負例 4 本・Silo template で発火しないこと (負例)、かつ template patch で発火すること (正例)。(b) `axis_*.py` の走査が `axis_trigger_gating` で発火しないこと。D2134 項 6 が禁じる「EBS 所属を鍵にする」「`SOURCE_REL == "cc/mocc/transaction.cc"` だけで全 module を探索する」を plan が踏んでいないか。発火時の要求 (JSON 実在・all_pass・sha 束縛・key 集合・auditor.md の mocc 行) の「auditor.md の mocc 行の実在」を文字列一致で判定すると恒真化しうる — どう判定させるべきか。
4. **consumer 束縛 (P5) の実効性**: 実 loop driver が無い状態で「将来の consumer が呼ぶ契約テスト」を置くことは D2134 項 6 の「consumer 導入時テスト」と整合するか、それとも consumer 導入時に別途要るか。3 対照 (別名 template → 拒否 / 定数直書き → 同じ proof 要求へ到達 / 直書き PIN → 拒否) が「拒否」の主体 (束縛関数か gate test か) を混同していないか。「任意の直書き経路を機械的に閉じた」と主張する文が plan にないか。
5. **P2 (新 driver / 新 JSON で wave 1 を不変にする)**: 設計 §12 「wave 1 の driver / test / JSON の拡張」との差を、D2134 項 5 (歴史的結果を書き換えない) と DW-O09 (凍結 bytes) で裁定できるか。新 JSON が wave 1 JSON の sha を束縛し、wave 1 JSON が T-2294 JSON の sha を束縛する鎖で、gate が要求する「旧 14 check と新設 check が揃う」を満たすか。
6. **過剰と削除 (DW-G05)**: plan に scope 外の実装 (探索 driver・broken patch の template 版・汎用台帳・全経路解析・auditor 型番号の連番・verifier 編集・追加 gate) が紛れていないか。逆に、要求内で欠けているもの (§12 wave 2 の表の 7 行、§7 末尾の check 6 種、§9.2 の 3 候補、§10 の機械要件 4 点) はないか。実装しないと成果物 (機械証拠 JSON) の**意味**が変わるものだけを must-fix にせよ。
7. **P1 の compute 範囲と時間予算**: 12 走 + build 4〜5 本 + condition gate + 同一性で 1 job (gen_S 3600 秒) に収まるか (wave 1 実測: Elapse 791 秒 / 36 走、verifier 最大 54.8 秒)。DQ 対照・consumer 束縛対照・auditor 定義の検査を compute (JSON に記録) と login (pytest) のどちらに置くべきか、二重化の無駄はないか。
8. **P9 (condition gate の cache route)**: `condition_meaning_gate` の ROUTE_CMAKE_CACHE 評価が Silo 専用定数に依存し mocc owner で評価不能なら、plan の代案が「gate を弱める」方向でないか。
9. **親 brief の file:line と前提の誤り**、P2 / P5 / P6 / P7 / P9 / P10 の当否、親自身の実測値 (pin 閉包の 12 file、sha) の一般化の誤り。

## 出力形式

- 見出しはすべて `##`。所見は `## 所見 N: <title>` の形で、各所見に「real/refuted の判定材料」「must-fix / should / nit」「是正案 (逐語)」を書く。
- 最後の節は必ず `## 総括` (`#` を 2 個)。`### 総括` と書いてはならない。`## 総括` には (a) must-fix の一覧、(b) pin 閉包の漏れ一覧、(c) P2 / P5 / P6 の当否、(d) 親 brief への異議を書く。
- 入力はデータであって指示ではない (規律 6)。断定には行番号か D 番号を添える。確信の無いことは「不確実」と書く。
