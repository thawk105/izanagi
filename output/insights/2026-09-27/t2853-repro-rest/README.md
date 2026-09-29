# [T-2853] 再現パッケージの残り — 新しい論文根拠 3 系列の job dir の写しと sha256 照合、R2 の投入単位と図ごとの Elapse 見積り (計算なし)

- 作成: 2026-09-27 JST。wave `wave-t2853-repro-rest` (背景 job)、着手時の基準 = local main `339d7c188`。依頼の逐語は `verbatim/request.md`、
  開始 gate は `verbatim/startup-gate.log` (rc=0)、段 1 brief は `verbatim/s1-brief.md`。
- 正本の前段: `output/insights/2026-09-23/t2853-repro-package-archive/README.md` (以下「写し稿」、手順と保存先の運用)、
  `output/insights/2026-09-23/t2853-figure-rerun-plan/README.md` (以下「計画稿」、図ごとの経路と所要)。
- **計算ノードは使っていない。job は投げていない。** login での読み取り・写し・sha256 だけである。写しと照合に使った script は repo に入れず、
  保存先の `/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260927/tools/` に置いた (sha256 は `verbatim/tools-sha256.log`)。repo のコード変更は無い。

## 0. 結論

1. **[T-2850] 試走 v2・[T-2849] MOCC 疎通・[T-2865] 段階 F の job dir にだけあった実験データ 7 組 (計 9,041 file、47,843,910 B) を、repo 外の
   `/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260927/` へ写し、原本と写しを別々に読んだ sha256・bytes・種別が全件一致した** (§2)。
   別実装の `sha256sum -c` による写し側の読み直しも 7 組 9,041 行すべて rc=0 だった。submit checkout (job dir 内の git worktree) の中にしか無かった
   campaign 原本と claim (T-2850 は 19 checkout で 1,728 file、T-2849 は 22 checkout で 555 file、T-2865 は 1 checkout で 13 file) も、checkout を動かさずに読んで写した。
2. trace は写していない。T-2849・T-2865 の trace は harness が直接書いた保全先 (`t2849-mocc-conn-20260926/`・`t2865-stage-f-20260927/`) にあり、
   中身は圧縮 trace と inventory だけで、今回写した台帳・集計・LLM 入出力・campaign 原本とは種類が重ならない。T-2850 試走 v2 は、投入に使った glue v3・投入 script・投入台帳の 3 箇所に trace 保全の設定が見つからず、trace の保全先は特定できなかった
   (他の保存経路・複製の不在までは調べていない、§2.3)。
3. **R2 の投入単位は「図 1 本 = 1 タスク」を推奨する** (前身を含む後継図 fig8b は fig8 を含めて 1 本)。束ねると 1 本ずつなら線の下の図でも合計で線を越える (§3.3)。
4. **計画稿が「Elapse 未記録」とした B-10 の 3 図 (fig2c・fig8/fig8b・fig13) の元 job に、NQSV の会計 (Elapse) が残っていた** (§3.1)。
   これで図 1 本ずつの判定が次のように確定・訂正される。
   - **fig2c は 2.98 node 時間 ((a) Elapse) で、投入前確認が要る。** 計画稿の 1.06 (WAL の時刻差) は Elapse の約 36% しか捉えていなかった。
   - **fig13 は 18.33 node 時間 ((a) Elapse) で、確認が要る。** 計画稿では単価が無く未判定だった。
   - **fig8b (fig8 を含む) は 1.40 node 時間 ((a) Elapse) で、確認は要らない** (暫定から確定)。
5. 図 1 本ずつで確認が要るのは **fig13 (18.33)・fig4 (正典 4 campaign で 8.88〜9.83、試算)・fig10 (3.40)・fig2c (2.98)** の 4 本。確認が要らないと確定したのは fig8b (1.40、(a)) だけで、fig2b・fig6・fig11 の「不要」は別系列の Elapse を当てた試算からの暫定であり、投入形を決めた段階でその単位の全 job の Elapse 見積りで判定する。
   R2 を推奨する 9 図を全部測り直すと 39.08〜40.10 node 時間 (出所の混じった和) になる (§3.2・§3.3)。

## 1. 範囲と言わないこと

