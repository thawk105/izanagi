# [T-2852] (c) の判断を repo に記録するか・どう記録するか — 相談用 brief (親、2026-09-29 JST)

## 経緯
- T-2852 の事前登録の草稿は local main に着地済み (D2278、worklog entry 1907)。T-2852 の持ち越し項は「ユーザー確認待ち」で、択一 (a) S1-wh で本走 / (c) S3 の後に回す を返していた。
- 2026-09-29 未明、マネージャー session から「ユーザーは朝まで不在。codex と相談して決めよ。(c) なら D の fragment で記録し T-2852 を更新して land まで」と中継された。
  親は codex 2 立場 (a 推し・c 推し) に相談して (c) と判断した: `decision.md`、`consult-a.md`、`consult-c.md` (同じ dir)。
- 記録用の worktree 作成が Claude Code の自動モード判定で拒否されたので、親は止めて「記録と land してよいか」をユーザーへ返した。
- ユーザー本人が直接「codex に相談して決めてください」と返答した (2026-09-29)。

## 決めること
1. (c) の判断を repo に記録して land するか。
2. 記録するなら、D の本文で判断の位置づけ (ユーザーの裁定か、ユーザーの委任による AI の判断か) をどう書くか。
3. T-2852 の持ち越し項の新しい状態と文面 (何を待ち、いつ・何の条件で再提示するか)。`decision.md` の「再判断の条件」を使う案。

## 参照
- `/work/1/SFC/tanab/tmp/t2852-p5-decision-20260929/decision.md`・`consult-a.md`・`consult-c.md`
- ユーザーの恒久指示 (memory の要旨): 「needs input は出さず codex に相談して決める、今後も」。「計算費用は私に確認を取って欲しい。重大な話です」(D2212 項 4、1 タスク 2 node 時間以上)。
- `/work/1/SFC/tanab/izanagi/docs/decisions.md` の「## D2278.」「## D2212.」「## D2272.」節 (委任による判断の書き方の先例として D2272 冒頭の「相談の採否」も参照)
- `/work/1/SFC/tanab/izanagi/docs/spool/decisions/README.md`・`docs/spool/worklog/README.md` (fragment の形式)
