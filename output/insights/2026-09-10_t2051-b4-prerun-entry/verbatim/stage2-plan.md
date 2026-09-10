## 枝 A — 発火する実装面の純増

結論は、**名指しできない。P1 は倒れない。**

候補を `DW-G04` / `DW-G05` / production consumer の3条件で落とすと次のとおり。

| 候補 | 既存 consumer | 不適格な理由 |
|---|---|---|
| publication 発行 CLI | launcher は bootstrap 時に publication root と attempt ID を必須にする。[launcher.py:561–589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_launcher.py:561)、[同:676–693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_launcher.py:676) | production の適格 precursor は M13 で 0 件。issuer は 201 eligible 行未満を publication 前に拒否する。[issuer.py:796–805](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_prerun_issuer.py:796)。したがって CLI を足しても今日の正当な入力では発行されず、台帳・report・受理集合を変えない。 |
| 実成果物 → `B4ScheduledAttemptInput` 変換器 | issuer はこの型の列を要求する。[issuer.py:709–713](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_prerun_issuer.py:709) | 実在する production caller がなく、変換後も eligible は 0/201。新 CLI は「公開呼び手を置くだけ」になる。 |
| report → certified-selection 接続 | 将来の sink 候補自体はあり得る | `report.complete`、report 後 caller、耐久判定先のいずれも実在しない。[T-2139 README:57–61](/work/1/SFC/tanab/izanagi/output/insights/2026-09-01_t2139-b4-certified-selection-connection/README.md:57)、[同:106–114](/work/1/SFC/tanab/izanagi/output/insights/2026-09-01_t2139-b4-certified-selection-connection/README.md:106)。`DW-G04` と consumer 条件を満たさない。 |
| raw writer / report generator の追加 | 既存 publication が consumer 入力 | 既に実装済みで「純増」ではない。writer は [raw_record_producer.py:2057–2093](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_raw_record_producer.py:2057)、report command は [material_report.py:1551–1614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_material_report.py:1551)。 |

したがって、編集 file・追加関数・呼び手・正負テストを伴う枝 A の実装案は起草しない。起草すれば、依頼が禁じた非発火 caller の提案になる。

## 枝 B — 実装面の純増が無い場合の成果物

成果物は親が予定する  
`output/insights/2026-09-09_t2051-b4-prerun-entry/` に、次の L1〜L5 を固定した停止地点として残す。

| 層 | 実測した停止地点 | file:line 根拠 | artifact path / 計測 |
|---|---|---|---|
| L1 — precursor と予定表 | production eligible precursor は 0。さらに実 artifact から予定表16列を導く権威ある producer がない。 | 列定義は [ledgers.py:123–144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_analysis_ledgers.py:123)、適格性は [同:922–936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_analysis_ledgers.py:922)。module 自身も authoritative producer 不在を宣言する。[同:1–6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_analysis_ledgers.py:1) | M10、M13。`t2341-eligibility/{base,sort,trigger}.json(.sha256)` は driver 配線証拠であり precursor 母集合ではない。[事前登録:314–331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/docs/phase3-b4-reflux-ablation-preregistration.md:314) |
| L2 — publication | issuer 機構は存在するが、0/201 なので `design_not_feasible` で bundle 公開前に停止する。 | [ledgers.py:1050–1105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_analysis_ledgers.py:1050)、[issuer.py:801–805](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_prerun_issuer.py:801) | M6: `output/**/{scheduled-attempt-registry.jsonl,analysis-manifest.json,prerun-issuer-receipt.json}` は各0件。固定名は [issuer.py:46–49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_prerun_issuer.py:46)。 |
| L3 — formal launch / raw result | launcher の publication 必須配線と durable writer は着地済み。ただし入力 publication がないので正当な bootstrap と planned-result write は発火しない。 | [launcher.py:561–589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_launcher.py:561)、[raw producer:527–590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_raw_record_producer.py:527) | M7: B-4 marker campaign 0件。将来 path は `<campaign-root>/b4_launch_context.json` と issuer に束縛された各 planned result path。 |
| L4 — analysis / §7.1 report | command、全 manifest block × 2 arm の射影、非上書き writer は実装済み。publication がないため production report は0。 | composition は [material_report.py:211–287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_material_report.py:211)、全件 frame は [同:331–355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_material_report.py:331)、完全射影検査は [同:546–710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_material_report.py:546)。 | 既定は `<publication-root>/reports/{report.json,report.md,report.complete}`。[同:1274–1302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_material_report.py:1274)。M5 では `report.complete` 0件。 |
| L5 — certified selection | report は明示的に非 certifying。report 後 caller、判断保存先、sink 参照がない。 | [material_report.py:883–897](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_material_report.py:883)、[T-2139 README:97–114](/work/1/SFC/tanab/izanagi/output/insights/2026-09-01_t2139-b4-certified-selection-connection/README.md:97) | 実 report path / 計測 ID はなし。一次資料は `output/insights/2026-09-01_t2139-b4-certified-selection-connection/README.md`。 |

