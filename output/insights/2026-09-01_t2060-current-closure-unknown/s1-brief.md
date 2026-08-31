# [T-2060] D1245 — 現行閉包の不在を歴史閲覧の拒否理由にしない

- 目的: D1245 を実装する。`current-closure-unavailable` を歴史閲覧の拒否理由にせず、現行適合を
  unknown として表示する。現行認証に必要な意味互換性は fail-closed のまま維持する。
- 状態: 段 2 実行中 (codex plan 子が稼働)
- 最終更新: 2026-08-31 23:35 JST
- 基準コミット (着手直前の local main): cb4a11b6e9c5281b4aa1feb7c7c1b67315d62aa0
  (作成直後に main が 13 commit 進んだため `--ff-only` で揃えた。開始 gate は再走で緑)
- worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown
- branch: worktree-dev-wave-t2060-current-closure-unknown
- job dir: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown

## 起動時に読了したもの

- CLAUDE.md クラス 3 起動手順、dev-wave 入口の読み込み契約・段 dispatch・条件 dispatch。
- `docs/dev-wave/core.md` 全節、`operations.md` 全節、`workers.md` 全節、`mutation.md` 全節。
- 一次資料: `docs/decisions.md` の D1245。親裁定 D1163 (絶対規律 7 の新設)。
  D1245 を参照する後続 D1312 (歴史 reverify に選択規則を課さない)。
- worklog 末尾エントリ (1111) と「次の一手」。T-2060 は (1110) からの持ち越しで未実装。
- 既存 handoff 2 件 (T-1998、T-2024/T-1760) を読了。いずれも本 wave と編集面の重複なし。

## 段 1 brief

### scope

D1245 の 2 面のうち、**歴史側の表示と構造保証だけ**を実装する。

1. 歴史閲覧 (`HISTORICAL_RAW`) は `current-closure-unavailable` で拒否されない、という現行の
   構造を **機構として名指しした正例・負例の対で固定する**。現状これを守っているのは
   `_require_verifier_epoch_for_purpose` の 1 分岐だけで、他層の mask が無いことを変異で示す。
2. 歴史側の診断に **現行適合 = unknown の明示表示**を足す。今は歴史 view が
   `state=E1 / reason=recorded-closure` だけを返し、現行適合について何も言わない。読者が
   これを現行適合の主張と読める (D1245 の却下選択肢「全面撤去 — 現行適合を過大主張しうる」)。
3. 現行認証 (`CERTIFIED_ACCEPTANCE`) の `current-closure-unavailable` は **撤去しない**。
   fail-closed のまま維持し、負例で固定する。

### 確定済みユーザー裁定 (覆さない)

- D1245: 歴史閲覧の拒否理由にしない / 現行適合を unknown 表示 / 現行認証の意味互換性は維持 /
  理由を全面撤去しない。
- D1163 (絶対規律 7): 記録 commit blob と記録 digest の照合、事前登録・凍結との束縛、
  入力・trace・判定の対応づけ、**現行の正しさ主張に必要な意味互換性の検査**は撤去対象外。
- 依頼文: 仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。規律 2 を緩めない。

### 不変条件

- `CampaignReadPurpose.CERTIFIED_ACCEPTANCE` の受理集合を **1 件も広げない**。
- `require_persisted_certified_commit`、記録 blob 束縛、`CertifiedCampaignView` の token 発行、
  `require_certified_campaign_view` の exact 型拒否は無変更。
- 既存の凍結成果物 bytes は不変 (`FROZEN_MANIFEST` 23 件はいずれも `output/` 配下の成果物で、
  本 wave の編集面 = 閉包ソースを 1 件も含まない。実測済み)。
- 既に保存済みの report artifact が読めなくならない (規律 7)。新 field を required にして
  過去の report を無効化しない。

### 実測した前提 (依頼文・裁定の前提の検証)

