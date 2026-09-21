# 段 4 裁定 — plan v2 と変異の事前登録 (2026-09-21 21:3x JST)

入力: `s1-brief.md` (P1〜P9)、`s1-pin-closure.md`、`codex/plan.md` (段 2)、`codex/consult-A.md` (レンズ A 正しさ境界、条件付き GO、must-fix 2)、
`codex/consult-B.md` (レンズ B 過剰・削除、条件付き GO、must-fix 2)。段 4 直前の再走査: local main は `36fb14a3d` のまま (wave 開始後 0 commit)、
決定台帳の末尾 D2210 は開始前から。裁定 inbox に wave 開始後の控え `2026-09-21-vldb-direction-verdicts.md` (21:17) が 1 本 → 下の P10。

## 所見の裁定

| 所見 | 裁定 | 採否・処置 |
|---|---|---|
| A-1 図中文字全体の禁止主張検査が無い | real (must-fix) | 採用。両図とも caption と全可視 `Text` (実 artist) を走査する禁止句 test を置き、正常 Figure の題・軸へ違反句を 1 つ足した負例で赤になることを確かめる。禁止句は肯定形の列挙 (否定の固定文を誤検出しない)。 |
| A-2 fig15 の重要な限定が caption だけ | real (must-fix、F872 同型) | 採用。fig15 は図中に短い注記 (下の「fig15 の形」) を実描画し、`fig.findobj(Text)` で存在を検査し、各注記を消す変異で赤。 |
| A-3 / B-2 曝露の生値 60 点で FC §2 の 95% CI を代替する説明は不成立 | real (B は must-fix) | 採用 = B の最小案。曝露は散布図・平均 marker・第 2 数値軸を描かず、**稿 §2.2 / §2.6 の記録値を数値の列として**添える (推論区間を新設しない)。README の「作図規約への適合」§2 に「曝露は記録した記述値で、区間を付けず推論に使わない (稿の表の逐語)」と局所の適用判断を書く。 |
| A-4 / B-6 P9 の「未確認」 | real (nit) | 採用。P9 = 台帳に登録しない (被覆 98.18%、余裕 2,459 node、親の実測)。条件分岐を計画から外す。 |
| B-1 fig15 の測定条件が caption・図に出ない | real (must-fix、FC §6) | 採用。W1〜W4 の `bindings.workload_argv` (4 block で一致を要求) から caption の `Conditions:` 文を作る (48 threads、10,000 records、Zipf 0.9、read ratio 50、rmw 0、max operations 10、3 s、TRACE=1 build、pin e9e477ca + X/P + witlight patches、Pegasus compute nodes、4 blocks)。caption test に条件の期待文字列。 |
| B-3 子の全 test 緑を親の作図・README より先に要求できない | real (should) | 採用。子の期待赤 = 着地 test (`test_landed_fig14_*`、`test_landed_fig15_*`) だけ。それ以外は子の自走で緑。親が作図 → README 収録 → 全関連 test の順。test 所要は親が login で実測し、追加分の合計が 60 秒を超えたら段 6 で縮める。 |
| B-4 failure / indeterminate の一般集計 | real (should、過剰) | 採用。全 240 走が `rc=0` かつ verifier (rc, status) ∈ {(0, `no-g2`), (1, `g2`)} でなければ早期拒否。k = `status == "g2"`、N = m = decisive_m = 60 を再計算して summary と照合。一般集計機能は作らない。 |
| B-5 不完全 bundle の全 6 組 | real (nit) | 採用。新図は全欠落 + 各 1 file 欠落 (3 例) に縮める。fig9 の既存 test は変えない。 |
| B-7 「結果節に図 2 枚が入る」は過大 | real (nit) | 採用。完了表現は「結果節で使える図素材 2 枚 (再現・caption・provenance・README 節付き)」。results 稿・版へは組み込まない。 |
| B P7 (2 panel) 反対 | real | 採用 = fig15 は 1 axes (下記)。 |

refuted: なし。plan の fig15 provenance に 240 走の縮約 `records` を持たせる案は、B-2 の採用で曝露の生値を描かなくなるので**不採用** (過剰。repo 側閉包は provenance に記録した arm 統計・block 別 k/m・書式文字列から caption / artist を作り直す自己整合、外部側閉包は 5 原本からの再導出一致、の射程を README に明記)。

