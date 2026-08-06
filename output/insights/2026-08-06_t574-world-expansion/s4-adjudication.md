# 段 4 裁定 — [T-574] 残余 (production consumer への world 拡大分)

段 3 の 2 レンズはいずれも NO-GO を返した。親が各所見を裏取りし、real/refuted と採否を確定する。
**本ファイルが実装の正本**であり、段 2 プランと段 1 brief より優先する。

## 親が自分で裏取りした事実

段 3 の主張を鵜呑みにせず、次を親が直接コードで確認した (F142 の教訓)。

1. **`mode=none` の calibration loader は grandfathered v1 bytes だけを受理する**
   (`env_attestation.py:1119-1121`)。正当な後継世代は calibration path/sha を必ず変えるので
   (`env_contract.py:202-228`)、合成 g2 の calibration 読込みは**必ず**失敗する。
   → 例外型だけを見る B の試験は恒真になる。**レンズ A 所見 1 / レンズ B 所見 4 は real。**
2. **2 世代 mapping の試験注入は既存慣行である。** `test_env_contract.py:618-632` が
   `monkeypatch.setattr(ec, "_CONTRACT_SHA256_INDEX", index)` で合成 2 世代 index を注入している。
   → 親 brief の実測 4「注入経路が構造的に塞がれている」は**誤り**。封じられているのは
   backing mapping の要素更新だけである。
3. **「発行済み oracle manifest 0 件」は decisions.md の D (3) 内に既記録である**
   (`docs/decisions.md:3677-3679` 近傍、"発行済み oracle manifest 0 件を output/ 全域 grep で機械確認")。
   → [T-588] の裁定を止めるべき「裁定時点で未見の新事実」ではない (`DW-S04`)。
4. **`build_manifest` / `write_manifest` の production caller は 0 件**である
   (`orchestrator/` と `tools/` の grep で、定義ファイル内の型検査 message 以外に hit なし)。
5. **`load_ratified_freeze` は唯一の実走 loader で、live active pointer が無ければ
   `no-active` で失敗する** (`s8b_ratified_freeze.py:1256`, `:1315-1334`)。
   → `reverify_published_freeze` は今日 production から到達不能。**レンズ B 所見 1 は real。**
   ただしこれは前 wave の `parent-measured.md:28-32` が既に限定として記録済みであり、新事実ではない。
6. **current guard は calibration 読込みより前に走る** (`s8b_floor_campaign.py:2750` →
   `s8b_floor_contract.py:149`、calibration は `:2762`)。この順序が B の再設計の土台になる。

## 所見裁定表

| # | 出所 | 所見 | 裁定 | 採否 |
|---|---|---|---|---|
| 1 | A-1 / B-4 | B の提案試験は current guard を壊しても後段 calibration 失敗で緑 (恒真) | **real** | **採用 — B を再設計** |
| 2 | A-2 | 「MappingProxyType なので 2 世代を注入できない」は誤り | **real** (親 brief の誤り) | 採用 — B の fixture を 2 世代一貫 patch へ |
| 3 | A-3 | monkeypatch 自体は `DW-O14` 違反ではない (正規 seam 不在を確認済み) | refuted | — |
| 4 | A-4 | A は live oracle admission へ漏れない。段 2 の「driver も caller」は誤記 | refuted (漏出) / real (誤記) | 誤記のみ訂正 |
| 5 | A-5 | A は真の legacy を壊さない。official v2 の非 Mapping は verifier が先に拒否 | refuted | 説明のみ訂正 |
| 6 | A-6 | A の例外は「manifest-global」ではない (early return / 0-row で消える) | **real** | **採用 — 保証名を狭める** |
| 7 | A-7 / B-6 | 親の実測 5 の site 列挙は不完全 | **real** | 採用 — D の inventory を訂正 |
| 8 | A-7 / B-6 / B-7 | P1「配線すべき read-only consumer は残っていない」への反例 | **refuted** (両レンズが独立に攻撃不成立と判定) | P1 維持 |
| 9 | A-8 | 凍結 bytes・path pin・role pin への影響なし | refuted | 記録のみ |
| 10 | B-1 | `reverify_published_freeze` は active pointer 不在で production 到達不能 | **real** | **採用 — D を「完了宣言」から反転** |
| 11 | B-2 | R1 未解決のまま [T-529] unblock を宣言するのは矛盾 | **real** | **採用 — blocker を明示** |
| 12 | B-3 | A は発火 artifact 0・producer 不在で `DW-G04` に反する | real (事実) / **裁定は止めない** | **A は実装する** (下記) |
| 13 | B-5 | B は仕様と一致し既存被覆と重複しない | refuted | B を残す |
| 14 | B-8 | C は訂正先が無く worklog が既に終端している | **real** | **採用 — decisions 新規を作らない** |
| 15 | B-9 | brief の `DW-G05` 4 項は誇張 | **real** | 採用 — 書き直す |

