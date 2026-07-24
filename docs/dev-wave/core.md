# dev-wave 親段・計画 gate

この文書は `/dev-wave` の親が担う段、計画 gate、context 境界、停止条件の正本である。
入口の段・条件 dispatch で指定された時点に、F/D 番号の記憶で代用せず該当節を読む。

## DW-C00 — manager の範囲

dev-wave は izanagi の開発作業を進める 1 wave の manager であり、CC 合成 campaign の実行ループではない。
第一声、進捗、裁定、最終報告、`result:` を含むユーザー向け出力は、すべて最初から日本語で書く。
`CLAUDE.md` のクラス 3 起動手順を実行し、command 引数があれば worklog の候補より優先する。
入口の読み込み契約、段 dispatch、条件 dispatch は本書を含む reference の実行時契約である。

## DW-STOP — fail-closed 停止条件

指定 reference が不在・読めない、指定節が一意でない、期限までに読了していない、検査が赤、
権限・scope・所有が不整合、承認済み裁定の前提を覆す未見の新事実がある、またはユーザー裁定待ちなら、
該当段へ進まず停止する。後発条件の期限超過は入口の巻き戻し規則に従い、既存成果物を流用しない。
停止条件を、テスト弱体化、権限拡大、rebase、force、別 session の差分取り込みで迂回してはならない。

## DW-S01 — 段 1 brief

brief は緻密なプランではなく 10〜30 行とし、scope、確定済みユーザー裁定、不変条件、成果物の形、
並列分割方針だけを書く。判断が割れうる前提は `(P1)`, `(P2)` のように採番し、
「親の provisional 裁定であり攻撃対象」と明記する。

brief 前に、承認済み裁定の前提を実測する。未見の新事実で前提が覆ったら、その変化を brief に書き、
段 4 で scope を裁定し直す。実測では何を模擬したか、実差分と模擬の差を必ず明記する。
コード変更を伴う裁定前提は monkeypatch で代用せず、実際にファイルを編集して測り、直後に復元する。
実編集での測定を環境が拒否したら、拒否された事実と模擬との差を記録し、模擬を実測と偽ってはならない。
自己 hash・自己参照・自己 pin を持つ対象では、模擬を裁定根拠にしてはならない（F29）。
裁定要約が参照する decision 本文を必ず開き、落ちた制約がないか照合し、食い違えば本文を優先する（F31）。
「人間手番待ち」と繰り越された前提は、git と実成果物で未実行を照合する。既実行なら stale と裁定し、
依存項目を次の一手で繰り上げる（F35）。

## DW-G01 — 生死実験先行

新しい探索軸・大型機構の本格実装前に、既存 driver または 100 行以内の使い捨て driver で
最安の生死確認を行う。確認前の専用機構・LLM driver 構築は brief で却下する。

## DW-G02 — 初回 cycle 前 blocker の限定

最初の E2E 1 cycle 前の hardening は、correctness 判定、selected/tie、数値、proof 参照、
試行欠落を実際に変える欠陥だけを blocker とする。それ以外は 1 cycle 後へ送る。

## DW-G03 — 族一般化には独立 2 例

単発事故は局所修復または一回限りの migration を既定とする。族全体への制度一般化は、
同型欠陥が異なる producer/consumer で独立に 2 件再現した場合だけ許す。

## DW-G04 — 条件付き機能の発火 gate

条件付き機能は、発火条件を満たす既存 artifact path または計測 ID を brief に書ける場合だけ実装する。
書けなければ設計メモに留める。

## DW-G05 — must-fix の成果物影響

レビューの must-fix には、放置すると成果物（certified 選択、レポート、台帳）の
どの値・受理集合・参照がどう変わるかを 1 行で必ず書く。書けなければ nit/backlog とし、
追加 review wave を起動しない。

## DW-S04 — 段 4 裁定

親が各所見を real/refuted、採用/不採用、scope 内/外に裁定してプラン v2 を確定する。
scope 外の real 所見は実装せず、設計択一・所見・推奨案を裁定パッケージとしてユーザーへ返す。
実装前の変異事前登録は `DW-M01` に従う。

段 4 で「実装しない」と裁定した場合だけ段 5・6 を飛ばして `4→7→8→9` とする。
worklog には、実装差分がないため変異 matrix と受入全走が対象外であると射程を明記する。

承認済み裁定を止める前に、その根拠とする事実が裁定文・worklog に既に記録されていないかを
必ず確認する。既知事実を新事実として扱って、承認済み裁定を独断で失効させてはならない。
止めてよいのは裁定時点で未見だった新事実がある場合だけで、その場合も親が不採用にせず、
新事実付きのユーザー再裁定待ちへ戻す。実装方向まで裁定済みの項目を非同値な代案との択一へ戻さない。
戻す前に代案の等価性をコードで確認する。

## DW-S07 — 段 7 記録

親が worklog への吸収、insights への逐語・変異台帳の凍結、decisions への設計判断を一括して行う。
逐語・台帳を凍結する前に、対象へ三軸語 conjunction（軸 template の生値）の機械検査を行い、
hit があれば defang と erratum を施す。docs を含むあらゆる記録 commit の後に、
repo scan invariant と影響テストを再走してから wave を閉じる（F34）。
AI provenance、worklog、push の境界は `CLAUDE.md` と `docs/ai-provenance.md` を正本とする。

## DW-S08 — 段 8 自己改善

wave 開始時に専用 handoff へ「dev-wave 改善候補」節を作り、作法の欠落・無駄・曖昧・失敗に
気づいた時点で候補を記録する。段 7 後に一度だけ `docs/skill-self-improvement.md` の gate と
routing を適用する。事故を伴わない明確化・無駄取りも能力として残すが、command 入口へ無条件追記せず、
該当 reference 節を是正する。大変更は実装せず裁定パッケージへ送り、候補ゼロなら無言で通過する。

## DW-S09 — 段 9 終端と local main

実装・記録・自己改善の全 commit と受入結果が揃ってから、wave 専用 branch の commit を扱う。
main worktree が clean、main が wave 開始基準から予期せず動いていない、fast-forward 可能、
取り込む集合が本 wave の監査済み成果だけ、の全条件を再確認する。すべて満たす場合だけ
`--ff-only` で local main へ取り込む。一つでも欠ければ rebase・force・他 session 差分の巻き込みをせず停止する。
push と remote branch 操作はしない。main HEAD、次タスク、停止条件、再開コマンドを最終報告し、
同じ session で新しい wave を始めない。

## DW-CTX — fresh context と外部 supervisor

1 wave は 1 fresh context とする。対話運用では段 9 後に人間が `/clear <完了 wave 名>` を実行し、
続けて報告された `/dev-wave <次タスク>` を起動する。command 内から `/clear` を実行せず、
command を自己再帰させない（D69）。

無人継続は command 外部の supervisor が wave ごとに新しい `claude -p` process を起動し、
組み込み `/loop` は使わない。外部 supervisor は最初の spawn より前に本節を読む。
supervisor は `max-waves`、金額/トークン予算、wall-clock deadline を必須とし、無限ループにしない。
次タスクなし、ユーザー裁定待ち、テスト/check/変異の赤、dirty/diverged main、取り込み不能、
想定外 commit、process の非 0 終了・timeout、task-run/handoff 不整合で fail-closed 停止する。
自然言語の完了だけで継続せず、Git HEAD、cleanliness、検査結果、task-run 終了状態を照合する。
