# 新規 silo 変異 14 本と trigger-misattr を現 pin で実走し、検出期待表と突き合わせた ([T-2847] 残り (2) のうち pin C に依存しない部分、2026-09-23)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
wave `dev-wave-t2847-mutation-run` (branch `worktree-dev-wave-t2847-mutation-run`)、起点 local main `65fd1422f` (開始 gate rc 0、2026-09-23 20:0x JST)、CCBench submodule `e9e477ca` (pin を動かしていない。並走の T-2858 が C へ進める wave)。
job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/` (brief・Codex の prompt / 出力・起動器・計測の原本 JSON と subprocess 記録・変異 harness の記録)。
段 1〜6 の全文は `verbatim/` (段 2 plan、段 3 相談 2 本、段 4 裁定、段 5 author 4 本と共通契約、段 6 review 2 本・裁定・fix 7 本・焦点再レビュー 2 本)。

期待の出所は `output/insights/2026-09-22/t2847-verifier-detection-design/README.md` (以下「設計書」) の §4。V 番号は設計書のもの。事前登録 (workload・期待・job 分割・分類の規則) は `verbatim/s4-ruling.md` の R2〜R5。

## 1. 依頼と結論

依頼 (ユーザー直接起動の `/dev-wave [T-2847]`、逐語は `verbatim/request.md`): 残り (2) 変異の実走のうち pin C に依存しない部分。本体は trigger-misattr (trigger-gating 骨格の上) の計算ノード実走。新規 18 変異 (D16 第 3 類の out-of-tree patch) は現 pin `e9e477ca` の上で作れて取り込めるものだけ同じ wave で実走する。結果は検出表 (期待した層で検出 / 別の層で検出 / 盲点として certified / 未発生・誤検出) に実測で書く。mocc の既存 4 本と sort-nonswo は範囲外。

結論:

1. **新規 18 のうち silo の 14 本 (変異 11・正しさを保つ対照 3) を patch にして実走し、trigger-misattr (V08) も実走した** (計 15 行、表は §3)。mocc の V25・V34 は X/P の emitter が pin C の計装の内容なので、si の V28・V29 は現行 parser が si の旧形式 trace を拒否して変異の有無に関わらず parse error になるので、走らせていない (段 4 裁定 R1、§4)。
2. **15 行の分類:** 期待した層で検出 3 (V17 巡回・V19 version dup・V20 orphan)、別の層で検出 1 (V18: 期待した version dup に加えて期待外の genesis への commit 4 件)、盲点として certified 6 (V22・V23・V26・V27・V35 と V08)、未発生 2 (V21 は発火 0 回、V24 は機構に未到達)、正しさを保つ対照 3 は誤検出 0。
3. **「盲点として certified」の 6 行は、変異が実際に挙動を変え、その取引が commit したことを発火診断で確かめたうえで certified だった** (§3.2)。発火診断は各 patch の有効枝だけにある計数で、終了時に stderr へ 1 行出す (段 4 裁定 R2)。「検出しなかった」を「発火しなかった」と取り違えないための記録で、verifier の判定には使っていない。
4. **V20 は初回の実装に誤りがあった。** 公開版の番号を更新ごとに減らす版で走らせると、巡回 1 本 (G2・長さ 4) と orphan が出た。巡回の rw 辺はすべて V20 自身が公開した版の番号の逆転から生じており、狙った機構 (公開版と C/W 行の不一致) とは別物だった。番号を増やす向きに直した patch で測り直すと orphan だけの I になった。初回の結果も表に残す (§3.1、段 1 brief P5)。
5. **trigger-misattr は既存 driver のままでは現行コードで走らなかった。** `s8a_trigger_coverage.main()` は misattr の build を admission (source digest) に通すが、現行の source digest は裸マクロ `IZANAGI_BREAK_TRIGGER_MISATTR` を未知マクロとして fail-closed で拒否する (T-148)。この防壁は緩めず、repo 外の起動器で misattr の build だけを他の壊し patch と同じ直 CMake 経路 (condition gate は通す、admission は通さない) に替えた。checks 11 個は driver の式のまま、すべて真 (§3.3)。
6. 計算ノードの使用 (job Elapse): 計測 7 run 計 1,148 秒 (§2.3。うち 1 run は driver の停止、1 run は V20 修正後の測り直し)、焦点走 2 回 393 秒、変異 matrix 1,343 秒 (§7)、受入 890 秒 (§8)。合計 3,774 秒 ≈ 1.05 node 時間。

## 2. 何をどう走らせたか

### 2.1 patch

`patches/broken-silo-*.patch` 11 本と `patches/control-silo-*.patch` 3 本 (V 番号・macro・変更は `patches/README.md` の該当節)。各 patch は `CCBENCH_` 外の裸マクロ 1 個の `#if` 枝に閉じ、未定義で pin と一致する (実装子が枝を除いた全文を pin と比較して確認)。条件 gate の許可ドメインに 14 macro を足した (既存の壊し patch と同じ登録。判定基準は変えていない)。patch は Codex author が書き、段 6 のレビュー 2 本・fix 3 巡・焦点再レビュー 2 巡を通した (`verbatim/`)。