## 裁定 1 — A ([T-588]) は実装する。ただし保証名を狭める

**実装する理由。** `DW-S04` は「承認済み裁定を止めてよいのは裁定時点で未見の新事実がある場合だけ」
と定め、さらに「根拠の事実が裁定文・worklog に既記録でないか確認する」ことを求める。
レンズ B が挙げた根拠 (発行済み manifest 0 件) は裏取り 3 のとおり **decisions に既記録**である。
よって新事実ではなく、[T-588] (a) の裁定は有効。親が不採用にしてはならない。

**ただし `DW-G04` の指摘自体は real なので、成果物に正直に書く。**

- 発火する artifact は今日 0 件。`build_manifest` / `write_manifest` の production caller も 0 件。
- したがって A は**既存の受理集合を 1 件も変えない**。変わるのは将来 (または手動投入) の
  schema-less manifest で `run_contract` を Mapping 宣言しながら identity field が
  欠落・空・非文字列のものだけである。
- worklog にはこの射程をそのまま書く。「proof chain の穴を塞いだ」とは書かない。

**保証名を狭める (レンズ A 所見 6)。** `receipt_expectations_error` は
`campaign-start` が一意で schedule row を持つ campaign の査定経路にしか載らない
(`s8b_oracle_report.py:1367`, `:1382`)。directory 欠落・WAL read error・terminal issue の
早期 return (`:1276`, `:1280`, `:1336`) と 0-row campaign (`:1696`, `:1711`) では診断が消える。
D203 と同型の「名ばかりの保証」を避けるため、

- コード・docstring・テスト名・台帳で **`manifest-global` の語を使わない**。
- 適用層を「campaign-start が一意で row のある campaign の observation」と明記する。
- 0-row / 早期 return 経路への top-level issue 新設は **scope 外** (D205: 防御的堅牢化は既定で見送り)。
  択一として返す。

**実装内容** (段 2 プランの A を、上記の名前縮小を除いてそのまま採用):
`_receipt_expectations` の Mapping 分岐で `env_tag` と `contract_sha256` を独立に検証し、
非空 str でなければ `ReportError` を送出する。末尾の fail-open `return None` を削除する。
非 Mapping と field 不在の既存挙動は変えない。

## 裁定 2 — B ([T-587]) は実装する。設計を v2 へ差し替える

段 2 の推奨 (未知 hash の否定は正しいが、代替の lookup-only patch + 例外型 pin) は**不採用**。
恒真だからである (裏取り 1)。次の v2 を実装する。

**fixture**: `test_env_contract.py:618-632` の既存慣行に倣い、現行 g1 と
`is_valid_successor` を満たす合成 g2 から 2 世代 mapping を作り、
`GENERATIONS` / `REGISTRY` / `_CONTRACT_SHA256_INDEX` を**一貫して**局所 patch する。
lookup だけを差し替えない (レンズ A 所見 2)。g1 が index に残ることが重要である —
将来 resume を historical resolver へ誤配線した改修は、g1 が解決できてしまうため
resume が通り、試験が赤になる。

