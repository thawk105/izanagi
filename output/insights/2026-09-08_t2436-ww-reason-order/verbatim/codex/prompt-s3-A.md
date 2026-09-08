単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order

必読事項の射影:

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md` — 点検対象のプラン。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/output/insights/2026-09-08_t2436-ww-reason-order/verbatim/brief-s1.md` — 親の段 1 brief。**これ自身も点検対象**。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s1-probe.md` — 親が段 1 で取った実測。**これ自身も点検対象**。読めなければ即停止。
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/verbatim/D1817.txt` — 本題の確定裁定 (逐語全文)。読めなければ即停止。
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/verbatim/D1388.txt` — enforcement closure の裁定 (逐語全文)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/verifier/dsg.py` — 変更対象の実体。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/verifier/model.py` — `EdgeReason` / `CycleEdge` / `Anomaly` の定義。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/verifier/report.py` — anomaly の直列化。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/CLAUDE.md` — 絶対規律 2 / 3 / 7 の正本。読めなければ即停止。

上記はすべてこの worktree または job dir の絶対パスである。repo path はこの worktree のものを使う。

## これは何のための依頼か

これは**私たち自身のリポジトリの、正しさ検査器 (verifier) に対する設計レビュー**である。
verifier は「トランザクションの実行履歴が直列化可能か」を判定する部品で、このプロジェクトの
正しさの番人にあたる。その理由列挙が実行のたびに順序を変えるため、同じ入力から違う要約値
(digest) が出てしまう。これを直すプランが妥当かを、独立の目で点検してほしい。
プランを守る立場ではなく、**見落としを指摘する立場**で読むこと。

## あなたのレンズ — 正しさ境界

このレンズの担当は「この変更が、正しさの判定そのものを動かしていないか」である。
実効性・所要時間・運用の話は別のレンズが担当するので、あなたは深入りしなくてよい。

次を順に点検し、指摘があれば **real / refuted** を明記して述べよ。

## 1. 受理集合が本当に不変か
親は「reason の集合は不変で、順序だけが変わる」と主張している。プランの実装差分を読み、
**判定結果 (anomaly の有無・件数・分類 `phenomenon`) を動かす経路が無いか**を確かめよ。
特に次を見ること。

- `_classify()` は `edges` から型集合を作る。並べ替えがこの集合に影響しないことを、コードで確かめよ。
- `anomalies()` が `reasons` の空判定で `integrity.notes` へ書き込む枝がある。並べ替えが
  この枝の発火条件を変えないことを確かめよ。
- 並べ替えの key の選び方 (key 文字列だけか、版を含むタプルか) によって、**同一 key に複数の
  WW 理由が出る場合に順序が決まらない**ことはないか。そのような入力が構成可能かを、
  `_reasons()` の判定式から論じよ。構成不能なら、なぜ不能かを式で示せ。

## 2. 親の実測とその一般化に無理がないか
親は probe で「rw の理由順は 6 seed すべて安定、変わるのは ww だけ」と測り、そこから
「wr 枝も同じ list を走査するので安定」と**一般化**している。この一般化は妥当か。
`_reasons()` の wr 枝と rw 枝が読む list が本当に同じ順序保証を持つか、
`Txn.reads` がどこで作られどう並ぶかまで辿って確かめよ。
並列実行 (`workers>1`) の経路で理由生成の入力順が変わりうるかも見ること。

## 3. 見落とされた束縛が無いか
親は段 1 で次を実測したと書いている。**独立に確かめ、抜けがあれば指摘せよ。**

- `dsg.py` の中身のハッシュを固定している台帳・テスト・信頼の根は無い (パス名の列挙だけ)。
- 追跡下の成果物のうち、1 つの辺に ww 理由を 2 本以上持つものは 0 件なので、
  凍結済み成果物の作り直しは要らない。
- `dsg.py` は enforcement source closure に入っているので、変更を commit する前に
  焦点テストを走らせると `contract-loader-drift` で落ちる。

親のこの 3 点のうち、**パス名以外を key にして張られている束縛** (役割名・グループ名・
schema 名などを key にするもの) を探し落としていないかを重点的に見よ。

## 4. 規律 2 に触れる向きが無いか
このプロジェクトの絶対規律 2 は「正しさゲートを緩める変更を許さない」である。
プランの中に、**判定を通りやすくする向き**の変更が紛れていないか。
特に、テストを足す設計が「現実装なら必ず緑になる」形に寄っていて、
検査として恒真になっていないかを見よ。

## 制約

- あなたは `sandbox=read-only` で走る。書込可能な tmp が無いので **pytest を実走しなくてよい**。
  静的検査で足りる。実測は親が行う。**実走していないものを緑と書いてはならない。**
- ファイルを書き換えてはならない。commit してはならない。
- 指摘には必ず `file:line` を添えよ。根拠のない断定を書かない。
- プランに同意する箇所は「refuted」として短く書き、同意しない箇所を厚く書け。
- 予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。
- 結合文字 U+0300〜U+036F を出力に使ってはならない。
- 日本語で書け。

## 出力形式

次の見出しをこの順で、すべて `##` (H2) で書く。`###` を使ってはならない。
各指摘は「所見 / 判定 (real か refuted か) / 根拠の file:line / 成果物への影響 / 直し方」を書く。
最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。

## 受理集合の不変性
## 親の実測と一般化の点検
## 見落とされた束縛
## 規律 2 の向き
## 総括