発火診断 (段 4 裁定 R2): reached = 変異枝に入った回数、changed = 元コードと違う挙動を実際に生んだ回数、committed = changed を含む取引が commit した回数 (V18・V35・V21 は追加の数も出す)。relaxed atomic の加算だけで、出力は process 終了時の 1 行。

### 2.2 起動器と経路

repo 外の起動器 `launch_mutation_run.py` (Codex author、job dir。前回 wave の `launch_patch_verify.py` を土台に、依存物・compiler・出力先の供給を同じ形で保つ):

- `mutations --job J1〜J4`: job ごとに stock (patch なし・TRACE=1) を 1 回 build し、job 内の各 workload で stock を 1 run ずつ走らせてから、各変異を既存の `s2_verify_calibration._broken_build_and_verify` (patch の `git apply` (fuzz なし)・condition gate・`-DCMAKE_CXX_FLAGS=-D<macro>=1`・commit 件数の証人つき verifier) で build・実走する。stock の前提 (certified・integrity clean・commit 非空) が崩れた workload の変異は走らせない (今回は全 workload で成立)。V21 だけ、同じ trace を証人なしでも verifier に掛ける。
- `s8a`: §1 の 5 のとおり。骨格+計装は driver の `_build` (admission つき)、misattr は直 CMake。
- ycsb の run と verifier の stdout / stderr をすべて保存する。

**起動器の要約欄の誤り:** J1〜J4 を走らせた版 (sha256 `e7be718a…`) は、`cmake --build --target ycsb_silo.exe` の呼び出しも ycsb の実行と分類したため、結果 JSON の変異の区間で run と発火行の要約が空になった (stock の区間は正しい)。**検出表は保存した subprocess 記録から親が集計し直した** (`raw/*.agg.jsonl`、集計 script は job dir の `aggregate.py`)。起動器は後の版 (sha256 `41fb84ff…`、J5 の再走と J2 の再走で使用) で分類を直した。

### 2.3 workload と job

共通 = 200 tuple・zipf 0.9・1 s・`clocks_per_us` 1800 (s2 の定数)。`t/r/m/o` = thread 数・読み比率・rmw・1 取引の操作数。

| W | t/r/m/o | 変異 |
|---|---|---|
| W1 | 4/50/false/5 | V17・V22・V35 |
| W2 | 4/0/false/5 | V18 |
| W3 | 1/0/false/1 | V19・V23 |
| W4 | 1/50/false/5 | V20・V24・V33 |
| W5 | 1/50/false/10 | V21・V26 |
| W6 | 1/0/false/10 | V27 |
| W7 | 4/50/true/5 | V31 |
| W8 | 1/0/false/5 | V32 |

V08 は driver 既定 (200 tuple・zipf 0.9・rratio 50・rmw・max_ope 5・1 s、4 thread と 1 thread、`clocks_per_us` 2100)。

