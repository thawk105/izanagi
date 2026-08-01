# 段 1 brief v2 — 並行セッション開発の無駄なチェック削減 (parallel-dev)

- wave: `/dev-wave parallel-dev`、branch `worktree-dev-wave-parallel-dev`、**基準 `5948a6f`**
- 環境: `pegasus02` = `PEGASUS_LOGIN`。受入・変異・重い処理は計算ノードへ dispatch する

## v1 を invalidate した理由 (F 型: 誤前提 / ドリフト)

v1 brief と v2 plan は基準 `5544794` で書いたが、**その時点で local main は既に 13 commit 先の
`5948a6f` にあり、その差分に本 wave の中心論点のユーザー裁定が含まれていた**。
親は段 1 で「承認済み裁定の前提を実測する」(`DW-S01`) を行ったが、**実測の対象を
自 worktree の worklog に取り、local main の worklog を見なかった**。
これは本 wave が解こうとしている症状そのものである。
v1 = `s1-brief-invalidated.md`、v2 plan = `s2-plan-invalidated.md` へ退避した。

**救済できた資産**: `git diff --stat 5544794..5948a6f` は対象 6 ファイル
(`dev_wave_land.py` / `check_docs.py` / `run_tests.py` / `check_wave_startup.py` /
`test_dev_wave_land.py` / `docs/dev-wave/`) に対し**空**である。したがって
invalidated plan の file:line 事実は新基準でもそのまま成立する。**設計目標だけが変わった。**

## 確定済みユーザー裁定 (実測で確認)

1. **2026-08-01「codex はレートリミットが近いので使わないでください。claude を代わりに使ってください」**
   → D105 決定 (1) の `AI-Agent-Waiver: reason=codex_rate_limit; ratified=2026-08-01` を統合 commit に付す
2. **[T-220] P1・裁定済み ((74)) → 実装待ち: 択 (a) 採用 —
   `DW-O23` の受理集合を「incoming と衝突する未知 untracked だけ拒否」へ緩める**
   (`docs/worklog.md:998`)。[T-213] の (b)「自分の差分が触れていない handoff は
   control-plane 検査の対象から外す」も同義で一本化済み (`:113-115`)
3. 裁定の根拠として記録されたユーザーの言葉 (`:951`):
   **「別セッション所有のもので検査が落ちても、それを main に入れようとしていないなら関係ないはず」**。
   実測の裏付けも同箇所にあり、**「検査は衝突の有無を見ていない」**が欠陥の一文である
4. (78) の land は **ユーザー指示「やってください。並行セッション開発してますんで、そういうことは
   おきます」を受けて同一 context で main を 3 度取り込んだ** (`:962` 付近)。
   D102/`DW-S09` の fresh-context 要求は運用上すでにユーザー裁量で上書きされている (R1 へ記録)

## scope (実装 3 件)

- **S1 — [T-220] 択 (a) の実装。** `tools/dev_wave_land.py`。
  control-plane 検査を「incoming と衝突する未知 untracked だけ拒否」へ緩める。
  **v1 の案 3 (schema だけ撤去) では不足である** — 敵対検証 I-3 が、案 3 が維持宣言した
  `_SAFE_HANDOFF_RE` (42-44, 543)、`S_ISREG` (246)、`require_one_link` (248)、
  `_MAX_HANDOFF_BYTES` (259) が**いずれも `_Reject(RC_CONTROL_PLANE)` を投げ 619 経由で
  snapshot 全体を落とす**ことを file:line で示した。`notes.txt` / `.foo.md.swp` / `foo.md~` /
  サブディレクトリ / 2MiB 超が案 3 後も land 全体を止める。裁定文を満たすには
  **per-file の大域拒否をすべて分類へ変え、拒否を衝突検査へ一本化する**。
  **成果物影響**: 放置すると wave の成果が main へ着地せず branch に留まり、worklog 台帳と
  main の実状態が乖離する ((73) は着地せず終了、(77)(78) は各 1 回拒否 = **実績 3 件**)
- **S1b — 失われる 3 値語彙の機械執行を発生源へ移す (S1 の補償制御)。**
  敵対検証 I-2: `_HANDOFF_STATES` の consumer は `dev_wave_land.py:45` と `:568` **のみ**で、
  S1 でこれが repo から消える。`check_docs.py:2181-2187` の 48h 検出は
  `re.search(r"作業中|計測中")` 依存なので、自由文の状態は**永久に stale 判定されない**。
  移設先は `tools/check_wave_startup.py` の `--external-handoff` 経路とする — **自分の handoff だけを
  見るので他セッションを巻き込まない**。I-2 は「check_docs へ移設」を反証した
  (`check_docs.py:24` の `REPO` は `__file__` 由来で、worktree から走らせると `DW-O20` により
  空の `docs/handoff/` を見る = **wave セッションの commit gate は自分の handoff を構造的に見ない**)。
  **成果物影響**: 放置すると死んだセッションの handoff が無検出で残り、未回収作業が worklog へ
  吸収されず失われる
