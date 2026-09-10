### RA-01 — method 判定は forward-only ではなく、過去の遷移を現行定数で再判定する

- 主張: serial 2 以降の authority はロードのたびに全遷移を再生するため、将来 `EFFECTIVE_CLOCK_METHOD` が更新されると、既に active な g2 の g1→g2 遷移まで新定数で拒否される。g3 発行前に現 authority 自体が読めなくなり、裁定の「これから active にする世代だけを狭める」を満たさない。
- 証拠: `orchestrator/campaign/env_contract.py:475-477` は successor の method を可変な現行定数と比較し、`orchestrator/campaign/env_contract_activation.py:365-401` はロード時に過去の全遷移へ callback を再適用する。通常 loader と issue tool はそれぞれ `orchestrator/campaign/env_contract.py:570-577`、`tools/issue_env_contract_activation.py:178-213` からこの再生を通る。裁定は forward-only としている (`s4-adjudication.md:63-65`)。
- 成果物影響: probe 方式更新時に current authority、次世代 activation 発行、新規 certified 選択、記録済み activation tuple の参照がすべて停止する。
- severity: **land 阻止**

### RA-02 — 既存の issue-tool 正例 2 件は静的に失敗する

- 主張: 2 テストは `_repository_root` を空の `tmp_path` に差し替えたまま g2 を発行する。composite はその root から g2 calibration を strict load するため、artifact 不在で `False` となり、期待する `main()==0` へ到達しない。
- 証拠: テストが作るのは authority record だけで、root 差替えは `orchestrator/tests/test_env_contract_activation.py:2334-2366` と `:2396-2438`。g2 の calibration path は `orchestrator/campaign/env_contract.py:262-271`、存在必須の解決は `orchestrator/campaign/calibration_verify.py:97-104`、失敗の `False` 化は `orchestrator/campaign/env_contract.py:450-464`、issue の終了は `tools/issue_env_contract_activation.py:205-216`。実装報告自身も pytest 緑 0 件としている (`s5-unitA.md:20-30`)。
- 成果物影響: land 後の受入が赤になり、activation 発行経路を検証済みとして扱えない。
- severity: **land 阻止**

### RA-03 — `ident.py` の composite 配線を戻す変異が生存する

- 主張: `ident.py` の 2 配線を構造判定へ戻しても、今日の serial 1 では callback が一度も呼ばれない。追加差分には serial 2 の recorded tuple を `ident.verify_recorded_activation_tuple` で検証するテストがない。
- 証拠: 配線は `orchestrator/campaign/ident.py:217-225` と `:306-313`。callback 発火は第 2 record 以降だけ (`orchestrator/campaign/env_contract_activation.py:395-401`) で、現 head は serial 1 (`orchestrator/campaign/env_contract.py:373-379`)。既存 ident consumer テストは serial/state の改竄だけ (`orchestrator/tests/test_artifact_admission.py:1639-1689`)。
- 成果物影響: 将来、不正な serial 2 successor を記録した campaign.lock が resume・台帳認証経路で受理される回帰を検出できない。
- severity: **fix**

### RA-04 — 許可外の既存テスト弱体化がある

- 主張: 65-env の既存正例で composite 自体を旧構造判定へ置換しており、production issue-tool の artifact admission を通さない。件数 2→3 と callback identity 2 件以外の変更を許可しない条件に反する。
- 証拠: `orchestrator/tests/test_env_contract_activation.py:2638-2664` が `_is_valid_activation_successor_with_artifact` を `_is_valid_activation_successor` へ monkeypatch している。実装報告もこの追加を認める (`s5-unitA.md:14-16`)。不変条件は既存テストを緩めないとしている (`brief.md:60-64`)。
- 成果物影響: 多数 env の activation 発行で artifact gate が抜ける回帰を、発行成功テストが見逃す。
- severity: **fix**

### RA-05 — 実在する単一理由負例がなく、単位 A の receipt 変異は層で mask される

