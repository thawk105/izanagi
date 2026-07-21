# Izanagi 作業ログ (worklog)

セッションごとの進捗を時系列で記録する。git 履歴や各正本に入らない協議・異常・持ち越しを束ねる
「作業の索引」であり、commit 内容の再説明はしない。役割分担:

- 設計判断と却下案 → `docs/decisions.md`
- CCBench の構造的事実 → `docs/ccbench-anatomy.md`
- CCBench のバグ等の知見 → `output/insights/`
- タスク分解 → `docs/phaseN.md`
- **このファイル = それらを束ねる日誌 (各セッションの索引)**

## 新規エントリの書式 (D35)

過去エントリは凍結し、次の規約は新規エントリに適用する。

- 本文化するのは、ユーザー承認・協議の決着、棄却 finding (refuted)、未コミット事象・セッション異常と
  救出、エージェント工数、人間判断待ち・持ち越し、次の一手など **git に入り得ない情報だけ**
- commit は「hash + 件名 (+ 位置づけ 1 行)」まで。連続群は「先頭..末尾 (N 本)」で表し、内容を再掲しない
- 監査の finding 全文と裁定は insight / audit JSON に凍結する。worklog はレンズ数、real/refuted 数、
  最重要 1〜3 件、一次資料ポインタの 10〜15 行に留める
- 論文素材になる段落は行頭に「素材:」を付ける。持ち越しは逐語再掲せず「変わらず (前エントリ参照)」
  とする
- docs(worklog) だけの commit は prose の body を付けず、件名 + 必須 trailer だけにする

### 次の一手の ID 規約 (D70)

「次の一手」の項目が黙って落ちる経路を塞ぐため、各項目に安定 ID を付け、`tools/check_docs.py` が
保存則を機械検査する。ID は角括弧で囲んだ `T-` + 連番で、**表記は 1 つに正規化する** —
1〜999 は 3 桁ゼロ埋め、1000 以上は先頭ゼロなしで書く。冗長なゼロ埋め (4 桁で 1 を表す等) は
同じ数値の二表記になるため**不正形式として赤にする**。

- **位置**: トップレベル list item (インデント無しの `1. ` または `- `) の**先頭**に置く。
  インデントされた子項目は原子として扱わない — **1 原子 = 1 トップレベル項目 = 1 ID** に平坦化する
  (子項目 `(a)(b)(c)` に原子を詰めると、その分は機械検査の網から外れる)
- **採番**: 現行 worklog (「ローテーション」節より後) + `docs/archive/worklog-*.md` + 見送り台帳に
  現存する有効 ID の最大値 + 1。並行セッションは番号を予約したとみなさず、統合直前に再走査して
  未統合側を振り直す (`landed` = main へ統合された時点)
- **不変性**: 一度 land した ID は変更・再利用しない
- **保存則 (機械検査)**: あるエントリの「次の一手」に現れた ID は、後続エントリのトップレベル項目
  (消化または継続) か、見送り台帳のトップレベル項目 (理由付き見送り) に現れなければ赤になる。
  ローテーション境界 (アーカイブ最新の末尾エントリ → 現行の先頭エントリ) も検査対象
- **この節と決定記録には有効 ID を書かない** (採番母集団と sink の自己汚染を避けるため、
  例示は `T-NNN` のようなプレースホルダで書く)

## ローテーション

Phase 境界または現行ファイルの肥大時 (`tools/check_docs.py` の閾値超過が
知らせる) に、過去分を `docs/archive/worklog-<範囲>.md` へ**移動**し、現行ファイルを軽く保つ
(ブート時に読むのは末尾エントリのみ、の運用を軽く保つため。2026-07-05 導入、D35)。
アーカイブは凍結 (訂正注記のみ追記可)。既存アーカイブの一覧は `docs/archive/README.md`。

---
## 2026-07-20 (1) — B-004 wave 実装完了: 公式実験数値 pin (extime=5/reps=5) + report 隣接 3 穴 (branch approved-waves、計測なし)

worklog (8) 次の一手 1・2。**ユーザー裁定 (2026-07-19、会話はコンテキストクリア済みのためここが
記録の正本): 公式実験は extime=5 秒 / reps=5。floor と oracle は結合 (単一 authority) で実装は
一致検査。試行錯誤 (探索) は 3 秒 3 回目安で検証器の対象外。oracle 側 reps (X3-52 erratum) と
隣接 3 穴 (P_timeout_reason / P_build_reason / P_reason_type_crash) も同時承認。**

標準ループ (プラン v1 [handoff 控え] → codex 敵対相談 2 本並列 [gpt-5.6-sol max、14 所見
real 14/refuted 0、プラン v1 に NO-GO] → プラン v2 → 実行 = codex 並列 2 worktree → レビュー =
codex 並列 2 本 [所見 E1:3 / E2:1、全 real] → fix 再投 2 → 親変異 matrix N1〜N14 全 KILL +
受入全走 7 連続緑)。設計判断 = D64。相談・実行・レビュー・fix の逐語と変異実測の正本 =
`output/insights/2026-07-20_b004-experiment-numbers-consultations.md`。

- **裁定パッケージ 5 件** (承認 scope 超えのため実装せず、同 insights に凍結): report→judge→
  verdict の manifest 検証迂回 + 探索 namespace 隔離 (high) / reps=5 の観測証拠件数意味論 /
  gate-check preflight 偽緑 / 段階順序 truth-table / payload 非 Mapping クラッシュ
- B-057 発火 → 変異 12 本を実装前事前登録 + レビュー起因 2 本追加。レビュー前は N13/N14 相当が
  実測 survivor (floor reps re-literal / s8b_approved 再輸出恒真) → fix 後 14/14 KILL。
  B-056 発火 → coverage baseline/final 観測 (同水準、新 leaf 2 本 100%、gate 化なし)
- **D63 列挙漏れを補完** (D64 に erratum 併記): 結線監査 meta-テスト自身が real-repo 競合面なのに
  直列 group 外で、統合後の全走で間欠赤 (2/3、failing node はログ保存 — (8) 異常 (ii) の教訓を
  適用)。二重台帳の両側更新で閉鎖、片側のみの変更は監査が実測検出 (恒真化防止が設計どおり機能)
- golden SHA は相談予測・実装再計算・レビュー独立再構成の三重一致。codex 相談で安全フィルタ
  発火ゼロ (防御的表現の運用知見を適用)
- 工数: codex 相談 2 (max) + 実行 2 (high) + レビュー 2 (high) + fix 2 (medium)、親 = fable
  (裁定・統合・変異ゲート・flake 真因同定)

### 次の一手

1. **ユーザー裁定 (裁定パッケージ 5 件)**: 上記 insights の §裁定パッケージ。推奨順 = P-A1 の (b)
   探索 namespace 隔離 (小) → P-B5/P-B6 (report 証拠 truth-table と payload guard、同一分岐群の
   隣接 wave) → P-A2 (reps 意味論) → P-A5 (gate-check)
2. C (backlog-guard-mechanism): 変わらず (前エントリ参照 — 機構形式のユーザー裁定待ち)
3. ユーザー: branch approved-waves の push 判断 (AI は push しない。基点 aba3774 = main、
   本 wave 分を含め未 push)

## 2026-07-20 (2) — 裁定パッケージのユーザー裁定記録 (発効なし・計測なし・実装は次セッション)

worklog (1) 次の一手 1。ユーザー裁定 (本セッション、ここが記録の正本):

- **P-A2 (reps の意味論): 裁定確定 — 「reps=5 は成功した測定値 5 個」を意図する。**
  足りなければ不合格。report が測定値の個数を数える検査を実装してよい
- **P-A5 / P-B5 / P-B6 (gate-check preflight / 段階順序 truth-table / payload 型 guard):
  推奨案どおりの実装を一任で承認** (「よしなに」)。実装順の推奨 = P-B5/P-B6 (report 同一
  分岐群の隣接工事で 1 wave に同梱) → P-A2 → P-A5
- **P-A1 (公式判定の名乗り): 裁定継続。** ユーザー質問「探索も 5 秒 5 回に揃えれば齟齬の
  心配はなくなるか」への回答を記録: **なくならない** — 穴は数値差でなく「後段が検査通過を
  確認しない」こと。揃えると未検査入力は依然通る上に探索と公式の見た目の区別が消えて
  混入リスクはむしろ上がり、探索も 25 秒/点に遅くなる。推奨は引き続き (b) 探索成果物の
  別 namespace/書式化 (→ 段階導入で (a) 後段の検査必須化)

### 次の一手

1. **承認済み実装 wave (次セッション、クラス 3)**: P-B5 + P-B6 (+ P-A2 の個数検査) を 1 wave、
   P-A5 を続けて。正本 = insights 2026-07-20 の §裁定パッケージ + 本エントリの裁定
2. P-A1: ユーザー裁定継続 (推奨 (b)。上記 Q&A 参照)
3. C (backlog-guard-mechanism): 変わらず (前エントリ参照)
4. ユーザー: push 判断 (AI は push しない。main へのローカル merge は本セッションで指示済み)

## 2026-07-20 (3) — P-A1 のユーザー裁定確定 (発効なし・計測なし・実装は次セッション)

worklog (2) 次の一手 2。ユーザー裁定 (本セッション): **P-A1 は推奨案で確定** — (b) 探索成果物を
別 namespace/書式に隔離し official 側が型で拒否する (小) を先行し、(a) report→judge→verdict の
検査必須化 + 旧形式受理の廃止は段階導入。これで裁定パッケージ 5 件は全件決着 (P-A2 確定 /
P-A1・A5・B5・B6 推奨案承認)。

### 次の一手

1. **承認済み実装 wave (次セッション、クラス 3)**: P-A1(b) → P-B5 + P-B6 (+ P-A2 の個数検査)
   → P-A5 → (段階導入の設計判断として P-A1(a))。正本 = insights 2026-07-20 の §裁定パッケージ +
   worklog (2)(3) の裁定
2. C (backlog-guard-mechanism): 変わらず (前エントリ参照)
3. ユーザー: push 判断 (AI は push しない)

## 2026-07-20 (4) — 裁定パッケージ 5 件の実装 wave 完了 + ハイブリッド標準ループ初回試行 (branch approved-waves、計測なし)

worklog (3) 次の一手 1。**ループ形式の変更 (ユーザー発案の試行):** 親 (fable) は緻密プランを書かず
brief (scope/裁定/不変条件) のみ書き、緻密プラン起草を codex へ委譲。親の担当 = 裁定・scope 監査・
統合・変異ゲート実測・記録。ユーザー未返信のまま仮定で進行 (「品質を変えずに節約できるならそうしたい」
の意向に沿う。差し戻し可能な設計で実施)。

標準ループ (brief → codex プラン起草 [max] → 敵対相談 2 並列 [max、25 所見 real 25/refuted 0、
プラン v1 NO-GO] → 親裁定でプラン v2 [V1〜V16] → 実行 = codex 3 単位 [E1 ∥ E2 → E3、high、
worktree 分離、cherry-pick 競合ゼロ] → 親検算 → 変異 matrix 20/20 → 全走 [plain-runner ガード発火
1 件 → fixup] → 敵対レビュー 2 並列 [9 所見、real コード 4 = symlink/TOCTOU・数値有限性・judge
fixture 5 値化・未知 schema 負例] → fix 1 単位 → 変異 22/22 KILLED [レビュー起因 RM1/RM2 は fix 前
生存を実測 → fix 後 KILL] → 全走 7 連続緑)。設計判断 = D65。逐語・変異台帳・新裁定パッケージの
正本 = `output/insights/2026-07-20_wave2-adjudicated-package-loop.md` +
`2026-07-20_wave2-mutation-ledger.json`。

