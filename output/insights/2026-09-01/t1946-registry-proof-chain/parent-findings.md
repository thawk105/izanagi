# 親の独立実測 (段 2 待機中に確定)

base commit 11b44e2d1。すべて実コードを読んだ結果であり、推測ではない。

## F-P4. adapter 遮断契約の実射程 (親の provisional 裁定 P4 を確定・一部修正)

`orchestrator/tests/test_s8b_attempt_registry.py:1580`
`test_floor_campaign_does_not_import_adapter_and_guard_has_positive_control`

- 検査本文は `_assert_production_source_has_no_attempt_adapter`
  (同 file:1551-1578)。AST を歩き、`ast.Import` / `ast.ImportFrom` / `ast.Name` に加えて
  **`ast.Constant` の文字列に `s8b_attempt_registry` が含まれるだけでも violation** にする。
- 検査対象は **ちょうど 2 file** — `s8b_floor_campaign.py` と `s8b_holdout_admission.py` (同 file:1583-1587)。
- 正例 (positive control) も同居している (同 file:1592-1597)。恒真ではない。

**帰結:**

- `s8b_floor_stats.py` は**検査対象に入っていない**。したがって
  `verify_floor_artifact_with_live_admission` (A2) から registry を読み取り目的で import しても
  この meta-test は赤にならない。
- 逆に、`inspect_floor_holdout_admission_evidence` (A12/A13、`s8b_holdout_admission.py` 内) へ
  registry 参照を足すと**この meta-test が確実に赤になる**。文字列定数でも落ちる。
  → 親 brief の P3 provisional 「A2 + A12 の併用」の **A12 側は採れない**。
- producer 側 (`s8b_floor_campaign.py`、A17) も同様に registry を直接触れない。
  新しい値を result へ届ける経路は campaign の外から渡すしかない。

## F-P5. historical reverify は同じ verifier を通る (版条件は必須)

- `orchestrator/campaign/s8b_ratified_freeze.py:3558` `reverify_published_freeze` は
  `_launch_validate` を `contract_resolver=_resolve_historical_contract_sha256` で呼ぶだけ。
- その `_launch_validate` の中 (同 file:3262) が
  `_floor_stats.verify_floor_artifact_with_live_admission` を呼ぶ。
- 呼び手は `s8b_oracle_judge.py:750` と `s8b_verdict.py:829`。

**帰結:** 束縛を**無条件**に足すと、既に publish 済みの freeze の再検証が落ちる。
これは D1112 択 (b) が禁じた「既存 certified 成果物の受理面を変える」に直接あたる。
版 (または同等の前向き条件) は好みの問題ではなく**必須**である。親の P1 provisional を確定とする。

## F-EXACT. result の exact key 述語をもつ consumer は 3 か所ある

`result_keys_for_mode` の production 呼び手 (`git grep` と
`orchestrator/tests/test_official_perf_closure.py` の call-site 閉包 pin の両方で照合済み):

| 記号 | file:line | 関数 |
|---|---|---|
| K | `orchestrator/campaign/s8b_floor_stats.py:734` | `verify_floor_artifact` |
| D | `orchestrator/campaign/s8b_holdout_freeze.py:1429` | `_validate_floor_inputs` |
| L | `orchestrator/campaign/s8b_ratified_freeze.py:2341` | `_validate_result_top_level_keys` |

閉包 pin は `test_official_perf_closure.py:198-199` (K)、`:202-203` (D)、`:216-217` (L)。

**帰結:** 新しい top-level key を足すなら **3 か所すべて**が新 key を受理するようにしなければ、
result は certified 経路のどこかで必ず落ちる。K だけ直しても発効しない。
`_validate_result_top_level_keys` は `_validate_result` (同 file:2374-2380) と
`_launch_validate` (同 file:3255) の**両方**から呼ばれる。

## F-ARTIFACT. repo に committed された certified floor result artifact は 0 件

- `git grep -l "s8b-floor-result" -- output` の hit は insight 文書 7 件のみ。artifact JSON は無い。
- `git ls-files` に floor result 相当の artifact は mutation probe の `.gz` だけ。

**帰結:**

- 「既存 certified 成果物の受理面を変えない」は、保存 file を守る話ではなく
  **コード経路 (現行 schema の受理条件) を守る話**である。
