# silo-function-policy 軸 系列 C の certified 候補 3 本を R2 で 2 回ずつ測り直した — 同じノードの stock 比は 2.10・2.10 / 1.92・1.85 / 2.54・2.61 で、元の 1 観測 (2.17 / 1.86 / 2.64) の水準と並びが再現した (2026-10-01、[T-2865])

- 位置づけ: [T-2865] 系列 C (`output/insights/2026-09-29/t2865-silo-policy-series-c/README.md`) の iteration 2・3・4 の候補を、R2 (runbook `docs/phase3-silo-policy-runbook.md` §3.1、`--replay-proposal`、`evaluation_purpose=r2`、LLM なし、loop の予算・状態・履歴を使わない) で測り直した記録。元の値は各候補 1 観測だった。可変状態の正本 (worklog 末尾) にはしない。
- wave: branch `worktree-dev-wave-t2865-r2-replay`、起点 local main `74029b18f` (開始 gate rc=0、`--mode fresh --external-handoff`)。repo のコード・テスト・job 本体は変えていない (段 4 で実装なし、4→7→8→9)。docs の変更は runbook §3.1 の誤記 1 文だけ (§4)。
- 逐語 (`verbatim/`): 依頼 `request.md`、段 1 brief `s1-brief.md`、段 3 相談の prompt `s3-consult-prompt.md` と出力 `s3-consult.md` (read-only codex 1 本、2 レンズ)、段 4 裁定 `s4-ruling.md`、集計 `values-all.json` (下の親専用 `r2-values.py` の出力そのもの)、wrapper job の時刻と NQSV 会計 `wrapper-logs.txt`、submit checkout の作成ログ `make-submit-tree.log`。
- 逐語の正規化: `verbatim/s3-consult.md` は原文 (sha256 `af66210357e50d600a2e51d15941fe5c04afe8e2495cf34738cd1ec39eb846bb`、7,619 bytes) の 22〜24 行末の空白 2 字 (Markdown の改行) を `git diff --check` のために除いた (7,613 bytes、可視文字は不変)。復元は 22〜24 行の行末に空白 2 字を足す。原文は repo 外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-r2-replay/artifacts/s3-consult.md`。
- 親専用の運用 script と job の evidence は repo 外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-r2-replay/` (`make-submit-tree.sh`・`run-make-tree.sh`・`make-rest-trees.sh`・`r2-pair-job.sh`・`submit-r2.sh`・`wait-jobs.sh`・`r2-values.py`、`evidence/<attempt>/{cand,stock}/`)。trace 保全先 `/work/1/SFC/tanab/izanagi-repro-archive/t2865-r2-20261001/<attempt>/{cand,stock}/` (合計 6,274,194,904 bytes、候補 613〜822 MB・stock 342〜363 MB)。
- 入力の proposal: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-series-c/llm/prop-{2,3,4}.json` (依頼文は同 job dir の `evidence/` と書くが、proposal は `llm/` にある)。repo の逐語 `output/insights/2026-09-29/t2865-silo-policy-series-c/verbatim/llm/prop-{2,3,4}.json` と sha256 が一致 (`f0a0afda…`・`4900e278…`・`4f7e78a0…`)。

## 0. 要約

1. 候補 3 本 × 2 round = 6 本の wrapper job を Pegasus gen_S で走らせ、6 本すべてで候補 (R2) と同じノード・同じ job の stock がどちらも成立した。正しさ: 12 attempt すべてで legacy verify 1 回・性能構成 verify 5 回が serializable・anomaly 0 件。候補は 6 回とも `certified`、stock は 6 回とも `certified-stock`。失格の候補は無い。
2. 同じ job の比 (候補 ÷ stock、5 rep 中央値): 候補 2 (iteration 2) = 2.10・2.10 (元 2.17)、候補 3 (iteration 3) = 1.92・1.85 (元 1.86)、候補 4 (iteration 4) = 2.54・2.61 (元 2.64)。候補ごとの R2 2 回と元の 1 回、計 3 観測の範囲は 1.85〜1.92 / 2.10〜2.17 / 2.54〜2.64 で互いに重ならず、並び「候補 4 > 候補 2 > 候補 3」は元の観測と R2 の 2 round の計 3 回とも同じだった。
3. abort 率も元の値の近くに戻った: 候補 2 = 37.96・37.83% (元 37.72%)、候補 3 = 42.23・41.39% (元 41.62%)、候補 4 = 60.79・60.51% (元 60.26%)、stock = 12.01〜12.53% (元 12.23〜12.65%)。
4. 識別子は driver に足さず、(候補, round) ごとに新しい submit checkout を 1 本ずつ作って分けた (§2)。同じノードの stock は、repo 外の親専用 wrapper job が同じ allocation で job 本体を 2 回 (replay → stock) 呼んで得た (§2)。
5. 計算: wrapper job Elapse 合計 4,642 秒 (約 1.29 node 時間)。smoke 1 本の実測で積算し、受入を含めても 2 node 時間の線の下と判断して確認なしで投入した。
6. この再現は「同じ動作点・同じノードで、元の CCBench Silo (stock) に対する比が測り直しても同じ水準に出る」ことを示すだけで、最高水準 (調整済みの既存手法や既知最良の設定) に対する優位の証明ではない (§3.3)。

## 1. 依頼と裁定

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = `verbatim/request.md`): 系列 C の certified 候補 3 本を R2 で再測定し比の再現を確かめる。候補ごとに 2 回を目標とし、同じノード・同じ round に stock を置く。反復の識別子は R2 に閉じた最小の対応で扱い、共有 driver の編集が稼働 wave と衝突するなら各候補の初回 R2 で区切る。trace 保全 (§3.2) と正しさ gate は実走と同じ、anomaly の候補は即失格。smoke の後に積算し 2 node 時間以上なら land 調整役に諮る。本題の再測定だけ。
- 段 1 で実コードから確かめた前提 (`verbatim/s1-brief.md`):
  - replay は候補を 1 評価するだけで、同じ job の stock 対照を持たない (`p3_s4_loop_policy.py` main の `args.replay_proposal` 分岐)。job 本体は 1 job で driver を 1 回呼ぶ。
  - R2 の campaign identity は候補を含まない (`default_cfg` の search_config は form・perf・verify・`evaluation_purpose` などだけ)。Pegasus の claim は `<checkout>/output/env/pegasus/claims/<identity>.claim` に O_EXCL で一度きり作られ、terminal 判定より前に取られる (`loop.py` `_authorize_measurement`)。よって同じ checkout で先行の R2 が claim を取得済みなら、2 本目の R2 は候補を問わず `ClaimError` で止まる。bootstrap stock も checkout ごとに 1 回。runbook §3.1 の「同じ候補を同じ checkout で 2 回 R2 すると terminal skip」は実コードと食い違っていた (§4 で是正)。D2270 の却下欄は「R2 の run id と `replay-pair` mode は、同じ候補を同じ checkout で繰り返す必要が出たときに足す」と保留している。
  - 並行: `worktree-dev-wave-t2867-contrast-run` (未着地) が driver の `run_stock_control` と `test_p3_s4_loop_policy.py` を編集中だった。driver に識別子や stock 対照を足す案はこれと同じ file に触れる。
- 段 3 (`verbatim/s3-consult.md`): 識別子を足さず checkout を分ける案 (P1) は支持。wrapper (P2) は stock 呼出しで proposal 変数を消すこと・scratch 名の `:` → `_` 置換・claim を退避しないことの明記を求めた。見積り (P3) は wrapper 全体の実測で積算し直すこと、失格 (P4) は候補単位にすることを求めた。pair mode の流用は R2 の定義を壊すので不可。
- 段 4 裁定 (`verbatim/s4-ruling.md`): 上を採用。全 6 checkout の起点を wave 開始時の local main `74029b18f` に固定 (段 4 時点で main は進んでいたが、差は md_23 の docs・insight だけで pin・driver・job 本体・patch・CCBench は不変)。順序は系列 C の pair と同じ候補 → stock に固定。変異 matrix は実装面差分ゼロで免除。

## 2. 実行の形

- **識別子 = submit checkout。** (候補, round) ごとに job dir 下 (AI worktree 容器の外) に detached checkout を 1 本作り (submodule 初期化・third-party hydrate・`git worktree lock`)、その checkout の r2 campaign と bootstrap campaign を 1 回ずつ使った。6 本とも HEAD `74029b18f`、CCBench `68106660` (= `axis_silo_function_policy.PIN` = 系列 C と同じ)、tracked clean、骨格 patch SHA-256 `9cb545520fe6d27a852ccb406f321924ee61d17ff86bf1b74eeafc54b9db2904` (系列 C と同じ)、投入前の claim 0 件。各 checkout には job 後に claim が 2 つ (`…-798ec179` = r2、`…-a84dd632` = bootstrap) だけ残った。campaign ID は 6 checkout で同じなので、ID 単独で結合せず下表の checkout 絶対 path と組にして読む。
- **同じノードの stock = wrapper job。** repo 外の `r2-pair-job.sh` (PBS header は job 本体と同じ `-A SFC -q gen_S -b 1`、`elapstim_req=2400`) が、同じ allocation で `tools/pegasus/p3_s4_loop_pegasus.sh` を 2 回 `bash` で呼ぶ。1 回目 `IZANAGI_S4_POLICY_MODE=replay` (proposal を渡す)、2 回目 `IZANAGI_S4_POLICY_MODE=stock` (`env -u IZANAGI_S4_POLICY_PROPOSAL_PATH`)。呼出しごとに evidence root と trace 保全先を分け、間で 1 回目の scratch `/scr/$USER/p3-s4-loop-pegasus/<PBS_JOBID の : を _ に置換>` を `.cand` へ改名した (job 本体の「scratch は新しいこと」検査を 2 回目も新しい dir で満たす。削除はしない)。job 本体の検査 (HEAD 照合、CCBench clean、予約観測、単独性、前処理、prebuild receipt、trace 保全必須) は両方の呼出しで全部走った。予約検査が要求する残り時間は 1 秒 (`loop.py`) で、これは存在確認に過ぎず完走保証ではないので walltime は 2,400 秒を取った (実 Elapse 705〜855 秒)。
- **smoke → 並行。** 候補 2・round 1 (`c2r1`、40205) を 1 本だけ投げ、候補・stock 両側の driver rc=0、WAL の bench_done、verify_done の anomaly 0、`certified` / `certified-stock`、trace 保全の実体を確かめてから、残り 5 本を 5 ノードへ投げた (候補 3・4 の round 1 と候補 2 の round 2 は 04:04、候補 3・4 の round 2 は checkout の作り直し後の 04:08)。
- 値の読み取りは親専用 `r2-values.py` (各 checkout の campaign WAL・claim と evidence の stdout・compute-result を突き合わせる、読むだけ)。出力の逐語が `verbatim/values-all.json`。

## 3. 結果

### 3.1 値 (5 rep、txn/s)

| attempt | 候補 (系列 C) | checkout | ノード | request (Elapse) | 候補 中央値 | 候補 5 rep | 候補 abort | stock 中央値 | stock 5 rep | stock abort | 比 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| c2r1 | iteration 2 `3e0b518a3b4e` | `trees/c2r1` | bnode018 | 40205 (752 秒) | 2,853,298 | 2,970,585・2,841,371・2,802,168・2,935,676・2,853,298 | 37.96% | 1,360,785 | 1,360,785・1,377,793・1,354,623・1,361,143・1,345,864 | 12.01% | 2.097 |
| c2r2 | iteration 2 `3e0b518a3b4e` | `trees/c2r2` | bnode018 | 40215 (749 秒) | 2,854,581 | 2,954,292・2,854,581・2,807,400・2,897,168・2,812,034 | 37.83% | 1,361,531 | 1,371,921・1,349,141・1,387,053・1,361,531・1,356,632 | 12.41% | 2.097 |
| c3r1 | iteration 3 `c107a40f0486` | `trees/c3r1` | bnode014 | 40213 (735 秒) | 2,616,461 | 2,632,180・2,549,799・2,643,510・2,567,434・2,616,461 | 42.23% | 1,362,319 | 1,362,319・1,382,024・1,352,830・1,372,409・1,361,314 | 12.38% | 1.921 |
| c3r2 | iteration 3 `c107a40f0486` | `trees/c3r2b` | bnode021 | 40219 (705 秒) | 2,553,388 | 2,553,388・2,485,755・2,482,880・2,632,785・2,578,053 | 41.39% | 1,378,729 | 1,378,729・1,381,843・1,365,132・1,350,661・1,403,899 | 12.35% | 1.852 |
| c4r1 | iteration 4 `7e475c2c6607` | `trees/c4r1` | bnode017 | 40214 (846 秒) | 3,524,648 | 3,660,514・3,444,741・3,562,822・3,510,854・3,524,648 | 60.79% | 1,385,527 | 1,342,539・1,414,662・1,341,161・1,392,183・1,385,527 | 12.17% | 2.544 |
| c4r2 | iteration 4 `7e475c2c6607` | `trees/c4r2` | bnode046 | 40220 (855 秒) | 3,582,728 | 3,707,439・3,596,193・3,518,779・3,582,728・3,556,274 | 60.51% | 1,373,176 | 1,348,465・1,359,285・1,374,260・1,373,176・1,399,168 | 12.53% | 2.609 |

- checkout の path は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-r2-replay/` 起点。stock の variant は 6 回とも `db4764543546` (系列 C の bootstrap・pair の stock と同じ)。bench の `settled=true`・`high_variance=false`・`unstable=false` は 12 attempt すべて。rep の変動係数は候補 0.016〜0.025、stock 0.008〜0.024。
- 候補 2 の 2 round は同じノード (bnode018) の別時刻 (03:20 と 04:04) に当たった。他は別ノード。
- 各 job の中で候補の後に stock を測った (逐次対照)。比は同じノード・同じ job の対照に対するもので、順序効果を除いた差ではない。

