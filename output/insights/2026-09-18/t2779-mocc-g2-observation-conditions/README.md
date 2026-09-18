# [T-2779] mocc G2 の観測条件の分離 — 通常 5/120、診断 0/120、backoff 2/120

作成 2026-09-18 (wave `dev-wave-t2779-mocc-g2-observation-conditions`、base main `c8e8dc06f`)。一次資料は repo 外の job dir
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2779-mocc-g2-observation-conditions/` (runner v5・走ごとの JSON・G2 走の生 trace・codex 逐語)。
本文は **非 certifying の観測記録** であり、headline・certified 選択・floor・oracle・fitness の根拠に使わない。

## 0. 問いと範囲、認可しないこと

- 問い (T-2774 insight §1 5〜6・§7 の次の一手): discriminator の観測条件 (witness on) で G2 signal が 0/40 になる理由を分離する。
  (1) witness を軽くする案の静的設計 — S 行の書出しを `unlockCLL()` の後へ移す。(2) 診断 patch (validation の版再読 + cold 側 abort) を
  witness off で走らせ、`e9-instr-nowit` と同一 block で率を比較する。(3) `BACK_OFF=1` の witness off arm で適応 backoff の効果を witness と
  分離する。cell は T-2774 と同じ固定 cell (3 秒・48 thread・10,000 record・rratio 50・rmw 0・max_ope 10・zipf 0.9)。
- 範囲外: 軽量 witness の実走 (静的設計まで)、pilot (`mocc_trace_pilot.sh`) の復旧 (T-2780)、hook branch への commit、仮説 cell、
  CCBench 本体の改変 (D16 / D18 / D20 に従い本 insight の構造化まで。上流 PR / push は人間判断)。
- 認可しないこと: mocc の certified 昇格判定、pin 前進 (D2114 項 3 / D1603)、変異探索の解禁 (D2134)。規律 2 (verifier / discriminator の
  受理集合は 1 文字も変えていない)、規律 7 (T-1892 の 5/42、T-1943 の `no-g2`、T-2774 Q1 / Q2 は各旧束縛で保持)。
  **陰性結果を「G2 が無い」証拠にしない。**

## 1. 結論 (先に上限を書く)

通常 arm は 5/120、診断 arm は 0/120、BACK_OFF=1 は 2/120 の G2 signal を得た。
診断介入側の低下方向の片側 Fisher は未調整 p=0.0299507441、backoff は p=0.2230864755。
前者は固定条件で2変更を束ねた介入と検出率低下が整合するという材料までであり、
2比較の family 全体で有意とは判定しない。後者はこの標本・条件では低下を検出できない。
0件は不在証明でなく、非有意は同等性証明でない。全走 witness off のため、7 signal の
実行順序を discriminator で同定したものではない。witness 軽量化は §3 の静的設計まで。

## 2. 実行の束縛

- outer: main `c8e8dc06f` (wave worktree + detached worktree 3 本、いずれも同 base)。CCBench: `e9e477ca1b55348ab4530de0b1cf663ce4555290`
  (hook branch `izanagi-t1943-mocc-g2-readfrom-witness` 先端、witness あり)。gitlink は `511c9538` のまま動かしていない。
- patch: X/P 計装 `patches/instr-mocc-lock-coverage.patch` (repo、D1686、sha256 `e9e65b7876050865ee1cbc4d3a05516b09a8fe0b18149e0c063632162fd7bb48`、
  T-2772 稼働中も不変)。診断 patch `mocc-close-version-counter-gap.patch` (T-2774 job dir、sha256
  `8a25bd0a5687437269c720cb34a4b26024a6f1f119adf1c16281d455b9ecaa1d`、1,168 byte、本 wave job dir `verbatim/` に写し)。
- runner: `probe/t2779_probe.py` (v5、T-2774 v4 `2e2ddea834f782abb7a671b42d8a57f82ac8b82d7ac90d23965ad3ca3fd41c00` 起点、Codex `role=author`、
  sha256 `7907a545b719845d69b36590cc90cff6b28c242d3b7140d9c52b4a838798df99`)。
  arm 定義 `probe/arms-t2779.json` (sha256 `4f6aaf5a172eb8eb737bd0ec6e2fcc52e92b5dce2691803f65d8f34e327ebb56`)。
- configure 基底 = T-1943 pilot と同一 (`-DCCBENCH_TRACE=1 -DCCBENCH_BACK_OFF=0 -DCCBENCH_BACKOFF_FIXED=-1 -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1
  -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=0`)。bo1 arm は `-DCCBENCH_BACK_OFF=1` だけ置換 (Q1 の `KEY_SORT=0` / `TEMPERATURE_RESET_OPT=1` は
  持ち込まない)。gcc-11、policy `tools/pegasus/mocc_trace_v1_policy.json`。
- arm (3、同一 block で round ごとに開始 arm を回転):

| arm | pin | X/P | 診断 | witness | BACK_OFF | observational_only |
|---|---|---|---|---|---|---|
| e9-instr-nowit | e9e477ca | 有 | 無 | off | 0 | false |
| e9-diag-nowit | e9e477ca | 有 | 有 | off | 0 | true |
| e9-instr-nowit-bo1 | e9e477ca | 有 | 無 | off | 1 | false |

- 実行 argv: `-ycsb_tuple_num=10000 -thread_num=48 -ycsb_zipf_skew=0.9 -ycsb_rratio=50 -ycsb_rmw=0 -ycsb_max_ope=10 -extime=3`。witness env は全 arm 未設定。
- 走: smoke は 5875.nqsv / bnode049、15:46:26〜15:48:17 JST、Elapse 116秒、3走は本走から除外。
  本走は §5 の4 block。queue gen_S、generic dispatch、投入元4 worktree。
- verifier: `python3.10 -m orchestrator.verifier <trace_dir> --json --protocol mocc --ccbench-root <arm の source> --expected-commits N` (測定時 outer `c8e8dc06f`、変更なし)。
  discriminator は witness off なので全走 `not-run (witness-off)`。

## 3. witness 軽量化の静的設計 (実装せず、設計まで)

段 2 plan §6 を段 3 レンズ A の所見 (MF1 / S1 / S4 / N1 / N2) で修正して確定した。行番号は e9e477ca の `cc/mocc/transaction.cc` (`M:行`)。

- **現物**: witness on のとき、S 行は各 write element の publish (`__atomic_store_n`、`M:1195`) の直後・`unlockCLL()` (`M:1207`) の前に
  `izanagi_mocc_g2_emit_post_store` (`M:1199`、定義 `M:100〜110`) が書く。同関数は共有 record `write.rcdptr_->body_` の先頭 8 byte を decode し
  (magic / 長さの検査に失敗すれば `std::abort()`、**decode に成功した値は writer txid と比較せず、不一致でもそのまま出力する**)、
  `S txid key epoch tid stored` を thread_local ofstream へ書式化して出す。不一致の検出は消費側 (`mocc_g2_discriminator.py` の
  `witness-post-store-token-mismatch`) が担う。L 行 (`M:1146`) は read_set_ ループで publish 前、stamp (`M:1167`) は各 UPDATE 要素の memcpy 前、
  E 行 (`M:1204`) は最後の publish の後・unlock 前、`write_set_.clear()` は `M:1211`。
- **観測者効果の静的根拠 (T-2774 §1 4)**: 静的所見 (a) の validation 側 (ii) は、R の tidword 比較 (`M:1010〜1013`) と counter 読み (`M:1024`) の
  2 load が W の publish (1195) と unlock (1207) を跨ぐ必要がある。S 行の書式化 + I/O が write element ごとに [publish, unlock] を伸ばす。
  **2 番目以降の write element の stamp と memcpy も先行要素の publish 後・unlock 前に入る** (`M:1160〜1207`) ので、「stamp は窓を伸ばさない」は
  単一 write か当該要素自身の publish との関係に限る。
- **別経路 (未実測の候補、レンズ A S1)**: write lock は validation で取得され (`M:989〜1000`)、L 行の I/O はその保持中 (`M:1141〜1147`)。他 transaction の
  validation が旧版を読んだ後に `W_LOCKED` を観測すれば `M:1024〜1033` が commit を拒否する。L の I/O が lock 保持を伸ばすことは、G2 でなく abort に
  化ける (率を下げる) 別の説明候補であり、S だけ軽くした追試が陰性でも観測者効果全体の否定にはならない。
- **案 (S 出力の遅延)**: (1) `M:1134` の `#if TRACE` 内、最初の publish より前 (write lock 取得後) で `thread_local std::vector<std::uint64_t>` を
  clear / `reserve(write_set_.size())`。(2) `M:1197〜1200` を「共有 body の decode + 既存の失敗判定 (`std::abort()`) + 確保済み vector への push」に置換
  (unlock 後は他 writer が record を上書きしうるので採取は publish 直後のまま)。(3) `unlockCLL()` (`M:1207`) の直後・`RLL_.clear()` の前で
  `write_set_` を同順に再走査し、保存した producer で S 行を出力して vector を clear。(4) `WriteElement` に field を足さない。
  (5) `stored ≠ txid` で abort する分岐は**追加しない** (不一致値を保持して出力し、消費側の被覆を保つ)。(6) `<vector>` を `#if TRACE` 内で include。
