単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg

必読事項の射影: 以下はすべて絶対パスである。**読めなければ即停止**し、読めなかったパスを出力に書け。

- 攻撃対象 1 = 段 2 プラン: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/plan.md`
- 攻撃対象 2 = 親 brief: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/brief.md`
- 逐語 D1813: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/d1813.md`
- 逐語 D1848: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/d1848.md`
- 逐語 D95: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/d95.md`
- 第 1 段 (探索走) の一次資料 全文: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/t2418-explore-README.md`
- 格子定数と符号化の逐語: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/backoff-constants.txt`
- 共通規律の正本: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/CLAUDE.md`
- 先例の事前登録: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-shape-preregistration.md`
- 実装の現物: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py`
- 失敗台帳: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/failures.md`

repo path はすべて上記 worktree のものである。必要なら同 worktree の `docs/decisions.md` /
`docs/worklog.md` / `docs/archive/` を検索して読んでよい。親側 repo は読まない。

## 依頼 — レンズ A「事前登録としての前向き性・恒真性・正しさ防壁」

[T-2500] の段 3 敵対相談である。**プランを守らず攻撃せよ。親 brief 自身も同じ強さで攻撃対象である。**
本 wave の成果物は事前登録 1 文書 (`docs/b10-backoff-static-tail-preregistration.md`) だけで、
本走 driver も投入も次 wave である。

このレンズが担当する攻撃面:

1. **恒真性。** 書こうとしている規則のうち、どれが「必ず満たされる」ために何も排除しないか。
   停止基準・失敗条件・格子規則を 1 つずつ取り、**それが偽になる具体的な観測**を書けるか検査せよ。
   書けない条項は恒真である。特に「飽和しなければそう書く」型の条項が、あらゆる結果を受理する
   逃がし道になっていないかを見よ。
2. **前向き性の実体。** 第 1 段の探索結果は既に判明している。この状況で「結果を見る前に固定した」と
   言えるのは正確にどの命題か。プランと親 brief が、探索で既に見えている事実を「前向きに固定した」と
   書き換えている箇所を挙げよ。先例 `docs/b10-backoff-shape-preregistration.md` の
   「これは事前登録ではない。probe の結果を見た後に行った改訂である」に相当する正直な限定が
   本書にあるか。
3. **正しさ防壁 (CLAUDE.md 絶対規律 2)。** 本書が本走に要求する correctness gate・binary 相異検査・
   欠測規則が、先例 t2266 / t2418 が実際に強制している強さより弱くなっていないか。
   探索走の一次資料 §3 が名指しする `_require_distinct_static_binary_hashes` の穴と、
   先例がそれを塞いだ方法を読み、本書の要求がその強さに達しているか検査せよ。
4. **consumer 不在の帰結。** 親は (P1-a) で「本 wave は docs-only、driver を書かない」と provisional に
   裁定した。この裁定の下で、本書は**何によって拘束されるのか**。後続 wave が本書を無視して別の格子で
   走らせたとき、それを止めるものが repo に存在するか。存在しないなら、本書は何を保証すると
   主張してよいか。**逆に、本 wave で driver を書くべきだという主張をするなら、その根拠を
   「仮想リスク」でなく実在の欠陥・要求で示せ** (CLAUDE.md と親 brief の scope 規律)。
5. **探索値の分離。** 「探索値を正式標本へ混ぜない」を、プランが実際に何で担保しているか。
   abscissa の再利用 (親 brief (P1-b)) と測定値の混入の区別が、機械可読 spec の上で判別可能か。
   判別できないなら、どの field が足りないか。
6. **親 brief 自身の実測値と一般化。** 親 brief が書いた事実 —
   「`EXTENDED_SWEEP_US` の上端は 1000」「表現上限は 9999」「`git grep b10-backoff-static-tail` は 0 件」
   「B-10 の過抑制域が本 wave の研究前進」「docs に静的 tail の事前登録は無い」— を独立に確かめ、
   誤り・過大一般化・言い過ぎを指摘せよ。
7. **信頼境界 (CLAUDE.md 規律 6)。** 本書が本走の結果や成果物の field を受け取る側になったとき、
   汚染された入力が判定を緩められる経路があるか。

## 親が実測した事実 (これは推測ではない。あなたの検査の入力として使え)

親が探索走の成果物 JSON を直に読んで得た実測である。
出所 = `/work/1/SFC/tanab/b10-backoff-grid-t2418-explore/b10-backoff-grid-20260908T193601Z-2540578-<workload>/campaigns/*/reports/*.json`
(あなたも読んでよい。読むときは `jq` か `cat` を使え)。

- report の point ごとの実 field は `backoff_us` / `kind` / `median_tps` / `representative_abort_rate` /
  `abort_rate_reps` (5 本) / `throughput_tps_reps` (5 本) / `cv` / `unstable` / `certified` /
  `correctness_verified` / `variant_id` ほか。
- **`cv` field は throughput の変動係数であって abort 率の変動係数ではない** (read-heavy adaptive で
  tps reps から再現して確認)。プランが「探索の最大 CV 0.65%」を閾値の根拠に使っている箇所が、
  abort の話と throughput の話を取り違えていないか検査せよ。
- **abort 率は小数第 4 位で量子化されて記録される。** 実測の逐語:
  - write-heavy 9999 µs の `abort_rate_reps` = `[0.0114, 0.0114, 0.0114, 0.0115, 0.0114]`
  - read-heavy 9999 µs の `abort_rate_reps` = `[0.0073, 0.0074, 0.0074, 0.0074, 0.0074]`
  - read-heavy 4000 µs の `abort_rate_reps` = `[0.012, 0.0119, 0.0119, 0.0119, 0.0119]`
  - balanced 9999 µs の `abort_rate_reps` = `[0.0145, 0.0147, 0.0145, 0.0145, 0.0145]`
- したがって tail の右端では、1e-4 の量子が平均の 0.9〜1.4% に当たり、**5 rep の標本標準偏差は
  量子化に支配されている** (write-heavy 9999 の abort CV は約 0.39%、量子の半分 0.44% より小さい)。

この事実を、プランの停止基準 (rep 標本から se を作り、その se で同時下限 `qL` を引き、
`U <= 0.05` で飽和と判定する) に突き合わせよ。**abort 率が報告分解能に近づくほど標本 sd が縮み、
区間が狭まり、飽和が宣言されやすくなる**という向きの誤りがあるかどうかを判定せよ。あるなら、
それは「機構が測れていないこと」を「飽和」と呼ぶ恒真化であり、規律 2 と規律 3 に触れる。

## 制約

- 所見は **real / refuted を自分で判定**し、根拠を path と行番号で示せ。判定しない所見を出すな。
- **scope 外の real 所見も報告してよいが、実装を要求するな。**「裁定パッケージ候補」と明記せよ。
- 成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるかを 1 行で書けない所見は
  must-fix にせず nit と明記せよ。
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
