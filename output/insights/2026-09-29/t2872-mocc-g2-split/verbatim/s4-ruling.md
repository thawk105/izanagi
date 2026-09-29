# [T-2872] 段 4 裁定と plan v2 (親) — 2026-09-29

入力: 段 1 brief (`verbatim/s1-brief.md`)、段 2 plan (`codex/s2-plan.md`)、段 3 相談 A (`codex/s3a-out.md`、機序・判定規則)・B (`codex/s3b-out.md`、過剰・費用)、親の実測 (`codex/s3-parent-facts.md`)。裁定 inbox は wave 開始後の新着なし (最新 = 第 39 回、D2277 と同内容)。

## 1. 所見の裁定

| # | 所見 | 判定 | 処置 |
|---|---|---|---|
| A-M1 | plan の V3 は L2 (lock 状態) の**後**の読みで、L2 の後に施錠・publish した書き手 (窓の外) も拾う。窓の証明にならない | real・採用 | 窓の中に版の再読 **Vmid** を 1 つ足す (§2)。`Vmid≠V1 ∧ L2 未施錠` を窓内の publish+unlock の確実な観測 (class A) とし、V3 だけで差が出るもの (class B) は曖昧として別に数える |
| A-M1' | L0 (版 load 前の lock 読み) は必要条件でなく、所有者と書き手の同一性も言わない | real・採用 | L0 を削る (窓の外の追加 load も 1 つ減る) |
| A-M2 / B-M1 | R2 の「(iv) 記録誤りを否定」は強すぎる。key と読んだ版は trace と同じ read set に依存する | real・採用 | R2 を「当該辺で trace の記録 (key・上書き版) と validation 内の独立 load の観測が一致し、書き手の publish と unlock が検査の窓内にあったことを観測した。(iii) の機序 (a) を支持。(iv) は当該辺で観測と矛盾しないが全般には排除しない」に弱める |
| A-M3 / B-M4 | 不一致・0 件の前に溢れ・abort 破棄・TSV 欠落・結合重複を判定不能に分ける | real・採用 | §3 R3 に判定不能の先行分離を入れる |
| B-M1' | R1 の「Silo の単一 word 検査なら拒否」は断定が強い | real・採用 | R1 を「trace 無しで、validation の版検査と lock 検査の間に他者の publish と unlock が入って commit した取引が実在する」に限定 |
| B-M2 | 「round ごとに verify」と「4 並列の式」が両立しない | real・採用 | batch = T 4・N 4・P 2 の benchmark を全部走らせてから T の 4 trace を並列 verify (§4) |
| B-M3 | configure argv・BACK_OFF=1・workload・patch 順・TRACE/probe define を build ごとに保存し照合 | real・採用 | §4 の binding 検査。T-2779 v5 の `BASE_CCBENCH_DEFINES`・`BACK_OFF=0`・10,000 record・rr50 を持ち込まない |
| A-S1 / B | (P1) は限定構成 (別 key の楽観読み・自己 write なし) の順序論証で、MOCC の任意の G2 へ一般化しない | real・採用 | insight に被覆境界として書く。witness ごとに key が別・両取引が相手の read key を自分の write set に持つかを trace で確認 |
| A-S2 | 版の比較は (epoch, tid)、run ID、(thid, epoch, tid) の一意性、溢れを事前固定 | real・採用 | §2・§3 |
| A-2 | V3 の local 受けと記録処理が `max_rset_` の値・時序を変えうる | real (時序のみ)・一部採用 | `max_rset_` は元の式のまま残す (§2)。V3 は `max_rset_` 更新後に別の load で読む。時序の変化は観測者効果として insight に書く |
| A-5 | torn read (i) と verifier の版順序の仮定は本計器では分けない | real・scope 内の限界 | insight §限界に書く |
| B-S1 | P arm は R1〜R4 に効かない。少数の負荷対照でよい | real・採用 | P は batch あたり 2 (§4) |
| B-S1' | TRACE=1 素の対照は R4 の解釈にだけ効く | real・不採用 (費用) | R4 は「帰属未達」に留める。T-2868 段 B (同 pin・同 argv・同 cell の harness、3/74) を同時刻でない参照として並記するだけ |
| B-3 | 固定 k・結果を見て延長しない・欠測別会計 | real・採用 | §4 |
| B-nit | plan の「argv 未抽出」「proof surface 未確定」は親の実測で更新 | real・採用 | author に親の実測を渡す |
| P4 nit | 負荷は hit 時の記録・key 複写を含む | real・採用 | insight の観測者効果の記述 |