## plan v2 (plan.md からの差分だけ)

### fig14 (`plot_a1_sized_paired.py`)

- plan §1・§2 を採用。attempt-0001 の定数名・値・挿入順、`load_leaf` 返り値の 9 key と値、`_caption` 出力、描画、CLI の既定と記録 argv は不変。
- attempt-0002 だけ: `data["attempt"] = "attempt-0002"`、panel 題を 3 行 (現行題 / `variance_plan_breach=true|false` / `sd <値> tps; planned sigma <値> tps`、比は作らない)、
  **図の上端に 1 行の図レベル text** で `attempt-0002` と「attempt-0001 とプールも比較もしない」旨を実描画 (凡例と重ねない)。値は描かない。
- caption は plan §1 の `_caption_attempt2` (固定文 2 つ + 既存 `FIXED_LANE` / `FIXED_SCOPE` / `COMPARISON_WARNING`、workload ごとの breach・sd・planned sigma、Conditions は data から)。
- 禁止句 test (A-1): caption + 可視 Text。肯定形の例: `reproduced`、`reproducibility confirmed`、`replicates attempt-0001`、`pooled estimate`、`difference between attempts`、`ratio to attempt-0001`、`overlap with attempt-0001`、`breach caused by`、`because of the breach`、`improvement`、`regression`、`significant`。
- test は plan §2 の一覧から `test_landed_fig14_rejects_missing_or_partial_bundle` を全欠落 + 単独欠落 3 例に縮める。

### fig15 (新規 `plot_mocc_witlight_four_arm.py`)

- **形 (P7 改訂):** 1 axes の forest。縦に 4 arm (上から `on / BACK_OFF=0`、`off / BACK_OFF=0`、`on / BACK_OFF=1`、`off / BACK_OFF=1`)、横軸 `G2 signal detection rate (%)`、点 = k/m、横線 = Clopper–Pearson 両側 95%。
  右側の予約領域に arm ごとの数値列: `k/m`、率、CP 区間、`mean commits per run` (稿 §2.2 の逐語 `613,741.5` 等)。BACK_OFF ごとに `on/off exposure ratio 0.8636` / `0.8450` を 1 行。
  図中の短い注記 (実描画必須、文言は子が layout に合わせてよいが次の 4 要素を含む): (i) `non-certifying` と TRACE=1 build、(ii) commits は `exposure, not performance`、
  (iii) 片側 Fisher (on が低い方向、未調整) `p = 0.500` を BACK_OFF=0 / 1 で、`not equivalence` と `power 0.105` が計算値であること、(iv) `G2 signal` は verifier の検出で `root cause` を同定しない。
  smoke を含めないこと・4 block は caption と注記のどちらかに (caption 必須)。
- 集計は B-4 のとおり早期拒否型。CP・Fisher は plan §3 の標準ライブラリ実装。
- provenance: `tracked_inputs` (caption_source 1 件)、`external_inputs` (5 件、root 相対 path・kind・sha256)、`source_inputs` (summary が記録する原保存先 path)、`measurement_conditions`、
  `arms` (統計と書式文字列)、`blocks` (block × arm の k/m と hostname)、`comparisons` (Fisher 2 表と p)、`exposure_ratios`、`artist_series` (実際に渡した値と文字列)、`caption`、`outputs`、`reproduction`。240 走の `records` は持たない。
- test は plan §4 から次を変更: `test_commit_mean_uses_all_runs_of_each_arm` は残す、`test_failure_and_indeterminate_are_not_no_g2` → `test_failure_or_indeterminate_is_rejected`、
  `test_rendered_artists_equal_provenance` は forest の点・CP 端点・数値列の Text、禁止句 test (caption + 可視 Text、否定の固定文は許す、題へ違反句を足した負例)、
  `test_landed_fig15_rejects_missing_or_partial_bundle` は全欠落 + 単独欠落 3 例。
  実証拠 test は 2 本に分ける: `test_real_evidence_matches_results_document_when_root_present` (着地物に依存しない。稿 §2.2 / §2.3 / §2.6 のセル逐語一致・layout) と
  `test_landed_fig15_external_closure_when_root_present` (着地 provenance の外部閉包)。skip は「外部 root が存在しない」ときだけ、root が在って file が欠ける・読めないのは失敗。
  禁止句の肯定形の例: `equivalent`、`equivalence established`、`no difference`、`no effect`、`no witness effect`、`absent with witness on`、`throughput`、`performance improvement`、`faster`、`slower`、
  `root cause identified`、`real anomaly confirmed`、`torn read confirmed`、`MOCC is certified`、`witness is certified` (否定の固定文 `non-certifying`・「certified flags do not certify」等は許す。単語単位の禁止はしない)。

