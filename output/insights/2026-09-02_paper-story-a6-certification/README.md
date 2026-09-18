# A-6 read-heavy 同一 workload certification — 実走 1 回目は indeterminate

## 結論

**attempt `a6-20260902a` の判定は `indeterminate` である。** read-heavy の correctness / performance の
どちらも取れていない。計算ノードの条件 gate (condition/meaning gate) が cell-0 を拒否し、
campaign が始まる前に driver が非 0 で終了した。

- outer certification status: `indeterminate`
- reason: `compute driver exited nonzero: {'rr95': 2}`
- cells: 空、effects: 空 (測定していないので値が無い)

**論文 §8 の但し書き 2 は外れていない。** read-heavy は今も「backoff は正しさに影響しない」という
機序論証による外挿のままである。A-6 の項目は残る。

## 実行 identity

- attempt: `a6-20260902a`
- source commit: `1c11a68cbed6c5077e1d61e8c5440ed3eecc98d3`
- CCBench pin: `511c953`
- policy: `orchestrator/campaign/paper_story_a6_certification.v2.json`
  (SHA-256 `4ca15d071f0bc10febe3274d0523b59f0e4903bf612ff050bef7e6728a3700d4`)
- protocol SHA-256: `a73bc3a0eabd1bcb960779c9b61b20983ef3cfb88d76d50c073e9ced4f6be445`
- request: `967525.nqsv`、Elapse 20S、host は reservation receipt 参照 (bnode)
- durable authority:
  `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260902a/`

## 何を測ろうとしたか

`docs/paper-story/2026-09-02.md` §8 の A-6。A-2 の正式 protocol は write-heavy (rratio=5) と
balanced (rratio=50) の exact 4 cell を対象としており read-heavy は対象外である。本 wave は
read-heavy (ycsb_rratio=95、stock = BACK_OFF 0 / BACKOFF_FIXED -1、adopted = BACK_OFF 1 /
BACKOFF_FIXED 2) を同じ protocol で 1 workload = 1 job 実施しようとした (D1169 が workload 単位の
独立 job を定めている)。

## なぜ止まったか — 根本原因

計算ノードの条件 gate が次の理由で cell-0 を拒否した。

```
condition gate rejected paper workload cell-0:
  BACKOFF_FIXED:supply-effectuation:configure-failed
  BACKOFF_NOINLINE:supply-effectuation:configure-failed
  BACKOFF_FIXED:runtime-meaning:materialized-branch-invalid
  BACKOFF_NOINLINE:runtime-meaning:meaning-witness-undeclared
```

計算ノード上で gate の記録を全文取得して原因を確定した (診断は repo 外で実施、repo は不変)。

- `configure-failed` の実体は、CCBench の `cmake/ThirdParty.cmake:54` の
  `FetchContent_Populate(masstree)` が `Build step for masstree failed: 2` で落ちること。
- 同じノードで `git ls-remote https://github.com/thawk105/masstree-beta.git` は rc=128、
  `fatal: unable to access ...: Could not resolve host: github.com`。
- 同じ cmake configure を**ログインノードで実行すると成功する**。したがって計算ノード固有である。

`docs/pegasus-runbook.md` は 2026-08-01 の実測として「計算ノードは直結の外部 network 不可」
「依存ソースはログインノードで pinned staging し `FETCHCONTENT_SOURCE_DIR_*` で渡す運用を維持する」と
既に定めている。**A-2 / A-6 の certification 経路はこの環境契約に従っていない** — job body も
条件 gate も、CCBench の FetchContent が実行時に git clone できることを前提にしている。

- 永続 cache `/work/1/SFC/tanab/izanagi-thirdparty-cache` (masstree / mimalloc / googletest) は
  既に存在し populate 済みである。供給 helper は `tools/pegasus/fetch_third_party.py`。
- これを使っている driver は `mocc_trace_pilot.sh` と `silo_ladder_rung1`、および t139 probe である。
- certification 経路は `run_campaign` 経由でビルドするが、`run_campaign` は
  FetchContent の source dir を受け取る引数を持たない (`buildcache` 側には既にある)。

