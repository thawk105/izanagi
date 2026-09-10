単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order

必読事項の射影:

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md` — 点検対象のプラン。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/output/insights/2026-09-08_t2436-ww-reason-order/verbatim/brief-s1.md` — 親の段 1 brief。**これ自身も点検対象**。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s1-probe.md` — 親が段 1 で取った実測。**これ自身も点検対象**。読めなければ即停止。
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/verbatim/D1817.txt` — 本題の確定裁定 (逐語全文)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/verifier/dsg.py` — 変更対象の実体。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/test_verifier.py` — テストを足す先。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/fixtures/README.md` — fixture の登録契約。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/docs/dev-wave/mutation.md` — 変異走行の契約。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/acceptance_duration_ledger.json` — 受入所要時間の台帳 (新規 node の登録先)。読めなければ即停止。

上記はすべてこの worktree または job dir の絶対パスである。repo path はこの worktree のものを使う。

## これは何のための依頼か

これは**私たち自身のリポジトリの、正しさ検査器 (verifier) に対する設計レビュー**である。
verifier の理由列挙が実行のたびに順序を変えるため、同じ入力から違う要約値 (digest) が出る。
これを直すプランが妥当かを、独立の目で点検してほしい。
プランを守る立場ではなく、**見落としを指摘する立場**で読むこと。

## あなたのレンズ — 検査の実効性と整合

このレンズの担当は「足すテストが本当に効くか」「手順と成果物の辻褄が合うか」である。
正しさ境界そのものは別のレンズが担当するので、あなたは深入りしなくてよい。

次を順に点検し、指摘があれば **real / refuted** を明記して述べよ。

## 1. 足すテストが未修正の実装を必ず落とすか
親は「既存テストは整列の有無を区別できない (1 つの辺に ww 理由を 2 本以上持つ golden が 0 件)」と
測っており、だから正例を足さないと変異が生き残ると書いている。プランのテスト設計を読み、
**未修正の実装 (元の未整列の集合走査) に対して、そのテストが必ず赤になるか**を確かめよ。

- 「偶然緑になる」経路は無いか。集合の列挙順は `PYTHONHASHSEED` で決まるので、
  key の数が少ないと未修正でも整列済みと同じ順序が出る確率が無視できない。
  プランが選んだ key 数と seed の組で、その確率がどれくらいかを見積もれ。
- 親の probe (`s1-probe.md`) には seed 0/1/2/3/4/777 の実際の順序が載っている。
  プランの選んだ seed で**現に**未整列の順序が出ているかを、その実測値と突き合わせよ。
  突き合わせられない seed を使っているなら指摘せよ。
- 別プロセスを立てる設計なら、そのプロセスが親と同じ repo を import するか、
  環境変数の受け渡しが正しいかを確かめよ。

## 2. 所要時間と受入への影響
このリポジトリには「テスト全体の所要は 5 分が絶対上限、直列化と長時間 job は禁止」という規律がある。

- プランのテストが立てるプロセス数と、1 本あたりの所要見込みを見積もれ。
- 新しい nodeid が増える場合、`orchestrator/tests/acceptance_duration_ledger.json` への
  登録が要るかを、同 file の使われ方から確かめよ。要るなら、それを誰がいつ作るかが
  プランに書かれているかを見よ。
- **新しいテストファイルを作る設計になっていないか。** この repo では新規 test file は
  自走 harness と受入台帳の両方を要求するため、既存 `test_verifier.py` へ足すほうが安い。
  プランが新規 file を作る設計なら、その追加費用が正当化されているかを見よ。

## 3. fixture を足す場合の副作用
プランが `orchestrator/tests/fixtures/` へ新規ディレクトリを足す設計なら、次を確かめよ。

- `fixtures/README.md` の更新義務に掛かるか。
- fixture ディレクトリを列挙・計数する既存テストがあるか (あるなら名指しせよ)。
- 逆に、テスト内で一時 trace を組み立てる設計なら、既存 helper (`test_verifier.py` の
  `_tmp_trace` 付近) を使っているか、後始末 (`shutil.rmtree`) が漏れていないかを見よ。

## 4. 変異事前登録の帰属が成立するか
`docs/dev-wave/mutation.md` の契約を読んだうえで、プランが挙げた変異候補について、

- 「整列を外して元へ戻す」変異が、プランのテストで **KILLED** になると言えるか。
  赤になる nodeid が名指しされているか。名指しが無ければ指摘せよ。
- 等価変異 (意味が変わらないので生き残って当然のもの) と、本当に検出されるべき変異が
  区別されているか。
- 変異が「診断だけが赤くなる」種類でないか (判定そのものが赤くなるか)。

## 5. 親 brief の scope 判断
親は「wr / rw 枝の変更、consumer 側の正規化、gate・検査・台帳・一般化の新設」を scope 外にした。
この線引きで、**本題が閉じきらずに残る穴**があるなら指摘せよ。
ただし、穴があっても scope を広げよという主張ではなく、
「残る限界として何を明記すべきか」の形で書くこと。

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

## テストの実効性
## 所要時間と受入への影響
## fixture の副作用
## 変異帰属の成立
## scope と残る限界
## 総括