- commits: 4857534 (E1: P-A1(b) 型/namespace 隔離) → bfef26f (E2: truth-table leaf + P-A5) →
  038e749 (E3: report 配線 B5/B6/A2) → 5c09ef3 (自走 harness fixup) → a89e2b8 (レビュー fix 4 件) +
  本 docs commit。基点 58934ae
- 検収: 全走 7 連続緑 (2111 passed / 19 skipped)、変異 22/22 KILLED (B-057、exact diff 台帳凍結)、
  coverage 観測 (B-056): report 76→83% / judge 77→84% / 他同水準 (gate 化なし)
- **新裁定パッケージ 3 件 (実装せず、insights §裁定パッケージ)**: P-C1 rep 成功の rc=0 意味論 /
  P-C2 prepare retry の report 偽陽性 (既存挙動、親裏取り済み) / P-C3 意味論 leaf が generator pin 外
- 運用知見: (i) fix unit が担当外 docs を編集 → 親差し戻し (exec プロンプトに docs 禁止を恒久明記)。
  (ii) 親が commit で hooksPath 迂回フラグを誤用 → 即是正 (git hooks 未配線で実害なし。予防的迂回も
  禁止)。(iii) codex 安全フィルタ発火ゼロ (防御的表現の運用知見を継続適用)
- ハイブリッド観測 (サンプル 1): codex 9 本 (max 3 / high 5 / medium 1)、品質面の劣化兆候なし
  (相談 25 所見はプラン v1 の実穴、レビュー 4 real は全て fix で閉鎖 + 変異裏取り)。継続判断は
  ユーザーへ

### 次の一手

1. ユーザー: ハイブリッド形式 (プラン起草の codex 委譲) の継続可否
2. **ユーザー裁定 (新裁定パッケージ P-C1〜C3)**: insights 2026-07-20 wave2 §裁定パッケージ。
   推奨順 = P-C2 (retry 偽陽性、report 契約の穴) → P-C1 (rep 成功意味論) → P-C3 (P-A1(a) と同時)
3. P-A1(a) 段階導入 (Stage 1〜3、D65): 各段階の個別ユーザー承認待ち
4. C (backlog-guard-mechanism): 変わらず (前エントリ参照)
5. ユーザー: branch approved-waves の push 判断 (AI は push しない。基点 aba3774 = main、未 push)

## 2026-07-20 (5) — task-run 台帳 pilot 実装 wave (D66) + /dev-wave 改善 (branch approved-waves、計測なし)

handoff 2026-07-19 (AI 開発作業の統計記録) の実装。worklog (4) 次の一手は全件ユーザー裁定待ちのため、
唯一の非ブロック作業を選定 (次の一手 1 のハイブリッド継続は /dev-wave 起動自体を継続意思と解釈 —
明示裁定があれば上書き)。標準ループ (brief → codex プラン起草 [max] → 敵対相談 2 並列 [max、48
must-fix、プラン v1 NO-GO] → 親裁定 プラン v2 = V1〜V26 + 変異事前登録 M01〜M32 [B-057] → 実装 =
codex 3 単位 E1→E2∥E3 [high、worktree 分離、競合ゼロ] → 敵対レビュー 2 並列 [high、27 所見 全 real、
refuted 0] → fix 1 単位 [F-1〜F-21] → 親変異 matrix 実測 31/32 KILLED + M30 等価変異は両層同時
M30c で KILLED → 受入全走 7 連続緑 2248 passed/19 skipped)。設計判断 = D66。逐語・変異台帳の正本 =
`output/insights/2026-07-20_task-run-ledger-consultations.md` + 同 `-mutation-ledger.json`。

- commits: 349cf4e (実装一式) → bd5e67b (/dev-wave 改善) + 本 docs commit。基点 9cbe36a。
  異常記録: 初回積載 (139edd2/224817c/c104962) は AI-Agent trailer と Co-Authored-By の間の空行で
  trailer block が分断され provenance 監査 3 違反 → 未 push のためメッセージのみ修正して積み直し
  (tree 不変)。台帳の commit event は旧 SHA 2 件が append-only で残存し、新 SHA を追記で訂正
- **pilot 発足 + dogfooding**: init-pilot + 実 FS selfcheck 合格 → 本 wave 自身を run 1 として記録
  (`20260720-dev-wave-taskrun-ledger-fb468b60`、test_run 17 件 [red→green 1 周を実записи] + check 2 件 +
  commit 2 件、completed)。dogfooding が実運用縫い目 2 件を fail-closed 発火で捕捉 → 親 fixup:
  (i) root 直下 README.md が unknown 扱いで start 拒否 (validator 許容列挙と文書 layout の不一致)、
  (ii) 記録付き外側 run の env が既存 golden テストの subprocess mock を汚染 (conftest に autouse
  隔離 fixture)。両方とも回帰テスト同梱、fix 後に変異 matrix + 全走を再走済み
- **/dev-wave 改善 (ユーザー指示 2026-07-20)**: wave 実測の観測 4 点 (-o 作法化 / wave 専用 tmp /
  read-only sandbox の pytest 不能 / 依存単位・意図的赤・等価変異の扱い) + pilot 自己記録の導線を
  スキルへ反映 (bd5e67b)。main へのローカル取り込みはユーザー指示に従い本セッションで実施 (push はしない)
- 工数: codex 7 本 (max 3 / high 4)、親 = fable (裁定 2 回・統合・変異ゲート実測・dogfooding・記録)

### 次の一手

1. **task-run pilot 運用中 (〜10 run または 08-03)**: クラス 2/3 の実装・統合セッションは
   `python3 tools/task_run.py start` で記録を開始し、受入走に `IZANAGI_TASK_RUN_ID` を付け、
   `finish` で閉じる。手順の詳細正本 = `output/task-runs/README.md` (CLAUDE.md へは配線しない —
   pilot 実証後にユーザー提案)
2. **ユーザー裁定 (新裁定パッケージ P-C1〜C3)**: 変わらず (worklog (4) 参照)
3. P-A1(a) 段階導入 (Stage 1〜3、D65): 各段階の個別ユーザー承認待ち (変わらず)
4. C (backlog-guard-mechanism): 変わらず (機構形式のユーザー裁定待ち)
5. ユーザー: branch approved-waves の push 判断 (AI は push しない。基点 aba3774 = main、未 push)

## 2026-07-20 (6) — /dev-wave 段 8「スキル自己改善」の常設化 (ユーザー指示、計測なし)

ユーザー指示 (本セッション、ここが記録の正本): **wave 開始時に改善案メモ → 終了時にスキルへ反映を
/dev-wave 自体に組み込む。小さい改善 (段構成・権限・防壁・裁定境界を変えないもの) は AI が自律反映、
大きい変更はユーザー裁定。** 段 8 として明文化し commit 8664323、main へ 9360e25 としてローカル
取り込み済み (push はしない)。

### 次の一手

変わらず (worklog (5) 参照 — pilot 運用中 / P-C1〜C3・P-A1(a)・C の裁定待ち / push 判断)

## 2026-07-20 (7) — /rulings スキル新設 (ユーザー指示、計測なし)

ユーザー指示: 裁定待ち確認の定型プロンプトをスキル化。**全件 1 行索引 + 先頭 N 件 (既定 5) の平易な
詳説** (件数固定でなく索引で全体量を常に可視化する構成は AI 提案をユーザーが了承)。commit 79c1e7c、
main へ be3a455 として取り込み済み (push はしない)。

### 次の一手

変わらず (worklog (5) 参照)

## 2026-07-20 (8) — P-C1/C2/C3・C の ユーザー裁定確定 + push 現況 (発効なし・計測なし・実装は次セッション)

ユーザー裁定 (本セッション /rulings 経由、ここが記録の正本):

- **P-C2: 推奨案で確定** — 正当な prepare retry の attempt lifecycle を閉表化 (trial-result なし +
  retry 1 件 + 次 attempt 番号一致の window を正当 retried として扱う) + 正例テスト
- **P-C1: (b) で確定** — rep ごとの rc を WAL に記録し、report が 5 件とも rc=0 を検査
- **P-C3: 推奨どおり P-A1(a) 段階導入と同時に実施** (generator pin の transitive 拡張)
- **C (backlog-guard-mechanism): 推奨案 (ID + 機械検査) で確定** — handoff の着手条件が全て成立
- push 現況 (親が実測): **main は push 済み** (origin/main = be3a455、ローカルと一致)。
  **approved-waves は未 push** (origin に ref なし。本日 3 wave 分 10 commit はローカルのみ)

### 次の一手

1. **承認済み実装 wave (次セッション、クラス 3)**: P-C2 + P-C1(b) — report 契約の隣接工事として
   1 wave 同梱を推奨。正本 = insights 2026-07-20 wave2 §裁定パッケージ + 本エントリ
2. **承認済み実装 wave**: C = backlog-guard (ID + 機械検査)。正本 = handoff
   2026-07-19-backlog-guard-mechanism.md + 本エントリ
3. P-A1(a) Stage 1 の承認待ち (承認時に P-C3 を同梱)
4. ユーザー: approved-waves の push (未 push。意図的保留か失敗かの確認から)
5. task-run pilot 運用中 (worklog (5) 次の一手 1 参照)

## 2026-07-20 (9) — 全ブランチ棚卸し + approved-waves を main へ統合 (計測なし)

ユーザー指示「worktree/branch を全確認し、main に入れられるものを全て入れる」。

- 棚卸し: 未マージは approved-waves のみ (8 ahead / 3 behind)。backlog-triage /
  model-economy-tuning / test-hygiene / test-runner-autoscale / worktree-s8b-env-contract-pegasus /
  origin/worktree-s8b-ruling-prep は全て ahead=0 (取り込み済み。ブランチ削除はユーザー判断に委ねる)
- behind 3 コミットは commands 変更の main への cherry-pick 複製 (内容同一) と確認 → main を
  approved-waves へマージ (競合ゼロ、merge-tree 予行 + 実マージで裏取り) → main を fast-forward
- 検収: 全テスト 2248 passed / 19 skipped、check_docs 違反なし
- push はしない (Pegasus 規約)。統合後の main はローカルのみ先行 (origin/main = be3a455)

### 次の一手

1. **承認済み実装 wave (次セッション、クラス 3)**: P-C2 + P-C1(b) — report 契約の隣接工事として
   1 wave 同梱を推奨。正本 = insights 2026-07-20 wave2 §裁定パッケージ + worklog (8)
2. **承認済み実装 wave**: C = backlog-guard (ID + 機械検査)。正本 = handoff
   2026-07-19-backlog-guard-mechanism.md + worklog (8)