- **`orchestrator/campaign/artifact_admission.py` は強制ソース閉包 24 path に含まれる**
  (`campaign_lock.py:57`)。よって本 wave の編集中 (未 commit の間) は、現行閉包が読めず
  `current-closure-unavailable` で **certified 経路のテストが赤になる**。これは期待赤であり、
  統合 commit 後に解消する。実装子・fix 子へ事前指定する。
- 中央 gate `_require_verifier_epoch_for_purpose` (`artifact_admission.py:953-972`) は
  **既に** `HISTORICAL_RAW` で現行閉包を一切読まない。**依頼文の「拒否理由にせず」は中央 gate では
  既に成立している。** 純増は「構造保証の固定」と「unknown 表示」である。
- **過去の測定事実が読めなくなる実害は消費者側に残る。** 過去の Phase 2 landscape を読む
  `replay.load_landscape` (`replay.py:179-186`) は `CERTIFIED_ACCEPTANCE` を要求し、
  `guided.py:204,225,252` と `search_baselines.py:304` がこれを使う。S-1 report は
  `s1_report.py:302-310,427` で私的 gate を `CERTIFIED_ACCEPTANCE` で呼び、拒否時は標本 0 件で
  degrade する。これらの purpose 付け替えは受理集合を変えるため (P1) として段 3 の攻撃対象にする。

### 変更面 (実アンカー表)

| # | path:anchor | 内容 |
|---|---|---|
| A1 | `orchestrator/campaign/artifact_admission.py:160-204` | `CampaignVerifierEpoch` の診断 dataclass。unknown 表示の載せ場所の第一候補 |
| A2 | `orchestrator/campaign/artifact_admission.py:376-391` | `HistoricalCampaignView`。`verifier_assessment_basis` の隣が第二候補 |
| A3 | `orchestrator/campaign/artifact_admission.py:953-972` | 目的別中央 gate。歴史が現行閉包を読まない唯一の実効点 |
| A4 | `orchestrator/campaign/layer3_schema.json:227-239` | report 側 `campaign_verifier_epoch` object の schema |
| A5 | `orchestrator/campaign/layer3_report.py:499` | 歴史 purpose での report 構築 |
| A6 | `orchestrator/campaign/s8b_oracle_artifacts.py:186-215` | official observations の epoch 検査 (reason enum の消費者) |
| A7 | `orchestrator/tests/test_artifact_admission.py:1535,1559-1576` | 既存の正例・負例 |

### 成果物影響 (DW-G05)

放置すると、歴史 purpose で作った Layer 3 report / S-1 report の `campaign_verifier_epoch` が
`state=E1 / reason=recorded-closure` だけを載せ、**現行適合を主張していないことを成果物が
言わない**。読者と下流 consumer は記録時の判定を現行の適合として読みうる。本 wave は report
artifact の epoch 投影に現行適合 = unknown を足し、参照の意味を確定させる。

### (P1) 親の provisional 裁定 — 段 3 の攻撃対象

- (P1-1) 消費者の purpose 付け替え (`replay.load_landscape` 等) は **本 wave では行わない**。
  行えば `require_persisted_certified_commit` と記録 certification まで同時に外れ、規律 2 の
  受理集合を緩める。D1245 は「歴史閲覧を拒否しない」であって「certified consumer を歴史化せよ」
  ではない。→ 攻撃点: これで D1245 に観測可能な効果が残るか。
- (P1-2) unknown 表示は `CampaignVerifierEpoch` の新 field ではなく歴史 view 側の property に
  置く。前者は certified 側の diagnostic 契約 (`s8b_oracle_artifacts.py`、`layer3_schema.json`)
  を同時に動かし、過去の report を無効化しうる。→ 攻撃点: 表示が report まで届くか。
- (P1-3) `layer3_schema.json` へ足す field は optional にする。required 化は保存済み report を
  読めなくし規律 7 に反する。→ 攻撃点: optional では恒真で何も固定しないのではないか。

### 成果物の形

- コード: `artifact_admission.py` の歴史側表示 + 中央 gate の構造保証。必要なら
  `layer3_report.py` / `layer3_schema.json` の投影。
