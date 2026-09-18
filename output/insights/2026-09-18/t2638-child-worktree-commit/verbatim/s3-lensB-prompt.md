単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit

必読事項の射影:

- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s1-brief.md` — 親の段 1 brief。**brief 自身も検査対象**。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s2-plan.md` — 段 2 の plan (攻撃対象)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/tools/dev_wave_codex.py` — 起動器 (354 行)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/tools/dev_wave_wait.py` の 1585〜2000 行。全文は読まない。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/docs/dev-wave/core.md` の `## DW-G05` 節。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/docs/dev-wave/workers.md` の `## DW-S05-A` 節。読めなければ即停止。

## 依頼 (レンズ B: 過剰・削除)

これは敵対相談である。plan と親 brief に含まれる**依頼外の追加**を見つけて削れ。依頼文は
「本題の終端契約だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。新しい保存
framework は作らない」である。`DW-G05` の基準 (確定主目的・scope の本体実装と足りる既存策・局所修正を
優先し、要求外の仮想リスクで framework・一般化・互換層・gate・検査・台帳を足さない) で裁け。

攻撃面 (最低限):

1. **待ち手側 (`--commit-worktree`) は要るか**: 起動器の終端 commit が launcher rc に依らず走るなら、
   待ち手側は「起動器 process 自体が signal で死んだ」場合だけの後詰めである。DW-C00 は
   「生産者を止めるとき待ち手も落とす」と定めるので、その場合は待ち手も死んでいる。残る事象
   (OOM 等) の実在を brief/plan が示しているか。示していなければ削除候補。**ただし依頼文は
   「起動器 / 待ち手の終端で」と両方を名指ししている** — 削る場合はこの文言との整合を明記せよ
   (文言の解釈: 「起動と待ちの終端 = 子の走行が終わった時点」か「両 tool」か)。
2. **skip 条件の過剰**: detached / main / mid-merge / root 不一致 / index.lock のうち、実在する経路に
   対応しないものはどれか。実在 = 現行の dev-wave 手順 (DW-S05-A、DW-C01) で発生しうるもの。
   「念のため」の条件は削る候補 (ただし安全側の skip は「gate」ではなく「発火しない」なので、
   削る根拠は実在性ではなく単一理由性・テスト負担で示せ)。
3. **stdout 固定書式・sidecar・台帳**: plan が receipt 形式の JSON や新 schema を足していないか。
   stdout 1 行で足りるか。
4. **helper の一般化**: 新 module や汎用 API (引数の多さ、将来拡張用 option) を足していないか。
   `git_state.py` の allowlist 追加は最小か。
5. **テストの過剰**: 正例 1 + 負例数件で足りるところに、同じ理由で落ちる冗長テストが無いか。
   逆に、依頼の本体 (残差が commit される・read-only で発火しない) の正例が実体を名指しして
   いるか (代役で通る緑になっていないか、F649)。
6. **docs**: DW-S05-A の改訂が L1.5 予算 (9,696 / 9,696) に収まる最小の bytes か。相殺のために
   安全義務を削っていないか。
7. **brief の (P5)**: cleanup-si-routing との相互作用を「記録する」だけに留めているか。解決策を
   忍び込ませていないか。

各所見に「削ると何が失われるか / 残すと何が増えるか」を 1 行で添えよ。

制約: read-only sandbox。pytest は走らせない。静的検査でよい。実装しない。予算が尽きそうなら
途中結論を出力形式どおり書いて終われ (無出力が最悪)。出力は最終メッセージ本文に全文を書け。

## 出力形式

見出しはすべて `##` (H2)。最後の節は必ず `## 総括` (`#` を 2 個)。`### 総括` と書いてはならない。

## 削除候補 (番号、対象、根拠、失うもの)
## 不足 (依頼の本体に足りないもの)
## brief への攻撃
## 推奨する plan v2 の最小形
## 総括