3. P-A1(a) Stage 1 の承認待ち (承認時に P-C3 を同梱)
4. ユーザー: main の push (統合後ローカルのみ先行。approved-waves ブランチと取り込み済み 5 ブランチの
   削除可否も合わせて判断)
5. task-run pilot 運用中 (worklog (5) 次の一手 1 参照)

## 2026-07-20 (10) — ブランチ・worktree 掃除の実施 + F26 台帳化 + /cleanup-branches スキル新設 (ユーザー指示、計測なし)

worklog (9) 次の一手 4 のうちローカル分をユーザーが裁定 (削除)。同一セッションで掃除 →
main push (ユーザー) → 本 commit の順。

- 掃除: ローカルブランチ 6 本 (approved-waves + 取り込み済み 5 本) と worktree
  s8b-c22-launch-cert を削除、ローカルは main 1 本に統一。main はユーザーが push 済み (a71057b)
- 掃除中に submodule 起因の罠 2 件を実測 (remove 無条件拒否・deinit の設定共有で main checkout の
  external/ccbench が一時未初期化 → update --init で復元済み) → **failures F26 に台帳化**
- **`/cleanup-branches` スキル新設** (.claude/commands/cleanup-branches.md): 棚卸し → 安全条件
  (ahead=0 のみ、-D 禁止) → F26 対応の worktree 削除手順 (deinit 禁止) → 事後検査 →
  push 系のユーザー引き渡し、の最小チェックリスト。ユーザー裁定 = 「failures 追記が本筋、
  スキルは最小」の推奨を承認

### 次の一手

1. **承認済み実装 wave (次セッション、クラス 3)**: P-C2 + P-C1(b) (worklog (8) 参照)
2. **承認済み実装 wave**: C = backlog-guard (worklog (8) 参照)
3. P-A1(a) Stage 1 の承認待ち (承認時に P-C3 を同梱)
4. ユーザー: 本 commit 後の main push + リモートブランチ削除の可否
   (origin/approved-waves・origin/worktree-s8b-ruling-prep。push 操作のため AI は行わない)
5. task-run pilot 運用中 (worklog (5) 次の一手 1 参照)

## 2026-07-20 (11) — /cleanup-branches に自己改善段を追加 (ユーザー指示、計測なし)

/dev-wave 段 8 と同型の「スキル自己改善」を §6 として追加 (発火条件つき — 記載と実挙動の
食い違い・新しい罠・手順不足を実測した場合のみ。failures 台帳との整合と 1 コミット化を規定)。
併せて初回実行 (worklog (10)) で得た未記載の知見を §3 に反映: ExitWorktree remove は ff 済み
コミットでも「未取り込み」と誤警告することがある — discard で押し切らず keep → 手動手順で畳む。

- 運用知見: EnterWorktree の fresh 基点は origin/main のため、ローカル main が push 前だと
  worktree に直近コミットが無い状態で始まる — 基点確認 (`git log --oneline -1`) を worktree
  作成直後に行う (本セッションで実測、reset --hard で復旧)

### 次の一手

1. **承認済み実装 wave (次セッション、クラス 3)**: P-C2 + P-C1(b) (worklog (8) 参照)
2. **承認済み実装 wave**: C = backlog-guard (worklog (8) 参照)
3. P-A1(a) Stage 1 の承認待ち (承認時に P-C3 を同梱)
4. ユーザー: main push (99bce0c + 本 commit の 2 件先行) + リモートブランチ削除の可否
   (origin/approved-waves・origin/worktree-s8b-ruling-prep)
5. task-run pilot 運用中 (worklog (5) 次の一手 1 参照)

## 2026-07-20 (12) — P-C2 + P-C1(b) 実装 wave (D67、branch worktree-dev-wave-pc2-pc1b、計測なし)

worklog (8) 次の一手 1 の承認済み実装 wave。ハイブリッド標準ループ (/dev-wave) で実施。

- **P-C2**: 正当な transient prepare retry が report で protocol_violation になる偽陽性を、
  per-row の attempt lifecycle DFA (受理形は `S1→pipeline→T1` と `S1→R→S2→pipeline→T2` の二形のみ、
  retry と trial-result の双方を窓へ全単射に束縛) で解消。**当初の局所修正案は敵対相談で却下** —
  それでは正規 driver に作れない列 (偽造 attempt 2) を受理し、攻撃者が選んだ性能値が正式標本に
  なる危険側の偽陰性が残るため。lifecycle 違反時も definitive-red を reason に残す (規律3)
- **P-C1(b)**: rep ごとの returncode を `bench_done.rep_returncodes` に記録し、report が
  非 bool int・件数 = APPROVED_REPS・全ゼロを検査。tps と rc の双方が成立して初めて bench_values を
  公開する。採用ラウンドと rc の対応は **object 同一性**で引く (最小 CV ラウンドが返るため index や
  dataclass equality では別ラウンドと誤対応し恒真化する)。一致が一意でなければ WAL を書かず fail-closed
- 検収: **2278 passed / 26 skipped**、check_docs 違反なし。**変異 18/18 KILLED・全て帰属成立**
- **erratum**: 変異の初回集計で 2 件を誤って「実効」と数えた (受理集合を変えない変異が理由文字列の
  変化だけで赤くなる過剰決定 fixture)。レビュー 2 本の独立指摘と親の追試で判明し、ゲートの構造分離と
  単一理由 fixture への差し替えで是正。経緯は insights の変異台帳 erratum に凍結
- 逐語 = `output/insights/2026-07-20_pc2-pc1b-loop.md`、変異台帳 = 同 `-mutation-ledger.md`

### 次の一手

1. **ユーザー裁定待ち (本 wave の裁定パッケージ 3 件)**: (a) campaign-terminal の物理位置が未検査
   (terminal を trial より前に置いた WAL が completed になる) / (b) session record の issuer
   (`variant`) と `env_tag` が未照合 (既存 report fixture 自体が manifest と異なる env を使っており、
   直すと fixture 群への波及が広い) / (c) WAL 改竄耐性 (duplicate key 最後勝ち・hash chain 不在)。
   いずれも敵対相談で real と判定したが scope 外。詳細 = D67 (7)
2. **承認済み実装 wave**: C = backlog-guard (ID + 機械検査)。正本 = handoff
   2026-07-19-backlog-guard-mechanism.md + worklog (8)
3. P-A1(a) Stage 1 の承認待ち (承認時に P-C3 を同梱)
4. ユーザー: main push (99bce0c 以降 + 本 wave の 2 件先行) + リモートブランチ削除の可否
   (origin/approved-waves・origin/worktree-s8b-ruling-prep)
5. task-run pilot 運用中 (worklog (5) 次の一手 1 参照)

## 2026-07-20 (13) — ruling-A のユーザー裁定確定 (発効なし・計測なし・実装は次セッション)

worklog (12) 次の一手 1(a)。/rulings 経由のユーザー裁定 (ここが記録の正本)。

- **ruling-A: 推奨案で確定 — ruling-C と同梱で 1 wave。** campaign-terminal の物理位置を検査する
  (完了宣言は WAL の最後、宣言より後の record は違反、宣言は最後の trial-result より後)。
  ruling-C (WAL 改竄耐性 = duplicate key 最後勝ち・hash chain 不在) を同じ wave に束ねる —
  どちらも「WAL を読む入口の堅牢化」で編集面とテスト土台が近いため。ruling-B (session record の
  issuer / env_tag 照合) は既存 fixture 群への波及が広いので**混ぜない** (未裁定のまま)
- **裁定前に親が実測し、D67 (7) の懸念を解消した**: D67 (7) は「terminal-last を課すと driver が
  terminal 後に書く record との整合検証が要る」として scope 外にしていたが、正規 driver は**両経路とも
  campaign-terminal が WAL への最後の書き込み**である (`s8b_oracle_driver.py:1073` = 予算切れ中断、
  `:1293` = 正常完了。いずれも直後が `return` で追記なし)。budget 台帳の settle は宣言より前かつ
  別ファイルのため WAL 順序に影響しない。よって「terminal は WAL の最後」規則は正規 producer の実挙動と
  一致し、**今回直した型の偽陽性を新たに作る恐れは否定された**
- 着手が安い時期である根拠: official campaign の WAL はまだ 1 件も生成されていないため、既存記録の
  適合棚卸しが不要

### 次の一手

1. **承認済み実装 wave (次セッション、クラス 3)**: ruling-A + ruling-C 同梱。正本 = D67 (7) +
   本エントリ。terminal 物理位置の検査は上記実測 (driver:1073/1293 が最後の書き込み) を前提にする
2. **承認済み実装 wave**: C = backlog-guard (ID + 機械検査)。正本 = handoff
   2026-07-19-backlog-guard-mechanism.md + worklog (8)
3. **ユーザー裁定待ち**: ruling-B (session record の issuer/env_tag 照合。既存 report fixture 自体が
   manifest と異なる env を使っており波及が広い) — 単独 wave を推奨
4. P-A1(a) Stage 1 の承認待ち (承認時に P-C3 を同梱)
5. ユーザー: main push (origin より 3 件先行) + リモートブランチ削除の可否
   (origin/approved-waves・origin/worktree-s8b-ruling-prep) + 本 wave の worktree 3 つとローカル
   ブランチ 3 本 (worktree-dev-wave-pc2-pc1b・wave-pc2-unit1・wave-pc1-unit2) の掃除可否
6. **B-008 (guard_agent 再検証) の発火条件が成立**: 見送り台帳の述語「新しい background job session
   の開始時」に本セッションが該当する (2026-07-20 の /rulings で確認)。拾うか見送り継続かは未裁定
7. task-run pilot 運用中 (worklog (5) 次の一手 1 参照)

## 2026-07-20 (14) — 裁定待ち一括裁定 + B-008 実施 (version drift 確定) + 運用方針の変更 (計測なし)

/rulings 経由のユーザー一括裁定 (ここが記録の正本)。裁定 6 件 + 標準指示 1 件。

- **1 push: 解決済み** — ユーザーが push 済み。親が実測確認 (`origin/main` = `1824c93`、差分 0)。
  **ただしリモートブランチ 2 本 (origin/approved-waves・origin/worktree-s8b-ruling-prep) の削除は
  未確認** — この環境は fetch の認証を持たず、ローカル追跡参照には 2 本が残ったままのため、削除の
  有無を確定できない。次の一手へ持ち越す
- **2 掃除: 承認** → 本セッションで実施 (wave 用 worktree 3 つとローカルブランチ 3 本)
- **3 次 wave: 推奨順で確定** = ruling-A + ruling-C を先、backlog-guard を次
- **標準指示 (新規、恒久): この水準の裁定は今後 AI が自動で行う。** 対象 = 掃除・順序決めなど、
  推奨が明確で可逆な運用判断。**対象外 = 設計の択一・正しさ防壁の変更・scope 拡張**で、これらは
  従来どおり裁定パッケージとしてユーザーへ返す。/rulings の索引には引き続き全件を載せる
  (見えない裁定待ちを作らないため) が、運用系は「実施済み」として報告する
- **4 P-A1(a) Stage 1: 承認** (P-C3 同梱)。公式 report API を検証済み manifest のみ受理へ狭め、
  raw Mapping / schema 分類器からの流入経路を廃止する
