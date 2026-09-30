# 段 4 裁定 — md_32 cicada-promotion-uaf-fix (2026-09-30 12:2x JST、親)

入力: s1-brief.md、out/s2-plan.md (Codex plan)、out/s3-consult-A.md (正しさ境界、sol)、out/s3-consult-B.md (実効性・過剰・削除、luna)。
段 4 直前の裁定 inbox 再走査: /work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-30-rulings-full40-verdicts.md (第 40 回、D2305) の項 6「CCBench 修正 3 branch は land 後に push 依頼、Cicada 2 本は別々に push、束ねた pin tip は AI が作り改めて依頼」と項 10「pin に入り GitHub CI 緑の修正から 1 修正 1 PR」が本 wave に掛かる。他の新着なし。

## 所見の裁定

| # | 所見 | 裁定 | 扱い |
|---|---|---|---|
| A1 | (P1) は具体的な版鎖 (rts=10・wts=30、`L(15,aborted)→V(5)` を読んだ後に `B(25,committed)` が入り、再検査が L から下りて通る) で成立する。前 wave 相談 A の「穴なし」は誤り | real・採用 | 単位 D で witness に帰属してから修理 (R1) |
| A1' | 成立条件は「`later_ver_` が aborted (pending→aborted) で、その手前に wts 未満の確定版が入る」。REUSE_VERSION の再利用は必要条件でない | real・採用 | 診断は pointer の状態と飛ばした確定版を分けて記録 |
| A2 | promotion 後の本来の `update()` が `searchWriteSet` 素通りで body を捨てる (値の欠落、版の trace と巡回 0 では見えない) | real・採用 (must-fix) | 修理 F2 (R2)。成果物影響: promotion genome の TPC-C・YCSB が依頼と違う値を書き、比較の作業量・結果が変わる |
| A3 | UAF の順序修正は報告済み UAF を消すが、索引から外す前に tuple pointer を得た並行読み手の寿命は解決しない | real・scope 外 | 既存の寿命問題 (stock にもある、正常 delete は gc_records で遅延解放) として一次資料と新 item に書く。遅延解放は epoch 相当の設計で本 wave の最小修理を超える (DW-G05) |
| A4 | OPT=0 では INSERT の別確保版は tuple 解放で解放されず未回収のまま (既存)。INSERT を writeSetClean で飛ばす案は status を pending に残すので不可 | real・採用 | P3 の順序案を採り、4 組合せの結果 (UAF の消失と既存の未回収) を分けて記録 |
| A5 | 小走行の巡回 0・ASan 0 件・完走は観測範囲の結果で、証明ではない | real・採用 | 記録の言い方 (上限 indeterminate、完走率、ASan の対象組合せ) |
| A6 | 壊しの帰属は witness の辺と発火 event の照合まで要る。値を狙う壊しは判定器の正例にならない | real・採用 | R8 |
| A7 | `#error` を外した trace は診断変種で W 行は promotion 由来か区別しない | real・採用 | 記録で限定 |
| A8 | early abort の `Status::OK` は呼出し側が status_ を見るので直ちに巡回原因ではない | real (原因候補から外す)・計数は作らない | B の過剰所見と合わせ D から外す |
| B1 | 読み取り専用 promotion の抑止では TPC-C (読み取り専用指定なし) は閉じない | real・採用 | TPC-C は独立に帰属 (単位 D の T 系) し、原因の修理を F の完了条件に入れる |
| B2 | 前 wave の script は F/G 直子・固定 build 群を要求し、そのまま流用できない | real・採用 | 部品流用 (CMake 設定・macro 束縛・判定器呼出し・CI 命令) で今回用の job 本体を Codex が新規に書く |
| B3 | 見積り 0.64 node 時間は条件の数え直しが要る | real・採用 | 単位 D・X の報告に variant×cell×反復の表と見積りを必須にする。親が合算して 2 node 時間未満を確かめてから投入 |
| B4 | D297 は「拒否 rc + 非 cicada path 差分 0」では取り直しにならない | real・採用 | R5 |
| B5 | merge 土台を push の一本化決定と扱わない | real・採用 | R4 |
| B6 | ledger 指定との相違は理由を書く | real・採用 | ledger.json に登録しない (entries 1 件固定の現行契約、先例 patches/README の cicada 節)。一次資料と README に明記 |
| B7 | 単位 D の全候補計数は過剰。最初は witness・再検査起点差・TPC-C の最初の失敗点 | real・採用 | R6 |
| B8 | 診断の修理前再現を確認の対照に再使用、CI は最終 tip で 1 回 | 採用 (nit) | R7 |

