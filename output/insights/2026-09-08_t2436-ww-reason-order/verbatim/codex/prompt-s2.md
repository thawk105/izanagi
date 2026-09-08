単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order

必読事項の射影:

- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/output/insights/2026-09-08_t2436-ww-reason-order/verbatim/brief-s1.md` — 親の段 1 brief。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s1-probe.md` — 親が段 1 で取った欠陥の end-to-end 実測。読めなければ即停止。
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/verbatim/D1817.txt` — 本題の確定裁定 (逐語全文)。読めなければ即停止。
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/verbatim/D1388.txt` — enforcement closure の drift を緩めない裁定 (逐語全文)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/verifier/dsg.py` — 変更対象の実体。`_reasons()` は 517 行目付近。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/test_verifier.py` — テストを足す先。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/test_s8c_preregistration_predicates.py` — 2952 行目付近に、別 `PYTHONHASHSEED` の subprocess を回す既存テストの型がある。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/test_s8b_floor_campaign.py` — 12052 行目付近に、env matrix (`PYTHONHASHSEED` 1 / 777) の既存テストの型がある。読めなければ即停止。

上記はすべてこの worktree または job dir の絶対パスである。repo path はこの worktree のものを使う。

## 依頼

`orchestrator/verifier/dsg.py` の `_reasons()` が WW 理由を未整列の集合走査から作っているため、
同一 trace が process ごとに別の理由順・別の anomaly digest を出す。これを **key 順に整列して
決定的にする**実装の plan を、file:line 粒度で起草せよ。実装は後段の別の子が行う。あなたは書かない。

親の段 1 実測 (`s1-probe.md`) で、共通 WW key を 6 個持つ 2-transaction trace が
`PYTHONHASHSEED` 0/1/2/3/4/777 で 6 通りの ww key 順と 6 通りの digest を出すことを確認済みである。
同じ probe で rw 枝の理由順は 6 seed すべて安定していた。`anomaly_count` は全 seed で 1 だった。

## 不変条件 (破ってはならない)

- **anomaly の検出条件・受理集合を一切変えない。** edge の reason の**集合**は不変で、順序だけを決める。
  これは izanagi の絶対規律 2 (正しさゲートを緩める変異を許さない) に直接掛かる。
- 変更してよいのは `orchestrator/verifier/dsg.py` の `_reasons()` の WW 交差の走査順と、
  `orchestrator/tests/test_verifier.py` (必要なら `orchestrator/tests/fixtures/` 配下の新規 fixture) だけ。
- consumer 側での正規化、wr / rw 枝の変更、gate・検査・台帳・一般化の新設は scope 外。
- D1388 のとおり、enforcement source closure の binding を緩める案は禁止。

## 起草してほしいこと

## 1. 実装の file:line
`_reasons()` のどの行をどう変えるか。差分そのものを書いてよい。整列の key として何を使うか
(key 文字列そのものか、`(key, u_ver, v_ver)` のようなタプルか) と、その選択が
「同一 key に複数の WW 理由が出る可能性」に対して十分かを述べよ。

## 2. 正例テストの設計 (本 wave の実質的な作業)
親の実測では、既存の `test_verifier.py` の `"reasons": [...]` golden 10 ブロックのうち、
1 edge に ww を 2 本以上持つものは **0 件**だった。既存 anomaly artifact 6 件も同様に 0 件。
つまり**整列を消しても既存テストは全部緑のまま**である。整列を撃つ正例を足さなければ、
段 6 の変異 matrix で SURVIVED になる。

親の provisional 裁定は「異なる `PYTHONHASHSEED` の subprocess を 2 つ以上走らせ、
report bytes / digest の一致を見る型」である。理由は、単に
「reason key 列が sorted と一致する」と assert するだけだと、**未修正の実装でも seed 次第で
偶然緑になる**ため。これを支持するか、より良い型があるかを述べよ。次を必ず論じること。

- subprocess を使う型と、同一 process 内で完結する型の比較。同一 process 内で決定性を
  **偽陰性なく**撃てる方法があるならそれを示せ (`PYTHONHASHSEED` は interpreter 起動時に
  固定されるので、同一 process 内で seed を変えることはできない点を踏まえよ)。
- 何 seed を使うか。既存の負例 (未修正実装) がその seed 集合で**必ず**赤になることを、
  親の probe の実測値から論じよ (probe の各 seed の ww 順が s1-probe.md に載っている)。
- テストの所要時間。この repo は「全体 5 分が絶対上限、直列化と長時間 job は禁止」という規律を持つ。
  subprocess を何本立てるとどれくらい掛かるかを見積もれ。
- fixture を `orchestrator/tests/fixtures/` へ新規ディレクトリとして置くか、テスト内で
  一時 trace を組み立てるか。既存 helper `_tmp_trace` (`test_verifier.py:386`) がある。
  新規 fixture ディレクトリを足す場合、`orchestrator/tests/fixtures/README.md` の更新義務や
  fixture を数える既存テストに掛からないかを確認して述べよ。
- **新規 test file は作らない**方が良いか (この repo では新規 test file が自走 harness と
  受入所要時間台帳の両方を要求する)。既存 `test_verifier.py` へ足す案を既定とし、
  異論があれば述べよ。

## 3. 変異事前登録の候補
段 6 で走らせる変異 (mutation) の候補を挙げよ。最低でも「`sorted(...)` を外して元の
集合走査へ戻す」変異が、あなたの設計したテストで **KILLED** になることを論じよ。
どの nodeid が赤になるかを名指しせよ。等価変異になりうるものがあれば区別して挙げよ。

## 4. 掛かる可能性のある既存の pin・検査
親は段 1 で次を実測済みである。**再確認して、見落としがあれば指摘せよ。**

- `orchestrator/campaign/campaign_lock.py:59` と `:128` の `dsg.py` 出現は path 列挙 (closure の
  membership) であり内容 hash ではない。`test_artifact_admission.py:56,82,1643`、
  `test_campaign_lock_codec.py:318`、`test_t671_source_binding.py:33,47` も同じ。
- dsg.py の現行 blob sha256 を repo 全体で grep すると hit 0 件 (file 全体 sha256 の live pin なし)。
- dsg.py は enforcement source closure 内なので、**変更を commit する前に焦点テストを走らせると
  `contract-loader-drift` で落ちる**。これは実装の回帰ではない。
- 追加で、**行番号を literal に焼いた consumer** や、`test_verifier.py` の行番号に依存する
  検査が無いかを確認せよ。

## 制約

- あなたは `sandbox=read-only` で走る。書込可能な tmp が無いので **pytest を実走しなくてよい**。
  静的検査で足りる。テストの実測は親が行う。**実走していないものを緑と書いてはならない。**
- ファイルを書き換えてはならない。commit してはならない。
- 予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。
- 結合文字 U+0300〜U+036F を出力に使ってはならない。
- 日本語で書け。

## 出力形式

次の見出しをこの順で、すべて `##` (H2) で書く。`###` を使ってはならない。
最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。

## 実装の file:line
## 正例テストの設計
## 変異事前登録の候補
## 掛かる既存 pin と検査
## 残る不確実性
## 総括