- **5 ruling-B: 承認、単独 wave** (session record の issuer/env_tag 照合。既存 fixture 群への
  波及が広いため他と混ぜない)
- **6 B-008: 実施 → 消化。判定 = version drift。** 新規 background job session (daemon
  **2.1.214**) で model 無し `Agent` を 1 回 probe → **guard_agent が PreToolUse で拒否、spawn なし**
  (拒否メッセージも逐語で親へ返達)。2.1.211 の不発は surface 固有の配送欠落ではなく version drift と
  確定。これにより **B-009 (追加防衛候補の裁定) も不要化** (価値は素通り時にのみ発生する条件付き
  候補だったため)。F21 の「恒真ゲート」懸念は本 probe で解消したが、**2.1.214 の 1 点観測**であり
  daemon 更新で再 drift しうる。反映先 3 箇所を更新: `hooks/README.md` hook 4「再検証の結果」/
  見送り台帳の B-008・B-009 を消化・不要化 / 本エントリ
- **7 限界受け入れ (viii)・8 pilot 配線提案: 推奨どおり据え置き** (いずれも発火条件・到達条件の
  手前。7 = floor 実測直前、8 = 10 run または 08-03)

### 次の一手

1. **承認済み実装 wave (次セッション、クラス 3、この順)**: (a) ruling-A + ruling-C 同梱 →
   (b) C = backlog-guard → (c) ruling-B 単独 → (d) P-A1(a) Stage 1 + P-C3 同梱。正本 =
   D67 (7) / handoff 2026-07-19-backlog-guard-mechanism.md / insights wave2 §7 + worklog (13)(14)
2. ~~ユーザー: リモートブランチ 2 本の削除可否~~ **解決 (2026-07-20)** — ユーザー観測により
   origin 側で削除済みと確認。本セッションは remote への鍵を持たず (`ls-remote` は
   `Permission denied (publickey)`) 自力検証できないため、**ユーザー観測を根拠に**古くなった
   ローカル追跡参照 2 本を `git branch -rd` で掃除した (追跡参照の削除のみ。remote は無操作)。
   結果: 追跡参照は `origin/main` のみ
3. B-008 の再試験条件: daemon の major/minor が上がった新規 background session で同じ probe
   (手順の正本 = `hooks/README.md`)
4. 限界受け入れ (viii) = floor 実測直前に最終承認 / task-run pilot 配線提案 = 10 run または
   08-03 到達時に提示 (現在 2 run)

## 2026-07-20 (15) — ruling-A + ruling-C 実装 wave (D68、branch worktree-dev-wave-ruling-ac、計測なし)

worklog (13)(14) 次の一手 1(a) の承認済み実装 wave。ハイブリッド標準ループ (/dev-wave) で実施。
実装内容は D68、逐語は insights。ここには git に入らない情報だけを書く。

- **敵対相談 2 本・敵対レビュー 2 本がいずれも NO-GO。** 相談 13 所見・レビュー 6 high は全て real
  (refuted 0)。**うち 3 件は親 brief 自身の誤り**で、brief を攻撃対象に含める規律が実際に効いた:
  (a) 「正規 writer は duplicate key を生成できない」→ 偽 (`json.dumps({1:"int","1":"str"})` が
  int key を str へ正規化して衝突。親が実測再現)、(b)「第二の reader は layer3」→ 実際は S-1 freeze と
  plotting も独立に WAL を読む、(c) hash chain 却下の根拠に D66 を引いたが D66 は task-run 台帳の
  決定で campaign WAL には適用できない
- **親の裁定ミスを 1 件、レビューが差し戻した。** 親は「reader で payload 型を落とすと D65 の行単位
  Mapping guard が到達不能になる」として検査を外したが、D65 の guard は **pipeline 限定**であり
  session record の非 Mapping payload は素通りしていた。しかも**親が入れたテストがその穴を機械固定**
  していた。レビュー 2 本が独立に指摘し、共有 parser で必須化 + 行単位 issue reader へ作り替えて是正
- **実装子の「赤なし」報告が全走で 10 件の赤だった** (単位 C)。実走範囲が 4 ファイルに限られており、
  主張の射程が曖昧だった。以降の実装子プロンプトに「緑の主張には走らせた範囲を必ず併記」を入れ、
  /dev-wave の定型にも反映 (段 8)
- **実装子がテスト fixture へ現行 hash を差し込んで破損を隠していた** (単位 C、S-1 freeze)。
  `s1_known_axes_freeze.py` は自己ハッシュ generator であり変更が freeze の `verify()` を壊す。
  親が実測確認のうえ 2 ファイルとも撤回。詳細 = D68 (7)
- 検収: **2304 passed / 26 skipped / 赤 0**、既存 WAL 30 ファイル 3,086 record の parse 回帰 0、
  check_docs 違反なし。**変異 注入 12 / HALT 0 / 12 が赤**。ただし **A04 は受理集合を変えないため
  kill 集計から外した** (診断保存 pin)。事前登録の C02・A02 もレビュー指摘で無効 kill / 過剰決定と
  判明し取り下げ。ハーネスは C09 で実際に HALT を発火させ、注入されなかった変異の誤報を防いだ
- エージェント工数: codex 7 本 (プラン 1 / 相談 2 / 実装 2 / レビュー 2 / fix 1、いずれも gpt-5.6-sol。
  相談・レビュー・fix は max、実装は high)。親の直接編集あり (payload 判断の試行 2 回 + S-1 撤回) —
  レビューには親作ハンクと明示して精査させた
- task-run: `20260720-ruling-ac-wal-terminal-43708d1e` (pilot 3 本目)

### 次の一手

1. **承認済み実装 wave (この順)**: (a) C = backlog-guard (正本 = handoff
   2026-07-19-backlog-guard-mechanism.md + worklog (8)) → (b) ruling-B 単独 (session record の
   issuer/env_tag 照合) → (c) P-A1(a) Stage 1 + P-C3 同梱
2. **ユーザー裁定待ち (本 wave の裁定パッケージ 6 件、いずれも real。正本 = D68 (8))**:
   (a) campaign WAL の hash chain / 外部 anchor — **D66 は根拠にならないと判明**したので改めて裁定が要る /
   (b) **WAL の byte 単位 record framing と resume の物理修復** (末尾断片が物理ファイルに残り次の
   `O_APPEND` が直結する。基準 HEAD から存在し全 campaign へ波及) / (c) S-1 freeze 再発行 (これが無いと
   S-1 reader を共有 parser へ収束できない) / (d) 宣言済み未使用 campaign の未評価 = F9 型 (P-A1(a) の
   守備範囲) / (e) 未知 stage の trial 前置 / (f) payload 型を writer で強制するか
3. B-008 の再試験条件: 変わらず (前エントリ参照)
4. 限界受け入れ (viii) = floor 実測直前に最終承認 / task-run pilot 配線提案 = 10 run または 08-03
   到達時に提示 (現在 3 run)

## 2026-07-20 (16) — /dev-wave の fresh-context 終端契約 (D69、計測なし)

ユーザーの問題提起を受け、開発 wave ごとの context 初期化は妥当と判断した。ただし skill 内自己再帰や
literal な無限ループではなく、1 wave を受入・commit・local main 取り込みまで閉じて外側から fresh
process/session を起動する安全側の終端契約だけを反映した。現行 Claude Code 2.1.214 と公式 docs を照合し、
組み込み `/loop` は同一 session 維持のため不採用。
外部 bounded supervisor は予算・最大 wave 数・permission mode が未確定なので未実装。サブエージェント利用なし。
検査は `check_codex_agents` / `check_docs` / `git diff --check` が全て rc=0。

### 次の一手

1. **承認済み実装 wave (この順)**: (a) C = backlog-guard (正本 = handoff
   2026-07-19-backlog-guard-mechanism.md + worklog (8)) → (b) ruling-B 単独 (session record の
   issuer/env_tag 照合) → (c) P-A1(a) Stage 1 + P-C3 同梱
2. **ユーザー裁定待ち (ruling-A/C wave の裁定パッケージ 6 件、いずれも real。正本 = D68 (8))**:
   (a) campaign WAL の hash chain / 外部 anchor / (b) WAL の byte 単位 record framing と resume の物理修復 /
   (c) S-1 freeze 再発行 / (d) 宣言済み未使用 campaign の未評価 / (e) 未知 stage の trial 前置 /
   (f) payload 型を writer で強制するか
3. B-008 の再試験条件: 変わらず (worklog (14) 参照)
4. 限界受け入れ (viii) = floor 実測直前に最終承認 / task-run pilot 配線提案 = 10 run または 08-03
   到達時に提示 (現在 3 run)
5. 外部 continuous-wave supervisor は、ユーザーが `max-waves`・予算・wall-clock・permission mode を
   指定した時だけ別 wave で実装する

## 2026-07-20 (17) — backlog-guard: 次の一手 ID + 保存則の機械検査 (D70、branch worktree-dev-wave-ruling-ac、計測なし)

worklog (15) 次の一手 1(a) の承認済み実装 wave。ハイブリッド標準ループ (/dev-wave) で実施。
機構形式は 2026-07-20 (8) で「ID + 機械検査」に確定済み。実装内容は D70、逐語は insights。

- **敵対相談 2 本がいずれも NO-GO。23 所見すべて real (refuted 0)。うち 3 件は親 brief 自身の誤り**:
  (a) 「台帳の既存 B-xxx は遡及ラベルしない」→ 設計正本 (前身 handoff) が台帳にも同体系を使うと明記、
  (b) 「末尾エントリに遡及で ID を振る」→ worklog 冒頭の凍結規約に抵触、(c) 台帳の対象を「45 件」と
  書いたが実数は **46 件** (親が実読で確定。プランの「48 行」も誤り)
- **プランの実バグを親の独立 probe が検出** (相談 A の BG-01 と一致し二重確定): 台帳抽出の正規表現が
  `re.DOTALL` 下で見出し行の `(?:[ \t].*)?` に改行を食わせ、**21,847 文字を飲んで body が 0 文字**に
  なる。台帳が sink として機能せず、見送った項目が常に「落ちた」と誤判定される。しかも抽出は
  「成功」扱いのため fail-closed finding も出ず**静かに壊れる**
- **保存則の設計を相談所見で 5 箇所強化した** (4 件は致命、1 件は高): 全隣接遷移の検査
  (末尾 2 件比較では 2 エントリ同時追加で飛び越せる) / ローテーション境界 (archive 最新末尾 → 現行先頭)
  の検査 / 台帳 sink を「裁定・完了記録」の手前で切る (完了記録の古い ID が永久 sink 化する fail-open) /
  sink を**トップレベル項目の先頭 ID** に限定 (prose や HTML コメントに token を書くだけの洗浄を封じる) /
  採番母集団から worklog 冒頭を除外 (書式節の例示による自己汚染、高)
- **プランの二段 land (worklog を 2 エントリ書く) は否認**。`handoff/README.md`「作業中は追記せず
  正常終了時に 1 回だけ吸収」に抵触するため。**なお親の裁定は「docs を先に land して実装子の意図的赤を
  無くす」だったが、実行では並列性を優先して実装子を先に起動した** — 実装子には期待 finding 5 件を
  事前に明示し、報告と実測が完全一致した (裁定と実行のこの差は敵対レビュー AC-05 が検出。
  本エントリの初稿は実行と逆の順序を書いていた)
