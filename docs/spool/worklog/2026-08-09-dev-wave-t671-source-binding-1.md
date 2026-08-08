---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t671-source-binding
seq: 1
title: 汎用 certified producer の source binding ([T-671] + t530 件 6) の設計択一を裁定へ返した — 実装はしていない (docs のみ、実装差分なし、受入 7505 passed / 20 skipped、変異は免除、branch worktree-dev-wave-t671-source-binding)
---

## 本文

- **ユーザー裁定 (2026-08-09 rulings2 件 1、一次控え
  `dev-wave-jobs/rulings-inbox/2026-08-09-rulings2-session-6rulings.md`) に基づく設計 wave。**
  「[T-671] = 設計 wave 起票を承認。t530 wave の裁定パッケージ件 6 (campaign id 分裂、[T-657] 直結)
  と束ねてよい」。**本番コードの編集はユーザー指示により禁止**されていた。実装差分ゼロで終端し、
  段 5・6 を飛ばして `4→7→8→9` を通った (`DW-S04` の「実装しない」裁定)。変異 matrix は同条項で免除。
  裁定パッケージと逐語は `output/insights/2026-08-09_t671-source-binding/`。
- **段 3 の敵対 2 レンズはいずれも NO-GO** (レンズ A = sol / must-fix 11・nit 1、
  レンズ B = luna / must-fix 7・nit 3)。両者が独立に一致した中核は 2 点。
  (i) 段 2 プランが束縛対象を loader 2 module へ縮約する根拠がない — silo も qualification も
  それより広い閉包を束縛しており、実際に契約を**強制する** `execution_guard` / `loop` / `pipeline` /
  `wal` が dirty でも「clean な commit 由来」を名乗れる。(ii) 提案されたどの gate も、現在の
  production artifact では**正に発火させられない** (`DW-G04`)。
- **親が自分の誤りを 2 件訂正した。** (i) 段 1 brief P1 は「silo と qualification という独立 2 実装が
  あるから `DW-G03` を満たす」と書いたが、`DW-G03` が要求するのは**同型欠陥が異なる
  producer/consumer で 2 件再現すること**であって、既に binding を持つ実装が 2 つあることではない。
  束縛閉包の選択は独立の択一 (R1) へ格上げした。(ii) 実測 B の「分裂には未完了 campaign が要る」は
  誤り。t530 は旧 root を探す前に current 契約で id を確定するため、terminal な campaign でも
  同じ論理入力を再実行すれば新 root ができる。**成果物の形として「分裂」と「断絶」は区別できない。**
- **親の provisional 裁定 P2 を段 2 が反証し、親が撤回した。** 「lock の契約 hash を
  `resolve_by_contract_sha256` の ever-active 解決で引き継げば旧世代 resume できる」は成立しない。
  同関数は**履歴検証専用**で、`env_contract.authorize()` と
  `execution_guard._contract_from_authorization` は terminal state の active row しか受理しない。
  旧世代での新規計測を許すことは**受理集合の拡大**であり、親が黙って選べる範囲を超える
  (パッケージ R2 の選択肢 (c) として明示的にユーザーへ返した)。
- **穴は g2 固有ではなく、現在の g1 でも成立していると訂正した。** 起票文は「第 2 世代の活性化後は
  検出できない」と書くが、実測では既存 campaign
  (`p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5`) の lock・WAL・layer3_report も
  loader authority を持たない。**g2 活性化は発覚の契機であって発生条件ではない。**
  したがって「活性化前に閉じる必要はない」は「いつ閉じてもよい」を意味しない。
- **書込み前停止は `run_campaign` の内部だけでは達成できない**ことを親が再現した。
  `p3_s4_loop.py:878` が `layout.ensure()` → `ensure_resumable_attempts()` を実行してから
  `run_campaign` を呼ぶ。実現層の選択を択一 (R6) にした。
- **D125 決定 (2) の実装が実在することを親が独立に確認した。**
  `p3_s4_loop_trigger_gating.py:92` の `_CAMPAIGN_ENV_KEY = "measurement_env"`。したがって
  段 2 プランの「identity と authority の分離は D13 の env 非 identity 規則を回復する」は**不正確**で、
  `measurement_env` が残る限り env は依然 campaign id を分ける。この扱いは t530 件 5
  (D125 決定 (2) の supersession 表記) と同じ面を持つため、同時裁定を推奨する形で R4 にした。
- **docs 予算の残りは 1 byte だった** (実測: core 8,655 / workers 4,526 / mutation 3,689 /
  operations 8,329 = aggregate 25,199 / cap 25,200)。前 wave (エントリ 319) 時点の 16 bytes から
  さらに縮んでいる。`docs/dev-wave/**` へ規範文を足す実装は [T-664] の予算捻出が前提である。
- **レンズ 2 件は t530 パッケージの既出項目と同一面と裁定し、二重起票しなかった。**
  raw reader / freeze / offline report の迂回は t530 件 2、S8b private lock は t530 件 3。
  したがって R1〜R8 を全部実装しても「proof chain が全経路で完結した」とは名乗れない。
