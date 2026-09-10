## 段 1 brief

### scope

B-4 材料レポート (`p3-b4-material-report/v1` の `report.json` / `report.md` / `report.complete`) を
入力とし、その内容が certified な選択を許すか否かを機械可読に返す **fail-closed な接続 consumer**
を 1 本新設する。`p3_b4_analysis_path.py` の docstring が scope 外と宣言する 5 語のうち最後の
`certified-selection connection` がこれである。

scope 外 (実装しない):
- floor の発効手続き ([T-2140]、人間の手番)。事前登録 §5 / §5.1 / §5.1.1 の文面は 1 byte も触らない。
- 材料レポート生成器 (`p3_b4_material_report.py`) の出力 wire の変更。
- `p3_b4_analysis_path.py` / `p3_b4_analysis_contract.py` / `_adapter` / `_ledgers` /
  `_prereg_consumer` の変更 (分析 source closure の 5 file)。
- `p3_b4_admission_record.py` / `p3_b4_closed_critic.py` / `p3_b4_launcher.py` /
  `p3_b4_wiring_probe.py` とその test (稼働中 wave が所有。下記「編集面の重複検査」)。
- 仮想リスク向けの gate・検査・台帳・一般化の追加。正規 B-4 実走・qsub・性能測定・build。

### 確定済みユーザー裁定・既裁定

- D1377 — 材料レポートは floor を caller から受け取らず、正規経路が生む分析 verdict は
  `protocol_violation` (`floor_domain_error`) 1 つだけだと自ら宣言する。**本 wave はこの制約を変えない。**
- D1060 — 事前登録 §5 は 1 欄も埋めない。
- D1142 — B-4 の判定は入力検証を先に済ませる全域関数。
- D1236 — B-4 の支配点は certified sink の合流点。
- 引数の指示 — 接続だけを作る。規律 2 を緩めない。Codex author = D95。

### 実測して brief に出す新事実 (段 4 で再裁定する)

1. **`[T-1769]` は現在稼働していない。** `git branch --list '*1769*'` は 0 件、`git worktree list`
   に T-1769 の木は無く、`docs/worklog.md` に `T-1769` の entry も無い。T-1769 は事前登録 §10 に
   2026-08-27 / 2026-09-01 の実測として記録済みで、`output/insights/2026-09-01_t1769-b4-reviewer-role/`
   が着地している。引数の「稼働中」という前提は現時点で覆っている。
2. **実際に稼働中の wave が触っている B-4 file は別集合である。** `t1999-unit2b` / `t1999-unit2c` /
   `t2005-fix1` / `t2005-fix2` / `t2005-fix3` の未 commit 差分が
   `p3_b4_admission_record.py`、`p3_b4_closed_critic.py`、`p3_b4_launcher.py`、
   `p3_b4_wiring_probe.py` とその test を占有している。**本 wave の編集面はこれらと素集合にする。**
3. **certified-selection の下流 consumer は checkout に実在しない。**
   `orchestrator/campaign/layer3_report.py:691` の docstring が
   "No certified-selection consumer exists in this checkout." と明記し、
   `build_accepted_report` を fail-closed な将来 entrypoint だと自ら宣言している。
   権威は `reflux_origin_binding.py:12` が言う launch-admission の `certifying` である。
   **したがって本 wave の「接続」は、実在しない consumer へ配線するのではなく、
   B-4 レポートが certified 選択を許さないことを機械可読に確定させる向きにしかできない。**
4. **材料レポート自身が欠落を名指ししている。** `report.json` の
   `certification_scope.not_guaranteed` に `certified_selection_connection` が入っている
   (`p3_b4_material_report.py:735` 付近)。
5. **到達可能な分析 verdict は 1 つだけ。** `B4Verdict` は 4 値だが、正規経路では
   `report_scope.expected_analysis_verdict == "protocol_violation"` が定数で、
   `analysis.status` は `evaluated` / `not_evaluated` の 2 値。
   `established` を要求する述語は**到達不能** (`DW-O13`)。

### 不変条件 (破ってはならない)

- **規律 2** — 接続は正しさゲートを緩めない。どの入力でも certified 選択を許す方向へ倒れない。
- 事前登録 §5.1.1 の raw bytes 束縛
  (`PREREGISTRATION_SECTION_5_1_1_SHA256 = 0ceab4cd…`) を壊さない = 当該文面を編集しない。
- 材料レポートの wire を変えない。`_assert_complete_projection` の完全射影と 402 field の
  既存 golden を動かさない。
- **caller の自己申告を権威にしない。** report.json の `verdict` field が `established` と
  書いてあっても、それだけで certified 選択を許してはならない (D1377 が floor 引数を却下したのと同じ向き)。
- 到達不能な枝を「保証」と数えない。恒真な assert を足さない。
- 既存テストの期待値を変えない。

### 成果物の形

- 新規 production module 1 本 (`orchestrator/campaign/` 配下、名称は段 2 で確定)。
  publication root ではなく **材料レポートの出力 root** を入力に取り、
  `report.complete` / `report.json` / `report.md` の 3 者束縛を検証したうえで、
  certified 選択の可否を持つ frozen dataclass を返す全域関数。
- 新規 test file 1 本 (`orchestrator/tests/` 配下)。正例・負例を実体名指しで置く。
- worklog / decisions fragment (`docs/spool/`)、insight (`output/insights/2026-09-01_t2139-…/`)。

### 分割方針

