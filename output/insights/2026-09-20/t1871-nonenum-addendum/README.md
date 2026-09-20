# [T-1871] 旧 headline 復活条件の「非列挙」に D1441 の操作的定義を置く追補 1 — 段 1 実測と裁定台帳

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)

- 裁定: D1441 (2026-09-02、ユーザー裁定)。一次資料 = `output/insights/2026-09-01_t1871-nonenum-axis-stage-b-package.md` §6 裁定 1〜4。
- wave: `dev-wave-t1871-nonenum-addendum` (branch `worktree-dev-wave-t1871-nonenum-addendum`、base main `42096593`)。
  docs-only、実装面 0、変異 matrix 免除 (DW-S04)。段 2 省略、段 3 敵対相談 2 本、段 6 独立 read-only レビュー 1 本 + 焦点再レビュー 1 本 + 焦点走 + 受入全走。
- 成果物: `docs/phase3-main-experiment-addendum-1.md` (新規)、`docs/README.md` +1 entry、`docs/phase3.md` 分離節 +1 文
  (commit `fb3a7e6d5`、レビュー fix `85aa8895c`)。
- 逐語は `verbatim/` (段 1 brief と一次資料射影、段 1 probe、段 3 相談 A/B、段 4 裁定、段 6 レビュー 1 と焦点再レビュー)。
  job dir = `/home/SFC/tanab/.claude/jobs/a9eb1066/tmp/` (生ログ・待ち手 receipt・受入 receipt)。

## 0. 結論 (先に書く)

1. **依頼の「同 doc へ日付付き追記」は、そのままでは実行できなかった。** `docs/phase3-main-experiment.md` の sha256
   `e544de1969dd4df13dc42aa3d165e22b70fab2ab399dc011baa46359727bea45` は凍結成果物 5 本
   (`output/s1-freeze/known_axes_freeze.json` 623〜624 行、`output/s1-freeze/measurement_freeze.json` 742〜743 行、
   `output/s8b-freeze/holdout_freeze.json`、`output/s8b-freeze/holdout_freeze.v2.g1.json`、
   `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`) に source として記録されている
   (key `D52 2026-07-12追記: read-heavy sk_ad事前固定`)。
2. **実測 (2026-09-20、DW-O19 一時変異、`verbatim/s1-probe-freeze-verifiers.md`):** 同 doc 末尾に 1 行足すと
   (sha → `ac760722…`)、現 root を読む直接 verifier `orchestrator/campaign/s1_known_axes_freeze.verify()` が
   `FreezeError: source sha256 不一致: docs/phase3-main-experiment.md` で赤。baseline (未変更) は OK
   (held check 1 件 `s1-known-axes.ccbench-submodule-head-pin` のみ)。`git checkout --` で復元、porcelain 0、sha = HEAD blob。
   この verify を実 root に対して呼ぶのは `s8b_oracle_driver.py` 506〜519 行 (T-080 adapter が発火しない分岐) と
   `s1_verify_extime_calibration.validated_target` (235 行)、test では
   `test_s1_known_axes_freeze.py::test_historical_current_use_matches_real_reconstruction` (1055 行、静的に同経路)。
   **一般化の射程 (段 3 A-1 / B-4 で限定):** T-080 adapter (active-valid receipt) 発火時は static adapter 経路で直接 verifier を
   呼ばず、source closure は H_mig の blob と照合する (`t080_freeze_migration.py` 1365〜1381 行)。「全 8b 経路が refuse する」とは言わない。
   `s1_measurement_freeze.verify()` は baseline でも generator sha256 不一致で赤 = 本 wave と無関係の既存状態。
3. **置き場の裁定 (P1):** 追補は別 file `docs/phase3-main-experiment-addendum-1.md`、同 doc は 0 byte 変更。根拠 = 上記実測 +
   D1789 (発効後の事前登録は bytes を変えず別 file で訂正、「文面だけ直して sha を貼り直す」は却下案) + 先例
   `docs/backoff-policy-performance-preregistration-erratum-1.md`。sha 追随 (先例 `e5dfa84c6`、2026-07-16) は、その後 T-080 が
   `known_axes_freeze.json` の raw bytes を code 定数 `KNOWN_AXES_RAW_SHA256` で pin し holdout v2 g1 も同 JSON の sha256 を束縛するため、
   凍結 chain 全体の再凍結になる — 採らない。`_HISTORICAL_CODE_PATHS` への docs 追加は verifier の弱体化 — 採らない。
   別 file は「唯一の形」ではない (段 3 B-5: `docs/phase3.md` 分離節に本文を置く / insight の erratum 節 / D1441 のまま、も可能で、
   前 2 者は運用文書へ拘束本文を戻す・事前登録への導線が要る、最後は依頼を履行しない)。
