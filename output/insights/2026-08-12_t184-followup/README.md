# [T-184] 追走 — 打ち切られた 5 job を上限を外して再走し、択一を再提示する

2026-08-12 のユーザー裁定 (第 4 束、測定先行 1c+2a+5a) 「追走 5 件 + CLI 版固定を先行、
sweep は不足時のみ、§17 は (c)」の執行。実装面差分ゼロ、repo 変更は docs のみ。

前 wave は `output/insights/2026-08-12_t184-stage-measurements/` (worklog 475)。

---

## 1. この測定が測るもの (estimand)

**原観測の censoring は解けない。** 資源上限は launcher が event 流を観測して外から kill する
外部強制であり、`tools/codex_worker_launch.py` の codex argv には 3 上限が含まれない
(argv は model / effort / sandbox / cwd / output / prompt のみ)。被験側は自分の上限を知らないため
上限を緩めても挙動は変わらないが、**再走は原 run の軌跡の続きではなく独立した別の 1 回**である。

測るのは次である。

> 同一 prompt bytes (sha256 一致)、同一 base commit、同一 CLI 版 (`codex-cli 0.146.0`)、
> 同一 model / effort / sandbox、submodule を当時の pin で初期化した木、
> **7 走並列という固定条件**の下で、3 上限を大きく緩めたときの当該 job **1 回**の消費量。

得られる観測は「原 run は cap を超えた」と「新 run はこれだけ消費した」の**独立した 2 事実の組**
であって 1 つの量ではない。`R_new` は `R_old` の推定値ではない。

## 2. 再現の同一性 (実測)

| 項目 | 確認方法 | 結果 |
|---|---|---|
| prompt bytes | receipt の `prompt_sha256` と file の sha256 | 5/5 一致 |
| job 識別子 | 生成 argv の `--job-id` と原 receipt | **7/7 完全一致** |
| base commit | replay worktree の HEAD から導出 | 7/7 一致 |
| CLI 版 | `--codex-bin` で 0.146.0 を pin、receipt の `codex_version` | 7/7 一致 |
| model / effort | base commit の `DW-O01` から launcher が導出 | 7/7 一致 |
| submodule | 当時の pin で初期化 | 5 worktree すべて |

打ち切られた t786 plan の prompt は **job dir に残っていなかった** (同 dir 93 file を全 hash して不在)。
codex rollout jsonl から復元して初めて `33599e9c...` と一致した。
**追走の一次資料が rollout にしかない場合がある。**

## 3. 実測 (第 2 走、7/7 有効)

投入 2026-08-12 21:21:00 JST、7 走 1 batch 並列。
cap = `max_model_calls=1000` / `max_cli_reported_tokens=2e7` / `max_wall_clock_s=14400`。

| cell | wave | 段/lane | 原打ち切り軸 | 原 calls | 追走 calls | 原 tokens | 追走 tokens | 追走 elapsed | 原 cap 比 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| A | t139-manifest-land2-s2 | consult/luna | tokens | 50 | 58 | 1,101,163 | **1,500,868** | 2,843 s | **1.50** |
| A2 | 同上 (repeat) | consult/luna | tokens | 50 | 61 | 1,101,163 | 368,744 | 701 s | 0.37 |
| B | t812-lease-self-renew | consult/luna | tokens | 41 | 26 | 1,017,768 | 229,641 | 1,076 s | 0.23 |
| C | t810-node-variance | consult/luna | tokens | 42 | 56 | 1,030,999 | 401,284 | 1,584 s | 0.40 |
| D | t756-trace-v2 | plan | calls | 100 | **100** | 419,857 | 795,087 | 2,296 s | 1.00 |
| D2 | 同上 (repeat) | plan | calls | 100 | 95 | 419,857 | 416,936 | 1,858 s | 0.95 |
| E | t786-docs-budget | plan | calls | 100 | **128** | 470,559 | 694,081 | 1,189 s | 1.28 |

**7 走とも `limit_trigger=null`・`codex_exit_code=0`・`metering_status=complete`・
`evidence_status=complete`。緩めた 3 cap のいずれにも当たっていない。**

`stop_reason` が `max_attempts` の 2 件 (A, A2) は成果物が validator を通らなかったもので、
資源上限とは無関係である (`limit_trigger=null`)。本測定は消費量だけを扱い、
受理判定を結論に使わない。

### 打ち切りが本物だった cell

