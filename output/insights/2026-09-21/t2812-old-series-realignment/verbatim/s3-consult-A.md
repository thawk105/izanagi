## must-fix

1. **real — 「段階4を塞ぐのは policy だけ」は、plan の訂正後も広すぎる。**
   `G1-BIN-HIST` が通したのは個々の `validate_portable_binary_record(expected_policy=None)`。段階4全体ではない。manifest の後には journal 検証、共有 admission 台帳の現況検査、result 検証、最初の適格な床値を選んだことの検査が残る（`s8b_ratified_freeze.py:3408,3428,3463,3471`）。しかも `:3167–3176` は **現行 contract** を要求するため、brief N3 の「現行に縛られるのは expected_policy だけ」も誤り。
   **訂正文:**「現在観測した最初の拒否は manifest 内の binary policy 不一致。12 receipt の個別歴史検証は成功。段階4の残部と段階5以降は未確認」。

2. **real — READONLY の証明範囲を拡大している。**
   brief:7 の「3木の…binary store が前後で不変」に対し、`probe-2 / READONLY` が持つ store 観測は `binary_store_before=false / after=false`。status 一致も、既に untracked な WAL・lock の内容変更を検出しない。
   **訂正文:**「3木の porcelain 出力と submodule HEAD、および観測対象 store の存在判定が一致」。全 bytes 不変や測定時 source 不変の証拠には数えない。

3. **real — S' の失効保証は、policy に符号化された値の変更に限定する必要がある。**
   plan の失効説明は registry の削除について正しい。ただし `_new_policy()` が持つのは schema、pin、authority の文字列、generator/review の名前集合だけ（`build_admission.py:499–507`）。generator の実装、review の意味、coder entrypoint registry 全体、enforcement closure は入らない。`POLICY-SERIES-PIN` の一致から「admission の意味も不変」「現在まで失効が一度もない」は導けない。
   これは **S' に固有の新しい穴ではなく既存保証の限界**。裁定パッケージで「現行 registry を維持」を「現行の正しさ保証を全面維持」へ拡張しないこと。

4. **refuted — S' にすると別 pin・別 contract・失効 registry の artifact がそのまま通る、という攻撃。**
   plan どおり外部期待値を維持する条件では、以下は拒否される。

   | 攻撃入力 | 拒否する根拠 |
   |---|---|
   | source を別 full OID にした record | `s8b_binary_admission.py:434–435` |
   | 先頭7桁だけ同じ別 OID | 同じ full OID exact 照合 |
   | 別 contract の receipt | 同 `:436–438`。protocol 自体も `s8b_ratified_freeze.py:3173–3176` |
   | 現在の名前集合と異なる registry の policy | `build_admission.py:505–506` → SHA 不一致、`s8b_binary_admission.py:371` |
   | store 内 binary の差し替え | `s8b_oracle_driver.py:1043–1052` |
   | coder-authored receipt の混入 | `s8b_binary_admission.py:362–365` |

   **この検査で、正しく実装した S' に固有の具体的な不正受理例は見つからなかった。** 全攻撃の不存在や live 成功を証明した意味ではない。

## should

- **S' が保つもの／失うものを明記する。**

  | 性質 | S' の扱い |
  |---|---|
  | generator/review 名前集合の変更による失効 | 保持。追加でも SHA が変わる |
  | coder authority 種別の epoch | 保持。ただし元から CLI 発行事実の再証明ではない |
  | policy schema 世代 | 保持。receipt schema の検査も別に残る |
  | 現行 repository の stock pin と同じ policy epoch であること | **失う。系列 pin の epoch へ置き換える** |
  | 測定 source と批准 protocol の対応 | full OID の別検査で保持 |
  | admission 実装・意味論全体の同一性 | 元からこの policy SHA の保証外 |

  coder entrypoint 情報は永続 receipt・WAL・cache identity に入らないことが `build_admission.py:474–479` に明記されている。

- **規律7を比較の一律禁止へ広げない。**
  plan:39 の「epoch 間の数値差を改善・退行・同等性の証拠にしない」は、今回の pair 不成立・条件差に限定すべき。policy epoch 差だけで比較不能とはならない。D2187 が禁じたのは今回の候補単独結果を pair／改善の証拠へ昇格すること。不要な一律再測定を要求しない。
  逆方向については、plan は historical と live を明示的に分けており、「旧判定不変だから現在も certified」という直接の格上げ論法は確認しなかった。

- **H の provenance 欠落という疑いは refuted。ただし HEAD 単独では再構成できない。**
  `patchharness.py:174–201` は submodule の HEAD と tracked 変更を見るが、親 gitlink と照合しない。A-1 v3 の親 status は明示的に submodule を除外する（`paper_story_a1_paired.py:2432–2438`）。
  一方、記録済み pair lock:1 の `identity_preimage.ccbench_commit` は full `511c…`、admission preimage は `repo_stock_pin=e9e477c`、authority は `contract_loader_commit=6a3e158…`。測定 source と親側 epoch は区別して残る。T-2795 README:45–56 も gitlink／checkout の差と receipt source を記録している。
  したがって「H の source が記録されない」は誤り。「親 HEAD を通常 checkout するだけでは測定木を再現できない」が正確。digest だけでは失われた source bytes を復元できない点は残る。

