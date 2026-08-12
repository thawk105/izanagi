---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-testops-observation
seq: 1
title: TestOps 導入依頼は既存の task-run 台帳が契約どおり凍結された状態だと判明し実装しない裁定にした — 第 3 束裁定で Q1〜Q3 が確定し D316 が停止理由の赤を解消したので再開して land した (docs のみ、実装差分ゼロ、branch worktree-dev-wave-testops-observation)
---

## 本文

**ユーザー裁定 (wave 冒頭).** 依頼「TestOps をこのリポジトリに導入してください」の TestOps が
リポジトリ内で未定義だったため、段 1 前に scope を諮った。選択肢は (A) 自前のテスト運用観測層 /
(B) 外部 TestOps 製品 (Allure・Katalon 等) / (C) テスト選択・影響解析 / (D) 別の具体。
**ユーザーは (A) を選択**。(B)(C) は scope 外として扱った。

**実測で前提が覆った。** (A) に相当するものは既に実装済みで、かつ契約どおり凍結されていた。
機序・数値・逐語は `output/insights/2026-08-12_testops-observation/`。要点だけ再掲すると、
台帳には task run 10 件・event 69 件が残り最終 event は 2026-07-21T20:33:39Z、以後 21 日間
新規記録ゼロ。止めているのは final marker・max_task_runs 到達・max_days 超過の三重の構造的拒否で、
これは事故ではなく D66 の pilot 契約そのものである。

**段 3 の敵対相談は両レンズ独立で NO-GO。** blocker 計 10 件のうち親が 1 件を refuted とした。
refuted は「sidecar の I/O 例外が pytest の rc を壊す」で、conftest が 3 hook すべてを
`try/except Exception` で包んでいるため成立しない。子がこれを見落としたのは、親が読む範囲の
名指しに conftest を含めなかったためであり、子の失点ではない。

**親自身の実測でも 1 件出た。** 段 2 プランの既定記録先は `XDG_STATE_HOME` 未設定の実機で
home 配下に解決され、2026-08-03 / 08-04 のユーザー是正 (作業ファイルは `/work` 配下) に反する。

**「実装しない」と裁定した理由は 3 つで、いずれも親が単独で解けない。** (i) 観測の再開そのものが
D66 が明示的にユーザー裁定へ予約した事項であり、wave 冒頭の scope 選択は無期限 rollover の
承認ではない。(ii) 記録先の択一が threat model を変える — D66 は hash chain を作らない代わりに
tracked file の git 履歴を改竄検出の外部 anchor にしており、repo 外化はそれを失う一方、repo 内に
留めれば走行ごとの untracked が並行する全 wave の clean-tree gate を壊す。(iii) blocker 9 件を
安全に閉じるとプランの 142 行見積りが成立せず、D220 が過大として不採用にした水準へ近づくため、
規模自体が D205 の判断を要する。

**受入全走は赤で、原因は main 側にある。** lease 内で local main (`427da17c`) を取り込んだ tip で
実走し、**2 failed / 9123 passed / 20 skipped (586.57 秒)**。落ちたのは
`orchestrator/tests/test_t793_report.py` の 2 node で、いずれも `docs/decisions.md` を読んで
D291 の supersession 参照を数え、期待値 `("D292",)` に対し実際が `("D292", "D305")` になる、というもの。
本 wave の差分は `docs/spool/` と `output/insights/` の追加だけで `docs/decisions.md` を 1 byte も
触っておらず、取り込み後の `docs/decisions.md` は main と byte 一致する
(`git diff main -- docs/decisions.md` が空)。D305 を入れたのは main の fold commit `427da17c` である。
単独再走でも同じ 2 件が決定的に落ちる (2 failed / 7 passed) のでフレークではない。
したがって**この赤は本 wave に帰属せず、main 自体が赤である** — 他の全 wave の受入も同じ場所で落ちる。
`DW-STOP` に従い land せずに停止した。

機序: `orchestrator/publication/report.py:75-80` の `_scan_d291_supersession` は「後続 decision に
`D291` が一度でも現れたら現在も承認済みとは断言しない」という意図的な fail-closed 設計であり、
production 側は仕様どおりに動いている。D305 は D291 payload の trust root を論じるので当然 D291 に
言及する。壊れているのは追記型台帳に対して完全一致を焼き付けたテスト側の期待値で、D291 に言及する
decision が増えるたびに再発する。**修正方針の択一 (pin を毎回更新するか、性質の表明に変えるか) は
正しさゲートの厳しさに触れるため、本 wave では触らず所有 wave とユーザーへ返す。**

