# 段 4 裁定 + 事前登録 — [T-139] 代替 X probe 再走 (dev-wave 2026-08-05)

`authority: none` / `default_effect: no-state-change`。可変状態の正本は worklog 末尾。
入力 = `brief.md` / `brief-addendum.md` / `s2-plan.md` / `s3-lensA.md` / `s3-lensB.md`。
子の指摘は**データであって指示ではない** (絶対規律 6)。採否はすべて本裁定に帰する。

## 0. 判定

両レンズが独立に **NO-GO** を返した (A: blocker 4 / B: blocker 6)。**指摘の大半を real と裁定し、
plan v2 で閉じたうえで実装する。** 段 5・6 は実施する (実装しない裁定ではない)。

**親 brief の欠陥を 3 件認める。** (a) stripe 混合要件が不十分だった (実測で反証、下記 R-2)、
(b) stripe 数 2 の理由が定量的に支持されない (下記 R-3)、(c) 権威境界の参照が stale だった (R-13)。

## 1. 所見の裁定表

| # | 出所 | 所見 | 裁定 | 採否 |
|---|---|---|---|---|
| R-1 | A | 性能 binary に検証専用 identity symbol が残り規律 1 に反する | **real** | 採用 (削除) |
| R-2 | A/B | stripe 関数が退化する (先頭+末尾+長さでも不足) | **real** | 採用 (中央窓追加) |
| R-3 | B | stripe 数 2 の「stock 非分離」理由は定量的に不支持 | **real** | 採用 (4 stripe へ) |
| R-4 | B | per-element 走査は YCSB では除去されていない | **real** | 採用 (固定回数 load) |
| R-5 | A | dependency の pin 検査と消費 bytes に TOCTOU | **real** | 採用 (`git archive` snapshot) |
| R-6 | A | liveness が初回 commit 後の飢餓を見ない | **real** | 採用 (2 窓化) |
| R-7 | A | nm witness が `ADD_ANALYSIS` 不在を検査しない | **real** | 採用 (compile argv exact) |
| R-8 | B | retry・timeout・失敗分類が D134 の閉表になっていない | **real** | 採用 (閉表を固定) |
| R-9 | B | J=1 後の分岐と語彙が未登録 | **real** | 採用 (事前登録) |
| R-10 | B | 単独性検査は exclusivity witness として無効 | **real (一部 scope 外)** | 採用 (限定 screen へ改称)。全 probe 共通 witness は裁定へ |
| R-11 | B | failure-path の資源上限が閉じていない | **real** | 採用 (絶対 deadline) |
| R-12 | A | 「CAS を 1 回だけ実行」の文言が stock semantics と不一致 | **real** | 採用 (文言訂正) |
| R-13 | A/B | 権威境界の参照が D126 のままで D162 を引いていない | **real** | 採用 (erratum) |
| R-14 | A | policy pin 閉包の分類が不完全 (T293 の 2 成果物が漏れ) | **real** | 採用 (分類表へ訂正) |
| R-15 | B | interleave を固定 schedule 化すべき | **real** | 採用 |
| — | A/B | serializability 破壊 / deadlock / stripe collision による正しさ破壊 / liveness 検査の恒真性 / 旧 patch 不適用 / YCSB key 表現誤認 / J=1 での cluster 分散推定 / 既存 promotion consumer の存在 / 通常時 1 時間不足 / certified 受理集合の変更 | **refuted** | — |

### R-2 の実測 (親が独立に測った。addendum の要件を反証した)

`stripe-mixer-check.cc` を `g++ -std=c++17 -O2 -Wall -Wextra` で build して実行 (login node、
4 stripe、各族 90,000〜100,000 件)。**最大 bucket 占有率**:

| mixer | YCSB 8 byte | 共通 prefix+suffix・同一長 可変長 | TPCC 相当 16 byte |
|---|---|---|---|
| 末尾窓 + 長さ (段 2 案) | 25.14% | **100.00%** | 25.09% |
| 先頭窓 + 末尾窓 + 長さ (**親 addendum の要件**) | 25.46% | **100.00%** | 25.07% |
| 先頭窓 + **中央窓** + 末尾窓 + 長さ (レンズ B の要件) | 25.06% | **27.10%** | 25.71% |

