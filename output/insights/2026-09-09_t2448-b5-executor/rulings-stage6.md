# 段 6 裁定 — [T-2448] 軸 B5 の実行器

段 6 の敵対レビュー 2 本 (A = 正しさ境界、B = 実効性と整合) と、親の実走で出た所見を裁定する。
親が現物で裏を取ったものだけを must-fix にした。

## 0. fix を 1 単位にする理由 (DW-S06-B)

所見が file を跨いで絡む。とくに OpenAlex の期待 AST は `runner.py` の builder、単位 A の合成 fixture、
両 test file の 3 面に同時に効く。所有を割ると境界が壊れるので、**fix は 1 単位が B5 の全 path を所有する。**

## 1. must-fix (production の欠陥)

| # | 所見 | 出所 | 裁定と修正方向 |
|---|---|---|---|
| F1 | directory exact set 検査が `__pycache__/*.pyc` を余分な path と数え、一度でも import した環境では registration preflight が必ず落ちる | **親の実走** | **real。** `.gitignore` の 2 行目が `__pycache__/`。worktree 走査から `__pycache__` directory と `*.pyc` を除く。commit tree 側には元から現れない |
| F2 | arXiv の日付 delimiter 正規化が `[...` と `..."` の混在形も正規形へ丸める | レビュー A | **real。** 凍結文が許すのは角括弧と二重引用符の差だけ。balanced な 2 形だけを照合し、混在を不一致にする |
| F3 | OpenAlex の期待 AST の形が実応答の形と一致しない | レビュー B | **real。ただし修正先は builder ではなく fixture と test。** 親が正本を確認した — 条件 1 の OpenAlex 節は `2026-09-02-axis1-search-amendment.md` §3 を軸 B5 へそのまま当てる規則で、その登録構造は `{"get_rows": ..., "filter_rows": [{"column_id": ..., "value": ...}, {"join": "or", "filters": [...]}]}` である (`orchestrator/axis1_search/catalog.py:325-353` が同じ形を作る)。**`runner.py` の builder は正しい。** 単位 A の `openalex_cursor_page_1.json` などが使う `{"title_and_abstract.search": "backoff"}` の直接 key 形が誤り。fixture を登録構造へ直し、test の期待も揃える。**`get_rows` は軸 B5 の登録どおり文字列 `"200"` のままにする** (軸 1 の `"works"` へ寄せない) |
| F4 | `B5-CTL-AND2023@openalex` の期待 AST が catalog 共通の 2026 cutoff になる | レビュー A | **real。** 閉包登録が固定する当該 control の値は `2023-12-31`。runner 側でこの control だけ凍結 literal の cutoff を使う。**catalog は変更しない** |
| F5 | `evaluate_live_preflight` が公開 seam で、呼び手が作った record から `may_start_run=True` を作れる。loader は record 内部の整合を見ない | レビュー A | **real。** 集約器を production の公開面から外して test-only の private seam にする。加えて loader は、各 `収録` が status・media type・transport error 不在・索引別の観測形と整合することを確かめる |
| F6 | seal が任意の `repo_root` を束縛するだけで、実際に import された module がその root 配下かを見ない | レビュー A | **real。** `catalog` / `parsers` / `preflight` / `runner` の `__file__` が `repo_root` 配下の対応 path と一致することを seal 成功条件にする |
| F7 | live schema に複製された `registration_seal` 定義が standalone schema より弱い | レビュー B | **real。** 複製定義を standalone と同じ制約へ揃える。production の出力は変えない |

## 2. must-fix (test の検出力)

これらは親が事前登録する変異の対象そのものなので、fix に含める。