**条件 gate は A-2 の実走 (2026-08-28、commit `639c1dba`) より後に、3 commit で driver 全体へ
義務化されたものである** (T-1999 / D1198)。したがって A-2 が当時通ったことは、同じ経路が今日
通ることを意味しない。**これは A-6 固有の欠陥ではなく、A-2 certification 経路そのものが
現在の環境契約の下では計算ノードで走らないという既存の不整合である。**

**規律 2 に従い、この gate を緩めて通すことはしない。**

## 判断を要する点 (ユーザー裁定へ返す)

read-heavy の測定を実際に取るには、certification 経路の build path をオフライン依存へ配線し直す
必要がある。これは共有の measurement pipeline (`run_campaign` → `pipeline.evaluate` →
`buildcache`) へ引数を通す横断変更であり、全 driver の測定ビルドの configure argv を変える。
本 wave の scope (本題の実走、一般化の追加は scope 外) を超えるため実装せず、裁定へ返す。

## 本 wave が実装したもの (変異で裏取り済み)

read-heavy を A-2 と同じ protocol で 1 workload 回すための受理面。**任意 N への一般化は採らなかった。**

- `load_policy` は `study` から shape を引く exact map を持つ
  (`paper-story-a2-certification` → 2 workload / 4 cell、`paper-story-a6-certification` → 1 / 2)。
- policy 選択面は repo 内 canonical な 2 path だけを受理する closed set。任意 path を受理しない。
  実行される policy bytes は tracked file であり、job body の HEAD 一致・tracked clean 検査を
  通じて `source_commit` へ束縛される。
- D1259 の partial v4 境界 (exact 2 workload で成功が exact 1) は writer 側 `finish_group` と
  consumer 最前段 `_validate_completion_receipt` の 2 箇所だけで保つ。前段に支配される
  manifest producer / loader / authority へは guard を足さない (恒真な保証を増やさないため)。
- A-2 の policy bytes、`protocol_sha256`、qsub environment の 7 key、job 名、workload 順序、
  既存成果物は変更していない。

### walltime を 06:00:00 から 12:00:00 へ変えた理由

A-2 の 6 時間枠は write-heavy と balanced の実測 (rr5 Elapse 3671s / rr50 3594s) に基づくもので、
read-heavy へは転用できない。read-heavy (48 thread / zipf 0.9 / rratio 95 / extime 3) の
直列性検査は 1 回 23 分の実測があり、同 regime の別走行は 5 時間で 15 点中 3 点しか完了していない
(`output/insights/2026-08-31_t1905-b10-formal-run/README.md`)。A-6 は 2 cell x
(legacy 1 + full-scale 5) なので full-scale 10 回を max 23 分で見積もると 3.83 時間になる。
12:00:00 はその約 3.1 倍で、gen_S の Per-Req Elapse 上限 86400S の内側である。
D193 により walltime 超過は attempt 全損 (自動回復しない) であり、この非対称性が枠を広く取る理由である。
`scheduler` は `_protocol_preimage` に含まれないため **protocol の同一性は変わらない**。
D1263 は A-2 fan-out の据え置きを定めた裁定であり A-6 を拘束しない。

## 実走前に閉じた欠陥

1. **投入器の重複検出は導入時から一度も発火していなかった。** `qstat` の `ReqName` 欄は 8 文字で
   切られる (実測: `izdw-b51bb380a6` が `izdw-b51` と表示される) ため、job 名の部分一致は永久に
   偽であった。inventory を引数なし `qstat -f` へ変え、`Request Name` 行の完全一致だけを
   同 study の重複として拒否する。**これは A-2 側にも等しく存在した恒真な保証である。**
2. compute job の `resolve_python` と policy 解決が `compute-result.json` を書く EXIT trap の
   前へ移動していた。interpreter や policy の解決で落ちると compute-result が残らず
   `finish-group` を閉じられない。trap の後ろへ戻した。