- **保存されるもの**: H / L / S の文法と S の 5 値、identity `(txid, key, version)`、1 要素 1 push 1 S (unlockCLL は CLL だけを消し write_set_ は再走査まで
  不変、`M:1094〜1113`)、witness 有効の完走経路は UPDATE のみなので `maxtid.epoch/tid` は全要素で共通 (`M:1131`, `M:1163〜1183`)、discriminator の
  mismatch / duplicate 被覆 (`G:367〜390`)。discriminator は S の実 store 順を検証しない (`limits.write_store_order_verified_beyond_post_store_token: False`)
  が、これは採取位置・値・件数を維持する本案に限った論証で、任意のタイミング移動を正当化しない。
- **生存期間 (レンズ A S4)**: 通常の validation 失敗は `writePhase()` に入らず採取を開始しない。採取開始時と完走時に clear する。witness 有効時の
  INSERT / DELETE と decode 失敗はプロセス終了であり、残留値を持って次 transaction を実行する分岐ではない。異常終了時の出力済み prefix は
  変わりうる (完全出力の同値性と異常終了時の prefix 同値性は区別、後者は未実測)。
- **動かさないもの**: L 行・stamp (介入を S に絞る。無影響の証明ではない)、E 行 (058d0c4e にも同位置にあるという根拠は運用事実からの引用で、
  058 source の独立照合は本 wave 未実施。時間寄与がゼロとは言えない)。