- テスト: 正例 = 現行閉包が読めない状態でも歴史閲覧が成功し現行適合 unknown を表示する。
  負例 = 同じ状態で現行認証は `current-closure-unavailable` で fail-closed 拒否する。
  いずれも実体 (`contract_loader_binding.capture_contract_loader_binding`) を名指しし、
  依存先を stub で置き換えない (F649)。
- 記録: worklog / decisions fragment (`docs/spool/`)、insight。

### 分割方針

編集面が `artifact_admission.py` を中心に一枚岩。**Codex 実装子 1 単位**とする。
段 2 プラン 1 本、段 3 敵対相談 2 本 (正しさ防壁に触るため軽量版の省略は不可)、
段 5 実装子 1 本、段 6 敵対レビュー 2 本。

### 受入・実測環境

- 所在: worklog の既定に従い、受入全走は `tools/dev_wave_wait.py acceptance` 経由。
- 焦点走: `orchestrator/tests/test_artifact_admission.py` と、変更 production file の
  consumer test (`test_t671_source_binding.py`、`test_layer3_report*`、`test_critic*`、
  `test_s1_report*` を参照関係で引く。DW-O26)。
- 機体固有情報は runbook に従う。計算ノードへの重い投入は本 wave では不要の見込み。

## 条件 dispatch の成立状況 (段 1 時点)

- DW-O08 成立 (oracle gate / proof chain に触る) → submodule 再帰初期化を実施済み。
- DW-O09 成立 → pin 閉包を検索済み。`FROZEN_MANIFEST` (23 件) に閉包ソースは 1 件も無い。
  `p3_b4_closed_critic.py:636` と `p3_b4_raw_record_producer.py:660` と
  `test_t671_source_binding.py:31` と `test_s1_9pair_figure_provenance.py:49` は
  **live hash 計算**であって literal bytes pin ではない。durable manifest の再発行は不要。
- DW-O10 不成立 (凍結 producer の出力 bytes を変えない)。
- DW-O13 要再評価 (段 2 前が期限)。新設 gate は作らない方針だが、負例テストの述語は
  実測した値域で採る。
- DW-O20 成立 (背景 job + worktree 隔離) → 本 handoff は repo 外。

## dev-wave 改善候補

(段 8 で routing する。現時点の候補は下記)

- (候補 1) DW-O09 の pin 閉包検索で「live hash 計算 vs literal bytes pin」の判別を毎回
  手作業でやっている。判別の観点を節に 1 行で書けるか。実測 2 例目を待つ (DW-G03)。

## 段 1 の後で足した実測

- **並行 wave との編集面重複は無い。** 5 つの対象 file について、全 29 worktree の実 bytes を
  main の blob と内容比較した。差分が出た木 (t1506、t1817-rescue、rulings-20260821、
  t2032-*、t2072-t2073、t1819-*、t2005-*、t2073-*) はいずれも **古い base の checkout** で、
  現 main 上で稼働中の wave (t1909-probe-closure、t2075-layer3-bypass-hard-failure、
  t2027-d1192-rebind、t2074-a1-estimand-realign) は 1 件も差分を持たない。
  mtime は land による checkout 更新で一斉に動くため判定に使えない。
- **現行閉包が「読めない」の実体を確認した。** `capture_contract_loader_binding`
  (`contract_loader_binding.py:348-361`) は 24 path のそれぞれで disk bytes と HEAD blob を
  比較し、1 件でも違えば `contract-loader-drift` を上げる。中央 gate はこの**戻り値を捨てて
  成否だけを見る**。よって「現行閉包の可用性」= 「working tree が 24 path について HEAD と
  一致しているか」である。
- 正例を作る手段として、既存の `_committed_closure_repo` fixture + `_REPO_ROOT` の差し替えで
  **実際に closure を dirty にする**経路が既にある
  (`test_certified_acceptance_rejects_each_verifier_drift_fail_closed`)。
  取得器そのものを `monkeypatch.setattr` で差し替える既存の負例と違い、こちらは機構を通る。
  段 2 の子にどちらを採るか判定させている。

