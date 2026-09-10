# [T-287] 裁定パッケージ — checkpoint 値チャネルの残余 4 件

本 wave (branch `worktree-dev-wave-t287-checkpoint-values`、実装 commit `02a5cf9`) が閉じたのは
**checkpoint 復元境界 (`state_from_dict`) だけ**である。段 3 / 段 6 の敵対子が独立に見つけた
real 所見のうち、ユーザー裁定 (worklog (115) 択 (a)) の射程外にあるものをここへ返す。
親は実装せず、設計択一として提示する。

---

## 1. producer 側が値域を検査しない (自己汚染 checkpoint)

**所見 (段 3 レンズ A §1 / レンズ B B-01 が独立に指摘)**

`assert_closed_proposal_schema()` (`orchestrator/campaign/projection_guard.py:273-315`) は
proposal の **key 集合しか**検査しない。core / sort / trigger の 3 driver は
`load_proposal_file()` で `direction` / `magnitude` を無検査のまま `PlannerProposal` へ移し、
`project_whiteboard()` → `state_to_dict()` がそのまま永続化する。

- core: `orchestrator/campaign/p3_s4_loop.py:733-744`
- sort: `orchestrator/campaign/p3_s4_loop_sort.py:282-300`
- trigger: `orchestrator/campaign/p3_s4_loop_trigger_gating.py:583-601`

8c だけは `parse_planner()` (`p3_autonomous_workload_trial.py:296-321`) で 3+3 語に閉じており、
**driver 間で実効境界が一致していない**。

本 wave の変更後、完全な key 集合を持つ `direction="sideways"` 等は driver に受理されて
checkpoint へ書けるが、**次回 resume で同じ driver が自分の checkpoint を拒否する**。
閉包ではなく「自己汚染を次回だけ発見する」非対称が残る。

**成果物影響:** human-supervised driver では 1 試行目の台帳は保存されても resume が停止し、
以後の試行・WAL 台帳が欠落する。

**択一**

- (a) 3 driver の `load_proposal_file` に同じ値域検査を置く (ingress で閉じる)
- (b) `project_whiteboard()` に置く (保存直前で閉じる。1 箇所で済むが proposal 受理は緩いまま)
- (c) 置かない (非対称を許容し、resume 時の停止で気づく設計とする)

親の推奨は **(b)**。`project_whiteboard` は 3 driver が共有する単一の合流点であり、
`_WB_VALUE_DOMAINS` をそのまま再利用できる。ただし in-memory 経路の受理集合を狭める変更なので、
事前登録変異と正例テストを伴う独立 wave が要る。

---

## 2. `layer3_report.py` の独立 reader と手動 runbook の raw whiteboard 経路

**所見 (段 3 レンズ A §5 / レンズ B B-04 が独立に指摘)**

`orchestrator/campaign/layer3_report.py:391-410` は `loop_state.json` を**直接**読み、
whiteboard が `list[dict]` であることしか検査しない。`state_from_dict()` を通らない。
`orchestrator/campaign/layer3_schema.json` も 3 値を**任意の string** として受理する。
読み取った値はそのまま層 3 材料レポートの `whiteboard` に入り、内容 hash が `wb:` source-ref になる
(`layer3_report.py:451-471`)。既存 fixture が `direction="up"` / `result="ok"` を使っていること
(`orchestrator/tests/test_layer3_report.py:387-390`) が、この独立 consumer が別の値域を
現に許している直接証拠である。

さらに手動 runbook は raw `loop_state.json.whiteboard` を planner 入力に使うことを許している。

- `docs/phase3-s4b-runbook.md:47-51`
- `docs/phase3-s5-sort-runbook.md:46`
- `docs/phase3-s8a-trigger-runbook.md:50-61`

つまり `state_from_dict()` は prompt 射影の唯一の関所ではない。

**成果物影響:** resume が拒否する値でも層 3 材料レポートは受理し、任意値を含む report と
内容由来の `wb:<hash>` 参照を生成する。certified 選択は不変でも、**レポートの受理集合と
参照集合が変わる**。

**択一**

- (a) 共有 validator を作り、`layer3_report` と `state_from_dict` の両方から呼ぶ
- (b) `layer3_schema.json` に enum を書く (schema 層で閉じる。runbook 経路は閉じない)
- (c) 閉じない。ただし「checkpoint 値を成果物まで閉じた」という主張を今後もしない

親の推奨は **(a)**。ただし `test_layer3_report.py` の `up` / `ok` fixture を書き換える必要があり、
既存テストの期待値変更を伴うため独立 wave の裁定が要る。

---

## 3. in-domain 改竄は値域検査では防げない (origin 束縛 / integrity の要否)

**所見 (段 3 レンズ A §4)**

