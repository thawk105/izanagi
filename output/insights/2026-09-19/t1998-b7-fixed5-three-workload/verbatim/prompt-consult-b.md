単独段 dispatch: stage=consult; sandbox=read-only; parent=/home/SFC/tanab/.claude/jobs/f6bf33bb/brief.md

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/f6bf33bb/brief.md (親の段 1 brief。**攻撃対象に含む**。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f6bf33bb/rulings-verbatim.md (ユーザー裁定・D1639・D2044 項 3・失敗条件 (e)・候補 prereg・床値・A-6 先例・nodes=5 probe の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f6bf33bb/plan-out.md (段 2 の plan。攻撃対象。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/docs/paper-story/results/2026-09-16-b7-three-run-materials.md (併記する既存材料。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/docs/paper-story/README.md (results 系列の規則。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md (nodes=5 と bench.lock 直列化の実測。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/output/env/pegasus/calibration/between_run_noise_t48_skew0p9_rr5_rmw0.json (床値 rr5。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/output/env/pegasus/calibration/between_run_noise_t48_skew0p9_rr50_rmw0.json (床値 rr50。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/output/env/pegasus/calibration/between_run_noise_t48_skew0p9_rr95_rmw0.json (床値 rr95。読めなければ即停止)

repo root は /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression。他の repo 内 file (module、tests、decisions、worklog、insights) も必要なら同 root 配下を読んでよい。

# 依頼 — 段 3 敵対相談 レンズ B: 実効性と過剰 — 研究前進に効くか、scope 外の混入、親の provisional 裁定 (P1)〜(P7)

plan を守らず検査せよ。**親 brief 自身が主な検査対象である。** 反論は具体的な根拠 (file:line、裁定 D 番号、一次資料の値) を
伴う real だけを挙げ、推測は「未確認」と分けて書け。

## 攻撃の観点

1. **研究前進に効くか**: この wave の成果物 (同一候補 fixed 5 µs の 3 workload 同時期測定 + 床値判定の稿) は、
   失敗条件 (e) と B-7 の材料として、2026-09-14 / 09-16 稿・A-1 sized attempt-0001 (`docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md`) では
   供給できない何を足すか。**足さないなら wave を止める理由になる**ので正直に書け。逆に、ユーザー裁定の範囲で
   足りない (例: 床値判定の定義が曖昧で稿が書けない) 点があれば挙げよ。
2. **(P3) 床値の適用**: ユーザー裁定「対差が −floor を下回れば退行」で、`effect_w = adopted_median / stock_median − 1` を
   `floor_w` (1 arm の between-run CV、JSON `between_run.cv`) と直接比べる形は、D1639 の定義 (「差が信用できるかの下限、compare の丸め閾値」)
   と整合するか。結果を見る前に固定すべき判定式の細部 (median の定義、丸め、等号の扱い、`unstable`/anomaly の扱い、
   床値 JSON の genome が `BACKOFF_FIXED=-1` を持たない旧 canonical である点) に穴が無いか。**判定式を緩める提案はしない**。
3. **(P1) 同一 build・(P5) 同時期・同時刻の対照**: 「同一 attempt で 3 request を同時 qsub、各 workload 内で stock/adopted を
   同 node・同 campaign で連続測定」が「同一 build・同時期・同時刻の対照」として稿で主張できる範囲と、主張できない範囲
   (node 差、bench.lock 直列化、queue 分断、binary の別 build) を区別せよ。ユーザーが要求する「性能主張には同時刻の対照」を
   この形が満たすか。
4. **scope 外の混入・過剰**: plan / brief に certification の昇格・新 protocol・追加 gate・partial 一般化・plotter 拡張・
   A-2/A-6 policy 変更・job body 変更が混じっていないか。逆に、scope を狭めすぎて成果物が成立しない箇所 (例: tracked leaf の
   materialize が 3 workload で通らないのに稿を書けない) が無いか。
5. **(P2) 新 policy = 新 protocol ではない**: この読みが A-6 先例と `protocol_sha256` の定義 (`_protocol_preimage`) で支持されるか。
   ユーザーの「新 protocol は scope 外」に反する読みが可能なら、その根拠と、代替 (既存 2 policy だけで 3 workload を測る方法があるか) を示せ。
6. **(P4)(P7) nodes=5・walltime 12h・queue**: 現在 gen_S に別 wave の fp-* 3 request が RUN 中 (2026-09-19 時点の qstat) で、
   `~/.izanagi/bench.lock` を共有するなら本 wave の 3 request と直列化しうる。所要・同時期性への影響と、投入前に親が確認すべき事実
   (fp-* が同 lock を使うか = `orchestrator/campaign/lock.py` と該当 job body の `IZANAGI_BENCH_LOCK` 設定) を挙げよ。
7. **results 稿の設計**: `docs/paper-story/README.md` の results 系列規則 (append-only、一次資料束縛、status を研究判定へ拡張しない、
   図は figures/ の凍結物 + provenance) に照らし、brief C の稿の形 (併記の分け方、「図の材料」を稿内表 + leaf で済ませる P6、B-7 充足を判定しない) で
   足りない・過剰なものを挙げよ。

## 制約

- sandbox read-only。pytest は走らせられない。静的検査でよい。
- 予算が尽きそうなら途中結論を下記の出力形式どおり書いて終われ (無出力が最悪)。
- scope 外の一般化・新 gate は提案せず、必要なら「裁定パッケージ候補」に分けて返す。

## 出力形式

- `## real` (番号、根拠、壊れ方、最小修正)
- `## refuted` (brief / plan の主張で正しいと確認できたもの、根拠)
- `## 未確認` (静的に決められないもの、親の実測で確かめる方法)
- `## 裁定パッケージ候補` (無ければ「なし」)
- `## 総括` (5 行以内)
