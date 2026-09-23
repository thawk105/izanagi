# sort-nonswo (V07) を gate と同じ供給経路で build し、stock 対照つきで計算ノード実走した ([T-2847] 残り (2) の 1 行、2026-09-23)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
wave `dev-wave-t2847-sort-nonswo` (branch `worktree-dev-wave-t2847-sort-nonswo`)、起点 local main `620a6bb13` (開始 gate rc 0、2026-09-23 20:47 JST)、CCBench submodule `e9e477ca`。
job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/` (brief・Codex の prompt / 出力・起動器・job の出力全文)。
段 1〜6 の全文は `verbatim/` (brief と事前登録の草案 `s1-*`、段 3 相談 1 本、段 4 裁定と確定した事前登録表 `s4-prereg.md`、段 5 author、段 6 review・fix 2 巡・焦点再レビュー・終結、起動器の逐語 `launcher-source.md`)。本書の read-only review 1 本 (`verbatim/s6-review-insight.md`) は NO-GO (must-fix 1・should 2・nit 1、数値と分類の独立照合は全一致) で、must-fix と should 2 件を採用して直した (nit は供給経路の説明に要るので残した)。生の出力は `raw/`。

期待の出所は `output/insights/2026-09-22/t2847-verifier-detection-design/README.md` (以下「設計書」) §4.3 の V07 行。前回の実走 `output/insights/2026-09-23/t2847-patch-verify/README.md` (以下「前回」) §3.3 で V07 だけが未実走 (「その他」) だった。

## 1. 依頼と結論

依頼 (ユーザー直接起動の `/dev-wave [T-2847]`): 残り (2) のうち sort-nonswo (V07) の 1 行だけを計算ノードで実走する。前回の repo 外起動器の方式で、build の供給経路を condition gate と一致させる。設計書 §4 の発生条件へ届く最小 workload と期待 (層と verdict) を投入前に表で固定し、同じ job に stock 対照を置き、4 分類で記録する。期待と違っても patch・workload を事後に寄せない。

結論:

1. **V07 の本行 (R4: 壊し build・17 要素) は「別の層で検出 (process の異常終了)」だった。** 主予測の hang (120 s の timeout) は起きず、process は開始から 0.013 s で SIGSEGV (rc −11) で終わった。verifier の判定で捕まえたのではなく、process が落ちたことで止まった。分類は投入前に固定した規則 (§3) を起動器が機械的に当てた値で、観測後に選んでいない。
2. **16 要素 (R3) では壊し build も完走して S (certified) だった** (write set 16 要素の取引が 25,862 件 commit、P 0)。設計書と D42 の記録「write set 16 要素以上で hang」は今回の build では再現せず、libstdc++ 11 の source 読み (要素数が 16 を**超える**ときだけ範囲検査の無い分割に入る) と合った。
3. **stock 対照 2 本 (R1・R2) は期待どおり** S (certified)・違反 0 で、write set の最大はそれぞれ 16・17。W(17) が 17 要素の write set を commit まで作れることを同じ job で示した。
4. **供給経路は gate と一致した。** gate (`SORT_VARIANT`、CMake cache 経路) は sort-nonswo patch を当てた木で admitted、実 build も `-DCCBENCH_SORT_VARIANT=<v>` で行い、`CMakeCache.txt` と `ycsb_silo.exe` の実コンパイル定義 (`-DSORT_VARIANT=1` / `=0`) を build ごとに照合した。前回の「driver の build 経路と gate の供給経路が一致しない」(前回 §1 の 2) はこの経路で解消した。
5. 計算ノードの使用は 1 job・Elapse 88 s (約 0.024 node 時間)。

## 2. 何をどう走らせたか

### 2.1 起動器

起動器 `launch_sort_nonswo.py` (Codex author が書き、段 6 review の所見で fix を 2 巡。投入版 sha256 `1e30c8c3…`、逐語は `verbatim/launcher-source.md`)。前回の起動器 (`launch_patch_verify.py`) の方式をそのまま使う: 依存物 (gflags・glog の使い捨て install、masstree・mimalloc・googletest の source) を `CMAKE_TOOLCHAIN_FILE` と `CMAKE_PREFIX_PATH` で渡し、compiler は policy が選ぶ g++-11、出力は job dir。driver module の名前の差し替えは `buildcache.DEFAULT_CC` / `DEFAULT_CXX` と verifier 呼び出しの受動記録だけ (`raw/meta.json` の `replaced_names`)。

新しく書いた部分:

- `s5_permutation_coverage.applied` (patchharness の `git apply`、fuzz なし) で `patches/broken-silo-sort-nonswo.patch` を当てた 1 つの文脈の中で、gate を `s5._require_condition_gate(sub, "SORT_VARIANT")` (request 値 1・既定 0) で評価し、壊し (v=1) と stock (v=0) の 2 build を作る。
- build の cmake argv は `s5._build_broken` と同じで、`-DCMAKE_CXX_FLAGS=-D<macro>=1` だけを `-DCCBENCH_SORT_VARIANT=<v>` に置き換えた。stock は同じ patch 適用木の v=0 (patch の `#else` 枝 = 素の `sort`)。
- run は `s5._run_trace` と同じ作り方だが、rc≠0・timeout で例外にせず rc・経過秒を記録する。trace の C 行の `write_count` の最大と度数分布を数え、timeout でない run だけ verifier を `s5._verify` と同じ argv で 1 回呼ぶ。
- 分類: 確定した事前登録表 (`verbatim/s4-prereg.md`) の段 A〜D を関数に写し、run ごとの分類を `result.json` に書く。