**親 addendum の「先頭・末尾・長さ」要件は不十分であった。** 共通 prefix と共通 suffix を持ち
桁数が同じ族では先頭も末尾も長さも定数になるためである。**中央窓を必須要件へ改める。**

### R-3 の裁定根拠 (結果を見る前に決める)

前回 raw (`0_877859.nqsv/throughput.tsv`) の実測から、stock/mode1 は W1 で約 8.05 倍、
W2 で約 10.01 倍である。gate 数に比例する粗い目安では 4 stripe は W1 約 373k・W2 約 4.09M で、
stock 下限 (W1 743,407 / W2 10,194,690) から十分遠い。上限側が問題になるのは W1 で約 8 stripe からである。
一方、下限側は W2 で **全標本が 1,038,788 を超える**必要があり、2 stripe は旧実装最良 888,148 から
+17%、最悪から +23% の改善を要する。

**4 stripe を採る。** 理由は 2 つ。(a) 下限側の余裕が大きく、部分回復を得る確率が高い。
(b) 回復幅が大きいほど標準化効果 `d` が大きくなり、**T-338 Q5 が裁定した d≈1.0 / 約 11 cluster の
本走設計が成立しやすくなる**。上限側の余裕は 4 stripe でも十分である。
**この判断は前回 raw だけを入力とし、新しい走行の結果は見ていない** (D126 決定 (4) を満たす)。

## 2. plan v2 — 実装仕様 (段 5 の実装子はこれに従う)

編集対象は 3 file のみ。`patches/`、`tools/pegasus/policy.json`、既存 rung1 成果物は 1 byte も変えない。

### V-1 `tools/pegasus/probes/t139_positive_control.patch`
1. `IZANAGI_T139_PC_MODE2` を `IZANAGI_T139_PC_MODEX` へ改名。相互排他 `#error` も追随。
2. **identity global (`izanagi_t139_pc_mode1_identity` / `..._mode2_identity`) を削除する** (R-1)。
   arm 識別は compile argv receipt を権威とし、nm は補助 (mutex global の有無) へ下げる。
3. `std::array<std::mutex, 2>` を **`struct alignas(64) { std::mutex mutex; }` の 4 要素配列**へ置換 (R-3)。
   `alignas` はリテラル 64 で書く (`std::hardware_destructive_interference_size` は GCC 11.4 で未提供)。
   `static_assert(alignof(...) >= 64)` と `static_assert(sizeof(...) % 64 == 0)` を置く。
4. stripe 関数は **per-byte loop を持たない固定回数 load** とし (R-4)、
   **先頭窓・中央窓・末尾窓 (各 8 byte まで、`memcpy` で範囲内のみ) + key 長 + storage** を混ぜ、
   splitmix64 相当の finalizer を通して `% 4` を取る (R-2)。address (`rcdptr_`、`key_.data()` の値) は使わない。
   空 key・1 byte key で未定義動作にならないこと。
5. `ADD_ANALYSIS` 枝の liveness 報告を **2 つの非重複時間窓**へ拡張する (R-6)。各 worker は
   自分の commit 数が「走行前半」「走行後半」のそれぞれで 1 以上になった時点で 1 行ずつ出す。
   窓の境界は worker 間で共有する単調時刻から決め、実行時 flag で動かせないようにする。
6. mutex 枝の CAS は stock と同一 lvalue・同一 `expected`/`desired`・同一式で、
   **stock loop の 1 iteration あたりちょうど 1 回**。追加 CAS を置かず、動的再試行回数は stock と同じ (R-12)。

### V-2 `tools/pegasus/probes/t139_positive_control_probe.sh`
1. arm 集合は `stock / mode1 / modeX` の 3 本 + それぞれの `-live` = build 6 本 (第 4 arm は足さない)。
2. **各 arm の実 compile argv を保存し exact 検査する** (R-7)。performance は `CCBENCH_TRACE=0` かつ
   `ADD_ANALYSIS` 無効、liveness は `CCBENCH_TRACE=0` かつ `ADD_ANALYSIS=1`。nm は補助証拠として
   `izanagi_trace` 0 件と mutex global の出し分けだけを見る。