## 段 2 の成果と親の独立確認

- plan は rc=0、`check_codex_output.py` 緑。推奨は
  `HistoricalCampaignView.current_verifier_conformance == "unknown"` を新設し、
  Layer 3 では **top-level の optional field** として投影する案。
- **親が独立に確認した 2 点 (段 4 の裁定に効く)。**
  1. nested の `campaign_verifier_epoch` object には **既に歴史 view 専用の optional field
     `verifier_assessment_basis` が存在する** (`layer3_report.py:588-617` で
     `_epoch_projection` へ渡し、`layer3_schema.json:237` に定義、同 231 の nested `required`
     には含まれない)。**新 field の自然な置き場所の先例はここにある。**
  2. しかし `test_layer3_report.py:1360-1368` が nested epoch を **exact dict 比較**しており、
     nested へ足すと既存テストの期待値変更が不可避になる。これは DW-S05-B / DW-S06-B が
     禁じている。plan の top-level 案はこの禁止を回避する形。
  → 段 4 で「先例に合わせて nested にし、既存期待値の変更を承認するか」対
    「top-level にして既存期待値を守るか」を裁定する。

## 段 3 レンズ B の結果 (rc=0、検査緑)

real 5 件 / refuted 3 件。核心は **B-01: 親の (P1-1) のままでは D1245 は満たされない。**

- **親 brief の一般化が 1 つ誤っていた。** 「消費者の purpose を替えると保存済み証拠検査まで
  同時に外れる」は **replay には当たるが S-1 には当たらない。** S-1 は可用性 gate
  (`s1_report.py:302-310`) と保存済み COMMIT 証拠検査 (`s1_report.py:352`) が**別関数**で、
  可用性だけを歴史側へ移せる。親が独立に確認した。
- replay は `require_certified_campaign_view` の exact 型拒否があるため、purpose だけ替えても
  動かず、wrapper まで緩めると規律 2 に触れる。安全な分離には新しい証拠 capability 経路が要る。
- B-03/B-04/B-05/B-07 は refuted。schema の certified 側禁止条件は仮想リスク gate ではなく
  新 field による certified 契約の拡大を打ち消す補償条件。保存済み report は読めなくならない。
  Layer 3 の表示は成果物へ実際に届く (DW-G05 はゼロ影響ではない)。oracle 契約は不変。
- B-08 real: 焦点走集合に replay 系 test が無い。

## 親が段 3 の後に独立に見つけた事実 (段 4 の裁定に効く)

- **S-1 の purpose を素朴に歴史側へ替えると、`current-closure-unavailable` だけでなく
  `E0 / v1-authority-absent` の拒否まで同時に落ちる** (`artifact_admission.py:961-962` は
  certified 分岐の内側にある)。D1245 が扱うのは前者だけである。
  よって S-1 の最小変更は「purpose の付け替え」ではなく
  「歴史 gate を呼び、E0 拒否は S-1 側で明示的に維持する」形になる。
  これは共有機構の新設ではなく S-1 局所の 2 行である。

## 段 4 裁定 (確定)

正本は `artifacts/dev-wave-t2060-current-closure-unknown/s4-adjudication.md`。要点だけ再掲する。

- **実装する範囲**: 歴史 view の `current_verifier_conformance == "unknown"`、Layer 3 歴史 report への
  top-level optional 投影、schema の optional 定義と certified 側の禁止、certified 昇格時の除去、
  正例・負例の 6 node。
- **実装しない範囲 (裁定パッケージへ)**: 過去の測定を読む消費者 (`replay.load_landscape`、
  `s1_report`、`s8b_oracle_report`) の purpose 再分類。**D1245 は purpose の分け方を定める裁定であり、
  どの消費者がどの purpose を宣言するかは certified 成果物の受理集合を変える設計判断である。**
  ユーザーは「現行認証に必要な意味互換性は fail-closed のまま維持」「ここを緩めるのは裁定の内容では
  ない」と明示した。よって親の一存では実施しない。RP-1 として推奨付きで返す。