成果物には各層について `state=stopped`、要求入力、観測値、M-ID、file:line、実在 path または「0件を確認した検索根」を記録する。推測・将来リスク・仮想 gate は入れない。

## 必答項目への回答

### 予定表を実成果物から導く経路

**今日、正当な production 経路は存在しない。**

不足は次の三点。

- `B4ScheduledAttemptInput` の16列は型として存在するが、ledger は既に与えられた値を検証・正規化するだけである。[ledgers.py:305–367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_analysis_ledgers.py:305)、[同:447–489](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_analysis_ledgers.py:447)
- issuer は実 artifact を読まず、caller-supplied 列を直接受け取る。[issuer.py:709–738](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_prerun_issuer.py:709)。外部の権威ある母集合へ束縛しないことも明記されている。[同:53–60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_prerun_issuer.py:53)
- 特に必須列 `initial_proposal_sha256` は [ledgers.py:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_analysis_ledgers.py:137) にある一方、downstream producer 自身が「計算・記録する経路が repo に無い」と宣言している。[raw_record_producer.py:62–70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_raw_record_producer.py:62)

### publication 発行前後に実在が必要なもの

機械的な issuer 成功条件と、正当な formal run 条件を分ける必要がある。

issuer 呼出し前に必要:

- 完全な `B4ScheduledAttemptInput` 列。ID一意性、型、reference 等は [ledgers.py:305–367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_analysis_ledgers.py:305)。
- そのうち最低201行が、`reason=scheduled`、whiteboard `rejected`、4赤 class のいずれか、calibrated workload、bootstrap member、一意 reference、arm digest 未受領等を満たすこと。[同:922–936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_analysis_ledgers.py:922)
- 全 scheduled attempt と全単射する planned result path。絶対・一意・未作成で、祖先衝突や issuer 固定 path との衝突がないこと。[issuer.py:336–404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_prerun_issuer.py:336)、[同:419–443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_prerun_issuer.py:419)
- publication root の実 directory parent。root leaf 自体は不存在でなければならない。[同:170–185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_prerun_issuer.py:170)、[同:221–252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_prerun_issuer.py:221)

seed、schedule receipt、registry、manifest、issuer receipt は事前成果物ではなく issuer が生成する。[issuer.py:745–849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_prerun_issuer.py:745)

発行後、formal run 前に必要:

- 実在する registry と manifest の path・sha256・行数を §5 の母集合欄へ束縛すること。規則参照だけでは不可。[事前登録:193–200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/docs/phase3-b4-reflux-ablation-preregistration.md:193)
- calibrated `PerfConfig`、frozen bootstrap、unique reference、floor artifact、予算、env tag、model/prompt/projection 値、実行責任者など §5 の全前提。[同:154–167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/docs/phase3-b4-reflux-ablation-preregistration.md:154)
- §6 は1条件でも欠ければ実走禁止。[同:624–684](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/docs/phase3-b4-reflux-ablation-preregistration.md:624)