patch・condition gate・verifier・s5 の関数本体は差し替えていない。tracked の CCBench・verifier・gate の登録表・`patches/` は編集していない (並走 wave `dev-wave-t2847-mutation-run` の編集面)。

### 2.2 build の記録 (`raw/result.json` の `builds`)

| build | `CMakeCache.txt` | 実コンパイル定義 (抜粋) | CXX_FLAGS | binary sha256 |
|---|---|---|---|---|
| 壊し (v1) | `CCBENCH_SORT_VARIANT:STRING=1` | `-DSORT_VARIANT=1 -DTRACE=1 -DBACK_OFF=1 …` | `-O3 -DNDEBUG -Wall -Wextra -Werror -std=c++20` | `075a5f91…` |
| stock (v0) | `CCBENCH_SORT_VARIANT:STRING=0` | `-DSORT_VARIANT=0 -DTRACE=1 -DBACK_OFF=1 …` | 同上 | `fc0e1fc9…` |

compiler は `x86_64-linux-gnu-g++-11` (Ubuntu 11.4.0-1ubuntu1~22.04.3)。gate の admission は `admitted: true`・`use_class: raw-measurement`。

### 2.3 job

| request | Elapse | 実行ノード | 起動器の rc | 条件 |
|---|---|---|---|---|
| `21250.nqsv` (gen_S) | 88 s | bnode017 | 0 (4 run とも実行・分類済み) | W(n) = 1 thread・200 tuple・zipf 0・rratio 0・rmw・max_ope n・1 s。run の timeout 120 s |

生の行は `raw/dispatch-elapse.txt`、hostname・時刻・compiler・差し替えは `raw/meta.json`。

## 3. 事前登録と観測

事前登録表は段 3 の相談 (`verbatim/s3-consult.md`、所見 9 件を全採用) で草案を改め、段 4 で確定した (`verbatim/s4-prereg.md`)。投入前後を結ぶ記録: job dir の `prereg.md` の最終更新 (mtime) は 2026-09-23 21:03:39 JST で、投入 (`runs/sn-1.log` の start 行、21:36:31 JST) より前。記録時点の sha256 は `4c8cd1f92482081ce07369ad5947ef3d817664ed7a4399977b64574d6542dd0a` で、`verbatim/s4-prereg.md` と一致する。表の冒頭の「21:05 JST」は親が書いた概算時刻で、確定時刻の正は mtime である。

### 3.1 事前登録した期待

| run | build | workload | 期待 | 根拠 |
|---|---|---|---|---|
| R1 | stock | W(16) | 完走・S・違反 0・write_count 最大 = 16 | R3 の対照 |
| R2 | stock | W(17) | 同上、最大 = 17 | R4 の対照、W(17) が 17 要素に届くことの証拠 |
| R3 | 壊し | W(16) | 完走・S・P 0・最大 = 16 | libstdc++ 11 は要素数 ≤ 16 で guarded な insertion sort。設計書・D42 の記録 (16 以上で hang) とは逆の予測。V07 の分類の必須条件ではない追加検証 |
| R4 | 壊し | W(17) | 17 要素で `__unguarded_partition` の範囲外走査 = 未定義動作。主予測は hang (timeout、verdict 無し)。他の観測も分類を先に固定 | D42 の release / ASan の実機記録と source の読み |

分類規則は「基盤の失敗 → 対照 → 本行」の順に最初に当たった規則を採る。R4 は timeout → 期待どおり (hang)、signal 終了 → 別の層で検出 (process の異常終了)、rc>0 → その他、verifier の失敗・空履歴 → その他、I / N → 別の層で検出 (verifier)、S かつ最大 ≥ 17 → 未発生、S かつ最大 < 17 → その他 (条件未到達)。全文は `verbatim/s4-prereg.md`。

### 3.2 観測

数値は `raw/result.json` (verifier の生出力は `raw/verifier/`)。integrity の 11 項目 (orphan read・version dup・txid の重複と欠番・genesis への commit・版の不一致・key の書式・frame の破れ・X・write intent・P) は R1〜R3 ですべて 0。