**因果の pin (恒真回避の要)**: 例外型だけを見ない。
`s8b_floor_campaign` から見える `env_attestation.load_verified_calibration` を、
呼出しを記録して元実装へ委譲する spy で包み、**呼出し回数 0** を assert する。
current guard (`s8b_floor_contract.py:149`) を外すと制御が `:2762` へ進んで spy が呼ばれるため、
この assert が変異を殺す。あわせて measure callback 未呼出しと journal bytes 不変も assert する。
**診断文字列 (`match=`) は pin しない** — 揮発する payload を期待値へ焼き込まないため。

**通る正例 (`DW-S04` の要求)**: current が g1 のまま (patch なし、または g1 を返す patch) の
同じ resume が正常に進むことを 1 本添える。試験の setup 自体が原因で落ちていないことを示す。

**模擬と実の差 (docstring へ明記)**: 実 registry は bootstrap fuse により単一世代のままであり、
本試験は「registry に g1 が残り current が g2 へ進んだ」状態を module 属性の局所差し替えで
模したものである。実際の世代発効 (activation) を模してはいない。

## 裁定 3 — C ([T-586]) は decisions を新設せず worklog で終端する

レンズ B 所見 8 のとおり「全 certified 成果物を再検証可能」という肯定表現は D196 本文に無く、
現行 worklog の [T-586] 項が既に「current 互換検査と明示し当該表現から除外する」と書いている。
新規 decision は重複であり、docs 予算を無駄に食う。

よって C は、本 wave の worklog fragment と insights で
「silo `verify-result` の binding 層は current 互換検査であり、記録 hash からの歴史再検証の対象外。
[T-586] は裁定どおり終端」と記録して消化する。decisions への新規 D は作らない。
D196 本文も書き換えない。

## 裁定 4 — D は「完了宣言」から「正直な閉包 + 残 blocker」へ反転する

**維持する結論 (P1)**: 記録 `contract_sha256` を current registry と比較する production site のうち、
historical resolver を新たに配線すべき read-only 再検証 consumer は**残っていない**。
両レンズが独立に攻撃を試みて反例を出せなかった (所見 8)。

**訂正する点**:

- 親の実測 5 の列挙は不完全だった。レンズが挙げた欠落 site
  (`s8b_ratified_freeze.py:2769`, `loop.py:62`, `p3_s4_loop_trigger_gating.py:313`,
  `pegasus_floor_scoping.py:74`, `t419_probe_causality.py:3388`,
  `s8b_prediction_runner.py:1457-1473`, `s8b_selector_freeze.py:879-905`,
  `s8b_verdict.py:199-213`, `autonomous_trial_completeness.py:1082-1188`) を inventory へ足し、
  各々を「live/current admission」「current 互換 (裁定済み)」「記録 contract を持たない reader」
  「非 certified probe」へ分類する。inventory は insights に置き、worklog には要約だけ書く。
- **[T-529] を unblock しない。** 残る blocker を worklog に明示する:
  (i) R1 (記録 hash を世代選択の権威にしてよいか) がユーザー裁定待ちであること、
  (ii) v2 active pointer が未発効で `reverify_published_freeze` が production 到達不能なため、
  historical 経路の production 正例を今日書けないこと (`DW-G04` と同型の欠落)。
- D196 (3) は「配線すべき consumer を洗い出して配線し切った」ところまでが済んでおり、
  「発火する正例を持つ」ところは済んでいない。この二分をそのまま書く。

## `DW-G05` 成果物影響 (書き直し)