- **S2 — 他セッションの 48h 稼働中 handoff が、無関係なセッションの必須 commit gate を落とすのをやめる。**
  `tools/check_docs.py:2185-2188`。所有者を見ずに rc=1。射程は **main checkout で作業するセッション**
  (worktree セッションは I-2 のとおり構造的に無関係)。
  **成果物影響**: main checkout で作業するセッションが無関係な理由で commit できず台帳更新が滞る。
  **本日 10:15 頃に自然発火する**(実測済み)
- **S3 — repo に pytest 設定を新設し collection 範囲を checkout 非依存にする (F41 射程拡大 / T-129、P1)。**
  **`addopts` は絶対に書かない** — invalidated plan の (P3) 確認が、ini の `addopts` は
  `run_tests.py` の 4 ゲート (`_is_full_suite:314` / `_is_acceptance_run:403` /
  `_has_no_execution_flag:375` / `_has_dispatch_exempt_flag:390`) から**構造的に見えない**
  (すべて env の `PYTEST_ADDOPTS` しか読まない) ことを示した。
  **成果物影響**: 放置すると「赤の有無が checkout に依存」し続け、受入結果を実装差分へ誤帰属する

## 不変条件 (緩めない)

- **拒否の一本化先は衝突検査であり、拒否をなくすのではない。** incoming (land 対象) と衝突する
  untracked は引き続き拒否する。ff-only / lock / stale / audited closure / postcondition /
  gitlink 同期 / worktree admin 双方向束縛は不変 (敵対検証は「案 3 で未監査差分が main に入る
  新経路がある」を **refuted** と裁定した — これらは `_ControlSnapshot` を参照しない)
- **`docs/handoff/README.md` は tracked であり、land 可能な target であり続ける** (I-1、4/4 レンズ一致)。
  `_handoff_snapshot:616-617` の skip を維持し、protected へ入れない。既存 36 test に負例が無いので
  境界テストを純増で作る
- 他セッション所有物を変更しない。rebase / force / remote / push をしない
- D96 の手続に従い、decision 記録と境界テストを同じ変更単位で更新する
- 実装面は親が直接編集しない (D95 / D105 waiver 経路)

## 攻撃対象の provisional 裁定 (段 3 で攻撃させる)

- **(P1)** 「per-file の大域拒否をすべて分類へ変える」で T-220 (a) を過不足なく満たす。
  過小 (まだ落ちる経路が残る) と過大 (衝突するのに通す) の両方を疑うこと
- **(P2)** S1b の移設先が `check_wave_startup.py --external-handoff` で正しい。
  対話型セッション (handoff が main checkout 側) でも本人の gate になるかは**未確認**
- **(P3)** post-land 発火経路 (I-5) — `_postcondition:1231` が `_verify_main_clean` を再呼びし、
  main 前進後に `RC_LANDED_POSTCONDITION_FAILED` (非再試行) を出す窓が S1 で閉じる。**未確認**
- **(P4)** 内容 sha256 は現状 discriminator として機能していない (I-4)。S1 で構造を触るとき
  **恒真な保証を「維持した」と記録しない**。実効化するか、効いていないと正直に書くかを段 4 で裁定する

## scope 外 → 裁定パッケージ (`ruling-package.md`)

R1 (main 進行の再検査ループ、D102/D104 に当たる。(78) の同一 context 取り込み実績を追記する)、
R2 (`output/insights/` 平置きが衝突源)、R3 (worktree の `.gitignore`、元 S4 を降格)、
R4 (`dev_waves` の main-dirty が共有 checkout で恒常発火)。
さらに敵対検証が出した **I-6** (「未知 untracked を拒否」はコード上すでに存在せず、
`docs/decisions.md:4527` / `DW-O23` / `F55` / `docs/phase3.md:630` の記述が実装より strict) と
**I-7** ((77) の原因帰属誤り) を台帳訂正として段 7 で扱う。

## 成果物の形と並列分割

- 成果物: S1/S1b/S2/S3 の実装 + 境界テスト + decision 1 本 + failures 追記 + worklog + 裁定パッケージ
- 分割 (編集ファイル所有が素集合): **U1** = `tools/dev_wave_land.py` + `test_dev_wave_land.py` /
  **U2** = `tools/check_wave_startup.py` + `tools/check_docs.py` + 各テスト (S1b と S2 は
  handoff 検査という 1 つの関心事の表裏なので同一単位に寄せる) /
  **U3** = `pytest.ini` + collection 境界テスト
