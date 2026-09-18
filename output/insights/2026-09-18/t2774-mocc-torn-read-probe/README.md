# [T-2774] stock mocc (RWLOCK 版、e9e477ca) の静的反例候補 (a) の計算ノード実走検証 — G2 signal は witness を切った producer でだけ再現し (2/40・3/40・2/40)、discriminator の観測条件では 0/40

作成 2026-09-18 (wave `dev-wave-t2774-mocc-torn-read-probe`、base main `d2ebef7a4`)。一次資料は repo 外の job dir
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2774-mocc-torn-read-probe/` (probe・走ごとの JSON・G2 走の生 trace・codex 逐語)。
本文は **非 certifying の観測記録** であり、headline・certified 選択・floor・oracle・fitness の根拠に使わない。

## 0. 問いと範囲、認可しないこと

- 問い: T-2757 insight §3.2 (a) = 「cold 読みの counter 検査 → body 読み → 版の再読と、validation の版比較 → counter 読取の
  別読みで、版と本文が食い違う読み (torn read) または旧版読みが commit しうる」を、固定 cell (3 秒・48 thread・10,000 record・
  rratio 50・rmw 0・max_ope 10・zipf 0.9) の実走で再現 / 未再現し、T-1943 の payload lineage discriminator で読み値の出所を照合する。
- 範囲外: (b) hot 読みの `absent` 非検査 (DELETE 経路)。仮説 cell (record 数・skew・value size の変動)。CCBench 本体の改変 (D16 / D18 / D20 に
  従い本 insight の構造化まで。上流 PR / push は人間判断)。
- 認可しないこと: mocc の certified 昇格判定、pin 前進 (D2114 項 3 / D1603)、変異探索の解禁 (D2134)。規律 2 (verifier / discriminator の
  受理集合は 1 文字も変えていない — 段 6 レビュー A が `git diff` で確認)、規律 7 (T-1892 の 5/42、T-1943 の `no-g2` は各旧束縛で保持)。

## 1. 結論 (先に上限を書く)

段 6 レビュー A の主判定文案を採用する。

> BACK_OFF=0 の固定 cell では、producer・計装・witness・診断変更の鎖に沿った G2 signal 検出数は 2/40、3/40、2/40、0/40、0/40 だった
> (先頭 2 arm の cycle ゼロ走は現行 verifier で indeterminate)。7 件の cycle 形は validation の別読みによる静的候補 (a) と整合するが、
> すべて witness off で、payload-lineage 識別には到達しなかった。witness 有効時の未再現は観測者効果の仮説と両立するものの、診断効果、
> 各間隙の寄与・必要性・根因、および hook / verifier 仮定の分岐は確定しない。

要点:

1. **静的所見 (a) の順序は現物で成立する** (§3)。実行順序 (cold / RLL 状態、2 load 間の順序) を直接観測した走は無い。
2. **G2 signal (長さ 2・両辺 rw・別 thid・同 epoch・commit tid 差 1、T-1892 の 5 件と同形) は、`BACK_OFF=0` かつ witness (T-1943 の
   payload watermark) を無効にした producer で再現した**: T-1892 の producer そのもの (058d0c4e) 2/40、e9e477ca 素 3/40、
   e9e477ca + X/P 計装 2/40。合算 7/120 = 0.058 (CP 95% [0.024, 0.117])。T-1892 の 5/42 = 0.119 (CI [0.040, 0.256]) と区間が重なる
   (片側 Fisher 0.237)。**環境の同等性を実証したものではない。**
3. **discriminator の観測条件 (e9e477ca + X/P 計装 + witness on) では 0/40。** `BACK_OFF=1` (Q1) の 56 走も 0/56。
   T-1892 5/42 に対する片側 Fisher は 0.031 (0/40) / 0.013 (0/56)。witness の on/off 直接比較 (instr-nowit 2/40 対 instr-wit 0/40)
   は 0.247、witness off 合算 7/120 対 instr-wit 0/40 は 0.128 (いずれも有意ではない)。**discriminator は 1 件も発火せず、
   `supported` / `contradicted` の証拠は 0 件。読み値の出所照合は未達。**
4. **観測者効果の候補 (静的根拠あり、実測は上の率差まで)**: witness は各 UPDATE の publish (`M:1195`) の直後に
   `izanagi_mocc_g2_emit_post_store` (S 行の書出し) を挟み、`unlockCLL()` (`M:1207`) までの区間を伸ばす。(a) の validation 側の順序は
   「R の版読み → W の publish + unlock → R の counter 読み」で、R の 2 load (数〜数十命令) がこの区間を跨ぐ必要があるため、区間が伸びる
   ほど跨ぎにくくなる。witness は S 行だけでなく L 行・stamp の書込み / decode も足すので、on/off 比較はこれらをまとめた介入である
   (レビュー A)。曝露量も変わる: 走あたり平均 commit 数は鎖の順に約 797,192 → 784,935 → 711,199 → 541,601 → 543,065 (固定 3 秒の
   走あたり検出率であり、同数の commit 機会に対する比較ではない)。**T-1943 の 1 cell `no-g2` は「その走で識別対象を得なかった」と読む。**
5. **診断 patch (対照 build) は witness on の arm でしか走らせておらず (0/40)、対照の instr-wit も 0/40 なので、必要性・寄与の分離・根因は
   判定できない。** 診断 patch は「固定した既存観測に対する attempt 単位の追加拒否」であり (cold 側 abort は read_set_ 登録前で
   `construct_RLL()` の温度更新の対象外)、実行全体の commit 数の単調減少は主張しない (Q2 総 commit: instr-wit 21,664,020、
   diag-wit 21,722,599)。
6. **`BACK_OFF` (適応 backoff) の効果は分離できていない。** Q1 (=1) は witness on の 2 arm だけで、witness off の BACK_OFF=1 arm が無い。
7. 原因 3 分岐 (実装 / hook / verifier 仮定、T-1892) は本 wave でも分離していない。

## 2. 実行の束縛

- outer: main `d2ebef7a4` (wave 4 worktree、いずれも同 base)。CCBench: `e9e477ca1b55348ab4530de0b1cf663ce4555290` (hook branch 先端、
  witness あり) と `058d0c4e5f237d88ec1c2ebe0739113d82906e47` (T-1892 の producer、trace hook のみ)。gitlink は `511c9538` のまま動かしていない。
- patch: X/P 計装 `patches/instr-mocc-lock-coverage.patch` (repo、D1686、sha256 `e9e65b78…`)。診断 patch
  `mocc-close-version-counter-gap.patch` (job dir `probe/`、sha256 `8a25bd0a5687437269c720cb34a4b26024a6f1f119adf1c16281d455b9ecaa1d`、
  1,168 byte、37 行、X/P 適用後の source に対する diff、`#line 350` / `#line 1038` で論理行番号保持。逐語は `verbatim/diag-patch.md`)。
  診断適用後 source の sha256 = `1c5da7c8439144d02621071622e5eba31f1ff583c4fbda5efdfe7483c2c3168a` (Q2 4 block の binding と一致、
  レビュー A が memory 上で再構成して照合)。X/P 適用後 source = `bd0add59890a…`、058d0c4e 素 = `1124788d7fba…`。
