単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg

必読事項の射影: 以下はすべて絶対パスである。**読めなければ即停止**し、読めなかったパスを出力に書け。

- **検査対象 (fix 後の本体)**: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md`
- **検査対象 (地図)**: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/README.md`
- 段 6 レビュー A の所見: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/review-a2.md`
- 段 6 レビュー B の所見 (数値再計算つき): `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/review-b2.md`
- 親の段 4 裁定 (erratum 2 件つき): `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/adjudication.md`
- 段 3 の相談 2 本: `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/consult-a.md` と
  `/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/consult-b.md`
- 実装の現物: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py`

repo path はすべて上記 worktree のものである。親側 repo は読まない。本体は untracked である。

## 依頼 — fix 後の焦点再レビュー

親は段 6 の 2 レビューの real 所見に対して本体を直した。**直ったかどうかを、親の申告ではなく
本体の現物だけを読んで判定せよ。**

### 1. 対応表を必ず作れ

レビュー A の所見 (must-fix 9 件 + nit 4 件) とレビュー B の所見 (must-fix 4 件 + nit 2 件) の
**すべて**について、`closed` / `partial` / `regressed` / `not-addressed` を判定した表を出せ。
根拠は本体の節番号と逐語で示せ。**表なしで「閉じた」と判定してはならない。**

### 2. fix が持ち込んだ回帰を探せ

親は次を変えた。**この変更自体を攻撃せよ。**

- 区間の分類を 2 分割から **3 分割** (`saturated` / `declining` / `indeterminate`) にした。
  `U_flat` は分類から外し、診断値にした。
- 多重度を「片側 18」から「両側 36 の片側限界」へ変えた (`t(1 - 0.05/36, nu)`)。
- 飽和位置に**上限まで続くこと**を要求した。局所的な平坦 2 区間では位置を出さない。
- workload の状態を 3 つの排他状態にし、集約 verdict を上から順に評価する一意の表にした。
- 対数を取る前の前提条件と、ゼロ境界の扱いを書いた。
- 失敗条件を 12 項から 18 項へ増やした。spec の失敗列挙も増やした。
- `analysis_input_contract` の各 field に出所を書いた。
- 3 job の同一性 (§4.9) と hash の対象 bytes (§8.2) を定義した。

疑うべき点の例 — **これは網羅ではない。自分で探せ。**

- 3 分割は本当に相互排他かつ全域を覆うか。`saturated` と `declining` が同時に成立する入力はあるか。
- 「上から順に評価する」と書いた 3 つの表 (区間・workload・集約) に、順序を変えると結果が変わる
  組合せがあるか。あるならそれは順序依存であって一意性ではない。
- 多重度 36 は正しいか。18 区間 × 両側で 36 という数え方が、実際に使う限界の本数と一致するか。
- 上限まで続くことを要求したことで、**到達できない結末**が生まれていないか
  (たとえば `saturated` が事実上宣言不能になっていないか)。
- 失敗条件を増やしたことで、**正常な走行が失敗になる**条項が混ざっていないか。
  とくに探索走の実測値を本走に当てはめたとき、新しい 6 項のどれかが発火しないか。
- 散文 (§0〜§4、§6〜§9) と機械可読 spec (§5) の値・規則が食い違っていないか。
- §6 の参考値 (自由度 8、t=4.2556、半オクターブ 3.26%、短区間 9.78%) を自分で再計算して確かめよ。
- §2.3 の「点推定で 29.8〜37.1%」を探索の生 rep から再計算して確かめよ。

### 3. 格子の再生成

本体 §4.1 の規則から値を再生成し、本体の表・§5 の 4 か所・測定順と全点一致するかを確かめよ。
親裁定の erratum 1 が主張する「本文の 3535 / 7070 が正しい」を独立に確かめよ。

## 制約

- 所見は **real / refuted を自分で判定**し、根拠を path と節番号で示せ。
- 成果物影響を 1 行で書けない所見は must-fix にせず nit と明記せよ。
- 本 wave は docs-only である。コード・test・gate の新設を要求しない。
- sandbox は read-only である。**pytest 緑を要求しない。静的検査でよい。**
- 予算が尽きそうなら途中結論を下記の形式で書いて終われ。無出力が最悪である。
- 出力に結合文字 U+0300〜U+036F を使うな。

## 出力形式

## 対応表
(段 6 の全所見 → closed / partial / regressed / not-addressed → 根拠)

## 再計算
(格子・多重度・検出力・探索点推定を自分で計算した値と本体の値の対照)

## 新しい所見
(1 件ずつ。無ければ「無し」と書き、確かめた命題を列挙する)

## 総括
(3〜8 行)
