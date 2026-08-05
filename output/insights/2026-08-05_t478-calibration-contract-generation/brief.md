# [T-478] 較正の contract 世代移行 — 段 1 brief

## scope

較正 artifact を再登録したときに **既存 certified 参照が解決不能にならない移行手順**を確定する。
本 wave の成果物は **設計 (docs) と裁定パッケージ**であり、世代機構の実装・凍結 bytes の更新・
pin の更新は行わない。実装は [T-419] U-2 (較正再取得) wave が所有する。

## 確定済みユーザー裁定 (前提、覆さない)

- [T-452] U-7 = (a): 本タスクを起票し **較正再取得の前提**に置く。順序は本タスクが先。
- [T-452] U-8 = (a): authority 実装を先に land し、campaign を閉じたまま U-2 と pin closure を
  連続 2 commit で行う (間の campaign 禁止)。
- [T-419] R-1 = 方式 α (走行 CPU を移しながら K 回読み、論理 CPU ごとに最小値)。
  U-2 は本タスクと [T-452]+[T-453] 権威実装の後。
- D155 決定 (5): 較正の再取得・凍結 bytes の更新・pin の更新は当該 wave で行わない。
- D143 決定 (3) = (b): 述語を正とし較正を取り直す。述語を緩める案は採らない (規律 2)。

## 段 1 前提実測 (この worktree、main 44ff1c11 相当)

1. `env_contract.REGISTRY["pegasus"].contract_sha256 = e576e9cd1369bba3…` (実行して計算)。
   `linux-baremetal` は `1b2ee853…`。
2. `output/s8b-freeze/floor_protocol.json` は `contract_sha256 = e576e9cd…` を**内包**し、
   同 file の bytes sha256 = `261cec1c…` が `FROZEN_MANIFEST` (23 件) の pin 対象
   (`orchestrator/tests/test_frozen_artifacts.py:45-46`)。
3. 同じ `261cec1c…` が `output/s8b-freeze/selector-runs/journal.jsonl` の
   `run_header.protocol_sha256` に入っている (journal 自身も FROZEN_MANIFEST pin)。
4. floor campaign の launch は `pre_oracle_head` の git blob と worktree の floor protocol が
   **byte 一致**であることを要求する (`s8b_floor_campaign.py:1411-1416`)。
   → 凍結 protocol の in-place 書き換えは history 側とも衝突し、実行不能。
5. `validate_protocol` は `protocol.contract_sha256 == contract_sha256_lookup(env_tag)` の
   **完全一致**を要求し、不一致は `FloorContractError` (`s8b_floor_contract.py:139-151`)。
6. `env_contract` の解決経路は `lookup(env_tag)` **のみ** (`env_contract.py:202`)。
   contract hash からの逆引きも世代の概念も存在しない。campaign 側の呼び出しは 20 箇所。
7. → **新事実 (N1)**: 4 と 5 は同時に満たせない。較正を再登録すると (a) 旧 protocol を残せば
   launch が拒否され、(b) 旧 protocol を書き換えれば FROZEN_MANIFEST・journal・blind seal の
   history 一致が同時に破れる。**現状は「再登録すると必ずどちらかが壊れる」構造**である。
8. **新事実 (N2)**: [T-452] 設計 §6 の pin 閉包列挙は**不完全**である。実測で追加が要る面 —
   - `reflux_origin_ledger.py:243,395,425,1552` の `environment_contract_sha256`
     (P3 origin ledger の**永続**フィールド)
   - `buildcache.py:650` の `contracts/<contract_sha256>/` namespace と manifest 照合 (:392)
   - `p3_s4_loop_trigger_gating.py:367` の記録
   - `s8b_ratified_freeze.py:174-175, 3027` の
     `protocol.contract_sha256 == journal.campaign-start.execution_receipt.contract_sha256` 等式
   - `execution_guard.py:78,110,122,336` の receipt 生成・照合
9. **同名二義化の危険 (DW-O13/D75)**: `s8c_preregistration` の `evidence_contract_sha256` は
   **別概念** (prereg 文書の evidence contract hash) であり、env contract 世代の閉包に含めない。
   設計本文で明示的に除外し、同名で括らない。

## 不変条件 (破ってはならない)

- 述語を緩めない・受理集合を広げない (規律 2)。移行のために attestation を外さない。
- **旧凍結 bytes を貼り替えない。** 旧 evidence の binding を新 SHA へ書き換えない
  (虚偽の履歴になる)。旧 artifact は歴史資料として自己完結のまま保持する。
- 本 wave はコード・テスト・凍結成果物・pin を一切変更しない (docs のみ)。
- 設計択一は親が既成事実化せず、裁定パッケージでユーザーへ返す。

## 成果物の形

- `output/insights/2026-08-05_t478-calibration-contract-generation/` に
  `README.md` (裁定パッケージ本体) + `brief.md` + codex 逐語 (`s2-plan.md`, `s3-lensA.md`,
  `s3-lensB.md`, `s4-ruling.md`)。
- README は次を持つ: (1) 実測した参照閉包の全件表 (path/file:line、live 照合か永続記録かの分類)、
  (2) 世代機構の択一と推奨、(3) 移行手順の順序 (U-8 の連続 2 commit へ落ちる形)、
  (4) 恒真化を塞ぐ機械と変異候補、(5) 保証しない範囲、(6) ユーザー裁定へ返す択一。
- `docs/spool/` に worklog fragment。設計判断が確定したら decisions fragment も。

## provisional 裁定 (親の暫定、攻撃対象)

- **(P1)** 本 wave は docs-only とし、世代機構の実装コード・テストは書かない。
  実装は U-2 wave が所有する。→ 段 5・6 を飛ばす前提で組む。
- **(P2)** 推奨方向は [T-452] §6 を踏襲した**世代付き移行** (旧 contract を厳密に解決できる形で
  保持し、新較正は新世代・新 protocol・新 evidence に束縛する)。ただし
  **世代をどこに持たせるか** (registry を env_tag→世代列にする / 凍結 artifact 側に世代 tag を持つ /
  contract hash からの逆引き resolver を新設する / 新 env_tag を切る) は択一として返す。
- **(P3)** 「解決不能にならない」の定義を「旧 artifact が現行コードで **verify 可能なまま**であること」
  とし、「旧 artifact が current eligibility を持つ」ことは要求しない (旧 evidence は失格でよい)。

## 成果物影響 (DW-G05)

設計しないまま U-2 へ進むと、較正再取得は上記 N1 の二択に突き当たる — 凍結 seal 連鎖を壊すか、
較正を登録できず campaign が開けないか。どちらでも **certified 選択の再開自体が不能**になり、
Phase 3 の主実験成果物 (certified 選択結果・材料レポート・試行台帳) が確定しない。

## 並列分割方針

段 2 = codex read-only 起草 1 本。段 3 = 敵対 2 レンズ並列 (レンズ A = 閉包の網羅性と実在性、
レンズ B = 移行手順の正しさ防壁・恒真化・親 brief の実測と一般化)。実装子は起動しない (P1)。