- runner `t2774_probe.py` (job dir `probe/`、Codex `role=author` が作成、fix 3 巡。repo には入れない。逐語は `verbatim/probe.md`)。
  実走ごとの版: v2 (fix 1 後、sha256 `77e8d3b16e3ec3504c3fa978ab8a35e136e60608de80e2545d8d86414bd56987`、519 行) = smoke と Q1、
  v3 (fix 2b 後、`24e03cd15c8768e4f25aa076e0f965ac3aa592ab8761bfa71265317923c28d97`、655 行) = Q2、
  v4 (fix 3 後、`2e2ddea834f782abb7a671b42d8a57f82ac8b82d7ac90d23965ad3ca3fd41c00`、704 行、36,746 byte) = 再分類集計 (§5.1)。
  v1 (author、`ef668a7981477bc1431c3767824aecb47636dc525ce8796b919d47ea0a5b98e9`、524 行) は未実走。job dir `probe-snapshots/v1..v3/`。
- build: gcc-11 (`/usr/bin/x86_64-linux-gnu-g++-11`)、policy `tools/pegasus/mocc_trace_v1_policy.json` (sha `66ea7135…`)。
  Q2 の configure define = `-DCCBENCH_TRACE=1 -DCCBENCH_BACK_OFF=0 -DCCBENCH_BACKOFF_FIXED=-1 -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1
  -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=0` (T-1892 / T-1943 の pilot と同一)。Q1 は
  `-DCCBENCH_BACK_OFF=1 -DCCBENCH_KEY_SORT=0 -DCCBENCH_TEMPERATURE_RESET_OPT=1` (T-2294 driver の genome の流用、`BACK_OFF` だけが
  CCBench 既定と異なる実効差)。**binary の sha256 は block ごとに異なる** (scratch path の埋込み等が候補、命令列の一致は未確認 —
  レビュー B)。arm 別 source file sha は 4 block で一致。