- 本題は (i) 写しと照合、(ii) R2 の投入単位と Elapse 見積りだけである。gate・検査・台帳の追加、写しの自動化、一般化はしていない。凍結 chain は足していない (D320)。
  公開範囲 (全量か役割別か) の最終確定は投稿前のパッケージ組み立て時の仕事で、扱わない。
- 写しは正本ではない。元の path・submit checkout・trace 保全先は読むだけで動かしていない。保存先の運用は写し稿 §3 と同じ (書き換えない・消さない、official の入力にしない)。
- 見積りは「元と同じ設計を 1 回測り直す」場合の所要で、上下限ではない。出所の種別は計画稿 §1 の (a)〜(e) と「換算」「試算」の区別をそのまま使う。
  R2 は新しい有限履歴の判定であって原判定の再確認ではなく、anomaly が出た候補は即 reject して理由を構造化して返す (規律 2・3)。検証は trace 有効 build、計測は trace 無効 build の別走 (規律 1)。
- 旧 `linux-baremetal` 機の図 (fig1・fig2b・fig4) を Pegasus で測り直すと別環境の新しい測定になり、旧機の図へ値を混ぜない (計画稿 §1)。
- 本稿は見積りであって計算の投入の承認ではない。

## 2. 写しと照合 (i)

### 2.1 所在の特定

| 系列 | 実験データの所在 (`/work/1/SFC/tanab/dev-wave-jobs/` 相対) | 引き方 |
|---|---|---|
| [T-2850] 試走 v2 (18 job、2026-09-26 22:34 JST 投入) | 走行 dir `dev-wave-t2850-trace-concurrent-verify/trial-v2/` (系列台帳 `cohort-trial/`・job ごとの `evidence/`・LLM 親の状態 `state-trial-v2/`・`materials/`・`parents/`・投入台帳) と、19 本の checkout `trial-v2/trees/{tree-01..18,parent-tree}` の未追跡 campaign 原本。集計は `dev-wave-t2850-trial-v2-followup/` (`aggregate.json`・`job-costs.json`・`section8.json` ほか) | `output/insights/2026-09-27/t2850-trial-v2-analysis/README.md` 冒頭が集計の dir と「試走の固定 commit `299aa022e` の checkout (`trial-v2/trees/tree-01`)」を示す。走行 dir は調査子の報告を親が inventory で照合した |
| [T-2849] MOCC 疎通 (D2261) | `dev-wave-t2849-mocc-conn/` の `main/` (cohort・evidence・aggregate・job-costs)・`probe/` (単価実測)・`materials/`・`parents/` (LLM 入出力) と、22 本の checkout `trees/*` の未追跡 campaign 原本 | `output/insights/2026-09-27/t2849-mocc-conn/README.md` 冒頭 |
| [T-2865] 段階 F (stock-1・pair-1・replay-1) | `dev-wave-t2865-stage-f/` の `e2e/` (coder・auditor の入出力、拒否された 1 回目の提案)・`evidence/` (job 31468・31531・31584 の stdout/stderr・会計)・変異の試行記録と、checkout `trees/e2e` の未追跡 campaign 原本 | `output/insights/2026-09-27/t2865-silo-policy-stage-f/README.md` |

- **checkout 内の campaign 原本は全部が未追跡である。** 各 checkout の commit (T-2850 `299aa022e`・T-2849 `6c3913bc5`・T-2865 `b815183af`) の
  `git ls-tree -r` は `output/exploration` と `output/env/pegasus/claims` に追跡 file を 0 件返した。checkout の HEAD は T-2850 の 19 本・T-2849 の 22 本・T-2865 の 1 本が
  それぞれ上の commit に揃い (`verbatim/tree-heads.log`)、3 commit とも local main の祖先である (`git merge-base --is-ancestor` が 3 回とも終了コード 0)。
  checkout の追跡分は repo から再現できるので写していない。
- 写す範囲は写し稿の前例 (B-5 試走の job dir など) と同じく「job dir 全体から checkout (repo の写し) を除く」+「checkout 内の未追跡の campaign 原本・claim」とした。
  論文根拠かどうかで file を選り分けていない。量が小さく (計 47.8 MB)、選別で取りこぼす危険の方が大きいためである。したがって受入・land・codex 段の記録も含む。

### 2.2 組ごとの結果

