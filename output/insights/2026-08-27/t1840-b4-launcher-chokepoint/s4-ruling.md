# 段 4 裁定 — [T-1840] B-4 の専用起動器と B-4 識別子を支配点にする

親裁定。段 2 プラン (`s2-plan.md`) と段 3 の 2 本 (`s3-sol.md` = 整合レンズ、
`s3-luna2.md` = 到達可能性・実効性レンズ) の全所見を real / refuted に裁定し、プラン v2 を確定する。

## 0. 段 4 直前の裁定 inbox 再走査 — 新しい裁定が設計に効いた

wave 開始後に main が 20 commit 進み、**D1124 / D1125 / D1126 が着地した**。

- **D1125**: 「bytes 級の凍結証拠、観測回数の台帳、**不可逆承認の token** を
  **測定の前提条件として新設しない**」。
- **D1124**: 「同じ cell を何度でも測ってよい」「途中死した run の復旧に専用機構を要求しない。
  落ちたら測り直す」。

**裁定: この 2 件は本 wave の設計を 1 点変える。** 段 3 の推奨にあった「create-only の
launch sidecar」は採らない。sidecar は**同じ campaign id に対して起動器が何度でも書き直せる**
形にする。関門が要求するのは「sidecar が実在し、この campaign id に束縛され、
process 内で生きている起動 context と一致すること」であって、**書かれた回数ではない。**

D1033 と D1124/D1125 は衝突しない。D1033 が分けるのは**標本の出所**であり、
D1124/D1125 が守るのは**測定の反復の自由**である。marker を付けない通常の測定は
本 wave の関門を 1 つも通らない。

既存の receipt 一回消費 (`consume_b4_iteration_authorization` の `os.link`) は
本 wave の編集面外であり、触らない。

## 1. 中心の所見 — real、採用、scope 内

### R1. 公開 producer が関門の下に残る (両レンズが独立に指摘)

**real。採用する。**

`orchestrator/campaign/loop.py:232-317` の `run_campaign` と
`orchestrator/campaign/pipeline.py:705-731` の `evaluate` は B-4 marker を検査せず、
検証通過後に `certified=True` として COMMIT を書く (`pipeline.py:1453,1466-1502`)。
`CampaignConfig` は frozen だが `search_config` は可変の `dict` であり
(`orchestrator/campaign/model.py:66-81`)、通常の `default_cfg()` の戻り値へ marker を
後付けできる。**親 brief の「実走の入口は 3 driver の main」という一般化は誤りだった。**
親 brief のこの一行は refuted である。

**支配点の置き場所を裁定する。** `wal.append` の COMMIT 分岐
(`orchestrator/campaign/wal.py:411-472`) に置く。根拠は 3 つ。

1. `wal.append` は `run_campaign` 直呼びと `pipeline.evaluate` 直呼びの**両方が必ず通る**
   唯一の合流点である。上の 2 箇所へ個別に関門を置くと、次に見つかる producer で同じ話になる。
2. 先例がある。T-1286 の certified sink の支配点は `wal.append` に置かれた
   (`docs/archive/worklog-phase3-0818-660.md:55`)。同じ骨格を使う。
3. `wal.append` は cfg を受け取らないが、**campaign lock が `search_config` を持つ**
   (`orchestrator/campaign/campaign_lock.py:17,162-163`)。lock は `layout.lock_file`
   (`orchestrator/campaign/layout.py:195-196`) から読める。したがって marker による分類が
   layout だけから可能である。

**発火条件は marker 付きのときだけとする。** lock が無い、または lock の `search_config` に
exact marker が無い campaign では、関門は 1 行も実行しない。**通常の campaign の受理集合は
1 bit も変わらない。**

### R2. 識別子が成果物へ残らない (sol の第 1 所見)

**real。採用する。**

プラン案では識別子が process 内の object に留まり、campaign lock・WAL・レポートから
「起動器を通ったか」を後から確かめられない。これでは D1033 の「B-4 識別子で標本を見分ける」が
成果物の層で成立しない。

**裁定:** 起動器は起動時に、権威 layout の root へ `b4_launch_context.json` を書く。
内容は campaign id、arm、driver kind、受理記録の sha256、起動 context の digest。
R1 の関門はこの sidecar と process 内 context の一致を要求する。
**上書き可能とする** (§0 の D1124/D1125)。

**scope 外に送るもの:** 非 B-4 の certified 成果物一般へ launcher capability を要求すること。
全 campaign の受理集合を変えるため本 wave では行わない。裁定パッケージへ回す (§4)。

### R3. P1 は「鋳造だけ」では支配点にならない (luna 第 2 所見)

**real。親の provisional 裁定 (P1) を修正する。**

修正後の (P1): 支配点は**「起動器で鋳造し、certified sink で消費する」**の 2 点で成立する。
鋳造だけを 1 箇所にしても、marker を後付けした cfg が別の producer から certified になる。

## 2. その他の所見 — 裁定

