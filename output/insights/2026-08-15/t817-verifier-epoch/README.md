# [T-817] verifier epoch — 実測台帳

wave: `dev-wave-t817-epoch` (2026-08-14 開始 / 2026-08-15 完了)
branch: `worktree-dev-wave-t817-epoch`
裁定の正本: `output/insights/2026-08-11_t817-verifier-epoch/verbatim/ruling-package.md`
(ユーザー確定、2026-08-12 /rulings 再裁定)

## 1. 何を入れたか

`campaign_verifier_epoch` を **v2 lock の既存 authority からの導出ラベル**として入れ、
「certified を名乗る受理集合」から E0 (現行 policy 未検証) 記録を外した。

| 値 | 意味 |
|---|---|
| `E1` | lock が v2 authority を持ち、その `contract_loader_blob_sha256s` が現在の enforcement source closure と exact 一致する |
| `E1-stale` | v2 authority を持つが blob map が不一致 |
| `E0` | v2 authority を持たない |

除外の適用点は**読み取り側の受理層 1 箇所**に集約した
(`artifact_admission.require_admitted_campaign`)。各 consumer は
`purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE` / `HISTORICAL_RAW` の**呼び出し方**で、
受理集合として読むのか歴史生値として読むのかを表明する。

新しい lock field、新しい JSON artifact、新しい凍結 pin、署名機構は**作っていない**。

## 2. 段 1 の実測が裁定文の欠けを埋めた

| # | 実測 | 値 |
|---|---|---|
| A1 | `campaign_verifier_epoch` のコード内出現 (着手前) | 0 件 |
| A2 | 実 campaign の lock 版数 | total 30 / v1 30 / **v2 0** |
| A3 | v2 lock の唯一の writer | `ident.py` の新規 campaign 経路のみ |
| A4 | v2 authority の中身 | enforcement source closure **exact 8 path** の blob SHA-256 |

**A2 は裁定文が明示していなかった。** 裁定パッケージは「v2 lock を持つ campaign については
bytes が既に pin されている」と書いたが、実 corpus に v2 lock campaign は 1 件も無い。
したがって **E0 = 既存 30 campaign 全部**であり、除外の母集合は P2-2 の 24 attempt に留まらない。
裁定の substance は覆らない (P2-5 の replay/guided/baseline が停止することを承知の上での選択)
が、適用面の広さが確定した。

## 3. consumer 分類は 16 経路

段 3 の敵対 2 レンズが独立に、[T-834] の挙げた 8〜10 経路に加えて
`s6_sort_sweep` / `s8a_trigger_sweep` / `backoff_sweep_report` /
`autonomous_trial_completeness` / p3 loop 群 / `tools/plotting/plot_backoff.py` /
`critic/online_digest` を発見した。全 16 経路に受理目的を表明させた。

取り込み後の全件集計 (実装子が AST で数え上げ、2026-08-15):
実呼び出し 65 件のうち production 16/16、test 48/49 が purpose を明示。
残る 1 件は purpose 必須を確認する意図的な `TypeError` 負例。

## 4. 変異 matrix

runner: `python3 tools/run_tests.py -rf orchestrator/tests/test_artifact_admission.py
orchestrator/tests/test_s8b_oracle_judge.py -p no:cacheprovider`
(`--runner-mode local`、`IZANAGI_TEST_NPROC=4`)
repo_head: `bc201a2f21e45596845c3375c1ce229c7cef0c75`
baseline: rc=0、赤 0 件

| ID | 種別 | 変異 | 結果 | kill node 数 |
|---|---|---|---|---|
| MUT-1 | negative | certified purpose の E0 拒否を削除 (wave 前の形へ戻す) | KILLED | 1 |
| MUT-2 | negative | 記録 map と現在 map の exact equality を key 集合比較へ緩める | KILLED | 1 |
| MUT-3 | both-layers | certified view の発行 token 検査と exact E1 検査を同時に外す | KILLED | 1 |
| MUT-4 | positive | 全 purpose で無条件拒否 (過剰拒否) | KILLED | 31 |
| MUT-5 | negative | epoch 判定を既存 admission の前段へ移す | KILLED | 8 |
| MUT-6 | negative | S8b judge の「E1 かつ certified_eligible」条件を削除 | KILLED | 2 |
| MUT-7 | negative | 歴史表示を現在 closure 依存にする | KILLED | 30 |

**7/7 KILLED、SURVIVED 0。**

負例の発火は合成でなく**実在 artifact** (`output/campaigns/p2-2-silo-read-heavy-enumerate-5ffcabad`、
v1 lock、現行 admission を通る) で示している。「既存 admission を通る記録が、新 gate だけで落ちる」
ことが恒真でないことの証拠である。

### erratum — 初回は probe だった (DW-M08)

`mutation-ledger-probe.json` / `mutation-spec-probe.json` が初回走で、
**MUT-4 / MUT-5 / MUT-7 が MISMATCH** だった。検出力の不足ではなく、事前登録した
期待 node 集合が不完全だったためである (登録 1 件に対し、実際の kill は 31 / 8 / 30 件)。

これは「新設 gate は後段の検査を先取りする」型である。gate が発火すると後段の loop が走らず、
`test_nontrigger_historical_campaigns_remain_admitted` の全 param のように、
一見無関係な既存テストが同じ分岐に依存し始める。段 4 の事前登録時点でこれを完全に列挙するのは
現実的でなく、`DW-M08` が許す「初回を probe と明記し、期待 node を完全集合として再登録して再走」
の手順で閉じた。baseline が完全に緑 (rc=0) であることが、観測 kill 集合を完全集合として
採用してよい根拠である。