親 brief は「全 `small` + 同一 `direction` の改竄で早期 `converged` する」を本 wave の根拠に挙げたが、
`small` / `increase` / `decrease` / `success` / `fail` は**すべて許可値**である。
例えば既存の `rejected` を許可値 `fail` に書き換え、方向を `increase`、magnitude を `small` に
揃える改竄は、本 wave の検査を**完全に通過する** (`check_stop()` は `result != "rejected"` を
評価済みとして扱う: `orchestrator/campaign/p3_s4_loop.py:335-340`)。

これは値域では閉じられない integrity / origin の問題であり、(99) の原問題が挙げた
**entry 件数上限・`iteration` 整合 (単調性・`state.iteration` との一致)・campaign/run origin 束縛**が
これに対応する。本 wave の裁定 (択 (a)) はこれらを含んでいない。

**成果物影響:** human-supervised driver では、in-domain 改竄で後続試行数と WAL 台帳を今も変えられる。

**択一**

- (a) `iteration` 単調性 + `state.iteration` との整合 + entry 件数上限を `state_from_dict` に足す
- (b) campaign/run origin を checkpoint に束縛し、別 campaign の checkpoint 流用を拒否する
- (c) checkpoint 自体に integrity (HMAC 等) を付ける
- (d) 実施しない (計測規律が並行実行を禁じており、改竄は運用外と見なす)

親の推奨は **(a) → (b) の順**。(a) は既存の型契約の延長で安く、(b) は D39 の
「checkpoint は WAL でなく loop 状態の投影」という位置づけと整合する。(c) は鍵管理が要り過剰。

---

## 4. `state_from_dict` の既存エラーが未信頼文字列を下流へ運ぶ

**所見 (段 6 レビュー A A-01)**

本 wave が**新設した**値域エラーは未信頼値を再掲しない (field 名・entry index・許可集合・型名だけ)。
しかしそれより**先に発火する既存防壁**は入力をそのまま例外へ入れる。

- top-level 未知キー本体を `{unknown}` で再掲: `orchestrator/campaign/p3_s4_loop.py:418-420`
- whiteboard 未知キー本体を `{extra}` で再掲: `:426-429`
- `delta_pct` の任意値を `{delta!r}` で再掲: `:430-434`
- `int()` / `float()` の変換失敗も入力を組み込み例外へ含めうる: `:435,449-451`

これらは 8c の `_whiteboard()` / driver 再ロードから伝播し、捕捉側は `str(exc)` を
`attempts.jsonl` の `supervisor-error.message` と `report.json` の
`fatal_error.message` / `cells[].error.message` へ保存する
(`p3_autonomous_workload_trial.py:739,1106-1118,1185-1186`)。

**本 wave では実装しない。** 理由は 2 つある。

1. これらのメッセージは**取り込み元 main (58cd6ff) に既存**であり、本 wave が作った defect ではない。
   本 wave は受理集合を狭めるだけでこの経路を悪化させていない。
2. 修正には**既存テストの期待値変更**が要る。
   `orchestrator/tests/test_p3_s4_loop.py::test_state_from_dict_rejects_unknown_top_level_field` は
   `assert "sweet_spot" in str(e)` として未信頼キー名の再掲を**明示的に要求している**。
   これは実装子契約が禁じる領域であり、独立の受理集合裁定を伴う。

**成果物影響:** certified 受理集合は拡大しないが、注入文字列が台帳・レポートの error message を
攻撃者選択値に変え、下流 AI への運び屋になる (規律 6)。

**択一**

- (a) 未信頼値を redact し、診断は key の**個数と位置**だけにする (既存テストの期待値を変える)
- (b) 未信頼値を長さ上限付きで `repr` し、制御文字と改行を除去する (診断性を残す)
- (c) 例外文はそのままにし、`p3_autonomous_workload_trial` の**保存側**で redact する
- (d) 実施しない

親の推奨は **(c)**。診断は開発者の手元では有用で、成果物 (台帳・レポート) に載る瞬間だけ
redact すればよい。境界が 1 箇所に閉じ、既存テストの期待値も変えずに済む。

---

## 5. 段 8 自己改善候補 — `DW-G05` に「防げることの確認」を足したいが予算が無い

**候補 (本 wave で実測した作法の欠落)**

`DW-G05` は「実装しない・放置した場合に成果物のどの値・受理集合・参照がどう変わるか」を
1 行書けと定める。本 wave の親 brief はその 1 行を書いたが、**その影響は当の変更では止められない
ものだった** (上記 3 の in-domain 改竄)。加えて「certified 選択が変わる」も現行承認経路には
実行経路が無かった。`DW-G05` は「書け」としか言っておらず、「**その変更が実際にその影響を
止めるか**」「現行承認経路で発火するか」を確認させない。段 3 の敵対レンズが両方とも反証したので
実害には至らなかったが、敵対子を省ける軽量版ならそのまま台帳に残っていた。

追記したい文 (2 行、約 274 bytes):

