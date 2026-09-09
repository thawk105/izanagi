単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg

必読事項の射影: 以下はすべて絶対パスである。**読めなければ即停止**し、読めなかったパスを出力に書け。

- 攻撃対象 1 = 段 2 プラン: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/plan.md`
- 攻撃対象 2 = 親 brief: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/brief.md`
- 逐語 D1813: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/d1813.md`
- 逐語 D1848: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/d1848.md`
- 第 1 段 (探索走) の一次資料 全文: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/t2418-explore-README.md`
- 格子定数と符号化の逐語: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/backoff-constants.txt`
- 実装の現物: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py`
- report の現物: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep_report.py`
- 投入 script: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/tools/pegasus/b10_backoff_grid.sh`
- patch の合成枝: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/patches/silo-backoff-fixed.patch`
- 先例の事前登録: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-shape-preregistration.md`
- docs の地図: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/README.md`
- docs 検査器: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/tools/check_docs.py`

repo path はすべて上記 worktree のものである。必要なら同 worktree の `docs/decisions.md` /
`docs/worklog.md` / `orchestrator/tests/` を検索して読んでよい。親側 repo は読まない。

## 依頼 — レンズ B「数値設計の実在性・既存系列との整合・時間予算」

[T-2500] の段 3 敵対相談である。**プランを守らず攻撃せよ。親 brief 自身も同じ強さで攻撃対象である。**
本 wave の成果物は事前登録 1 文書だけで、本走 driver も投入も次 wave である。

このレンズが担当する攻撃面:

1. **格子の実在性。** プランが選んだ µs 値のそれぞれについて、`encode_static_backoff_us` /
   `decode_static_backoff_us` の往復と、C++ 側 hole (`patches/silo-backoff-fixed.patch` の合成枝) の
   分岐条件を突き合わせ、**その値が実際に意図した物理量になるか**を確かめよ。境界 (1000 / 1001 /
   999 / 3000 / 9999) を必ず個別に検査せよ。到達できない値・別の枝へ落ちる値があれば指摘せよ。
2. **判定入力の実在 (DW-O13)。** 停止基準と失敗条件が参照する量が、本走が実際に出す成果物の
   **どの field** に存在するか。`backoff_extended_sweep_report.py` と探索走の report 実物を読み、
   field 名・型・単位を突き合わせよ。**field が存在するだけでは足りない。その field が実環境で
   取りうる値を探索の実測から見積もり、基準が要求する値が到達可能か**を確かめよ。到達不能な閾値は
   恒真か恒偽である。
3. **検出力。** rep 数 (プランが固定した値) と探索で実測された変動係数 (§12 は 0.7% 未満と書く) から、
   停止基準の閾値が**その反復数で判別できるか**を評価せよ。判別できない閾値なら、必要な rep 数か、
   閾値の側を直す提案をせよ。ただし絶対規律 4 (無造作に大きくしない) を守れ。
4. **時間予算。** プランの格子 (点数 × workload × rep) が `SWEEP_CAP_S` と PBS `elapstim_req` に
   収まるか、探索走の一次資料 §2 / §12 の**実走所要**から見積もれ。律速が build か直列性検査かも
   一次資料の記述から確かめよ。**推測の所要で議論するな。**
5. **既存系列との衝突。** 選んだ格子・命名・成果物 stem・schema 名が、`extended` / `t2266-tail` /
   `t2418-explore` の識別子や凍結物と衝突しないか。`git grep` で確かめよ。
   `EXTENDED_SWEEP_US` の上端を pin している test の実体を突き止め、本 wave が触れないことを確認せよ。
6. **docs 側の機械検査。** 新規 docs file と `docs/README.md` の追記が
   `python3 tools/check_docs.py` の予算・行番号参照禁止・living docs・三軸語・placeholder などの
   検査に抵触しないか。抵触する条項があれば、その条項の実体を `tools/check_docs.py` の行番号で示せ。
7. **親 brief の数値主張。** 親 brief が書いた「`REPS=5` / `EXTIME=3` / `RECORDS=1_000_000` /
   `THREADS=48`」「表現上限 9999」「上端 1000 が test に pin」を独立に確かめ、誤りを指摘せよ。

## 親が実測した事実 (これは推測ではない。あなたの検査の入力として使え)

親が探索走の成果物 JSON を直に読んで得た実測である。
出所 = `/work/1/SFC/tanab/b10-backoff-grid-t2418-explore/b10-backoff-grid-20260908T193601Z-2540578-<workload>/campaigns/*/reports/*.json`
(あなたも読んでよい。読むときは `jq` か `cat` を使え。`python3 -c` は guard に拒否されることがある)。

- report の point ごとの実 field は `backoff_us` / `kind` / `median_tps` / `representative_abort_rate` /
  `abort_rate_reps` (5 本) / `throughput_tps_reps` (5 本) / `cv` / `unstable` / `certified` /
  `correctness_verified` / `variant_id` ほか。top level に `reps` / `extime_s` / `records` / `threads` /
  `run_kind` / `schema_version` / `status` / `points` / `measurement_order` ほか。
- **`cv` field は throughput の変動係数であって abort 率の変動係数ではない** (read-heavy adaptive の
  tps reps から再現して確認した)。
- **abort 率は小数第 4 位で量子化されて記録される。** 実測の逐語:
  - write-heavy: 2000 µs `[0.0292,0.0296,0.0292,0.0293,0.0292]` / 4000 µs
    `[0.0199,0.0198,0.0199,0.0198,0.0198]` / 9999 µs `[0.0114,0.0114,0.0114,0.0115,0.0114]`
  - balanced: 2000 µs `[0.0404,0.0402,0.0404,0.0404,0.0402]` / 4000 µs
    `[0.0269,0.0267,0.027,0.0267,0.0268]` / 9999 µs `[0.0145,0.0147,0.0145,0.0145,0.0145]`
  - read-heavy: 2000 µs `[0.017,0.017,0.017,0.017,0.0169]` / 4000 µs
    `[0.012,0.0119,0.0119,0.0119,0.0119]` / 9999 µs `[0.0073,0.0074,0.0074,0.0074,0.0074]`
  - 静的点の throughput `cv` は 0.0018〜0.0065、文脈点は none 0.0132 / adaptive 0.0188 (read-heavy)。

**この実測を使って、プランの数値をあなた自身で計算し直せ。** 少なくとも次を確かめよ。

- プランの `qhat` / `se` / `nu` / `qL` / `U` の式に上の実測を入れて、探索の 3 点から
  隣接区間の値を実際に計算せよ。**閾値 `U <= 0.05` と CV gate `0.02` が、この実測の値域に対して
  恒真か恒偽か、それとも判別できるか**を数値で示せ。
- 量子化 1e-4 が、右端 (abort 0.0073〜0.0145) で平均の何%に当たるかを計算し、
  5 rep の標本 sd がその量子より小さくなる点があるかを確かめよ。あるなら、se がどちらの向きに
  誤るか (区間が広がるのか狭まるのか)、その結果として飽和が宣言されやすくなるのか
  なりにくくなるのかを、符号つきで結論せよ。
- 半オクターブ (log 比 0.3466) で 1 区間を測ることが、この分解能で意味を持つかを評価せよ。

## 制約

- 所見は **real / refuted を自分で判定**し、根拠を path と行番号で示せ。判定しない所見を出すな。
- **scope 外の real 所見も報告してよいが、実装を要求するな。**「裁定パッケージ候補」と明記せよ。
- 成果物の値・受理集合・参照がどう変わるかを 1 行で書けない所見は must-fix にせず nit と明記せよ。
- sandbox は read-only である。**pytest 緑を要求しない。静的検査でよい。** 実走していないものを
  「確認済み」と書くな。
- 予算が尽きそうなら途中結論を下記の形式で書いて終われ。無出力が最悪である。
- 出力に結合文字 U+0300〜U+036F を使うな。

## 出力形式

## 所見
(1 件ずつ。`[real|refuted] [must-fix|nit|裁定パッケージ候補] 見出し` → 根拠 (path:line) → 成果物影響 1 行 → 提案)

## 親 brief への攻撃
(brief 固有の誤り・過大一般化。無ければ「無し」と書き、確かめた命題を列挙する)

## 総括
(3〜8 行)