| # | 所見 | 出所 | 裁定 |
|---|---|---|---|
| R4 | driver kind が driver 境界で照合されていない | sol | **real・採用**。`expected_driver_kind` を必須にし、factory と全 driver 境界で exact 一致を検査する。cross-driver 流用の負例を足す |
| R5 | 既存 6 拒否の発火維持が証明できない | sol | **real・採用**。6 条件を `require_b4_iteration_authorization` の直接 unit test として全件残し、加えて**実 production context を持つ fixture** で関門通過後も同じ 6 拒否が発火することを固定する |
| R6 | exact message だけでは変異の単独帰属にならない | sol・luna | **real・採用**。§3 の変異事前登録で、各境界の負例に**副作用の不在**を観測させる。message 一致だけを根拠にしない |
| R7 | golden 一覧が不完全 (marker 付き on/off の 6 件) | sol | **real・採用**。`orchestrator/tests/test_p3_b4_closed_critic.py:2564-2588` の 6 件を保持する。他 file の historical pin は更新対象外として明記する |
| R8 | 起動器と実 factory・実 driver の合成が未証明 | luna | **real・採用**。**ユーザー依頼の中心**。registry の各値が `p3_s4_loop.main` / sort `main` / trigger `main` と **object identity で一致**することを検査する。順序テストで stub を使う場合は「routing の証拠」と明記し、負例の代用にしない |
| R9 | 負例 6 (test-only 流用) が過剰決定される | luna | **real・採用**。test-only 拒否の message を境界ごとに変え、下層 spy の未到達を併せて観測する |
| R10 | stdin の固定 JSON handshake は過剰 | luna | **real・採用**。proposal path は通常引数で受け、receipt 出力後の**単一行 ready signal** だけを stdin で待つ。JSON parser と schema は作らない |
| R11 | bootstrap 専用負例が無い | luna | **real・採用**。親の実測 M4 (bootstrap は receipt を要求しない) を閉じる負例を必須にする。不正な受理記録で実 verifier を通し、driver spy の未到達を観測する |
| R12 | projection 閉包は起動器追加前から変わる | sol | **real**。(P4) は維持 (起動器を閉包へ入れる)。独立算出 helper `test_p3_b4_closed_critic.py:491-554` と exact-set test `:1554-1617` も更新対象に含める。**「費用 0」は既存成果物の失効費用に限る**と親 brief を訂正する |
| R13 | (P3) 親案は誤り。旧 receipt-only CLI は hard-fail 化 | 両方 | **real・採用**。親の (P3) を撤回し、プラン案を採る。`p3_b4_closed_critic.main` は起動器を案内して失敗する |
| R14 | D1042 の一回 token を後付けしにくい | sol | **real・採用**。現行の物を `B4LaunchContext` と命名し、将来の外側 `SignedLaunchToken` と別概念にする |
| R15 | §7.2 の 2 項を丸ごと閉じたと書けない | luna | **real・採用**。項目を削除せず分割して書く。§5 に閉じた範囲を正確に記す |
| R16 | 重複 guard を最小へ減らせ | luna | **一部 real・採用**。`main` 境界の独立 guard を**置かない**と裁定した (下記) |
| R17 | 既存受理集合の拡張・D1043/D1050 の先取りは無い | sol | **所見なし**。確認済み |

### R16 の詳細裁定 — `main` 境界に独立 guard を置かない

3 driver の `main` は `default_cfg(b4_reflux_ablation=True)` を呼んで cfg を作る。
**鋳造関門 (G1) が先に拒否するため、`main` 側の guard は完全に過剰決定される。**
`DW-M01` は「同じ入力を拒否する層が前後に無いこと」を登録の条件にしているので、
`main` guard は登録できない。**したがって置かない。**

「driver main を `--b4-reflux-ablation` 付きで起動器なしに叩く」という負例は**残す**。
落ちる場所が G1 になるだけであり、ユーザー依頼の「支配点を通らずに実走できてしまう呼び方を
検査で赤にする」は満たす。負例は G1 の exact message と、build helper 未到達の spy を観測する。

## 3. プラン v2 — 確定した関門集合と変異事前登録 (DW-M01)

### 関門

- **G1 鋳造**: 3 driver の `default_cfg(..., b4_reflux_ablation=True)` は、生きた production
  `B4LaunchContext` が無ければ marker を作らず例外にする。context は `search_config` にも
  `CampaignConfig` にも保存しない (golden identity 不変の根拠)。
- **G2 反復**: base / sort の `run_one_iteration` 先頭、trigger の `_run_one_iteration_resolved`
  先頭と公開 `run_one_iteration` 先頭。cfg に marker があれば production context を要求する。
- **G3 駆動**: 3 driver の `drive_iteration` の既存 `b4_mode` 分岐の**最初の文**。
  `layout.ensure()` と state 前進より前に置く。
- **G4 certified sink**: `wal.append` の COMMIT 分岐。lock の `search_config` に exact marker が
  あれば、`b4_launch_context.json` の実在・campaign id 束縛・生きた context との一致を要求する。