- 基準時点 allowlist 案は、発火条件を満たす既存 artifact path を brief に書けない
  (DW-G04 に抵触する。書けなければ設計メモに留める)。版で条件づける案が実在物に依拠しない。
- ただし repo 外 (計算ノード上の output) の artifact 有無は未確認。

## F-CHAIN. chain head の実体

- `orchestrator/campaign/attempt_registry_core.py:253` `previous_event_sha256(rows)` が
  末尾の chained row の `event_sha256` を返す。chained row が 1 件も無ければ `_ZERO_SHA256`。
- chain の field は `event_index` / `previous_event_sha256` / `event_sha256`
  (同 file:239-251 `chained_event_row`、`:442` `_assert_chain`)。
- registry の所在は `s8b_attempt_registry.py:485` `registry_path(repo_root, *, freeze_sha256)`。
  代替 path は `_entry_paths` (同 file:462-483) が明示的に拒否する。
- 読み取り API は `s8b_attempt_registry.py:1086` `read_attempt_registry`。lock 内で replay する。

**帰結 (P2 への含意):** chain head 単独では、空 registry (zero sha) と
「genesis しか無い registry」を区別できない可能性がある。freeze binding と row 数まで
含めるかは plan / 敵対相談の結論を待つ。

## F-SCHEMA. `s8b-floor-result` の schema 等値検査は 4 か所ある (exact 述語の追加分)

`result_keys_for_mode` の 3 consumer とは**別に**、schema 文字列を `!=` で照合する production 経路が
4 か所ある。版を増やすなら全部が「受理集合」の意味を学ぶ必要がある。

| file:line | 役割 |
|---|---|
| `orchestrator/campaign/s8b_floor_campaign.py:163` | `RESULT_SCHEMA = _floor_contract.RESULT_SCHEMA` (producer 側の別名束縛) |
| `orchestrator/campaign/s8b_floor_campaign.py:6585` | producer が result へ `"schema": RESULT_SCHEMA` を書く |
| `orchestrator/campaign/s8b_floor_stats.py:745` | pure verifier の等値検査 |
| `orchestrator/campaign/s8b_holdout_freeze.py:1437` | holdout 経路の等値検査 |
| `orchestrator/campaign/s8b_ratified_freeze.py:2385` | ratified 経路の等値検査 (`_validate_result` 内。`_validate_result_top_level_keys` とは別) |

**帰結:**

- `_validate_result_top_level_keys` (key 集合) と `_validate_result` (schema 等値) は
  **別の述語**であり、ratified 経路だけで 2 か所ある。片方だけ直しても発効しない。
- `s8b_floor_campaign.py:163` は**別名束縛**である。`RESULT_SCHEMA` という識別子名で grep しても
  campaign 側の hit は別名の定義であり、schema 文字列 `s8b-floor-result/v4` の grep では
  campaign は 1 件も出ない。閉包は識別子と文字列の両方で引く必要がある。

## F-NESTED. ratified 経路は result の入れ子にも独自 exact key 集合を持つ

- `orchestrator/campaign/s8b_ratified_freeze.py:205` `_RESULT_CONFIG_KEYS` (`result.config`)
- `orchestrator/campaign/s8b_ratified_freeze.py:209` `_RESULT_CELL_KEYS` (`result.cells[*]`)
- 適用は `:2392` と `:2398`、判定器は `:1523` `_exact_keys`。

**帰結:** 束縛の値を `result.config` や `result.cells` の中へ入れる設計を採ると、
`s8b_floor_contract` 側だけでなく ratified 側の入れ子 key 集合も直す必要がある。
top-level へ新 key を置く方が触る述語が少ない。

## 親の provisional 裁定 (P1/P2/P3 の更新版。段 3 の攻撃対象)

- **P1 確定:** 版で前向きに条件づける。`s8b-floor-result/v5` を新設し、
  v4 は**今日と完全に同じ規則**で受理し続け、v5 だけが registry 束縛を無条件に要求する。
  F-P5 により、これは好みではなく必須。上記 4 + 3 = 7 の述語すべてを「受理集合」対応にする。