| 項 | 実装しない・放置した場合に成果物のどの値・受理集合・参照がどう変わるか |
|---|---|
| A | 現在の certified 選択・レポート・台帳は **0 件変化しない**。将来 v2 manifest producer が現れたとき、`run_contract` を宣言しながら identity が不完全な schema-less manifest を oracle report が受理し続け、その campaign の row が contract / calibration / execution receipt の束縛なしに `completed` へ到達しうる |
| B | 現在値は変わらない。放置すると、将来 resume を historical resolver へ誤配線した改修が無検出で入り、旧世代 protocol の中断 run を現世代環境で再開して journal に世代混在を持ち込む受理拡大を許す |
| C | 値・受理集合・参照はいずれも不変。台帳の主張範囲だけが正直になる (nit だが裁定済みの終端義務) |
| D | 偽の完了記録を入れると、[T-529] の依存参照が実際には未充足のまま解除され、活性化権限の実装が「前提は済んだ」という誤った土台の上に載る |

`DW-G05` により、A と C は **must-fix ではない**。B と D が本 wave の実質である。

## scope 外へ返す択一 (裁定パッケージ候補)

| # | 択一 | 根拠 |
|---|---|---|
| R9 | **`_receipt_expectations` の診断を本当に manifest 全域へ効かせるか。** (a) 現状受容 — 適用層を明記して閉じる / (b) 0-row・早期 return 経路にも載る top-level structured issue を新設する | 現状 (a) を採った。(b) は受理集合ではなく observations の issue/reason または report CLI の受理集合を変える。D205 により既定は (a) |
| R10 | **v2 oracle manifest の production producer をいつ作るか。** `build_manifest` / `write_manifest` に caller が 0 件で、v2 manifest を発行する経路が実装されていない | A の gate も C3-10 の receipt 検査も、この producer が現れるまで一切発火しない。Phase 3 の後続段の順序に関わる |
| R11 | **`reverify_published_freeze` の production 到達性をいつ確保するか。** active pointer が未発効のため、唯一の loader が `no-active` で落ちる | historical 再検証の正例を書けない原因。[T-529] の blocker (ii) と同一 |

## 変異事前登録 (`DW-M01`)

実装前に登録する。各変異は「同じ入力を拒否する層が前後に無いこと」「無効化時の赤理由が一つに
絞れること」をコードで確認済みである。

| ID | 対象 | 変異内容 | 期待 | 単一理由性の確認 |
|---|---|---|---|---|
| M1 | `s8b_oracle_report._receipt_expectations` の `env_tag` 非空検査 | 検査を削除 (fail-open へ戻す) | KILLED — A の新規 test の `env_tag` 3 ケース | 前後に同入力を拒否する層なし (schema-less Legacy 経路、official verifier は分類が別。裏取り: `s8b_oracle_artifacts.py:131`) |
| M2 | 同 `contract_sha256` 非空検査 | 検査を削除 | KILLED — A の新規 test の `contract_sha256` 3 ケース | 同上 |
| M3 | `s8b_floor_contract.py:149` の current hash 不一致検査 | 検査を削除 | **KILLED — B v2 の calibration spy 呼出し回数 0 の assert** | この変異こそ段 2 案では SURVIVED になる。v2 の因果 pin が実効 gate である |
| M4 | 正例 (受理集合の過剰縮小検出、`DW-M01` 後段) | `run_contract` field を持たない真の legacy manifest | 全 4 本の legacy 受理 test が緑のまま | A が承認外の過剰拒否をしていないことの正例 |
| M5 | `DW-M08` の新旧両走 | B v2 の新テストを、変更前 HEAD 版テストとともに M3 変異へ掛ける | 新テストだけが M3 を検出する | テスト強化だけの単位なので新旧差分を示す義務がある |

`hang_risk` は無し。harness は `tools/mutation_harness.py` を使う (`DW-M05`)。

## 実装単位の分割 (所有は素集合)

| 単位 | 所有ファイル |
|---|---|
| 実装子 1 (A) | `orchestrator/campaign/s8b_oracle_report.py`、`orchestrator/tests/test_s8b_oracle_report.py` |
| 実装子 2 (B) | `orchestrator/tests/test_s8b_floor_campaign.py` |
| 親 (C・D・記録) | insights、spool fragment、統合・変異・受入・commit |

A と B にコード依存はなく並列投入できる。実装子は docs を編集せず commit もしない。