- **負荷の静的見積**: 現行の要素ごとの publish 後処理 = decode + stream 取得 + key の hex 化 + 5 値の書式化 + 区切り / 改行の出力。案 = decode + 既存失敗判定 +
  確保済み vector への push。短縮量は未実測。後続 write・X/P 検査・E 出力・CLL 順の unlock が残るので窓が memcpy だけになるとは言えない。
- **D16 の分類と後続**: `#if TRACE` 内の計器で validation・publish・CC lock 操作を変えない → trace-hook 分類、正式な実装先は hook branch
  `izanagi-t1943-mocc-g2-readfrom-witness` (上流 push は人間判断)。本 wave は設計までで commit も実走もしない。追試の arm 名は `e9-instr-witlight`
  (job dir で試験 patch を作るなら X/P → witlight の順で適用し、その preimage に対する diff、`#line` を整える。正式 hook commit には X/P を混入させない)。
  witlight と診断 patch の併用は本設計の対象外。hook branch の新 commit を pin に使う追試では runner の `pin != PIN` による discriminator 対象外条件に注意。
  **TRACE=1 の観測者効果低減は仮説であり未実測。**

## 4. 実走の設計 (事前登録 = job dir `s4-ruling.md` 6、結果を見る前に確定)

- 3 arm を同一 block で round ごとに開始 arm を回転 (`round_order`: ABC / BCA / CAB の 3 周期、30 round は 3 の倍数なので各 node で各 arm が各位置に 10 回)。
  4 block (B1〜B4) × 30 round × 3 arm = 90 走 / block、各 arm 120 走。smoke は別 block (`--rounds 1`、3 走) で本走に合算しない。**結果を見て増減しない。**
  launcher自体はround数を引数で受ける実装であり、30を機械的に固定していない。本走4 blockの実値が30だったことを確認した。
