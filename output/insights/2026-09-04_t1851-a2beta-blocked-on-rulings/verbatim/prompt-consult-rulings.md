単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-04_t1851-a2beta/s1-brief.md` — 本 wave の親 brief。読めなければ即停止
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-04_t1851-a2beta/s4-adjudication.md` — 本 wave の段 4 裁定 (裁定パッケージ 3 件を含む)。読めなければ即停止
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-04_t1851-a2beta/refs/a2alpha-README.md` — 直前 wave (A2α) の成果。**2 節・3 節・11 節・13 節・14 節が主たる検査対象**。読めなければ即停止
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-04_t1851-a2beta/refs/a2alpha-s4-adjudication.md` — A2α の段 4 裁定 (E1 の分析と分割の根拠)。読めなければ即停止
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-04_t1851-a2beta/refs/a1prime-s4-adjudication.md` — A1' の段 4 裁定。**3 節が E1〜E4 の境界 signature の正本**。読めなければ即停止
6. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-04_t1851-a2beta/refs/a2alpha-decisions-fragment.md` — A2α が書いた決定 2 件 (未 land)。読めなければ即停止
7. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-04_t1851-a2beta/refs/decisions-verbatim.md` — 確定裁定の逐語 (D1113 / D1193 / D1194 / D1341 / D1530 / D1533 / D1522 / D387)。読めなければ即停止

作業 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a` (branch `worktree-dev-wave-t1851-unit-a`、tip `57154c1dd`) である。**所見は必ずこの worktree の現物コードで裏を取れ。** 主な現物は `orchestrator/campaign/s8b_attempt_registry.py`、`orchestrator/campaign/attempt_registry_core.py`、`orchestrator/campaign/s8b_attempt_profile.py`、`orchestrator/campaign/s8b_holdout_admission.py`、`orchestrator/campaign/s8b_floor_attempt_launcher.py` と、それらの test (`orchestrator/tests/test_s8b_attempt_registry.py`、`test_attempt_registry_core_s8b_profile.py`、`test_s8b_floor_attempt_launcher.py`)。

## 目的

これは自分たちのコード (試行台帳 attempt registry の世代別 v2 と、その terminal 行を封印証拠から導出する設計) の設計レビューである。直前 wave (A2α) がユーザーへ返した裁定パッケージ 3 件について、ユーザーは「別系統モデルに相談したうえで親が決めてよい」と委任した。あなたの仕事は、各件について**どの選択肢を採るべきか**を、現物のコードと確定裁定に照らして根拠付きで推奨することである。前 wave の推奨を再説明する仕事ではない。**前 wave の推奨が現物と食い違う箇所があれば file:line で示せ。**

## 裁定パッケージ (本 wave の s4-adjudication.md「ユーザーへ返す裁定パッケージ」と同文)

1. **E1 の境界 signature を補正してよいか。** A1' 段 4 裁定 3 節が固定した 2 つの封印 terminal API (`record_sealed_*_terminal`) は観測・封印記録・終了時刻しか受けず、同じ裁定が承認した「起動層所有の生の事実 (probe / classification receipt / throughputs / exec failures / rep evidence) から status / reason / primary value を再導出し、自己申告 field は比較にだけ使う」を実装できない、と A2α の 3 者 (plan / レンズ A / レンズ B) が結論した。選択肢は (推奨) 起動層が生の事実を snapshot して発行する evidence-bound handle を第 9 の境界として追加し resume 可能な durable evidence digest も持たせる / (代案 a) 2 つの sealed API へ `probe_outcome` / `throughputs` / `execution_failures` / `repetition_evidence` の keyword-only 引数を直接足す / (代案 b) 境界を変えず E1 を単位 C (起動層) と同じ変更単位へ送る (D1530 の形)。併せて `record_sealed_classified_failure_terminal()` は呼び手 0 件であり、単位 C で呼び手を名指しできるか API を落とすかを land 前条件にする。
2. **E1 の分類 policy の権威をどこに置くか。** `expected_use_perf` を verified mode / perf-preflight evidence へ束縛するか v2 台帳を単一 mode に限定するか、`probe_outcome` を計測前・計測後の組へ広げるか計測前 probe の session を v2 台帳の対象外と明示するか、`repetition_evidence` を到達可能にする起動層の sink をどの変更単位に置くか。3 点とも起動層 (単位 C) の所有面である。
3. **v2 の分類 claim / 回復 row を marker capability で囲むか。** A2α は境界どおり囲まず、束縛される側とされない側を exact に pin して非束縛の集合を明記した (A2α decisions fragment の 2 件目)。