## 決定

- **R1 (巡回の修理、事前登録):** 単位 D の観測で「判定器の巡回 witness の tx が、読み取り専用で読み promotion で読み書きに転換し、再検査で `later_ver_` 起点と最新版起点の結果が食い違ったまま commit した tx を含む」ことを示せたら、修理 F1 = **`is_ronly_` の tx では promotion しない** (inlineVersionPromotion の条件に `!is_ronly_` を足す、transaction.hh:200-214 の `#if INLINE_VERSION_PROMOTION` 内)。理由: 原論文 §3.1 は読み取り専用 tx を rts の snapshot で読み読み取り集合を検証しないと定め、§3.3 の promotion は「可視版として読んだ版の読みを RMW へ格上げ」で、rts で読む tx の格上げは書いていない。読み書き tx の promotion は `later_ver_` が wts 基準なので (P1) の穴に当たらない。代案 F1b (転換前の読みだけ最新版から再検査) は変更と証明範囲が広いので、F1 で巡回が消えない場合に限り段 4 追補で選ぶ。帰属が示せなければ修理せず追補で再裁定する。
- **R2 (値の欠落の修理):** 修理 F2 = promotion が積んだ書き込み要素に限り、同じ tx の後続 `update()` が body をその要素の新版へ移す (promotion 由来の目印は `#if INLINE_VERSION_OPT && INLINE_VERSION_PROMOTION` の内側だけに置き、既定 genome の前処理出力を変えない)。promotion 以外の既存 write への二重 update の扱い (stock の素通り) は変えない。確認は発火計数 (使い捨て計器、修理前 > 0・修理後に置換が発火) と TPC-C の完走。巡回の修理と別 commit。
- **R3 (UAF の修理):** 修理 F3 = abort で INSERT の tuple を退避して索引から外し、writeSetClean の後に delete する (transaction.cc:745-754、writeSetClean は変えない)。既定 genome の abort 本文が変わるので、既定文脈の前処理出力は「意図した差分」として範囲を記録する。並行読み手の寿命 (A3) と OPT=0 の未回収 (A4) は残る既存問題として記録し新 item にする。別 commit。
- **R4 (土台):** 新 local branch `izanagi-cicada-promotion-uaf-fix` を、G `eb93423b` と gc 修理 tip `81fc4a84` の merge commit (親が作る。衝突したら停止して追補) から切る。これは本 wave の **local 検証土台** で、第 40 回項 6 の「束ねた pin tip」ではない。既存 2 branch は動かさない。修理は F1・F2・F3 を 1 修理 1 commit (項 10 の 1 修正 1 PR に合わせる) にする。
- **R5 (D297):** 検査器を新 tip で 1 回走らせて cicada による拒否の rc と stderr を記録し (pass と呼ばない)、加えて **新 tip の `cc/cicada/` だけを pin C の bytes に戻した probe tree** で C→probe を判定し、非 cicada TU の同一性を新 tip の bytes で取り直す。cicada の TU は意図した差分として範囲 (変更 file と、既定文脈の前処理比較の結果) を書く。検査器・受理条件は変えない。
- **R6 (単位 D の範囲):** YCSB 系 = (i) 再検査起点差の計数と event (判定は変えない)、(ii) promotion の試行・成功を読み取り専用/読み書き別に計数、(iii) event の tx wts を trace の C 行で txid に写し判定器 witness の tx と照合、(iv) 一要因対照として「読み取り専用 promotion だけ無効」の使い捨て版。TPC-C 系 = (v) Debug build の gdb catch throw による送出点 backtrace (gdb が無ければ記録して ASan へ)、(vi) ASan build (Debug・ENABLE_SANITIZER=ON・detect_leaks=0) の最初の報告、(vii) 一要因対照 (UAF 順序修正のみ / 後続 update の素通り回避のみ / 読み取り専用 promotion 無効のみ) を土台と交互。(viii) 後続 update の素通りの計数。early abort・版の回収再利用の計数は作らない (必要なら追補)。
- **R7 (確認・CI):** 単位 X が修理後 tip で: 8 genome build (修理前は 8 genome の build 済みを前 wave の G で確認済み、merge 土台の build は代表 1 genome で足りる)、YCSB K・W・R・P × thread 4 と TPC-C M・R2 × thread 4 の判定 (修理前の対照は単位 D の同 SHA・同設定の走行を再使用し、同じ job に土台の代表 genome を交互に 1 回ずつ置く)、TPC-C M・R2 の反復 (修理後 各 3 回)、ASan M × thread 4 (修理前後 各 2 回)、上流 CI (format・CI image の全 protocol build) を最終 tip で 1 回、D297 (R5)、計装 patch 2 本の新 tip への `git apply --check` (fuzz なし)。
- **R8 (正例):** `patches/broken-cicada-promotion-ronly-stale-recheck.patch` (R1 が F1 のとき) = 修理後 tip → instr-cicada-trace → (promotion 診断変種の `#error` 除去は repo 外) → 壊し の順の無条件 patch。F1 の条件を外して読み取り専用 promotion を戻し、再検査起点差で通った commit tx を `CICADA_BREAK_EVENT slug=promotion-ronly-stale-recheck tx_wts= key= a_wts= b_wts=` に出し、終了時 `CICADA_BREAK_FIRED slug= reached= changed= committed=`。判定器の witness の tx・key と event を照合し、巡回の辺に壊した経路が入ることを確かめる。R1 が別の修理になったら壊しも追補で差し替える。名前は `IZANAGI_` を含む条件 macro を持たない。
- **R9 (記録):** 巡回 0 は「観測した cell で巡回 0、上限 indeterminate」、完走は反復数、ASan は対象 genome と組合せを添える。性能値は取らない (規律 1)。ledger.json に登録しない理由を書く。push・pin 前進・束ねた pin tip は人間 / 別 wave。

## 変異の事前登録 (DW-M01)

izanagi の pytest が消費する実装面の変更はない (repo 内の実装面は壊し patch 1 本、CCBench は submodule の branch で gitlink 不変)。変異は判定器・ASan を検出器とする走行で登録する。

| ID | 変異 | 期待 | 単一理由性の根拠 |
|---|---|---|---|
| M1 | 修理後 tip + 壊し patch (R8) | 判定器 non-serializable、witness の tx が壊し event の commit tx を含む (KILLED) | 壊しは F1 の条件 1 か所だけを外す。他の integrity 数値項目 0 を併せて確かめる |
| M2 | 修理後 tip から F3 だけを戻した使い捨て版 (= abort の順序を元に戻す) | ASan の `heap-use-after-free` が abort/writeSetClean の frame で出る (KILLED) | F3 以外は同一。修理前土台の ASan と同じ frame で照合 |
| M3 | 修理後 tip から F2 だけを戻した使い捨て版 | 素通りの計数 > 0 (diagnostic sensitivity pin、kill に数えない) | 判定器は値を見ないので kill の検出器が無い |

変異走行は単位 X の確認 job に同梱し、初回の結果は消さず記録する。
