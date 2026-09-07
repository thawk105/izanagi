## 所見

所見 1: (P2) は成立せず、primary outcome 欄は埋めてはならない

§5.1 の解除条件は「raw な試行記録から入力型を作る経路」の実装を要求するが、adapter は既に解釈済みの専用 JSON を読むだけである。[p3_b4_analysis_adapter.py:9–14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_analysis_adapter.py:9) は、権威ある producer がない raw field が残り、それらを導出しないと明記する。実際、`treatment_fired`、`contaminated`、`protocol_ok` 等を入力 JSON からそのまま受け取る。[p3_b4_analysis_adapter.py:186–199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_analysis_adapter.py:186) [p3_b4_analysis_adapter.py:262–274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_analysis_adapter.py:262)

統合 path も `raw_analysis_records_bytes` と `source_artifact_bytes` を caller から受け取る API であり、元の WAL・whiteboard・receipt からそれらを生成しない。[p3_b4_analysis_path.py:199–207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_analysis_path.py:199) 同 file は「authoritative artifact producer、sanctioned command、durable writer」は scope 外だと明記している。[p3_b4_analysis_path.py:1–16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_analysis_path.py:1)

したがって 5-member closure に raw-record producer が欠落しており、§5.1 の逐語的条件を満たさない。[phase3-b4-reflux-ablation-preregistration.md:206–215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:206) brief の「adapter 実装済み」という (P2) は過大評価である。[brief.md:29](/home/SFC/tanab/.claude/jobs/6937f3cc/tmp/t2140-b4-prereg/brief.md:29)

所見 2: consumer は adapter と artifact-to-verdict 経路の契約一致を挙動検査していない

consumer 自身が、AST 検査は限定的で「hidden constant や alternate path がないことは証明できず、追加 tripwire もその強い主張の証明ではない」と宣言する。[p3_b4_analysis_prereg_consumer.py:9–13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:9)

さらに実装上、`assert_preregistration_matches_implementation()` が受け取る source は contract・ledgers・path のみで、adapter source は渡されない。[p3_b4_analysis_prereg_consumer.py:1005–1024](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:1005) adapter について確認するのは imported enum の missing-disposition 対応だけである。[p3_b4_analysis_prereg_consumer.py:957–986](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:957)

`evaluate_b4_artifacts` は AST 上の呼出順を調べるだけで、consumer の挙動 probe から実行されない。[p3_b4_analysis_prereg_consumer.py:739–754](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:739) live probe は ledger 選択・違反件数・pure contract の順位と閾値に限定される。[p3_b4_analysis_prereg_consumer.py:819–954](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:819)

したがって brief の「§5.1.1 の定義との一致を live 挙動まで検査する」という要約と、plan の「静的に確定できた」という総括は強すぎる。[brief.md:29](/home/SFC/tanab/.claude/jobs/6937f3cc/tmp/t2140-b4-prereg/brief.md:29) [plan.md:89–93](/home/SFC/tanab/.claude/jobs/6937f3cc/tmp/t2140-b4-prereg/plan.md:89)

所見 3: 「その artifact」をどちらに読んでも、plan の 5 path+sha256 は解除条件を満たさない

より自然なのは、consumer の成功を表す durable な検証 artifact、すなわち source-closure receipt と読む解釈である。単なる source hash は consumer が実際に成功した事実を示さないためである。consumer は確かに receipt producer を名乗るが、公開関数は receipt オブジェクトを返すだけで、artifact path へ永続化しない。[p3_b4_analysis_prereg_consumer.py:19–24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:19) [p3_b4_analysis_prereg_consumer.py:1092–1101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:1092) plan は receipt の path/hash ではなく 5 source member の path/hash を記入するため、この読みでは明白に不適合である。[plan.md:5–11](/home/SFC/tanab/.claude/jobs/6937f3cc/tmp/t2140-b4-prereg/plan.md:5)

「その artifact」を source file と読む場合でも、所見 1 の producer 欠落と所見 2 の consumer 射程不足が残る。したがって解釈の曖昧さで (P2) は救えない。

所見 4: primary 欄の記入は、§5.1 が明示的に塞いだ latent gate relaxation を再び開く

§5.1 は、実走前検査が値セルの意味・参照先を検査しないため、実装なしで欄を埋めると「他の欄が揃った時点で関門が開く」と警告している。[phase3-b4-reflux-ablation-preregistration.md:210–215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:210)

plan 自身も primary 行の path/hash の意味を parser が検査しないこと、freshness も検査しないことを認めている。[plan.md:13–24](/home/SFC/tanab/.claude/jobs/6937f3cc/tmp/t2140-b4-prereg/plan.md:13) [plan.md:26–31](/home/SFC/tanab/.claude/jobs/6937f3cc/tmp/t2140-b4-prereg/plan.md:26) 他欄の sentinel が残るため直ちに gate が通るわけではないが、未充足の primary 条件を「充足済み」に変えて将来の関門を一段開く。これは brief 自身の規律 2 と [CLAUDE.md:67–71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/CLAUDE.md:67) に抵触する。

