# 段 4 裁定 — [T-2854] (1) header 差分受理規則 v2 の実装

入力: brief (`s1-brief.md`)、生死確認 (`s1-live-summary.md`)、段 2 plan (`out/s2-plan.md`)、段 3 相談 A (`out/s3-consult-A.md`、正しさ境界) ・B (`out/s3-consult-B.md`、実効性と過剰・削除)。
裁定 inbox の再走査: local main は着手時 `339d7c188` から不動 (20:0x JST)。wave 開始後の新しい裁定なし。

## 1. 所見の裁定

| 所見 | 判定 | 採否・扱い |
|---|---|---|
| A1 stock だけで genome を選ぶと genome でだけ読む production target を落とす | real | 採用 → R4 実装 (§2 S4) |
| A2 同じ (entry, argv) でも生成物・依存閉包の内容が違えば集約は偽緑 | real | 採用 → 集約鍵に依存閉包の内容 digest を含める (§2 S7) |
| A3 TRACE token の無い entry を両 TRACE 状態で確かめないと consumer 判定が崩れる | real | 採用 → 全 entry で両状態を作り実効値を確認 (§2 S5) |
| A4 production target の出所の未確定 | real | 採用 → `_v2_commands` の build argv から導く (§2 S4) |
| A5 変異 #4・#5・#6 の test が狙いを識別できない | real | 採用 → §4 の変異登録で単一理由の fixture を指定 |
| B1 合成 fixture を production configure 経路に縛ると新分岐に届かない | real | 採用 → configure argv 供給だけを狭い seam にする (§2 S3) |
| B2 同一 (entry, argv) の集約 (R4) が plan から落ちた | real | 採用 (A2 の条件つき) |
| B3 0.52 node 時間は外挿 | real | 採用 → 判定 job の Elapse を実費として記録。見積りは §5 |
| B4 計算 job の実行条件が未確定 | real | 採用 → 判定 job script に事前確認を入れる (§3) |
| B5 実 CCBench の負例は通常 suite に置かない | real | 採用 → 判定 job 内の負例対照 (§3) |
| B 削減: 追加 stdout snapshot test・独自 digest・schema 変更は不要 | real | 採用 (既存 test の維持で足りる、`_comparison_evidence` を再利用) |
| plan 3: `git archive` を使わず git worktree で展開 | 一部 refuted | 与えられた repo の管理領域を変えないため worktree は作らない。scratch の bare clone に `info/attributes` (`* -export-ignore` `* -export-subst`) を置いて `git archive` し、全 regular file の blob sha1 と tree の file 集合を照合する (単位 11 の実証済み手順)。照合で export-ignore・subst の取りこぼしは拒否に変わる |

## 2. plan v2 (検査器 `tools/check_trace0_preprocess_identity.py`)

