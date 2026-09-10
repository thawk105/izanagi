単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg

必読事項の射影: 以下はすべて絶対パスである。**読めなければ即停止**し、読めなかったパスを出力に書け。

- 親 brief: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/brief.md`
- 逐語 D1813 (本 wave を発注したユーザー裁定): `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/d1813.md`
- 逐語 D1848 (第 1 段の設計判断): `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/d1848.md`
- 逐語 D95 (実装面の定義): `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/d95.md`
- 第 1 段 (探索走) の一次資料 全文: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/t2418-explore-README.md`
- 格子定数と符号化の逐語: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/backoff-constants.txt`
- 先例の事前登録 (形式の手本): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-shape-preregistration.md`
- 実装の現物: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py`
- 投入 script (時間枠): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/tools/pegasus/b10_backoff_grid.sh`
- docs の地図 (挿入先): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/README.md`
- 論文側の残件 B-10: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/paper-story/2026-08-26.md`
- backoff 論文の主張軸: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/paper-story-backoff/2026-09-05.md`

repo path はすべて上記 worktree のものである。親側 repo (`/work/1/SFC/tanab/izanagi/docs/...`) を読んで
はならない。必要なら `decisions.md` / `worklog.md` も上記 worktree 側を検索して読んでよい。

## 依頼

[T-2500] の段 2 プラン起草である。**書くのは事前登録 1 文書だけ**であり、driver・RUN_KIND・test・
コードは本 wave の scope 外である (親 brief の (P1-a))。あなたは file:line 粒度のプランを起草する。

作るもの: 新規 `docs/b10-backoff-static-tail-preregistration.md`。静的 backoff の**右側**
(物理値 1000 µs 超、表現上限 9999 µs) の本格格子・反復数・停止基準 (飽和判定)・失敗条件を、
**本走の結果を見る前に**固定して凍結する事前登録である。第 1 段の探索は完走済みで、その結果
(3 workload とも 2000→9999 µs で abort 率が単調低下し飽和しない) は既知であり、**開示したうえで**
格子を選んでよい。開示せずに選ぶことだけが禁じられる。

## あなたが決め、根拠つきで書くこと

1. **格子。** (1000, 9999] のどの µs を測るか。点数と間隔の規則 (対数等間隔か等比か、端点の扱い)、
   その点数で足りる理由、および**それ以上増やさない理由** (CLAUDE.md 絶対規律 4 = 飽和する最小規模)。
   参照点 (backoff なし / adaptive / 正式格子の上端 1000 µs) を同一 job 内に含めるか、含めるならどれを、
   なぜか。探索の 3 点 (2000 / 4000 / 9999) を abscissa として再利用してよいか、その可否の根拠。
2. **反復数と動作点。** rep 数・extime・records・threads・workload 集合を literal で固定する値と、
   共有定数を参照しない理由。
3. **停止基準 (飽和判定)。** 「飽和した」と判定する述語を、結果を見る前に確定した式として書く。
   - 何の量に対する述語か (abort 率か、throughput か、両方か)。
   - 隣接点間の相対変化か、微分の推定か、区間推定を使うか。閾値の数値と、その数値をどう正当化するか。
   - 反復間ばらつき (探索の実測では変動係数 0.7% 未満) をどう入れるか。
   - **表現上限 9999 µs までに飽和が現れない**という結末を、正当な結末として前向きに定義する
     (親 brief (P1-d))。その場合に何を主張し、何を主張しないか。
   - 停止基準は「測るのを止める規則」なのか「飽和位置を報告する規則」なのか、語を曖昧にせず定義する。
4. **失敗条件。** 事前登録の失敗条件 = その条件が起きたら結果を主張として使わない条件。少なくとも
   correctness gate、静的 amount ごとの binary 相異検査 (完全性)、欠測 cell、変動係数の上限、
   時間枠超過、非単調性の扱い、job の途中終了を扱え。**規律 2 を緩めない** — 先例 t2266 / t2418 が
   要求している強さより弱い gate を書いてはならない (探索走の一次資料 §3 を読め)。
5. **開示。** 第 1 段の探索値・探索から格子を選んだ経緯・停止基準の選定根拠を本文のどこにどう書くか
   (D1813 が開示を明示要求している)。探索の測定値を正式推定へ混ぜない規則も書く。
6. **機械可読 spec。** 先例 `docs/b10-backoff-shape-preregistration.md` §5 と同形式の、HTML comment で
   区切った JSON ブロックの**完全な骨格**。key と型と値を全部書く (値が本 wave で確定できないものは
   置いてはならない — 確定できないなら格子か基準の設計が未完である)。`schema_version` の命名も決める。
7. **後続 wave の driver への束縛。** 本走 driver が満たすべき条件 (本書の commit hash の記録、spec の
   parse、campaign identity の分離、探索走との成果物 stem の非衝突) を、本書が前向きに要求する形で書く。
   **driver 自体は書かない。**
8. **文書構成。** 章立てを決め、各章に何行程度で何を書くかを示す。`docs/README.md` の**どの行の直後**に
   何行の項目を足すかを line 番号つきで示す。

## 制約 (違反したら plan は差し戻す)

- `orchestrator/`・`tools/`・`hooks/`・test をひとつも変更しない前提で立案する (docs-only)。
- `EXTENDED_SWEEP_US` (0..1000) と、その上端を pin している test を変更しない。
- 表現上限 9999 µs (`STATIC_BACKOFF_MAX_US`) を超える値を格子へ入れない。符号化の変更も提案しない。
- 既存正式系列 (`extended` / `t2266-tail`) の受理集合・成果物・report schema を変えない。
- 仮想リスク向けの gate・検査・台帳・一般化を足さない。事前登録が要求する規則だけを書く。
- 時間予算は実測から見積もる。`b10_backoff_grid.sh` の `SWEEP_CAP_S` と PBS の `elapstim_req`、
  および探索走の一次資料 §2 / §12 にある実走の所要を根拠にせよ。**推測の所要を書かない。**

## 実行条件

- sandbox は read-only である。書込可能 tmp が無いため **pytest 緑を要求しない。静的検査でよい。**
  テストの実測は親が行う。実走していないものを「確認済み」と書いてはならない。
- 予算が尽きそうなら、途中結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。
- 出力に結合文字 U+0300〜U+036F を使うな。
- 数値・引用は必ず上記の実ファイルから取り、記憶で書かない。引用元は path と行番号で示せ。

## 出力形式

見出しは以下の H2 を使う。

## プラン
(上の 1〜8 を file:line 粒度で。挿入位置・章立て・JSON spec の完全な骨格を含める)

## 根拠
(各判断の根拠を、読んだ file の path と行番号つきで)

## 未確定・リスク
(自分の案の弱点、割れうる択一、親が裁定すべき点)

## 総括
(3〜8 行。何を決め、何が未確定か)