- **G5 factory**: `create_b4_closed_critic_pair` は production context と driver kind の exact 一致を
  要求する。
- **G6 test-only**: 試験用 context は全 formal 境界で拒否する。message は境界ごとに変える。
- **G7 旧 CLI**: `p3_b4_closed_critic.main` は起動器を案内して失敗する。
- **G8 registry**: 起動器の driver registry の値が実 `main` と object identity で一致する。
- **G9 bootstrap**: 起動器の bootstrap は driver へ触れる前に実 `verify_b4_admission_record` を通す。
- **G10 projection**: 起動器 module を `projection_closure_manifest` の全 driver 共通 entries へ入れる。

### 変異事前登録 (実装前に確定。18 件)

|#|外す検査|単独帰属の根拠 (前後に同じ入力を拒否する層が無いこと)|
|---|---|---|
|M01|G1 base|前に層なし。後段は marker を持つ cfg を前提とするため、marker が作られない入力は到達しない|
|M02|G1 sort|同上|
|M03|G1 trigger|同上|
|M04|G2 base|marker 付き cfg の直接呼び。G3 は別の入口であり本経路を通らない|
|M05|G2 sort|同上|
|M06|G2 trigger resolved|公開 `run_one_iteration` とは別経路 (`p3_s4_loop_trigger_gating.py:1011`)|
|M07|G2 trigger public|`:793` の公開入口。resolved 側とは呼び手が異なる|
|M08|G3 base|後段の G2 が同じ入力を拒否するため、**副作用の不在で帰属する** — 外すと `layout.ensure()` と state 前進が起きる。負例は campaign root 不在と state 未前進を観測する|
|M09|G3 sort|同上|
|M10|G3 trigger|同上|
|M11|G4 sidecar 実在|前後に層なし。marker 付き lock で COMMIT を書く直接呼び|
|M12|G4 campaign id 束縛|別 campaign の sidecar を置く。実在検査は通るため単独帰属する|
|M13|G4 context 一致|sidecar は正しいが生きた context が別。上 2 つは通る|
|M14|G5 production context|factory 直呼び。受理記録読取より前|
|M15|G5 driver kind|正しい context だが kind 不一致。G5 の context 検査は通る|
|M16|G6 test-only を factory で拒否|test context は seal が異なる。production 検査を `evidence_class` の見た目だけにする弱い実装も殺す|
|M17|G7 旧 CLI hard-fail|前後に層なし|
|M18|G8 registry identity|registry を別 callable に差し替える。**stub 空回りを殺す変異** (ユーザー依頼の中心)|

**正例 (過剰拒否の検出、DW-M01):** 受理記録を検証して得た production context の下で、
起動器が実 factory と実 driver `main` を通して 1 iteration を完走し COMMIT を書けること。
これが赤になる変異は受理集合を不当に縮めている。

G9 と G10 は変異でなく直接検査で固定する (G9 は順序、G10 は manifest の exact set)。

## 4. scope 外・裁定パッケージ候補 (実装しない。ユーザーへ返す)

1. **非 B-4 の certified 成果物一般へ launcher capability を要求すること。** 全 campaign の
   受理集合を変える。D1050 (受理記録の置き場所の一本化) と接する。
2. **報告時の後付けの名乗り。** marker 不在の campaign を報告時だけ B-4 と名乗る経路は、
   report / ledger の consumer を変えないと閉じない。**D1033 が却下した「下流での名乗り拒否」と
   同じ形になるため、本 wave では設計しない。**
3. D1042 (使い捨て署名 token)、D1043 (送信前の写しの固定)、D1050。
4. proposal producer と critic 決定の因果的束縛、実行主体の真正性、pair の完全性、file-drawer。

## 5. 事前登録 §7.2 の更新方針 (R15)

項目を削除しない。次のとおり分割して書く。

- `run_one_iteration` 直呼び: **列挙した 3 driver の境界と certified sink では閉じた。**
  ただし marker を持たない campaign を後から B-4 と名乗る経路は開いている。
- marker 自己申告: **sanctioned driver 内での marker 自作は閉じた。**
  報告時の名乗り替えは閉じていない。
- 他の項目 (file-drawer、proposal 因果束縛、`policy_hint`、legacy critic route、PATH、
  pair 完全性、同一 process の属性書換え) は**1 項も削らない。**

## 6. 親 brief の訂正

- 「実走の入口は今 3 本」は誤り。公開 API を含めると `loop.run_campaign` と
  `pipeline.evaluate` も入口である (R1)。
- (P1) は「鋳造 + certified sink での消費」へ修正 (R3)。
- (P3) は撤回。旧 CLI は hard-fail 化する (R13)。
- (P4) は維持。ただし「費用 0」は既存成果物の失効費用に限る (R12)。
- (P5) は不十分だった。§3 の 18 変異と正例で置き換える (R6)。