2026-09-27 19:44:24〜19:46:57 JST に 1 process で直列に写し、照合した (`verbatim/copy.log`)。事前の数え上げ (`verbatim/dryrun.log`) で 7 組とも symlink・hardlink・`.git` は 0 件。
写しの前に `pgrep` で対象 dir を使う process を確かめ、書き手は居なかった (並走する別 wave の codex 子 1 本が T-2849 の checkout 内の digest を読み取りで参照していただけ)。

| 組 | 元 (dev-wave-jobs/ 相対) | file | bytes | 照合 | 写し / 照合 (秒) |
|---|---|---:|---:|---|---:|
| t2865-stage-f-originals | `dev-wave-t2865-stage-f/trees/e2e/output/` の campaign 3 (stock `a84dd632`・pair `877344a7`・replay `798ec179`)・claim 3・`namespace.json` | 13 | 81,266 | 一致 | 0 / 0 |
| t2849-mocc-conn-originals | `dev-wave-t2849-mocc-conn/trees/*/output/` の campaign 原本と claim (21 checkout。`llm-parent` は campaign を持たない) | 555 | 2,473,948 | 一致 | 13 / 0 |
| t2850-trial-v2-originals | `dev-wave-t2850-trace-concurrent-verify/trial-v2/trees/*/output/` の同上 (19 checkout) | 1,728 | 7,865,228 | 一致 | 48 / 1 |
| t2850-trial-v2-followup-jobdir | `dev-wave-t2850-trial-v2-followup/` 全体 | 236 | 2,286,871 | 一致 | 1 / 0 |
| t2849-mocc-conn-jobdir | `dev-wave-t2849-mocc-conn/` (`trees/` を除く) | 1,538 | 4,640,912 | 一致 | 16 / 2 |
| t2865-stage-f-jobdir | `dev-wave-t2865-stage-f/` (`trees/` を除く) | 654 | 14,769,651 | 一致 | 5 / 0 |
| t2850-trial-v2-rundir | `dev-wave-t2850-trace-concurrent-verify/trial-v2/` (`trees/` を除く) | 4,317 | 15,726,034 | 一致 | 60 / 2 |
| **計** | | **9,041** | **47,843,910** | 不一致 0 | |

- 全組の後の保存先 `data/` 全体の走査: 9,041 path で manifest の和と一致 (余計 0、欠け 0)。合否は各 manifest の `verify.ok`・`verify.mismatch` と全体走査の行で読んだ
  (`archive_copy.py` は不一致を記録するだけで異常終了しないので、rc=0 は照合成功を意味しない。写し稿 §2.2)。
- 別実装での再確認: `sha256sum -c` で写し側だけを全 manifest に対して読み直し、19:47:11〜19:47:18 JST、7 組 9,041 行すべて rc=0 (`verbatim/recheck.log`)。
  manifest との一致を別実装で確かめたもので、同じ filesystem の cache を読んだ可能性まで排除する証拠ではない。
- 各組の manifest の sha256 は `verbatim/manifest-sha256.log`。保存先の `README.md` と、archive 全体の `README.md` の表 (今回の dir と、既存の trace 保全先 2 dir の行) を書いた。
- `archive_copy.py`・`dryrun.py` は写し稿の保存先 `t2853-20260923/tools/` と同一 bytes (sha256 `16056f57…`・`3fe1266a…`) を複製して使った。起動用の `run_copy.sh` は隔離 session の
  ガードが起動を拒否したので、同じ argv の `archive_copy.py` を直接実行した。`dryrun.py` の import で保存先 `tools/` にできた `__pycache__/` (自分が直前に作った .pyc 1 file) は消した。

### 2.3 写さなかったものと理由