- 標本の根拠 (親が計算、plan が独立に再計算して丸め精度で一致): 片側 Fisher α=.05、独立・同率 Bernoulli、等標本、完全抑制、単一比較の設計仮定で、
  基準率 0.058 (T-2774 の witness off 合算 7/120) 対 0 なら K=120 で 0.83、直接対応 arm `e9-instr-nowit` の点推定 0.05 (2/40) 対 0 なら 0.72
  (K=56 では 0.22 / 0.15)。部分抑制 (0.058 対 0.02) は K=120 でも 0.30。2 比較で各 α=.025 なら 0.058 対 0 で約 0.70。**計算値であり実測ではない。**
- 主比較 (2 本固定): ① `e9-diag-nowit` 対 `e9-instr-nowit`、② `e9-instr-nowit-bo1` 対 `e9-instr-nowit`。②の問いは「witness off に固定した条件で
  `BACK_OFF` だけの変更による検出率差」。介入側の率が低下する方向の片側 Fisher を参考値、主表示は arm 別 k / m と Clopper-Pearson 両側 95%。
  2 比較の未調整 p を示し、どちらか 1 つの p<.05 で family 全体の効果とは判定しない。block 別件数を併記し、合算値だけから node 一般の効果を主張しない。
- 欠測規則: block ごとに (a) 保存済み (`result.json.runs` 収載)、(b) 開始証拠あり・未収載、(c) 未開始確認済み、(d) 状態不明を区別。主解析は (a) のみ。
  揃わない block は補充せず不足を明示。原本は書き換えない。
- 所要の見積 (v3 Q2 の 5 arm block からの外挿、上限ではない): 90 走 × 約 22 秒 + build 3 + warmup ≈ 40 分 / block。walltime 02:30:00。
- 各走: 別 trace dir → verifier (timeout 300 s) → cycle 正の走は trace-manifest を作り生 trace を退避 (witness off なので discriminator は `not-run`) →
  走ごとに JSON を逐次保存。

## 5. 結果と欠測会計

| block / request | hostname | Created / Started / Ended (JST) | Elapse 秒 | 通常 k/m | 診断 k/m | backoff k/m |
|---|---|---|---:|---:|---:|---:|
| B1 / 5894 | bnode037 | 15:50:01 / 15:59:55 / 16:37:04 | 2233 | 1/30 | 0/30 | 0/30 |
| B2 / 5895 | bnode042 | 15:50:07 / 15:50:15 / 16:27:12 | 2222 | 2/30 | 0/30 | 2/30 |
| B3 / 5897 | bnode044 | 15:50:14 / 15:55:36 / 16:32:39 | 2227 | 1/30 | 0/30 | 0/30 |
| B4 / 5898 | bnode045 | 15:50:21 / 15:50:29 / 16:27:34 | 2229 | 1/30 | 0/30 | 0/30 |

4 block は `.done=0`、`status=completed`。各90走の (a) 保存済みを result と各 run.json の一致で確認し、
run directory 集合も一致した。(b) 開始証拠あり未収載、(c) 未開始、(d) 状態不明は各 block で0。
全 arm の計画数=N=m=120、failure=indeterminate=未開始=0。事前登録の締切までに4 blockが揃い、
回収時に結果原本を変更せず、補充・再計測はしていない。smoke と過去 wave は合算しない。

| arm | k/m | 検出率 | Clopper–Pearson 両側95%区間 |
|---|---:|---:|---:|
| e9-instr-nowit | 5/120 | 4.1667% | [1.3665%, 9.4559%] |
| e9-diag-nowit | 0/120 | 0% | [0%, 3.0273%] |
| e9-instr-nowit-bo1 | 2/120 | 1.6667% | [0.2025%, 5.8909%] |