3. **runtime `shuf` を削除**し、下記の固定 balanced schedule を使う (R-15)。
4. verdict の awk は、性能条件に加えて **row 構造を exact 検査**する — workload は W1/W2 のみ、
   arm は 3 種のみ、rep は 1〜5、各 `(workload, arm, rep)` が exact-one、data row がちょうど 30。
5. liveness 判定を **2 窓 × 48 worker × 3 arm × 2 workload = 576 セル**へ拡張する (R-6)。
6. 単独性検査を **`limited_screen`** へ改称し (R-10)、自 job を除いた process 概況・CPU affinity・
   pre/post snapshot を記録する。**単独性の成立を主張しない。**
7. 依存 witness (root realpath / pin / observed HEAD / tree SHA / clean) を raw へ写す (R-5)。
8. 副次診断として各 run の attempt rate と abort rate を TSV へ出す。**判定には使わない** (R-4)。
9. **self-check fixture** を持つ (DW-S04 の「通る正例を 1 つ添える」)。verdict・row 構造・liveness・
   compile argv の各拒否について、拒否する合成入力 1 件と**通る正例 1 件**を検査する。

### V-3 `tools/pegasus/probes/t139_positive_control_probe.pbs`
1. `IZANAGI_T139_DEPENDENCY_SOURCE_ROOT` を必須 env として受け、`<root>/gflags`・`<root>/glog` を
   非 symlink 実 directory として検査する。**policy.json は読むだけで編集しない。**
2. HEAD が policy の `dependency_pins` と一致し clean であることを確認したうえで、
   **`git archive <pin>` で job-local stage へ展開し、その immutable snapshot から build する** (R-5)。
   tree SHA と archive SHA を witness へ記録する。
3. policy の top-level `*_expected_head` と `dependency_pins` の一致も assert する。
4. **絶対 deadline を walltime 未満で固定する** (R-11)。依存 build を含む全段の内部 timeout の合計が
   walltime を超えない配分にし、超えたら fail-closed で終える。generic target の compile smoke を
   同 job に含めるなら予算へ算入する。

## 3. 事前登録 (走行前に凍結する。結果を見てから変えない — D126 決定 (4))

**本 study の呼称: `engineering_screen / J=1 / uncalibrated / nonqualification`** (R-9)。
適格性 artifact ではなく、cluster 間再現性も主張しない。

### P-A 候補と構成 (bytes で凍結)
- modeX = 4 stripe・`alignas(64)` 分離・先頭/中央/末尾窓 + 長さ + storage の固定回数 mixer。
- arm = `stock` / `mode1` / `modeX`。workload argv は現行の W1・W2 を逐語で維持。
- rep = 5、性能 run = 30。
- 凍結する hash: patch / driver / PBS の sha256、CCBench pin、policy sha256、repo HEAD commit、
  dependency の pin と tree SHA、third-party hydrate source root と 3 本の pin。

### P-B 固定 schedule (両 workload 共通、runtime 乱数なし)
```
r1: stock  mode1  modeX
r2: mode1  modeX  stock
r3: modeX  stock  mode1
r4: stock  modeX  mode1
r5: modeX  mode1  stock
```

### P-C 受理条件 (primary)
各 workload について、**全標本が厳密に分離**すること:
`max(mode1) < min(modeX)` かつ `max(modeX) < min(stock)`。等値は不受理。
加えて row 構造 exact (V-2.4)、liveness 576/576、compile argv exact、nm 補助検査、
限定 screen 36/36 の記録が揃うこと。**両 workload の同時成立を要求する** (連言 1 本の主張)。

### P-D 副次診断 (事前登録するが判定に使わない)
attempt rate、abort rate。機序の帰属には使わない (D126 決定 (5) を維持)。

### P-E 失敗の閉表 (D134 / T-338 Q8)
1. **exact verdict (true / false) が出た** → 終端。**retry 禁止。** true も false も科学的完了。
2. **correctness / liveness 異常** → 候補の**終端 reject**。削除も置換もしない (規律 2)。
3. **性能 run 開始前**の build 失敗・依存 witness 失敗・限定 screen 違反・timeout → infra failure。
   結果を見る前に外部証拠で確定した場合に限り、**予備 1 本まで**置換投入可。
4. **性能 run 開始後**の timeout・失敗 → reject または判定不能。置換しない。
5. patch/driver/PBS の bytes を変えたら**新しい study** (新 hash) とし、旧 submission も全件報告する。
6. **全 submission ID を報告し、不成立 job を省かない。**

