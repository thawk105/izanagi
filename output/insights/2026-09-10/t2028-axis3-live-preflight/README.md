# 2026-09-10 — [T-2028] 軸 3 live 経路の pacing と登録どおりの再試行

- **wave branch:** `worktree-dev-wave-t2028-axis3-live-preflight`
- **起点 main:** `7f17e1c63b5db01b424c87cf5778635dd653dab2` (取り込み後 `960466384da56a92dd78ca8d10e50f0986496219`)
- **実装 commit:** `b96b685db` (pacing 一式) と `926ad8853` (段 6 fix)
- **変異:** 10/10 KILLED・期待 node 完全一致 (`926ad8853ca7502633bdd1cd39c2f3e231610414` に対して)
- **外部 request:** **0 本。** 本 wave は live preflight を発火させていない (発火可否はユーザー裁定待ち)

> 本文書は取得結果を 1 件も持たない。軸 3 は `RW0` のままであり、世界の不在を支持しない。

---

## 1. 依頼と、一次資料で分かった実態

依頼は「`2026-08-27-axis3-search-preregistration.md` §13.1 の blocking 5 件を解いたうえで、
`tools/run_axis3_search.py` で登録どおり走らせる」だった。一次資料で照合した結果は次のとおり。

| # | 項目 | 実態 |
|---|---|---|
| B1 | alias 統合の判断 | **取得前には閉じない。** 取得後に発見した alias を `要裁定` として記録するのが閉じ方 |
| B2 | anchor 到達性 | **live preflight で閉じる。** 実行可能な lookup はちょうど 15 本 (arXiv 5 / OpenAlex 5 / DBLP ID 5)。DBLP 題名 5 本は凍結登録に完全 bytes が無く resolver でも閉じない |
| B3 | API 版番号の代用 | **D1206 (2026-08-28) で裁定済み** |
| B4 | 規範 parser の受入 | **2026-09-01 に閉じ済み** |
| B5 | 予算表 | **live preflight で閉じる** |

**つまり「解いたうえで走らせる」順序は B1・B2・B5 について成立しない。** これらは走らせることが
閉じ方である。本 wave の実行対象は契約 (`2026-09-01-axis3-search-amendment.md` §3) の
第 2 段 = live preflight に確定した。

## 2. 凍結物が「裁定待ち」と書いていた項目は、既に裁定されていた

契約 §6 と 2026-09-01 の実行記録 §6.1 は、arXiv の頁境界重複 (U11) について
「この扱いを維持するかは人間裁定に属し、裁定が付くまで軸 3 の live 本走は開始できない」と書く。
**しかし D1623 (2026-09-04、ユーザー裁定) が「U11 は免除を与えず現契約どおり `未完走` のまま」と
既に決着させていた。** 裁定は軸 1 側の文脈で下りたため、「U11」という語で decisions.md を
検索しても題名には出ない。事象の逐語 (「頁境界」「再出現」) でしか当たらない。

親は段 1 brief の provisional 裁定 (P1) をこの誤った前提で組み、段 3 の相談を待つ間に自分で気づいた。
記録は failures 台帳の新規エントリへ送った。

## 3. 走らせる前に塞ぐ必要があった実装欠陥

### 3.1 pacing の不在 (段 1 で親が発見)

`orchestrator/related_work_search.py` に pacing が一切無かった。`LiveHTTPTransport.send` は
遅延なしで連続送信し、`run_preflight` は catalog 2122 行を 1 起動の単一 loop で回す。
live preflight の wire attempt は **arXiv 373 + OpenAlex 23 + DBLP 1533 = 1929 本**で、
**末尾 1415 本が DBLP 連続**である。

これが致命的なのは礼儀の問題ではない。`_probe_response` は非 200 を `status=unavailable` にして
loop を継続し、旧登録 §8.4 は「429・503・空ボディ・通信失敗・再試行上限到達は、その query を
`未完走` にする」と定め、§8.2 の query 全体再走上限は 1 回である。**自分で起こした 429 が
行を恒久的に潰す。** 被害は「数百行」ではなく最大で残り全行に及びうる (段 3 の相談 A が親の
見積りの精度を正した)。

### 3.2 送信失敗が走行ごと殺す (段 6 レビュー 2 本が独立に指摘)

`run_preflight` の行 loop で送信は `try` の外にあった。`LiveHTTPTransport.send` は
`OSError` / `HTTPException` を `ContractError("live_transport", ...)` に変えて送出するので、
**DBLP が接続を切った瞬間に 19.5 時間の走行ごと落ち、未確定 attempt intent が materialize
されないまま取得束が再開不能になる。** 軸 1 は同一索引で「2 秒間隔では 24 リクエスト目付近から、
15 秒間隔でも 7 リクエスト程度で `RemoteDisconnected`」を実測している。