## 検査の軸

次を必ず全部見て、見た結果を書け。「前 wave の推奨どおりでよい」も結論として有効である。

1. **裁定 1 の 3 択を現物で比較せよ。** それぞれについて (a) 変更が及ぶ file と関数 (file:line)、(b) 受理集合が広がるか狭まるか、(c) D1113 (呼び手が値を選べる形を避ける) と D1530 (未接続 interface の権威束縛は本番の呼び手を繋ぐ変更と同じ単位で行う) との整合、(d) 単位 C の scope を先食いしないか、(e) 見積り changed LOC (A2α README 10 節の「2 wave 連続で下振れ」を織り込む)、を書け。evidence-bound handle 案は「第 9 の境界」を A1' の 8 signature に足す形だが、その handle を誰が作り (起動層)、誰が検証し (台帳層)、resume 時に何を読み直すかを、現物の `s8b_floor_attempt_launcher.py` の token open 以後の流れ (A2α README 2 節が挙げる行) に当てて具体化せよ。
2. **裁定 1 で (代案 b) を選んだ場合の帰結を書け。** 単位 A に残る作業は 0 になるか。v2 terminal の二層拒否 (A2α decisions fragment の 1 件目、署名 `[s8b-v2-terminal] v2 terminal requires the sealed evidence API`) と E2 の理由語彙 4 語の active 化が単位 C へ移ることで、B2 / D1 の着手順序に影響が出るか。
3. **裁定 2 の 3 点について、それぞれ「v2 台帳側で今決める」べきか「単位 C の brief へ送る」べきかを分けよ。** 台帳側で今決めないと v2 の schema や validator が後で壊れるものがあれば、それを名指しせよ。`repetition_evidence` は起動層から到達不能 (A2α README 3 節) であり、DW-O13 (到達不能な入力を要求する validator は採用しない) が拘束する。
4. **裁定 3 について、囲む/囲まないの受理集合の差を現物の `_atomic_update()` と marker 経路 (`_atomic_update_with_consumption_marker`) で示せ。** 囲まない場合に v1 より広くなる形が本当に無いか、囲む場合に既存の v1 経路・test が壊れないか。
5. **前 wave の推奨の出所を疑え。** A2α README 13 節の (推奨) はレンズ A の推奨をそのまま採ったものである。レンズ A の根拠が現物のコードで裏付けられているか、それとも「あるべき設計」の主張か。裏付けが無い部分は「根拠不足」と書け。

## 制約

- **read-only である。** 書込み可能な tmp が無いため pytest の実走は要求しない。静的検査でよい。テスト実測は親が行うので、走らせていない検査を緑と書くな。
- 予算が尽きそうなら、途中結論を下の出力形式どおりに書いて終われ。無出力が最悪である。
- 出力へ結合文字 U+0300〜U+036F を使うな。
- 正しさゲートを緩める方向の提案 (verifier の省略、自己申告値の無検証受理) は選択肢に含めるな。

## 出力形式

見出しはすべて `#` 2 個 (H2) で書く。`###` 以下の見出しを使ってはならない。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。

## 裁定 1 の比較表と推奨

3 択それぞれの (a)〜(e) と、推奨する選択肢 1 つとその根拠。

## 裁定 1 で代案 b を選んだ場合の帰結

## 裁定 2 の推奨

3 点それぞれについて「今決める / 単位 C へ送る」と、今決める場合の決め方。

## 裁定 3 の推奨

## 前 wave の推奨の根拠の裏付け状況

裏付けあり / 根拠不足 を項目ごとに file:line 付きで。

## 総括

各裁定の推奨を 1 行ずつ、計 3 行。続けて、親が裁定する前に確かめるべき現物の事実があれば 3 件以内で。