- **E は 128 calls を要した** (原 cap 100)。原の打ち切りは「上限が足りなかった」で正しい。
- **A は 1,500,868 tokens を要した** (原 cap 1e6)。同上。

### 打ち切りが再現しなかった cell

- B (0.23)、C (0.40)、A2 (0.37)、D2 (0.95)、D (1.00) は原 cap 以下で完走した。
- **同じ cap で殺される走と余裕で終わる走が同一 prompt でも混在する。**

## 4. 最重要 — 上限軸そのものが不安定である

**A と A2 は同一 prompt・同一 base・同一 CLI・同一 batch の 2 走である。**

| 量 | A | A2 | 比 |
|---|---:|---:|---:|
| `model_calls` | 58 | 61 | **1.05 倍** |
| `cli_reported` | 1,500,868 | 368,744 | **4.07 倍** |
| `wall_clock_s` | 2,843 | 701 | 4.05 倍 |
| `cached_input_tokens / input_tokens` | 0.790 | 0.954 | — |

**やった仕事の量 (calls) はほぼ同じなのに、上限がかかっている量 (`cli_reported`) は 4.07 倍違う。**
`cli_reported = input_tokens - cached_input_tokens + output_tokens` が 5/5 の原観測で厳密に
成立しており (親が検算)、この軸は **cache miss 分だけを数える**。cache 比率が 0.790 と 0.954 で
違えば、同じ軌跡でも値は数倍動く。

**prompt bytes・base commit・CLI 版は pin できるが cache は pin できない。**

D と D2 でも同様に calls 1.05 倍に対し tokens 1.91 倍である。

**帰結:** `max_cli_reported_tokens` に段別の値を置くことは、**同じ仕事が走るたびに 4 倍動く量**に
線を引くことである。`max_model_calls` は同条件で 1.05 倍しか動かず、**仕事量の代理として桁違いに安定**
している。これは軸 4 (どの軸を段別化するか) に直接効く実測である。

## 5. 事前登録した sweep 発火条件の判定

段 4 で凍結し、結果を見る前に固定した 4 条件。

| | 条件 | 実測 | 判定 |
|---|---|---|---|
| (i) | 2 走以上が 3 cap のいずれかに再度当たった | 0 走 | 非発火 |
| (ii) | 完走した cell が 1 つも無い | 7/7 完走 | 非発火 |
| (iii) | repeat 対の `model_calls` または `cli_reported` が 2 倍以上ずれた | **A/A2 の tokens が 4.07 倍** | **発火** |
| (iv) | treatment 不一致による無効化が 1 件以上 | 0 件 (第 2 走) | 非発火 |

**(iii) により sweep が発火した。** ただし発火の中身は「必要量が測れなかった」ではなく
**「上限軸が run 間で不安定であることが測れた」**である。

### 事前登録した sweep 設計 (本 wave では走らせない)

段 4 で結果を見る前に凍結したもの。

- 対象: 発火 cell と同じ (段, lane, model) の組。consult/luna と plan/sol の 2 層。
- 水準: 打ち切り軸を原既定の 1x / 2x / 4x / 8x の 4 水準。他 2 軸は緩和値で固定。
- 各セル 1 走、層あたり 4 走、最大 2 層 = 最大 8 走。
- 停止規則: ある水準で完走したらその層の上位水準は走らせない (最小完走水準を探す)。

**本 wave の終端は択一の再提示であり、sweep は独立した測定である。** ユーザーの発令を待つ。
なお §4 の結果を受けて、**sweep を token 軸で回す価値は下がった** — 不安定な軸の閾値を
精密化しても意味が薄い。回すなら calls 軸を推す。

## 6. 事故 — 第 1 走が並行 session の cleanup で汚染された

第 1 走 (20:41:24 投入) は **20:57:55 JST に追走 worktree 5 本を削除され**、7 走中 6 走が
走行中に working directory を失った。cell B のみ削除前 (20:53:11) に完了して無傷。

削除を行った並行 session (worktree debris cleanup) から申告があり、双方の実測が一致した。

**2 層の原因がある。**

1. **生成側**: `.claude/worktrees/` の detached HEAD・未施錠・main の祖先・dirty ゼロは
   残骸の 4 条件をすべて満たす。作成 20:18:15〜20:21:28 の 5 本が、その直後のユーザー棚卸しで
   path + SHA 付きの残骸リストに載っていた。
