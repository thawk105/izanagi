---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t139-r4-probe
seq: 1
title: [T-139] R4 環境 probe を実走し 3 測定を取得して追補 A を再発行した — 閾値は観測から作らず [0,1.0] のまま (コード + docs、受入 7570 passed / 20 skipped、変異 7/7 検出・SURVIVED 0、branch worktree-dev-wave-t139-r4-probe)
---

## 本文

- **裁定 R4 (a) が要求した 3 測定をすべて取得した。**gen_S の非 study probe
  (request `0:896504.nqsv`、node `bnode028`、633 秒、run commit `1fa2b75b`)。
  (i) 待機後の `/proc/stat` は **13 窓すべて `valid`、すべて `[0, 1.0]`、最大 `0.0791`
  core-equivalents** (上限の 7.9%)。窓長も全窓が `10.000 ± 0.100` 秒以内。判定 **`feasible`**。
  (ii) **`CCBENCH_TRACE=1` の build が通った** (`stock`)。witness ゼロの状態が解消した。
  (iii) **compiler の realpath・`--version`・bytes SHA-256 を取得した** (gcc/g++ とも 11.4.0)。
- **`a03` の許容範囲 `[0, 1.0]` は初版から 1 文字も変えていない。閾値を観測から作っていない。**
  「実測で確定」を「閾値の数値を実測に合わせる」と読まず、
  「事前登録した閾値が成立するかを実測で決着させる」と読んだ。
- **敵対検証が親の設計を 2 度倒した。これが本 wave の最大の収穫である。**
  段 1 の親案 `上限 = max(1.0, ceil_{0.1}(U) + 0.5)` は `U ≤ 3.5` の全域で `上限 ≥ U + 0.5` となり、
  **probe の全観測値が probe 自身の作った区間へ必ず入る**。段 4 で差し替えた梯子 `{1.0, 2.0}` も
  成功域 `U ≤ 2` で `T(U) ≥ U` となり**構造が同型**だった。とくに `U = 1.01` は `[0,1.0]` を
  **否定する**証拠であるのに、その観測自身が `[0,2.0]` への拡大を発火させ即座に受理される。
  「`2.0` = 他テナント 1 thread まで」という親の物理的説明も誤り (1 thread 100% の寄与は `1.0`)。
  いずれも凍結 core §14 の「実現値を必ず含む許容範囲」の禁止に該当する。
  最終形は「閾値を作らず `feasible` / `not_feasible` / `incomplete` の 3 値を返す」。
- **実測が既存の追補 A の誤りを 2 件確定させた。**
  `a04` の「その分は予備 2 本が吸収する」は**偽**である — core §9 の逐語は予備置換を
  「性能測定の**開始前**の infra failure」に限るが、`a04` は `a03` 不成立を**開始後**へ写している。
  当該文を削り、写像先を `判定不能` 一意に絞った (core の分類は増やしていない)。
  `a08` の「probe の `COMMON` との唯一の差は `-DCCBENCH_TRACE`」も**偽**である —
  計算ノードでも `command -v` = `/bin/gcc`、`realpath` = `/usr/bin/x86_64-linux-gnu-gcc-11` で
  両者は異なる文字列であり、exact argv validator は別 token として扱う。
- **`load1` を判定に使わない選択が実データで裏付けられた。** `post-03` は `load1 = 3.33` だが
  実測 busy は `0.0150` core-equivalents で 2 桁以上乖離する。
  `load1` に `[0,1.0]` を当てていれば正常な割当てが軒並み不成立になっていた。
- **敵対検証は 4 本すべて NO-GO だった** (段 3 の 2 レンズ = blocker 16 件、段 6 の 2 レビュー =
  blocker 17 件、焦点再レビュー = blocker 4 件 + high 1 件)。所見対応表では
  段 6 の 15 件中 8 件が `closed`、7 件が `partial` (限界を明記して scope 外へ)。
- **fix を 8 巡費やした。**うち 1 巡は親の prompt 不備で空振り (改善候補として記録)。
  1 件は 6 巡かけても閉じず、`DW-O16` の 3 巡上限を超えたため親が裁定して
  **到達不能な性質として限界を記録した** — driver が group-TERM を受けたとき受領証が
  段失敗コードとして記録することがある (bash が複合文中の pending trap を遅延させ、
  子の死が `wait` を正常復帰させる)。測定と中断検出には影響せず、
  `COMPLETED` marker による中断検出はテストで固定済みである。
- **probe を 2 回投入した。**attempt 1 (`896500`) は窓 **0 件**の `incomplete` で終わり、
  原因は環境ではなく**自作 validator の 1 行**だった — `compile_commands.json` に
  `arguments` 配列を要求したが、CMake の Makefile generator は `command` 文字列を出す。
  先例 `t139_positive_control_probe.sh:65` が既に両形式を扱っていた。
  **窓 0 件なので凍結した再走 gate (「窓を 1 つでも観測した attempt は terminal」) に該当せず、
  不都合な観測を捨てて選び直した事実はない。**両 attempt の成果物を repo へ残した。