| run | request | 計算ノード | Elapse | 起動器の rc | commit (checkout) | 内容 |
|---|---|---|---|---|---|---|
| m1-J1 | 21202.nqsv | bnode042 | 194 s | 0 | `c2878989a` | V17・V22・V35・V18 |
| m1-J2 | 21219.nqsv | bnode091 | 194 s | 0 | `6c67f0679` | V19・V23・V20 (初回の実装)・V24 |
| m1-J3 | 21203.nqsv | bnode047 | 143 s | 0 | `c2878989a` | V33・V21・V26 |
| m1-J4 | 21221.nqsv | bnode042 | 178 s | 0 | `c2878989a` | V27・V31・V32 |
| m1-J5 | 21222.nqsv | bnode059 | 108 s | 1 | `c2878989a` | V08 (driver の `main()`、misattr build で停止) |
| m2-J5 | 21249.nqsv | bnode032 | 139 s | 0 | `c2878989a` | V08 (起動器の手順) |
| m2-J2 | 21277.nqsv | bnode004 | 192 s | 0 | `ff9e48b66` | V19・V23・V20 (修正後)・V24 |

compiler は全 job で policy が選んだ `x86_64-linux-gnu-g++-11`。各 job は専用の計測用 worktree (detached、submodule 初期化) から `tools/pegasus/dispatch_compute.py --task generic` で投げた。V20 以外の patch は `c2878989a` と最終 commit で同じ bytes。原本の結果 JSON の sha256 は §5。

## 3. 観測と期待の突き合わせ

「巡回」は verifier の `total_cycles`。integrity の他の項目 (orphan read・version dup・txid の重複と欠番・genesis への commit・版の不一致・frame の破れ・X・P・I) は、表に書いたもの以外すべて 0。stock 対照 11 run (W1〜W8、J2 は 2 回) はすべて serializable・certified・integrity clean。

### 3.1 検出表

| V | 変異 | W | 期待 (段 4 R4) | 観測 | 発火 changed / committed | 分類 |
|---|---|---|---|---|---|---|
| V17 | 他者 lock 中の読み key での abort を外す | W1 | N (巡回)、未発火なら S | **N**: 巡回 263 (報告 20 本はすべて G2・長さ 2)、integrity 0、取引 329,673 | 2,860 / 2,752 | 期待した層で検出 |
| V18 | commit TID から書く key の現版を外す | W2 | N (巡回) または I (version dup) | **I**: 巡回 0、version dup 189,746、**genesis への commit 4**、取引 290,850 | 102,283 / 102,283 (版 ≤ 書く key の現版: 102,283) | 別の層で検出 (genesis への commit は期待に無い) |
| V19 | commit 版を (1,1) に固定 | W3 | I (version dup) | **I**: version dup 1,055,879、取引 1,056,079 (再走 1,054,616 / 1,054,816) | 1,056,078 / 1,056,078 | 期待した層で検出 |
| V20 | UPDATE で公開する版だけを C/W 行と違う値に | W4 | I (orphan) | 初回 (公開 epoch を減らす版): **N**、巡回 1 (G2・長さ 4)・orphan 673,163。修正後 (増やす版): **I**、orphan 688,989、巡回 0、取引 293,502 | 初回 694,806 / 278,156、修正後 709,546 / 284,402 | 期待した層で検出 (修正後)。初回の巡回は実装の誤り (§3.4) |
| V21 | 終了 flag の後の取引で writePhase を省いて成功を返す | W5 | 証人あり I・証人なし S (発火時) | **S** (証人あり・なしとも)、取引 160,552 | 0 / 0 | 未発生 |
| V22 | read の再確認で 2 度目の TID を採り payload を取り直さない | W1 | S (盲点) | **S**、取引 314,272 | 47 / 28 | 盲点として certified |
| V23 | 公開 payload の先頭 byte を反転 | W3 | S (盲点) | **S**、取引 1,051,724 (再走 1,050,810) | 1,051,724 / 1,051,724 | 盲点として certified |
| V24 | node map の検証を外す | W4 | S (未到達) | **S**、取引 301,471 (再走 304,887) | reached 0 | 未発生 (機構に未到達) |
| V26 | 自分の書いた key の read で旧 payload を返す | W5 | S (盲点) | **S**、取引 160,064 | 48,558 / 39,922 | 盲点として certified |
| V27 | 同じ key の 2 度目の update で buffer を誤って書く | W6 | S (盲点) | **S**、取引 136,752 | 166,756 / 98,824 | 盲点として certified |
| V35 | commit TID から読んだ版を外す (Silo の TID 規則) | W1 | S (盲点) | **S**、取引 326,314 | 7,832 / 7,832 (版 ≤ 読んだ版: 7,832) | 盲点として certified |
| V08 | lock 競合の abort を node validation と誤記録 | s8a t4 | verifier は S、構造ゼロ検査が赤 | **S** (巡回 0)、abort 7,572 件の要因のうち node-vali 4,184 (lock-conflict 0) で構造ゼロ検査が赤 | — | 盲点として certified (abort 要因の構造ゼロ検査が捕捉) |
| V31 (対照) | abort 後の backoff を 2 回 | W7 | S | **S**、取引 252,628 | 6,086 / 0 | 誤検出なし |
| V32 (対照) | write set を共通の逆順で並べる | W8 | S、X/P 0 | **S**、取引 287,987 | 287,969 / 287,969 | 誤検出なし |
| V33 (対照) | 要素数が偶数の write set の取引を lock 前に abort | W4 | S、commit 非空 | **S**、**取引 3** (abort 1,232) | 1,232 / 0 | 誤検出なし (commit は 3 件だけ) |

