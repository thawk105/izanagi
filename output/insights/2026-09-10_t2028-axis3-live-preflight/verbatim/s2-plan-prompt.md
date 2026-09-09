単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight

必読事項の射影: 次を読む。読めなければ即停止し、読めなかった絶対パスを報告して終わる。

- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/brief.md` — 親の段 1 brief。scope の正本
- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/verbatim.md` — 既裁定と契約文の逐語射影
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py` — 軸 3 実行器 (8849 行)。改修対象
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/tools/run_axis3_search.py` — 軸 3 CLI
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/axis1_search/runner.py` — 軸 1 実行器。`HostLimiter` の既存実装 (移植元)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py` — 軸 3 の consumer test
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-09-01-axis3-search-amendment.md` — 契約の正本 (凍結)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-09-01-axis3-registration-preflight.md` — 直近の実行記録 (凍結)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/schemas/axis3_search_page_evidence.schema.json` — page evidence schema
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/schemas/axis3_search_checkpoint.schema.json` — checkpoint schema

## 依頼

軸 3 の live preflight を安全に実走できるようにする改修の **file:line 粒度の実装プラン**を起草せよ。
実装はするな。プランだけを書け。

## 背景 (親が実測で確定した事実)

- `orchestrator/related_work_search.py` に pacing が一切ない。`LiveHTTPTransport.send` は遅延なしで
  連続送信し、`run_preflight` は catalog 2122 行を 1 起動の単一 loop で回す。
  live preflight の wire attempt は arXiv 373 + OpenAlex 23 + DBLP 1533 = 1929 本。
- `_probe_response` は非 200 を `status=unavailable` にして loop を継続する。旧登録 §8.4 は
  「429・503・空ボディ・通信失敗・再試行上限到達は、その query を `未完走` にする」と定め、
  query 全体の再走上限は 1 回。**したがって無 pacing の実走は、自分で起こした 429 で
  数百行を恒久的に潰し、軸全体を `未完走` にする。**
- 軸 1 は同じノードから同じ 3 索引に対し `HostLimiter` (host 単位の最小間隔、`sleeper` 注入 seam、
  runtime 状態の file 永続化) で production 実績がある。最小間隔は arXiv 3.0 / OpenAlex 1.0 / DBLP 45.0 秒。
- `resume_bundle` の preflight 経路 (`_resume_preflight_from_wal`) は、既に試行済みの stream id を
  飛ばして残り行を継続する。ただし `begin_attempt` 後・`record_raw_response` 前に落ちると
  `unconfirmed_attempt_intent` で `status=blocked` を返す。

## プランに必ず含めること

1. **pacing の配置。** どの関数のどの行に host limiter を差し込むか。`run_preflight` /
   `_run_stream` / `run_ready` / `_resume_preflight_from_wal` のどこを通しても同じ limiter が効くこと。
   **待ち (sleep) は `begin_attempt` より前に置くこと** — 後ろに置くと、待機中に process が落ちた場合に
   `unconfirmed_attempt_intent` の袋小路へ入る。この順序が実際に成り立つ行番号を示せ。
2. **注入 seam。** `sleeper` を既定 `time.sleep` の引数として通す経路。monkeypatch は最後の手段
   (D78)。既存の `clock` 引数がどう流れているかを辿り、同じ経路に載せられるか判定せよ。
3. **N3 の観測記録。** `Retry-After` と rate-limit header、および実観測した request 間隔を
   preflight report のどの field へ書くか。**schema 変更が要るなら、どの schema の
   どの property をどう足すかまで書け。** 既存 field で足りるならそう書け。
4. **受理集合を変えないことの論証。** pacing は scheduling だけに触れ、
   `ready` / `unavailable` / `blocked` の判定規則を変えない。これを行単位で示せ。
   非 200 を `unavailable` にする既存分類を緩める案は禁止。
5. **429 を「起こさない」ことと「起きた 429 を無かったことにする」ことの区別。** 後者 (retry で
   握り潰す) は §8.4 違反なので提案するな。前者だけを設計せよ。
6. **test 計画。** 変更した挙動を殺す test を、既存 `orchestrator/tests/test_related_work_search.py` の
   どの class / 関数の隣にどう足すか。実時間 sleep をテストで走らせない方法 (fake sleeper) を示せ。
   **既存 test の期待値を変える案は禁止。**
7. **seal 再発行の手順。** source を変えると 2026-09-01 の seal は失効する。`register` 再実行の
   前提条件 (closure 8 file の作業ツリー bytes と `HEAD:<path>` の一致) を満たす commit 順序を書け。
8. **凍結物を 1 byte も変えないこと。** `2026-08-27-*` と `2026-09-01-*` の 4 文書は編集対象外。

## 禁止

- 実装・編集・commit をしてはならない。read-only である。
- 登録の語彙・10 枝・cutoff (2026-12-31)・包含・除外・判定語彙・query ID 集合を変える案。
- 本走 (`run-ready --live`)、resolver、control 評価器、`start_independent_pass` /
  `blocked_on_ruling` executor の実装。いずれも本 wave の scope 外。
- 仮想リスク向けの gate・検査・台帳・一般化の追加。
- 最小間隔を軸 1 の実測下限より**緩める**案 (速度のための弱体化)。厳しくする案は可。

## 実行環境の注意

書込可能な tmp が無いため pytest 緑を要求しない。静的検査でよい。テストの実測は親が行う。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## 出力形式

以下の H2 見出しをこの順で使う。結合文字 U+0300〜U+036F を使うな。

## 現状の把握
## 実装プラン (file:line 粒度)
## schema と成果物への影響
## test 計画
## seal 再発行と commit 順序
## 残るリスクと親への質問
## 総括