> **その 1 行は当該変更が実際に止める経路に限る。** 変更後も同じ改竄・欠陥が成立する例を根拠にしない。
> 影響が現行の承認済み経路で発火しないなら、発火条件と現行の実行経路の有無を併記する。

**予算で入らない。** `docs/dev-wave/**` の合計は **25196 / 25200 bytes** (hard ceiling) で、
残りは 4 bytes である。自己改善契約は「予算のために安全義務を削除・弱化してはならない」
「予算に収まらなければ reference へ統合し、それでも意味等価にできなければ変更を止めて
ユーザー裁定へ返す」と定めるので、**親は編集を撤回してここへ返す**。

**択一**

- (a) 発火実績のない L2 節を 1 つ剪定して枠を作る ([T-313] の裁定どおり「発火実績なし ×
  機械検査で義務代替済み」の両条件を満たすものに限る)。**削除の実施はユーザー裁定に限る**
- (b) doc へ入れず、本 wave の worklog 記録だけに留める (次の wave は読まないので実効性は無い)
- (c) hard ceiling を上げる (自己改善に含めず理由付きの独立審査。memory の「上限を上げない」方針に反する)
- (d) `DW-G05` の既存文を意味等価に縮約して枠を作る

親の推奨は **(a)**。ただし剪定対象の選定自体がユーザー裁定を要するため、本 wave では実施しない。
(d) は既存の安全義務文を触るので、意味等価性の担保コストが追記の価値を上回ると判断した。

---

## 6. 受入全走の省略条件が repo 全体走査型の gate と噛み合っていない

**所見 (本 wave の land 阻害から実測)**

[T-407] の赤 (`ruleops.py inventory` が非 UTF-8 の証跡 blob を拒否) を持ち込んだ wave は、
worklog に「probe と login 側 controller だけ。したがって**変異 matrix と受入全走は対象外**とする」と
書いて全走を一度も回していない。一方、赤くなった
`test_real_checkout_independent_maximum_package_and_runner_preflight@real_repo` は
**repo の実チェックアウト全体を走査する型**の gate であり、自差分が触らないファイルでも落ちる。

つまり「自差分が触らない領域なら全走は要らない」という射程判断が、この型の gate と噛み合っていない。
証跡ファイルを 1 個足すだけの commit でも repo 全体走査型 gate は壊せる。

さらに land 経路 (`tools/dev_wave_land.py`) は `--tested-main-sha` / `--tested-wave-tip-sha` を
受け取るだけで**受入結果を検証しない**ので、検知器が赤でも land は機械的に通る。
検知と land 阻止が繋がっていない。

**成果物影響:** local main が赤のまま進み、後続の全 wave が `DW-STOP` で止まる
(本 wave が実際に止まった)。緑を前提とする受入の基準線が失われる。

**択一**

- (a) 受入全走の省略条件から「repo 全体走査型 gate を含む suite」を除外する
  (= docs/probe だけの wave でも、その型の gate は必ず回す)
- (b) `dev_wave_land.py` が受入結果の証跡 (test 出力の digest と rc) を受け取り、
  自己申告でなく検証する
- (c) 全 wave で受入全走を必須にする (省略条件を廃止する)
- (d) 現状維持 (waiver 運用で凌ぐ)

親の推奨は **(a) → (b) の順**。(a) は安く、今回の混入経路を直接塞ぐ。(b) は land 側の
根治だが、証跡の受け渡し設計が要るので独立 wave が要る。(c) は計算資源を食う割に
(a) 以上の効果が薄い。

**なお本 wave は、この裁定が出るまでの暫定として既知赤 waiver W1 を適用して land した**
(条件・失効は worklog 末尾エントリが正本)。waiver は [T-407] の land で自動失効する。

---

## 記録上の訂正 (本 wave の親 brief の誤り)

段 3 の敵対検証が反証した親の過大表現を、記録として残す。

1. 「全 `small` + 同一 `direction`」の早期収束攻撃は**本修正では防げない** (上記 3)。
2. 「予算超過」ではなく「`MAX_ITER` / wall budget の**上限まで消費**」。
   `check_stop()` は予算を収束より先に検査する (`p3_s4_loop.py:325-340`)。
3. 現行承認経路 (8c は `MAX_APPROVED_GENERATIONS=1` + fresh checkpoint 必須) では、
   3 連続 streak が成立せず、terminal report にも layer3 renderer にも `selected` field が無いため、
   **試行数変化も「最終 selected の変化」も実行経路がない**。実害が実在するのは
   human-supervised driver の後続試行数と WAL 台帳である。
4. on-disk checkpoint 3 件の走査は「**現存 tracked specimen の互換確認**」であり、
   任意 `run_root`・programmatic `CampaignLayout`・archive・別 worktree・将来 producer への
   一般化ではない。
5. `project_whiteboard` の production 呼出は 12 箇所ではなく **15 箇所** (core 6 / sort 4 / trigger 5)。