CP / Fisher は独立・同率試行を仮定した参考値。node内相関、回転順、時間変動はモデル化していない。
片側 Fisher の表は行=介入/通常、列=G2/非G2 として診断 `[[0,120],[5,115]]`、backoff `[[2,118],[5,115]]`。
介入側の G2 数を x、観測値を k、両群合計を K とし、
`sum(comb(120,x)*comb(120,K-x)/comb(240,K), x=0..k)` から上記p値を得た。
区間と母数は `summary.json`、原結果SHAと入力4本も同ファイルに記録した。

正例は B1/82 通常、B2/30 backoff、B2/33 通常、B2/69 通常、B2/77 backoff、B3/6 通常、B4/80 通常。
各1 cycle、計7走。各走の verifier JSON・run JSON・trace-manifest と生traceを元job dirに保全する。
7走はすべて現象名G2・長さ2・両辺rw。親が全336 traceファイル（1,981,789,619 byte）の
集合・サイズ・SHA-256をmanifestと照合して一致した。逐語JSON/manifestはrepoにも保存し、生traceはjob dirに保持する。
全360走で discriminator は witness off による not-run。通常/bo1 の `observational_only=false` や
個別 verifier の `certified=true` は本観測の認証を意味せず、本文全体は非certifyingである。

binding は4 blockの arm別 pin・patch SHA・define・witness・source SHA・observational_only、
runner SHA、arms JSON SHA、policy SHA、toolchain を照合した。bo1だけBACK_OFF=1、他は0。
sourceとbinaryの一時path、base/policyのworktree path、binary SHAはblockごとに異なる。
全bindingのbyte同一やnode専有を主張しない。runnerは開始時と各走前に `_assert_single_tenant()` を呼ぶが、
その既存検査の射程を超えたnode専有の実証ではない。

## 6. 解釈の上限と次の実験

段4で固定した診断armの結果別主張範囲を維持する。

| 結果 | 言える範囲 | 言えないこと |
|---|---|---|
| 低下 | 固定条件で、2変更を束ねた介入と検出率低下が整合する | cold検査/validation再読、(i)/(ii)、実装/hook/verifier仮定の三分岐は識別できない |
| 差なし | この標本・条件では低下を検出できない | 効果ゼロ、候補経路の不在、診断の無効性 |
| diagでも正例 | 当該producer/計器条件でsignalが残る | 元と同じ実行経路であること |

今回diagは0件だが陰性はG2不在の証拠ではない。診断patchは拒否条件を加えるため
受理集合を縮小する方向の介入であり、それを元実装の根因同定や修正版の認証に読み替えない。
backoffにもsignalが2件あり、witness off固定での率比較までである。Q1の0/56は歴史的参考に留める。
T-1892の5/42、T-1943のno-g2、T-2774 Q1/Q2は当時の束縛で保持する。
certified昇格、pin前進、変異探索、規律2の即reject契約は変更しない。
後続候補は§3の軽量witnessを別waveで実装し、同じ値・件数・異常検出を保持した上で観測条件を比較すること。
本waveでは改善実装も次waveも開始しない。還元判断: ユーザー確認待ち。

## 7. 中断回収の範囲

着手時local main `b2037abfa1467507cf92c851c83f262239f81641` から専用Codex worktreeを作成。
旧waveは未収載commitもdirty差分もなく、job dirの既存結果・裁定・草稿を回収した。
probe保存commit `9a2a525504fb840de737fdb6f2f362ed2b7bd7a9` は製品コードへmergeしない。
本記録は製品実装差分ゼロのため事前裁定どおり変異matrix免除。受入は免除しない。

独立read-onlyレビューA/Bは双方must-fix 0、GO。Aのshould（launcherの実装と裁定予定の差）を§4、
nit（stampの行番号）を§3へ反映した。Bはshould/nitも0。生traceの再解析と軽量witnessの実走は行っていない。
親のselftestは21/21。レビュー逐語は `verbatim/recovery-review-{A,B}.md`。
旧親のcwdを持つPID 1534820が生存していたため、旧worktreeを変更せず独立の回収ファイルを使った。
