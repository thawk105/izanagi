# 段 4 裁定 — 8c 条件 C09 / C10 の consumer 実装

親裁定。2026-08-18 18:58 JST。base は merge 後の `64d37b1a` (main を ff-only 取り込み済み、
並行していた t1333 wave は land 済みで重複面は解消)。

## 0. 実測の更新

merge 後に再測定:

- C09 UNSATISFIED / `formal-acceptance-layer3-consumer-absent` (変化なし)
- C10 UNSATISFIED / `cross-binding-verifier-incomplete` (変化なし)
- C01 は t1333 により `ratified-generation-reference-absent` へ変化 (本 wave の対象外)

焦点 5 file のベースライン: 552 passed / rc=0 (base 38f173cb 時点。merge 後に再取得する)。

## 1. 所見の裁定 (real / refuted、採用 / 不採用、scope 内 / 外)

### 採用 (scope 内、blocker)

| ID | 所見 | 裁定 |
|---|---|---|
| A-1 / B-01 | aggregate digest が再検証不能 | **real / 採用**。per-trial の leaf digest を受領証へ保存し、top-level の aggregate を leaf から再計算できる形にする。leaf を持たない v3 化は「外観だけの schema 拡張」であり不採用 |
| A-2 | `campaign_root` が report の自己申告で古い campaign を指せる | **real / 部分採用**。`assert_campaign_layer3_chain` は `expected_root = output_root/campaigns/<campaign_id>` と一致することを既に要求する (`autonomous_trial_completeness.py:3009-3011`)。よって「任意の別 root」は既に拒否される。**残る穴は `output_root` 自体が report 由来である点**なので、acceptance 側で `output_root` を report の run root から導出し、cell の `campaign_root` がその配下にあることを独立に要求する。manifest 側での campaign root 事前登録は scope 外 (下記 3 節) |

### 採用 (scope 内、must-fix)

| ID | 所見 | 裁定 |
|---|---|---|
| A-3 | admission failure cell を持つ build report は層3 chain を 1 本も持たずに受理される | **real / 採用 (機構の理解は訂正)**。`continue` は「層3 レポート不在」かつ「campaign が独立に admitted でない」ときだけ発火する正当な失敗経路であり偽造経路ではない (`:3013-3027`)。しかし結果として chain 欠落の build report が `accepted` に入るのは C09 の要求に反する。**専用の non-certifying reason code を積む**ことで塞ぐ |
| A-4 | 検証 CLI `verify_autonomous_trial_files` が C10 の consumer から外れる | **real / 部分採用**。CLI からも同じ `verify_s8c_cross_binding` を呼ぶ (単一権威 verifier という C10 の要求と整合)。lifecycle 台帳を C10 の authority に含めるかは scope 外 (下記 3 節) |
| A-5 / B-08 | acceptance の既存 fixture は 6 件とも no-build で build 枝を発火させない | **real / 採用**。**本 wave の中核要件**。下記 4 節に受入条件を書く |
| A-6 | `do_build` は report の自己申告 | **real / scope 外**。manifest / launch admission へ束縛するのは manifest schema の変更であり、依頼の scope 外 (契約 JSON と凍結 record を触らない) に接する。裁定パッケージへ (下記 3 節) |
| A-7 | 評価器は dead code と未使用 literal を受理する | **real / 不採用 (評価器は変更対象外)**。ただし**本 wave の不変条件として拘束する**: 実装子は `if False:` 下の呼び出し・未使用 literal・`pass` wrapper を書いてはならない。変異 matrix で実効性を実証する |
| A-8 | no-build 変異テストは run-start 側も変えないと別の gate で落ちる | **real / 採用**。テスト設計として反映 |
| B-02 / B-06 | v1 / v2 / v3 の exact key 集合を分離しないと凍結 fixture を壊す | **real / 採用** |
| B-03 | WAL に `build_records` / `bench_records` という実 key は無い | **real / 採用**。`layer3_report.py` の projection と同じ正規化を使い、union が再読した全 record を覆うことを検査する |
| B-04 | `_bound_regular_bytes` は相対 path を process cwd 基準で解決する | **real / 採用**。親が独立に確認 (`:450` の `os.path.abspath`)。新 helper は root を明示結合する |
| B-05 | 判定軸は `cells` 数ではなく `do_build` | **real / 採用**。親 brief の (P4) を訂正 |
| B-07 | `no-build` を `MANDATORY_NON_CERTIFYING_REASONS` へ入れてはいけない | **real / 採用**。条件付き reason とする |
| B-pin | C10 の declared-unimplemented pin 2 件は実装しても自動では移動しない | **real / 採用**。手で CHECKS へ移す。放置は「宣言止まり」の再導入であり不採用 |

### 不採用 / refuted

- レンズ A が「`campaign_root` 付き failure cell が `continue` で素通り」と書いた再現手順のうち、
  「同じ campaign ID の古い campaign への symlink」は `expected_root` 一致検査で既に拒否される。
  行番号 (`:2914`, `:2925`) は merge 前のもので、現行 base では `:3009-3027`。