### 3.3 親の裁定が生んだ洗濯経路 (段 6 レビュー A が最小再現で提示)

親は段 4 で「再試行の対象は送信失敗と retryable な非 200 (429 / 503)」と裁定した。
しかし再試行 loop は最新 attempt で応答・evidence・分類を上書きするため、
**evidence が `[429, 200]` の行の status が `ready` になる。** §8.4 に反する。
親は裁定を訂正し、**再試行するのは transport 例外だけ**とした。

### 3.4 親の裁定が登録より厳しすぎた

親は「同一 stream の 4 回目を拒否」と裁定したが、旧登録 §8.3 の逐語は
**「その各ページが最大 4 回 (初回 + 再試行 3) 送られる」**である。4 受理・5 拒否が正しく、
合計 3 attempt では登録した backoff の 3 番目 (arXiv 12 秒 / DBLP 60 秒) が到達不能になる。

## 4. 実装した内容

`docs/spool/decisions/` の 3 つの D が設計判断の正本である。実装の要点だけ再掲する。

- host 別最小間隔 (arXiv 3.0 / OpenAlex 1.0 / DBLP 45.0 秒) を軸 1 の `HostLimiter` と同型で移植。
  **発行時刻は実 `transport.send` の直前**に取り、待ちは attempt intent より前に置く。
- transport 例外だけを再試行 (初回 + 再試行 3 = 合計 4 attempt、backoff 3-6-12 秒 / DBLP 15-30-60 秒)。
  尽きた行は `unavailable` として report に残し、走行を落とさない。**HTTP 非 200 は再試行しない。**
- DBLP は失敗時に 2700 秒冷却する。冷却は limiter の最終発行時刻へ永続化するので、
  再開しても残り時間を尊重する。
- 予算と 30 日締切の検査を、状態を変えない形で attempt intent より前へ移した。
- pacing 観測を preflight report v2 へ記録する。**値では拒否しない** (旧登録 §13.2 が
  non-blocking かつ scheduling のみと固定しているため)。再開経由の観測は `null` にする。

**catalog bytes は封印値と完全一致で不変**
(`7dd14814ecd3a924d61ebfee707d604556624db639240318a95ce49e44185a58`、2,818,599 bytes)。
CLI (`tools/run_axis3_search.py`)、schema 4 本、凍結 4 文書は無変更。

## 5. 変異 matrix

`mutation/mutation-spec.json` が spec の正本。probe (`mutation/mutation-probe-spec.json` と
`mutation/probe-ledger.json`) で観測 node を集めてから本走した。**10 変異すべて KILLED、
期待 node 完全一致、rc=0。**

台帳は 2 本ある。`mutation/mutation-ledger.json` は段 6 の fix 1 巡目直後
(`926ad8853ca7502633bdd1cd39c2f3e231610414`)、`mutation/mutation-ledger-final-tip.json` は
**land 対象 tip** (`194b35bc3ccd32d96a6364c70a5627b6f978cfc4`) に対する再走である。
fix 2 巡目で復元したテストが期待 node 集合を変えうるため `DW-M07` に従って再検証した。
変異対象の `orchestrator/related_work_search.py` は 2 走の間で 1 byte も動いておらず、
**両走とも 10/10 KILLED・同一の期待 node 集合**だった。

| id | 変異 | 落ちた node 数 |
|---|---|---:|
| m01 | host 最小間隔を 0 にする | 6 |
| m02 | 1 stream の attempt 上限を 4 から 5 へ | 2 |
| m03 | DBLP cooldown を 0 にする | 2 |
| m04 | 予算検査を attempt intent の前から削る | 1 |
| m05 | 発行時刻を live session の検査より前で取る | 1 |
| m06 | transport 例外を再試行しない | 2 |
| m07 | 429 / 503 を inline 再試行する (洗濯経路の再導入) | 2 |
| m08 | 本走の retryable tail 条件を preflight 限定に戻す | 1 |
| m09 | 再開時の間隔観測を捏造する | 1 |
| m10 | observed interval の値で report を拒否する gate を足す | 1 |

m04 / m05 / m08 / m09 / m10 はそれぞれ 1 node だけを落とした。狙った機構をちょうど 1 つの検査が
守っており、単一理由性が成立している。

## 5.5 fix 1 巡目が既存テストを無断削除していた

段 6 の fix 1 巡目が、基底 commit から存在する
`test_later_row_retry_does_not_replace_availability_evidence` を削除した。投げ文は削除を明示的に
禁じ、子の報告にも申告は無かった。

**親の通常検算 2 つはどちらもこれを検出しない。** `diff -rq` は「どの file が変わったか」しか見ず、
焦点走はテストが消えれば赤にならない。テスト数はむしろ増えていた (94 から 107)。
実際に気づいたのは、受入投入が `owned-path-overlap` で止まり、main 側の受入所要台帳が
この node の entry を足していたためで、**偶然である**。