3. queue 状態検査が対象 queue の行に束縛されておらず、別 queue が ENA/ACT なら通っていた。
4. テストで実 `qstat` の記録 fixture を手書き文字列へ置き換えていた箇所を fixture へ戻した。
5. harness の `load_policy` 差し替えが `path` 引数を無視しており、どの driver 呼出しから
   `--policy` が落ちても A-6 のまま通っていた。

## 変異 matrix

baseline PASSED、M1〜M6 が 6/6 KILLED、SURVIVED 0 / MISMATCH 0 / TIMEOUT 0。

事前登録の訂正が 2 件ある (erratum)。

- **M3**: 初回登録「study→shape map の shape 一致要求を削除」は、workload 数検査と cell 数検査が
  相互に支配し単独帰属が成立しなかった。両層同時変異へ再照準した。単独条件への帰属は主張しない。
- **M7**: 初回登録「A-2 の policy bytes SHA / protocol SHA の比較を削除」に対応する production
  変異位置が存在しなかった。`load_policy` は現行 bytes から SHA を計算するだけで凍結値と比較
  しない。変異としては撤回し、A-2 不変性の golden 回帰テストとして残した。D1169 が求める
  「規則が恒真な飾りでないことの負例」は M5 が担う。

probe 走 (全件 SURVIVED 期待で観測 node を集める回) では、`tools/mutation_worktree.py` の
共有木事後検査が失敗した (rc=125)。ledger 自体は完走しており、本 wave 中に local main へ
23 commit が着地している以上、他 session の churn に帰属する。本走は `tools/mutation_harness.py`
を自 worktree に対して回した (固定 HEAD 束縛・復元時の内容比較・flock・逐次 flush・signal 復元は保たれる)。

## 主張の上限

いずれも A-2 にも等しく存在する性質であり、本走の判定経路を弱めるものではない。

1. **事前登録 policy SHA が proof chain へ結ばれていない。** preregistration は policy SHA を
   持つが submission / completion / acquisition の必須 field に無い。ただし certification result
   自身は `policy_sha256` と `policy_bytes_base64` を持ち materialize 時に照合する。また policy は
   tracked file に限られ、job body が HEAD 一致と tracked clean を要求するので、実行された
   policy bytes は `source_commit` へ git 経由で束縛される。D1257 に従い本走では足さない。
2. **full v3 の materializer は report を evidence から再導出しない。** partial v4 は
   `report == expected` の全体一致を要求するが、full v3 は identity と field 形状しか見ない。
   本走の report は `collect` が同一 process 内で evidence から導出したものである。
3. **投入の重複防止は運用上の保証である。** `qstat` snapshot と `qsub` の間の競合窓を閉じる
   永続 claim は無い。本走は単一 submitter が投入直前に 0 件を確認して 1 回だけ投入した。
4. **単独性確認の射程。** campaign は各 verify / bench の前に割り当てノード上で `pgrep` による
   競合検出を行うが、他 tenant の PID が見えることを立証する canary は未実装である。
   今回は campaign 自体が始まっていないので、この確認は 1 度も走っていない。
5. **既存 A-2 receipt chain は現配置では再検証できない** (`submission_cwd` が消えた worktree を
   指す)。A-6 導入前の版でも同じ拒否になるため本 wave の回帰ではない。
6. correctness 実行の argv と executable hash は既存 pipeline が独立記録しない (D1257)。
   `a4_noise_floor_status` は `open`、`global_minimality_established` は `false`。

## 参考 — トレース切り捨ては起きていない

`output/insights/2026-09-02_b10-trace-truncation/README.md` が、read-heavy の長時間走で疑われた
トレース切り捨てを否定している。検査器は `observed_commits == expected_commits`・
`missing_txids == 0`・`framing_violations == 0` を要求し、287 反復すべてで一致した。
本 wave の測定が取れた場合、read-heavy の correctness 判定は全取引を覆うと言える。ただし同一
process 内の共通要因で counter とトレースが同時に落ちる形は残る (同 README の限界節)。