scope 外の real 所見なし。gate・検査・台帳・一般化の追加なし (DW-G05)。repo 実装面の差分 0 → 変異 matrix 免除 (DW-S04)。受入全走は免除しない。

## 2. 計器 (診断 patch) の確定形

pin C + template 適用後の `cc/mocc/transaction.cc`、macro `IZANAGI_MOCC_G2_PROBE` (既定未定義 = 0、`-DCMAKE_CXX_FLAGS=-DIZANAGI_MOCC_G2_PROBE=1` で有効)。すべて `#if IZANAGI_MOCC_G2_PROBE` 内、`#if TRACE` の外。`#line` で元の論理行を保つ。

- validation read set 走査 (1033-1063):
  - 版 load (1035-1036) と比較 (1037-1045) は**変えない** (V1 = `check`)。
  - 比較を通った直後・lock 条件の前に **Vmid** = `__atomic_load_n(&rcdptr_->tidword_.obj_, __ATOMIC_ACQUIRE)` (新規 load、窓の中)。
  - lock 条件 (1048-1049) は `l2 = ldAcqCounter()` を local に受けて `l2 == W_LOCKED && searchWriteSet(...) == nullptr` と同じ短絡評価 (load 回数同じ)。
  - `max_rset_` 更新 (1062) は**元の式のまま**。その後に **V3** = 同様の acquire load (新規、窓の外)。
  - 判定: lock 条件を通った item について、`(Vmid.epoch,Vmid.tid) ≠ (V1.epoch,V1.tid)` なら class A、そうでなく `(V3.epoch,V3.tid) ≠ (V1.epoch,V1.tid)` なら class B。どちらも取引ごとの固定長 pending へ (key の bytes を値で複写、V1・Vmid・V3 の (epoch,tid)、l2)。
- validation が false を返す全経路と `abort()` で pending を破棄。writePhase の `maxtid` 確定直後 (trace の C 行出力の前) に pending を (thid, maxtid.epoch, maxtid.tid) 付きで thread ごとの固定長 committed 配列へ移す。
- counter (thread ごと): validation に到達した read item 数、class A 数、class B 数、commit した取引数、pending・committed の溢れ数。溢れは件数で残し 0 と扱わない。
- 出力: worker 停止後 (プロセス終了時) に環境変数 `IZANAGI_MOCC_G2_PROBE_OUT` の path へ TSV (hit 行 + counter 行)。測定区間内に I/O をしない。
- validation・lock・publish の判断と `max_rset_` の値の出所は 1 bit も変えない (差分で示す)。macro off の前処理後 source は template 適用済み pin C と行 marker を除き byte 一致すること (build 前検査)。

## 3. 判定規則 (結果前に固定)

- **R0 (判定不能の先行分離):** run ごとに、pending/committed の溢れ > 0、TSV 欠落、TSV の行数と counter の不一致、(run, thid, epoch, tid) の重複、TRACE=1 で hit の (thid,epoch,tid) が同 run の C 行に無い、のいずれかがあれば、その run は帰属判定不能として別会計する。
- **R1:** N arm (TRACE=0+probe) の class A 総数 > 0 → 「trace 無し build で、validation の版検査と lock 検査の間に他者の publish と unlock が入り、その取引が commit した実例がある」。0 件なら「本標本では trace 無しで class A を観測しなかった」(不在証明にしない)。class B は参考。
- **R2:** T arm の G2 witness (R0 を通った run) の各々について、2 本の rw 辺のどちらかで、読み手の C 行 (thid,epoch,tid) に結合した class A hit が「同 key ∧ V1 = 辺の読んだ版 ∧ Vmid ≥ 辺の上書き版 ((epoch,tid) 辞書順)」を満たせば **一致**。全 witness 一致 → R2 の文言 (§1 A-M2 行)。
- **R3:** 一致しない witness があれば、まず class B の同条件一致 (曖昧一致) と、R0 の判定不能を分ける。残る不一致は「計器が捕捉しなかった」か「機序 (a) 以外」かを区別できない、と書く。機序 (a) を否定しない。
- **R4:** T arm の G2 が 0 件 → 帰属未達。R1 だけを書く。

## 4. 実走設計

- build 3 本 (runner が configure argv・compiler realpath・compile commands・binary sha を保存):
  - T = pin C + template + probe patch、`TRACE=1`、probe on
  - N = pin C + template + probe patch、`TRACE=0`、probe on
  - P = pin C + template (probe patch なし)、`TRACE=0` (harness の性能 build と同じ argv)
  - 共通 argv = 親の実測の harness argv (Release・ENABLE_SANITIZER=OFF・`/usr/bin/x86_64-linux-gnu-gcc-11`/`g++-11`・`-DCCBENCH_BACKOFF_FIXED=-1 -DCCBENCH_BACK_OFF=1 -DCCBENCH_KEY_SORT=0 -DCCBENCH_TEMPERATURE_RESET_OPT=1 -DCCBENCH_TRACE=<0|1>`)。FetchContent の置き方は runner の既存 hydrate に従う。