### `EXPECTED_BLOCK_COUNT == 201` の意味

**実装上は「201個の実 precursor file が存在すること」ではない。**

`generate_analysis_manifest()` は caller-supplied registry 行を `_attempt_is_eligible()` で絞り、eligible 行が201未満なら `design_not_feasible`、201以上なら canonical 順の先頭201行を採る。[ledgers.py:1050–1105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_analysis_ledgers.py:1050)

したがって機械条件は「201件の適格な型付き registry 行」。元 precursor artifact の存在や正当性は実装が再導出しない。規範上は、これらの行が B-4 結果を見る前に凍結した実 precursor 母集合から導かれていなければならない。[事前登録:358–408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/docs/phase3-b4-reflux-ablation-preregistration.md:358)

### M13

**提示された実測の範囲では正しい。反例 path はない。**

M13 の7件は success 7 / rejected 0。一方、適格性には `whiteboard_result is REJECTED` が必須なので、eligible precursor は0件になる。[ledgers.py:922–936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_analysis_ledgers.py:922)

T-2049 の「real seed 1 block + 200複製」は test fixture であり production 反例ではない。[T-2049 README:162–170](/work/1/SFC/tanab/izanagi/output/insights/2026-09-01_t2049-b4-material-report/README.md:162)

### M2〜M5

- **M2: 正しい。** producer/durable writer と report generator/sanctioned command の着地は [T-2049 README:18–39](/work/1/SFC/tanab/izanagi/output/insights/2026-09-01_t2049-b4-material-report/README.md:18) で確認できる。
- **M3: 正しい。** 同 README は残件を certified-selection connection の1語と明記する。[同:20–24](/work/1/SFC/tanab/izanagi/output/insights/2026-09-01_t2049-b4-material-report/README.md:20)
- **M4: 結論は正しいが、件数表現は不正確。** T-2139 は「4点」とし、3点は無条件、4点目は順方向を含める場合だけの条件である。[T-2139 README:106–114](/work/1/SFC/tanab/izanagi/output/insights/2026-09-01_t2139-b4-certified-selection-connection/README.md:106)
- **M5: 3つの無条件条件について正しい。** 正方向まで含めるなら、§5 の floor がなお `未記入` なので条件4も少なくとも一部未成立である。[事前登録:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/docs/phase3-b4-reflux-ablation-preregistration.md:162)

## 親 brief の誤り

明確な訂正点は二つ。

1. M4 の「再開条件3件」は、正確には**無条件3件 + 順方向の場合の条件1件**。
2. M14 の「§5 は6欄が `未記入`」は文字どおりには誤り。`未記入` を含む値セルは line 159、162〜167 の**7行**ある。開始時刻については義務撤廃が追記された一方、sentinel gate との関係は未裁定のままと明記されている。[事前登録:275–287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/docs/phase3-b4-reflux-ablation-preregistration.md:275)

また、親 M8 は現 launcher の実装に照らして正しいが、issuer の `"formal_launcher_not_wired_to_require_this_receipt"` と事前登録 §7.2 の「正式 launcher への必須配線も無く」は現コードと食い違う。[issuer.py:53–55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_prerun_issuer.py:53)、[事前登録:709–720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/docs/phase3-b4-reflux-ablation-preregistration.md:709)。これは親 brief の誤りではなく、投影資料内の陳腐化した記述として停止成果物へ記録すべきである。凍結 doc の編集は提案しない。

## 総括

P1 は維持される。今日の最初の実停止点は、**実成果物から正当に予定表を作る権威経路がなく、かつ production eligible precursor が 0/201**であること。そこから publication、formal launch、raw writer、report、certified selection が順に未発火になる。

実装 diff は0とし、L1〜L5 の停止地点、M4/M14の訂正、陳腐化した non-guarantee の食い違いを insight と worklog に残す計画が妥当。read-only のため編集・pytest 実走は行っておらず、未実走を緑とは扱っていない。