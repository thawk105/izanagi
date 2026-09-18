# dev-wave 親段・計画 gate

親段・計画gate・context境界・停止条件の正本。

## DW-C00 — manager の範囲

範囲・言語・起動手順は入口に従い、command 引数は worklog 候補より優先する。層は読了トリガで決める:
L0=入口、L1=常時段の U 節、L1.5=クラス依存段の U 節、L2=C 節。

設計択一が割れる・正しさ防壁に触る・受理集合が変わる段では独立の敵対検証子を省かない。
変更面の確定時にも再評価する。該当なしだけ**既定の軽量版**とし、段 2・3 と段 6 の
review 子を省ける。実装面があれば段 5 の Codex 実装子と fix 子は省略不可で、
親は直接編集しない。docs-only は子ゼロでよい。実測は省かず、全 9 段はユーザー明示時に使う。

待ち手は 1 条件 1 本とし、通知ごとに作り直さず `tools/dev_wave_wait.py` を使う。生産者を止める
とき待ち手も落とし、その死も待ち条件に含む。停止後`ps`全cmdlineで対象worktreeの
0件実測後に投入。完了は`.done`非空で決める。同一worktreeのdispatchは全種直列（並行はorphan
holdでrc=16、`DW-O26`）。

## DW-C01 — 実測で是正した作法

`DW-O01/O08/O17/O20`より優先。
- `--lane`はconsult、`--reasoning`はplan/consultで必須。他段指定/必須段無指定はrc=2。
- 待ち手はpid file実在後に張る。先行は子の生存中も即戻る。
- 隔離worktreeのdetachは`.sh`2枚(launcher/detach)へ。直に叩くとguard拒否。
- 複数起点は全隣接区間の異なる正値で判別。
- 変異harnessはbaseline緑必須。既存赤は根拠を台帳へ書き`--deselect`。
- 全新規worktreeを`python3 tools/dev_wave_submodule_init.py --worktree <ABSOLUTE>`で再帰初期化する。
- 呼出し規約変更取込は、両親の変更行が非競合でも全呼出しを数える。
- 段6fixも受理・拒否の含意を2文に分け、通る正例を添える。
- merge/`add`/commitは親、子は競合解決だけ。
- 子の成果物はrepo内に書かせ、親が実行後repo外へ退避。
- Web検索は必要な段だけ明示して使う。

## DW-STOP — fail-closed 停止条件

参照契約違反・検査赤・権限/scope/所有違反は次段を止め、調査・修正・再検証する。
直せる赤で終了しない。承認前提を覆す新事実・裁定/権限待ち・
許可範囲で復旧不能な場合だけ正式停止。
停止条件をテスト弱体化、権限拡大、rebase、force、未監査差分の取り込みで迂回しない。

## DW-S01 — 段 1 brief

brief は 10〜30 行で研究前進、scope、確定済みユーザー裁定、不変条件、成果物の形、並列分割方針だけを書く。
研究前進は、進む論文の主張・図表・実験と完了判定、土台なら止めている研究の実測と最小差分を 1 行で示す。
起点を問わず、示せなければ後送も開始もせずユーザー裁定へ返す。割れうる前提は
`(P1)` と採番し「親の provisional 裁定・攻撃対象」とする。依頼・対象 vector の既存被覆を性質で
decisions / failures / archive まで検索し、純増だけ書く。確認前に子を起動しない。受入・実測環境を
決める（所在=worklog、機体固有情報=runbook）。変更面は分類でなく実アンカー表で渡す。

brief 前に承認済み裁定と引数と一次資料の未了項目の前提を実測し、覆す新事実は brief に出して段 4 で再裁定する。模擬/実の差を書き、自己 hash・
参照・pin は模擬で裁定しない（F29）。コード変更前提は monkeypatch でなく実編集し、`DW-O19` で
即時復元する。実編集不能なら拒否と模擬差を書く。別 program 起動物は build・環境変数・
外部 command・注入 seam の実在を棚卸しする。

decision / archive worklog の不一致は decision 優先（F31）。人間手番待ちは git / 成果物で済を
照合し、stale なら依存項目を繰り上げる（F35）。日付・hash・件数は commit / 成果物 field から取り、
docs は一次資料と一致するまで根拠にしない（F1）。

## DW-G01 — 生死実験先行

