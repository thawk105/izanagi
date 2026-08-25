---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1605-known-violation-groups
seq: 1
title: [T-1605] known-violation 台帳を不可逆な歴史群と新規群へ分け、運用目標を新規群 0 とする指標へ改めた (コード + テスト、branch worktree-dev-wave-t1605-known-violation-groups)
---

## 本文

- D742 の実装。**受理集合は 1 bit も変えていない。** どの commit が rc=0 / rc=1 / rc=2 に
  なるかは変更前後で同一で、群の値は rc の入力にしていない。既存の総数表示
  (`known-violations=N`) も、それが範囲相対の一致件数であるという意味も変えていない。

- **親のプラン v1 を段 3 で破棄した。** 当初案は「群を pinned boundary commit の ancestry で
  導出する」で、親はこれを「新しく作った違反を歴史群と自称する経路が構造的に存在しない」
  として provisional 裁定に置いた。敵対相談 2 レンズが**独立に別々の角度から壊した**。
  レンズ A は「ancestry は commit の年代を判定するだけで**歴史群の集合を固定しない**。
  boundary より古い commit へ entry を足せば歴史群が 54 件へ増えても全検査が通る」と示し、
  レンズ B は「boundary が解決できない repo で fallback の git 失敗が
  **従来 rc=0/1 の入力を rc=2 へ変える**」と示した。前者は D742 の「固定」が成立しないこと、
  後者は不変条件「受理集合を変えない」の違反である。二値分類で boundary 不在を扱うこと自体が
  未解決だった。**そこで群の定義から git を完全に外し**、凍結 baseline 集合への所属で判定して
  ancestry は test 層の独立裏取りへ移した ({{D:known-violation-frozen-baseline}})。
  この 1 手で must-fix 6 件が構造的に消えた。

- **親が一次資料で裏取りした事実 3 件。** (1) D742 を `docs/decisions.md` へ入れた唯一の commit は
  `5265fc6782fa5807aa742a198fa16d58006d17fb` で、その親には D742 が無く、main の祖先である。
  (2) **その commit 時点の台帳は現在と完全に同一の 53 entry・同一順序**だった (追加 0・削除 0)。
  (3) 53 entry の commit は 53/53 がその祖先。よって凍結 baseline は現在の 53 複合キーと一致する。
  レンズ A が提案した boundary SHA も親が独立に検証してから採用した。

- **worklog(922) の記述が一次資料と食い違っていたので訂正する。** 同エントリは
  「受入 receipt が bytes で束縛するのは `tools/run_tests.py` / `tools/dev_wave_wait.py` /
  `tools/check_ai_provenance.py` の 3 本だけ」と書いているが、実際に receipt へ入る byte 束縛は
  `launcher_executed_sha256` (`tools/acceptance_launcher.py`) / `waiter_executed_sha256`
  (`tools/dev_wave_wait.py`) / `runner_executed_sha256` (`tools/run_tests.py`) であり、
  **`tools/check_ai_provenance.py` は含まれない。** `checker_receipt_sha256` は非帰属赤 checker の
  ものである。段 6 のレンズ B が repo 全体の byte consumer を再検索し、
  `tools/codex_reasoning_ab.py` に checker file の**歴史 snapshot** SHA-256 pin があることも
  出した (過去 bytes の pin なので現在の編集で更新してはならない)。

- **親の裁定自身に恒真な positive control があり、段 6 のレビューが見つけた。**
  裁定は「2 群の和が台帳全体」「2 群が互いに素」「件数の和が一致」を positive control とし
  「台帳を空にすればこの 3 つが赤になる」と書いたが、`H = L∩B` / `G = L−B` の定義から
  導かれる恒真で 1 つも falsify できない。空台帳を捕まえるのは「baseline ⊆ 台帳」1 本だけだった。
  同型で、凍結 baseline の 53 キーにも独立 oracle が無く、baseline を台帳から実行時導出する
  退行が全検査を通過していた。両方とも閉じた ({{F:partition-derived-positive-control}})。