### 共通

- 実装子 2 本は所有を分ける: 単位 A = `tools/plotting/plot_a1_sized_paired.py` + `orchestrator/tests/test_plot_a1_sized_paired.py`、
  単位 B = `tools/plotting/plot_mocc_witlight_four_arm.py` (新規) + `orchestrator/tests/test_plot_mocc_witlight_four_arm.py` (新規)。docs・README・図の成果物・台帳・他 file は編集しない。
- test file は plain runner (`if __name__ == "__main__": sys.exit(_run())`、既存 A-1 test と同型) を持ち、子は `python3 <test file>` で自走する (pytest を `-c` で呼ばない)。
- 追加 test の matplotlib 実描画は各図 4 回以内を目安 (layout 正例・artist 照合・CLI・禁止句負例)。数値 test では Figure を作らない。
- **P10 (新規):** 裁定 inbox `2026-09-21-vldb-direction-verdicts.md` 項 4 (実験の計算投入は都度ユーザー確認。開発の検査が対象かは確認中)。本 wave は実験の計算を使わない
  (作図・生成器・test は login)。計算ノードを使うのは受入 (と必要なら焦点走の dispatch) だけで、**最初の計算ノード投入の直前に同 inbox と記憶 `experiment-compute-needs-user-confirmation` を再照会**し、
  「開発の検査も確認対象」と決まっていれば見積りを示してユーザー確認を取ってから投入する。未決なら login で済む検査を先に全部済ませ、受入は投入前に判断する。

## 変異の事前登録 (DW-M01、実装前。位置は実装後に逐語 anchor で確定し、単一理由性を確認できない候補は登録から外す)

| # | 対象・変更 | kill 予定 test | 期待 |
|---|---|---|---|
| M1 | fig14: attempt-0001 の `variance_plan_breach is False` 拒否を除去 | 既存 `test_variance_plan_breach_true_is_rejected` | KILLED |
| M2 | fig14: attempt-0002 の result pin を 1 文字変更 | `test_attempt2_pinned_input_hashes_match_results_document` | KILLED |
| M3 | fig14: attempt-0001 caption の 1 語 (`sized run` → `sized  run` 等) | 既存 `test_landed_fig9_repo_closure_and_caption_when_present` | KILLED |
| M4 | fig14: `_caption_attempt2` からプール・比較禁止の固定文を除去 | `test_attempt2_caption_contains_fixed_literals_and_breach_values` | KILLED |
| M5 | fig14: attempt-0002 panel 題の breach 行を描かない (caption は不変) | `test_attempt2_rendered_breach_and_statistics_match_provenance` | KILLED |
| M6 | fig15: `EXTERNAL_SHA256["summary.json"]` を 1 文字変更 | `test_production_pins_match_results_document` | KILLED |
| M7 | fig15: `summary.json.inputs` の exact 照合を除去 | `test_summary_inputs_reject_smoke_extra_entry` | KILLED |
| M8 | fig15: CP 上限の分位 `.975` → `.95` | `test_cp95_matches_reference_values_and_boundaries` | KILLED |
| M9 | fig15: 片側 Fisher を両側確率和へ | `test_fisher_is_one_sided_on_lower` | KILLED |
| M10 | fig15: commit 平均の分母を 240 へ | `test_commit_mean_uses_all_runs_of_each_arm` | KILLED |
| M11 | fig15: 図中注記の `not performance` 要素を削除 | `test_required_disclosures_are_rendered` | KILLED |
| M12 | fig15: panel 題へ `equivalent` を足す | fig15 の禁止句 test (可視 Text 走査) | KILLED |
| M13 | fig15: `_publish_outputs` の layout 検査呼出しを除去 | `test_layout_failure_publishes_nothing` | KILLED |
| M0 | fig14 生成器へコメント 1 行 (等価対照) | (全 test 緑) | SURVIVED |