- 実行 argv: `-ycsb_tuple_num=10000 -thread_num=48 -ycsb_zipf_skew=0.9 -ycsb_rratio=50 -ycsb_rmw=0 -ycsb_max_ope=10 -extime=3`。
  witness on の走は `IZANAGI_MOCC_G2_WITNESS=1` + `IZANAGI_MOCC_G2_WITNESS_DIR`。
- 走: smoke `5065.nqsv` (bnode003)、Q1 = `5068` (bnode002) / `5069` (bnode003) / `5070` (bnode012) / `5072` (bnode022)、
  Q2 = `5142` (bnode004) / `5143` (bnode006) / `5144` (bnode009) / `5145` (bnode022)。queue gen_S、policy nodes 1、generic dispatch
  (`tools/pegasus/dispatch_compute.py --task generic`、4 worktree から並行投入。pending orphan hold は全 9 log で作成→解除の正常経路)。
  各 block の `result.json` に repo HEAD・pin・patch sha・source file sha・binary sha・toolchain・configure argv・hostname・時刻を記録。
  arm 定義 `probe/arms-q2.json` (sha256 `8d9c91af7a60…`)。
- verifier: `python3.10 -m orchestrator.verifier <trace_dir> --json --protocol mocc --ccbench-root <arm の source> --expected-commits N`
  (現行 main の verifier、変更なし)。discriminator: `orchestrator/campaign/mocc_g2_discriminator.py` (変更なし)。
- 単独性: runner は準備前と各走直前に `_assert_single_tenant` 相当を呼び全走完走した。node 専有の実証 (process 一覧) は取っていない (レビュー B N1)。

## 3. 順序論証 — 現物での検算と被覆境界

(段 2 plan §1、段 3 レンズ A S1 / S2 の検算を親が現物で確認。行番号は e9e477ca、`M:行`。)

- cold 読み (316〜356): tidword 読み (320) → `ldAcqCounter() == W_LOCKED` の spin (322) → absent 検査 (341) → body 読み (347〜348) →
  tidword 再読 (350〜352)。lock 状態は tidword に無いので、counter 検査後に writer が w_lock を取り memcpy (1169) を始めても、publish (1195) 前なら
  再読は T0 のまま抜ける。**(i) の順序は排除されない。**
- validation (1008〜1039): tidword 比較 (1010〜1013) → counter 読み (1024) の 2 load。writer の publish (1195) + `unlockCLL()` (1207) がこの間に
  入ると両検査を通る。1038 の `max_rset_` 更新は再比較ではない。**(ii) の順序は排除されない。**
- **(ii) だけで、本文の不整合無しに長さ 2・両辺 rw の cycle が commit されうる**: W が x を施錠 → W が y を検査 (R 未施錠) → R が y を施錠 →
  R が x の版 T0 を読む → W が x を publish + unlock → R が x の counter 空きを読む → 両者 commit。前提 (被覆境界) = x≠y、両者とも相手の
  read key を自分の write set に含めない、cold・RLL 空、W の y 検査が R の y 施錠より先。同 epoch・tid 差 1 は `max_rset_` (1038) と
  commit tid = 最大版 + 1 (1118〜1131) の帰結であって必然ではない。
- (i) が commit まで届くには (ii) も要る (validation が版不一致か W_LOCKED で拒否するため)。
- T-1892 の 5 件と本 wave の 7 件はいずれもこの形と整合するが、形の一致は (ii) 固有の証拠ではない。今回は各辺の rw reason が 1 本ずつ (計 14 本)
  で、歴史的 ordinal 32 の「一辺 2 reason」は無い。

## 4. 実走の設計

- Q1 (裁定時の主設計、後に観測へ格下げ): e9e477ca + X/P 計装、witness on。arm = `instr` / `diag` (診断 patch)。4 node × 14 組 = 各 56 走
  (AB / BA 交替)。`BACK_OFF=1` は runner が T-2294 driver の configure を流用した親の見落としで、Q1 の 3 block 完了後に判明。