### 3.2 元の観測との対照

| 候補 | 元 (系列 C の pair job、1 観測) | R2 round 1 | R2 round 2 | 3 観測の範囲 |
|---|---|---|---|---|
| iteration 2 `3e0b518a3b4e` | 2.17 (34246、候補 2,988,984 / stock 1,376,465、abort 37.72%) | 2.10 (37.96%) | 2.10 (37.83%) | 2.10〜2.17 |
| iteration 3 `c107a40f0486` | 1.86 (34247、2,556,839 / 1,371,220、41.62%) | 1.92 (42.23%) | 1.85 (41.39%) | 1.85〜1.92 |
| iteration 4 `7e475c2c6607` | 2.64 (34356、3,614,547 / 1,368,428、60.26%) | 2.54 (60.79%) | 2.61 (60.51%) | 2.54〜2.64 |

- 候補ごとの 3 観測の範囲は互いに重ならず、並び「iteration 4 > iteration 2 > iteration 3」は 3 回とも同じだった。系列 C の記録が「候補間の差として読めない」とした比の並びは、R2 で同じ向きに再び観測された。候補あたり 3 観測 (元 1 + R2 2) の記述であり、分布や信頼区間は主張しない。
- 候補 2 の R2 は 2 回とも元の値より約 3% 低い (候補の中央値が 2,853,298・2,854,581 に対し元 2,988,984。stock は 1,360,785・1,361,531 に対し元 1,376,465)。元の job は系列 C の checkout (HEAD `1887f56e4`) の pair で、今回は別 checkout (HEAD `74029b18f`) の R2。CCBench と骨格 patch は同じだが、差の原因はこの 2 回では切り分けていない。
- 候補の abort 率の並び (iteration 4 ≫ iteration 3 > iteration 2) も元と同じで、iteration 4 は abort 率が約 60% と最も高いのに throughput の比も最も高い。系列 C の記録 §2.4 が書いた「施錠競合時の方策が verify・bench 中に発火した証拠 (hook の計数) は v1 に無い」は今回も同じで、比の差を方策のどの要素に帰属させるかはこの再測定では決めていない。

