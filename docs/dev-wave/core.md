# dev-wave 親段・計画 gate

親が担う段、計画 gate、context 境界、停止条件の正本。

## DW-C00 — manager の範囲

範囲・言語・起動手順は入口に従い、command 引数は worklog 候補より優先する。読み込み契約と
dispatch は実行時契約であり F/D 記憶で代用しない。層は読了トリガで決める:
L0=入口、L1=常時段の U 節、L1.5=クラス依存段の U 節、L2=C 節。

設計択一が割れる・正しさ防壁に触る・受理集合が変わる段では独立の
敵対検証子を省かない。変更面の確定時にも再評価する。該当なしだけ**既定の軽量版**とし、
段 2・3 と段 6 の review 子を省ける。実装面があれば段 5 の Codex 実装子と fix 子は
省略不可で、親は直接編集しない。docs-only は子ゼロでよい。実測は省かず、全 9 段は
ユーザー明示時に使う。

待ち手は 1 条件 1 本とし、通知ごとに作り直さず `tools/dev_wave_wait.py` を使う。生産者を止める
ときは待ち手も落とし、生産者の死も待ち条件に含める。

## DW-C01 — 実測で是正した作法

`DW-O01`/`DW-O08`/`DW-O17`/`DW-O20` に優先する。
- `--lane`は`--stage consult`だけ必須、無指定/他段rc=2。
- 待ち手はpid file実在後に張る。先行は子の生存中でも即戻る。
- 隔離worktreeのdetachはrunnerとlauncherの`.sh`へ外出しする。定型はguardが拒む。
- 複数起点の判別は全隣接区間へ異なる正値を入れる。
- 変異harnessはbaseline緑必須。既存赤は`--deselect`で外し根拠を台帳へ書く。
- submoduleは`git -c protocol.file.allow=always submodule update --init --recursive`。素は拒否、再帰なしはpreflight rc=2。
- 呼出し規約を変える取込は、両親の変更行が非競合でも全呼出しを数える。
- 段6のfixも受理・拒否の含意の向きを2文へ分け、通る正例を添える。
- mergeは親。子は競合解決だけ、`add`とcommitも親。
- 子のWeb検索を禁じる。成果物が全損する。

## DW-STOP — fail-closed 停止条件

指定 reference が不在・読めない、指定節が一意でない、期限までに読了していない、検査が赤、
権限・scope・所有が不整合、承認済み裁定の前提を覆す未見の新事実がある、またはユーザー裁定待ちなら
該当段へ進まず停止する。後発条件の期限超過は入口の巻き戻し規則に従い、既存成果物を流用しない。
停止条件をテスト弱体化、権限拡大、rebase、force、未監査差分の取り込みで迂回しない。

## DW-S01 — 段 1 brief

brief は緻密なプランではなく 10〜30 行とし、scope、確定済みユーザー裁定、不変条件、成果物の形、
並列分割方針だけを書く。判断が割れうる前提は `(P1)`, `(P2)` と採番し「親の provisional 裁定で
あり攻撃対象」と明記する。検査・テストを増やす wave では対象 vector の既存被覆を
機構名でなく性質で先に検索し、純増検出力だけを書く。未確認で子を起動しない。受入・実測の環境も確定する
（所在は worklog、機体固有情報は環境 runbook）。変更面は分類文を置かず実アンカー表だけを渡す。

brief 前に承認済み裁定と引数の前提を実測する。覆す新事実は brief に出して段 4 で再裁定する。模擬対象と
実との差を明記し、自己 hash / 参照 / pin 対象では模擬を裁定根拠にしない（F29）。コード変更を伴う
前提は monkeypatch でなく実編集・即時復元で測る。本走ではないが `DW-O19` の復元規律に従い、
段 5 へ遅らせない。実編集不能なら拒否事実と模擬との差を書く。別 program を起動する成果物では
build・環境変数・外部 command と注入 seam の実在を棚卸しする。

裁定要約が指す decision 本文と archive worklog を開き、食い違いは本文を優先する（F31）。人間手番待ちは git と成果物で
未実行を照合し、済なら stale として依存項目を繰り上げる（F35）。日付・hash・件数は commit / 成果物
field から取り、既存 docs は一次資料と一致するまで根拠にしない（F1）。

## DW-G01 — 生死実験先行

新しい探索軸・大型機構の本格実装前に、既存 driver か 100 行以内の使い捨て driver で
最安の生死確認を行う。確認前の専用機構・LLM driver 構築は brief で却下する。

## DW-G02 — 初回 cycle 前 blocker の限定