- **S1 起動 (P1):** header 分岐は CLI の 4 引数 `--header-cc <C compiler>` `--third-party-cache <dir>` `--dependency-prefix <dir>` `--scratch-root <dir>` が**全部**あるときだけ有効。header を含む差分でこれらが無ければ、現行と同じ文言 (`header の変更は consumer TU での解析が必要であり、この checker の保証範囲外なので fail-closed で拒否する: <path>`) で拒否。一部だけの指定は拒否。header を含まない差分でこれらを渡しても処理経路に使わない (.cc だけの report bytes は不変、P8)。compiler は既存 `--cxx` (C++) と `--header-cc` (C) の 1 組 = 1 起動 (P2)。
- **S2 diff 検証:** 共通拒否 (status ≠ M、mode 変更、regular file でない、非 C/C++) は現行順序のまま先に行い、header suffix だけを header 集合へ分ける。.cc は既存 `_compare_file` をそのまま通す。header と .cc が同居すれば両方の合格を要する。
- **S3 configure argv の供給 (P3、B1):** 既定の供給関数は production の `orchestrator.campaign.buildcache._v2_commands` を呼び、返る configure argv に `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON` と `-DCCBENCH_CCACHE=OFF` を足す (後者は production argv との差分として report に記録)。stock は `Genome(<protocol>, {})` (genome define なし)。toolchain dict は `{"cmake","cc","cxx"}` の realpath。FetchContent は hydrate の source (masstree は構成ごとの複製)。check 関数には「configure argv 供給」と「genome 空間」だけを差し替えられる keyword 引数を置き、test は小さな合成 CMake project 用の供給と小さな空間を渡す。依存列挙・TRACE 確認・前処理・比較・選定・予定集合照合は差し替え不可 (test も実物を通す)。
- **S4 選定 configure 集合 (R4、A1、A4):** production target の出所 = genome 空間を持つ各 protocol p について `_v2_commands(Genome(p, {}), …)` の build argv の `--target` 値 (取得できない・形が想定外なら拒否)。test では S3 の差し替え供給が同じ形で target を返す。選定の手順: (a) stock configure (旧新) で全 entry の依存を列挙する。(b) genome 空間を持つ各 protocol p について、stock で p の production target の entry が変更 header を読むなら p の空間全体を選定。読まないなら、p の空間の**全 genome を依存列挙だけ**で調べ (configure + p の production target の entry の依存列挙、旧新 × TRACE 0/1。生成物は同じ compiler・同じ側の stock の生成物を読むだけで build しない)、1 つでも読めば p の空間全体を選定。(c) 選定 configure 集合 = stock + 選定 protocol の全 genome。report に選定集合と、選定しなかった protocol ごとに調べた genome 数を列挙する。
- **S5 依存列挙と TRACE (R3・R6、A3、P5):** 選定 configure ごとに全 entry を旧新 × TRACE 0/1 で `-MG` なしに依存列挙する。各 entry の argv は `arguments` 優先、`command` は `shlex.split`。出力系 (`-o` `-c` `-MD` `-MMD` `-MP` `-MF` `-MT` `-MQ` と連結形) を除き、`-MG`・`@file`・`-Wp,` を含む entry は拒否。`-DTRACE=` token が 2 個以上か値が 0 以外なら拒否。token が 1 個ならその値を 0 / 1 に置換、無ければ末尾に `-DTRACE=0/1` を足す。各状態で `-E -dM -MD -MF <depfile>` を 1 回実行して依存と macro 状態を同時に得て、`#define TRACE <要求値>` が無い entry は拒否 (全 entry)。依存の失敗・rc≠0 は拒否。変更 header を 1 度でも読む entry の和集合を consumer とし、変更 header ごとに選定集合全体で consumer 0 件なら拒否。
- **S6 旧新 database の一致 (R3):** configure ごとに、照合済みの root (旧新の source root、build root、masstree 複製 root、third-party source root) を長いものから順に論理名へ置換した後の (file, target, argv) の多重集合が旧新で一致しなければ拒否。重複 entry は拒否。
- **S7 比較 (R5、A2、B2):** 比較の予定集合を依存列挙の後・前処理の前に固定する。予定の要素 = (configure, consumer entry)。同じ比較を 1 回に集約する鍵 = (entry の file・target、正規化 argv、旧側と新側それぞれの TRACE=0 依存閉包の全 file の正規化 path と内容 sha256)。鍵が同じなら結果を再利用し、report に属する configure を列挙。各比較で旧新の `-E -P -dD` と `-E` の入退場 file 列 (line marker の flag 1/2) を正規化後に `_comparison_evidence` で比べる。不一致は拒否 (最初の不一致で止めてよい。report に entry・configure・mode)。実行済み集合は予定集合と厳密一致 (過不足は拒否)。`__DATE__` `__TIME__` `__TIMESTAMP__` が旧新いずれかの完全展開に現れたら拒否。
- **S8 source (R2):** scratch に `git clone --bare --no-local <repo>`、`info/attributes` を置いて旧新を同じ長さの dir 名へ `git archive`、tree の regular file 集合と blob sha1 を全件照合。symlink・gitlink は拒否 (CCBench では生死確認で問題なし)。
- **S9 生成物 (P6):** 選定 configure ごとに masstree source を複製し `masstree_build` を build、複製側の `config.h` の存在を確認。生成 target 名は検査器の定数 (CCBench の実 target 名)。test の供給は自分の生成 target 名を返せる形にする (S3 の供給が「生成 target の列」も返す)。
- **S10 report:** header を含むときだけ `header_rule` field を足す (保証名 = D2255 項 2 の逐語、compiler 2 本の realpath と版、選定集合、consumer、予定・実行件数、比較 evidence、production argv との差分 `CCBENCH_CCACHE=OFF`、D780 項 1 の文言)。.cc だけの report は bytes 不変、schema 不変。
- **S11 並列と時間:** 依存列挙・`-dM`・前処理は `os.cpu_count()` 上限の thread pool。configure と `masstree_build` は直列。subprocess の timeout は configure 300 秒・`masstree_build` 600 秒・compiler 1 回 120 秒 (実測 max 0.8 / 10.6 / < 1 秒に対する余裕)。timeout は拒否。
- **S12 scratch:** 起動ごとに `--scratch-root` 下へ一意 dir を作り、終了時 (成功・失敗とも) に削除。

## 3. 判定 job (実 CCBench、計算ノード 1 job)