所見 5: (P7) の「開始時刻を埋めない」理由は §5.1 から反証される

開始時刻は実際の開始値ではなく、timezone 付きの予定時刻であり、「この時刻より前に開始しない」という下限である。[phase3-b4-reflux-ablation-preregistration.md:261–262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:261) §0 はこの行だけ部分記入を明示的に許し、他欄の未充足と独立に扱う。[phase3-b4-reflux-ablation-preregistration.md:37–41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:37)

したがって「他欄が未了なので予定時刻を書けば虚偽」という brief の理由には根拠がない。[brief.md:34](/home/SFC/tanab/.claude/jobs/6937f3cc/tmp/t2140-b4-prereg/brief.md:34) 適切な将来時刻を選べば本当は埋められる欄である。ただし射影資料には選定済みの exact 時刻がないため、この consult から値そのものは導出できない。

所見 6: §10 の「(ii) 実測・(iii) 採否は完了」という無条件の追記は、射影された証拠だけでは裏付けられない

現行 §5 行が記入済みなのは確認できるが、§5.1.0 は「本小節を読む機械検査は無い」「履行は記入 commit と insight に人が書く」と明記する。[phase3-b4-reflux-ablation-preregistration.md:264–271](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:264) また §10 自身は、probe の dogfood は採用証拠ではないと警告する。[phase3-b4-reflux-ablation-preregistration.md:810–822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:810)

plan は §11 には現物確認条件を付ける一方、§10 の完了主張には同条件を付けていない。[plan.md:33–43](/home/SFC/tanab/.claude/jobs/6937f3cc/tmp/t2140-b4-prereg/plan.md:33) 現在の表と §10 が矛盾すること自体は確かだが、既存の probe 証拠・commit 束縛を親が確認するまでは「実測完了」を事実として断言できない。

## 反証できなかった前提

- (P1) は妥当。母集合欄には manifest/registry の実体が必要であり、規則や生成器だけでは埋められない。[phase3-b4-reflux-ablation-preregistration.md:193–200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:193)
- (P3) は妥当。規範本文が、calibrator の値へ差し替えるまで記入しないと明記する。[phase3-b4-reflux-ablation-preregistration.md:226–227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:226)
- (P4) は妥当。§5.1 は対称性・失敗の消費・retry 禁止だけを固定し、3 種の exact な予算値を供給しない。[phase3-b4-reflux-ablation-preregistration.md:228–229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:228)
- (P5) は妥当。env_tag には actual driver・execution site・tag、環境契約 path/hash、確認者が必要である。§5.1.0 の Pegasus 指定は eligibility probe の site であって正式実走 site ではない。[phase3-b4-reflux-ablation-preregistration.md:254–258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:254) [phase3-b4-reflux-ablation-preregistration.md:279–285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:279)
- (P6) は妥当。model 行は 4 点の別 commit 固定と人間の識別子を要求し、部分記入も禁止する。[phase3-b4-reflux-ablation-preregistration.md:230–253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:230)
- 計画した primary 値は §0 の表構文・値セル形式自体には違反しない。1 行・2 セルで、説明文・placeholder・内部 `|` はなく、5 hash も現 checkout の bytes と一致した。ただし意味上の解除条件は満たさない。
- §11 の追記案は、親が material-report の現物を確認するという plan の条件を厳守する限り、接続だけの解消に限定し、他の発効条件を解消済みとは読ませない。[plan.md:43–60](/home/SFC/tanab/.claude/jobs/6937f3cc/tmp/t2140-b4-prereg/plan.md:43)
- §1 の ancestry と §9 の HARKing 境界に、新しい独立問題は見つからなかった。§5.1.1 の規範 bytes を変えず正式結果より前に commit する限り、この種の実装参照更新自体は許容される。[phase3-b4-reflux-ablation-preregistration.md:45–55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:45) [phase3-b4-reflux-ablation-preregistration.md:790–806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:790)

## 総括

plan の primary outcome 行置換は却下すべきである。5-member closure は raw 試行 artifact の authoritative producer を含まず、consumer も adapter/path の契約一致を挙動検査していない。source 読みでも receipt 読みでも解除条件を満たさず、記入は規律 2 が塞いだ gate relaxation になる。

親の provisional 判断では (P7) だけが明確に過小評価である。§10 は既存証拠の確認後に限って完了追記を断言でき、§11 は plan の条件付き扱いを維持すれば過剰主張ではない。テストは実走しておらず、緑とは評価していない。