最初の E2E 1 cycle 前の hardening は、correctness 判定、selected/tie、数値、proof 参照、
試行欠落を実際に変える欠陥だけ blocker とし、他は 1 cycle 後へ送る。

## DW-G03 — 族一般化には独立 2 例

単発事故は局所修復か一回限りの migration を既定とする。族全体への制度一般化は、
同型欠陥が異なる producer/consumer で独立に 2 件再現したときだけ許す。

## DW-G04 — 条件付き機能の発火 gate

条件付き機能は、発火条件を満たす既存 artifact path か計測 ID を brief に書ける場合だけ実装する。
書けなければ設計メモに留める。

## DW-G05 — 成果物影響

段 1 の scope とレビューの must-fix には、それを実装しない・放置した場合に成果物（certified 選択、
レポート、台帳）のどの値・受理集合・参照がどう変わるかを 1 行で必ず書く。
書けない must-fix は nit/backlog とし、追加 review wave を起動しない。
段 1 で書けなければ `DW-G02` に従い、子を起動せずその場で 1 cycle 後へ送る。

## DW-S04 — 段 4 裁定

親が各所見を real/refuted、採用/不採用、scope 内/外に裁定しプラン v2 を確定する。
scope 外の real 所見は実装せず、設計択一・所見・推奨案を裁定パッケージでユーザーへ返す。
実装前の変異事前登録は `DW-M01` に従う。
gate の禁止は署名で書き、通る正例を 1 つ添える。

「実装しない」と裁定済みで実装差分ゼロの wave だけ変異 matrix を免除する。受入全走は免除せず、
実 repo を読むテストは段 7 の記録前に実走し、結果を worklog へ書く。
段 4 直前に裁定 inbox を再走査し、wave 開始後の更新を取り込む。

承認済み裁定は裁定時の未見事実でだけ止め、裁定文・worklog に未記録か確認する。親は不採用にせず、
新事実を添えてユーザー再裁定待ちへ戻す。実装方向まで裁定済みなら、コードで代案の等価性を
確認しない限り非同値な択一へ戻さない。

## DW-S07 — 段 7 記録

親が worklog、insights の逐語・変異台帳、decisions の設計判断を一括記録する。
**worklog / decisions / failures の 3 台帳は直接編集せず、`docs/spool/README.md` の形式に従う
fragment として書く**（insights は従来どおり直接書く）。fragment は wave branch へ commit するだけとし、
canonical への追記・採番・ローテーションは段 9 の land が lock 内で一度だけ行う。
**wave 側で fold してはならない。**
凍結前に全 gate の検出語（三軸語・placeholder）を機械走査し、hit は原文 hash 付きの可逆 defang +
erratum とする（D88）。逐語末尾空白の `git diff --check` 抵触時も、原文hash・byte 数・
復元法を記録した可逆最小正規化だけを許す（可視文字不変）。
docs commit 後に repo scan invariant と影響テストを再走して閉じる（F34）。受入・検査は実測前に
欄を作らず未実施はそう書く。値なし前方参照と placeholder を禁じ、再走値は amend する。
hash 自己参照は禁止（F36）。AI provenance、worklog、push の境界は `CLAUDE.md` と
`docs/ai-provenance.md` を正本とする。

## DW-S08 — 段 8 自己改善

段 7 後に一度だけ `docs/skill-self-improvement.md` の発火 gate・routing・command 別終端を適用する
（同文書と入口が正本。手順を本節へ再掲しない）。

## DW-S09 — 段 9 終端と local main

全 commit・受入結果を固定し、tested main/tip と監査 commit 列を実測して `DW-O23` を行う。
`tools/dev_wave_land.py` は local main を変更する唯一の通常 land 経路である。
`DW-O23` の成功結果以外は `DW-STOP` に従い、main HEAD と既存 branch を報告する。
段 9 後に `tools/collect_wave_usage.py` を実行。

## DW-CTX — fresh context と外部 supervisor

対話運用では段 9 後に人間が `/clear <完了 wave 名>` を実行し、報告された
`/dev-wave <次タスク>` を起動する。command 内から `/clear` を実行しない（D69）。

無人継続は外部 supervisor が wave ごとに新しい `claude -p` を起動し、組み込み `/loop` は
使わない。supervisor は `max-waves`、金額/トークン予算、wall-clock deadline を必須とし
無限ループにしない。次タスクなし、ユーザー裁定待ち、テスト/check/変異の赤、
未許可 dirty/diverged main、取り込み不能、想定外 commit、process の非 0 終了・timeout、
task-run/handoff 不整合で fail-closed 停止する。自然言語の完了だけで継続せず、Git HEAD、
cleanliness、検査結果、task-run 終了状態を照合する。
