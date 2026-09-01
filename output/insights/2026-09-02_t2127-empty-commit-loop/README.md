# [T-2127] certified view の全称保証と存在保証を分ける

wave: `dev-wave-t2127-empty-commit-loop` / branch `worktree-dev-wave-t2127-empty-commit-loop`
起票の正本: `docs/archive/worklog-phase3-0901-1130.md` の [T-2127] 項
背景: `output/insights/2026-09-01_t2060-current-closure-unknown`
Codex author = D95。

## この wave が変えたもの

1. `orchestrator/campaign/artifact_admission.py` に `admit_persisted_certified_commits()` を新設し、
   `_require_admitted_campaign` の手書き commit 走査 loop をこの 1 呼出へ置換した。
   証拠の母集合は `records` 全体のまま内側の単数 helper へ渡す。
2. `CertifiedCampaignView` に必須 field `persisted_certified_commit_count` を足し、
   exact int・非負・WAL snapshot の commit 件数との一致を `__post_init__` で検査する。
3. `require_certified_commit_evidence()` を新設し、件数 0 を拒否する。
4. 配線先は `replay.load_landscape` と `layer3_report.build_accepted_report` の **2 箇所だけ**。
5. class と helper の docstring に、view が commit の存在を保証しないこと、
   件数が検証の証拠ではないことを明記した。

epoch gate、overlay ledger、certified token 発行、exact 型拒否、外部 8 consumer の
helper 呼出は**すべて無変更**である。

## 実測で分かったこと

### 起票の欠陥記述が不正確だった

「commit 0 件で loop が空回りし、証拠なしで certified view が発行される」とあるが、
**「存在する全 commit の証拠が妥当」という全称命題は 0 件でも真**である。空走そのものは欠陥ではない。
欠陥は、その全称保証を「certified commit が存在する」という存在保証として読む consumer 契約の
曖昧さにある。段 3 のレンズ A が指摘し、親が採用した。

### 値が変わる箇所は 1 つだけで、既存テストがそれを固定していた

`layer3_report.build_accepted_report` は acceptance receipt の certifying、trial 一致、
`admission_status=admitted`、decision 不変、epoch E1 を要求するが、**どこも commit の存在を
要求しない**。1 件も commit されず 1 件も検証されていない campaign から
`certifying_input: True` の Layer3 report を発行できる。

**これは親の推測ではない。** `orchestrator/tests/test_layer3_report.py` の現行 passing test は
`build_start` 1 件だけ (commit 0 件・verify_done 0 件) の campaign に対して
`report["certifying_input"] is True` と epoch `E1` を assert していた。

### admission 層での一律拒否は正しさ検査を 1 本殺す

受理集合を「certified かつ commit 0 件なら拒否」へ等価に縮小する probe を当てると、
baseline 全緑の consumer テストが **126 node 赤**になった。中身は全試行 abort の campaign の
棄却を報告する正当な経路である。

さらに `autonomous_trial_completeness` の failure campaign 制御は
「failure campaign が certified 受入で**拒否されること**」に依存する**負例側の制御**である。
admission 層で 0 件を拒否すると、この制御が abort-only campaign に対して**恒真化**し、
意図した gate を一度も通らなくなる。受理集合を締めたつもりで検査を無効化する型である。

### 段 2 プランの consumer 共通化は受理集合を広げるものだった

単数 helper は `records[:commit_index]` を証拠の母集合とし、receipt の証拠列と WAL の
verify 列の**完全一致**を要求する。プランは外部 consumer へ segment / window だけを渡す
共通化を提案したが、母集合を狭めると receipt に載っていない余分な verify が見えなくなり、
**いま拒否されている入力が通る**。段 3 のレンズ A の指摘を採用して不採用にした。

### 配線は 6 箇所から 2 箇所へ縮小した (反実仮想)

各箇所について「非ゼロ要求を置かなくても、同じ入力で別の gate が先に赤を出すか」を確かめた。

| 箇所 | 先に赤を出す既存 gate | 判定 |
|---|---|---|
| `backoff_sweep_report` | `if not static: skip` を抜けた時点で commit >= 1 が含意される | 恒真。足さない |
| `backoff_overthrottle` | `require_complete_bindings` が空集合と非空 expected の不一致で raise | 恒真。足さない |
| `backoff_extended_sweep_report` | `len(perf_statuses) != 1` で raise | 恒真。足さない |
| `autonomous_trial_completeness` certifying chain | producer は常に non-certifying report を作り、先行の不一致検査が拒否する | 発火する既存 artifact path を書けない。足さない |
| `replay.load_landscape` | 無し (commit 投影より前) | 足す |
| `layer3_report.build_accepted_report` | 無し | 足す |

親の反実仮想と段 3 のレンズ A・B が独立に同じ結論に達した。

### consumer 閉包は名前検索の和集合では足りない

- `CERTIFIED_ACCEPTANCE` を名前で参照する production file: 20
- `require_persisted_certified_commit` を呼ぶ production file: 9 (外部 8 + 定義元)
- 和集合: 22。差分 2 件 (`backoff_repro.py`、`paper_story_a2_certification.py`) は
  `CERTIFIED_ACCEPTANCE` を名前で持たず helper だけを呼ぶ。**名前 grep を 1 本引くと落ちる。**