- Q2 (主解析、Q1 の 3 block 完了後・走行前に事前登録 = job dir `s4-ruling.md` 追記 2): configure を pilot と一致 (`BACK_OFF=0`)。5 arm を
  因子 1 つずつの鎖: `p058-plain` (058d0c4e、patch なし、witness code なし) → `e9-plain-nowit` (e9e477ca、patch なし、witness env off) →
  `e9-instr-nowit` (+X/P) → `e9-instr-wit` (+witness on = discriminator の条件) → `e9-diag-wit` (+診断 patch、観測のみ)。
  4 node × 10 round × 5 arm、round ごとに開始 arm を回転 (各 arm が各位置に 2 回)、各 arm 40 走。K は結果を見て増減していない。
- 各走: 別 trace dir (+ witness dir) → verifier (timeout 300 s) → G2 走は manifest 2 種 + discriminator (witness on かつ pin e9e477ca の
  arm のみ) → 走ごとに JSON を逐次保存、G2 走の生 trace / witness を退避、非 G2 の raw は削除。

## 5. 結果

### 5.1 Q2 (主解析、BACK_OFF=0) — `arm-B/summary-q2.json` (sha256 `1ef9af1773a828a2…`、v4 runner の `summarize --reclassify`)

| arm | pin | X/P | witness | G2 signal / 40 | certified no-G2 | indeterminate | 率 | CP 95% |
|---|---|---|---|---|---|---|---|---|
| p058-plain | 058d0c4e | 無 | 無 (code 自体無し) | **2** | 0 | 38 | 0.050 | [0.006, 0.169] |
| e9-plain-nowit | e9e477ca | 無 | off | **3** | 0 | 37 | 0.075 | [0.016, 0.204] |
| e9-instr-nowit | e9e477ca | 有 | off | **2** | 38 | 0 | 0.050 | [0.006, 0.169] |
| e9-instr-wit | e9e477ca | 有 | on | **0** | 40 | 0 | 0 | [0, 0.088] |
| e9-diag-wit | e9e477ca + 診断 | 有 | on | **0** | 40 | 0 | 0 | [0, 0.088] |

- **plain 2 arm の「率」は全 40 走中の G2 signal 検出数であり、cycle ゼロの走は X/P emitter が無いため現行 verifier (`e4c949f08`、09-03) で
  `indeterminate` になる (integrity の違反 counter は全走 0)。判定確定率ではない** (レビュー A S1 / B)。CP 区間は独立 Bernoulli を仮定した
  検出 signal の率に対するもの。
- 失敗 (timeout / rc 異常 / JSON 不正) 0、未開始 0、benchmark rc≠0 は 0。**原本 `result.json` の 75 走 (Q1/Q2/Q3/Q4 = 19/19/20/17) は
  v3 runner の分類誤り (`rc=3 ⇒ serializable False` を仮定) で `failure` と記録されており、v4 の `--reclassify` が保存済み verifier.json
  から `indeterminate` へ訂正した** (summary の `inputs.status_changes` に全件。原本は書き換えていない)。
- G2 走 7 件は全件 total_cycles 1・anomaly 1、長さ 2、両辺 rw、別 thid、同 epoch、commit tid 差 1、key は 0x0 / 0x1 / 0x2 / 0x4:

| block / run | cycle txid | thid | commit 版 |
|---|---|---|---|
| Q1 (bnode004) / 010-p058-plain | 340513, 340514 | 7, 4 | (33,112), (33,113) |
| Q2 (bnode006) / 040-e9-plain-nowit | 748934, 748936 | 33, 16 | (69,37), (69,38) |
| Q3 (bnode009) / 036-e9-instr-nowit | 424162, 424163 | 28, 37 | (46,67), (46,68) |
| Q4 (bnode022) / 032-e9-instr-nowit | 182647, 182648 | 9, 2 | (20,328), (20,329) |
| Q4 / 040-e9-plain-nowit | 370499, 370500 | 11, 9 | (36,530), (36,531) |
| Q4 / 043-p058-plain | 676564, 676565 | 25, 29 | (62,137), (62,138) |
| Q4 / 044-e9-plain-nowit | 88887, 88888 | 24, 13 | (9,1219), (9,1220) |

- 率の比較 (片側 Fisher、参考値。node 内相関・回転順・複数比較は未調整): X/P 追加 3 対 2 = 0.5、witness 追加 2 対 0 = 0.247、
  診断追加 0 対 0 = 1.0。witness off 合算 7/120 対 instr-wit 0/40 = 0.128。T-1892 5/42 対 instr-wit 0/40 = 0.031、対 p058-plain 2/40 = 0.237。
