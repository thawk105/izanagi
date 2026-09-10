単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order

必読事項の射影:

- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s4-ruling.md` — 親の段 4 裁定 (実装の正本)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s1-probe.md` — 親の実測値。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/verifier/dsg.py` — 変更後の実体。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/test_verifier.py` — 追加されたテスト。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/verifier/model.py` — `EdgeReason` / `Integrity` / `VerifyResult` の定義。読めなければ即停止。

## 差分の所在と、親が既に実行した分担

レビュー対象の差分は **commit 済み**である。この worktree で
`git show HEAD` または `git diff HEAD~1..HEAD` で読める (HEAD = `c3f130e34`)。
**commit は親が行った。** 実装子は commit していない。docs、fixture、受入所要時間台帳は
いずれも変更されていない (裁定どおり)。

`output/insights/2026-09-08_t2436-ww-reason-order/` は未追跡だが、これは親が書いた入力資料であり
レビュー対象の実装差分ではない。

## これは何のための依頼か

これは**私たち自身のリポジトリの、正しさ検査器 (verifier) に入れた変更のレビュー**である。
verifier の理由列挙が実行のたびに順序を変えていた欠陥を直した。実装が裁定どおりか、
正しさの判定を動かしていないかを、独立の目で点検してほしい。実装を守る立場ではなく、
**見落としを指摘する立場**で読むこと。

## あなたのレンズ — 実装が判定を動かしていないか

次を順に点検し、指摘ごとに **real / refuted** と **must-fix / nit** を明記せよ。

## 1. 差分が裁定の範囲を超えていないか
裁定 (`s4-ruling.md` 第 9 節) は「`dsg.py` の 1 行」と「`test_verifier.py` へテスト 1 本」だけを
許した。差分にそれ以外の変更が 1 byte でも入っていないか、`git show HEAD` の全ハンクを数えて確かめよ。

## 2. 判定を動かす経路が入っていないか
整列の導入で、次のいずれかが変わる経路がないかをコードで確かめよ。

- `EdgeReason` の**集合** (順序ではなく、どの理由が作られるか)。
- `CycleEdge.types`、`_classify()` の返り値、`anomaly_count`、`total_cycles`。
- `integrity.notes` へ「理由を再構成できなかった」と書く枝の発火条件。
- `versions` を引く `bisect_left` の判定式そのもの。

`sorted()` が例外を投げうる入力 (比較不能な key の混在など) が現行モデルで構成できるかも述べよ。
構成できるなら、それは新しい失敗経路である。

## 3. 追加テストが恒真になっていないか
このプロジェクトで最も避けたいのは「謳うだけで発火しない検査」である。次を確かめよ。

- 実装から `sorted` を外したとき、このテストは**必ず**赤になるか。親の実測では
  seed 1 の未整列順は `5,2,4,1,3,6`、seed 777 は `2,1,3,4,5,6` である (`s1-probe.md`)。
  テストが比較しているものが、この差を実際に捕まえる位置にあるかを確かめよ。
- 逆に、テストが**実装と同じ誤りを共有していて**両方直っていなくても緑になる形になっていないか。
  特に、テスト側が期待値を `sorted(...)` で計算していて、実装の順序をそのまま受け入れる形に
  なっていないかを見よ。
- assert している値が、cycle 以外の理由でも成立する**過剰決定**になっていないか。
  親は `certified` を過剰決定と判定して外した。残した 5 つの assert
  (`verdict`、`serializable`、`anomaly_count`、`total_cycles`、`phenomenon`) のうち、
  同じ理由で過剰決定になっているものがあれば指摘せよ。

## 4. 既存テストを弱めていないか
既存テストの期待値が 1 つでも変わっていないか、xfail や skip が足されていないかを確かめよ。
既存の golden (`"reasons": [...]` を持つもの) が整列の影響を受けて書き換えられていないかも見よ。

## 5. 親の実測とその一般化への攻撃
親は次を実測したと書いている。**独立に確かめ、誤りがあれば指摘せよ。**

- wr / rw 枝の理由順は 6 seed すべてで安定し、変動するのは ww だけである。
- 同一 key に複数の WW 理由が出る入力は現行モデルでは構成できない。
- 合成 trace では `integrity.clean()` が proof-surface の欠落で False になる。

## 制約

- あなたは `sandbox=read-only` で走る。書込可能な tmp が無いので **pytest を実走しなくてよい**。
  静的検査で足りる。実測は親が行う。**実走していないものを緑と書いてはならない。**
- ファイルを書き換えてはならない。commit してはならない。
- 指摘には必ず `file:line` を添えよ。
- **成果物への影響 (certified な選択・レポート・台帳の値・受理集合・参照がどう変わるか) を
  1 行で書けない指摘は must-fix にしてはならない。** nit として区別して書け。
- 仮想リスク向けの gate・検査・台帳・一般化の新設を勧めてはならない (scope 外)。
- 予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。
- 結合文字 U+0300〜U+036F を出力に使ってはならない。
- 日本語で書け。

## 出力形式

次の見出しをこの順で、すべて `##` (H2) で書く。`###` を使ってはならない。
各指摘は「所見 / real か refuted か / must-fix か nit か / 根拠の file:line / 成果物への影響 / 直し方」。
最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。

## 差分の範囲
## 判定を動かす経路
## テストの恒真性
## 既存テストの弱体化
## 親の実測への攻撃
## 総括
