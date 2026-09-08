# [T-2437] 段 6 裁定 — 所見の採否と fix 指示

親が (1) 自分の焦点走、(2) レンズ A、(3) レンズ B を裁定した結果。
**fix 子はこの文書の「採用した所見」をすべて閉じる。「不採用」には触らない。**

対象 wave HEAD: `636e943802cbb309694bf23ed3fe7794087438f4`

---

## 採用した所見

### P1 (blocker、親の焦点走) — 発行 context 未指定でも引数が評価され、既定経路が壊れる

`s6-parent-finding.md` の全文が指示である。

`_issue_campaign_result_evidence(...)` の 4 呼び出し点 (`loop.py:664, 697, 713, 839`) が引数を
無条件に評価する。Python は呼び出し前に引数を評価するので、helper 冒頭の `if context is None: return`
では防げない。既定 (originless) 経路が従来読まなかった属性 (`authorized_contract.contract_sha256`、
`r.build_attempt_id`) を読み、既存 test が渡す stub / `SimpleNamespace` で `AttributeError` になる。

**直し方:** 4 呼び出し点それぞれを、引数の評価ごと `if result_evidence_context is not None:` で囲む。
helper 内の早期 return は残してよいが、**それだけでは防護にならない**ことを code comment に 1 行書く。

**足す負例:** 属性アクセスで例外を投げる番人 object を `authorized_contract` と `EvalResult` に渡し、
`result_evidence_context=None` の `run_campaign()` が最後まで通ることを検査する node を 1 件。

### P2 (blocker、レンズ A 所見 1 + レンズ B 所見 2 が独立に同じ穴) — receipt の真正性を誰も検証していない

**実測 (親が裏取り済み):** `orchestrator/campaign/reflux_result_evidence.py` に
`receipt_matches_contract` / `execution_guard` への参照が **0 件**。
issuer は `type(execution_receipt) is dict` と `contract_sha256` の一致しか見ない
(`reflux_result_evidence.py:1298-1307`)。
一方 repo には権威ある検証器 `execution_guard.receipt_matches_contract()` が既にあり、
schema で分岐して v1 は `attestation_mode == "none"` のときだけ、v2 は required + hash-bound
calibration のときだけ受理する (`execution_guard.py:225-250`)。

**これは段 4 裁定 §5 の「receipt が無ければ拒否する」が、字面は満たされているのに中身が空である**
状態である。条件に合う任意の dict が通る。規律 3 に反する。

**直し方 (2 つとも必須):**

1. **issuer が権威ある検証器を呼ぶ。** `issue_campaign_result_evidence` は
   `execution_guard.receipt_matches_contract(receipt, env_tag=..., contract_sha256=...,
   attestation_mode=..., verified_calibration=...)` を通し、`False` なら
   `ResultEvidenceIssuanceRefused` で拒否する。必要な `env_tag` と `attestation_mode` は
   `ResultEvidenceIssuanceContext` へ足すか、呼び手 (`loop.py`) から渡す。
   **自前で receipt の形を再定義しない。**既存の検証器が正本である。
   - 負例を足す: schema が違う dict / `env_tag` 不一致 / `attestation_mode` 不一致 →
     いずれも拒否され、file が 1 件も作られないこと。

2. **中心正例が production で起きない状態を合成しない。**
   現在の正例は `attestation_mode="none"` の契約で走り、実 `_authorize_measurement()` が返す
   `None` を `execution_guard.build_receipt()` 製の receipt へ差し替えている
   (`test_reflux_campaign_issuer.py:311-324, 433-439`)。**production はこの状態を作らない。**
   - **第 1 選択:** 中心正例を `attestation_mode="required"` の契約で駆動し、
     **実 `_authorize_measurement()` が実際に receipt を作る**形にする。
     required 契約の作り方は `orchestrator/tests/test_env_attestation.py` と
     `orchestrator/tests/test_calibrator_certify.py` に既存の型がある。
     receipt の差し替え wrapper (`_install_fixture_receipt_authorization()` 相当) を**削除する。**
   - **第 2 選択 (第 1 が本当に不可能なとき):** 合成をやめ、
     `attestation_mode="none"` では **file 0 件で拒否される**ことを正例にする。
     その場合、中心正例は「発行の成功」ではなく「到達不能性」を示すものになる。
     **どちらを採ったかを完了報告に明記し、第 2 を採った理由を file:line で書く。**
     **合成 receipt を残したまま「発行できた」と報告してはならない。**
   - 併せて、`test_reflux_result_evidence.py:354-359, 1096-1104` の任意 schema receipt を使う
     正例も、1 の検証器を通る形へ直す。

### P3 (must-fix、レンズ B 所見 1) — 既存 accepted terminal の skip が record を新規発行してしまう

context ありで既存 terminal を skip する 2 分岐 (`loop.py:664-674, 713-721`) が generic issuer を呼ぶ。
accepted terminal は `derive_physical_result()` が typed 値なしで受理するため、
**過去 attempt の WAL と現在 run の execution receipt を混ぜた record が新規発行されうる。**