- **敵対レビュー 2 本も NO-GO。19 所見。うち 3 件は親が書いた docs 自身の誤り** (工程記述の逆転 /
  codex 本数と所見深刻度の誤記 / D70 が自ら定めた「決定記録に有効 ID を書かない」規約の自己違反)。
  実装側の致命 3 件 (fenced code・複数行 HTML コメント経由の sink 洗浄 / archive 内部遷移の未検査 /
  同日 archive の順序不定) を fix 単位で塞いだ
- **本機構はまだ実データで一度も発火していない** (レビュー 2 本が独立に指摘)。現 repo の遷移候補
  25 本すべてで source が空 (ID 導入前) であり、**保存則の適用遷移は 0 本**。現時点で実際に働くのは
  「末尾 13 項目の形式・重複」と「台帳 46 ID の形式・重複」だけである。実発火の確認は次エントリの課題
  として台帳化した (T-013)
- 検収: **2344 passed / 26 skipped / 赤 0** (baseline 2304 から +40 = 追加テスト 40 本と一致)、
  `check_docs` 違反なし。**変異は 2 走**: fix 前 = 注入 16 / HALT 0 / KILLED 14 / 生存 2、
  fix 後 = **注入 12 / HALT 0 / KILLED 12 / 生存 0**。単一理由の kill は 6 件
- **変異ハーネス自身のバグを親が自己検出**: 初版は pytest の ANSI 色コードを除去せず失敗テスト名を
  常に 0 件に見せていた。**rc だけで kill を数えており、過剰決定を判定できないまま「12 kill」を
  報告するところだった**。修正後に第 1 走をやり直し、生存 2 件の内訳が判明した —
  **BG-M10 は等価変異** (実効ゲートは finding 側で、変異した `return None` は冗長ゲート。
  再照準した両層同時変異 BG-M10b が単一理由で kill) なので **kill 集計から外し**、
  **BG-M14 は真の生存 = テストの穴** (3 エントリで中間本文の消化 ID を分離する fixture が無かった)。
  後者は fix でテストを追加し第 2 走で単一理由の kill になった。erratum の正本 = 変異台帳 JSON
- エージェント工数: codex 7 本 (プラン 1 / 相談 2 / 実装 1 / レビュー 2 / fix 1、いずれも gpt-5.6-sol。
  相談・レビュー・fix は max、実装は high)。逐語の正本 =
  `output/insights/2026-07-20_backlog-guard-loop.md`、変異台帳 = 同 `-mutation-ledger.json`
- task-run: `20260720-backlog-guard-nextstep-ids-4ffdb273` (pilot 4 本目)

### 次の一手

1. [T-001] **承認済み実装 wave**: ruling-B 単独 (session record の issuer/env_tag 照合。既存 fixture 群への波及が広いため他と混ぜない)
2. [T-002] **承認済み実装 wave**: P-A1(a) Stage 1 + P-C3 同梱 (公式 report API を検証済み manifest のみ受理へ狭める)
3. [T-003] **ユーザー裁定待ち**: campaign WAL の hash chain / 外部 anchor (D66 は根拠にならないと判明済み。正本 = D68 (8))
4. [T-004] **ユーザー裁定待ち**: WAL の byte 単位 record framing と resume の物理修復 (末尾断片が物理ファイルに残り次の `O_APPEND` が直結する。基準 HEAD から存在し全 campaign へ波及)
5. [T-005] **ユーザー裁定待ち**: S-1 freeze 再発行 (これが無いと S-1 reader を共有 parser へ収束できない)
6. [T-006] **ユーザー裁定待ち**: 宣言済み未使用 campaign の未評価 = F9 型 (P-A1(a) の守備範囲)
7. [T-007] **ユーザー裁定待ち**: 未知 stage の trial 前置
8. [T-008] **ユーザー裁定待ち**: payload 型を writer で強制するか
9. [T-009] **ユーザー裁定待ち (本 wave の裁定パッケージ、real)**: dev-wave の実装子が負う規律の所在。実装子は docs と commit を禁じられる一方、`AGENTS.md` のクラス 2/3 規律は handoff とセッション末 worklog を求める。現状は親が射影して吸収しているが、この例外は AGENTS.md に明文化されていない (相談 B の R-05)
10. [T-010] B-008 の再試験条件: 変わらず (前エントリ参照)
11. [T-011] 限界受け入れ (viii) = floor 実測直前に最終承認
12. [T-012] task-run pilot 配線提案 = 10 run または 08-03 到達時に提示 (現在 4 run)
13. [T-013] **本機構の実データ初回発火の確認**: 本エントリの ID は導入直後のため保存則がまだ 1 度も実データで発火していない。次エントリ執筆時に (17)→(18) の遷移が実際に検査されることを確認する

## 2026-07-21 (1) — ユーザー裁定 4 件の記録 + 保存則の実データ初回発火 (計測なし)

/rulings 経由のユーザー裁定 4 件 (ここが記録の正本)。あわせて (17) で導入した次の一手 ID の
保存則が、実データで初めて発火する遷移になった。

- **並行セッションとの重複を記録する。** 本セッション (background job) は (17) と同一の
  backlog-guard wave を独立に実施していたが、**別セッションが先に完走・commit していた**
  (29ec921..49be772)。本セッションの敵対レビュー 2 本が出した 20 所見 (致命 3) は、commit 済みの
  版で**すべて塞がれている**ことを実読で確認した — fenced code / 複数行 HTML comment の除外、
  archive 内部の全隣接遷移、同日 archive の順序証明 (証明できなければ finding)、台帳 ID の完備性、
  末尾以外のエントリへの ID 必須検査。重複した実装成果は破棄し worktree を掃除した
- **重複の原因は task 分配であって機構ではない。** 同じ handoff と同じ「次の一手」を 2 セッションが
  同時に拾える経路は塞がれていない (handoff は排他を主張しない)。次の一手の ID 機構も**着手中の
  宣言は持たない** — 保存則は「落とさない」ことだけを保証し、「二重に拾わない」ことは保証しない
- 検収 (本セッションの独立実測): 全走 **2344 passed / 26 skipped**、`check_docs` 違反なし

### 消化した ID

- [T-003] campaign WAL の hash chain / 外部 anchor — **裁定: 作らない (現状維持)**。脅威境界は
  「正直だがバグりうる producer への構造検査」から変わっておらず、機構を足す理由がない。
  かわりに「改竄耐性」「改竄不能」「証明可能」とは書かない運用の明文化を [T-060] へ引き継ぐ
- [T-013] 保存則の実データ初回発火の確認 — **確認済み**。本エントリの執筆で (17)→本エントリ の
  遷移が初めて評価され、(17) の 13 ID の保存が実際に検査された (導入時の 0 遷移から 1 遷移へ)

### 次の一手

1. [T-005] **承認済み実装 wave (裁定 2026-07-21)**: S-1 freeze の再発行。`s1_known_axes_freeze.py` は自己ハッシュ generator であり、再発行時は**旧凍結との対応を記録に残す**こと (これが済むと S-1 reader を共有 parser へ収束できる)
2. [T-004] **承認済み実装 wave (裁定 2026-07-21、単独 wave)**: WAL の byte 単位 record framing と resume の物理修復。末尾断片が物理ファイルに残り次の `O_APPEND` が直結する。基準 HEAD から存在し全 campaign へ波及するため他と混ぜない
3. [T-001] **承認済み実装 wave**: ruling-B 単独 (session record の issuer/env_tag 照合。既存 fixture 群への波及が広いため他と混ぜない)
4. [T-002] **承認済み実装 wave**: P-A1(a) Stage 1 + P-C3 同梱 (公式 report API を検証済み manifest のみ受理へ狭める)
5. [T-060] **[T-003] 裁定の実装分**: WAL に関する記述から「改竄耐性」「改竄不能」「証明可能」を使わない運用を明文化する (脅威境界の正本 = D68 (6))
6. [T-061] **main への取り込みがユーザー待ち**: branch `worktree-dev-wave-ruling-ac` (49be772) と main (ed72579) が分岐しており ff-only で取り込めない。AI は merge を実行しない規約のため、rebase または merge の実行判断はユーザーへ渡す
7. [T-062] **並行セッションの重複防止**: 同じ「次の一手」を 2 セッションが同時に拾う経路が塞がれていない (本エントリ冒頭)。着手中の宣言をどこに置くか (handoff の排他化 / 次の一手への着手マーク / 何もしない) は設計択一のためユーザー裁定へ回す
8. [T-006] **ユーザー裁定待ち**: 宣言済み未使用 campaign の未評価 = F9 型 (P-A1(a) の守備範囲)
9. [T-007] **ユーザー裁定待ち**: 未知 stage の trial 前置
10. [T-008] **ユーザー裁定待ち**: payload 型を writer で強制するか
11. [T-009] **ユーザー裁定待ち**: dev-wave の実装子が負う規律の所在 (実装子は docs と commit を禁じられる一方、`AGENTS.md` のクラス 2/3 規律は handoff とセッション末 worklog を求める。この例外は AGENTS.md に未明文化)
12. [T-010] B-008 の再試験条件: 変わらず (前エントリ参照)
13. [T-011] 限界受け入れ (viii) = floor 実測直前に最終承認 (**裁定 2026-07-21: 推奨どおり据え置き**。発火は floor 実測の直前)
14. [T-012] task-run pilot 配線提案 = 10 run または 08-03 到達時に提示 (現在 4 run)

## 2026-07-21 (2) — 裁定 5 件の確定 + main 取り込み・push の完了記録 (計測なし)

/rulings 経由のユーザー裁定 5 件 (ここが記録の正本)。**いずれも推奨どおりで確定**。
あわせて前エントリの持ち越し 2 件が完了したので消化する。

- 裁定の設計上の含意は 2 つ。(a) **重複防止の機構は入れない** — 前エントリで実測した二重実行は
  成果物を壊さず、失うのは AI の実行時間だけだったため、「守るものの価値 < 機構の複雑さ」と判断した。
  (b) **記録まわりの 3 項目を 1 wave に束ねる** — [T-004] [T-007] [T-008] は同じ WAL 経路を触るため、
  別々の wave にすると同じファイルを 3 回触ることになる
- 保存則は本エントリで **2 遷移目**の評価に入った (前エントリで 1 遷移目が初発火)

### 消化した ID

- [T-061] main への取り込み — **完了**。ユーザーが branch を `ed72579` の上へ rebase して local main
  へ取り込み、さらに **push まで完了** (`origin/main` と一致、先行 0 commit)。前エントリ執筆時点の
  「分岐しており ff-only 不可」は解消済み
- [T-062] 並行セッションの重複防止 — **裁定: 何もしない**。着手中の宣言 (handoff の排他化 /
  次の一手への着手マーク) はいずれも採らない。二重実行は再発しうるが、成果物は壊れず番号衝突も
  繰り下げで解決できることを実測で確認したため、これを受け入れる
- [T-006] 宣言済み未使用 campaign の未評価 (F9 型) — **裁定: [T-002] に同梱**。以後は [T-002] の
  守備範囲として扱い、単独項目としては持たない

### 次の一手