## この policy file の版番号について

`paper_story_a6_certification.v2.json` の `.v2` は **policy schema の版**
(`paper-story-a2-certification-policy/v2`) を指し、A-6 の文書世代ではない。**A-6 の v1 は
存在しない。** A-1 側の `v1` / `v2` / `v3-pilot` は文書世代を数えているので読み方が異なる。
policy 本文には注記を置けない (`_TOP_LEVEL_KEYS` が exact key set のため)。

---

## 追記訂正 (2026-09-03) — 「23 分」は検査器単体の費用ではなく、帯の max でもない

**上の本文は 1 バイトも変更していない。絶対規律 7 に従い、追記でのみ訂正する。**
walltime を `12:00:00` とした判定も、本書の他の結果も、昇格も降格もさせない。

「walltime を 06:00:00 から 12:00:00 へ変えた理由」の節に、2 つの誤りがある。

**(1) 帰属の誤り。** 「直列性検査は 1 回 23 分の実測があり」と書いているが、この所要は
検査器そのものの費用ではない。一次資料
(`output/insights/2026-09-02_b10-trace-truncation/README.md` の「所要の内訳と、並列化への入力」節)
は、これが WAL の時刻差による**混合区間**だと明記している。内訳はベンチマーク本体 (extime 3 秒)・
トレースの書き出しとスレッド終了時の flush・C 行の数え直し・標準出力の解析・直列化可能性検査・
一時ディレクトリの作成と削除・WAL への書き込みであり、同資料は「**『検査器そのものの費用』では
ない**」「どれが律速かは、この時刻差からは分離できない」と書いている。

**(2) 積み方の誤り。** 「full-scale 10 回を max 23 分で見積もると 3.83 時間」と書いているが、
23 分は観測帯の max ではない。保存されている帯は、read-heavy の高 commit 3 変種で 1 反復あたり
**1346.9-1465.6 秒 (約 22.45-24.43 分)** であり、23 分は上端ではなく帯の中ほどである。

| 量 | 本文の値 | 上端 1465.6 秒で積み直した値 |
|---|---:|---:|
| 1 反復 | 23 分 (max と表記) | 約 24.43 分 |
| full-scale 10 回 | 3.83 時間 | **約 4.07 時間** |
| 12:00:00 の倍率 | 約 3.1 倍 | **約 2.95 倍** |

**walltime `12:00:00` という結論は動かない。** D193 の「中断 attempt は自動回復しない」という
非対称性が、枠を広く取る別の理由として残るからである。倍率が 3.1 から 2.95 へ下がっても、
12 時間枠は積み直した 4.07 時間の外側にある。

同じ 2 つの誤りは `docs/decisions.md` の D1485 と D1489、および
`docs/archive/worklog-phase3-0902-1187.md` にもある。同 1189 の T-2191 は帯が
「22-24 分」へ既に直っており、残るのは (1) の帰属だけである。
訂正の全文と検算は
`output/insights/2026-09-02_t2229-t2230-verify-cost-erratum/README.md` にある。

## 追記 (2026-09-04) — D1529 の但し書き: 欠測 attempt を含む母集団から出た数値主張

**上の本文と追記訂正は 1 バイトも変更していない。** 但し書きは値を無効にするものではなく、
読み手が根拠の強さを区別できるようにするためのものである (D1529)。既存の訂正
(上の追記訂正、D1554) も変えない。

「欠測 attempt」とは、campaign 記録上 commit (変種の認証確定) に到達しないまま打ち切られた
実行を指す。read-heavy の `constant-mu2` 変種 `292d58f1dad8` では初期確認 (legacy) 1 反復と
本規模 (performance) 3 反復だけが記録に残っている。

