**緑の実測を proposal-2 へ戻す経路はあります。ただし「critic の診断も次の生成入力に使った」という brief の完了条件は、plan の手順だけでは成立しません。** campaign ID は今回も T-2581 と同一ですが、専用 submit-tree による分離は有効です。

以下、パスは特記がなければ repo root 基準です。編集・pytest・計算ノード実走はしていません。

### 1. real — critic の診断は保存されるだけで、次の生成入力へ接続されていない

- 根拠: [brief.md:11](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2588-k2-loop-roundtrip/brief.md:11) は「その診断と実測を入力にした proposal-2」を要求する。一方、[plan.md:197](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2588-k2-loop-roundtrip/plan.md:197) の還流手順は、診断逐語の保存後、測定値・whiteboard・knowledge projection から次提案を生成する。
- 現物: `p3_s4_loop.py:1237` の射影は whiteboard、knowledge_input、任意 policy_hint のみ。`:2213` の `_fold_critic_reverse` はカウンタ更新だけで、`:2486` で次回評価入口に消費される。proposal-2 は評価しないため、保存した bool も今回中には消費されない。
- **放置時の差:** 成果物は「実測と評価結果の還流」になるが、「critic 診断を次提案生成に利用した」という完了主張だけが過大になる。
- 既存範囲の最小対応: run-card:109–114 の区別に合わせ、**緑実測の還流と critic 診断・逆方向 bool の保存**として記録する。診断を whiteboard や knowledge source に追加する対応は、この固定入力契約から外れる。

### 2. refuted — 実測が型付き入力へ届かない、または率の単位が違うという疑い

plan:180–203 の写像は現物と一致する。

| 次入力 | 実測の出所 | 現物 |
|---|---|---|
| `current_perf.throughput_ops_sec` / coder の baseline | `leading_indicators.throughput_tps` | `calibrator/model.py:96` |
| `abort_rate_pct` | `abort_rate × 100` | 同 `:71`, `:97` |
| `cache_miss_rate_pct` | `llc_miss_rate × 100` | 同 `:38`, `:99` |
| `IPC_overall` | `ipc` | 同 `:47`, `:100` |
| whiteboard | 実走後 checkpoint の5フィールド | `p3_s4_loop.py:1217`, `:1964`, `:2510` |

`critic/digest.py:763–768` は committed attempt の `committed_bench` を選ぶ。`pipeline.py:1455–1468` が指標を作り、`:1516` で WAL に出す。`last_delta_pct=null` と contention「未判定」も、存在しない計測値を補わない扱いとして正しい。

**放置時の差:** この写像を実際の spawn 入力へ反映すれば、今回の実測が次提案の参照値になる。ただし plan の存在だけでは実行済みの証拠にならず、保存した次入力が完了証拠となる。

### 3. real — 停止時の扱いが「生成禁止」から「成功に数えない」へ弱まっている

- 根拠: run-card:107 と `docs/phase3-s4b-runbook.md:109` は、stop が `continue` 以外なら終了する。plan:205 は「継続生成を成功として扱わない」とし、plan:199–203 の手順には critic・次生成へ進む前の明示的な分岐がない。
- 現物: `p3_s4_loop.py:2532–2533` は評価後の停止理由を返す。`:1270` の時間予算は、1評価だけでも成立し得る。
- **放置時の差:** 停止済みの走から critic と proposal-2 を作り、固定した停止条件を超えた成果物が残り得る。
- 最小対応: 既存の `stop_reason` を読み、`continue` の場合だけ critic・次生成へ進む、と手順を明記する。新しい gate は不要。

### 4. refuted — 同一 campaign ID のため、必ず過去 terminal に skip されるという疑い

読み取り専用で現行 `default_cfg()`、指定 manifest、Pegasus marker から再導出した結果は、**`p3-s4-loop-s4-autonomous-409e13f8`**。今回は「同じになるかもしれない」ではなく、記載設定なら同じになる。

- 根拠: `ident.py:212–229` のハッシュ対象は `spec_content`、`ccbench_commit`、`search_tag`、`search_config`、`trial`。proposal の値、superproject HEAD、submit-tree path は入らない。
- `search_config` には軸・scale・records・threads・reflux・文法版・build admission policy・K2 manifest digest・Pegasus marker が入る。
- `loop.py:579` は渡された layout の WAL だけを replay し、`:589–610` で terminal 集合を作り、`:696` で skip する。
- `layout.py:595–596` と job body:39 により、専用 submit-tree の既定 output に分離される。

**放置時の差:** ID だけで成果物を区別すると新旧の参照が曖昧になる。一方、plan:221 の新規 tree・過去 WAL 非持込みを守れば、T-2581 由来の skip や出力混在は起きない。

既存の最小回避策は、計画済みの専用 submit-tree と新規 evidence root。ID を変えるための設定変更は不要。

### 5. refuted — pin／verifier の修正が今回も必要という疑い