4. **追補が発効させるのは語義改訂だけ** (段 3 A-4)。旧 headline の復活・D1012 の休眠 (B-5 対照、対照 3/4、段 6 (a)〜(e))・
   D52 (c')・壁 2 (D1409) は動かない。承認記録は 3 分割: 語義変更の承認 = D1441 (2026-09-02)、追補作成の根拠 = 本依頼、
   反映 = 本追補の日付付き commit。
5. **既知結果の開示 (段 6 R-1):** 根拠 insight は既存軸の偵察結果を「3 workload とも floor 超が cross-run 再現済み」という
   二値としてだけ引用している (同 §2 M8)。「性能値・偵察結果は 1 件も見ていない」とは書かない。追補は新たな性能測定・偵察を報告しない。

## 1. 段 3 敵対相談の裁定台帳 (2 本、`gpt-6-astra`、medium、read-only、逐語 = `verbatim/s3-consult-{A,B}.md`)

| 所見 | 判定 | 採否 | 反映 |
|---|---|---|---|
| A-1 / B-4 8b refusal の無条件一般化に反例経路 (T-080 static adapter、H_mig blob 照合) | real | 採用 must-fix | 追補冒頭・phase3 pointer・worklog から「全 8b 経路」「唯一の形」を削除、直接 verifier + 既存 test に限定 |
| A-4 語義改訂の発効と D1012 休眠解除の発火を分ける、承認記録 3 分割 | real | 採用 must-fix | 追補 §3 冒頭と承認記録 |
| A-5 / B-2 / B-5 phase3 pointer の将来規則 `addendum-N`・「2026-09-20 以降 pin」・「唯一」を削る、不在 path は check_docs 赤 | real | 採用 must-fix | pointer は実在 file への 1 文のみ |
| B-2 五節構成の圧縮 | real | 採用 nit | 冒頭 + §1〜§3 (65 行) |
| B-3 命名を erratum に寄せる | real | 一部採用 nit | file 名は依頼語「追補」= addendum-1、README と冒頭で erratum 系列との対応を明記 |
| A-2 D1441 逐語で足りるが適用対象・未確定事項を明記 | refuted (採用条件) | 反映済み | §1 適用範囲、§3 「予算・生成器・判定手続きを確定しない」 |
| A-3 休眠・(c')・B-5 と矛盾なし。論文ストーリー 2026-09-14 版 1549〜1550 行の「未裁定」は陳腐化 | refuted | 記録のみ | 論文ストーリー次版は scope 外 (worklog 次の一手に 1 行) |
| B-1 D1441 の記録だけで足りる | refuted | — | 研究前進を「D1441 を事前登録の改訂として参照可能にする」に限定 |

## 2. 段 6 (レビュー・焦点走)

- **独立 read-only レビュー 1 本** (`verbatim/s6-review-1.md`): real 3 件 = must-fix R-1 (「偵察結果を 1 件も見ていない」と
  「後付けでない保証は Git 履歴だけ」が一次資料 §2 M8 / §8 を超える)、nit R-2 (verifier の実測と test への静的波及の混同)、
  R-3 (壁 1 再説明の圧縮)、任意 R-7 (状態記述は発行日時点)。refuted R-4 (逐語一致・sha 実測一致・凍結成果物 5 本の実在と記録確認)、
  R-5 (D1441 を超えない)、R-6 (段 3 の 5 件反映)。NO-GO → fix `85aa8895c` (追補 21 行)。
- **焦点再レビュー** (`verbatim/s6-review2-1.md`): R-1/R-2/R-3/R-7 すべて closed、R-4〜R-6 回帰なし、新規所見なし、**GO**。
- **焦点走** (追補入りの木 `fb3a7e6d5`、`orchestrator/tests/test_s1_known_axes_freeze.py` 1 file、`tools/run_tests.py` が
  bounded local を選択、login node、94 秒): **50 passed / 9 skipped / 0 failed**。skip 9 は growth hold
  (`IZANAGI_GROWTH_HOLD_V1`、2026-08-12 rulings 第 3 束) の node であり、
  `test_historical_current_use_matches_real_reconstruction` は skip 集合に含まれず passed 側。
- 受入全走は段 7 の記録 commit の後に投入する (land は tested tip をそのまま取り込むため)。結果は job dir の受入 receipt。

## 3. 工数

codex 子 4 本 (consult 2・review 1・焦点再レビュー 1、すべて `gpt-6-astra` medium read-only)。
test 走行: 焦点走 1 (bounded local)・受入全走 1。計算ノード job 0 (受入が dispatch する分を除く)。