- **親の実測 2 件を訂正した** (レンズ A の E-02 / E-04)。閉包の「読めない」は drift 以外
  (root 解決・Git 実行・race・timeout) も同じ理由コードに畳む。編集中の期待赤も
  **一括分類してはならない** — 隔離 fixture のテストは未 commit 編集中でも緑になる。
- **A-02 (certified view token の偽造可能性) は D1252 が既に裁定済み**で、新事実ではない。再提起しない。
- 変異は 7 件を事前登録し、**kill として数えるのは 4 件** (境界 M1/M2/C1/C2)。
  表示値の変異 2 件は診断感度 pin、certified 昇格の除去は liveness として別枠にした。

## 段 5

実装子は **wave worktree そのもの**を編集面にした (単位が 1 つで所有が素集合に割れないため。
隔離 session からは他 worktree への git 操作が guard で拒否され、限定 patch の往復が成立しない)。
親は実装面を直接編集しない。投入直前に `check_wave_startup.py --mode midflight` rc=0。

## 段 5 の結果 (00:40 JST 完了、rc=0)

差分は **130 行の追加のみ・削除ゼロ**。裁定 §2 の 4 項目がそのまま入り、既存テストの期待値は
1 つも変わっていない。統合前 snapshot は `artifacts/.../s5-diff.patch` に退避済み。

## 段 6 の結果 (レビュー 2 本 rc=0、裁定は `s6-fix-adjudication.md`)

**両レビューとも「受理集合の拡大」「schema 禁止の不発」「scope 逸脱」「変異位置の消失」は
無いと独立に判定した。** must-fix は 3 件。

- **PF-01 (blocker、親所見)。どちらのレビューも指摘していない。**
  `autonomous_trial_completeness.py` は保存済み Layer 3 report と `build_report` の再構築を
  byte 比較する。新 field のせいで、**同 field を持たない保存済み report は必ず食い違う。**
  親の実測: `output/campaigns/` の保存済み report 7 件はいずれも同 field を持たない
  (先頭 1 件の top-level key は 15 個、v2 形式)。
  **本 wave が防ごうとしている規律 7 違反そのものを実装が作り込んだ。**
  しかも**テスト内で report を作れば両側に field が付き緑になる型**で、実成果物だけが壊れる。
  直しは同 file の既存 legacy omission 正規化と同型の flag を 1 つ増やすだけ。
  保存済み side が field を持つ場合は厳密比較を維持する (受理を広げない)。
- PF-02 (= B-07): certified の正例と schema 負例が同一 node にあり、変異 L1 と C2 の帰属が
  一意にならない。2 node へ分割する。
- PF-03 (= T-02): certified 昇格の `pop` が既定値付きで field の実在を要求していない。

**採用しない real 所見:** A-02 (COMMIT 0 件の campaign へ certified view が出る。今回の導入では
ないため RP-4 として裁定パッケージへ)、A-03 (D1252 が既裁定)、T-01 (新規 6 node のうち 3 つは
旧実装でも通る。段 4 の P-01 と整合、worklog に正直に書く)、D-01 (定数表示の限界。P-03 で受容済み)、
E-01 (既存 test に `del` を 1 行追加。期待値は不変だが実装子の「既存テストを一つも変更していない」
という報告は不正確)。

## 未完の作業と次の一手

- 段 6: Codex `role=fix` 稼働中 (`logs/s6-fix1.done`)。
- 段 6 続き: 焦点走 (裁定 §4 で 6 file 追加、計 18 file) → 変異 probe → 変異本走 → 受入全走。
  **同一 worktree からの dispatch は全種を直列にする。** 子と走行を重ねない。
- 段 7〜9: 記録 (spool fragment。下書きは `draft-decisions-fragment.md` と
  `draft-failures-fragment.md`)、自己改善、land。
