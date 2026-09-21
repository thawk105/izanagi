単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-xp-pin-candidate

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief (provisional 裁定 (P1)〜(P6)、段 1 実測、不変条件、条件表): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-xp-pin-candidate/s1-brief.md
- 段 2 plan (codex read-only の起草、全文): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-xp-pin-candidate/codex/s2-plan.md
- 依頼文の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-xp-pin-candidate/verbatim-request.md
- 既裁定の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-xp-pin-candidate/verbatim/ の D16.md, D579.md, D1603.md, D2114.md, D2150.md, D2153.md, carry-T2294-T2295-entry1240.md
- e9e477c を含む tracked file 一覧 (43 行): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-xp-pin-candidate/verbatim/e9e477c-tracked-files.txt
- 親の実測 log (逐語): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-xp-pin-candidate/probe/p1-patch-merge.log, p4-keep-line17.log, p5-proof-surface.log
- 先例 insight (worktree の path): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-xp-pin-candidate/output/insights/2026-09-17/t2756-pin-evidence/README.md (§2〜§4)、
  /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-xp-pin-candidate/output/insights/2026-09-20/t2304-pin-advance/README.md (§0〜§3)、
  /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-xp-pin-candidate/output/insights/2026-09-19/mocc-witlight-arm-run/README.md (§2・§7)
- repo 内コード (read-only、worktree の path): `tools/dev_wave_submodule_init.py`、`tools/dev_wave_wait.py` (受入の post-claim merge と submodule の扱い)、
  `orchestrator/campaign/patchharness.py` (`checkout` :346)、`orchestrator/campaign/s3_mocc_lock_coverage.py`、`orchestrator/tests/test_mocc_proof_surface.py`、
  `orchestrator/campaign/materializer_admission.py`、`orchestrator/campaign/condition_meaning_gate.py`、`orchestrator/tests/test_ccbench_spawn_sites.py`、`orchestrator/tests/test_p3_build_authority_cli.py`、
  `patches/README.md`、`docs/phase3.md` (見送り台帳 [T-167] 行)、`docs/ai-provenance.md`

## 前置き — これは自分たちのコードの設計レビューである

研究用 repo (並行性制御の自動合成) で、MOCC の検証計装をベンチマーク submodule の現行 pin の子 commit として載せ、pin 再承認の判断材料 (D1603 の 3 点) を揃える計画を点検してもらう。
依頼は「本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」と明示している。あなたは read-only の相談役で、実装・テスト実行はしない (静的読解でよい)。
**plan を守らせず点検せよ。親 brief の前提・file:line・親自身の実測値とその一般化も点検対象である。**

## レンズ B — 過剰・削除と、pin 材料・可搬性の実効性

次を点検し、所見ごとに real / refuted の見込み・重大度 (must-fix / should / nit)・根拠 file:line・放置時に成果物 (certified 判定・材料レポート・試行台帳) の値や受理集合がどう変わるかを 1 行で書く。

1. **過剰・削除。** plan の各成果物 (driver 候補 mode、新 JSON、`patches/` への候補 patch、新 test 11 node、変異 16 件、そして plan が brief を超えて足した
   hot 正負例 2 走 (hot-update-unlock)・`objcopy` による `.text` bytes 比較・候補固有 7 key・land 前 fetch への前倒し) のうち、研究前進 (brief の完了判定 (i)〜(iv)) か実測欠陥に対応しないものはどれか。
   既存策 (T-2294 の driver・test・JSON、D297 検査器) で足りる部分、削れる部分、局所修正で済む部分を具体的に。逆に、足りないせいで材料 3 点が揃わない部分があれば指摘する。
2. **(P5) test の可搬性。** 他 wave の worktree の submodule が C の object を持たないという親の読み (C は gitlink でない) は、`tools/dev_wave_submodule_init.py` の取得範囲 (全 branch を取るか) と受入経路で正しいか。
   正しいなら、C に依存する test が他 wave の受入を赤にする経路を具体的に。候補の中身を `patches/` に置く案と D16 (trace-hook は branch、patches/ は broken / variant / 診断) の緊張、T-2294 の先例との整合を判定せよ。
3. **(P3)/(P4) submodule commit と保全。** branch 名、commit message と trailer (`docs/ai-provenance.md`、witlight の先例)、一時 worktree 手順、submodule checkout を gitlink のまま clean に保つこと、
   bundle 保全、主 checkout の submodule git dir への fetch の時期 (land 前 / 後) — 各々の実効性と、land 検査・掃除道具・他 wave への副作用。
4. **D1603 材料 (3) 波及表の実効性。** plan の分類 (追随 / 据置 / 衝突) が t2756 §4 と t2304 §0〜§3 の実例と矛盾しないか。文字列外の依存 (patch の preimage、axis_mocc_temperature の PIN、
   mocc trace pilot と D2153 receipt v2、build admission policy epoch、s3_* driver の自前 PIN、fixture) の取りこぼし。43 件の数え方。
5. **scope 境界。** plan が gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN`・push・再承認の提示・探索開始・mocc の変異軸化・verifier や D297 検査器の変更に踏み込んでいないか。
   見送り台帳 ([T-167] 行) への記録の仕方が「再承認の提示」に当たらないか。I 面 ([T-2295]) の扱いが「不足の明記」に留まっているか。
6. 変異候補の帰属: 各変異が単一理由で赤になるか、冗長 gate (JSON sha 束縛など) で併発赤が出るものの扱い。

## 出力形式

- 見出しは `#` 1 段だけを使い、`##` は最後の `## 総括` のみ。`### 総括` と書いてはならない。
- 実行できない検査は「未実走・静的読解」と明記する。予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- **出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。
- 末尾に `## 総括`: must-fix / should / nit の一覧 (各 1 行)、削除・縮小の推奨一覧、(P1)〜(P6) への支持 / 反証、plan の修正要求の要約。