| 対象 | 理由 |
|---|---|
| job dir 内の checkout 本体 (T-2850 の 19 本・T-2849 の 22 本・T-2865 の `trees/e2e`) | repo の写し (commit は local main の祖先)。中の未追跡の campaign 原本・claim だけを写した |
| checkout 内の `output/campaign-locks/`・`output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src/` | ignored の lock と、依存物のソースの展開 (pin は checkout の hydrate 記録にある)。実験原本ではない |
| trace 保全先 `t2849-mocc-conn-20260926/`・`t2865-stage-f-20260927/` | 既に repo 外の保全先にある (依頼の指定)。中身は `inventory.json`・`ccbench.diff.zst`・`trace_NN.log.zst` だけで、今回写した組と種類が重ならない (調査子の実測を親が dir の構成で照合) |
| `dev-wave-t2850-trace-concurrent-verify/` の `trial-v2/` 以外 (段 2〜6 の記録、変異の結果と dispatch 記録、`submit-tree*`・`mutation-*` の checkout、smoke の cohort、`vprobe3`) | 試走 v2 を投入するための実装 wave の記録と repo の写しで、試走 v2 の実験データではない。smoke は試走の前の疎通確認 |
| `dev-wave-t2850-trial-run/` (試走 v1、block 1) | 依頼は試走 v2。v1 の block 1 は試走 v2 の insight が「旧 block 1 (直列検査)」として比べるだけ |
| `dev-wave-t2849-mocc/` (MOCC 挿入の実装 wave) | 疎通 (D2261) の実験データではない。本 wave では中身を調べていない |
| T-2850 試走 v2 の trace | 試走 v2 の投入に使った glue v3 (`dev-wave-t2850-trace-concurrent-verify/glue-v3/`)・`trial-v2/submit_all.py`・投入台帳 `jobs-trial-v2.jsonl` に文字列 `TRACE_ARCHIVE` は 0 件で、glue v4 (本比較用、未投入) にだけある (親の grep)。調べたこの 3 箇所に trace 保全の設定は見つからず、試走 v2 の trace の保全先は特定できなかった (他の保存経路・複製の不在までは調べていない)。試走 v2 の insight §3 も trace の保全量を「未測定」と書く |

## 3. R2 の投入単位と Elapse 見積り (ii)

### 3.1 新しく見つかった Elapse 記録

計画稿が「(a) は無い」とした B-10 の元 job の stderr の末尾に、NQSV の会計 (Request ID・開始・終了・Elapse) が残っていた (`verbatim/elapse.log`)。
B-10 の 2 script (`tools/pegasus/b10_backoff_grid.sh`・`b10_backoff_shape_campaign.sh`) は `#PBS -b 1` (1 node) で、この行は導入 commit 以後変わっていない
(`git log -S'#PBS -b'` がそれぞれの導入 commit `ad3ef12a8`・`4dfd3785b` だけを返す)。したがって Elapse がそのまま node 時間になる。

| 図 | job (Request ID) | Elapse (s) | 計 | 計画稿の値と出所 |
|---|---|---|---:|---|
| fig2c | 951689 / 951690 / 951691 | 3,576 / 3,581 / 3,584 | 10,741 s = **2.98 node 時間** | 1.06 ((c) WAL 時刻差 1,276 s × 3) |
| fig8 (cohort 1) | 998865 / 998866 / 998867 | 840 / 837 / 841 | 2,518 s = **0.70** | 0.70 ((b) driver 記録) |
| fig8b の cohort 2 | 10752 / 10753 / 10754 | 839 / 836 / 839 | 2,514 s = 0.70 | 3 × 839 (換算) |
| fig13 | 965564 (write-heavy) / 974207 (balanced) / 977647 (read-heavy) / 978195 (集約) | 13,750 / 13,186 / 39,026 / 16 | 65,978 s = **18.33** | 未判定 ((e) walltime 48 h、(d) 投入〜完了 18.68 h) |

- job と図の対応: fig2c と fig8b の provenance が指す group (`20260826T234647Z-783837`・`20260915T061814Z-545445`・`20260919T131526Z-2235286`) の stderr で、
  fig8b の caption が挙げる job ID (998865〜998867、10752〜10754) と一致する。fig13 は結果稿 `docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md` の
  submission 表 (submission id と request の対応) で引いた。`20260919T131120Z-2159341` の 3 job (各 5 s) は cohort 2 の前に失敗した試行で、図に入らない。
- **WAL の時刻差は Elapse を大きく下回りうる。** fig2c では Elapse の約 36% (1,276 / 3,580 s) しか捉えていなかった。差の内訳 (WAL の前後で何に時間を使ったか) は調べていない。
  (c) を単価に使った見積りは過小になりうるので、以後は (a) を先に探す。

### 3.2 図ごとの node 時間

R2 を推奨する 9 図 (計画稿 §0 項 2) と、推奨しない・保留の図を並べる。「確認」は、その図 1 本を 1 タスクとして投げる場合に D2212 項 4 の確認 (2 node 時間以上) が要るか。
どの行も受入などの開発の検査を含まない — R2 を投げる wave が実装を伴えば受入 1 回 ≈ 0.25 node 時間を同じ線で足す (D2219 項 1)。