- **受入要否の判定証拠 ([T-648] fallback 義務)**: 本 wave は docs-only・実装差分ゼロだが、
  **実 repo を読むテストは存在する**。判定証拠 = `orchestrator/tests/test_check_docs.py` と
  `orchestrator/tests/test_spool_fold.py` (いずれも実 checkout の `docs/` と `docs/spool/` を読む)、
  および D88 の literal placeholder gate (対象族に `output/insights/*.md` を含み、本 wave が
  追加した package・逐語 8 ファイルを走査する)。したがって受入全走を実施した。
  **7505 passed / 20 skipped、rc=0** (land 対象の tip `80549392`、request `896545`、1273 秒)。
  この受入値を記録する commit 自体は、その走行の対象に含まれない (値を書く前に測る順序のため)。
- **受入 lease を約 4 時間取得できなかった。** 120 秒周期の待ち手が 2 度 (各 2 時間) 空振りし、
  45 秒周期へ詰めて取得した。その間 holder は 5 回交替し、local main は 7 回進んだ
  (`ee2da0bf` → `00eb029a`)。**これは [T-648] wave (エントリ 333) が同日に実測した
  「lease に fairness が無く、待ち周期が短い側が有利」という観測の独立 2 例目**である。
  待ちの間に main を 4 回取り込み、そのつど検査を通した。
- **rulings の fold が `[T-671]` の項目本文を書き換えたため、fragment の base digest を
  取り直した。** 取り直さずに land していれば、rulings が入れた「裁定済み → 設計 wave 起票可」の
  記述を古い本文で上書きするところだった。**base digest 検査が設計どおり止めた**実例である。
- **[T-664] の結論を受けて前提条件を訂正した。** パッケージは当初「実装は [T-664] の予算捻出が
  前提」と書いたが、[T-664] が「依頼された 2 経路 (陳腐化ルール削除・テスト化) では予算が
  空かない」と確定させた (main で実体確認)。**前提は [T-664] ではなく [T-313] の実装**であり、
  規範文を必要としない形を選べればこの前提自体が外れる、と書き換えた。
- **段 8 の改善候補は 2 件で、どちらも独立 2 例目が揃った。** (i) 受入 lease の fairness 欠如 —
  新規起票した (下記)。(ii) `DW-O01` の実行雛形を worktree 隔離セッションで inline 実行すると
  harness の隔離 guard が拒否し、wave 専用 subdirectory の `.sh` へ書くと通る (エントリ 319 が
  1 例目、本 wave が 2 例目で 2 回発火)。**(ii) は本文編集を見送る** — `docs/dev-wave/**` の
  aggregate 残は 1 byte で、[T-664] が「依頼された 2 経路では空かない」と確定させたため、
  [T-577] の既定どおり見送りで確定し、**再訪条件を [T-313] の実装に紐づける**。
- **失敗台帳 fragment は書いていない。** 本 wave は実装ゼロで、恒久対応が宣言だけの恒真な
  ものにしかならないため (`docs/spool/failures/README.md` は実体へのポインタを要求する)。
  機構が入る実装 wave で起票する。

## 次の一手差分

### 更新

- [T-671] **P2・ユーザー裁定待ち**: 汎用 certified producer の source binding。設計択一を
  `output/insights/2026-08-09_t671-source-binding/package.md` の R1〜R8 として返した。
  R1 (束縛閉包) と R7 (発火計測を先に作るか) が中核。t530 件 6 (campaign id 分裂) を R2・R4・R5 として
  束ねた。実装の前提条件は [T-664] (docs 予算)、および t530 の land 保留。
  起票文の「第 2 世代の活性化後は検出できない」は実測により訂正 — 同じ穴は現行 g1 でも成立する。
  base: c493a4e594ccd2250469715d0b51c0834b17f57686b28669ea40b1b3ca95af09

### 新規

- {{T:caller-inventory-any-tautology}} **P3・新規**: certified writer の caller 閉集合検査が
  部分的に恒真である。`orchestrator/tests/test_campaign.py:2513` の `direct_sinks` 側は
  `assert any(... for call in calls)` (:2553) なので、`authorization_contract` keyword を持つ
  呼出しが同ファイルに 1 本あれば他の呼出しは keyword なしでも通る (`expected_run_calls` 側は
  `all(...)` で正しい)。また `expected_run_calls` は固定 dict + `ast.Name` 照合のため、
  新規ファイル・alias・attribute 呼出しを検出しない。成果物影響 = 新規または別形態の writer が
  authority なしの COMMIT を書いても閉集合検査は緑のまま。[T-671] の段 3 レンズ A-04 が発見し、
  親が再現した。既存 gate の弱点であり [T-671] の所有ではない。
- {{T:acceptance-lease-fairness}} **P2・新規**: 受入 lease に fairness が無く、待ち周期が短い側が
  有利になる (`tools/wave_land_window.py` は FIFO の待ち行列を持たず、release 直後の claim 競争で
  決まる)。**独立 2 例が揃った** — [T-648] wave が 2 時間 15 分 (holder 5 回交替、60 秒周期が
  90 分空振り)、[T-671] wave が約 4 時間 (holder 5 回交替、120 秒周期の待ち手が 2 度空振り、
  45 秒周期へ詰めて取得)。いずれも同日 2026-08-09、別 wave・別 holder 列。成果物影響 = 受入結果
  そのものは変わらないが、待つ側が local main を都度取り込み直すため wave の実時間が延び、
  取り込み回数ぶん検査と base digest の再基準化が増える (本 wave は main 取り込み 4 回、
  digest 再基準化 1 回)。実装は `tools/` の変更であり Codex author を要するため、
  本 wave (docs-only・本番コード編集禁止) では行わない。
