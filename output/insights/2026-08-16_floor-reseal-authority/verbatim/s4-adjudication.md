# 段 4 裁定 — 床値 protocol の再封印を AI へ開放する

2026-08-16 14:15 JST / wave floor-reseal-authority / 親裁定

段 2 プラン + 段 3 敵対 2 本 (lensA=NO-GO 4 blocker、lensB=NO-GO 2 blocker) を裁定する。
親が独立に実測して裏取りした所見には `[実測済]` を付す。

## 1. 所見の裁定表

| # | 出所 | 所見 | 判定 | 処置 |
|---|---|---|---|---|
| A1 | lensA 1 | pin を進めるたび新しい組ができ、測り直せる | **real (major)** | 案 3 の射程の問題。裁定パッケージへ。実装では射程を明記 |
| A2 | lensA 2 / lensB 1 | Q3 の片側交代 (`g1`, 新 pin) を issuer が受理する | **real (blocker)** | **D3 で機械拒否**する |
| A3 | lensA 3 | anchor を working tree から読むため真正性が束縛されない | **real (major)** `[実測済]` | **D4** anchor を committed HEAD blob から読む |
| A4 | lensA 4 | 削除すれば同じ組を再発行できる (履歴不変でない) | **real だが scope 外** | 保留中の凍結チェーン族 (M-7)。限界として明記 |
| A5 | lensA 5 / lensB 3 | 新 artifact が consumer に届かず機構が inert | **real (major)** | **D6** 成果の呼び名を正す。consumer 結線は後続 wave |
| A6 | lensA 6 | publish 直前の contract 再照合は恒真 | **real (major)** `[実測済]` | **D5** 恒真ゲートを積まない。当該再照合を落とす |
| A7 | lensA 7 | 事前登録テストに検出力の対照が無い | **real (major)** | **D10** 公開入口経由の変異を必須化 |
| B2 | lensB 2 | 新 namespace が既存 launch の未知 file 拒否に当たる | **real (blocker)** `[実測済]` | **D2** chain-record pattern を足す |
| B4 | lensB 4 | ratified pointer は任意 canonical path を受理する | **real (major)** `[実測済]` | 射程外。限界として明記 + 裁定パッケージ |
| B5 | lensB 5 | manifest / hold / literal pin は新 artifact を見ない | **partial** | D2 で `clean_scan_digest` には載る。manifest 追加は見送り (裁定パッケージ) |
| B6 | lensB 6 | 専用 issuer が generic writer と hooks を迂回する | **refuted (境界)** | 裁定そのものが AI 発行を許す。writer は destination を自分で導出し外を書けない |
| B7 | lensB 7 | `reseal-protocol` に実運用の呼出し地点が無い | **real (minor)** | 発火 gate を明示 (下記 §4) |
| B8 | lensB 8 | `check-protocol-index` は余剰 | **refuted** | 親の live dogfood と runbook 入口として必要 |
| B9 | lensB 9 | index コストが artifact 数に比例 | **real (minor)** | N = 環境世代数 (現在 1)。履歴比例ではない。記録のみ |

### 実測の根拠

- A3: `validate_protocol` は `master_seed` / `stock_configuration` を非空 str、
  `wired_min_rel_floor` を (0,1] の有限数としか検査しない (`s8b_floor_contract.py:154-200`)。
- A6: authority snapshot は PID ごとに一度だけ load して cache する
  (`env_contract.py:576-586`)。同一 process の 2 度目の `lookup()` は必ず同じ object を返す。
- B2: `_assert_freeze_allowlist` が `output/s8b-freeze` を `rglob("*")` し、
  `_PREFLIGHT_FIXED_FILES` / `selector-runs/` / `_CHAIN_RECORD_PATTERNS` のどれにも当たらない
  file を「freeze namespace に未知 file がある」で拒否する
  (`s8b_floor_campaign.py:3216-3237`)。
- B4: `_closure_entries` / `_assert_canonical_relative_path` は
  `floor_protocol` record の path を canonical 文法だけで受理する
  (`s8b_ratified_freeze.py:887-897`)。固定 path 束縛は selector 盲検側 (`:2647`) にしかない。

## 2. 確定した設計 (プラン v2)

- **D1 path**: `output/s8b-freeze/floor-protocols/<contract_sha256>--<ccbench_pin>.json`。
  64 hex + `--` + 40 hex。組から一意に導出し、呼び手は指定できない。
  自己記述的で目視照合できるため、追加の digest は作らない。
- **D2 chain record**: `_CHAIN_RECORD_PATTERNS` へ
  `output/s8b-freeze/floor-protocols/[0-9a-f]{64}--[0-9a-f]{40}\.json` を足す。
  **これが無いと、versioned protocol を 1 件置いた瞬間に既存 launch が拒否になる (B2)。**
  chain record は `clean_scan_digest` の namespace allowlist へ hash 込みで載る。
  受理集合が広がる唯一の箇所なので、過剰受理の負例を必ず登録する (§3 の M6/M7)。
- **D3 Q3 の機械化**: issuer は、**target の `contract_sha256` が index に既出なら拒否する**
  (= 環境契約 1 世代につき床値 protocol は最大 1 件)。
  legacy anchor は g1 を占有しているので、現在状態での `(g1, 511c9538…)` 発行は拒否される。
  これは新規則の発明ではなく、裁定が「破らない」と明記した Q3 (`both-components-change`) の機械化である。
  受理集合を**狭める**方向なので、過剰拒否を検出する正例を必ず登録する (§3 の M4)。