- レンズ B の B-10 (t1333 との行衝突は再現しない) は **観測時点では正しい**。
  子の実行中に t1333 が land し main へ入ったため。衝突は消滅した。
- 親 brief の (P4) 「既存 fixture は全て `cells=[]`」は **誤り**。`_complete_report` は 1 cell を作る。

## 2. プラン v2 (実装する形)

### 2.1 C09 — 層3 検証を acceptance の必須経路へ

`assert_trial_registry_acceptance` の per-report loop 内、`assert_execution_digest_chain` の後、
`accepted.append` の前に置く。

1. `report["do_build"]` が `bool` でなければ `TrialRegistryError` (型を先に閉じる)。
2. `do_build is False` → 層3 chain を呼ばず `no_build_seen = True`。
3. `do_build is True`:
   - `cells` が list かつ非空でなければ `TrialRegistryError` (`do_build=True and cells==[]` を拒否)。
   - 各 cell の `campaign_root` を必須とする。欠落は `TrialRegistryError`。
   - `output_root` は cell の `campaign_root` の親の親から導き、**全 build cell で 1 つに一致すること**を要求する
     (producer `p3_autonomous_workload_trial.py:2720-2736` と同形)。
   - さらに `output_root` が **report の run root と同じ試行に属すること**を独立に要求する
     (report の `attempt_journal` が指す run root から導いた output root と一致すること)。
     一致しなければ `TrialRegistryError` (A-2 の残る穴を塞ぐ)。
   - `assert_campaign_layer3_chain(report=report, output_root=output_root)` を実走する。
     `AutonomousTrialCompletenessError` は `TrialRegistryError` へ変換する。
   - chain を通過した build cell のうち、**persisted layer3 report を持たない cell**
     (admission failure cell) が 1 件でもあれば `layer3_chain_absent_seen = True` とする。
4. 受領証構築時:
   - `no_build_seen` なら reason code `"no-build"` を積む。
   - `layer3_chain_absent_seen` なら reason code `"layer3-chain-absent"` を積む。
   - どちらも `MANDATORY_NON_CERTIFYING_REASONS` には入れない (条件付き reason)。
   - `"certifying": False` は反転させない。

`"no-build"` は `do_build is False` という report の実値から導かれる。未使用 literal ではない。

### 2.2 C10 — 単一権威 verifier

`autonomous_trial_completeness.py` に新設。

`read_and_verify_bytes(value, *, root, expected_sha256, gate, label) -> tuple[Path, bytes]`

- 相対 path は `root / value` へ**明示結合**する (process cwd 基準にしない。B-04)。
- 絶対 path は `root` 配下であることを要求する。
- symlink 通過・非 regular file・root 外を拒否する (`_bound_regular_bytes` を内部で使ってよい)。
- 読み直した bytes の sha256 が `expected_sha256` と一致しなければ失敗する。
  `expected_sha256` が `None` の呼び出しを作らない (検査を無効化できる口を残さない)。

`verify_s8c_cross_binding(*, report, events, run_root, output_root=None) -> dict[str, Any]`

- `do_build is True` のとき、下記 12 field を実 bytes から束縛する。
  1. `input_payload_sha256` — role event の flat key。provider payload bytes の再計算値と一致
  2. `raw_response_path` — role event の path。root 境界検査を通す
  3. `raw_response_sha256` — raw response bytes の再計算値と一致
  4. `provider_payload_sha256` — `provider_artifacts.payload_path` の bytes 再計算値と一致
  5. `provider_envelope_sha256` — `provider_artifacts.envelope_path` の bytes 再計算値と一致
  6. `proposal_path` — proposal descriptor の `path`。root 境界検査を通す
  7. `proposal_sha256` — proposal bytes の再計算値と一致
  8. `build_records` — campaign WAL を再読し build stage record の projection を作る
  9. `bench_records` — 同 WAL の bench stage record の projection。supervisor の
     `harness` / `bench_wall_seconds` と突き合わせる
  10. `artifact_refs` — persisted layer3 の `artifact_refs` 各 `{path, sha256}` を全件再読して照合
  11. `source_refs` — WAL と loop state から canonical ref を再計算し multiset 完全一致
  12. `admission_decision` — cell / persisted layer3 / `require_admitted_campaign(...)` の三者 exact 一致
- WAL の record は build / bench の 2 projection の union が**再読した全 record を覆う**ことを検査する
  (未分類 record を黙って捨てない。B-03)。
- `do_build is False` のときは `mode="no-build"` の projection を返し、
  12 field を束縛したとは扱わない。`unbound_fields` に 12 field 名を明示する。
- 返す per-report 受領証は `receipt_sha256` を自分の canonical JSON (自 field を除く) から導く。

呼び出しは C09 の直後、`accepted.append` の前。`_exclusive_create_acceptance_receipt` より前。

`verify_autonomous_trial_files` からも同じ verifier を呼ぶ (A-4)。

### 2.3 受領証 v3