### 3.2 分類の規則と集計

分類の規則は事前登録 (段 4 R4): 期待した層の counter で N / I → 期待した層で検出。期待に書いていない層の counter も非 0 → 別の層で検出。S のとき、changed ≥ 1 かつ committed ≥ 1 なら盲点として certified、そうでなければ未発生。対照が N / I なら誤検出。

| 分類 | 行数 | 内訳 |
|---|---|---|
| 期待した層で検出 | 3 | V17 (巡回)、V19 (version dup)、V20 (orphan、修正後) |
| 別の層で検出 | 1 | V18 (version dup に加えて genesis への commit) |
| 盲点として certified | 6 | V22・V23・V26・V27・V35 (変異が commit した取引を含む履歴が certified)、V08 (verifier は certified、abort 要因の検査が捕捉) |
| 未発生 | 2 | V21 (終了 flag が取引の途中で立つ場面が 0 回)、V24 (YCSB は範囲読み・insert を使わず node map の検証に届かない) |
| 誤検出 | 0 | 対照 V31・V32・V33 はいずれも S |
| 計 | 15 | 変異 12 (V08 を含む) + 対照 3 |

### 3.3 V08 trigger-misattr の checks (m2-J5)

`raw/s8a-m2-J5-summary.json`。checks 11 個すべて真: 骨格 4 thread は certified、abort 7,882 件に対し要因の記録 (A 行) も 7,882 件で全数一致、構造ゼロ (YCSB で起きない要因が 0)、早期 abort 0、実在の要因 (lock-conflict 4,445・readvali-locked 2,682・readvali-tid 755) が記録された。1 thread は abort 0。misattr の 4 thread は verifier が certified (巡回 0) のまま、要因は node-vali 4,184・readvali-locked 2,640・readvali-tid 748 で lock-conflict が 0 になり、構造ゼロ検査が赤、保存則 (A 行 7,572 = abort 7,572) は破れなかった。2026-07-10 の記録 (`patches/README.md` の trigger-gating 節、linux-baremetal、旧 pin) と同じ型である (件数は pin・機体が違うので比べない)。

### 3.4 V20 の初回の誤り

初回の V20 (公開 epoch を UINT32_MAX から更新ごとに 1 ずつ減らす) の巡回 1 本は、4 本の rw 辺がすべて「V20 が公開した版」と「公開版から導かれた C/W 版」の間にあった (例: key `...1f` で読んだ版 [4294967289, 268435456]、次の版 [4294967293, 268435457])。後から公開した版ほど番号が小さく、同じ key の版順が実際の書き込み順と逆転して見かけの rw 辺ができていた。これは狙った機構 (公開版と C/W 行の不一致) とは別の機構なので、段 1 brief P5 に従い patch の実装の誤りとして直し (公開 epoch を 2^31 から増やす、wave commit `ff9e48b66`)、別 run (m2-J2) で測り直した。修正後は orphan だけの I で、巡回は 0 だった。V20 の patch は段 6 で 3 回直している (tid の巻き戻り → 公開値の重複 → 版順の逆転)。

