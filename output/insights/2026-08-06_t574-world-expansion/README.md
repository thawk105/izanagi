# [T-574] 残余 — production consumer への world 拡大分の閉包

契約世代を進めても publish 済み成果物を再検証できるようにする配線 ([T-574]) の残余を扱った wave の
一次資料。branch `worktree-dev-wave-t574-world`。前 wave は
`output/insights/2026-08-06_t574-historical-resolver/` (worklog エントリ 262)。

## 結論

**historical resolver を新たに配線すべき read-only 再検証 consumer は残っていない。**
残余は裁定済み 3 項の消化だった。ただし **[T-529] の blocker は外れていない** (下記)。

## 何をしたか

| 項 | 対象 | 結果 |
|---|---|---|
| A | [T-588] `s8b_oracle_report._receipt_expectations` の fail-open | 締めた。宣言済み `run_contract` の identity 欠落・空・非 str を resolver より前に拒否 |
| B | [T-587] 契約世代を跨いだ resume | current-only resume を正式仕様として回帰試験で固定 (production code は不変) |
| C | [T-586] silo `verify-result` | current 互換検査と明示して終端。decisions は新設しない (重複のため) |
| D | [T-574] 閉包 | 全 site の分類 inventory を下記に置き、残 blocker を明示 |

## 保証しないこと

- **A の gate は今日どの成果物に対しても発火しない。** `run_contract` を宣言した publish 済み
  artifact は 0 件で、`s8b_oracle_manifest.build_manifest` / `write_manifest` の production caller も
  0 件である (親が grep で実測)。よって A は**既存の受理集合を 1 件も変えない**。
  変わるのは将来 v2 manifest producer が現れて以降だけである。
- **A の診断は manifest 全域には効かない。** `receipt_expectations_error` が行へ載るのは
  campaign-start が一意で schedule row を持つ campaign の観測経路だけで、directory 欠落・
  WAL read error・terminal issue の早期 return と 0-row campaign では載らない。
  この限定を docstring に書き、`manifest-global` の語を成果物で使わない (D203 と同型の規律)。
- **B は実際の世代発効 (activation) を模していない。** 実 registry は bootstrap fuse により
  単一世代のままであり、試験は module 属性の局所差し替えで「registry に g1 が残り current が g2 へ
  進んだ」状態を模したものである。

## 記録 contract hash と current registry の比較 site — 全 inventory

段 1 の親の列挙は不完全だった (段 3 の 2 レンズが独立に指摘)。訂正した全体像を置く。
**resolver を新たに配線すべきものは 1 件も無い。**

| 分類 | site | 理由 |
|---|---|---|
| **historical resolver 配線済み (read-only 再検証)** | `s8b_ratified_freeze._validate_published_protocol` (2803-2837) / `reverify_published_freeze` (3244-3254)、`s8b_oracle_report._receipt_expectations` (1189-1231) | 前 wave (262) で配線 |
| **live/current admission (D202 により current 据置)** | `s8b_floor_campaign` (308-324, 410-440, 1865-1882, 2750-2790)、`s8b_oracle_driver` (745-805, 770)、`s8b_ratified_freeze` (976, 2769-2775)、`loop.py:62`、`p3_s4_loop_trigger_gating.py:313`、`pipeline.py:535`、`t126_driver.py` (496, 868) | 履歴解決へ切り替えると旧世代の証拠と現世代の receipt を混成した新規実走が受理されうる |
| **current 互換検査と裁定済み** | `silo_ladder_rung1.py` (3511-3542, 4832-4841) = [T-586]、floor campaign の resume 経路 = [T-587] | ユーザー裁定でそれぞれ (b) / (a) |
| **記録 contract を持たない artifact reader** | `s8b_prediction_runner` (1457-1473)、`s8b_selector_freeze` (879-905)、`s8b_verdict` (199-213)、`autonomous_trial_completeness` (1082-1188)、`s8b_holdout_freeze.verify` | 検証はするが `contract_sha256` を持たないので世代解決の対象外 |
| **非 certified probe / 調査 driver** | `pegasus_floor_scoping.py:74`、`tools/pegasus/probes/t419_probe_causality.py:3388` | certified consumer へ接続しない |

## [T-529] の blocker は外れていない

段 1 brief は「[T-529] を unblock する」と書いたが、段 3 レンズ B が 2 点で覆した。親が裏取りして採用した。

1. **R1 (記録 hash を世代選択の権威にしてよいか) がユーザー裁定待ちのまま**である。
   resolver が証明するのは形式・登録・一意性・env 一致だけで、「その世代が artifact 作成時に
   active だった」ことは証明しない。これは [T-529] (活性化権限) の前提そのものである。
2. **historical 経路に production 正例を書けない。** `reverify_published_freeze` の唯一の
   production loader である `load_ratified_freeze` は、live active pointer が無ければ
   `no-active` で失敗する (`s8b_ratified_freeze.py:1256`)。v2 が未発効の今日、publish 済み
   `output/s8b-freeze/floor_protocol.json` を実際に読む経路は current 束縛の floor driver だけである。
   `DW-G04` (発火条件を満たす artifact path か計測 ID を書けること) を満たさない。

したがって D196 (3) は「配線すべき consumer を洗い出して配線し切った」ところまでが済んでおり、
「発火する正例を持つ」ところは済んでいない。

