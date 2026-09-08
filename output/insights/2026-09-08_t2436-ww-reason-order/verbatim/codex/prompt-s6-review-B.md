単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order

必読事項の射影:

- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s4-ruling.md` — 親の段 4 裁定 (実装の正本)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/test_verifier.py` — 追加されたテスト。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/verifier/dsg.py` — 変更後の実体。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/conftest.py` — test の収集と分類。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/docs/dev-wave/mutation.md` — 変異契約。読めなければ即停止。

## 差分の所在と、親が既に実行した分担

レビュー対象の差分は **commit 済み**である (HEAD = `c3f130e34`)。
`git show HEAD` で読める。**commit は親が行った。** 実装子は commit していない。
docs、fixture、受入所要時間台帳はいずれも変更されていない (裁定どおり)。
`output/insights/2026-09-08_t2436-ww-reason-order/` は未追跡の親の入力資料であり、実装差分ではない。

実装子はこの sandbox の制約により `PYTHONPATH=. python3 orchestrator/tests/test_verifier.py` の
自走 harness だけを走らせ、**106 件全緑**を報告している。`tools/run_tests.py` と
`python -m pytest` はこの環境では走らない。親は統合後に受入全走を行う。

## これは何のための依頼か

これは**私たち自身のリポジトリの、正しさ検査器 (verifier) に入れた変更のレビュー**である。
実装そのものの正しさは別のレンズが担当する。あなたは**検査の穴と波及**を担当する。
実装を守る立場ではなく、**見落としを指摘する立場**で読むこと。

## あなたのレンズ — 検査の穴、波及、運用の実効性

次を順に点検し、指摘ごとに **real / refuted** と **must-fix / nit** を明記せよ。

## 1. 追加テストが環境に依存して落ちないか
このテストは別プロセスを 2 本立てる。次を確かめよ。

- `cwd` と `env` と `sys.executable` の渡し方が、受入時の実行環境 (共有 login node、
  別の cwd、`PYTHONPATH` 未設定) でも成立するか。`PYTHONPATH` を渡していないが、
  `cwd` を repo root にするだけで `orchestrator` を import できるかを、
  repo の他のテストの先例と突き合わせて確かめよ。
- `timeout=30` が、負荷の高い共有ノードで不足しないか。この repo には
  「負荷 70 超の login node が 20 秒 timeout の subprocess テストを落とす」実績がある。
  不足するなら、**成果物への影響を書いたうえで**具体的な値を提案せよ。
- `check=True` で子が落ちたときに、失敗の原因 (stderr) が読める形になっているか。
- 一時 trace directory の後始末が、subprocess が失敗した経路でも行われるか。

## 2. 収集・分類の meta-test に掛からないか
新しいテスト関数が増えたことで赤になる検査が無いかを、**名指しで**確かめよ。少なくとも次を見よ。

- 素の自走 runner (同 file 末尾) の収集規則。
- `orchestrator/tests/conftest.py` の分類 (real-repo、slow、serial などの marker 付与)。
- test 関数の命名規約・数え上げ・一覧を固定する meta-test が repo にあるか
  (あるなら名指しし、掛かるか掛からないかを述べよ)。
- 新しい nodeid が増えることで exact 一致を要求する検査が赤にならないか。
  親は「受入所要時間台帳は nodeid ごとの被覆率 90% 以上を要求するだけなので 1 node 増でも
  破れない」と裁定した。**この裁定を独立に検算せよ。**

## 3. 変異事前登録が契約に合っているか
親は M1〜M3 を **`diagnostic sensitivity pin`** として登録し、`KILLED` とは数えないと裁定した。
`docs/dev-wave/mutation.md` の `DW-M03` と `DW-M08` に照らして、この区分が正しいかを確かめよ。
また次を見よ。

- M1 (`sorted` を外す) の期待失敗 node が **`test_multi_ww_reason_report_is_hash_seed_deterministic`
  ただ 1 件の完全集合**である、という親の期待は妥当か。
  **他に赤になる既存テストが無いか**を、`_reasons()` の出力順に依存する既存テストを
  全部洗い出して確かめよ。1 件でも見落とせば期待 node の完全一致が崩れる。
- M2 (降順) と M3 (version だけを整列 key) が、それぞれ本当にこのテストで赤になるか。
  特に M3 は「stable sort が入力 set 順を温存する」ことに依存している。この依存が成立するかを
  コードと Python の仕様から述べよ。
- 単一理由性 (`DW-M01`): これらの変異で赤になる理由が 1 つに絞れているか。

## 4. 下流の consumer への波及
`_reasons()` の出力順が変わることで、次のどれかが影響を受けるかを名指しで確かめよ。

- `orchestrator/verifier/report.py` の text renderer とその出力を読む consumer。
- `orchestrator/critic/digest.py` など、verifier の出力を要約する側。
- anomaly の JSON を読む campaign 側 consumer (`reflux_formal_consumer.py`、
  `mocc_g2_discriminator.py` など)。
- 追跡下の凍結成果物。親は「多重 WW を持つ辺は 0 件なので bytes は変わらない」と実測したが、
  **順序が変わらないことと bytes が変わらないことが同値になる条件**を確かめよ。

## 5. 残る限界の書き方
親は「固定 seed 2 本の保証は現行 CPython 実装での実測に基づく」「`workers=1` だけを通す」を
限界として記録すると裁定した。**この 2 つで足りるか。**書き漏らしている限界があれば挙げよ。
ただし scope を広げる提案ではなく、「何を明記すべきか」の形で書くこと。

## 制約

- あなたは `sandbox=read-only` で走る。書込可能な tmp が無いので **pytest を実走しなくてよい**。
  静的検査で足りる。実測は親が行う。**実走していないものを緑と書いてはならない。**
- ファイルを書き換えてはならない。commit してはならない。
- 指摘には必ず `file:line` を添えよ。
- **成果物への影響を 1 行で書けない指摘は must-fix にしてはならない。** nit として区別して書け。
- 仮想リスク向けの gate・検査・台帳・一般化の新設を勧めてはならない (scope 外)。
- 予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。
- 結合文字 U+0300〜U+036F を出力に使ってはならない。
- 日本語で書け。

## 出力形式

次の見出しをこの順で、すべて `##` (H2) で書く。`###` を使ってはならない。
各指摘は「所見 / real か refuted か / must-fix か nit か / 根拠の file:line / 成果物への影響 / 直し方」。
最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。

## 環境依存
## 収集と meta-test
## 変異登録の妥当性
## 下流への波及
## 残る限界
## 総括