## 4. 走らせなかったものと理由

| V | 理由 |
|---|---|
| V25・V34 (mocc) | 期待 (完走 prefix が S、温度述語の等価変形で S) の検証には X/P の emitter が要り、それは pin C の計装の内容。既存の mocc 4 本と同じく C 依存 (段 4 R1)。V25 の停止そのものは計装なしでも観測しうるが、今回は走らせていない |
| V28・V29 (si) | 現行 parser が si の旧形式 (v1) の trace を拒否し、変異の有無に関わらず parse error になる。si の emitter の v2 化 ([T-2854] の実装単位 (12)) の後に意味を持つ |
| V07 sort-nonswo・mocc 既存 4 本 | 依頼で範囲外 |

## 5. 記録の置き場と束縛

- `raw/m1-J{1,2,3,4}.agg.jsonl`・`raw/m2-J2.agg.jsonl`: 保存した subprocess 記録から親が集計した行 (stock と各変異の run・verifier の要約・発火行)。
- `raw/meta-*.json`: 各 job の起動器の meta (hostname・compiler・差し替えた名前・rc・例外)。
- `raw/s8a-m2-J5-summary.json`: V08 の checks と run の要約。原本 `runs/m2-J5/s8a_trigger_gating_coverage.json` (446,774 bytes) の sha256 `e57f4153d397c49ce0d839eab8dc21062da0e5aaac67ad64ccb8ac23b1467934`。
- 結果 JSON の原本 (job dir `runs/`、大きいので repo に入れない): m1-J1 `a4a6ab563e66f0e17999c8875e72fba51d30a51480b79729592156a583e9f265`、m1-J2 `21be8e6e94932a8394c4a3afe8576c0546a20089580f9c7766714b924da01022`、m1-J3 `4f7d979a8d1f37fca64ce1487b0ea35127d70b83fdaa55d67e2c94a074380d8f`、m1-J4 `97335bfd9a0ddb194b1f6c3e00d26e6fe5d9c9b2ec5b835219314b008ca290b3`、m2-J2 `685f3e1ad3a0cdba37487553bcadcec7784f65716eaed8355523380de6730d7e`。
- `raw/mutation-spec-{probe,final}.json`: 変異 harness の spec。

## 6. 限界・言わないこと

- 各行は 1 回の有限の走の観測である。未発生の 2 行を「検出力が無い」とは書かない。V21 は終了 flag が取引の途中で立つ schedule に依存し、1 s・1 thread の 1 回では起きなかった。V24 は YCSB では機構に届かず、範囲読みの phantom への検出力はここでは測っていない (TPC-C 段 2 の設計が正本)。
- 「盲点として certified」は、verifier の判定の宣言範囲 (設計書 §2.2) の外にある変更が、変異を含む取引の commit した履歴で certified になったという観測である。verifier の欠陥の主張ではない。V08 は verifier の外の構造ゼロ検査が捕まえた。
- V18 の genesis への commit 4 件は、読み集合が空の blind write で commit TID の元が 0 になる場合と推測できるが、run ごとの原因は確かめていない。
- V33 の対照は commit 3 件だけの短い履歴についての S である。偶数の write set の取引が再試行で abort を繰り返したためで、対照として弱い。
- V20 の最終形の公開値 (epoch を 2^31 から増やす) が 1 s・W4 で通常の版と重ならないことは、実行量についての前提であって source 上の厳密な上限ではない (実装子の報告 `verbatim/s6-fix3-fa.md`)。
- trigger-misattr は driver の `main()` ではなく、起動器が同じ関数と同じ checks の式で組んだ手順で走らせた。差異は misattr の build が admission を通らないことだけである。
- 性能値は取っていない。job の Elapse は計算資源の記録である。
- tracked の verifier・driver・source digest は編集していない。条件 gate への登録・screening の既定値・test の表の更新は、新しい patch を既存の経路で build するためのものである。

## 7. 変異 matrix (実装面の変異テスト)