新しい探索軸・大型機構の本格実装前に、既存driverか100行以内の使い捨てdriverで
最安の生死確認をする。確認前の専用機構・LLM driver構築はbriefで却下する。

## DW-G02 — 初回 cycle 前 blocker の限定

最初のE2E 1 cycle前のhardeningは、correctness判定、selected/tie、数値、proof参照、
試行欠落を実際に変える欠陥だけblockerとし、他は1 cycle後へ送る。

## DW-G03 — 族一般化には独立 2 例

単発事故の既定は局所修復か一回限りのmigration。族全体への制度一般化は、
同型欠陥が異なるproducer/consumerで独立に2件再現したときだけ許す。

## DW-G04 — 条件付き機能の発火 gate

条件付き機能は発火条件を満たす既存artifact pathか計測IDをbriefに書ける場合だけ実装し、
書けなければ設計メモに留める。

## DW-G05 — 成果物影響

scope/must-fix は、放置時に成果物（certified 選択・レポート・台帳）の値・受理集合・参照がどう
変わるかを 1 行で示す。示せない must-fix は nit/backlog とし、追加 review を起動しない。
段 1 の scope で示せなければ子を起動せず `DW-G02` で 1 cycle 後へ送る。

確定主目的・scope の本体実装と足りる既存策・局所修正を優先する。超える追加実装・防壁は、明示要求内か、
段 1 の研究前進・実在欠陥・受入要件に必要で既存策不足を資料/実測で確認できる場合だけ scope/must-fix にする。
要求外の仮想リスクで framework・一般化・互換層・gate・検査・台帳を足さず、安全規律・要求・受入要件を弱めない。

## DW-S04 — 段 4 裁定

親が各所見を real/refuted、採用/不採用、scope 内/外に裁定しプラン v2 を確定する。
全段の scope 外 real 所見は実装せず、研究前進か実測欠陥を資料/実測で示した場合だけ設計択一・推奨案付き
裁定パッケージでユーザーへ返し、他は起票せず insight に記録する。
gate の禁止は署名で書き、通る正例を 1 つ添える。

実装面 (D95 決定 2) の差分ゼロの wave だけ変異 matrix を免除する。受入全走は免除せず、
実 repo を読むテストは段 7 の記録前に実走し、結果を worklog へ書く。
段 4 直前に裁定 inbox を再走査し、wave 開始後の更新を取り込む。

承認済み裁定は裁定時の未見事実でだけ止め、裁定文・worklog に未記録か確認する。親は不採用にせず、
新事実を添えてユーザー再裁定待ちへ戻す。実装方向まで裁定済みなら、コードで代案の等価性を
確認しない限り非同値な択一へ戻さない。

## DW-S07 — 段 7 記録

親が worklog、insights の逐語・変異台帳、decisions の設計判断を一括記録する。配置は`output/README.md` に従う。
**worklog / decisions / failures の 3 台帳は直接編集せず、`docs/spool/README.md` の形式に従う
fragment として書く**（insights は従来どおり直接書く）。fragment は wave branch へ commit するだけとし、
canonical への追記・採番・ローテーションは段 9 の land が lock 内で一度だけ行う。
**wave 側で fold してはならない。**
凍結前に全 gate の検出語（三軸語・placeholder）を機械走査し、hit は原文 hash 付きの可逆 defang +
erratum とする（D88）。走査器は `python3 -m orchestrator.campaign.s8b_holdout_freeze search`（rc≠0 で hit）。逐語末尾空白の `git diff --check` 抵触時も、原文hash・byte 数・
復元法を記録した可逆最小正規化だけを許す（可視文字不変）。
docs commit 後に repo scan invariant と影響テストを再走して閉じる（F34）。受入・検査は実測前に
欄を作らず未実施はそう書く。値なし前方参照と placeholder を禁じ、再走値は amend する。
hash 自己参照は禁止（F36）。

## DW-S08 — 段 8 自己改善

`docs/skill-self-improvement.md` を適用する。

## DW-S09 — 段 9 終端と local main

全 commit・受入結果を固定し、tested main/tip と監査 commit 列を実測して `DW-O23` を行う。
`tools/dev_wave_land.py` は local main を変更する唯一の通常 land 経路である。
正式な停止時だけ main HEAD と既存 branch を報告する。
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