- 主張: 今日の repo に実在し「その検査だけ」が拒否する入力を、追加 production 検査のいずれにも名指しできない。単位 A の4面はすべて合成 fixture であり、receipt は同じ schema 検査を前後 2 回通すため、composite 内の一方だけを無効化する変異は生存する。
- 証拠:
  - 実在 g1 は自己不整合と method 不一致の両方を持つ (`brief.md:14-17`、`output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1442`、`:1484`)。裁定自身も単一理由に使えないと認めつつ、直後に method だけの証拠と記して矛盾する (`s4-adjudication.md:149-151`)。
  - g2 は4面を通る正例である (`s5-unitA.md:1-2`)。content-addressed path は `orchestrator/campaign/env_contract.py:262-271`。
  - 4面負例はその場で JSON を改変して作る (`orchestrator/tests/test_env_contract_activation.py:1456-1521`)。
  - receipt は `_verify_entry_calibration` 内の load (`orchestrator/campaign/env_contract.py:532-559`) と直後の再 load (`:454-462`) の両方で `schema_v2` の束縛を通る。実際の ID 束縛は `orchestrator/calibrator/schema_v2.py:532-535`。
  - floor の zero-match と SHA 不一致も合成入力である (`orchestrator/tests/test_s8b_protocol_builder.py:977-995`、`orchestrator/tests/test_campaign.py:5026-5061`)。現行 index は current 1 件の正例 (`orchestrator/tests/test_s8b_protocol_builder.py:945-968`)。
- 成果物影響: fixture 限定または冗長層に mask された防壁を「変異で証明済み」と記録し、certified 選択の較正由来性を過大表示する。
- severity: **fix**

単位 A の等価変異判定:

| 面 | 単独変異を殺すテスト | 判定 |
|---|---|---|
| 自己整合 | 合成 `self-consistency` 負例 | 殺す。ただし実在単一理由入力なし |
| method | 合成 `method` 負例 | 殺す。ただし実在 g1 は自己整合にも失敗 |
| content-address | 合成 `content-address` 負例 | 殺す。前後に同じ path 検査なし |
| acquisition receipt | 合成 `acquisition-receipt` 負例 | shared schema leaf の変異なら殺すが、composite の片側 load 無効化は他方に mask される |

### 静的に維持されている防壁

- 現 serial 1 は `previous_rows is None` のため composite を呼ばず、通常 authority load と recorded tuple の今日の受理は静的経路上変わらない。
- 現 floor record は current g1 hash と一致し、ccbench pin は resolver の選択条件に入っていない (`orchestrator/campaign/s8b_floor_campaign.py:877-896`)。
- floor mode は必ず `_admit_floor` を通り (`orchestrator/campaign/certified_writer_admission.py:400-420`)、再読 SHA は parse 前に全経路で実行される (`:205-229`)。
- composite の既知例外は `False`、その他の `Exception` も activation validator が `ActivationRecordError` にするため、例外から受理へ倒れる fail-open は見つからない (`orchestrator/campaign/env_contract.py:451-464`、`orchestrator/campaign/env_contract_activation.py:301-329`)。
- 歴史 resolver gate、g1 例外、runtime attestation、production catalog 全走査、receipt field、凍結 bytes の変更は差分にない (`integrated.diff:1-668`)。
- pytest は実走しておらず、緑とは判定していない。

## 総括

- 今日の serial 1 authority、floor admission、serial 1 recorded tuple の受理低下は静的には見つからない。
- SHA 再照合と callback 例外処理に fail-open は見つからない。
- ただし method gate は過去の activation 遷移を可変な現行定数で再判定する。
- このため g2 活性化後の probe 更新が authority を読めなくする。
- issue-tool の既存正例 2 件は artifact 不在の temp root により静的に赤となる。
- `ident.py` 配線変異と receipt 面の mask に検査網の穴がある。
- 許可外の 65-env テスト弱体化もある。
- **判定: NO-GO**