- `p3_s4_loop.py:112` の PIN と `git ls-tree HEAD external/ccbench` は、ともに `511c9538e4e8efa54b45cda62e72389ed3b706ec`。
- `git log -L112,112` で変更元は brief 記載の `55d0f239945d34eaf39de500f076f332dc7e20b3`。
- `verifier/parse.py:323–330` は5フィールドの C record を拒否し、7フィールドを要求する。
- 同 commit から現 HEAD まで `orchestrator/verifier` の差分は検出されなかった。

**放置時の差:** この面で投入対象や受理集合を変える必要はない。今回の目的に必須となる実装変更は特定できなかった。

### 6. refuted — T-2581 の cache／IPC が残っているという反証仮説。ただし絶対的不在は未証明

指定 job root と repo insight を走査したが、**T-2581 本走に帰属する cache miss／IPC の数値は発見できなかった**。

- 残存証拠: `evidence/attempt-0001/job.stdout:223–225` は verifier 件数、713,068 tps、CV、commit 件数。
- `handoff.md:40–44` と insight README:17–20 も同じ範囲。
- insight README:75 が原本所在地とする `submit-tree/output/...` は、現在の job root に存在しない。導出先の不在だけでは打ち切らず、残存資料を継続検索した。
- **現行 brief:70–77 に「どこにも残っていない」という文言自体はない。** 歴史測定を選ぶ裁定と、T-2581 を使う可能性への問いが書かれている。

**放置時の差:** 「検索で発見できなかった」を「絶対に存在しない」へ強めると証拠の範囲を超える。また、歴史測定を使う直接の根拠は run-card:47–52 の固定入力であり、不在の証明ではない。

### 7. real／nit — plan の参照位置と拒否署名にずれがある

参照を個別に照合した。以下は正確な対象位置へ直せる箇所。成果物の数値・受理集合を変える実害までは示せないため、**nit** とする。

| plan の箇所 | 記載参照 | 現物の対象位置 |
|---|---|---|
| :29 入力 schema 全体 | adapter JSON:99 | `:32`。`:99` は `planner_direction.properties` |
| :31 hole 条件 | `p3_s4_loop.py:125` | 空行。MARKER は `:126`、SOURCE は `:127` |
| :58 重複 key 拒否 | 同 `:2274` | ファイル読込み。拒否 hook の指定は `:2281–2283` |
| :63 型構築 | 同 `:2356` | 呼出しの閉じ括弧。構築は `:2357` |
| :138 driver 呼出し | shell `:581` | 分岐条件。コマンドは `:582` |
| :168 admission 取得 | loop `:2512` | 分岐条件。取得は `:2513` |
| :180 `committed_bench` | digest `:762` | 反復開始。取得は `:768` |
| :219 skip | loop `:695` | variant ID 計算。条件は `:696` |
| :229 spec/search/trial | S4 loop `:1505` | B4 呼出しの閉じ括弧。`:1508–1515` |
| :230 `ccbench_commit` | 同 `:1512` | spec 本文。代入は `:1513` |
| :231 search_config 開始 | 同 `:1495` | `reflux` 行。辞書開始は `:1494` |
| :233 K2 identity fields | 同 `:1548` | 辞書展開。fields は `:1549–1551` |

さらに plan:62 の「bool、非整数、範囲外、重複 index は `RolePolicyError`」は、**semantic 関数単体と loader 全体を混同**している。`p3_s4_loop.py:2236` が先に output schema を検査するため、bool・非整数・負数・完全重複 item は `EventValidationError` で先に拒否され得る。根拠は adapter JSON:181–196、`codex_roles/events.py:178–186`。

**放置時の差:** 実際の拒否を想定外エラーと誤分類する可能性がある。拒否集合自体を変える所見ではない。

関数名と指定キーワードについては、manifest resolver、射影、preflight、K2 loader、digest、hydrate、job 環境変数に不一致を検出しなかった。`load_proposal_file` の実際の `coder_role` 既定値は `None` なので、plan:37 は正式署名ではなく今回の呼出し形として読む必要がある。

### 8. refuted — その他の固定事項からの逸脱

軸・整数1..1000・hole 文法・manifest・空の初期 whiteboard・scale・親の回数予算について、brief と plan に固定事項との不一致は検出しなかった。manifest bytes／source bytes の SHA-256 も run-card 記載値と一致した。

login で `--emit-planner-context` を使わず直接射影する点は、run-card の CLI 言及からの**実行方法の変更**だが、`p3_s4_loop.py:2678–2689` の site gate 順序に対応したもの。射影対象は同じである。

**放置時の差:** 上記固定入力を維持する限り、測定対象や受理集合は変わらない。T-2581 の値へ初期入力を差し替えるなら、別途「固定入力からの逸脱」と明記する必要がある。

## 総括

投入前に直すべき中心は、**brief の診断利用という完了主張と、停止時の実行分岐**です。緑実測の次入力への写像は成立し、同一 campaign ID も新規 submit-tree で分離できます。今回必要なコード変更は特定していません。実走・terminal 取得・proposal-2 への実際の入力保存は未確認です。