- discriminator: 発火 0 件 (witness on の arm に G2 が無い)。witness off の G2 走は `not-run (witness-off)`。`comparisons` 0 件。
- 所要: 1 block 50 走 = 1,100〜1,111 秒 (runner 内部)、verify 10.5 / 18.6 / 22.7 秒 (最小 / 中央 / 最大)、run 3.07 秒。

### 5.2 Q1 (BACK_OFF=1、観測) — `arm-B/summary-q1.json` (sha256 `d1722280f515b6d2…`)

instr 0/56、diag 0/56 (全走 certified serializable、CP 上限 0.064)、失敗 0。T-1892 5/42 に対する片側 Fisher 0.013。
1 block 28 走 = 635〜646 秒。

### 5.3 smoke

`5065.nqsv` (bnode003): 会計 80 秒 (runner 内部 75.6 秒) で完走 (hydrate + gflags/glog build + checkout ×2 + masstree warm-up + build ×2 +
2 走 + verify ×2)、両 arm serializable。Q1 の分母に含めない。

## 6. 解釈と限界

- 「(a) と整合」の意味: G2 の形 (長さ 2・両辺 rw) と発生条件 (BACK_OFF=0・計器なし・hot key) が (ii) の静的順序に反しない、まで。
  実行順序の直接観測ではなく、分岐 2 (hook の記録取り違え) / 分岐 3 (verifier の版順序仮定) は排除していない。
- discriminator の `supported` / `contradicted` は「報告された rw 辺の reader version の producer と payload 先頭 8 byte の stamp producer
  の一致 / 不一致」だけを言い、(ii) / (i) と一対一には対応しない (段 2 plan §2 の限定表、段 3 レンズ A MF2)。本 wave では比較対象が 0 件。
- 観測者効果: 静的根拠は §1 4。率差は方向が整合するが有意水準に届かない。X/P 計装 (3 検査点 + P の集合検査) は率を下げていない
  (instr-nowit 2/40 対 plain-nowit 3/40)。
- BACK_OFF: Q1 (=1) と Q2 (=0) は witness on では両方 0 なので効果を分離できない。T-1892 との条件一致のため Q2 では 0 に固定した。
- 診断 patch: 対照の instr-wit が 0/40 なので、`e9-diag-wit` 0/40 は何も言わない。診断 patch が受理集合を縮小する方向だけであること
  (validation 再読は追加拒否、cold 側は retry でなく abort) は静的に確認 (段 3 レンズ A S3、段 6 レビュー A)。
- 標本: 各 arm 40、率 0.05〜0.075。率差の検出力は低い (K=40 の等標本 Fisher は理想条件でも約 57%)。
- hot 読み比率・温度到達は未計測。value size の効果は未実測 (親 brief の P2 は撤回)。
- runner の集計境界 (再利用時): 正の `total_cycles` を現象名の検査なしに `g2` と呼ぶ、N は保存済み走数から作る (未開始走の分母規則なし)。
  今回は全 anomaly が G2、未開始 0 で影響なし (レビュー A N1 / B N3)。discriminator は rc=3 (indeterminate、serializable true) の入力を
  `_validate_verifier` で拒否する既存不整合があるが、本 wave は cycle 正の走だけを渡すので影響なし (レビュー A N2)。

## 7. CCBench 側への扱い

- (a) の静的所見と、計器なし producer での G2 signal 再現は、第三者 submodule の実装に関する所見でありうる。上流 PR / push は人間判断 (D16)。
  診断 patch は job dir に留め、repo にも submodule にも入れていない。
- T-1943 の witness 設計への含意: witness on で G2 が出ないなら、payload lineage による原因識別はこの計器では到達しにくい。計器を軽くする
  (S 行を unlock 後に出す等) 案と、診断 patch を witness off で走らせる対照は次の一手 (worklog 新規 T)。

## 8. 見つけた欠陥 (本 wave では修正しない)

1. `tools/pegasus/mocc_trace_pilot.sh` の hydrate (1534 行) が素の `python3` で `fetch_third_party.py` を呼び、T-548 (09-16) 以降は
   `orchestrator/verifier/parse.py:71` の 3.10 専用式 (module 直下の `bool | Literal[...] | None`) に推移的に到達して計算ノード
   (python3 < 3.10) で rc=2 (job `4936.nqsv`、9 秒)。checker (1756〜) / verifier (2203〜) gate は ≥3.10 選択済みで、hydrate だけ未追随。
   1493 行の compiler gate も素の `python3` で repo module を import するが 4936 では通過している (段 3 レンズ B N1)。
   修正設計 = 段 2 plan v2 §4 (同型の interpreter 選択 block `HYDRATE_PY` + 契約 test 1 本)。failures fragment に記録。