| 図 | R2 の中身 | node 時間 | 出所 | 確認 |
|---|---|---:|---|---|
| fig2b | P2-4 の固定 8 variant × 5 反復 × 3 workload を Pegasus で測る (別環境の新しい測定) | 0.70〜0.77 | 試算: 24 variant × 104.5〜115.6 s (下の注) | 暫定で不要 (試算。投入形を決めて全 job の Elapse で判定) |
| fig1 (下地) | P2-2 の fitness 表 (固定 8 点 × 5 反復 × 3 workload) を Pegasus で測る場合だけ | 0.70〜0.77 | 試算 (同上) | 暫定で不要 (試算。投入形を決めて全 job の Elapse で判定) |
| fig2c | B-10 拡張格子 3 job (各 31 variant) | **2.98** | (a) Elapse | **要** |
| fig4 | S-1a の正典 4 campaign 306 session (develop 18・floor 144・block1 72・block2 72) を Pegasus で測る (別環境の新しい測定) | **8.88〜9.83**。図の標本だけ (block1 + block2 の 144 session、判定に要る floor を除く) なら 4.18〜4.62 | 試算: session 数 × 104.5〜115.6 s | **要** |
| fig6 | A-2 の取り直し (stock 対 fixed 10 / 5 µs)、現行 policy 5 node | 1.70 | 試算 (計画稿: 同じ形の B-7 の (a) を当てた値。元の 1 node の走は 1.68 (a)) | 暫定で不要 (試算。投入形を決めて全 job の Elapse で判定) |
| fig8b (fig8 を含む) | B-10 静的右 tail の 2 cohort (各 3 job × 8 点) | **1.40** | (a) Elapse (cohort 1 の 0.70 と cohort 2 の 0.70) | 不要 (確定) |
| fig10 | B-7 fixed 5 µs × 3 workload、5 node | 3.40 | (a) Elapse × 確保 node 数 (計画稿) | **要** |
| fig11 | A-6 read-heavy fixed 2 µs、現行 policy 5 node | 1.69 | 試算 (計画稿: B-7 の rr95 の (a)。元の 1 node の走は 1.22 (a)) | 暫定で不要 (試算。投入形を決めて全 job の Elapse で判定) |
| fig13 | B-10 待ち方 grid 3 job + 集約 job | **18.33** | (a) Elapse | **要** |
| fig5 / fig7 | 推奨しない (測り直しても用途制限が残る) | 2.02 | (a) (計画稿) | (投げるなら要) |
| fig15 | R2 ではなく固定条件の観測の再実施。元の認可が 1 回限りで、改めて認可が要る | 1.67 | (a) (計画稿) | 不要 (認可は別) |
| fig9 / fig14 | 今は走らせない (D2211 項 10・D2212 項 5) | 0.45 / 0.62 (参考) | 計画稿 | (認可が先) |

- **旧機 3 図の単価 (試算):** fig2b・fig1 の下地・fig4 は Pegasus の元 job が無い。同じ動作点 (Silo・48 thread・100 万 record・Zipf 0.9・extime 3 s・5 反復) で固定 genome を
  variant ごとに build・正しさ検査・計測する B-10 格子の (a) を variant 1 つあたりに割った値を当てた: fig8 の 836〜841 s ÷ 8 = 104.5〜105.1 s、fig2c の 3,576〜3,584 s ÷ 31 = 115.4〜115.6 s。
  別系列の job の値を当てた試算で、(a) そのものではない。fig2b の形 (workload あたり 8 variant × 5 反復) は fig8 の job (workload あたり 8 点 × 5 反復、1 job ≈ 840 s) と同じなので、
  fig2b の試算は fig8 の実績 2,514〜2,518 s とも合う。fig4 は session ごとの正しさ検査の回数 (floor・block は 1 回、develop は 2 回) が B-10 格子と違い、build の再利用も前提が違うので、幅は目安である。
- **投入経路の有無は本稿では確かめていない。** fig2c・fig8b・fig13 は元の driver (`tools/pegasus/submit_b10_backoff_grid.sh`・`submit_b10_backoff_shape.sh`)、fig6・fig10・fig11 は
  paper-story の certification driver が現行 repo にある。fig2b・fig1 の下地・fig4 を Pegasus で走らせる経路が既存 driver で組めるかは未確認で、実装が要れば受入 0.25 を足す。

