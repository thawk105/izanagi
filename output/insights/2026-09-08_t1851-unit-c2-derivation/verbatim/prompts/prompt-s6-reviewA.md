単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root (read-only。実装が入っている木): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2`
- **本 wave の全差分**: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/wave-full.diff`
- **親の段 4 裁定 (受入基準の正本)**: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s4-adjudication.md`
- 契約の正本: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
- 過去の失敗の型: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/failures.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/CLAUDE.md`

# 段 6 敵対レビュー A — 正しさ境界

**実装を守らせない。壊しに行く。** 対象は段 2 の plan ではなく**実際に入ったコード**である。

作業 root は read-only で書込み可能な tmp が無い。**pytest 緑を要求しない。**
静的読解と grep による実測だけで結論を出す。**走らせていないものを緑と書かない。**
**file を 1 つも作れない。成果物は最終メッセージの本文へ全文を書くこと。**
予算が尽きそうなら**途中結論を出力形式どおりに書いて終わること** (無出力が最悪)。

## 親が実測済みの事実 (再測不要。誤りと判れば指摘すること)

- 対象 3 file の親による独立実走: **675 passed / 3 skipped / 0 failed**。
- `FORMULA_ID` は変更していない。診断 counter `rep_integrity_failures` が
  `post_spawn_execution_exception` の class でのみ増えることを、
  producer の全 outcome class 直積 341 通りで exact に固定した。
  `exec_failures`・qualified throughputs・session の有効性・median は不変。

## このレンズが見るもの — 正しさ境界だけ

1. **受理集合が広がった箇所を全部見つける。** 実装後のコードで、
   **以前は拒否されていた入力が今は受理される**箇所を具体値で示すこと。
   とくに `execution_failure` を足したことで緩んだ条件が無いか。
2. **`exec_failures` と `rep_integrity_failures` の分離が、実装後のコードで本当に保たれるか。**
   片方をもう片方から導けてしまう経路、または片方が他方の代理として使われている箇所を探すこと。
   terminal evidence の本数式の作り直しが**新しい再結合を持ち込んでいないか**を疑うこと。
3. **carrier 欠落 padding の `None` が、下流のどこかで `False` と同じ扱いに落ちていないか。**
   `None` を schema error にする経路が本当に発火するかを追うこと。
4. **`execution_failure is True` と成功情報の矛盾を拒否する条件が、実際に発火するか。**
   その条件へ**到達する前に別の gate が拒否している**なら、その条件は恒真であり効いていない。
5. **恒真になる検査を探す。** 本 wave が足した assert のうち、
   **変更前のコードでも必ず通るもの**を名指しすること。
6. **旧 6-key の拒否が、意図せず正当な入力まで拒否していないか** (過剰拒否)。
7. **v1 (非 v2) 側の受理集合が 1 bit も動いていないこと**を独立に確かめること。
8. **診断文字列だけが変わって挙動が変わっていない箇所**を名指しすること
   (それは kill にも成果物影響にも数えられない)。

## 実装面の著者

**実装面のハンクに Codex `role=author` が無いものがあれば、レビューで代替せず停止して報告すること。**

## 過去の型の再発検査

`docs/failures.md` の型タグを攻撃面に含めること。とくに
**説明と実装の食い違い・consumer 取り残し・恒真な保証**を疑うこと。F 番号を引くこと。

## 禁止

- 実装を擁護しない。「概ね妥当」で終わらない。
- file を作らない。`git` の状態を変えない。
- 走らせていないテストを緑と書かない。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 出力形式 (この見出しをこの順で使う。本文へ全文を書く)

## 受理集合が広がった箇所
## 2 量の分離の破れ
## padding の None が落ちる経路
## 発火しない条件 (恒真)
## 過剰拒否
## v1 側への波及
## 診断だけの変化
## 過去の型の再発
## blocker と nit の仕分け
## 総括