2. **検出側 (本命)**: cleanup の生存判定 `/proc/*/cwd` 全走査は **launcher 型の子を
   構造的に検出できない。** `codex_worker_launch.py` の cwd は**起動元** (親 wave の worktree)
   であり、操作対象 worktree は `--repo-root` / `--cwd` / `--artifact-dir` として
   **argv にしか現れない。**

**独立検算 (2026-08-12 21:28、稼働中の第 2 走で実測):**
`/proc/*/cwd` に追走 worktree が現れる process = **0 件**、`/proc/*/cmdline` = **14 件**
(launcher 7 + codex 本体 7)。検出された launcher の実 cwd は親 wave の worktree だった。
掃除側の同時刻の観測と独立に一致した。

**`git worktree lock` は必要だが十分ではない。** lock が止めるのは `git worktree remove` であり、
実際に使われた `rm -rf` + `git worktree prune` の手順は lock を見ない。

### 汚染は receipt からは見えない

汚染 6 走の receipt は `codex_exit_code=0` / `metering_status=complete` /
`evidence_status=complete` / `limit_trigger=null` のまま残った。**値だけ見て気づくことはできない。**
検出できたのは rollout の逐語だけである。

- `exec_command failed for '/bin/bash -lc pwd': ... Rejected(...)` (11:57:54Z〜11:58:03Z)
- `rg: external/ccbench/common/runner.cc: No such file or directory` (11:57:59Z)

**削除時刻 20:57:55 と、汚染初発 20:57:54〜20:58:06 が秒単位で一致した。**

### 汚染の効果量 (同一 cell の 2 走比較)

| cell | run1 (汚染) calls | run2 (施錠) calls | run1 tokens | run2 tokens |
|---|---:|---:|---:|---:|
| A | 79 | 58 | 432,644 | 1,500,868 |
| B | 20 | 26 | 180,804 | 229,641 |
| C | 40 | 56 | 394,664 | 401,284 |
| D | 81 | 100 | 500,754 | 795,087 |
| E | 65 | 128 | 322,139 | 694,081 |
| A2 | 50 | 61 | 466,572 | 368,744 |
| D2 | 91 | 95 | 379,766 | 416,936 |

**汚染は消費量を系統的に下振れさせた** (calls は 7 cell 中 6 cell で run2 の方が大きい。
E は 65 → 128 の 2.0 倍、D は 81 → 100)。汚染に気づかず報告していれば、
**上限を実際より低く見積もる提案**になっていた。

### 汚染判定器の誤検知 (自己訂正)

第 2 走の判定で当初 cell A を汚染と出したが**誤検知**だった。実体は
`rejected: rm -f style commands are not permitted` という sandbox の方針拒否であり、
worktree 消失ではない。`Rejected(...)` 単体を汚染の徴候に使ってはならない。
判定は `pwd` 自体の失敗と worktree 配下の file 消失に限定する。

## 7. この測定から言ってはならないこと

- 完走値を「必要量」「推奨 cap」と呼んではならない。各 cell は n=1 であり、しかも
  **原 run が cap に当たったことを条件に選別されている** (regression to the mean)。
- 5 cell を pool して「consult と plan の共通必要量」と言ってはならない。
- consult と plan の差を**段の効果**と言ってはならない。段・lane・model・base commit・prompt が
  すべて交絡しており、本追走はこの交絡を解かない (原の偏りを同じ比率で再現するだけ)。
- 原観測で wall 発火 0 件だったことから「wall は不要」「余裕がある」と言ってはならない
  (3 軸同時上限下の competing risk)。
- 0.146.0 の固定から現行 CLI (0.147.0 以降) への転移を言ってはならない。
- 7 走が完走しても未観測の対象に sweep が不要とは言えない。
- p95・分布・因果帰属を出してはならない。

## 8. 限界

- **n=1 が 5 個** (共通分布の n=5 ではない)。repeat 対は同一 batch 内の replicate 変動であり
  一般的な分散ではない。
- **並列度 7 が固定条件**である。「calls / tokens は輻輳非依存」とは主張しない。
- 追走 worktree は当時の path 名で再作成したが**当時の worktree そのものではない**。
  prompt が名指しする絶対 path 14 種はすべて解決することを確認した。それ以外の環境差は測っていない。
- backend 側の版・seed・system instruction・tool surface の drift は pin できない。
- 集計器は repo 外にあり、テストを持たない。

## 9. 成果物影響 (DW-G05)

