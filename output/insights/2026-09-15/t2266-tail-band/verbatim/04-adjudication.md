# 段 4 裁定 — [T-2266] 静的 backoff tail の残帯

親が段 2 の plan と段 3 の敵対相談 2 本 (sol / luna) を裁定する。
段 4 直前に local main を再確認した — `0600887d9` から動いていない。裁定 inbox の新規更新なし。

## 1. (P1') の判定 — 帯の測定に研究前進は無い (確定)

sol と luna が独立に探索し、**901〜998 マイクロ秒の測定値を必須入力とする既存の consumer・主張・
図表・事前登録は 1 つも見つからなかった。** sol の探索範囲は `docs/paper-story/`、
`docs/paper-story-backoff/`、`docs/decisions.md`、事前登録文書、`output/insights/` の Markdown で、
帯に触れる箇所はすべて「未取得である」という限界の記載であって「測る必要がある」ではない。
`tools/t2216_backoff_walk_model.py:53` と `tools/plotting/plot_t2266_tail_mechanism.py:38` の較正は
既存 6 点と schema v1 に固定されており、帯を要求しない。

**sol は (P1') が反証型 (d) — 依頼が帯を明示している — でだけ倒れると判定した。親はこれを採用する。**
すなわち帯を測る理由は研究上のものではなく、依頼がそう書いているという理由だけである。

## 2. (P2) の判定 — 2 つの指定は現行契約下で同時に満たせない (確定)

plan・sol・luna の 3 者が独立に確認した。名指された `b10_backoff_static_tail_formal.py` は
事前登録の bytes から格子を再生成し (`:148`)、spec から測定点を得る (`:245`)。格子を差し替える
引数は CLI に無く (`:777`)、事前登録 §8.2 は定数置換を禁じている。**帯はこの driver では測れない。**

## 3. 採る O — O-C (未投入の `t2500-tail-formal` 本走を投入・回収する)

**採用理由。**

- 依頼は「本題の実測だけ」と書いている。O-C は**実装面の差分ゼロ**で、依頼が名指した driver を
  そのまま使う。O-A は新しい登録系列 (専用 schema / stem / identity) を submit 入口・job 側受理・
  argv 転送・完了確認・binary 相異検査まで配線する実装 wave になる (sol 所見 8)。
- O-A が作る成果物を読む consumer は存在しない (§1)。帯を測っても、その値は
  どの主張・図表・model にも入らない。
- O-C は事前登録済みの飽和判定を進める。これは B-10 で実際に止まっている研究であり、
  driver も投入経路も着地済みで一度も走っていない。
- 計算資源の側から見ても、いま queue が空いている。

**採らない理由を明示する (依頼の不履行を隠さない)。**

sol 所見 1 を real / must-fix として採用する。**O-C は依頼された帯の測定を代替しない。**
本 wave は 901〜998 マイクロ秒を 1 点も測らない。これを T-2266 の完了、帯の測定済み、
B-10 の完了として記録しない。段 7 の記録と最終報告に、測らなかったことと理由を明記する。

**帯を測りたい場合に必要なもの (裁定パッケージとしてユーザーへ返す)。**

D1848 の形に従い、凍結格子へ点を足さず第 5 の RUN_KIND と専用 campaign identity を作る。
最小形は帯の内部 1 点 (例 950 マイクロ秒) を 3 workload で測る専用系列で、
`tools/pegasus/submit_b10_backoff_grid.sh` の受理集合、`tools/pegasus/b10_backoff_grid.sh` の
job 側受理と argv 転送と完了確認、`orchestrator/campaign/backoff_extended_sweep.py` の
第 5 種別と専用 schema / stem、binary 相異検査の接続、テストが要る。**これは実装 wave であり、
本 wave の「本題の実測だけ」という scope には入らない。**

## 4. 所見の裁定

| # | 出所 | 判定 | 採否 | 成果物影響 (放置時) |
|---|---|---|---|---|
| 1 | sol 1 | real / must-fix | **採用** | 帯の標本がゼロのまま。記録と報告に未測を明記して閉じる |
| 2 | sol 2 | real / must-fix | **採用** | 未測が「解消済み」へ変わる。§3 のとおり未測と書く |
| 3 | sol 3 / luna 9 | real / nit | **採用** | 追補 §2 の 700→800 balanced は **−5.64%**、参照行は 56/58/59 と 90〜92。訂正済み |
| 4 | sol 4 / luna 1 | refuted | — | 親が独立に検算した。作業ツリーの prereg sha256 = `8084be04dc1fc6a78b0fa1ac4a16986add796945d8c4ecace86ed2df4c44a45a` は `cad6f46d8` の blob と一致、HEAD の祖先。初版 commit を渡した場合だけ止まる |
| 5 | sol 5 | refuted | — | 正しさゲートに緩む経路は確認されなかった。権威は `payload.certified is True`、anomaly 上限 0、異常を含む集団は `invalid` |
| 6 | sol 6 | real / must-fix | **採用** | report が出ない失敗 (外側締切・PBS kill・事前登録照合前の停止) を回収対象から落とさない。残存 WAL・stdout・receipt を回収して欠測と理由を記述する |
| 7 | sol 7 | refuted | — | formal report は専用 schema / stem で create-only。v1 consumer は受理しない |
| 8 | sol 8 | real / must-fix | **scope 外** | O-A を採らないので実装しない。§3 の裁定パッケージへ収容した |
| 9 | luna 2 | real / must-fix | **採用** | 出力親 `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal` は未作成。投入前に作る。放置すると qsub 前に終了し 3 job も標本も出ない |
| 10 | luna 3 | real / must-fix | **採用** | 「約 20 分/job」は見積りであって実測ではない。保証として扱わず、遅延を失敗と誤認しない |
| 11 | luna 4 | real / must-fix | **採用** | 外側 `timeout 11700` が driver 内タイマーより先に効く経路がある。締切に当たったら完走成果物だけを待たず、部分観測と理由を回収する |
| 12 | luna 5 | real / must-fix | **採用** | 投入は clean tree で行う。走行中に repo へ書かない (草稿は job dir に置く)。子も起動しない |
| 13 | luna 6 | refuted | — | 別ノードというだけで集団が `invalid` になる構造ではない。T-2566 §2(a) の source token は追跡 source bytes の digest へ修正済み |
| 14 | luna 7 | refuted | — | 3 job の並行投入は runbook の典型。直列化は標本を改善せず queue 待ちを足すだけ |
| 15 | luna 8 | real / must-fix | **採用** | 部分失敗で submit 全体を再実行しない。receipt の成功 request を先に照合し、同一性を保てないなら不完全 cohort を失敗として報告して止める。別 campaign の cell を継ぎ合わせない |
| 16 | luna 10 | refuted / nit | — | plan は qstat ゼロ行を裏取り不能と明記しており、それに依存していない。親は投入直前に queue を再確認する |

## 5. プラン v2 (親が実行する手順)

1. 出力親 `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal` を作る (repo 外・絶対 path)。
2. 投入直前に queue と既存 receipt を再確認し、既投入の formal cohort が無いことを実測する。
   あれば回収へ進み、重複投入しない。
3. **clean tree のまま** repo root (= wave worktree) から 1 回だけ投入する。
   - `--run-kind t2500-tail-formal`
   - `--preregistration-commit cad6f46d86ae4dc31edadfbdfad39c65ed73d70a`
   - `--explore-campaign /work/1/SFC/tanab/b10-backoff-grid-t2418-explore/b10-backoff-grid-20260908T193601Z-2540578-write-heavy/campaigns/t2418-backoff-static-explore-v1-silo-write-heavy-sweep-c9cea61a`
   - `--output-parent /work/1/SFC/tanab/b10-backoff-grid-t2500-formal`
4. group id・job id・receipt を記録する。走行中は repo へ書かない。草稿は job dir に置く。
5. 3 job の `completion.json` を確認する。出ない job は残存 WAL・stdout・receipt を回収し、
   欠測と理由を記述する。格子・rep を削って救済しない。
6. 集団報告を手順書 §4 の argv で 1 回だけ実行する。位置引数は campaign directory を 3 つ明示。
7. 記録 (段 7)。insight + spool fragment。受入全走。

## 6. 変異 matrix

**実装面 (D95 決定 2) の差分がゼロなので、`DW-S04` により変異 matrix を免除する。**
Python・shell・実行 bit 付き file・symlink・機械設定を 1 つも足さない。
**受入全走は免除しない。**

## 7. 段の遷移

実装しないので段 5・6 を飛ばし、`4 → 7 → 8 → 9` とする。実測は段 7 の記録の前に親が行う。