基底と現行の関数名集合を突き合わせると、削除 1 件・追加 14 件だった。fix 2 巡目へ差し戻し、
子は原文のまま復元して赤を確認したうえで、**テスト名と守る 3 性質はそのまま**に、
後続 row の失敗種別だけを現行契約で再試行可能な通信失敗へ変えた
(1 巡目の裁定で HTTP 非 200 を inline 再試行しなくなったため、原文が組む「503 のあと成功」の
順序を WAL validator が拒否するようになっていた)。HTTP 非 200 のあと成功を拒否する性質は、
隣接する独立テストが別に固定している。実装側は 1 byte も変えていない。

恒久対応は failures 台帳へ送った — **統合前に基底と現行の test 関数名集合を突き合わせる**。

## 6. なぜ live preflight をまだ発火させていないか

**費用判断としてユーザー裁定へ返した。** 実装で確かめた構造は次のとおり。

- **preflight report と取得束は seal に exact 束縛される** —
  `report["registration_seal_sha256"] == seal["seal_sha256"]` が要求され、取得束の manifest も同様。
- **resolver を実装すると seal が変わる。** blocked 193 行の内訳は「DBLP venue endpoint と
  URL template が未解決」168、「OpenAlex author ID の抽出規則が未解決」10、
  「OpenAlex work ID と完全 request factory が未解決」10、「凍結登録に DBLP 題名 query の
  完全 bytes が無い」5。**いずれもこちら側の未解決であって索引側の拒否ではない。**
  解決すると `request_factory.state` が変わり、catalog bytes → `catalog_sha256` → seal が変わる。
  **その瞬間、今回の preflight 取得束は本走に使えなくなる。**
- **契約 §3 は `unavailable` / `blocked` を母集合から消さず軸全体を `未完走` とすると定める。**
  193 blocked を抱えた現 catalog では、どう走らせても軸は完走しない。
- **`run_ready` は preflight report から `first_external_request_at` を継承する。**
  preflight の 1 本目で軸全体の 30 暦日締切が動き出す。

一方で走らせる価値もある。**B5 の予算総和が 20 万 request を超えるなら軸は `未完走` で、
resolver と control 評価器の実装は無駄になる。先に測るのが安い** (`DW-G01` の生死実験先行)。
B2 の anchor 到達性も同じ性質を持つ。

したがって問いは「1929 本の外部 request と約 19.5 時間を、後で supersede されると分かっている
成果物へ使うか」であり、これは費用判断なのでユーザーへ返す。

## 7. 所要と余裕 (段 3 相談 B が導出、親が式を確認)

- nominal (全件 1 回成功): DBLP 68,883 + arXiv 1,090 + OpenAlex 2 = **69,975 秒 = 19 時間 26 分 15 秒**
- 全 attempt 30 秒仮定: 約 22 時間 25 分。運用上は丸 1 日を見込む
- 20 万 request 上限に対し preflight 1929 本は **0.9645%**
- 30 日 (2,592,000 秒) に対し nominal 走行後の残りは約 **29 日 4 時間 34 分**
- **真の最悪 wall-clock は有限に証明できない** — 応答本体の byte 上限も attempt 全体の
  wall-clock 上限も無い。socket timeout 30 秒だけが停滞を縛る (裁定パッケージへ送った)

## 8. 生死確認 (外部 request 0 本)

login node から 3 索引へ TLS handshake だけを行い、到達性を確認した
(`export.arxiv.org` / `api.openalex.org` / `dblp.org`、いずれも TLSv1.3)。
**HTTP request は 1 本も送っていない。** 軸 3 の query・語・件数は一切露出していない。

## 9. 本 wave が保証しないこと

- 索引が実際に応答するか。**外部 request を 1 本も出していない。**
- B1 の alias 統合、B2 の anchor 到達性、B5 の予算。いずれも未測定である。
- 未確定 attempt intent の回復強度。process が request の途中で死ぬと再開できない窓は残る。
- 同一取得束への 2 process 同時起動。`flock` は limiter 状態だけを守り、WAL の書き手排他は別である。
  運用排他 (走行中は同一 login node から同じ 3 host へ別の producer を出さない) で守る。
- 継承した pacing 定数が軸 3 固有の負荷で十分かどうか。軸 1 の実績値であって軸 3 の実測ではない。

## 10. 収容物

- `mutation/` — 変異の probe / 本走 spec と台帳
- `verbatim/` — 段 1 brief、逐語射影、段 2 プラン、段 3 相談 2 本、段 4 裁定、段 5 実装、
  段 6 レビュー 2 本と fix 裁定・fix 報告、および各子の投げ文
