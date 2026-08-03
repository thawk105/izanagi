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