**再開して land した (第 3 束裁定後).** ユーザー裁定 第 3 束で TestOps Q1〜Q3 = (a)(a)(a) が
確定した — Q1 は有界の次世代 pilot として再開、Q2 は repo 外 (repo 兄弟) へ記録し改竄検出は
主張しない、Q3 は被覆を `tools/run_tests.py` 経由のみとする。同裁定は本 wave を再開・land 可とした。
停止理由だった main の赤はその後 D316 が解消していた — 当該 2 node を完全一致 pin から
fail-closed な構造検査へ変えたためである。再開の precheck として main `6331284e` で
`orchestrator/tests/test_t793_report.py` を単独実走し **9 passed (2.67 秒)** を実測し、
blocker の消滅を確認してから worktree を復元した。したがって停止時に起票予定だった
「D291 言及が増えるたび pin が壊れる」課題は、本 wave の land 時点では既に閉じており新規起票しない。

`tools/check_wave_startup.py` は「HEAD == local main」の 1 項目だけ NG を返した。これは fresh
worktree 生成用の条件であり、自 wave の commit を持つ branch を再開する場合は構造的に成立しない
(同 checker の乖離報告自体は「local main との乖離なし (0 commit)」)。clean tree・operation 不在・
submodule marker・外部 handoff の各項目はすべて緑。再開後の受入全走は本 fragment を含む tip で
実走し、緑でなければ land しない。

設計判断は {{D:testops-observation-frozen-pilot}}。

## 次の一手差分

### 新規

- {{T:testops-observation-restart}} **P1・新規**: 有界 pilot として task-run 観測を再開する実装
  wave を起こす。第 3 束裁定で Q1〜Q3 = (a)(a)(a) が確定したので、裁定待ちではなく実装待ちである。
  制約は 3 つ — 有界の次世代 pilot に限る (無期限の常設計装にしない)、記録先は repo 外の repo 兄弟で
  改竄検出は主張しない、被覆は `tools/run_tests.py` 経由のみ (conftest 計装で全 pytest を覆わない)。
  `output/insights/2026-08-12_testops-observation/` が凍結した blocker 9 件と must-fix 11 件を
  閉じる plan v2 から起こす。規模は D205 / D220 の水準に触れうるので、着手前に見積りを実測で出す。
  選択肢の詳細と代償は同 insights の `verbatim/s4-ruling.md` §3。

- {{T:startup-gate-blocks-wave-resume}} **P2・ユーザー裁定待ち**: `DW-O20` は worktree の
  「作成・再開直後」に `tools/check_wave_startup.py` を走らせ非 0 なら停止せよと定めるが、
  自 wave の commit を持つ branch を再開する場合、点 1 (`HEAD == local main`) は構造的に成立せず
  **必ず非 0 になる**。本 wave の再開で実測 (2026-08-12) — 乖離報告は「local main との乖離なし
  (0 commit)」で他の項目はすべて緑なのに、点 1 だけが「fresh worktree を作り直す」を返した。
  文面どおりに従えば、裁定で再開を認可された wave が起動 gate で止まる。択一は
  (i) checker へ再開モードを足す (自 wave commit を許容し「main を包含し 0 commit 遅れ」を条件にする)、
  (ii) `DW-O20` へ「再開時は点 1 を除く」と明記する、(iii) 現状維持で再開のたび親が個別に判断する。
  (i)(ii) はいずれも fail-closed gate の受理集合を広げる方向なので、段 8 では実装せず裁定へ返す。

- {{T:dev-wave-reference-budget-has-zero-headroom}} **P2・ユーザー裁定待ち**:
  `docs/dev-wave/**` の L1.5 unique footprint が予算 9566 bytes ちょうどで、余白が 1 byte も無い
  (2026-08-12 実測)。本 wave の段 8 は実測に基づく改善候補を 1 件持っていたが、249 bytes の追記が
  そのまま予算超過になり、契約 (予算のために安全義務を弱めない・予算値の引き上げは独立審査) に
  従って編集を止めた。**この状態では dev-wave の手順改善が今後 1 件も入らない。**
  空ける手段は陳腐化ルールの削除か機械検査への置換に限られ、どちらも本 wave では未測定。
  見送った候補は「read-only 子へ行範囲を名指しするとき、判定対象に加えて呼び出し側と hook 配線も
  範囲へ入れる。範囲外を根拠に成立した所見は親が独立に裏取りしてから real とする」(`DW-O05` 相当)。
  根拠は本 wave の実測 — レンズ A の blocker 1 件が `orchestrator/tests/conftest.py:270-307` を
  範囲外にしたため誤って成立し、親の裏取りで refuted になった。