**直し方:** context ありの 2 つの skip 分岐では issuer を呼ばず、**無条件に明示拒否する。**
通常評価の accepted (per-result 発行点) は現行どおり typed 値不要でよい。
対応後に `_result_evidence_attempt_id()` が未使用になるなら削除する。
負例を足す: accepted terminal を持つ campaign を同じ context で再実行すると拒否され、
新しい record が 1 件も作られないこと。

### P4 (must-fix、レンズ A 所見 2) — originless の WAL 不変検査が変更後どうしの自己比較

`test_reflux_campaign_issuer.py:424-429, 525-545` は、context あり run と context なし run を
比べている。**両方に同じ frame を足す回帰は緑のまま通る。**

**直し方:** originless の file 集合・stage 集合・payload key 集合を、
**具体的な期待集合** (test 内に literal で書いた非揮発の集合) と比較する。
context つき run を比較対象にしない。

### P5 (must-fix、レンズ A 所見 3) — eval-exception の issuer 判断がテストされていない

実装 (`loop.py:816-847`) は裁定どおりだが、`test_reflux_campaign_issuer.py:723-793` は
`result_evidence_context=None` を渡すので issuer 判断を一度も通らない。

**直し方:** context **あり**の eval-exception を、attempt ID あり / なしの両形で駆動し、
`ResultEvidenceIssuanceRefused` の伝播と result-evidence file 0 件を検査する。
identity-error (`:695-719`) と terminal-skip (`:509-518`) も、例外だけでなく
**拒否の前後で evidence file 集合が変わらないこと**を検査する。

---

## 不採用 / 親が引き取る所見

- **レンズ B 所見 3 (変異の再照準)** — real だが、変異事前登録は親の仕事である。
  fix 子は触らない。親が下記 §「変異事前登録 v2」で確定した。
- **レンズ B 所見 4 (受入所要台帳の 19 node)** — real だが、台帳追記は main 取り込み後に親が
  1 回で行う (段 4 裁定どおり)。fix 子は触らない。
  fix 子は**完了報告に per-node の実測秒を書く**こと。それが親の入力になる。
- **レンズ A の「恒真な保証」2 件** — 指摘は正しいが、いずれも既存 API の意味であって
  本 wave が足した防護ではない。insight の限界節に 1 行書く。実装は変えない。

---

## 変異事前登録 v2 (親が段 6 で確定。段 4 §7 を差し替える)

レンズ B の判定を採り、**単一理由にならない 6 件を分割・exact 化した。**

| ID | 位置 | 無効化する述語 | 期待する赤 |
|---|---|---|---|
| M1 | `pipeline.py:2093-2097` | abort のとき typed 値を渡す | typed 保持の正例 + 中心正例 |
| M2 | `pipeline.py:1870-1871` | `type(x) is VerifyResult` の exact 型検査 | 非 exact 型の拒否負例 |
| M3' | `_admit_verify_fanout_result` の戻り値を projection 前に検査する専用 node へ再照準 | fan-out の typed 値なし | fan-out 専用 node (新設) |
| M4' | `reflux_result_evidence.py` の source ref path **だけ**を live WAL へ変える (snapshot 書込みは残す) | prefix snapshot の immutability | 中心 producer 正例 + append 生存負例 |
| M5 | `byte_start` を 0 固定 | 区間の起点 | 2 番目 attempt の正例 |
| M6a | derive を write より後へ移す | 「発行前に拒否し file 0 件」 | 非 exact typed の拒否負例 |
| M6b | assemble / expected path 検査を write より後へ移す | 同上 (別 gate) | 不正 expected path でも file 0 件を見る新 node |
| M7' | `execution_receipt=None` を**自己申告 dict に置換**する変異 | receipt の真正性検証 (P2 の 1) | receipt 不在 / 非真正の拒否負例 |
| M8' | context-none 分岐で content marker を 1 件置いて return する | originless で file を 1 つも置かない | originless 専用 node (P4 で新設する具体集合比較) |
| M9a | 新規 identity-error の明示拒否 | 同 | identity-error 拒否負例 |
| M9b | identity 解決失敗 + accepted stock terminal の skip 拒否 | 同 (P3 で新設) | accepted terminal skip の拒否負例 |
| M9c | 通常の accepted terminal recovery skip の拒否 | 同 (P3 で新設) | 同上の別 node |
| M10a | `_validate_result_evidence_context()` の `len(genomes) == 1` | 単一 genome 前提 | 直接呼びの multiple-genome 負例 |
| M10b | 同関数の balanced 拒否 | balanced 非併用前提 | 直接呼びの balanced 負例 |
| M11 | issuer call **だけ**を catch して return する exact 変異 | fail-closed の伝播 | 中心正例 |
| M12 | P1 の call site guard を外す (引数を無条件評価へ戻す) | 既定経路の意味不変 | P1 で新設する番人 object の node |

**登録しない (単一理由にならない):** truncated final frame、全 frame の attempt 一致、
terminal / attempt / projection schema の producer 側複製、
pre-build / identity-error / eval-exception への attempt ID 追加。

**期待 node 集合は fix 後の最終 commit で確定し、変異本走の前に台帳へ書く (DW-M07/M08)。**