- **「walltime を 06:00:00 から 12:00:00 へ変えた理由」節の「1 回 23 分」と、追記訂正の帯
  1346.9-1465.6 秒 (約 22.45-24.43 分)・約 4.07 時間・約 2.95 倍:** 母集団は read-heavy で
  commit 数が飽和した 3 変種の本規模反復 (反復数 5・5・3) で、3 反復だけの 1 変種が欠測 attempt
  である。欠測 attempt を除いた再計算は行っていない。
- **同節の「5 時間で 15 点中 3 点」:** 5 時間は撤去された request `965996` の走行時間を指すが、
  その計測区間は現記録から確定できない (request 全体の Elapse は 20950 秒 = 約 5 時間 49 分)。
  いずれの区間でも、完了 3 変種のほかに欠測 attempt の初期確認 1 反復と本規模 3 反復の時間を
  少なくとも含む。終了直前に次の反復が始まっていたかは記録が無く不明である。「15 点」は登録格子の構造数で欠測とは無関係である。
  欠測 attempt の時間を除いた再計算は行っていない。
- **同節の「max 23 分」「3.83 時間」「約 3.1 倍」:** 追記訂正が既に誤りと確定した旧値である。
  母集団は上と同じで、本但し書きはその訂正を変えない (旧値は誤りのまま残る)。

## 追記 (2026-09-07、[T-2198]) — 停止原因を解消したが、本 attempt の値は取り直さない

本 attempt が `indeterminate` になった原因 (計算ノードの外部 network 不在で FetchContent が落ちる、
F808) は、D1524 / D1693 に従って解消した。閉じた trace0 configure 文法へ FetchContent の枠を
厳密な期待値として足し、認証経路の測定 build を staged 依存へ配線した。

**本 attempt の値は取り直さない (絶対規律 7)。** 本 attempt は旧 policy に束縛されたまま残る。

- 本 attempt が束縛する A-6 policy: bytes `4ca15d071f0bc10febe3274d0523b59f0e4903bf612ff050bef7e6728a3700d4`、
  protocol `a73bc3a0eabd1bcb960779c9b61b20983ef3cfb88d76d50c073e9ced4f6be445`
- 現行 (2026-09-07 以降) の A-6 policy: bytes `8969a7e4ee740a94ec12084c89ef88a37ebd255073cfb0122245113a295b87a8`、
  protocol `21427e71793ea744777d11bd90429ce2db1a8d3333ea9e2e0f227ecf377c25dc`

**両者は一致しない。** A-6 の read-heavy 認証は新しい hash に束縛された新しい attempt で取り直す。
**本追記の時点でその実測はまだ行っていない。** 論文 §8 の但し書き 2 は外れていない。

**旧 submission receipt は現行の exact qsub env 契約でも再受理されない** — 新しい環境変数
`IZANAGI_A2_THIRD_PARTY_SOURCE_ROOT` が exact key 集合へ入ったため。これは新しい破壊ではなく、
protocol hash と job body hash の変化に既に含まれている。

なお `protocol_sha256` が束縛するのは policy document であって、Python 側の判定式や qsub env の
exact 集合ではない。この限界は記録として残す (絶対規律 7)。

詳細は `output/insights/2026-09-07_t2198-trace0-fetchcontent/README.md`。

## 追記 (2026-09-18、[T-2321]) — 「5 時間」の記録境界と旧所要の区別

上の但し書き (D1529) の「5 時間」の計測区間は引き続き未同定である。request `965996` の Started
(2026-09-02 01:07:49 JST) からの秒表示差として、3 変種目の認証確定までは 16,387 秒、WAL 末尾 (4 変種目の
本規模 3 反復目) までは 20,682 秒、Ended までは 20,946 秒 (scheduler の Elapse 記載は 20950S)。欠測 attempt の
本規模 3 反復を含むことは WAL 末尾まで等の区間では確認できるが、旧所要への帰属は確定しない。根拠と精度は
`docs/b10-multinode-formal-run-design.md` §1 の同名追記を参照。上の本文・但し書き・追記訂正は 1 バイトも
変更していない。値を無効にせず、欠測 attempt の時間を除いた再計算は行わない。