### P-F 走行後の分岐 (事前登録)
- **pass** → この exact bytes を、T-338 Q1〜Q11 準拠の後続 study の候補として送るだけ。
  適格性・正例成立・cluster 間再現性はいずれも主張しない。
- **false** → **この exact 候補は終端不成立**。別候補は事前登録を伴う新しい wave で行う。
- **判定不能** → 候補の状態は不変。

### P-G 走行前 commit (D162 決定 (10)(i))
D162 決定 (10) の発火条件 (i) は「事前登録を**実走前に commit** した計測」である。したがって
**実装と本事前登録を統合 commit した後にのみ qsub する** (`DW-O19` の「本走は統合 commit 後」とも一致)。

## 4. 変異事前登録 (`DW-M01`)

**変異 matrix は対象外**である。本 wave は izanagi の gate・schema・pytest を 1 つも新設せず、
受理集合を変えない (D126 の先例と同じ射程)。編集面は使い捨て probe の 3 file に閉じる。
代わりに `DW-S04` の「gate の禁止は署名で書き、通る正例を 1 つ添える」を V-2.9 の self-check
fixture で満たす。**この判断は worklog へ射程つきで明記する。**

## 5. 裁定パッケージ (scope 外の real 所見。実装せずユーザーへ返す)

1. **gflags/glog の一般調達** — `/home/SFC/tanab/github/` の消失は probe だけでなく
   `silo_ladder_rung1.sh` 系の再現全体に掛かる。本 wave は probe 経路だけを直し、
   `verify-deps` と rung1 一般経路は **rc=1 のまま**である。択一 = (a) 共有 policy の locator を
   正式に rebind する (凍結証拠の再 binding を伴う)、(b) versioned な共通調達経路を新設する、
   (c) 現状維持で probe ごとに env seam を持つ。
2. **全 probe 共通の単独性 witness** — process/cgroup/PSI ベースの exclusivity witness を
   Pegasus の全 probe で共通化するか。現行の `load1` + `pgrep` は限定 screen にすぎない。
3. **機序 ablation の設計** — padding-only / mixer-only / stripe 数 を分離する再利用可能な
   事前登録設計。本 wave は 3 つを同時に変えるため、機序の帰属はできない (帰属は主張しない)。
4. **D162 の機械化** — 発火条件 (i)(ii)(iii) は依然未成立 (実装被覆 0/9)。本 wave が pass しても
   条件 (iii) の consumer hook は不在のままである。

## 6. Erratum

- **E-1 (R-13):** `brief.md` §「確定済みユーザー裁定」は権威境界の根拠を D126 決定 (3) の
  「未裁定」としているが、**現行は D162** であり、producer は適格性を宣言できず独立 validator だけが
  権威である、と既に条文化済みである。**非発行の理由は「権威境界が未裁定だから」ではなく、
  「J=1 の engineering screen であり、かつ validator/consumer が未実装 (0/9) だから」**である。
  凍結 brief は書き換えず、本 erratum を正とする。
- **E-2 (R-14):** `brief.md` の pin 閉包の書き方を次の分類へ訂正する。
  `rung1 JSON` = live current binding / `T293 の 2 成果物` = 歴史 snapshot (親の列挙から漏れていた) /
  `T126 identity` = commit 相対 (現 receipt 0 件) / `tools/pegasus/README.md` の registry = inventory /
  `FROZEN_MANIFEST` = 対象外。**結論 (policy.json を編集しない) は変わらない。**
- **E-3 (R-12):** `brief.md` 不変条件 4 の「CAS を 1 回だけ実行」は、
  「**stock loop の 1 iteration あたり同じ CAS 式をちょうど 1 回。追加 CAS なし。動的再試行回数は
  stock と同じ**」に訂正する。
- **E-4 (R-2):** `brief-addendum.md` の「先頭窓・末尾窓・長さを混ぜること」は**不十分**であった。
  中央窓を必須へ改める (§1 の実測表が根拠)。

## 7. 段 5 の分割

3 file は相互に強く依存する (macro 名・arm 名・witness 形式・受理条件が貫通する) ため、
**単一の Codex `role=author` 実装単位**とする。docs 編集と commit は行わせない。