実装面 (patch・条件 gate の登録・test の表) の誤りを既存の test が殺すかを、`tools/mutation_worktree.py` を独立 clone に当てて確かめた。runner = `tools/run_tests.py --force-dispatch` で `test_condition_meaning_gate.py`・`test_ccbench_spawn_sites.py`・`test_screening_driver.py`・`test_p3_s4_loop.py::test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted`。

- 事前登録 (段 4 R6) の M1〜M4 のうち、M4 は「patch に同じ `#if` の site を 1 つ足す」だと patch の hunk 行数が壊れて別の理由で赤になるため、同じ誤り (site 数の虚偽) を登録簿側の site 数 (`IZANAGI_BREAK_READ_LOCK_CHECK: 4 → 5`) で起こす形に再照準した (erratum)。
- probe (全件 SURVIVED 期待、独立 clone = `6c67f0679`、spec sha256 `59db9354…`): 正例 M0 (comment だけの変更) は生存、M1〜M4 はすべて赤 (`raw/mutation-probe-summary.json`)。
- final (観測した赤 node を期待 node に固定、独立 clone = 最終の実装 commit `ff9e48b66`、spec sha256 `d951ad2ac5af7b9c80fcc6fcd2fdf1cfd0bd90df777cd7950c60a2901e6b25e0`): **KILLED 4・SURVIVED 1 (正例)・MISMATCH 0** (`raw/mutation-final-summary.json`、原本 sha256 `56e3f6fd6d42867ba07f234c17a3aa9a24aeba1cb42ce7dae14f22fd82153cb4`)。

| 変異 | 誤り | 赤 node 数 | 赤の理由 |
|---|---|---|---|
| M0 (正例) | comment 1 語の変更 | 0 | — |
| M1 | `_DEFINE_SPECS` から新 macro 1 件を削る | 7 | 登録簿から 1 件欠けた (在庫照合・domain 件数・branch 選択・screening の既定値照合) |
| M2 | `_CONDITIONAL_BRANCH_WITNESSES` から 1 件を削る | 5 | witness の欠落 (patch 束縛・branch 選択・domain 件数) |
| M3 | `_DEFINE_SPECS` の key を 1 字違える | 7 | 登録名と patch の macro の不一致 |
| M4 | 登録簿の site 数を 4 → 5 | 4 | site 数と patch 本文の不一致 |

各変異の赤 node は複数だが、どれも 1 つの誤り (登録簿の 1 件の欠落・名前違い・件数違い) から生じている。patch の中身の誤り (未定義側の pin 一致・1 patch 1 機構・変更の向き) は test では殺せないので、実装子と親の source 照合 (`verbatim/s5-author-*.md`・段 6 レビュー) と §3 の実走で確かめた。

計算ノードの使用 (job Elapse): probe 7 request 673 秒、final 7 request 670 秒。

## 8. 受入全走

- 1 回目 (tag final): 投入前の main 取り込みで `orchestrator/tests/test_p3_s4_loop.py` が両親と違う内容に自動合流し、実装面に Codex author の無い merge として provenance の事前検査が赤 (rc=94、merge は中止)。Codex が 3 版 (base `4f0a74997`・wave `5ee4e8578`・main `973db24ed`) と照合して修正なしで確定し、親が merge `0721f059f` (Codex author つき、submodule は pin C `68106660`) を作った。
- 2 回目 (tag final2): 3 shard とも test は 1 件も走らず、shard-0 が計算ノードの待ち行列で `queue-wait-timeout`、shard-1・2 は連動して中止 (signal 15) した (rc=70、`dispatch-attestation-missing`)。基盤の赤でコードに帰属しない (DW-O18)。Elapse は log に残っていない。
- 3 回目 (tag final3): 投入時に local main `aa96126f2` を merge `ddb079e34` で取り込み、**27,557 passed・74 skipped、child-green** (受領証 `acceptance-receipt-final3-1.json`、tested main `aa96126f2`・tested tip `ddb079e34`)。3 shard の Elapse 249・247・394 秒 (計 890 秒)。

計算ノードの使用 (記録のある job Elapse の合計): 計測 1,148 秒 + 焦点走 393 秒 + 変異 1,343 秒 + 受入 890 秒 = 3,774 秒 ≈ 1.05 node 時間 (受入 2 回目の中止分は含まない)。
