# 裁定パッケージ — [T-813] 受入全走のノード横断シャーディング (設計・実測評価)

- 起草: dev-wave `dev-wave-t813-shard-eval` (背景 job `3e4d7d2a`)、2026-08-11
- 種別: 設計択一 (受入の受理集合の意味論)。**実装差分ゼロ。本パッケージは択と推奨だけを返す**
- 上位裁定: 受入窓は **(d) 直列維持 + 占有短縮** (2026-08-11 ユーザー裁定)。本件はその (d3') の可否
- 正本: `question-lease-serialization/ruling-package.md`、inbox §98 (追記含む)、worklog [T-813]
- 一次資料: 本 wave の `facts.md` (F-1〜F-9)、`measurements.md` (M-1〜M-8)、`s2-plan.md`、
  `s3-sol-out.md`、`s3-luna-out.md`。実測はすべて 2026-08-11 の実走

---

## 0. 結論

**現時点では分割を実装しないことを推奨する。** 理由は「効かないから」ではない。
性能の signal はある。**受入の受理集合を保てないから**である。

1. **性能: 短縮の signal はあるが、採用値としては使えない。**
   実測時間で重み付けした k=4 で pytest wall は 539.83 → **271.87 秒**、
   ポイント (PBS Elapse 合計) は 546 → **634 ノード秒 (+16%)**。
   ただし **(i) 重みを同じ走行から取った in-sample 配分**、**(ii) 全 arm が rc≠0 の
   意味論的赤を含む**、**(iii) queue 待ちを入れた end-to-end では件数均等 arm が
   baseline より遅い (791 秒 vs 565 秒)**。**「1.99 倍」を設計の前提数値にしてはならない。**
2. **天井が低い。** 最長テスト単体が **263 秒**あり、時間均等シャードの wall 271.87 秒は既にその下界。
   **k を増やしても 271 秒より速くならない。** 占有 15〜25 分に対する短縮は 18〜30% にとどまる。
3. **正しさが壊れる。実測 3 型。**
   - **分割不変性の破れ:** 試した 2 通りの分割の**両方**で、全走なら緑のテストが赤になった
     (10 件消失 / 24 件消失)。**分割を変えると犠牲者も変わる。**
   - **同時投入が実 repo を汚す:** `_real_output_snapshot()` が他 job の dispatch receipt を検出して 8 件赤。
   - **排他閉包が無い:** `real-repo` group に**入っていない**実 repo reader/writer が多数ある
     (§3-3)。group-atomic に束ねても排他は作れない。

**推奨する順序は次の 3 段である。**
**(前提) M0 分割不変性と排他閉包を成立させる → (次) M5 遅いテストの是正で下界を下げる →
(最後) 必要なら M1/M6 を再評価する。**
なお **待ち行列に対する費用対効果の最上位は、本件ではなく既裁定の [T-812]** である (§7)。

---

## 1. 「分割後も受入の受理集合を保つ」の定義 (要件 1)

受入とは「**この tip をこの main へ入れてよい**」の唯一の証拠である。

固定入力 `X` を「tested main SHA・tip SHA・HEAD・tracked/untracked/index/submodule の状態・
既定 target・pytest config・plugin 集合・interpreter version・実行環境クラス」とし、
既定 target を canonical に 1 回走らせた判定を `A0(X)`、分割 `p` と host 配置 `h` による
合成判定を `AM(X,p,h)` とすると、保つとは

```
すべての許容 X, p, h について  AM(X, p, h) = A0(X)
```

である。**ただしこの全称式は「守りたい結論」そのものであって、機械的な witness ではない。**
運用可能にするには、次の 6 条件を証拠の形で要求する。

- **(A) 被覆 (順序付き多重集合として):** 各シャードの collection を canonical ordinal で併合した列が、
  既定 target の canonical collection と**重複数・順序・collection error まで含めて一致**する。
  集合一致では足りない — `conftest.py` は収集中に `real-repo` marker を自動付与し (238–248 行)、
  収集終了時に順序を変える (270–282 行) ため、pre-hook の file 集合は証明にならない。
  (**親の当初案 (a)「集合として一致」は段 2 に否定され、採用しない。**)
- **(B) 一意割付け:** 各 item は nodeid 文字列ではなく **canonical ordinal** を主鍵として
  ちょうど 1 シャードに属し、report phase と receipt まで一意に束縛される。
- **(C) gate:** §2 の表のとおり、**回数ではなく「どの snapshot・どの実行 root・どの分類に対する証明か」**を要求する。
- **(D) 木の同一性 (fencing):** 全シャードが**同一 snapshot** を見る。
  現行の tree fingerprint (`run_tests.py:1537–1609`) は `git status`・tracked diff・submodule status だけを見るので、
  **ignored な `output/` の bytes を束縛しない**。しかし `_real_output_snapshot()` は
  ignored を含む `output/` 全体を hash する (`test_s8b_floor_campaign.py:432–446`)。
  **つまり現状の `X` の定義では `A0(X)` が関数になっていない** (同じ `X` に複数の結果が対応しうる)。
- **(E) 結果の合成:** **`max(rc)` は使えない** — pytest の rc は 0/1/2/3/4/5(/6) の**名義尺度**であり、
  runner 独自 rc 13〜16 と混ざる (`run_tests.py:111–116`)。
  必要なのは (i) 期待シャード manifest と terminal receipt の 1 対 1 照合
  (欠落・重複・signal・timeout・JUnit 破損はすべて拒否)、(ii) 生の child rc を保存した型付き集約、
  (iii) JUnit は `(ordinal, occurrence, raw nodeid, report phase)` で併合し、collection error・
  setup/teardown error・skip/xfail/XPASS と理由を保存すること。
  (**親の当初案 (d)「max(rc)」は段 2・段 3 に否定され、撤回する。**)
- **(F) 分割不変性:** 同じ item の判定が分割の取り方に依存しない。**これは機構の帰結ではなく事前条件である。**

**(D)(F) は現状成立していない。** したがって現状の分割は、定義上すでに受理集合を保てない。
**静的に (F) を保証できない suite は、canonical 全走へ fail-closed で戻す設計にすべきである。**

## 2. 受入専用 gate 4 箇所の分割後の意味 (要件 1)

**親の当初案「全体として 1 回以上発火」も「各シャードで発火」も誤りである。**

| 行 | 検査 | 正しい要求 | 「発火しない」ときに通る不正 |
|---|---|---|---|
| 594 | 未 stage 削除 | **fan-out 前に、凍結した authority snapshot に対して exactly once。加えて走行後に再検査 (fencing)** | 未 stage 削除を含む木を受理 (canonical なら rc 13) |
| 632 | RuleOps 台帳 | **同一 snapshot に対して exactly once** (timeout・実行不能も rc 15 に倒す) | production ledger 破損が無音で通る (canonical なら rc 15) |
| 705 | submodule 初期化 | **distinct な実行 root ごと**。しかも現 predicate は `CMakeLists.txt` と `.git` の存在しか見ないので、**gitlink pin・HEAD・dirty も attest する必要がある** | 実 submodule を使うテストが skip し、その経路を壊した main が全 rc=0 になりうる |
| 1677 | 受入形警告 | **警告の回数を数えない。** 各 child は構造化 `non-standalone` receipt を返し、**唯一 acceptance を名乗れる coordinator token** に置換する | シャード 1 本の結果を受入と誤認できる (警告に強制力は無い) |

## 3. 実測 — 分割は正しさを壊した (要件 1・2)

### 3-1. 分割不変性の破れ (両方の分割で発生)

- 件数均等: `test_s8b_approved.py:31` の `from tests.skiputil import` が `No module named 'tests'` で
  収集エラー → **10 テストが 1 件も走らない**。`test_profiler_directive.py::…role_policy_check` が
  `No module named 'codex_roles'` で赤 (**実行時 import**)。
- 時間均等: `test_s8b_protocol_builder.py:37` の `from tests import repo_tree_util` が同じ形で
  収集エラー → **24 テストが消失**。さらに消えた module への横断整合検査が巻き添えで赤。
- **すべて全走では緑。**

**根本原因 (実測で特定):** repo には `orchestrator/__init__.py` も `orchestrator/tests/__init__.py` も無く、
pytest 既定では `orchestrator/tests/` しか `sys.path` に入らない。`orchestrator/` を入れているのは
**`orchestrator/tests/test_reflux_ir.py:120–128` の module 直下の `sys.path.insert` という副作用**である。
**xdist の各 worker は全 file を収集する**ので全走では必ずこの副作用が走る。シャードでは同居しなければ走らない。

**広がり:** 163 file の単独収集検査では収集エラーは **2 file** だけ。
しかし段 2 の静的抽出では **consumer 5 file・9 import 文**が下限であり、
`test_p3_s4_loop.py:1139–1145` と `test_real_repo_serialization.py:823–827, 900–910` は
**今回たまたま provider と同じシャードに入って赤が隠れている**。
**`--collect-only` では実行時 import を捕まえられない** ので、収集検査だけでは足りない。

### 3-2. 同時投入が実 repo を汚す

`assert repo_before == _real_output_snapshot()` が 8 件赤。差分は `output/pegasus-dispatch/…` =
**他 job の dispatch receipt**。**baseline 側でも起きた** (baseline は 4 シャードと並走していた)。

- `run_tests.py` 経由の dispatch は receipt を `<repo>/output/pegasus-dispatch/` へ書く。
  **ただし `dispatch_compute.dispatch()` には repo 外へ逃がす `output_root` seam がある**
  (`dispatch_compute.py:1286–1320`) — `run_tests._default_dispatch` が渡していないだけである。
  したがって「構造的に必ず起きる」は言い過ぎで、**現配線では必ず起きる**が回避 seam は存在する。

### 3-3. 排他閉包が無い (最も重い所見)

D63/D258 の `real-repo` group は**単一 runner invocation 内**の排他でしかなく、しかも
**実 repo に触る node を網羅していない**。段 3 が file:line で挙げた未閉包:

- `_real_output_snapshot()` を使う **9 node** (`test_s8b_floor_campaign.py` 4138/4227/4248/4371/4768/4856/4881/4925/4960) —
  `real-repo` の 13 file に**入っていない**。
- T-080 の実 repo payer: `test_s8b_oracle_driver.py` の `_run(root=ROOT)` 系。cache miss / lock 失敗時に
  実解決へ **fail-open** する (`real_repo_receipt_memo.py:145–163`)。**既知の穴 [T-715]**。
- 別名 group の実 Git writer: s8c の session fixture が実 root に対し alternate index で
  `write-tree` / `commit-tree` を行い共有 object database へ書く。group 名は
  `s8c-preregistration-candidate` で `real-repo` と別。**既知 [T-716]、未裁定**。
- runner 自身の writer (dispatch receipt)。pytest marker では直列化できない。

**したがって「group-atomic に束ねれば排他は保てる」という親の (P2) は成立しない。**
分割は、**既知の穴 ([T-715]/[T-716]) を単一プロセス内の潜在問題からプロセス・ノード横断の実害へ変える。**

### 3-4. fail の帰属

上の 3 型は、赤を見ただけでは「実装の赤」と区別できない。
**赤は原因にかかわらず land 不可**とするしかないが、それだけでは
「既知の干渉だから無視」という運用が生まれ、**実際に実 output を書いた不正 main を受理する経路**になる。
機械的な帰属には、同一 snapshot での **(1) 隔離 canonical、(2) 隔離した失敗シャード、
(3) 並走シャード + resource 変更台帳**の差分再走が要る。

## 4. 実測 — 性能 (要件 2)

| 指標 | base (1 ノード) | k=4 件数均等 | k=4 時間均等 |
|---|---|---|---|
| pytest wall の最大 | **539.83s** | 437.78s | **271.87s** |
| **dispatch wall (queue 込み) の最大** | **565s** | **791s (遅い)** | **293s** |
| ポイント (PBS Elapse 合計) | 546s | 758s (+39%) | 634s (**+16%**) |
| 直列総和 (junit time) | 10320.5s | 7941.1s | 7827.5s |

**この数値の限界 (採用値にしてはならない理由):**

1. **in-sample 配分。** k4time の重みは base 走行の junit から取った。学習と評価が同じ走行である。
2. **全 arm が意味論的に赤。** base は receipt 汚染で 8 failed、k4count/k4time は分割由来の消失を含む。
   **「壊れた状態での速さ」である。**
3. **end-to-end では逆転しうる。** queue 待ちを含む dispatch wall では、件数均等 arm は
   **baseline より遅い** (791 秒 vs 565 秒)。5 job 同時投入で約 350 秒待った。
4. **worker 数が交絡。** 各シャードが 48 worker を使うので総 worker は 192。
   「ノードを増やした効果」と「worker を 4 倍にした効果」が分離できていない。
5. **n=1。** base の 539.83 秒は他 wave 15 本 (535〜566 秒) と整合するが、シャード側の再現性は未測定。
6. 現行の k4 は「1 lease の中の分割」ではなく **4 つの独立 dispatch** に近い。
   本番形なら coordinator の直列作業 (canonical collection・manifest・照合) が乗る。

**それでも確からしいこと:**

- **件数均等は無意味。** 件数を完全に均等 (2182/2181/2181/2181) にしても実時間は
  437.8 / 227.3 / 53.4 / 16.5 秒。均衡化は実測時間の重みでしか行えず、
  **その重みは新規テストに対して常に陳腐化する** (決定性設計の中心課題)。
- **下界は k に依存しない。** 単体最長 263.08 秒 (非競合時) で、時間均等シャード 0 の wall は 271.87 秒。
- **コアは余っている。** 走行中の実測で平均 4.4〜6.0 コア / 48。suite は subprocess・git 待ちで律速される。
  分割の利得の一部は並列度ではなく**競合の緩和**である (最長テスト 303.96 → 263.08 秒)。
- **ポイントは不変ではない。** 段 2 が置いた「±10% を不変とみなす」基準に対し、+16% と +39%。

## 5. 占有時間の内訳 (Amdahl、要件 2)

サービス時間は `S(k) = F_fixed + U_unshardable + (T_test − U_unshardable)/k + H(k)` の形になる。

| 区間 | 実測 | 分割で縮むか |
|---|---|---|
| lease 取得後の main 取り込み (`merge --no-ff` ほか) | 数十秒 | いいえ (取得後に行う正しさの機構) |
| **受入全走** | **546 秒** | 一部。**263 秒は分割不能** |
| dispatch queue + bootstrap | 19〜350 秒 (実測幅) | **いいえ。k 本にすると増えうる** |
| land (ff-only + fold) | 十数秒 | いいえ |
| 全史 provenance 監査 (land lock の外だが lease は保持) | **44 秒** | いいえ |
| `check_docs` | 3 秒 | いいえ |

**注意:** 待ち手の poll (30 秒) は **lease 取得の前**にしか回らないので占有ではない (`dev_wave_wait.py:607–628`)。

機械的な合計は約 11 分だが**観測される占有は 15〜25 分**で、差は
**親 (LLM) が lease を握ったまま行う判断・記録・commit の時間**である。
分割が取り戻せるのは受入 546 秒のうち 274 秒 = 占有の **18〜30%**。
`S(∞) ≥ F_fixed + 263 秒` であり、ゼロにはならない。

**待ち行列としての効き:** 単一 lease の処理能力は占有 900〜1500 秒から **2.4〜4.0 wave/時**。
理想的な短縮後でも **2.8〜5.2 wave/時**程度で、**4 倍にはならない**。
到着率 λ が未計測なので、「どれだけ行列が縮むか」は数値保証できない (§9)。

## 6. 機構案

### (M0) 分割不変性と排他閉包を成立させる — **分割を採る採らないに関わらず先に要る**

- (i) `orchestrator/` を conftest で明示的に `sys.path` へ入れ、偶然の module 副作用への依存を断つ。
  検査は**収集だけでは足りない** (実行時 import があるため)。
- (ii) 排他の正本を **marker 名から resource conflict graph へ**。各 node が read-set / write-set を宣言し、
  同じ mutable resource に触る producer/consumer をプロセス・ノード横断の同一排他域へ閉じる。
  分類漏れを安全側に倒せないなら、共有 checkout をやめてシャードごとに隔離する。
- 受理集合への影響: **強める方向**。現在は `-k` や単一 file の targeted run でも同じ罠を踏むので、
  分割を採らなくても価値がある。既知の [T-715]/[T-716] とも同じ面。
- 規模: (i) 小、(ii) 中〜大。

### (M1) manifest の和で acceptance を証明する

- coordinator が canonical collection・snapshot・group 閉包・割付け・期待 artifact を manifest に固定し、
  全シャード完了後に §1 の (A)〜(E) を再検査する。
- 変更面は `run_tests.py` の runner-only option 消費 (149–156)、形状判定 (388–426, 505–563)、
  preflight 構成 (1784–1792)、`conftest.py` の collection 出力 (238–282)、task-run identity、
  N request の dispatch/receipt/JUnit 併合。**規模は大。**
- **manifest だけでは (F) を証明できない。** canonical collect を行った coordinator の
  `sys.path` 副作用は別プロセスのシャードへ移らない。**M0 の後でなければ候補にならない。**

### (M2) 非選択オプション allowlist に `--tx` / `--rsyncdir` を足す — **不成立 (実機で反証)**

- 本機の xdist 3.8.0 は `numprocesses` が非ゼロのとき
  `config.option.tx = ["popen"] * numprocesses` で**指定済み `--tx` を local popen へ上書きする**
  (`xdist/plugin.py:325`、親が逐語確認)。`run_tests.py` は明示 `-n` が無ければ必ず `-n <既定>` を足す
  (367–385 行)。→ **allowlist を直しても remote worker は 1 台も増えない。**
- `--rsyncdir` は xdist 4.0 で削除予定、既定 ignore `.*` が `.git` を送らないため実行環境が変わる。
- **「非選択オプションだから安全」という論法自体も撤回する。** selection を変えないことは
  outcome を変えないことではない (実行 root・環境が変われば skip 経路が変わる)。

### (M3) PBS 複数ノード確保 + 単一 pytest プロセス

- Pegasus/NQSV では `select=k` ではなく **`-b k`** が正しい。現 dispatcher は job script・qsub・receipt の
  すべてが 1 ノード固定 (`#PBS -b 1`、`"nodes": 1`)。
- `-b k` の既定 `distrib` は同じ script を各ノードで起動するので、値だけ変えると複数 process が
  同じ `result.json` と marker を書く。leader 1 台だけで pytest を回せば意味論は安全だが、
  残り k−1 台の CPU は使われず **ポイントだけ k 倍**になる。**短縮機構にならない。**

### (M4) 占有の非全走部分を削る

- provenance 監査 44 秒・check_docs 3 秒は既に小さく、provenance は既に land lock の外に出ている。
- 削り代は**親の turn 時間**にある (lease を握る前に記録・commit を済ませ、握ったら走らせて即 release)。
- 受理集合に触れない。規模 = 運用規範のみ。

### (M5) 遅いテストを是正して下界を下げる

- `test_s8b_oracle_driver.py` 4103.9 秒 / `test_codex_reasoning_ab.py` 2436.8 秒 = 直列総和の **63%**。
  200 秒超のテスト 9 本はすべてこの 2 file。**下界 263 秒はこの file の 1 テストが作っている。**
- `_t080_stub_free_e2e_repo` は「36MB / 2300 ファイルの copytree + `git submodule add` + 子 python での
  draft→finalize→commit→verify で 1 回 15〜22 秒」で [T-057] により**プロセス内**メモ化済み。
  **xdist の worker はプロセスが別なので、9 本が別 worker に散れば 9 回払う。分割しても減らない。**
- **分割と違い、受理集合に触れず、全 wave の占有が同時に縮む。** 規模 = 中 (内訳の計測が先)。

### (M6) allocation-aware な単一 xdist controller (将来の cross-node 候補)

- `-b k` を 1 回だけ確保し、leader 1 つで pytest controller を 1 つだけ起動、
  deprecated rsync を使わず全 worker が同じ Lustre checkout を参照、
  割当て host だけへ sanctioned transport で worker を起動する。総 worker は 48 のまま
  (k=4 なら各ノード 12) から始める。collection・session hook・JUnit・`loadgroup` は 1 つ。
- **xdist の worker は各自が全 suite を collect するので、M1 より (F) を保ちやすい。**
- ただし **「単一 collection」ではない** (collection は worker ごとに走る)。
  transport 可否・共有 checkout の整合・root ごとの submodule attest・receipt 拡張を実測するまで
  I1 は宣言できない。規模 = 特大。

## 7. 推奨

**(A) いま分割は入れない。(B) M0 と M5 を先に片付ける。(C) その後 M1 か M6 を再評価する。**

- **待ち行列への費用対効果の最上位は、本件ではなく既裁定の [T-812]** である。
  自己保持 lease deadlock は 1 回あたり 18〜20 分級の**無効占有**を生み、追加ノード無しで除去できる。
  分割が取り戻せるのは占有の 18〜30% であり、しかも受理集合の意味論に触る。
- **(C) の再評価条件 (3 つとも必要):**
  1. M0 が完了し、分割不変性と排他閉包が**機械検査で維持**されている。
  2. 受入中に repo (ignored 領域を含む) へ書く経路が無い、または snapshot fencing が実装されている。
  3. 性能の再評価が、**意味論 screening を通過した後に**、repo 外 receipt・隔離 canonical control・
     同一 tip・**out-of-sample の重み**・固定総 worker・複数 partition・paired block・
     ノードの Latin square で行われている。
- **採らない理由の要点:** 分割は「全走が緑」の意味を分割の取り方に依存させる。
  これは規律 2 の面に当たる。実測では 2 通りの分割の両方が別々のテスト群を静かに消した。

## 8. [T-810] への条件付き (要件 3)

実 wall に依存するテストは、静的検索で少なくとも 8 面ある。

| test | gate |
|---|---|
| RuleOps 実 checkout | 実 `monotonic` で `<60s` かつ `<45s` (`test_ruleops.py:3444–3451`) |
| codex worker launcher | 子へ既定 `--max-wall-clock-s 3` (`test_codex_worker_launch.py:949–960`) |
| s8c preregistration | git timeout 180s (`test_s8c_preregistration_invariant.py:28–65`) |
| dev-waves protocol | slow-byte drip に対し `<0.15s` (`test_dev_waves_protocol.py:256–312`) |
| dev-waves worker | `<5s` / `<2s` (`test_dev_waves_worker.py:188–198, 378–385`) |
| dev-waves checker | `<1s` (`test_dev_waves_checker.py:304–317`) |
| login headroom | lock deadline `<0.5s` (`test_login_headroom.py:982–1001`) |
| dev-wave land | lock-busy `<2s` (`test_dev_wave_land.py:1223–1245`) |

本 wave の probe は 8 ノード (bnode014/015/016/017/020/022/023/024) に散り、これらは全 arm で緑だった。

> **条件付き結論:** 分割は「どのテストがどのノードで走るか」を走行ごとに変える。
> 上の gate の余裕がノード間差を吸収できるかは、**[T-810] (ノード間性能差の測定 protocol、未 land)**
> の結果が出るまで判定できない。特に RuleOps node は `real-repo` group に含まれるため、
> **group を持つシャードの host が critical path と wall gate を同時に支配する**。
> **本推奨 (いま分割しない) はこの点に依存しない** — §3 の (F) 違反だけで現状の分割は反証済みである。
> [T-810] への依存は、M6 の速度・ポイント・wall flake 率を採否判断する段階に限る。
> なお [T-810] は CC binary の protocol なので、**pytest workload 用の同型 protocol は別に要る**
> (runbook 自身が pytest wall を CC throughput の代理にしないと明記している)。

## 9. 未測定 (根拠にしないこと)

- **到着率 λ と占有時間の分布。** 待ち行列の短縮量を数値保証できない。
  必要なのは wave の到着時刻・lease 取得/開始/終了・再試行・land 失敗の記録 (数週間分)。
- **意味論的に緑な状態での性能。** 全 arm が赤を含む。screening 通過後の paired 測定が要る。
- **out-of-sample の重みでの分割性能。** k4time は in-sample。
- **総 worker を 48 に固定したときのノード分散効果** (4 ノード × 12 worker 対 1 ノード 48 worker)。
- **k=2 / k=8。** 下界から k=8 に利得が無いことは言えるが、k=2 で足りるかは補間。
- **分割不変性の破れの全体像。** 単独収集で 2 file、静的抽出で 5 file・9 文が下限。完了値ではない。
- **263 秒テストの内訳** (subprocess / build / git / sleep)。M5 の第一歩。
- **Pegasus での cross-node transport の可否** (M6 の前提)。
- 排他閉包の完全な列挙 (read-set / write-set 宣言が無いため静的には出せない)。