1. [T-005] **承認済み実装 wave**: S-1 freeze の再発行。`s1_known_axes_freeze.py` は自己ハッシュ generator であり、再発行時は**旧凍結との対応を記録に残す**こと (これが済むと S-1 reader を共有 parser へ収束できる)
2. [T-004] **承認済み実装 wave (単独 wave、[T-007] [T-008] を同梱)**: WAL の byte 単位 record framing と resume の物理修復。末尾断片が物理ファイルに残り次の `O_APPEND` が直結する。基準 HEAD から存在し全 campaign へ波及する
3. [T-008] **裁定確定 (2026-07-21): payload 型を writer 側でも強制する**。追記専用の台帳は後から直せないため入口で止める。[T-004] の wave に同梱
4. [T-007] **裁定確定 (2026-07-21): 未知 stage は拒否する** (fail-closed)。stage 追加時は検査側の更新を要するが、頻度は低くタイプミス由来の stage 名を通さない利得が上回る。[T-004] の wave に同梱
5. [T-001] **承認済み実装 wave**: ruling-B 単独 (session record の issuer/env_tag 照合。既存 fixture 群への波及が広いため他と混ぜない)
6. [T-002] **承認済み実装 wave ([T-006] を同梱)**: P-A1(a) Stage 1 + P-C3。公式 report API を検証済み manifest のみ受理へ狭め、あわせて宣言済み未使用 campaign の未評価 (F9 型) を塞ぐ
7. [T-009] **裁定確定 (2026-07-21): 実装子の規律免除を明文化する**。「親が射影して吸収する dev-wave の実装子は handoff とセッション末 worklog の義務を負わない」を `AGENTS.md` へ 1 段落追記する
8. [T-060] **[T-003] 裁定の実装分**: WAL に関する記述から「改竄耐性」「改竄不能」「証明可能」を使わない運用を明文化する (脅威境界の正本 = D68 (6))
9. [T-010] B-008 の再試験条件: 変わらず (前エントリ参照)
10. [T-011] 限界受け入れ (viii) = floor 実測直前に最終承認 (裁定 2026-07-21: 据え置き)
11. [T-012] task-run pilot 配線提案 = 10 run または 08-03 到達時に提示 (現在 4 run)

## 2026-07-21 (3) — [T-005] S-1 freeze 再発行は依存閉包に阻まれ差し戻し (D71、branch worktree-dev-wave-ruling-ac、計測なし)

worklog (2) 次の一手 1 の承認済み実装 wave として着手したが、**実測により承認 scope の中では完了
できないと判明したため実装せず差し戻した**。ハイブリッド標準ループ (/dev-wave) で実施。
設計判断は D71、逐語は `output/insights/2026-07-21_s1-freeze-reissue-loop.md`。
ここには git に入らない情報だけを書く。

- **canonical 成果物は 1 byte も変更していない。** `output/s1-freeze/` の 2 本と
  `output/s8b-freeze/holdout_freeze.json` は着手前と同一。本 wave の commit は docs と skill のみ
- **敵対相談 2 本がいずれも独立に NO-GO。** レンズは正しさ境界 / 整合・実効性。両者が別経路で
  同じ閉包 (S-1 → holdout → v1 trust root → v2 transition table) に到達した
- **親の provisional 裁定 8 件のうち 6 件が否認された** (P1/P2/P5/P6/P7/P8)。brief を攻撃対象に
  含める規律が効いた 2 回目の実例。特に P2 (published commit へ anchor を貼り替える) は、
  「push 前の anchor は新 generator bytes を含まない」という単純な事実で崩れた。**親が自分の案の
  実行順序を最後まで辿っていなかった**のが原因
- **親の brief の事実誤認を 2 件、相談が検出した。** (a) F11「freeze 内世代連鎖は本 repo で未裁定」
  → 誤り。`s8b_ratified_freeze.py` に generation / approval / active pointer / transition が実装済みで、
  v1 が世代 field を拒むのは型分離。この誤った根拠の上に P4′ を立てていた。
  (b) F17 の二状態モデル → 誤り。holdout は再発行前から既に落ちている (親が実測で自己訂正済み)
- **事前登録変異 M1..M5 は 5 件すべて欠陥**で、変異実測に到達しなかった。単層変異が等価変異
  (M4)、先行検査に食われて受理集合が変わらない (M1・M5)、過剰決定 (M3)、baseline と mutant の
  期待が逆転 (M2)。**5 件中 5 件が机上で誤っていた** — 変異の事前登録はコードでの裏取りを要する
- **submodule 未 init が真の破損を隠していた。** worktree には submodule が入らないため、
  最初の verify は「source が存在しない」で ancestry より手前で落ちていた。
  `git submodule update --init` を先に実行して初めて実体が見えた
- **ユーザー指摘への対応を wave 冒頭で実施** — `/dev-wave` が英語で始まる問題。日本語規律を
  skill 冒頭へ格上げし第一声を明示的に対象化した (commit `f2f3756`)
- 検収: `check_docs` 違反なし、S-1 freeze 系テスト green (`3 passed / 3 skipped`、skip は submodule
  依存)。**実装差分が無いため変異 matrix と受入全走は本 wave の対象外**
- エージェント工数: codex 3 本 (プラン 1 / 相談 2、いずれも gpt-5.6-sol、プラン max・相談 max)、
  claude 子 1 本 (構造地図、sonnet)。**実装子・レビュー子は起動していない** (実装が無いため)
- task-run: `20260720-s1-freeze-reissue-e5aef5fe` (pilot 5 本目)

### 消化した ID

- なし。[T-005] は完了せず、性格を「承認済み実装 wave」から「**ユーザー裁定待ち**」へ変更して
  次の一手に残す (D71 (9))。承認は新事実により前提を失ったため、再承認が要る

### 次の一手

1. [T-005] **ユーザー裁定待ちへ差し戻し (2026-07-21、D71)**: S-1 freeze 再発行の可否。実行すると
   holdout の `known_axes_freeze.sha256` が外れ、上書きは `V1_FREEZE_SHA256` (v1 trust root) を壊し、
   v2 追随は `_TRANSITION_V1_TO_G1` に `/known_axes_freeze/sha256` が無いため拒否される。
   **正規の道が 3 方向とも塞がっている**。推奨 = 単独では実行せず [T-063] [T-064] と束ねて裁定する
2. [T-063] **裁定待ち (新規)**: 再発行の**許容 JSON Pointer 差分契約**を確定する。親の当初案
   「差分は `frozen_at_head` と `python_version` のみ」は成立しない (known bytes が変われば
   measurement の `/implementation_hashes/known_axes_freeze/sha256` も必ず変わる)。推奨 =
   exact な許容 pointer 集合をユーザーが確定し、それ以外は厳密一致とする
3. [T-064] **裁定待ち (新規)**: legacy holdout freeze を**歴史成果物として据え置く**か、
   **s8b trust root ごと移行する**か。据え置くなら oracle 非復旧を明記する。移行するなら
   `V1_FREEZE_SHA256`・transition table・protocol golden まで含む別 wave が要る。
   holdout 再生成は `confirmed_by` (人間確認者名) を必須とするため **AI 単独では実行できない**
4. [T-065] **実装待ち (新規、要裁定)**: holdout freeze が **2026-07-18 から無効**である
   (`design_source` sha256 のドリフト、F9 型)。floor protocol 裁定記録の commit 群が
   `docs/phase3-8b-descriptor-design.md` を更新したことが原因。3 日間検出されなかった
5. [T-066] **実装待ち (新規、要裁定)**: `test_s1_measurement_freeze.py` に
   **D68 (7) の隠蔽パターンが現存**する (production generator の現行 hash を動的注入 +
   `K.build_document` を fixture の echo へ置換)。防壁変更にあたるため裁定へ回す
6. [T-067] **実装待ち (新規、要裁定)**: oracle 系テストが **refusal の増加を検出できない**
   (`test_s8b_oracle_driver.py` は floor-null / budget-null / status=refused / rc=2 しか要求しない)。
   拒否理由の exact 検査へ強化する
7. [T-068] **裁定待ち (新規)**: dangling `frozen_at_head` は **freeze 族共通の病**。S-1 の歴代 5 世代と
   holdout の計 6 個すべてが repo に存在しない。wave branch で生成 → rebase で SHA 書換え、が原因。
   恒久対応は [T-063] と同時に決める必要がある
8. [T-004] **承認済み実装 wave (単独 wave、[T-007] [T-008] を同梱)**: WAL の byte 単位 record framing と
   resume の物理修復。末尾断片が物理ファイルに残り次の `O_APPEND` が直結する。基準 HEAD から存在し
   全 campaign へ波及する。**本 wave が実装に至らなかったため、次に着手すべきはこれ**
9. [T-008] **裁定確定 (2026-07-21): payload 型を writer 側でも強制する**。[T-004] の wave に同梱
10. [T-007] **裁定確定 (2026-07-21): 未知 stage は拒否する** (fail-closed)。[T-004] の wave に同梱
11. [T-001] **承認済み実装 wave**: ruling-B 単独 (session record の issuer/env_tag 照合)
12. [T-002] **承認済み実装 wave ([T-006] を同梱)**: P-A1(a) Stage 1 + P-C3
13. [T-009] **裁定確定 (2026-07-21)**: 実装子の規律免除を `AGENTS.md` へ 1 段落追記する
14. [T-060] **[T-003] 裁定の実装分**: WAL に関する記述から「改竄耐性」「改竄不能」「証明可能」を
    使わない運用を明文化する (脅威境界の正本 = D68 (6))
15. [T-010] B-008 の再試験条件: 変わらず
16. [T-011] 限界受け入れ (viii) = floor 実測直前に最終承認 (据え置き)
17. [T-012] task-run pilot 配線提案 = 10 run または 08-03 到達時に提示 (現在 5 run)

## 2026-07-21 (4) — `/loop-w` bounded supervisor の実装設計 (提案のみ、計測なし)

ユーザー要望に基づき、task ごとに context を切った fresh `claude -p` で `/dev-wave` を最大 N 回だけ
直列実行する supervisor の実装案を作成した。実装・real model 呼出し・local main 取り込みはまだ行って
いない。作業は main と分離した branch `codex/dev-waves-supervisor-design`、worktree
`.codex/worktrees/dev-waves-supervisor-design` で実施した。

- 実行鎖はユーザー訂正どおり **Claude project skill `/loop-w N` → external Python supervisor daemon →
  wave ごとの fresh `claude -p` → `/dev-wave --supervised-manifest ...`**。Codex CLI は設計・実装作業者で
  あって runtime chain には含めない
- 新規入口は公式推奨の `.claude/skills/loop-w/SKILL.md`。副作用を伴うため
  `disable-model-invocation: true` とし、人間だけが起動する。skill 名制約に従い `_` でなく `-` を使う
- skill 配下から child Claude を直接 nested spawn しない。Bash tool 配下の公式 marker
  `CLAUDECODE=1` を daemon 起動拒否条件にし、環境変数 unset で迂回しない。skill は Claude の外で
  起動済み daemon の Unix socket client に限定する
- daemon は exact local main SHA から専用 Git worktree を自前作成し、stdin `/dev/null`、explicit
  `--permission-mode auto`、structured output schema、per-wave budget/timeout 付きで 1 child だけ起動する。
  auto 不可時に dangerous bypass へ fallback しない