- `SCHEMA_VERSION` を v3 へ。`LEGACY_SCHEMA_VERSION` (v1) は据え置き、v2 は
  `PREVIOUS_SCHEMA_VERSION` として保存する。
- top-level key 集合を v1 / v2 / v3 で**分離**する。v1 / v2 の受領証は従来どおり parse できること。
- v3 の top-level に `cross_binding_receipt_sha256` を追加 (必須、64 桁)。
- v3 の各 trial に per-trial の `cross_binding_receipt_sha256` を追加 (必須、64 桁)。
  trial の exact key 集合も schema 別に分離する。
- `verify_acceptance_receipt` は v3 のとき **leaf から aggregate を再計算して照合**する (A-1 / B-01)。
  再計算しない v3 検証は不採用。

## 3. scope 外 (実装しない。裁定パッケージとしてユーザーへ返す)

1. **`do_build` の外部束縛** (A-6)。現状 `do_build` は report と run-start の一致しか検査されない。
   manifest または launch admission へ固定するには manifest schema の変更が要り、
   依頼が明示した scope 外 (契約 JSON・凍結 record 不可触) に接する。
2. **manifest 段階での campaign root 事前登録** (A-2 の残余)。本 wave は
   「report の run root から導いた output root と一致すること」までを実装する。
   実走前に campaign root を manifest へ焼く設計は別 wave。
3. **lifecycle 台帳を C10 の authority に含めるか** (A-4 の残余)。
   本 wave は acceptance receipt と検証 CLI を authority とする。

## 4. 受入条件 (これを満たさないと本 wave は完了しない)

1. C09 / C10 がともに `EVIDENCE_UNDEFINED` / `completion-proof-not-machine-checkable` になる。
2. **acceptance の build 枝が実 fixture で発火する。** 具体的には
   `assert_trial_registry_acceptance` を `do_build=True` の 6 report で通し、
   実在する campaign (campaign.lock / WAL / loop state / layer3 report /
   proposal / provider payload・envelope / raw response) に対して
   `assert_campaign_layer3_chain` と `verify_s8c_cross_binding` の両方が実走し、
   受理が成功する正例テストが 1 本以上あること。
   **これが作れない場合は production を緩めず、何が阻んだかを報告すること。**
3. 12 field それぞれについて、その 1 field の束縛を壊す変異で赤になる負例テストがあること。
4. 既存の no-build acceptance テストが production を緩めずに緑であること。
5. v1 / v2 の凍結 fixture が変更なしで緑であること。

## 5. 変異事前登録 (DW-M01)

実装前に登録する。各変異は単一理由であることを実装後に確認する。

| # | 変異位置 | 変異内容 | 期待 kill |
|---|---|---|---|
| M01 | `trial_registry.assert_trial_registry_acceptance` | `assert_campaign_layer3_chain(...)` 呼び出し行を削除 | C09 述語 UNSATISFIED + build 正例テスト赤 |
| M02 | 同上 | `do_build=True and not cells` の拒否を削除 | cells 空の負例テスト赤 |
| M03 | 同上 | `"no-build"` reason の append を削除 | no-build reason の exact assert 赤 |
| M04 | 同上 | `"layer3-chain-absent"` reason の append を削除 | failure cell 負例テスト赤 |
| M05 | 同上 | `verify_s8c_cross_binding(...)` 呼び出し行を削除 | C10 述語 UNSATISFIED + 正例テスト赤 |
| M06 | 同上 | run root 由来 output root との一致検査を削除 | 別 output root の負例テスト赤 |
| M07 | `autonomous_trial_completeness.read_and_verify_bytes` | sha256 比較を削除 | byte 変異の負例テスト赤 |
| M08 | `autonomous_trial_completeness.verify_s8c_cross_binding` | `raw_response_sha256` の照合を削除 | raw response 変異の負例テスト赤 |
| M09 | 同上 | WAL projection の union 完全被覆検査を削除 | 未分類 record の負例テスト赤 |
| M10 | 同上 | `artifact_refs` の全件再読を 1 件目だけに縮小 | artifact 変異の負例テスト赤 |
| M11 | `s8c_acceptance_receipt.verify_acceptance_receipt` | aggregate の leaf からの再計算を削除し保存値をそのまま採用 | aggregate 改竄の負例テスト赤 |

前後に同じ入力を拒否する層が無いこと、無効化時の赤理由が 1 つに絞れることを、
実装後・fix 後の最終 commit で `DW-M07` に従い再検証する。

## 6. 不変条件 (実装子への拘束)

- `if False:` 下の呼び出し・未使用 string literal・`pass` だけの wrapper を書かない。
  評価器がそれらを受理することは既知だが、本 wave はそれを利用しない (A-7)。
- production の検査を緩めて fixture を通さない。fixture 側を直す。
- `"certifying": True` を発行する枝を作らない。
- 契約 JSON・評価器・凍結 record・producer の既存 layer3 呼び出しを変更しない。
- 相対 path を process cwd 基準で解決しない。