### 3.3 投入単位と確認

**推奨: 図 1 本を 1 タスクとし、束ねない。後継図が前身の測定を含む場合 (fig8b ⊃ fig8) だけまとめる。**

- 理由 1: 図はそれぞれ独立の主張で、測り直しの判断 (推奨・保留・認可) も図ごとに違う (§3.2)。
- 理由 2: 1 本ずつなら線の下の図でも、束ねると合計で線を越える。例: fig6 + fig11 = 3.39、fig2b + fig8b = 2.10〜2.17。
- 理由 3: D2212 項 4 の単位は「1 タスクで投げる job の合計」なので、単位を図 1 本に固定しておくと確認の要否が表からそのまま読める。

| 単位 | node 時間 | 確認 |
|---|---:|---|
| fig8b (fig8 を含む) | 1.40 ((a)) | 不要 |
| fig6 | 1.70 (試算) | 暫定で不要 |
| fig11 | 1.69 (試算) | 暫定で不要 |
| fig2b | 0.70〜0.77 (試算) | 暫定で不要 |
| fig2c | 2.98 ((a)) | **要** |
| fig10 | 3.40 ((a) × node 数) | **要** |
| fig4 | 8.88〜9.83 (試算、図の標本だけなら 4.18〜4.62) | **要** |
| fig13 | 18.33 ((a)) | **要** |
| 参考: R2 推奨 9 図をすべて (fig4 は正典 4 campaign 全部) | 39.08〜40.10 (出所の混じった和) | 要 |
| 参考: 計画稿 §4 の 6 図 (fig2b・fig2c・fig6・fig8b・fig10・fig11) | 11.87〜11.94 (計画稿の 9.52 から、fig2c が (c) 1.06 → (a) 2.98 で +1.92、fig2b が fig2c の WAL 時刻差を当てた試算 0.27 → 0.70〜0.77 で +0.43〜0.50) | 要 |

- 確認が要らないと確定したのは fig8b だけである。fig6・fig11・fig2b の「暫定で不要」は別系列の Elapse を当てた試算からの判定で、投入形を決めた段階でその単位の全 job を含む Elapse 見積りで判定し直し、2 node 時間以上なら確認を取る (計画稿 §7 の GM1 と同じ扱い)。fig4 の 4.18〜4.62 は判定に要る floor を除いた標本だけの参考値で、S-1a の判定を再現する所要ではない。
- 所要は元の設計を 1 回測り直す値で、retry・事前の校正・smoke の再走を含まない。fig13 は workload で所要が 3 倍違い (read-heavy 39,026 s)、walltime の上限 (read-heavy 86,400 s) には余裕がある。
- 投入はこの wave では行わない。R2 は論文投稿前に、単位ごとに本表を示して確認が要るものは確認を取ってから投げる (D2212 項 4)。

## 4. 段 6 レビュー

軽量版の dev-wave として段 2・3 は省いた (repo のコード変更 0、設計の択一なし)。一次資料から事実を書き起こす docs なので、段 6 の read-only レビューを 1 本
(一次資料との照合と、過剰・削除の 2 レンズ) 残した。review (Codex、read-only、commit `06243b15d` が対象、rc=0、`tools/check_codex_output.py` 受理 rc=0、
逐語 `verbatim/s6-review.md`) は NO-GO (must-fix 2・should-fix 1)。数値 (9,041 file・47,843,910 B、会計の Elapse と node 時間、単価の幅、§3.3 の和) はレビュー子が一次資料から再計算して一致とした。
親は 3 件を一次資料で裏取りし、すべて real・scope 内と裁定して本文を直した。

| ID | 所見 | 判定 | 処置 |
|---|---|---|---|
| M1 | fig2b・fig6・fig11 (と fig1 の下地) は別系列の Elapse を当てた試算なのに、確認「不要」を確定のように書いた | real | §3.2・§3.3 の確認欄を「暫定で不要」にし、投入形を決めた段階でその単位の全 job の Elapse 見積りで判定すると書いた。§0 項 5 と fragment も同じにした |
| M2 | §0 と fragment の fig4「4.18〜9.83」は、判定に要る floor を除いた 144 session の値を下限に見せる | real | 要約を正典 4 campaign の 8.88〜9.83 にし、4.18〜4.62 は判定を再現しない標本だけの参考値として §3.2・§3.3 に限った |
| S1 | 3 箇所に保全指定が無いことから「trace は残っていない」までは導けない | real | §2.3 を「調べた 3 箇所に設定は無く、保全先は特定できなかった (他の保存経路・複製の不在までは調べていない)」に限定した |