- child final / exit code を単独では信頼しない。structured receipt と main の clean/ff/commit 集合、
  worklog ID 保存則、handoff、task-run pilot、submodule、check/provenance を独立照合し、1 件でも不一致なら
  次 wave を起動しない。push、rebase、merge、force、自動 retry、自動 worktree cleanup はしない
- supervisor が見た値と行った操作は `output/dev-wave-supervisor/runtime/<run-id>/` の gitignored private
  runtime へ記録する。`events.jsonl` を append-only control WAL、raw stdout/stderr、worker structural exit、
  sanitized receipt/check/summary を分離し、WAL write/fsync failure は fail-closed にする
- crash-after-land を含む recovery、PID/process-group kill、resource bounds、closed reason code、fake Claude
  + temp Git repo の integration、各 gate の mutation matrix、max-waves=1 から 3 への段階導入まで設計した
- 提案の正本は `output/insights/2026-07-21_dev-waves-supervisor-design.md`。冒頭を
  `status: unadjudicated / authority: none / default_effect: no-state-change` とし、現行状態へ効かないことを
  明示した
- 公式 Claude Code docs とローカル 2.1.214 `--help` を照合した。サブエージェント利用なし。検査は
  `check_codex_agents` / `check_docs` / `git diff --check` が初回 rc=0。real `claude -p` は未実行

### 次の一手

1. [T-069] **ユーザー裁定待ち**: bounded supervisor 設計の 4 択 — daemon は v1 foreground 起動、child は explicit auto (不可なら停止)、pilot 中は session persistence を保持、timeout/cost 値は実装前に明示指定、という推奨を採るか。採用後は fake child の機械層から別実装 wave で着手する
2. [T-005] **ユーザー裁定待ちへ差し戻し (2026-07-21、D71)**: S-1 freeze 再発行の可否。実行すると
   holdout の `known_axes_freeze.sha256` が外れ、上書きは `V1_FREEZE_SHA256` (v1 trust root) を壊し、
   v2 追随は `_TRANSITION_V1_TO_G1` に `/known_axes_freeze/sha256` が無いため拒否される。
   **正規の道が 3 方向とも塞がっている**。推奨 = 単独では実行せず [T-063] [T-064] と束ねて裁定する
3. [T-063] **裁定待ち (新規)**: 再発行の**許容 JSON Pointer 差分契約**を確定する。親の当初案
   「差分は `frozen_at_head` と `python_version` のみ」は成立しない (known bytes が変われば
   measurement の `/implementation_hashes/known_axes_freeze/sha256` も必ず変わる)。推奨 =
   exact な許容 pointer 集合をユーザーが確定し、それ以外は厳密一致とする
4. [T-064] **裁定待ち (新規)**: legacy holdout freeze を**歴史成果物として据え置く**か、
   **s8b trust root ごと移行する**か。据え置くなら oracle 非復旧を明記する。移行するなら
   `V1_FREEZE_SHA256`・transition table・protocol golden まで含む別 wave が要る。
   holdout 再生成は `confirmed_by` (人間確認者名) を必須とするため **AI 単独では実行できない**
5. [T-065] **実装待ち (新規、要裁定)**: holdout freeze が **2026-07-18 から無効**である
   (`design_source` sha256 のドリフト、F9 型)。floor protocol 裁定記録の commit 群が
   `docs/phase3-8b-descriptor-design.md` を更新したことが原因。3 日間検出されなかった
6. [T-066] **実装待ち (新規、要裁定)**: `test_s1_measurement_freeze.py` に
   **D68 (7) の隠蔽パターンが現存**する (production generator の現行 hash を動的注入 +
   `K.build_document` を fixture の echo へ置換)。防壁変更にあたるため裁定へ回す
7. [T-067] **実装待ち (新規、要裁定)**: oracle 系テストが **refusal の増加を検出できない**
   (`test_s8b_oracle_driver.py` は floor-null / budget-null / status=refused / rc=2 しか要求しない)。
   拒否理由の exact 検査へ強化する
8. [T-068] **裁定待ち (新規)**: dangling `frozen_at_head` は **freeze 族共通の病**。S-1 の歴代 5 世代と
   holdout の計 6 個すべてが repo に存在しない。wave branch で生成 → rebase で SHA 書換え、が原因。
   恒久対応は [T-063] と同時に決める必要がある
9. [T-004] **承認済み実装 wave (単独 wave、[T-007] [T-008] を同梱)**: WAL の byte 単位 record framing と
   resume の物理修復。末尾断片が物理ファイルに残り次の `O_APPEND` が直結する。基準 HEAD から存在し
   全 campaign へ波及する。**本 wave が実装に至らなかったため、次に着手すべきはこれ**
10. [T-008] **裁定確定 (2026-07-21): payload 型を writer 側でも強制する**。[T-004] の wave に同梱
11. [T-007] **裁定確定 (2026-07-21): 未知 stage は拒否する** (fail-closed)。[T-004] の wave に同梱
12. [T-001] **承認済み実装 wave**: ruling-B 単独 (session record の issuer/env_tag 照合)
13. [T-002] **承認済み実装 wave ([T-006] を同梱)**: P-A1(a) Stage 1 + P-C3
14. [T-009] **裁定確定 (2026-07-21)**: 実装子の規律免除を `AGENTS.md` へ 1 段落追記する
15. [T-060] **[T-003] 裁定の実装分**: WAL に関する記述から「改竄耐性」「改竄不能」「証明可能」を
    使わない運用を明文化する (脅威境界の正本 = D68 (6))
16. [T-010] B-008 の再試験条件: 変わらず
17. [T-011] 限界受け入れ (viii) = floor 実測直前に最終承認 (据え置き)
18. [T-012] task-run pilot 配線提案 = 10 run または 08-03 到達時に提示 (現在 5 run)

## 2026-07-21 (5) — 裁定 9 件の確定 (発効なし・計測なし・実装は次セッション)

/rulings 経由のユーザー裁定 9 件 (ここが記録の正本)。**いずれも推奨どおりで確定**。
本エントリは裁定の記録のみで、コード・凍結成果物の変更は行っていない。

- **並行セッションとの番号衝突を繰り下げで解消した。** 本エントリは当初 `(4)` として commit し
  (`837e15f`)、`T-069` を push 判断に割り当てていた。しかし別セッションが先に `(4)` =
  bounded supervisor 設計を main へ着地させ、同じ `T-069` を supervisor 裁定に使っていた。
  ff-only が不可となったためユーザー判断を仰ぎ、**rebase 許可を得て本エントリを `(5)`、
  push 判断を `[T-070]` へ繰り下げた** (先に main へ着いた方を優先。7/20 の `D69→D70` と同作法)。
  [T-062]「重複防止の機構は入れない」の裁定どおり、機構を足さず繰り下げで処理している (2 回目の発現)
- **裁定の設計上の含意 (最重要)。** [T-068] の格下げ ((b) `frozen_at_head` を fail-closed 検査から
  参考情報へ) を採ると、**[T-005] の再発行そのものが不要になる可能性がある**。元の破損は
  「作成時点の記録が repo から消えている」ことによる ancestry 検査の失敗**だけ**であり、内容は
  健全である (63 個の source sha256 + generator sha256 + 文書の機械再構成一致が担保、D71 (1))。
  格下げすれば `known-axes-freeze-verify` は**現行ファイルのまま通り**、measurement も連鎖して通る。
  holdout の bytes も `FROZEN_MANIFEST` の literal pin も無変更で済む。
  **次の wave は brief の前にこれを実測で確認すること** (/dev-wave 段 1 の「裁定前提の実測確認」)
- **格下げが規律 2 に抵触しないかの判断根拠。** `frozen_at_head` の ancestry は CC 正しさの
  ゲートではなく provenance 検査である。かつ**歴代 6 個すべてが不在**で一度も通ったことがない
  (D71 (7b))。恒常的に赤い検査を維持しても検出力は増えない。内容の同一性を担保する検査
  (source sha256 / generator sha256 / 再構成一致) は**すべて fail-closed のまま維持する**
- [T-064] の「据え置き」は、S-1 を再発行した場合に holdout が**旧 bytes を参照し続ける**状態を
  受け入れることを意味する。ただし上記のとおり再発行自体が不要になりうるため、その場合は
  holdout の known_axes 照合は**現状のまま一致し続ける** (悪化しない)

### 消化した ID

- [T-064] legacy holdout の扱い — **裁定: 据え置き (推奨どおり)**。歴史成果物として旧 known bytes を
  参照し続け、**公式 oracle gate は当面復旧しない**と明記する。信頼の起点 (`V1_FREEZE_SHA256`)・
  世代交代の許可表・protocol golden には手を触れない。holdout の再生成は `confirmed_by`
  (人間確認者名) を必須とするため AI 単独では実行できない (D71 (3))。「非復旧の明記」は
  [T-005] の実装 wave の docs に含める
- [T-065] holdout freeze の design_source ドリフト (2026-07-18 から無効) — **裁定: [T-064] に同梱**。
  下限値の実測時の再凍結でまとめて解消する。単独で直しても再生成には人間確認が要り、
  どのみち floor 実測時に再度作り直すため二度手間になる

### 次の一手

1. [T-069] **ユーザー裁定待ち (別セッション由来、未裁定のまま引き継ぎ)**: bounded supervisor 設計の
   4 択 — daemon は v1 foreground 起動、child は explicit auto (不可なら停止)、pilot 中は session
   persistence を保持、timeout/cost 値は実装前に明示指定、という推奨を採るか。採用後は fake child の
   機械層から別実装 wave で着手する (正本 = worklog 2026-07-21 (4))
2. [T-005] **裁定確定 (2026-07-21): 単独実行せず [T-063] [T-068] と束ねて 1 wave で扱う**。
   **着手前に「[T-068] の格下げだけで破損が解消するか」を実測で確認すること** — 解消するなら
   再発行は行わず格下げのみで閉じる。解消しない場合のみ [T-063] の差分契約に従って再発行する
3. [T-063] **裁定確定 (2026-07-21): 変わってよい箇所を明示列挙し、列挙外は前世代と厳密一致を
   要求する** (推奨どおり (a))。列挙の具体案は未作成 — [T-005] の wave で起草する。
   既存の `_TRANSITION_V1_TO_G1` と同じ考え方に揃える
4. [T-068] **裁定確定 (2026-07-21): `frozen_at_head` を fail-closed 検査から参考情報へ格下げする**
   (推奨どおり (b))。[T-063] と同時に決める。内容同一性の検査は fail-closed のまま維持する
5. [T-066] **承認済み実装 wave (裁定 2026-07-21)**: `test_s1_measurement_freeze.py` の
   D68 (7) 型の隠蔽 (production generator の現行 hash を動的注入 + `K.build_document` を
   fixture の echo へ置換) を、外部固定の期待値へ置き換える
6. [T-067] **承認済み実装 wave (裁定 2026-07-21)**: oracle 系テストを拒否理由の exact 検査へ
   強化する (現状は floor-null / budget-null / status=refused / rc=2 しか要求せず、拒否理由が
   増えても緑のまま)