| # | 欠けている検査 | 出所 |
|---|---|---|
| T1 | 期待 AST の正例が production builder の出力同士を比べており恒真。凍結文から独立に書いた literal AST で照合する (F4 の 2023 control を使う) | A |
| T2 | registration の正例が、実行器本体を 1 つも含まない fake root を通す。実 module path を要求する正例にする (F6 と対) | A |
| T3 | OpenAlex の cursor 終端 (条件 3 の `next_cursor` 不在) を検査する test が無い | A |
| T4 | live preflight の負例に `非収録` が無い (30 件中 1 件だけ `非収録` の構成) | A |
| T5 | 本走の fail-closed を `issue_run_request` 直呼びでしか見ていない。**production 入口 `run_leaf` を通す** test を置く | A・B |
| T6 | 成功側の `run_live_preflight` が未実走。transport seam で 30 応答を返し、30 request・schema-valid な durable record を確かめる | B |
| T7 | 部分最終 page の正例が条件 2 で落ちる fixture を使っており、6 条件すべてを通る統合正例が無い | B |
| T8 | retry delay の test は定数凍結 test であることを名前か docstring で明示する (実効 retry test を名乗らない) | B (nit だが名乗りの誤りなので直す) |

## 3. 受入所要台帳

新規 54 nodeid が未登録。**親が正本 runner で作った JUnit** を使い、
`tools/update_acceptance_duration_ledger.py --add-only` で一度だけ追加する。手書きの秒数を書かない。
JUnit: `/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/junit-b5.xml` (54 件・失敗 0)。
**fix で test が増減したら、親が JUnit を取り直してから台帳を更新する。**

## 4. 不採用 (refuted / scope 外)

- 本走 HTTP request を出せる公開 bypass は無い (レビュー A が公開面 43 名を数えて確認)。production 修正不要。
- `capacity_echo`・短い非最終 page・総数 drift・cursor 終端に、他の受理拡大経路は無い (A)。
- README の pytest allowlist 追加は不要。両 file とも自走 harness を持つ (B)。
- W-ID drift・`capacity_echo` 一致・control 発火を拒否 gate にしていないことを確認 (A)。裁定どおり。
- レビュー B の「凍結原文との 1 文字比較は判定不能」は正しい自己申告。**親が別途 anchor 16 件の DOI と
  W-ID、member 集合 16/1/13 を凍結記録の表から独立抽出して照合済み** (全件一致)。

## 5. 変異の事前登録 (更新)

レビュー B の帰属判定を容れ、次を probe 先行で登録する。位置は fix 後に確定する。

| id | 変異 | 帰属の見込み |
|---|---|---|
| m01 | OpenAlex の初回 cursor を literal `*` から `%2A` へ | B が「行単位へ具体化せよ」と指摘。request builder の該当行 1 箇所に限定する |
| m02 | 期待 AST の children を set 化 (多重度を落とす) | T1 の独立 literal test が単独で赤になる |
| m03 | live preflight の `all(収録)` を `any` へ | 29 収録 + 1 不達で単独 |
| m04 | 総件数 drift を最終 page の値で受理 | 3 page 構成で条件 5 へ帰属させる |
| m05 | 条件 3 の実要素数を `capacity_echo` に差し替え | 単独 |
| m06 | 本走発行の fail-closed を外す | T5 の `run_leaf` 経路 test と対 |
| m07 | seal の directory exact set を部分集合検査へ緩める | 単独 |
| m08 | DBLP の cutoff 判定を落とす | 行単位へ具体化する |
| m09 | 3 値に入らない応答を `収録` へ丸める | 行単位へ具体化する |
| m10 | OpenAlex の判定順序を content type 先行へ入れ替える | 単独 |
| m11 | `G2-08` の主キーを arXiv ID にする | **registry と自己検査 literal を同時に変異させないと loader 全停止へ帰属が崩れる** (B)。両層変異として kill 期待を事前登録する |
| m12 | retry delay の `6.0` を `7.0` へ | 定数凍結 test の検査に留まることを明記する |
| m13 | `__pycache__` の除外を外す (F1 の回帰) | 実 repo を走査する test が要る。T2 と対 |