Codex author が gitignore 下に書き親が job dir へ退避する job script。事前確認 (bnode であること、cache・prefix・`/usr/bin/{gcc,g++}-{11,12}` の実在、scratch の空き 20 GiB、bundle head = 裁定済み C2') → GCC 11.4 と 12.3 の 2 起動を**並行**に実行し、report・rc・所要秒を保存 → 負例対照: scratch clone で C2' に `include/tpcc.hh` の `#line 56` を消す commit を作り GCC 11.4 で 1 起動 (期待: rc=1、完全展開の不一致、entry は TPC-C consumer)。walltime 1 時間 30 分。

## 4. 変異の事前登録 (実装後に anchor を固定し、単一理由性を確かめてから本走)

| ID | 変異 (検査器) | kill の期待 (test) |
|---|---|---|
| V1 | consumer 判定を「変更 header を直接 include する entry」に劣化 | 間接 consumer (wrapper 経由) の TRACE=0 値変更 fixture が pass に変わる → 負例 test が赤 |
| V2 | 依存列挙に `-MG` を足し、かつ生成 target の build を飛ばす (2 層、事前登録) | 生成 header 経由でだけ変更 header を読む consumer の値変更 fixture (他に正常 consumer あり) が pass に変わる → 負例 test が赤 |
| V3 | 生成 target の build を飛ばす (単層) | 正例 fixture が依存列挙失敗で拒否に変わる → 正例 test が赤 |
| V4 | 依存列挙を TRACE=0 だけにする | TRACE=1 でだけ読む consumer を含む正例 fixture で、consumer の期待集合と一致しなくなる (report の consumer 集合を test が厳密照合) → 正例 test が赤 |
| V5 | 選定を stock だけにする (S4 (b) の genome 調査を外す) | genome でだけ production target が変更 header を読む fixture が pass に変わる → 負例 test が赤 |
| V6 | 比較を選定 protocol の entry だけに絞る | genome option が他 protocol consumer の argv だけを変え、その下でだけ差が出る fixture が pass に変わる → 負例 test が赤 |
| V7 | 集約鍵から依存閉包の内容 digest を外す | 2 つの選定 configure で argv は同じだが生成 header の値が違い、後の configure でだけ差が出る fixture が pass に変わる → 負例 test が赤 |
| V8 | TRACE 実効値の確認を外す | argv の token は `-DTRACE=0` だが強制 include で TRACE を 1 にする entry と、`#if !TRACE` 内だけの変更の fixture が pass に変わる → 負例 test が赤 |
| V9 | 予定集合の最後の 1 件を実行しない | 正例 fixture が「予定と実行の不一致」で拒否に変わる → 正例 test が赤 |
| V10 | 完全展開の比較を外す | TRACE=0 側の値変更 fixture が pass に変わる → 負例 test が赤 |
| V11 | include 活性の比較を外す | 空 header の include を `#if TRACE` 内へ移す fixture (完全展開は不変) が pass に変わる → 負例 test が赤 |
| V12 | header 分岐の有効化を「4 引数のどれか 1 つ」に緩める | 一部指定の拒否 test が赤 |

- V2 は 2 層変異で kill 期待を事前登録する (DW-M04)。V3 は V2 の片側単独。
- 既存拒否 (A/D/R/C・mode・非 C/C++・.cc の include 規則・header 無効時の文言) は既存 test の維持で守り、変異にしない (相談 B)。
- 実 CCBench の H-line (設計審査 §6 #7) は §3 の判定 job の負例対照で行い、pytest 変異にしない。
- harness は `tools/mutation_harness.py` (DW-M05)。期待 node は実装後に login self-run か dispatch probe で集める (DW-M08)。

## 5. 見積り (2 node 時間の線)

判定 job: 生死確認の単価 (旧新対 54 秒) × 34 対 ≈ 31 分に、選定の genome 調査 (tictoc 24 + cicada 24 genome × 旧新 × 2 compiler の configure + 依存列挙、1 件 ≈ 2 秒で ≈ 6 分) と負例対照 (最初の不一致で止まる) を足し、2 起動並行なら wall ≈ 25〜40 分 ≈ 0.4〜0.7 node 時間。受入 2〜3 回 ≈ 0.5〜0.75、焦点走・変異 ≈ 0.3。合計 ≈ 1.2〜1.75 node 時間 (2 未満)。判定 job の再走が要る時点で合計を再計算し、2 以上ならユーザー確認。

## 6. 実装の分割

一枚岩 (検査器 1 file + 新 test file 1 本 + 判定 job script 1 本)。所有 path:
`tools/check_trace0_preprocess_identity.py`、`orchestrator/tests/test_check_trace0_header_rule.py` (新規)、`output/runs/t2854-hv2/judge/run_judge.sh` (gitignore 下)。
既存 test file (`test_check_trace0_preprocess_identity.py` ほか) は編集しない。test の追加所要は合計 60 秒以内 (login 相当) を目標、超えたら報告。