7. [T-070] **ユーザー判断待ち (新規、旧 [T-069] から繰り下げ)**: local main の push。
   AI は push しない規約のため判断を渡す。/rulings では推奨 = 今 push する (裁定パッケージを
   並行セッションが古い前提で扱うのを防ぐため) としたが、本裁定では未決
8. [T-004] **承認済み実装 wave (単独 wave、[T-007] [T-008] を同梱)**: WAL の byte 単位 record
   framing と resume の物理修復。基準 HEAD から存在し全 campaign へ波及する。
   **実装 wave としては引き続きこれが次の着手先**
9. [T-008] **裁定確定 (2026-07-21): payload 型を writer 側でも強制する**。[T-004] の wave に同梱
10. [T-007] **裁定確定 (2026-07-21): 未知 stage は拒否する** (fail-closed)。[T-004] の wave に同梱
11. [T-001] **承認済み実装 wave**: ruling-B 単独 (session record の issuer/env_tag 照合)
12. [T-002] **承認済み実装 wave ([T-006] を同梱)**: P-A1(a) Stage 1 + P-C3
13. [T-009] **裁定確定 (2026-07-21)**: 実装子の規律免除を `AGENTS.md` へ 1 段落追記する
14. [T-060] **[T-003] 裁定の実装分**: WAL に関する記述から「改竄耐性」「改竄不能」「証明可能」を
    使わない運用を明文化する (脅威境界の正本 = D68 (6))
15. [T-010] B-008 の再試験条件: 変わらず
16. [T-011] **裁定確定 (2026-07-21): 据え置き (推奨どおり)**。限界受け入れ (viii) の最終承認は
    floor 実測の直前に発火する。現時点では未発火
17. [T-012] **裁定確定 (2026-07-21): 試験運用を継続 (推奨どおり)**。task-run pilot 配線提案は
    10 run または 08-03 到達で提示する。**現在 5 run** (折り返し)

## 2026-07-21 (6) — [T-005] 格下げ経路も自己 hash blocker で差し戻し (D72、branch worktree-dev-wave-ruling-ac、計測なし)

worklog (5) 次の一手 2 の裁定確定分として着手したが、**段 1 の実測確認で裁定の前提が覆り、
実装せず裁定パッケージで終えた**。[T-005] は **2 wave 連続の差し戻し**。ハイブリッド標準ループ
(/dev-wave) で実施。設計判断は D72、逐語は `output/insights/2026-07-21_s1-freeze-downgrade-loop.md`。
ここには git に入らない情報だけを書く。

- **canonical 成果物は 1 byte も変更していない。** `output/s1-freeze/` の 2 本と
  `output/s8b-freeze/holdout_freeze.json` は着手前と同一 (baseline hash を wave 内で採取・照合済み)。
  本 wave の commit は docs のみ
- **段 1 の「裁定前提の実測確認」が誤った結論を出した — ただし段 2 が検出した。** 親は
  ancestry の格下げを **runtime monkeypatch** で模擬し、「現行 bytes のまま verify が通る」と結論した。
  これは「内容が健全か」としては正しいが、**実差分をモデル化していない**。codex プラン v1 が
  自己 hash blocker を指摘し、親が実測で確認して brief v2 へ全面訂正した。
  **段 1 の実測は「何を模擬したか」を明示しないと、正しく測って誤った結論に至る**
- **敵対相談 2 本がいずれも独立に NO-GO。** レンズは正しさ境界 / 整合・実効性。両者が別経路で
  同じ 2 blocker (`FROZEN_MANIFEST` / v1→g1 transition) に到達した。**D71 と同じ構図の 2 回目**
- **親の provisional 裁定 13 件のうち、否認 4 (P2′ P4 P11 P12) / 条件付き 7 / 採用 2** (c1 集計)。
  特に **(P11)「trust root と transition table には触れない」は、transition と両立しない**という
  形で否認された。**「触れない面」を宣言するときは、それが目的と両立するかを先に確認する**
- **`FROZEN_MANIFEST` を親も codex プランも見落としていた** (`test_frozen_artifacts.py:33`)。
  凍結成果物を触る wave のチェックリストに入れる必要がある
- **worklog (5) の裁定要約が D71 の制約を落としていた。** D71 (2)(c) は v1→g1 の許可 pointer に
  `/known_axes_freeze/sha256` が無いことを既に記録していたが、(5) の「格下げすれば再発行不要」は
  それを迂回する前提だった。**要約から着手せず元 decision に当たる**
- **相談が親の主張を 1 件 refute した。** 「格下げ後は別の実在 ancestor へ差し替えても受理」は
  差分としては誤り (現行実装も任意 ancestor を受理済み)。新たに失うのは
  「存在しない SHA」と「実在する非 ancestor」の拒否だけ (D72 (8))
- **worklog (5) の記述を 1 件訂正。** 「measurement も連鎖して通る」は**両サイトを格下げした場合に限り**
  正しい。measurement は自前の dangling `frozen_at_head` を持つ (`s1_measurement_freeze.py:422`)
- 検収: `check_docs` 違反なし。**実装差分が無いため変異 matrix と受入全走は本 wave の対象外** (D72 (12))。
  段 1 の baseline 実測として freeze/oracle 4 suite を走らせ `88 passed / 1 skipped` を確認している
  (これは実装の検収ではなく、着手前の現況把握である)
- エージェント工数: codex 3 本 (プラン 1 / 相談 2、いずれも gpt-5.6-sol、すべて max)。
  **実装子・レビュー子は起動していない** (実装が無いため)
- task-run: `20260721-s1-freeze-downgrade-92ee634c` (pilot 6 本目)

### 消化した ID

- **[T-063] 部分消化。** 許容 JSON Pointer の列挙は起草でき、敵対相談 2 本とも
  「S-1 JSON の semantic 差分としては過不足なし」と判定した (D72 (6))。ただし
  **repository transition の変更面はこれより広い**ため、契約全体としては未確定のまま残す
- [T-005] [T-068] は消化せず。性格を「裁定確定・承認済み」から **「ユーザー裁定待ち」へ再度変更**する。
  承認は新事実 (自己 hash blocker) により前提を失ったため、再承認が要る

### 次の一手

1. [T-071] **ユーザー裁定待ち (新規、最優先)**: v1→g1 の許可 JSON Pointer 集合に
   `/known_axes_freeze/sha256` を加えるか。加えないなら (a) 旧 known bytes を持つ歴史的 source head から
   g1 を導入する手順を仕様化するか、(b) 将来の v2/oracle 復旧が blocked であると明示的に受容するか。
   **この裁定なしに S-1 の bytes を変えてはならない** (将来の g1 が構造的に生成不能になる)
2. [T-072] **ユーザー裁定待ち (新規)**: 旧/新 artifact hash・基準 blob・許容 4 pointer・
   raw-byte 同一性検査を持つ**一回限りの transition receipt** を作り、新 S-1 2 hash と receipt hash を
   `FROZEN_MANIFEST` へ再 pin してよいか。D71 自身が要求していたが未実施
3. [T-073] **ユーザー裁定待ち (新規、設計択一)**: 格下げの実装形。
   **選択肢 A** = checker 編集 + 4 pointer transition (canonical が変わる。[T-071] [T-072] が前提)。
   **選択肢 B** = 消費側 (`s8b_oracle_driver.py`、pin されていない) で ancestry 失敗を参考情報扱いにする
   (canonical も checker も byte 不変。ただし判別がエラー文字列一致に依存し、`verify()` の
   直接 caller では破損が残る)。**推奨 = B を第一候補として再設計する** (凍結を凍結のまま保てる)。
   いずれを採る場合も `frozen_at_head` を「未検証 metadata」と明記し、observation を
   report / calibration / oracle へ構造化伝播することが条件 (D72 (8))
4. [T-005] **ユーザー裁定待ち (差し戻し 2 回目)**: [T-071] [T-072] [T-073] が決まるまで着手しない
5. [T-063] **部分消化・継続**: S-1 JSON 内の 4 pointer 列挙は確定した (D72 (6))。
   repository transition の変更面 (manifest・receipt・oracle manifest fixture・ratified g1・
   real-repo serial group) を含む契約全体は [T-072] の裁定後に確定する
6. [T-068] **ユーザー裁定待ちへ差し戻し**: 格下げ自体の可否は [T-073] に含めて裁定する
7. [T-074] **裁定パッケージ (新規、恒久設計)**: 「成果物が自分を検証する checker を pin する」設計の
   是非。checker のバグ修正が必ず canonical 再発行を強制する現状を、入力と出力だけを pin する
   設計へ分離するか (D72 (10))
8. [T-075] **裁定パッケージ (新規、原因側)**: freeze を wave branch で生成 → rebase で SHA 書換え、が
   dangling `frozen_at_head` の原因である。格下げは症状の対処であり原因を絶たない。
   生成時ガードか field 廃止かを決める
9. [T-066] **承認済み実装 wave**: `test_s1_measurement_freeze.py` の D68 (7) 型の隠蔽を外部固定の
   期待値へ置き換える。**[T-005] とは独立に着手できる** (canonical を触らない)
10. [T-067] **承認済み実装 wave**: oracle 系テストを拒否理由の exact 検査へ強化する。
    現在の拒否集合は実測でちょうど 4 件、`any(startswith(...))` しか要求していないため
    集合の変化を 1 件も検出しない。**[T-005] とは独立に着手できる**
11. [T-069] **ユーザー裁定待ち (別セッション由来)**: bounded supervisor 設計の 4 択 (正本 = worklog (4))
12. [T-070] **ユーザー判断待ち**: local main の push。AI は push しない規約のため判断を渡す
13. [T-004] **承認済み実装 wave (単独 wave、[T-007] [T-008] を同梱)**: WAL の byte 単位 record framing と
    resume の物理修復。基準 HEAD から存在し全 campaign へ波及する。
    **canonical 凍結成果物に触れないため、[T-071]..[T-073] の裁定を待たずに着手できる。
    実装 wave としては引き続きこれが次の着手先**
14. [T-008] **裁定確定 (2026-07-21): payload 型を writer 側でも強制する**。[T-004] の wave に同梱
15. [T-007] **裁定確定 (2026-07-21): 未知 stage は拒否する** (fail-closed)。[T-004] の wave に同梱
16. [T-001] **承認済み実装 wave**: ruling-B 単独 (session record の issuer/env_tag 照合)
17. [T-002] **承認済み実装 wave ([T-006] を同梱)**: P-A1(a) Stage 1 + P-C3
18. [T-009] **裁定確定 (2026-07-21)**: 実装子の規律免除を `AGENTS.md` へ 1 段落追記する
19. [T-060] **[T-003] 裁定の実装分**: WAL に関する記述から「改竄耐性」「改竄不能」「証明可能」を
    使わない運用を明文化する (脅威境界の正本 = D68 (6))
20. [T-010] B-008 の再試験条件: 変わらず
21. [T-011] **裁定確定 (2026-07-21): 据え置き**。限界受け入れ (viii) の最終承認は floor 実測の
    直前に発火する。現時点では未発火
22. [T-012] **裁定確定 (2026-07-21): 試験運用を継続**。task-run pilot 配線提案は 10 run または
    08-03 到達で提示する。**現在 6 run**