## 5. main 取り込み (69 commit) で 1 件の衝突と 3 件の穴が出た

引き継ぎ後に local main `22c13a04` → `330f67d0` を取り込んだ。

- **衝突 1 件** — `p3_autonomous_workload_trial.py`。main 側 wave [T-244] (8c 多世代開放) が
  critic digest の分岐を `pending["critic_digest_generated"]` の exact bool 契約 + 通常 file 要求へ
  強化した箇所と、本 wave が同じ呼び出しへ足した `purpose=` が衝突した。両側を保存する合成にした。
- **行が競合しなかった穴 2 件** — main から入った `require_admitted_campaign` 呼び出しが
  purpose 省略だった (`test_p3_autonomous_workload_trial.py` / `test_campaign.py`)。
- **fixture の epoch 欠落 1 件** — main 側 wave [T-856] が新設した `test_s8b_verdict.py` の
  `_oracle_verifier_case()` が observations を `campaign_verifier_epochs` 無しで組み立てるため、
  本 wave の gate が正しく fail-closed で弾き、全 cell が `status=unknown` /
  `median_of_medians=None` になって下流 assertion が 2 件落ちた。
  **gate 側は設計どおりなので緩めず、合成 fixture へ certified E1 の宣言を足して閉じた。**
  production は 1 行も変えていない。

**行が競合しないことは意味が壊れていないことの証拠にならない。** 3 件のうち 2 件は
conflict marker が出ない面で見つかっており、合成監査を別途回さなければ受入まで露出しなかった。

## 6. 焦点走の赤 8 件のうち 6 件は非帰属

2026-08-15 22:03–22:12 JST、bounded local、28 ファイル、1891 passed / 8 failed / 29 skipped。

| 件数 | 原因 | 帰属 |
|---|---|---|
| 5 | login node に `/tmp/.git` (2026-07-28 作成の空ディレクトリ) が実在し `_has_git_ancestor` が発火 | 非帰属 ([T-698]) |
| 1 | `from codex_roles import policy` の import 経路依存 | 非帰属 (既知) |
| 2 | 上記 §5 の fixture epoch 欠落 | **帰属** → fix 済み |

fix 後の `test_s8b_verdict.py` 単独走 = 72 passed / 0 failed (bounded local、`IZANAGI_TEST_NPROC=4`)。

## 7. 計算資源 — dispatch が 3 回とも queue で尽きた

2026-08-15 21:57–23:20 JST の間、`gen_S` は実行中ジョブ 0 のまま待機列だけが残る状態が続き、
`run_tests.py` の dispatch 経路は **15 分の `queue-wait-timeout` を 3 回**返した
(`rc=16` は基盤障害でありテスト結果ではない)。

bounded local も単独では通らなかった。予算は「前回ピーク × 1.25」で算出されるため、
`test_s8b_verdict.py` は 1.00 GiB → 1.25 GiB と伸ばしても足りず 2 走を空費した。
`IZANAGI_TEST_NPROC=4` で並列度を落として初めて 65 秒で完走した。

**この 2 つは同じ律速の裏表である** — 計算ノードが埋まっているとき、login の bounded local は
予算の伸びが遅すぎて代替にならない。並列度を落とすのが実際に効いた唯一の手であり、
変異 8 走もこの設定で回している。

## 8. 変わらないこと

- CCBench (`external/ccbench`) は 1 bit も変えていない。
- 既存 WAL、`output/s1-freeze/*`、`output/s8b-freeze/*` の bytes は 1 bit も変えていない。
- `campaign.lock` の wire contract (`IDENTITY_KEYS` / `AUTHORITY_KEYS` / `V2_KEYS` /
  `CONTRACT_LOADER_RELATIVE_PATHS`) と `search_config` は不変。既存 campaign の ID も不変。
- 裁定 Q2 のとおり、WAL と stdout の突き合わせ機構は作っていない。
- [T-860] (guided WAL の位置づけ) と [T-861] (歴史 campaign の admission) には触れていない。

## 9. ユーザー裁定へ返す 2 件

`verbatim/ruling-package.md` を正本とする。

- **Q1**: epoch の authority (exact 8 path) に `orchestrator/verifier/*` が入っていない。
  正しさ判定の実体が束縛外にある。親推奨 = closure を広げる (実 corpus に v2 lock が 0 件の今なら
  壊れる成果物ゼロ)。本 wave では名乗りの限定だけ行った。
- **Q2**: [T-834] (旧 certified consumer の分類) を本 wave の 16 経路分類表で閉じてよいか。
  親推奨 = 閉じる。

## 10. 一次資料

- `mutation-spec.json` / `mutation-ledger.json` — 本走 (7/7 KILLED)
- `mutation-spec-probe.json` / `mutation-ledger-probe.json` — 初回 probe (erratum、§4)
- `verbatim/s4-adjudication.md` — 段 4 裁定 (変異事前登録・実装単位・scope)
- `verbatim/ruling-package.md` — ユーザー裁定へ返す 2 件
- `verbatim/merge-audit.md` — main 取り込みの合成監査
- `verbatim/fix-merge-reds.md` — 取り込みで露出した帰属赤 2 件の fix