- **誤実装に対する負例を具体化する。**

  | 案 | 静かに通す危険な誤実装 | 必要な検査 |
  |---|---|---|
  | S' | resolver 失敗を `None` にして歴史分岐へ落とす | resolver 例外で live 拒否。`:368` は `None` を拒否しない |
  | S' | receipt 由来 pin を期待値にする | caller のデータ経路を検査。exact 型だけでは pin の出所を証明しない |
  | O' | 旧 branch に存在しない現行 gate を未移植のまま「現行相当」とする | branch 自身で閉包・負例を検証。main の結果で代用しない |
  | N | generation 制限だけを削除する | 新世代の証明書・chain 束縛を設計し、世代混在を拒否 |
  | K2／A-1 | claim や prior barrier を一括解除する | 認可範囲外の再取得・prior を拒否 |
  | B-4 | HEAD／spec／binary 束縛を外して移転する | 旧 w1 と新 HEAD の組合せを拒否 |

## nit

- plan の resolver 未commit拒否の参照は `s8b_floor_campaign.py:984` より **`:983`** が正確。`:983` の HEAD blob 取得で不在を拒否し、`:984` は取得済み bytes の比較。
- 「`s8b_holdout_freeze` は launch から呼ばれない」とファイル全体へ一般化しない。`:1387,1522` の **`_validate_floor_inputs` は呼ばれない**が、同ファイルの `_assert_floor_selection_identity` は呼ばれる。第三の policy consumer という疑いは、`:1952–1987` まで追って refuted。
- `READMIT-STOCK` の名前・トップレベル `call` は実処理より強い。g1/B-4 の各 check は `registry membership only`。plan の訂正を最終成果物にも残す。

## 観測が支えていない主張

| 主張 | 実際の到達範囲 |
|---|---|
| S' で段階4を完走できる | 個別 receipt の歴史検証と SHA 到達可能性まで |
| S' 後に別の拒否は出ない | journal、共有台帳、result、床値選択、段階5–8が未確認 |
| W-5 の実行準備が整う | approved spec は `None`。store・環境・reservation・予算等も未通過 |
| H なら A-1 attempt-0003 が走る | boundary／source 検査だけ。認可列挙は0002のみ |
| 新 main の K2 pair が成立する | 過去 HEAD の候補成功だけ。stock は build 未到達 |
| registry が admission 時から継続して不変 | 現在との値の一致。途中の変更・復元や意味変更は未証明 |
| 再 admission 成功を実測した | membership 確認。receipt 再発行は未実施 |
| READONLY が全 artifact bytes 不変を証明する | status・HEAD・存在判定の一致だけ |

`g1-gate-check.json` は `allowed:false`、拒否2件、held checks 3件。候補削除後の成功も、この記録からは言えない。

## 私が確かめた file:line

以下のコード名は `orchestrator/campaign/` 配下。

- **policy／receipt:** `build_admission.py:48–52,474–507,528–545,674–705`、`s8b_binary_admission.py:324–479`。型・SHA・class・source・contract・subject の説明は上記限定付きで一致。
- **g1／W-5:** `s8b_ratified_freeze.py:1905,3167,3273,3330,3369,3394,3408,3428,3471,3609`、`s8b_oracle_driver.py:659,1003–1052,1340,1441,1759`。二つの直接 policy consumer という記述に反例は確認できなかった。
- **間接経路:** `s8b_floor_stats.py:1112–1192`、`s8b_holdout_freeze.py:1375,1522,1889–1987`。共有台帳の現況検査と床値選択を確認。
- **K2／H:** `p3_s4_loop.py:116,2005,2089,3369,3390`、`patchharness.py:174–201`、`source_digest.py:2413–2463`。stock capability と source 記録を確認。
- **A-1:** `paper_story_a1_paired.py:228,2390,2432,2715,2795,2970,3478,8406`、`paper_story_a1_source.py:68,95`。0003・prior 集合の指摘は一致。
- **lock／WAL:** `campaign_lock.py:491`、`ident.py:84,121,350,412`、`wal.py:2130,2145,2800`。歴史型と live 型の分離は一致。
- **B-4／reseal:** `s8b_floor_campaign.py:983,1032,1110,4836,5825,5884,6495,8149`、`b4_binary_record.py:140,170,185`、`floor_pair_driver.py:1091,1136`、`tools/pegasus/submit_floor_pair.sh:173`。現行配置と歴史消費の区別は一致。
- **閉包:** `tools/pegasus/b10_backoff_grid.sh:585,596,648`、`orchestrator/tests/test_backoff_extended_sweep.py:1670,2025`。追加 protocol が aggregate hash を変える説明は一致。

## 総括

**S' は条件付きの設計候補として支持する。ただし「policy 以外は通る」「現行の正しさ保証を全面維持」は未証明。** 失う性質は repository pin による epoch 束縛であり、残す full source・contract・chain・binary 検査を個別に説明すべき。

P1は候補経路だけ、P2は0003認可前提、P3は未実装の候補、P4は固定木継続、P5はSHA束縛からの静的帰結として同意する。テスト・測定は実行しておらず、live 成功を緑とは記録しない。