2. 同 pilot は X/P 計装 patch を当てないので、`e4c949f08` (09-03) 以降は mocc の走が `certified` にならず `--t1943-g2-discriminator`
   mode は `indeterminate` しか出せない (段 3 レンズ A MF1)。T-1943 job (08-28) はこれより前。pilot の復旧は次の一手 T。

## 9. 段 2〜6 の所見と裁定

- 段 2 plan (v2、1 本目は上流 classifier に遮断、F102 再発): N=42 / K=24、診断 patch = validation 再読 + cold 側 abort、`⇔` の限定、
  `0/K` は根因確定でない、仮説 cell 不採用、decisions fragment 0。
- 段 3 レンズ A: must-fix 3 (X/P `evidence-present` 条件で素の e9e477ca は全走 indeterminate → producer 変更 / 対応表の限定 / 0-K 撤回)、
  should 3、nit 3。レンズ B: must-fix 5 (終端 file の記述 / 生死確認の成功条件 / timeout 300 s・逐次保存・walltime / 根因撤回 /
  集計の分離)、should 2、nit 3。**全件 real・採用** (`s4-ruling.md`)。腕 A (pilot 経路) と scope 0 (repo の job script 修正) は撤回、
  単一計器 = job dir runner。
- 段 5 author 1 本 + 段 6 fix 3 巡 (policy / cwd、configure 一致 + arms-json、classify 是正 + reclassify)。fix 2 (1 本) は親が途中で停止
  (configure 要件を足すため、file 未変更)。
- 段 6 レビュー A (正しさと主張): **GO** (観測記録として。根因確定・診断効果には NO-GO)、must-fix 0、should 3 (検出率と判定確定率の
  区別 / 識別未到達・診断効果未確認を主判定に / cold abort の適応挙動と曝露量)、nit 2。レビュー B (実行と収集): **GO**、must-fix 0、
  should 1 (runner の版を実走ごとに束縛 → §2)、nit 3。全 314 走の JSON と G2 raw 336 file (2,007,636,727 byte) の manifest 一致を独立検算。
  所見は全件 real・採用 (本文へ記述で反映。実装変更なし)。
- 変異 matrix: repo の実装面差分 0 (probe は job dir、docs のみ) → DW-S04 により免除。受入全走は land 前に実施 (結果は worklog)。

## 10. 再現資料 (job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2774-mocc-torn-read-probe/`)

- `probe/t2774_probe.py` (v4)、`probe/mocc-close-version-counter-gap.patch`、`probe/arms-q2.json`、`probe-snapshots/v1..v3/`。
- `arm-B/{smoke,B1..B4,Q1..Q4}/result.json` と `runs/<ordinal>-<arm>/` (run.json / verifier.json / discriminator.json / stdout / stderr、
  G2 走は trace-manifest.json + trace/、witness-manifest は witness on の G2 走のみ = 0 件)。`arm-B/summary-q1.json`、`arm-B/summary-q2.json`。
- `dispatch-{smoke,B1..B4,Q1..Q4}.log` (dispatcher の会計付き log)、`attempts-A/` (撤回した pilot 経路の job 4936 の submit receipt)。
- `s1-brief.md`、`s4-ruling.md` (追記 1・2 を含む)、`codex/` (prompt・plan・consult・author・fix・review の全文と launcher)、`HANDOFF.md`。
- 投入は `codex/launch-q2.sh` (Q2) / `codex/launch-block.sh` (Q1) / `codex/launch-smoke.sh`。

## 11. verbatim 一覧 (本 dir `verbatim/`)

`s1-brief.md`、`s2-plan.md`、`s3-lensA.md`、`s3-lensB.md`、`s4-ruling.md`、`s5-author.md`、`s6-fix1.md`、`s6-fix2b.md`、`s6-fix3.md`、
`s6-reviewA.md`、`s6-reviewB.md`、`prompt-plan.md`、`prompt-consult-A.md`、`prompt-consult-B.md`、`prompt-author.md`、`prompt-fix1.md`、
`prompt-fix2b.md`、`prompt-fix3.md`、`prompt-review-A.md`、`prompt-review-B.md`、`diag-patch.md`、`probe.md` (runner v4 の逐語)、
`arms-q2.json.md`、`summary-q2.json.md`、`summary-q1.json.md`、`s2-plan-attempt1-salvage.md` (遮断された 1 本目の途中 message)。