- workload: `-ycsb_tuple_num=1000000 -thread_num=48 -ycsb_zipf_skew=0.9 -ycsb_rratio=95 -ycsb_rmw=0 -ycsb_max_ope=10 -extime=3`。
- batch = benchmark T 4・N 4・P 2 を順番回転で直列に走らせた後、T の 4 trace を最大 4 並列で verify (benchmark と verifier を重ねない)。verifier argv は T-2868 inventory と同形 (`--json --expected-commits N --protocol mocc --ccbench-root <T の source>`)、`/usr/bin/python3.10`、timeout 600 s。G2 の run は trace (zstd)・TSV・verifier JSON を保全、他は raw trace を削除 (TSV と verifier JSON は全 run 保存)。
- 単独性: 各 benchmark 前に既存 runner の単独性検査。
- smoke (確認不要の枠内): 1 job、3 build + 1 batch。Elapse・build 所要・1M record の load 時間・verifier 4 並列の elapsed と RSS を測る。R0 の検査 (TSV と C 行の結合、macro off identity) もここで通す。
- 本走: 反復数は smoke の Elapse から**結果を見る前に固定**し、4 node へ等分。結果を見て延長しない (追加は目的と費用を再提示)。合計 2 node 時間以上ならユーザー確認後に投入。目標 T 120 反復 (独立・率 2.8% の仮定で 1 件以上 97%、3 件以上 65%)。

## 5. 所有と段 5

- Codex author 1 本 (workspace-write)、子 worktree `t2872-probe-author` (branch 同名、base = wave HEAD)。所有 path = `t2872_probe/mocc-g2-probe.patch`・`t2872_probe/t2872_probe.py`・`t2872_probe/arms-t2872.json` の 3 file。docs 編集・commit をしない。親が監査して job dir `probe/` へ退避し、repo には入れない (D95、probe-only も実装面)。
- runner は T-2779 v5 (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2779-mocc-g2-observation-conditions/probe/t2779_probe.py`) を起点に書き換えてよい。`selftest` = 結合・一致判定の合成正例・負例 (両側一致・片側一致・key 不一致・V1 不一致・Vmid < 上書き版・class B だけ・重複・C 行欠落・溢れ)。`join` subcommand で保存済み G2 run を login で再集計できること。
- 変異 matrix 免除 (repo 実装面差分 0)。probe の機構は selftest と smoke の R0 検査で確かめる。
- 親の login 検査: `selftest`、`git apply --check` (pin C + template の上)、macro off identity (前処理比較) を smoke 投入前に行う。

## 追記 1 (2026-09-29 16:50 JST、本走の事前登録。smoke の結果のうち本走の条件を決めるのに使ったのは所要だけ)

- smoke (`35579.nqsv`、Elapse 267 s、batch 1): 3 build + 10 走 + verify 4。benchmark 1 走 約 3.5 s、verifier 1 回 155〜159 s (4 並列)。R0 判定不能 0。smoke は本走に合算せず別に報告する。
- smoke 1〜3 (`35474`・`35492`・`35505`、Elapse 28・29・約 30 s) は runner の欠陥で build 前後に停止 (fix2〜fix4 で修正)。
- 本走: 2 job (投入元 = wave worktree と子 worktree `t2872-probe-author`)、各 `--batches 14`、walltime 00:56:00。計 28 batch = T 112・N 112・P 56 走。反復数は固定し、結果を見て延長しない (追加は目的と費用を再提示)。
- 費用: 見積り 1 job ≈ 60 + 14 × 200 = 2,860 s。上限 (walltime) で 2 × 56 分 = 1.87 node 時間、smoke 計 ≈ 0.10 node 時間と合わせ 1.97 node 時間 < 2 node 時間 (ユーザー確認の線の内側)。walltime で切れた job は保存済みの run を `join` で集計し、欠けた batch を欠測として別会計する (補充しない)。
- runner `t2872_probe.py` sha256 `50c16ab01a321487e8831bdc640c9dec292d84eb4090ba3c59957bc88ad59e42`、patch `ff243794b33e360eba952c552a716b1118a084cc12e31aeca5b2ac94b707cfc5`、arms `807c584816c0d48d0bc0c6be7277c1fed2e279832f1ba96ee0e62210a5256e19` (smoke 4 と同一)。