- **D4 anchor 源**: legacy anchor は **committed HEAD の blob** から読む
  (`git cat-file blob HEAD:output/s8b-freeze/floor_protocol.json` 相当)。
  working tree の dirty な値を継承させない。読めなければ fail-closed。
  凍結チェーン検証 (保留中) を復活させるものではない — 「今の HEAD が凍結時 commit か」は問わない。
- **D5 恒真ゲートを積まない**: publish 直前の active contract 再照合は削除する (A6)。
  HEAD gitlink の再実測 (subprocess・cache 無し) だけ残す。
  **撃てないゲートを防壁として数えない。**
- **D6 成果の呼び名**: 本 wave の成果は
  **「AI 発行可能な issuer と組 index を land した (dormant)」**である。
  「案 1 + 案 3 実装完了」「正しさ防壁が閉じた」とは記録しない。
  consumer 結線 (Python 5 + shell 1 = 6 件) と実発行は g2 活性化 chain の後続 wave。
- **D7 その他**: プランの零引数 API、legacy 固定 anchor、strict scan、create-only、
  16/2 field 分割、既存 `freeze_protocol` 非改変は採用する。

## 3. 変異の事前登録 (DW-M01)

各変異は「同じ入力を手前で落とす層が無いこと」を実装後に確認してから本走する。
期待 node は fix 後 commit で完全集合を再導出する (DW-M07 / DW-M08)。

| ID | 変異位置 | 変異内容 | 単一理由性の根拠 | 期待 |
|---|---|---|---|---|
| M1 | 組 index の走査集合 | legacy 固定 path を走査集合から外す | legacy を外すと g1 が未使用に見える。手前に同等検査は無い | KILLED |
| M2 | 組 index の重複判定 | 同一組 2 件目の拒否を落とす | `validate_protocol` は単体しか見ない。create-only は同一 path しか見ない | KILLED |
| M3 | 継承検査 | `_AI_RESEAL_MUTABLE_FIELDS` へ 3 つ目の field を足す | 16 field の byte-exact 比較以外にこの field を守る層は無い | KILLED |
| M4 | D3 の Q3 判定 | `contract_sha256` 既出拒否を落とす | **過剰拒否の正例**と対。落とすと `(g1, 新 pin)` が通る | KILLED |
| M4p | 同上 (正例) | 判定を「常に拒否」へ倒す | 承認外の過剰拒否を検出する正例 | KILLED |
| M5 | D4 anchor 源 | anchor を working tree から読む形へ戻す | dirty anchor の継承を止める層は他に無い | KILLED |
| M6 | D2 chain pattern | pattern を `.*\.json` へ緩める | freeze namespace の未知 file 拒否が広く空く | KILLED |
| M7 | D2 chain pattern (正例) | pattern を削除する | versioned protocol を置いた launch が拒否になる正例 | KILLED |
| M8 | path 導出 | 導出 path と document の組の束縛を落とす | 別名配置を止める層は他に無い | KILLED |

`DW-M08` の新旧両走は本 wave では不要 (テスト強化だけの wave ではない)。

## 4. 発火 gate (DW-G04)

`reseal-protocol` の発火条件は
**「`orchestrator/campaign/env_contract_activations/` に pegasus generation ≥ 2 を active にする
activation record が追加された時点」**である。現行の active record は
`00000001.json` (pegasus g1) であり、この path を brief に書ける。
`check-protocol-index` は本 wave の親 dogfood で 1 回通す (実 repo・read-only)。

## 5. 成果物影響 (DW-G05)

- 実装した場合、certified 選択・レポート・試行台帳の**現在値は 1 件も変わらない**
  (artifact を実 repo へ追加しないため)。
- 変わるのは launch 受理集合の 1 点だけ = D2 の chain pattern に合致する path が
  「未知 file」から「chain record」へ移る。現在その path に file は無いため、
  今日の launch 判定も変わらない。
- 実装しない場合は M-1〜M-13 のとおり、新しい組で真正な物差しを封印できない状態が続く。

## 6. ユーザー裁定パッケージ (段 9 で返す)

1. **pin を進めれば測り直せる (A1)。** 案 3 が消したのは「同じ組で 2 本目」であって
   「pin を進めて新しい組で測り直す」ではない。閉じるには不採用にした案 2 (事前登録) が要る。
   現状の射程で足りるか、案 2 を復活させるか。
2. **D3 (環境契約 1 世代につき床値 1 件) を採ってよいか。** Q3 の機械化として親が入れた。
   pin だけの前進で床値を作り直したい場面があるなら Q3 の変更裁定が要る。
3. **ratified pointer が namespace 外の protocol を指せる (B4)。** 案 3 の一意性は
   sanctioned namespace 内に限る。pointer 側を namespace へ束縛するか。
4. **versioned artifact を `FROZEN_MANIFEST` へ載せるか (B5)。** 既定は見送り
   (bytes 級 provenance 機構の新設は既定で最小)。
5. **run 層の測り直し (T-1140 問 1)。** 案 3 は protocol 単位であり、同一 protocol の
   複数回実走は現在許されている。ここは別裁定として係属中。