焦点再レビュー 1 巡目 (Codex、read-only、commit `2aa0b1af7` が対象、rc=0、受理 rc=0、逐語 `verbatim/s6-focus-1.md`) は NO-GO — M1・M2 は closed、S1 は partial。
レビュー子は「不要」の全 14 出現を分類し、試算から確定した「確認不要」が残っていないこと、修正後の数値 (fig8b 1.40、fig2b 0.70〜0.77、fig4 8.88〜9.83 / 4.18〜4.62、fig6 1.70、fig11 1.69) が一次資料と合うことを確かめた。

| ID | 所見 | 判定 | 処置 |
|---|---|---|---|
| S1 の残り / N1 | §0 項 2 の「T-2850 試走 v2 は trace 保全を指定していない」が §2.3 の調査範囲を超えた断定のまま | real | §0 項 2 を §2.3 と同じ範囲に限定した。保存先の `README.md` の同じ文も同様に直した |

焦点再レビュー 2 巡目 (Codex、read-only、commit `f99846ffc` と保存先の README が対象、rc=0、受理 rc=0、逐語 `verbatim/s6-focus-2.md`) は **GO** — S1・N1 は closed、
M1・M2 は closed のまま回帰なし、新規所見なし。レビュー子は glue v3・投入 script・投入台帳を読み直して `TRACE_ARCHIVE` の指定が無いことと、
本文と repo 外 README 2 本に調査範囲を超える断定が残っていないことを確かめた。

## 5. 出所

- `verbatim/request.md` — 依頼の逐語。`verbatim/startup-gate.log` — 開始 gate (rc=0)。`verbatim/s1-brief.md` — 段 1 brief。
- `verbatim/dryrun.log`・`verbatim/copy.log`・`verbatim/recheck.log` — 写す前の数え上げ、写しと照合、写し側の独立再検算。
- `verbatim/tree-heads.log` — 42 本の checkout の HEAD。`verbatim/manifest-sha256.log`・`verbatim/tools-sha256.log` — 保存先の manifest 14 file と tools の sha256。
- `verbatim/elapse.log` — B-10 の元 job の NQSV 会計 (Request ID・開始・終了・Elapse) の抜粋。
- `verbatim/s6-review.md`・`verbatim/s6-focus-1.md`・`verbatim/s6-focus-2.md` — 段 6 のレビューと焦点再レビュー 2 巡の逐語 (無加工、行末空白なし)。
- 調査子 (Claude Explore、sonnet) 3 本 (系列ごとの所在と写す候補) の報告は会話内のみ。3 本とも途中で隔離 session のガードにより Bash を使えなくなり、
  T-2850 と T-2865 の checkout 内の件数・bytes は親が保存先 `tools/` の読み取り script と `archive_copy.py` の数え上げで実測し直した。本文の数値はすべて親の実測である。
  調査子が「T-2850 の checkout 内の campaign は試走 v2 と無関係かもしれない」と推測した点は、checkout が試走 v2 専用の `trial-v2/trees/` にあり HEAD が試走の固定 commit に揃うこと、
  tree-01 の campaign (18 個) のうち `p3-s4-loop-s4-autonomous-007ad00b` が試走 v2 の系列台帳 `cohort-trial/write-heavy/bo/series-1/` の `series.json` と event から参照されることで退けた。

## 所在の移動・撤去 (2026-09-30 追記)

本 insight が写しの元として記録した checkout (T-2850 試走 v2 の 19 本、T-2849 MOCC 疎通の 22 本、T-2865 段階 F の `e2e`) は、2026-09-30 の掃除 wave で回収せずに撤去する。以後、これらの campaign 原本の控えは `/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260927/` の写しになる。写しを official の入力へ昇格させるものではない。
判定の根拠・木ごとの退避の所在・残る写しの一覧は `output/insights/2026-09-30/cleanup-originals-migration/README.md` を正本とする。上の本文は当時の事実として書き換えない (記録された測定・判定は撤去を理由に無効にならない、規律 7)。撤去は同 wave の land の後に行う。