**certified な選択結果・材料レポート・試行台帳の値は 1 bit も変わらない。** 資源上限は
correctness 判定・受理集合・proof chain のいずれにも関与しない。これは前 wave §15 で確定済みの
不変条件であり、**本追走の値から新たに証明したものではない。**
追走 job は全件 `read-only` sandbox で走り repo を書き換えていない。

## 10. 択一の再提示 (5 直交軸)

軸の定義は前 wave §13 を継承する。**本 wave は択一を決めない。**

### 軸 1 — いつ決めるか

| | 選択肢 | 本追走がどう関わるか |
|---|---|---|
| 1a | 今決める | token 軸の不安定性が測れた。calls 軸なら今決められる |
| 1b | [T-183] 完了後へ延期 | 変化なし |
| 1c | **測定先行 (現行裁定)** | 追走は完了した。sweep が (iii) で発火したが、§4 により token 軸 sweep の価値は下がった |

### 軸 2 — 権威をどこに置くか

変化なし。**2a (権威を置かない) を維持する理由は強まった** — 上限軸が run 間で 4 倍動く以上、
docs 権威で値を固定して hash 束縛する意味が薄い。

### 軸 3 — 既定の形

| | 選択肢 | 本追走がどう関わるか |
|---|---|---|
| 3a | 全段共通の単一既定 | 変化なし |
| 3b | 段別の既定表 | **段への帰属は依然できない** (交絡は解けていない) |
| 3c | 既定なし・明示必須 | 変化なし |

### 軸 4 — どの軸を段別化するか (**本追走が最も動かした軸**)

| | 選択肢 | 本追走がどう関わるか |
|---|---|---|
| 4a | 3 軸すべて | wall は 306 走で 0 件発火のまま |
| 4b | `model_calls` と `tokens` だけ | **`tokens` を段別化する根拠が弱まった** — 同一 prompt・同一 batch で 4.07 倍動く |
| 4c | 段別化しない | 変化なし |
| **4d** | **`model_calls` だけ** (新設) | calls は同条件で 1.05 倍しか動かず、E が 128 > cap 100 を実測した。**仕事量の代理として安定** |

**軸 4 に選択肢 4d を追加する。** これは本追走が生んだ唯一の新しい選択肢である。

### 軸 5 — 親の override

変化なし (5a 現状 / 5b 理由の記録 / 5c 禁止)。

### 親の推奨

**1a + 2a + 3a + 4d + 5a。**

- **4d (`model_calls` だけ)**: 本追走の唯一の強い実測。calls は同一 prompt の replicate で
  1.05 倍しか動かず、token は 4.07 倍動く。**安定な軸にだけ意味のある上限を置く。**
  token 軸は安全網として単一の大きい値に残し、段別化しない。
- **3a (単一既定を維持)**: 段への因果帰属は本追走でも解けていない。段別表を作る根拠がない。
  前 wave の親推奨 3b から**後退させる** — 交絡が解けていない以上、段別化は誤った軸で切る危険がある。
- **1a**: calls 軸に限れば今決められる。token 軸の sweep を待つ必要はない (§5)。
- **2a / 5a**: 変化なし。

**この推奨が誤りうる点:** `model_calls` の安定性は repeat 2 対 (n=2) の観測にすぎない。
4 対以上で 1.05 倍が保たれるかは測っていない。また E の 128 は n=1 であり、
「plan は 128 で足りる」ではなく「この 1 回は 128 だった」である。

## 11. §17 (c) の実装と、その限界

前 wave §17 の裁定 (c) に従い、`docs/README.md` の地図へ `codex_worker_launch.py` が書く
`receipt.json` の所在と主要 field を追記した (`check_docs.py` rc=0)。

**これは navigation pointer であって resource authority ではない** (authority を置けば 2a と衝突する)。
**「dev-wave の探索欠陥を解消した」とは書かない** — 同追記は `docs/dev-wave/**` の読み込み導線には
乗らないため、次の wave が地図を読まなければ再び自力探索になる。マシン固有の絶対 path は書いていない。

## 12. 本 wave が発行していないもの

- canonical stage matrix — 発行していない
- 起動前 policy — 発行していない
- retry policy — [T-183] 依存のまま、触れていない
- cap sweep — 設計を事前登録したが**走らせていない**
- 0.147.0 対照走 — scope 外として実施していない (転移の測定案として択一へ返す)

したがって [T-316] / [T-665] / [T-662] の待ちは解除されない。
