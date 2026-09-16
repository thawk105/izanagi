# 床値 official の予算承認 — ユーザーが決めること

この文書は、`output/s8b-freeze-budget-approvals/g1.json` の承認をユーザーが行うために、
AI 側が用意できるところまでを整理したものである。裁定の正本は D1161、
承認の表し方の正本は D287 である。

## 1. この文書が扱うもの・扱わないもの

扱う: 何が塞がっているか、誰が何を決めるか、決めるための根拠の在り処、決めた後の手順。

扱わない: 予算数値の確定、承認 JSON の発行、`BUDGET_APPROVAL_SHA256` の設定、
official campaign の起動。これらはこの文書では行わない。

## 2. いま塞がっているもの

**2026-09-17 追記: 下記 2 つの関門は 2026-09-05 に閉じた** (`g1.json` が置かれ、`BUDGET_APPROVAL_SHA256`
は同 file の sha256 と一致する)。§3 の「現時点でいずれも不在」も 2026-09-16 の official 走行と
2026-09-17 の候補生成で解消した。以下は承認前の記述として残す。

承認が効くまでに閉じている関門は 2 つある。

1. 承認 JSON が `output/s8b-freeze-budget-approvals/g1.json` に**存在しない**。
2. `orchestrator/campaign/s8b_holdout_freeze.py` の `BUDGET_APPROVAL_SHA256` が `None` である。

2 番目は入力を読む前に拒否する。つまり承認 JSON を置いただけでは関門は開かない。
これは設計どおりであり、D287 が「承認前は機構全体が動かない」と定めた形である。

## 3. 承認がどこで使われるか

この承認 artifact を読むのは `build_v2_g1_candidate` **ただ 1 つ**である。
床値 campaign の起動側 (`s8b_floor_campaign.py`、`s8b_budget.py`、`s8b_oracle_driver.py`) は
この artifact を読まない。

したがって承認は、床値 official campaign の**起動**を塞いでいるのではなく、
official 実行の**後**に行う再凍結 (v2 candidate の生成) で使われる。

さらに `build_v2_g1_candidate` は、承認とは別に次を要求する。現時点でいずれも不在である。

- official の path 規約を満たす `result.json` (`output/env/<env>/calibration/s8b-floor-official/...`)
- 同じ run の `manifest.json` と `journal.jsonl`
- それらと protocol・v1 freeze・build admission の整合、`eligible_for_refreeze` が真であること

つまり**承認を確定しても、それだけで v2 candidate が作れるわけではない。**
D1161 の「残る閂は承認 1 件」は、ユーザーが負う最後の**判断**が承認 1 件である、という意味で
読むのが実装と整合する。

## 4. ユーザーが決めること

決めるのは**予算の数値**である。承認 JSON に入る値は次の 3 つで、
`per_holdout_bench_s` の対象は `rr20` と `rr80` の 2 つである。

```text
total_bench_s
per_holdout_bench_s = {rr20, rr80}
oracle_shared = true
```

### 根拠の在り処

`output/insights/2026-08-24_t986-budget-approval-package/README.md` が根拠一式を持つ。
とくに次の節を読むと判断できる。

- §2 量の対応関係 — 承認上限 `B` と、実行時に実際に効く予約 `R` は別物である
- §5 見積り式 — `n=8` を仮定した場合の値
- §6 不確実性 — なぜ今の証拠では数値を確定しにくいか
- §10 数値の択一

### 3 つの択一と現時点の状況

| 択 | 値 (total / rr20 / rr80) | 状況 |
|---|---|---|
| 保留 | — | T-986 の推奨。現証拠で支持されるのはこれ |
| 上げる | 2592 / 1296 / 1296 | 未裁定。planning 用の見積り値 |
| 名目に合わせる | 2400 / 1200 / 1200 | 未裁定。実行時予約と同じで余裕がない |

**この 3 つはまだ裁定されていない。** D964 は依存物の運搬、D979 は観測回数の上限、
D926 は承認の束縛方式を決めた裁定であり、いずれもこの数値を承認していない。

保留が推奨される理由は「数値が誤りだから」ではない。
pilot で測った 1 session の所要時間と、実行時に積算される時間が同じ量だと示せていないこと、
および承認上限を上げても実行時の予約は名目値のままで余裕が使えないことによる。

## 5. 手順

AI は骨組みの生成と検証までを行う。承認者欄と数値はユーザーが書く。

1. 骨組みを出す (AI でもユーザーでも実行してよい)。

   ```text
   python3 tools/s8b_budget_approval_preflight.py skeleton --out <repo の外の絶対パス>
   ```

   出力には承認者・日時・数値が入っていない。これは承認ではない。

2. ユーザーが承認者名・日時・決めた数値を書き込む。

3. 書いたものを検証する。

   ```text
   python3 tools/s8b_budget_approval_preflight.py verify --candidate <path>
   ```

   この命令は**何も書き換えない**。形式・値・holdout の対応を検査し、
   通れば内容の sha256 と、`BUDGET_APPROVAL_SHA256` に入れる行をそのまま表示する。

4. ユーザーが承認 JSON を `output/s8b-freeze-budget-approvals/g1.json` へ置き、
   表示された行を `s8b_holdout_freeze.py` に反映し、**差分を自分で読んで commit する。**
   この commit が承認の実体である (D287)。

5. `build_v2_g1_candidate` を使う段では、承認 JSON と同じ数値を持つ budget 文書を別に用意し、
   `--budget <path>` で渡す。両者は 1 byte も違ってはいけない。

## 6. AI が行わないこと

- 承認者欄を埋めない (D1161)。
- 承認 JSON を canonical な path へ発行しない (D287)。
- `BUDGET_APPROVAL_SHA256` を書き換えない (D287)。
- 予算数値を確定しない。tool にも既定値や候補値を持たせない。

`s8b_budget_approval_preflight.py` には承認者を受け取る引数が無く、
環境変数・git 設定・既存の凍結記録から承認者を補う経路も持たない。

## 7. 限界

ここで言えるのは「承認者が対話以外の経路から入り込まないこと」「数値に既定値が無いこと」
「置かれた内容が形式として正しいこと」までである。
検証 tool と被検証対象を同じ主体が変更できる以上、これは意図的な改変への完全な防壁ではない
(D387、D1128)。事故的な誤りは検出できるが、そう書くに留める。
