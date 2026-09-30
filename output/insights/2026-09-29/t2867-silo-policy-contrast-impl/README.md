# silo-function-policy 軸の生成器対照を回せるようにした — 系列台帳・slot ごとの計測 campaign・機械生成 IR の口・G_rand と (1+1)・起動器・LLM の round tool と親・report を実装し、計算ノードで LLM×C++・LLM×IR・random×IR の各 1 評価を通して見積りを取り直した (2026-09-29、[T-2867])

- 位置づけ: 事前登録の草稿 `docs/silo-policy-generator-contrast-preregistration.md` (D2263、未発効、以下「草稿」) の §5・§10 の欠ける部品の実装と、
  §10 の生死確認。起草の記録は `output/insights/2026-09-27/t2867-silo-policy-contrast-draft/README.md`。arm 構成は D2272 項 4 で 4 arm に決定済み、
  系列数 (n = 12 か 10) と発効はユーザーが決める (本 wave では決めない)。本 insight は記録で、可変状態の正本 (worklog 末尾・`docs/phase3.md`) にはしない。
- wave: branch `dev-wave-t2867-silo-contrast-impl`、起点 local main `035fc11fa` (2026-09-29 14:4x JST に開始 gate rc=0)。9 段の全段 (段 2 plan・段 3 相談 2 本・段 6 レビュー 2 本・焦点再レビュー 3 巡)。
- 逐語 (`verbatim/`): 依頼 `request.md`、段 1 brief `s1-brief.md`、段 2 plan `codex-plan.md`、段 3 相談 `codex-consult-a.md`・`codex-consult-b.md`、段 4 裁定 `s4-ruling.md`、
  実装子 `codex-author-{x,y,z}.md`、段 6 レビュー `codex-review-r1.md`・`codex-review-r2.md`、焦点再レビュー `codex-focus-{1,2,3}.md`、段 6 裁定 `s6-ruling-{1,2,3,5}.md`
  (裁定 4・6 は fix 子への依頼文の中、`s6-ruling-4-in-fix5-prompt.md`・`s6-ruling-6-in-fix7-prompt.md`)、fix 子 `codex-fix*.md`。
  裁定 7 (fix 8) と裁定 8 (fix 9) は生死確認で見つかった欠陥で、本書 §4 に書く。codex の prompt・受領証・変異の spec と結果・生死確認の script・台帳・evidence は
  wave の job dir (repo 外、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-silo-contrast-impl/`) にある。
- 記録上の注記: 段 6 の途中 (`67fb3b721`、fix 8) の `git add -A` で本 insight の `verbatim/` が実装の commit に同乗した。内容は記録物だけで、実装への影響は無い (amend はしない)。

## 0. 要約

1. **実装 (Codex author 3 本 + fix 9 回、親は docs だけ):** 政策 driver に対照の系列 identity (`contrast_cohort`・`contrast_arm`・`contrast_series` と同時検査の key、既定 cfg の bytes は不変) と
   slot ごとの計測 campaign (`contrast_slot` = `<slot>-<index>-a<attempt>`)、機械生成 IR と初期点の口 (auditor を省けるのはこの 2 つだけ、LLM arm の系列では機械 proposal を拒否)、
   stock・静的 10 µs (D2240 と同じ適用方法、既存の stock 評価関数に載せて `run_campaign` の呼出し箇所は 2 のまま)・score の slot、`--contrast-run-unit` (台帳との照合 → slot を順に測る → 台帳へ)、
   job body の `contrast` mode。系列台帳 (`orchestrator/campaign/silo_policy_contrast.py`: event 8 種、A・B の計上、次の単位、系列の終了の一元記録)、
   生成器 (`silo_policy_contrast_generators.py`: 草稿 §4.4・§4.5)、起動器 (`tools/pegasus/silo_policy_contrast_launch.py`)、round tool (`tools/silo_policy_contrast_round.py`)、
   1 原提案ごとに新しい `claude -p` を起こす親 (`tools/pegasus/silo_policy_contrast_parent.py` と指示文)、report (`silo_policy_contrast_report.py`)。
2. **段 6:** レビュー 2 本 (R1 = 正しさ境界・整合、NO-GO / R2 = 過剰・削除) の後、焦点再レビュー 3 巡 (DW-O16 の上限、3 巡とも NO-GO だが所見は巡ごとに細くなった) と
   fix 7 回。最後の実害所見 (driver の異常終了を schema 却下として A に計上) は fix 6 で閉じ、以後は親がテストと変異で閉じた。
3. **変異:** 14 件を事前登録 (段 4)。最初の probe で m14 (親が前の session を `--continue` で引き継ぐ) が生存 → 親のテストに argv の検査を足した (fix 7)。
   本走は `72810ed01` で 14/14 KILLED (1 job 364 秒) の後、最終実装 commit `4fbe4b26a` で fix 9 を壊す m16 を足して取り直し、**baseline PASSED・15/15 KILLED (期待 node と完全一致、1 job 373 秒)**
   (spec と結果は `mutation/`)。fix 8 は変異で表しにくい構造の直しなので、新旧両走 (修正前のコードに同じ結合テストを入れると同じ `binding mismatch` で赤、修正後は緑) を証拠にした。
4. **生死確認で結合欠陥が 2 件見つかった (DW-G01 がそのとおり効いた):** (a) 1 job の全 slot で 1 つの authorization session を共有し、2 つ目の slot で `binding mismatch` (fix 8)。
   (b) round tool が coder role の `{"proposal": ...}` を剥がさず preview に渡し schema 不合格 (fix 9)。どちらも単体テストは差し替えで通っていた。
5. **生死確認は 3 本とも成立した (§4):** random×IR (機械生成 IR) の評価 1・LLM×IR の 1 iteration・LLM×C++ の 1 iteration。job 1 の Elapse は 718〜759 秒、評価 job は 256〜289 秒 (§5)。
6. **見積りの取り直し (§5):** 図 1 枚 (4 arm × n = 12) は約 61〜70 node 時間、n = 10 は約 51〜59 node 時間 (いずれも job Elapse の実測単価からの換算、score と参照 job は換算)。
   LLM の 1 原提案は 5.7〜8.0 分 (4 観測)。

## 1. 依頼と裁定

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = `verbatim/request.md`): 草稿の起草 insight §5 の部品を Codex author で実装し、段階 F の生死確認の job Elapse で草稿 §11.3 の見積りを取り直す。
  発効と系列数はユーザーが決めるので、発効束 (草稿 §12) を埋めた見積りを返して止める。検査と生死確認の job 合計が 2 node 時間以上なら見積りを示して確認後に投入。本題だけ。
- 計算の確認: 段 1 で見込み約 3〜3.5 node 時間を示し、段 4 で見込み約 2.8・上限約 5.4 node 時間に改めた。ユーザーの「続けて」(18:1x JST) を投入の了承と解釈して生死確認を投入した。
- 段 4 の主な裁定 (`verbatim/s4-ruling.md`): slot ごとの計測 campaign (D2281 の iteration ごとの計測 campaign の拡張)、系列 dir は `policy_history.jsonl` の唯一の置き場、
  初期点は proposal file を経由させず driver が `enumerate_recon()` の `0000`・`0001` から組む、機械 proposal は arm と生成器名の閉じた対応で照合 (生成器の再計算による照合は足さない)、
  対照の経路は通常 loop の `check_stop`・`loop_state.json` を使わない (通常 loop の予算の数え方 [T-2881] は先取りしない)、auditor の出力形は round tool の prompt に書く (role 定義 [T-2870] は変えない)。
- 生成器の分布の逐語照合で親が見つけたずれ (比較を operand 型ごとに別候補に数え、bool を要求する node で比較が 3/4 になっていた) は fix 1 で草稿 §4.4 のとおり
  「演算子を一様に選び、比較のときだけ operand 型を一様」に直した。

## 2. 実装 (commit)

| commit | 内容 | 作者 |
|---|---|---|
| `12eb785c0` | 段 5 統合 (driver・job body、台帳・生成器・launcher、round・親・report) | Codex author × 3 |
| `98a1e894f` | fix 1: 段 6 裁定 1 の F1〜F16 (endpoint 固定の形、系列終了の一元記録、auditor veto を A の段で確定、429 後の判定、初期点の履歴番号、a の導出の一本化、critic に性能値、拒否の内訳、G_rand の演算子) | Codex fix × 3 |
| `5d0193e3a` | fix 2 (対照でない preview の文言を基点へ戻す、静的 10 µs を既存 stock 関数へ) と docs (README 登録表・対照 mode、pegasus-runbook §7.0、方策 runbook §3.3) | Codex fix・親 (docs) |
| `65a7d53b8` | fix 3: report は論理 slot ごとに最後の attempt、親と round は既存終端を冪等に、stock 不成立で初期点を測らない | Codex fix × 3 |
| `cf97b3c43` | fix 4: テストの台帳読み直し | Codex fix |
| `23f00dbf9` | fix 5: 不正な LLM 出力は A の却下 1 回、親の再開で attempt 番号を引き継ぐ | Codex fix |
| `745b343ea` | fix 6: 対照 preview の拒否を構造化 (`proposal-schema`・`auditor-gate`・`auditor-digest`)、driver の異常終了は A に計上しない | Codex fix × 2 |
| `72810ed01` | fix 7: テスト (裁定 5 の挙動、親 argv に resume・continue が無いこと) | Codex fix |
| `67fb3b721` | fix 8: slot ごとに authorization session を開く (生死確認で発見) | Codex fix |
| `4fbe4b26a` | fix 9: coder role の `{"proposal": ...}` を展開 (生死確認で発見) | Codex fix |

- 既存の受理集合: 対照を指定しない driver の cfg・action・拒否文言、job body の stock|pair|replay、`loop.py`・claim・session は不変。driver の `run_campaign` 呼出しは 2 か所のまま
  (`test_campaign.py`・`test_p3_exploration_namespace.py` の閉じた inventory の期待値は変えていない。fix 2 で段 5 の変更を基点の値へ戻した)。
- 規律 2: 全 slot が既存の gate と pipeline (検疫 → 構文 → 単独 TU → [LLM 由来は auditor の veto と digest] → 書込 → digest 再照合 → build → legacy verify 1 + 性能構成 verify 5 → bench) を通る。
  auditor を省けるのは機械生成の候補と初期点だけ (変異 m1・m4)。

## 3. 段 6 の経過

- レビュー R1 (NO-GO) は score の endpoint の形の食い違い・系列終了の欠落・auditor veto が B を消費・429 後の取り違え・テスト fixture の不一致など must-fix 5 件、R2 は同じ 2 件と縮小 8 件。
  段 6 裁定 1 で全件 real とし、fix 1 (F1〜F16) を 3 本並列に投げた。
- 焦点走の赤で見つけたもの: 既存テストの拒否文言の変更 (実装の誤り、fix 2 で基点へ戻す)、`run_campaign` の呼出し箇所の増加 (閉じた inventory の期待値は変えず、実装を既存の呼出しに載せた)。
  login の local 実行で T-2871 の結合テスト 3 件が `IZANAGI_EXPLORATION_OUTPUT_ROOT は repository 外` で赤になったのは、login の `/tmp/.git` による既知の偽赤で (計算ノードでは緑)、実装に帰属しない。
  wiring probe の赤は未 commit の新 file を数えたもので、commit 後に 65 passed。
- 焦点再レビュー 1 巡目 (NO-GO): report が retry 前後の行を全部数える (N1)・429 が終端記録の後に起きたときの重複 (N2)・stock 不成立でも初期点を測る (N4) を real、
  生死確認の checkout が AI worktree 容器の中なら job body が拒否 (N5) は refuted (容器の外に作る計画)。2 巡目 (NO-GO): 不正な LLM 出力が A の却下にならない・親の attempt 番号の衝突。
  3 巡目 (NO-GO、上限): driver の異常終了まで schema 却下として A を消費 (P1) と digest 不一致の分類 (P2)。fix 6 で閉じ、DW-O16 に従い以後は親がテストと変異で閉じた。
- 焦点走 (計算ノード、fix 8 の後): 1027 passed / 3 skipped / 失敗 0 (Elapse 48 秒)。fix 9 の後の round・親・台帳・driver のテスト: 64 passed。

## 4. 生死確認 (計算ノード、write-heavy 較正動作点、同時検査あり)

- 実行場所: AI worktree 容器の外の submit checkout 3 本 (job dir 下、detach + submodule + hydrate + lock、1 系列 1 checkout)。台帳は repo の外、
  版文字列 (cohort) は試験用の `silo-policy-contrast-test-2026-09-29` (登録版 v1 の preimage は誰も見ていない)。LLM の親は login の `claude -p --model claude-opus-5-5`
  (サブスクのログイン、API キーなし)、settings は空の JSON。
- **series 1 (HEAD `745b343ea`): 3 系列とも stock slot が certified になった後、初期点の slot で `ExecutionGuardError: authorization session binding mismatch` で停止**
  (request 35824・35825・35835、Elapse 198〜210 秒)。session は最初に認可した計測 campaign の identity に束縛される (`loop.py` の `_authorize_with_session`) が、
  1 job の slot は identity が違う。単体テストは `measure_slot` を差し替えていたので実物の session を通らなかった。fix 8 で slot ごとに session を開き、
  実物の `authorization_session`・`_authorize_measurement`・claim を通す結合テストを足した (修正前のコードに同じテストを入れると同じ `binding mismatch` で赤、修正後は緑)。
  series 1 の台帳は未終端 slot (dead-job) のまま残し、stock-0 の claim は使用済みなので series 2 以降で取り直した。
- **series 2 (HEAD `67fb3b721`):** job 1 は 3 系列とも成立 (stock・初期点 5 µs・10 µs が certified・品質正常)。random×IR は `generate` で原提案 1 が 11 秒で preview を通り、
  評価 1 が certified・品質正常 (2,111,434 tps、job Elapse 265 秒) → **機械生成 IR の 1 評価は成立**。
  LLM の 2 系列は原提案 1 で critic は成立したが、round tool が coder の `{"proposal": ...}` を剥がさず `coder-schema` の却下 (A を誤って 1 消費) → fix 9。
- **series 3 (HEAD `4fbe4b26a`、LLM の 2 系列):** job 1 成立。**LLM×IR:** 原提案 1 が critic → coder → preview → auditor (pass、違反 0) → finalize で `proposed` (6 分 2 秒)、
  評価 1 が certified・品質正常 (2,824,556 tps、job Elapse 256 秒) → **1 iteration 成立**。**LLM×C++:** 原提案 1 が同じ流れで `proposed` (7 分 27 秒)、評価 1 が certified・品質正常 (3,723,229 tps、job Elapse 289 秒) → **1 iteration 成立**。
- 系列の HEAD の束縛: 台帳 header は作成時の checkout の HEAD を持ち、job はそれと自分の HEAD の一致を確かめる。fix 9 は login 側の round tool だけの変更だが、
  系列は 1 つの HEAD で通すことにして LLM の 2 系列を series 3 で取り直した (random×IR は series 2 の HEAD へ木を戻して完了)。

| 系列 (HEAD) | job 1 Elapse | stock slot | 初期点 slot (5・10 µs) | 評価 1 |
|---|---:|---|---|---|
| llm-cpp-2 (`67fb3b721`) | 740 s | 190 s・1,355,614 tps | 261・256 s、3.96 M・3.96 M tps | (原提案 1 は fix 9 前の却下) |
| llm-ir-2 (`67fb3b721`) | 725 s | 175 s・1,375,785 | 256・260 s、3.94 M・3.93 M | (同上) |
| random-ir-2 (`67fb3b721`) | 759 s | 195 s・1,367,753 | 261・265 s、4.07 M・4.00 M | Elapse 265 s、slot 234 s、2,111,434 tps |
| llm-ir-3 (`4fbe4b26a`) | 748 s | 203 s・1,364,769 | 256・255 s、3.80 M・3.86 M | Elapse 256 s、slot 226 s、2,824,556 tps |
| llm-cpp-3 (`4fbe4b26a`) | 718 s | 166 s・1,374,750 | 256・259 s、3.83 M・3.85 M | Elapse 289 s、slot 258 s、3,723,229 tps |

- 値は各 1 観測の生死確認であって、生成器の比較や候補の良否の証拠ではない (登録した比較は発効後の本走だけが行う)。初期点が stock の約 2.8〜3.0 倍なのは偵察 (段階 D・小比較) と整合する。
- 同時検査 (D2251) 入りの stock slot は 166〜203 秒で、段階 F の直列検査の stock 単独 job (300 秒) より短い。性能構成 verify 5 本の同時検査は 65〜74 秒。

## 5. 見積りの取り直し (草稿 §11)

出所: **実測** = 上の job Elapse、**換算** = 実測の単価を系列へ当てた値。score job と参照 job は未実測で、slot の単価からの換算である。

| 量 | 式 | 値 |
|---|---|---:|
| job 1 | 実測 718〜759 s (5 本) | 718〜759 s |
| 評価 job | 実測 256・265・289 s。候補の throughput で verify の trace 量が変わるので上側を 300 s に置く | 256〜300 s |
| score job (5 session) | 5 × 評価 slot (226〜265 s、LLM×C++ は 258 s) + job の準備 31〜35 s | 1,163〜1,360 s |
| 1 系列 (B = 10 を使い切る場合) | 718〜759 + 10 × (256〜300) + 1,163〜1,360 | 4,441〜5,119 s (1.23〜1.42 h) |
| 参照 job 3 本 | 3 × (5 × stock slot 166〜203 s + 5 × 静的 10 µs の slot (初期点の 255〜265 s で置く) + 33 s) | 6,264〜7,194 s (1.74〜2.00 h) |
| **4 arm × n = 12 (48 系列)** | 48 × 1 系列 + 参照 | **約 61〜70 node 時間** |
| **4 arm × n = 10 (40 系列)** | 40 × 1 系列 + 参照 | **約 51〜59 node 時間** |

- 起草時の換算 (約 59〜69 / 49〜58) とほぼ同じ。同時検査で 1 評価が短くなった分と、初期点の slot が長い分がほぼ打ち消した。
- 含まないもの: queue 待ち、品質再測定、機械故障の retry、A の枯渇で B が 10 に届かない系列の節約 (上の値は B を使い切る上側)。
- walltime の案 (実測の最大所要への倍率): job 1 = 30 分 (759 s の 2.4 倍)、評価 job = 15 分 (300 s の 3 倍)、score job = 45 分、参照 job = 60 分。
  契約上限 = 48 × (0.5 + 10 × 0.25 + 0.75) + 3 × 1 = 183 node 時間 (n = 12)、40 系列なら 153 node 時間。
- LLM: 1 原提案は critic + coder (却下) で 5.7・8.0 分、critic + coder + auditor (提案) で 6.0・7.5 分 (4 観測、各 1 回の `claude -p`)。
  240〜720 機会 (系列あたり 10〜30、LLM 24 系列) × 5.7〜8.0 分 = 直列 23〜96 時間、同時 4 親の理想で 6〜24 時間。週上限に当たるまでの機会数は測っていない。

## 6. 検査の費用 (本 wave)

- 生死確認の job: series 1 の 3 本 (614 s)、series 2 の job 1 3 本 + 評価 1 本 (2,489 s)、series 3 の job 1 2 本 + 評価 2 本 (718 + 748 + 256 + 289 = 2,011 s) = 5,114 s ≈ 1.42 node 時間。
- 開発の検査: 焦点走 9 回 (計算ノード分は各 30〜48 s)、変異 probe 2 本 + 本走 2 本 (402・370・364・373 s)、side run 1 本、全史 provenance 1 本 = 約 0.6 node 時間。受入の結果は worklog のエントリに書く (DW-S04)。

## 7. 残るもの

- 発効 (草稿 §12 の発効束の記入、系列数の選択) はユーザー判断。進化×IR は計算で回しておらず、固定入力の試験だけで確かめた。score job と参照 job (静的 10 µs を含む) は計算ノードで未実走。
- report は台帳の読込と判定まで試験で確かめたが、実台帳での 1 通しは本走の後になる。