編集面が 2 file (production 1 + test 1) と小さく所有が一枚岩なので、段 5 の Codex `role=author`
実装子は 1 本。段 2 plan 1 本、段 3 敵対相談 2 本、段 6 敵対レビュー 2 本 + fix + 焦点再レビュー。

### 親の provisional 裁定 (割れうる前提。段 3 の攻撃対象)

- **(P1) 接続の向きは「不許可の確定」である。** 到達可能な全入力で
  `admits_certified_selection = False` を返す全域関数とし、許可枝は**実装しない**
  (置くと恒真・到達不能な保証になる)。許可の条件は事前登録 §5 の発効であり、それは [T-2140]。
  → 攻撃点: 「常に False を返す関数は接続ではなく定数ではないか」「何も接続していないのに
     接続と名乗るのは D1377 が禁じた自己宣言の水増しではないか」。
- **(P2) 既存 file を 1 つも編集しない。** `p3_b4_analysis_path.py` の docstring も、
  材料レポートの `not_guaranteed` list も変えない。前者の「この module の scope 外」という
  記述は接続を別 module に置いても真のままであり、後者は wire 変更で既存 golden を動かす。
  → 攻撃点: 「5 語目を埋めたと worklog に書くのに docstring が古いままなのは記録と実装の食い違い
     (`DW-O12`) ではないか」。
- **(P3) 権威の束は「凍結事前登録 + レポート bytes」の 2 点。** 接続は
  `p3_b4_analysis_prereg_consumer.verify_repository_preregistration_contract()` の受領証を要求し、
  §5 未発効という repository 側の事実に束縛する。レポートの verdict field 単独には束縛しない。
  → 攻撃点: 「prereg consumer は §5.1.1 の凍結を見るだけで §5 の空欄を見ていないのでは」。
- **(P4) 発火条件 (`DW-G04`)** — 正規コマンド
  `python3 orchestrator/campaign/p3_b4_material_report.py PUBLICATION_ROOT --output-root PATH`
  が書く実 pair。既存の実 CLI subprocess test
  (`test_p3_b4_material_report.py::test_cli_clean_subprocess_runs_twice_and_refuses_overwrite`)
  が実際に pair を disk へ作っている。**real な B-4 publication は output/ に未着地**である
  (`find output -name report.complete` = 0 件)。
  → 攻撃点: 「実 artifact が 1 件も無いのに発火 gate を満たしたと言えるか」。

### 成果物影響 (`DW-G05`)

放置すると、材料レポート (evidence-only・verdict は `protocol_violation`) を certified な選択結果の
根拠として引用する経路が機械的に閉じないままになる。接続を置くと、B-4 レポートが certified 選択の
受理集合へ入らないことが定数の宣言でなく**検査可能な判定**になり、`certification_scope.not_guaranteed`
の 1 項目が「未配線」から「配線済み・不許可」へ移る。

### 受入・実測環境

- 受入全走・変異走は計測機の外 (login node) で親が行う。所在は worklog、機体固有情報は runbook。
- 変異 matrix は実装面の差分があるので免除しない (`DW-S04`)。

### 変更面の実アンカー表

| 種別 | path | 役割 |
|---|---|---|
| 新規 | `orchestrator/campaign/<接続 module>.py` | 段 2 で命名確定 |
| 新規 | `orchestrator/tests/test_<接続 module>.py` | 正例・負例 |
| 参照のみ | `orchestrator/campaign/p3_b4_material_report.py:46-59,691-795,1155-1277` | 入力 wire・commit marker |
| 参照のみ | `orchestrator/campaign/p3_b4_analysis_contract.py:42-92,206-219` | 4 verdict・invalid reason |
| 参照のみ | `orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:1080-1092` | 凍結事前登録の受領証 |
| 参照のみ | `orchestrator/campaign/layer3_report.py:682-693` | 下流 consumer 不在の一次資料 |
| 参照のみ | `orchestrator/campaign/reflux_origin_binding.py:1-20` | certified 昇格の権威 |
| 触れない | `docs/phase3-b4-reflux-ablation-preregistration.md` | §5.1.1 raw bytes 束縛 |
| 触れない | `orchestrator/campaign/p3_b4_{admission_record,closed_critic,launcher,wiring_probe}.py` | 稼働中 wave が所有 |

### pin 閉包 (`DW-O08` / `DW-O09`)

- 分析 source closure の path tuple は 2 か所 —
  `p3_b4_analysis_path.py:68-74` の `_SOURCE_CLOSURE_PATHS` と
  `p3_b4_analysis_prereg_consumer.py:98-106` の `_CLOSURE_PATHS`。**新規 module を足さない。**
- xdist group の独立 oracle は `orchestrator/tests/test_real_repo_serialization.py:247-253`
  (`_XDIST_GROUP_NAMES_GOLDEN`) と `:308-314` の
  `_LONG_LIVED_FIXTURE_GROUP_NODES_GOLDEN`。**新規 test file に `xdist_group` marker を付けるなら
  この 2 つの golden に登録が要る。付けないのが既定。**
- `orchestrator/tests/conftest.py:260` の `_REAL_REPO_NODE_INVENTORY` は real-repo fixture を使う
  node の独立 oracle。新規 test が real repo を読むなら登録が要る。**tmp_path 完結にするのが既定。**
- 凍結 bytes を変える producer は本 wave に無いので `DW-O10` は不成立。
- submodule 初期化は wave worktree で実施済み。