### 3.3 主張の範囲

- 示したこと: 動作点 (YCSB、48 thread、1,000,000 tuple、zipf 0.9、read 5%、max_ope 10、extime 3 秒、write-heavy 較正点) と同じ CCBench pin で、LLM を使わずに保存 proposal を実走と同じ gate に通して測り直すと、元の CCBench Silo (stock、方策 patch なし) に対する同じ job の比が元の 1 観測と同じ水準・同じ並びに出た。
- 示していないこと: 最高水準に対する優位。stock は既定の Silo であり、backoff を調整した設定、既知最良の手書き方策、他の CC 手法との比較ではない。他の動作点・他の workload・他のノード型への一般化もしていない。
- 正しさは各 attempt の trace-enabled build による検査 (legacy 1 回・性能構成 5 回) であり、性能値は trace-disabled build の bench (規律 1)。

## 4. 運用の実測と是正

- runbook §3.1 の誤記を実コードに合わせた: 「同じ候補を同じ checkout で 2 回 R2 すると terminal skip」→「同じ checkout で先行の R2 が claim を取得済みなら、2 本目は候補を問わず terminal 判定より前の claim 取得で `ClaimError`。反復は checkout を分けて測る」。wrapper の手順は runbook に足していない (本 insight §2 と repo 外 script が手順)。
- submit checkout の 4 本目 (`trees/c3r2`) は、`git worktree add` から `git worktree lock` までの間に管理 dir (`.git/worktrees/c3r2`) が外から消えて孤児になり、作成 script がそこで止まって job 時間上限で打ち切られた。この wave からは prune・撤去を打っていない。同時刻に別 session の git 操作 (worktree unlock・list) が走っていたが、どの操作が消したかは確かめていない。以後は `git worktree add --lock` で追加と lock を同時に行い、`trees/c3r2b` として作り直した (作成ログ `verbatim/make-submit-tree.log`)。孤児 dir はその後も外から削除が進んでおり、この wave からは触っていない。
- `qstat <request>` は request が存在しなくても rc=0 を返した (出力は「does not exist」)。rc で終了を判定した最初の待ち手は smoke の終了を検出できなかったので、文言で判定するよう直した。
- repo 外の運用 script (wrapper job・投入・checkout 作成・待ち手・集計) は親が書いた。系列 C と T-2871 の親専用 script と同じ扱いで、repo には入れていない。`docs/ai-provenance.md` は所在を問わず Shell・Python の実行可能資材を実装面に数えるので、この扱いが dev-wave の「実装面は Codex author が書く」と整合するかは段 8 の改善候補として handoff に挙げた (結論はこの記録では出さない)。
- submit checkout 6 本 (`trees/c2r1`・`c2r2`・`c3r1`・`c3r2b`・`c4r1`・`c4r2`) は locked のまま残す (campaign 原本と claim を持つ)。撤去は land 後の掃除に委ねる。

## 5. 計算ノードの使用

wrapper job Elapse: 752・735・846・749・705・855 秒、合計 4,642 秒 (約 1.29 node 時間)。smoke (752 秒) を単価に 6 本 ≈ 1.25 node 時間と積算し、受入を足しても 2 node 時間の線の下と判断して確認なしで投入した。LLM 子は使っていない (R2 は LLM なし)。codex: 段 3 相談 1 本 (gpt-6-astra、ultra)。受入は本記録の commit 後に行う。

## 6. scope 外と次の一手

- 比の差をどの方策要素に帰属させるか (施錠競合時の方策の発火回数・abort 要因別の件数) は v1 に無く、今回も取っていない。
- 最高水準との比較 (調整済み stock・既知最良の手書き方策・他の CC 手法) は本 wave の scope 外。
- 同じ checkout で R2 を繰り返す識別子 (D2270 の保留) は今回も足していない。checkout を分ければ既存コードで反復できることを実測した。