- 変異は焦点再レビューが実効性を判定した 7 件だけを事前登録し、**7/7 検出・SURVIVED 0**。
  MISMATCH 2 件は生存ではなく**過剰検出** (期待 node に加えもう 1 件が同時に赤化) で、
  `DW-M03` に従い冗長 gate として記録した。取り下げた 6 件の理由も台帳に残した。
- **凍結していない。**承認は `package.md` の Q1〜Q5 でユーザーへ返す。段階 1 で終端。
  凍結 core の bytes は 1 byte も変えていない (`ac939af4…` を投入前後で照合)。
- **段 8 の改善候補 1 件は予算不足で本文へ入れられず、[T-664] へ寄せた。**
  `DW-S06-B` の「fix の prompt には既存テストの期待値を変更しないを明記する」は、
  **「既存」を tracked で切ると本 wave が中間 commit した自分のテストまで禁止対象に入る。**
  本 wave では倒れた設計 (梯子) を pin した期待値を直せず、fix 子が正しく fail-closed して
  1 巡空振りした。判定基準は「本 wave より前から存在する」で切り、対象外のファイル名を
  prompt へ列挙するのが最小修正である ([T-471] が独立 1 例目、本件が 2 例目で `DW-G03` の
  独立 2 例を満たす)。`docs/dev-wave/workers.md` は 4526/5000 bytes で単体には収まるが、
  **`docs/dev-wave/**` の合計が編集前 25199 / 上限 25200 bytes で実質満杯**であり、
  453 bytes の追記が合計上限を超えた。上限引き上げは提案せず、同じ壁を 4 wave 続けて
  踏んでいる [T-664] の材料として記録する (前回 [T-139] wave も同じ理由で見送っている)。
- **受入全走は land 対象 tip そのもので緑。** request `0:896546.nqsv`、node `bnode001`、1345 秒、
  **7570 passed / 20 skipped / rc=0**。測った checkout は `aaffa644` (main `34957a24` を
  投入直前に取り込んだ merge commit)。受入 lease は `acquired` を確認してから投入した
  (取得まで 2 巡・約 4 時間待った。その間 main を 6 回取り込み、うち 1 回は fold の
  `base-mismatch` を実際に踏んだ — 並行セッションが同じ [T-139] 項へ R1〜R7 の裁定を
  fold したためで、古い本文からの上書きを防ぐ機構が設計どおり働いた)。
  記録後検査は `check_docs.py` rc=0、`spool_fold.py --dry-run` が `planned`、
  provenance 監査 rc=0 (既知違反 7 件のみ)。
  **land 対象 tip でも再走して緑を確認した** (request `0:896547.nqsv`、node `bnode001`、
  1381 秒、**7570 passed / 20 skipped / rc=0**)。1 回目との差分は本 fragment 1 ファイルの
  docs 差分だけで、件数も一致した。**本行を書き足す最後の docs-only commit だけは
  全走に含まれていない** (自己参照になるため。先例と同じ扱い)。
- 一次資料 = `output/insights/2026-08-08_t139-r4-env-probe/`
  (`derivation-map.md` / `submission-receipt.md` / `addendum-a-reissue.md` / `package.md` /
  変異 spec と台帳)。実測成果物 = `output/env/pegasus/t139-r4-env-probe/` の 2 attempt。

## 次の一手差分

### 更新

- [T-139] **P1・ユーザー裁定待ち (再提出)**: R4 = (a) の環境 probe を gen_S で実走し、
  3 測定をすべて取得した — (i) 待機後の `/proc/stat` は 13 窓すべて `valid` かつ `[0,1.0]`、
  最大 `0.0791` core-equivalents (上限の 7.9%) で判定 `feasible`、
  (ii) `CCBENCH_TRACE=1` build 成立 (`stock`、witness ゼロを解消)、
  (iii) compiler の realpath・`--version`・bytes SHA-256 を取得。
  **`a03` の許容範囲 `[0,1.0]` は初版から不変で、閾値を観測から作っていない**
  (観測に合わせる 2 案はいずれも core §14 の恒真化に該当すると敵対検証が反証した)。
  実測が追補 A の誤り 2 件を確定させた — `a04` の「予備 2 本が吸収する」は core §9 に
  照らして偽、`a08` の「唯一の差は `-DCCBENCH_TRACE`」も偽 (compiler の渡し方が異なる)。
  追補 A を再発行済み。裁定するのは
  `output/insights/2026-08-08_t139-r4-env-probe/package.md` の Q1〜Q5。
  Q1 = 4 本 (追補 A 再発行版・判定写像・erratum・record-items) を一括承認して
  段階 2 へ進めるか。Q2 = 3 arm × `TRACE=1` witness を追加で取るか。
  Q3 = 単一割当ての記述的結果で締めるか。Q4/Q5 = 再走 gate と signal identity の限界の受容。
  凍結後の順序は「追補 A → producer 実装 → pilot」で変わらない。pilot 投入は依然不可。
  base: 1b403b69d977646bb64782823b14e492c690d077893f678151ca0004317167ad