## 実測 (親が自分で走らせた値)

- 受入全走: **7066 passed / 20 skipped** (`child_rc=0`)。これが land した tip `ff63ef72`
  (main `23337171` 取り込み後) を certify した値である。
  途中の **6846 passed / 20 skipped** は main `0d64599e` を取り込んだ時点 (`f264a269` 相当) の値で、
  その後の main 取り込みでテスト数が増えた。**worklog エントリの題は 6846 のまま land した** —
  題に書いたのは land 直前の再走前の値であり、certify 値は 7066 である (erratum)。
- 変異 run 2 (採用): **4/4 一致、全 KILLED**。
- 変異 run 1: **erratum** (M4 の変異が非 Mapping 経路も巻き込み、事前登録外 2 node を落として
  MISMATCH。field 不在経路だけに絞って再照準したものが run 2)。消さずに残す。
- `check_ai_provenance.py`: 1577 件中 5 違反。**5 件すべて別セッション
  (`worktree-rulings-20260806-a`) の既存 merge commit** で、本 wave の commit は clean。

### 変異 matrix

| ID | 変異 | 期待 | 結果 |
|---|---|---|---|
| M1 | `_receipt_expectations` の `env_tag` 非空検査を削除 | KILLED (env-tag 3 ケース) | **KILLED・一致** |
| M2 | 同 `contract_sha256` 非空検査を削除 | KILLED (contract-sha256 3 ケース) | **KILLED・一致** |
| M3 | `s8b_floor_contract.py:149` の current hash 不一致検査を削除 | KILLED (resume 負例) | **KILLED・一致** |
| M4q | `run_contract` field 不在を `{}` へ倒す (過剰拒否の正例) | KILLED (legacy 正例 + mixed-legacy) | **KILLED・一致** |

M3 が本 wave の要である。段 2 の当初案 (例外型だけを pin) では M3 が **SURVIVED** になる —
`attestation_mode="none"` の calibration loader は grandfathered v1 bytes だけを受理するため、
current guard を消しても合成 g2 の calibration 読込みが必ず失敗して同じ例外型になるからである。
段 4 で calibration loader の呼出し回数 0 という**因果 pin** へ差し替えて実効 gate にした。

## ファイル

| file | 内容 |
|---|---|
| `brief.md` | 段 1 brief。**実測 4・5 と P1 の根拠、P3 が段 3・4 で訂正されている** (下記) |
| `s4-adjudication.md` | **段 4 裁定 (実装の正本)**。親の裏取り 6 点を含む |
| `s6-fix-ruling.md` | 段 6 fix 裁定。R2-1 を blocker にしない根拠を含む |
| (段 2・3・6 の子逐語) | job artifact `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t574-world/` に置いた |
| `mutation-spec.json` / `mutation-ledger.json` | 変異 run 2 (採用) |
| `mutation-spec-run1-erratum.json` / `mutation-ledger-run1-erratum.json` | 変異 run 1 (erratum、消さずに残す) |

## 段 1 brief の誤り 3 点 (段 3・4 で訂正済み)

1. **実測 4「`MappingProxyType` で 2 世代の試験注入が構造的に塞がれている」は誤り。**
   封じられているのは backing mapping の要素更新だけで、module 属性の局所 patch は既存慣行である
   (`test_env_contract.py:618-632`)。B の fixture 設計を誤らせた。
2. **実測 5 の site 列挙が不完全。** 上の inventory が訂正版である。
3. **(P3) の「未知 hash で世代跨ぎを模す」案は不十分。** 世代跨ぎ固有の退行を検出できない。
   段 2 が正しく退け、段 4 が因果 pin へ差し替えた。

なお **(P1)「配線すべき consumer は残っていない」は両レンズの独立攻撃を耐えた**。

## ユーザー裁定待ちの択一 (実装していない real 所見)

| # | 択一 | 重さ | 根拠 |
|---|---|---|---|
| R9 | **`_receipt_expectations` の診断を manifest 全域へ効かせるか。** (a) 現状受容 — 適用層を明記して閉じる (本 wave の採用) / (b) 0-row・早期 return 経路にも載る top-level structured issue を新設する | 中 | (b) は observations の issue/reason または report CLI の受理集合を変える。D205 により既定は (a) |
| R10 | **v2 oracle manifest の production producer をいつ作るか。** `build_manifest` / `write_manifest` の caller が 0 件で、v2 manifest を発行する経路が実装されていない | 中 | A の gate も C3-10 の receipt 検査も、この producer が現れるまで一切発火しない |
| R11 | **`reverify_published_freeze` の production 到達性をいつ確保するか。** active pointer 未発効で唯一の loader が `no-active` で落ちる | **重** | historical 再検証の正例を書けない原因。[T-529] の blocker (2) と同一 |
| R12 | **report source bytes の変更が `generator_versions.report` pin を動かす件をどう扱うか。** (a) 設計どおりとして受容 (本 wave の採用) / (b) rollover 手順を明文化する | 小 | byte pin の意味論そのもので、どんな編集でも起きる。発行済み manifest 0 件のため既存受理は不変 |

R11 と、前 wave から持ち越しの R1 が [T-529] の骨格を決める。