- **事前登録した変異 1 件が単一理由でないとレビューに指摘され、変異での証明を諦めた。**
  「baseline と台帳の両方へ post-D742 entry を足す」変異は ancestry 以外に逐語 mirror・
  件数・stdout の pin も赤にするため、ancestry assertion の生存証明にならない。
  `DW-M03` の「過剰決定なら単一理由へ差し替えるか冗長 gate と明記する」に従い、
  ancestry の生存は変異ではなく**テスト内の positive control** (同じ判定器が post-D742 commit へ
  False を返すことを要求する) で証明する形へ再照準した。代わりに
  「分類器へ結果を変えない subprocess 呼出しを足す」を単一理由の変異として登録した。

- **敵対レビュー 2 本の所見は must-fix 6 件・nit 2 件・refuted 3 件で、既存 assertion の弱化は
  ゼロだった。** レビュー B が変更された 8 assertion を全件分類し、1 件が強化 (substring 不在から
  stdout 完全一致へ)、7 件が等価と確定した。逐語 mirror (53 件)、`len(...) == 30`、
  stale の rc=2 と診断文字列、correction / waiver 合成の結果はいずれも無変更である。
  nit 2 件 (`__hash__` が `KeyError` を投げる str subclass、新しい print の `BrokenPipeError`) は
  実入力から到達不能なので実装していない。

- **非帰属赤を main 単独再現で確定させた。**
  `test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean` は
  本 wave の tree で file 単位走でも単独走でも赤になるが、**base `c3c5ca0a` を checkout した
  差分ゼロの probe worktree でも同じ `CertifiedWriterAuthorizationError` で赤**だった。
  本 wave の差分 2 file に `orchestrator/campaign/` は 1 件も含まれない。
  署名の見た目一致ではなく main 単独再現で確定させている。

- **指標が通常運用で保存されない件は scope 外とし、裁定パッケージへ回す。**
  waiter も land も checker の成功 stdout を捨てるため、群の値は時系列として残らない。
  D742 の理由「生成器修理の効果も測れる」を完全に満たすには受入 receipt schema と
  land result への投影が要るが、schema 変更は byte 束縛済みの waiter を巻き込み全 wave の受入へ
  波及する。本 wave は「値を定義し・計算し・常時公開し・凍結を gate する」までを担う。

- 親の作法違反を 1 件記録する。焦点走を前景の既定 2 分タイムアウトで投げて打ち切り、
  dispatch job を孤児化して orphan hold を武装させた。実害ゼロで 140 秒で解除したが、
  記憶に同型が既にあったのに踏んだ。詳細は {{F:partition-derived-positive-control}} と同じ
  fragment の F333 再発に書いた。

- **段 8 は候補 3 件を裁定し、dev-wave docs への追記は 3 件とも見送った。**
  (1) worklog(922) の byte pin 記述の誤りは worklog 本文の訂正で閉じ、docs 変更を要さない。
  (2) 「親のテスト走行を前景の既定タイムアウトで投げない」の収容先 `DW-O18` は
  **ちょうど 1000 bytes** で単節予算の上限に張り付いており、既存の安全義務を削らないと入らない。
  F333 の恒久対応が既に正本を持つ。
  (3) 「上限と対で置く positive control は、上限が守る対象と同じ定義から導出しない」は
  発火段が段 4 の事前登録なので `DW-M01` が正しい収容先で、単節では 467 bytes の余裕があった。
  **しかし L1 層全体の予算残が 9 bytes しかなく** (実測 10616 / 上限 10625)、
  157 bytes の追記で `L1 unique footprint 10773 bytes > 予算 10625 bytes` になった。
  契約は予算のために安全義務を削ることを禁じ、予算値の引き上げは独立審査としているため撤回した。
  実際に編集し、検査を走らせ、撤回して clean に戻したうえでの実測である。

## 次の一手差分

### 完了

- [T-1605] known-violation を不可逆な歴史群と新規群へ分け、運用目標を新規群 0 とする指標へ改めた。
  遡及訂正枠の一回性は解除していない。
  remaining: none
  base: 42fde69431df5c3dd4bbaf54aba2c856036fcc5114d7a1032821690a4c15dc04

### 新規

- {{T:known-violation-metric-persistence}} **P2・新規**: known-violation の群別指標を受入 receipt と
  land result へ投影し、時系列で追えるようにする。現状は waiter も land も checker の成功 stdout を
  捨てるため、生成器修理の前後差を現在値だけからは導けない。受入 receipt schema の変更は
  byte 束縛済みの waiter を巻き込むため、着手前にユーザー裁定が要る。