- 意味的 consumer +1 = 23。`orchestrator/verifier/commit_receipt.py` が関数内 import で
  `CertifiedCampaignView` を受ける。
- さらに `replay.load_landscape` 経由の間接 consumer 2 file
  (`search_baselines.py`、`guided.py`)。**どちらも `CERTIFIED_ACCEPTANCE` も helper 名も持たない。**
  非ゼロ要求を共有入口へ置いたのはこの取りこぼしを避けるためである。

### 件数 field が証明すること・しないこと

- 証明する: 誤った件数を発行できない (0 を 1、1 を 0 と偽れない)。consumer が件数を信頼してよい。
- 証明しない: その commit が実際に証拠検査を通ったこと。
  `__post_init__` の件数一致検査は records から導出できる値の二重導出である。

実際の防壁は (a) 走査 loop が共通 helper 1 本であること と (b) 非ゼロを要求する 2 箇所であり、
件数 field はその橋渡しである。docstring にも明記した。

### 変異は冗長 gate に過剰決定されていた

初回 probe (全件 SURVIVED 期待) では `artifact_admission.py` を触る 9 変異すべてで
`test_p3_b4_wiring_probe.py` の 21 node と `test_layer3_report.py` の 5 node が落ちた。
contract-loader drift と作業ツリー汚染の gate であり、機構の証拠にならない。

この 2 file を選択から外して実効 gate へ再照準し、機構固有の node 集合を完全集合として本走した。

| 変異 | 機構 node 数 | 結果 |
|---|---|---|
| M1 内側の証拠検査を除去 | 6 | KILLED |
| M2a stage filter を除去 | 24 | KILLED |
| M2b 件数を全 record 数へ | 18 | KILLED |
| M3 件数を定数 1 へ | 3 | KILLED |
| M4 exact int 検査を削除 | 2 | KILLED |
| M5 件数一致検査を削除 | 1 | KILLED |
| M6 非ゼロ条件を弱化 | 2 | KILLED |
| M7 replay の配線を除去 | 1 | KILLED |
| M8 layer3 の配線を除去 | 1 | KILLED |
| M9 非ゼロを admission 層へ移動 | 2 | KILLED |

**10/10 KILLED、生存 0、MISMATCH 0、baseline 緑。**
M8 が `test_accepted_report_rejects_no_commit_campaign` 1 件だけで殺されることが、
本 wave の成果物影響が単一理由で守られていることの証拠である。

### 依頼が名指しした対象の 1 つは閉包外だった

`certified_writer_admission.py` (415 行) と `certified_writer_preflight.py` (196 行) は
`artifact_admission`・`CertifiedCampaignView`・`CERTIFIED_ACCEPTANCE`・`STAGE_COMMIT` の
いずれも参照していない (全文検索で 0 件)。計算資源・較正・提出物の writer 受入であり、
campaign admission とは別の関心事である。編集面から外した。

## 実装しなかったこと (記録するが scope 外)

### 自己 SHA による成果物 bytes の変化

`artifact_admission.py:1039` は自分自身の SHA を `validator_sha256` として decision に入れ、
`layer3_report.py:651` は自分自身の SHA を `meta.generator.sha256` に入れる。
`autonomous_trial_completeness` の比較正規化は `generated_from_head` しか除かないため、
両 file を編集すると保存済み v3 report と fresh rebuild が byte 不一致になりうる。

**本 wave の blocker ではないと判定した。** repo 内の保存済み Layer3 report 7 件の
`meta.generator.sha256` は `705508de…` / `89aa98e8…` で、当時の現物 `362fb98f…` と
**既にずれていた**。`admission_decision.validator_sha256` は 7 件とも field 自体が無い。
本 wave が持ち込む破れではなく、両 file を編集するあらゆる wave に共通する既存の設計性質である。
互換層の新設は要求外として却下した。

### 「既存 certified 成果物の値は変わらない」の射程

tracked corpus に E1 certified campaign がそもそも無いため、ほぼ空集合についての結論である。
正しくは「tracked repository corpus では未発火」である。外部 `output_root` の全数把握は
本 wave では行っていない。

## 一次資料

- `s1-brief.md` — 段 1 brief と親の実測
- `s4-adjudication.md` — 段 4 裁定、変異事前登録、配線の縮小理由
- `s6-fix-adjudication.md` — 段 6 裁定 (レビュー 2 本 + 親の実測)
- `parent-verification-notes.md` — 親が段 2 プランを裏取りした実測
- `verbatim/` — 子の出力逐語 (plan、相談 2 本、実装、レビュー 2 本、fix 2 巡)
- `mutation/` — 変異 spec と本走台帳

初回 probe の生台帳 (`mutation-probe-2.json`、2.9 MB) は大きいため repo へ入れていない。
過剰決定の内訳は本文の表と `s6-fix-adjudication.md` に要約がある。