- **P3 更新:** 実体読み取りは `s8b_floor_stats.verify_floor_artifact_with_live_admission` (A2) に置く。
  **A12/A13 (`s8b_holdout_admission.py`) は採らない** — F-P4 の meta-test が確実に赤になる。
- **P2 未確定:** pin する値の閉包は plan と段 3 の結論を待つ。

## F-ORDER. 順序の既裁定との抵触 (着手後に判明。段 3 の主題)

段 2 plan が「production から `launch_floor_attempt()` を呼ぶ箇所は 0 件」と報告した。
**親が独立に確認した:** `git grep -n "launch_floor_attempt" -- orchestrator tools` の
production hit は定義 3 件 (`s8b_floor_attempt_launcher.py:548,648,673`) だけで、
呼び手はすべて `orchestrator/tests/test_s8b_floor_attempt_launcher.py` (6 件) である。
`s8b_floor_attempt_launcher` を import する production module も 0 件
(`s8b_attempt_registry.py:4` の docstring 言及を除く)。

**したがって現状、production の床値 campaign は attempt registry を一度も作らない。**

関係する既裁定 (主題で引いた。T-ID の grep では出ない):

- **D1114 (2026-08-27)**「発火する path を名指しできない gate は、部分実装でも land しない」
  — 「(a) 発火条件を満たす既存 artifact path も計測 ID も名指しできず、(b) 独立した敵対検査が
  『先行 land すると production 呼び手 0 件の死んだ gate になる』と判定した場合、部分実装を
  land しない。設計を凍結して裁定へ返す。」
  理由節に **「検査だけ land すると既存 campaign が止まる」** と明記されている。
- **D1193 (2026-08-28、ユーザー裁定)**「床値試行台帳は予算を凍結単位に残したまま、台帳だけを
  世代ごとに分ける」— 冒頭が「床値 campaign を試行台帳へ**配線するにあたり**」であり、
  配線が未了であることを前提にしている。さらに
  **「予算の置き場所は新しい設計判断なので、設計に入る時点で改めて諮る」**と留保している。
- **D1194 (2026-08-28、ユーザー裁定)** が D1112 の後継で、択 (b) を確認する。
  却下欄には「書き手だけ land して束縛を後続へ送る」はあるが、
  「検査だけ land して書き手を後続へ送る」は無い。

**親の読み (段 3 で検査させる):**

1. D1194 は本 wave の主題を確認しており、実装方向は覆らない。
2. しかし D1114 は、まさに本 wave の形 (検査側だけの land) を名指しで止めうる。
   D1114 の発火条件 (b) は「**独立した敵対検査が**判定した場合」であり、
   その判定は段 3 の仕事である。親が段 2 の plan 1 本で代替してはならない。
3. D1193 が留保した「予算の置き場所」は未裁定であり、配線 (T-1851) はそこで止まっている。
   本 wave が配線まで踏み込むと未裁定の設計判断を先取りすることになる。
   ユーザーの本 wave 指示も「本題の実装だけ」と scope を限っている。

**この項目は段 3 の 2 本ともに必ず判定させ、段 4 の裁定で real/refuted を決める。**

## F-S8C. 公式選択表を発行する最終層は live verifier を通らない (レンズ A 所見 2 を親が独立確認)

- `orchestrator/campaign/s8c_result_judge.py:2103` `verify_floor_bytes()` は
  `load_ratified_freeze()` の binding に対して **path の一致と sha256 の一致だけ**を検査する。
- 同 file で `reverify_published_freeze` も `verify_floor_artifact` も呼んでいない
  (`git grep -n "reverify_published_freeze\|verify_floor_artifact" -- orchestrator/campaign/s8c_result_judge.py`
  の hit は 0 件)。

**帰結:** plan どおり束縛を実装しても、s8c の最終層は「一度 ratified された bytes」を
hash で確かめるだけなので、その時点で registry が消えていても公式表を発行できる。

**ただし親の読み:** s8c は certification の**消費**側であり、certification 自体は
ratified 経路 (live verifier を通る) で起きている。消費時点で台帳の生存を再確認することは
D1194 が要求した「新規成果物への前向き束縛」より強い性質である。
レンズ A はこれを must-fix としたが、scope 内かどうかは段 4 で裁定する。