| run | rc | 経過 | C 行 (commit した取引) | write_count 最大 (度数) | verifier | 分類 (起動器) |
|---|---|---|---|---|---|---|
| R1 | 0 | 1.01 s | 50,228 | 16 (27,054) | S (certified)、巡回 0・X 0・P 0 | 期待どおり (対照) |
| R2 | 0 | 1.00 s | 45,810 | 17 (22,868) | S (certified)、巡回 0・X 0・P 0 | 期待どおり (対照) |
| R3 | 0 | 1.00 s | 47,801 | 16 (25,862) | S (certified)、巡回 0・X 0・P 0 | 期待どおり (16 要素では S) |
| R4 | **−11 (SIGSEGV)** | 0.013 s | 0 | — | (I、`stats.txns` 0、rc 3。分類には使わない。下記) | **別の層で検出 (process の異常終了)** |

- R4 の verifier: 事前登録では verifier を省くのは timeout の run だけなので、R4 の空の trace にも verifier が 1 回走り indeterminate (rc 3) を返した。分類は規則の順で先に当たる「signal による終了」で決まり、この I は分類に使っていない。
- R4 の stderr は空。
- write set の度数分布は R1〜R3 とも 11〜16 (R2 は 12〜17) で、W(n) の取引の約半分が n 要素に届いた。

### 3.3 4 分類

分類の単位は run。V07 の本行は R4。

| 分類 | run | 内訳 |
|---|---|---|
| 期待どおり | R1・R2 (対照)、R3 | 対照 2 本は S。R3 は 16 要素の壊し build で S (境界の下) |
| 別の層で検出 | R4 | process の異常終了 (SIGSEGV)。主予測の hang ではない |
| 未発生 | — | |
| その他 / 誤検出 | — | 対照の誤検出 0 |

前回 §3.3 の V07 行 (「その他 (未実走)」) は、この実走で「別の層で検出 (process の異常終了)」になる。

## 4. 解釈と限界・言わないこと

- **各行は 1 回の走の観測である。** R4 の SIGSEGV は未定義動作の 1 つの現れで、同じ binary を何度走らせても同じになるとは言えない。
- **R4 がなぜ hang でなく SIGSEGV になったかは確かめていない。** 候補は、比較がアドレスの比較だけで副作用を持たないため GCC (`-O3`) が範囲外走査のループを終わるものと仮定して変形し、その後の要素の入れ替えが範囲外の address に書いた、というものだが、disassembly も core も見ていない未検証の仮説である。D42 の記録 (2026-07、release / ASan で hang) と今回 (g++ 11.4.0・`-O3`・pin `e9e477ca`・Pegasus) は compiler・pin・機体・build が違うので、hang と SIGSEGV の差をどれか 1 つに帰属させない。
- **R4 の C 行 0 は「commit した取引が 0 件」の証明ではない。** trace は process 内で buffer されるので、SIGSEGV で書き出されなかった可能性がある。どの取引で落ちたかは不明である。
- **R3 は「16 要素では壊れない」の証明ではない。** 比較関数の反対称性の破れは要素数に関わらず C++ の契約違反 (未定義動作) で、今回の build と libstdc++ 11 の実装で 16 要素の insertion sort が要素を保ったことだけを示す。permutation 保存検査 (P) も 0 だった。
- **V07 は設計書で「盲点」の行である。** verifier の判定は今回も V07 を捕まえていない (R3 は S。R4 は空の trace に I (`stats.txns` 0) が出たが、事前登録の順で signal 終了が先に当たるので分類に使わず、V07 の検出力にも数えない)。「別の層で検出」は process の異常終了で止まったという意味で、verifier の検出力に数えない。論文で「sort の反対称性の破れは検出される」と書かない。
- gate の通過は「供給経路が効く」ことの証拠で、sort-nonswo の挙動の証拠には数えていない。gate の登録 patch は `silo-sort-variant.patch` で、sort-nonswo の木で gate を評価したのは同じ 2 file (transaction.cc・Options.cmake) を変える別 patch の上である。
- 実走は pin `e9e477ca` で行った。記録の直前に local main の pin が `68106660` へ進んだ ([T-2858]、mocc の X/P 計装)。2 つの pin の差は `cc/mocc/transaction.cc` の追加 64 行だけで、silo の source は同じ (`git diff --stat e9e477ca 68106660`)。新 pin で走らせ直してはいない。
- 性能値は取っていない。job の Elapse は計算資源の記録。
- raw trace は起動器が走の後に消すので残っていない。残っているのは trace の C 行統計・verifier の出力全文・build 記録。
- repo に入れたのは本書と `raw/`・`verbatim/` の記録だけで、実装面の差分はゼロ。起動器は repo 外に置き、逐語を `verbatim/launcher-source.md` に残した。
