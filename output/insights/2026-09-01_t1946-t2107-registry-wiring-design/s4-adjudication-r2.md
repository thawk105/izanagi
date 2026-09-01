# 段 4 裁定 (2 巡目) — [T-1851 前半] + [T-2107] + [T-1946]

親裁定。base = 本 worktree HEAD (`e1e53d7db`、着手時 `2bf9cf387` から local main へ ff 済み)。
材料 = plan v2、段 3 2 巡目のレンズ A (所見 A2-1〜A2-8)・レンズ B (所見 B2-1〜B2-13)、
1 巡目の plan・レンズ 2 本 (`verbatim-r1/`)、1 巡目裁定 (`s4-adjudication.md`)、親の独立実測。

## 結論 — 本 wave では実装しない (4→7→8→9)

DW-S04 の「実装しない」裁定にあたる。段 5・6 を飛ばす。実装面の差分がゼロなので変異 matrix は
DW-S04 の免除に該当する。**受入全走は免除しない。**

**設計を諦めるのではない。** 本 wave の成果は、4 本の独立検査を通した実装可能な設計と、
残る 13 件の blocker への具体的な修正案、および次 wave が段 5 から始められる材料である。

### 根拠 1 — 土台が安定していない (B2-11、親が実測)

本 wave の編集面 3 file を、稼働中の 3 wave が同時に触っている。証跡 `overlap-scan.txt`。

| worktree | 重なる path |
|---|---|
| `worktree-dev-wave-t2027-root-class2` | `orchestrator/campaign/s8b_floor_campaign.py` (未 commit 6 行) |
| `worktree-dev-wave-t2074-a1-estimand-realign` | `orchestrator/tests/test_s8b_floor_campaign.py` |
| `impl-dev-wave-t2074-fix2` | `orchestrator/tests/test_s8b_floor_campaign.py` |

本 wave は同じ 2 file の journal writer、measurement wrapper、`_run_session`、resume、
result/finalize と、test 側の共通 helper を広く書き換える。2,650 行超の差分をこの上に載せると、
merge 解決の誤りが受理集合と proof 参照を変質させる。**先に 3 wave を着地させるのが正しい順序である。**

### 根拠 2 — 実装単位の依存順が誤っており、組み替えが要る (B2-9)

plan v2 の A→B→D(leaf)→C→D(consumer) では、A の adapter が受ける marker capability を
B が後から定義するため、A の時点で API が未成立になる。レンズ B が示した正しい順は
`B1 (claim/marker capability) → A (core/profile/adapter) → B2 (inspector) → D1 (contract/proof 型)
→ C (writer/reconcile) → D2 (consumers/fixtures)` の 6 段である。
各境界の symbol・引数・戻り型を plan に固定してからでないと実装子へ渡せない。

### 根拠 3 — 未解決の設計 blocker が 13 件残っている

いずれも具体的で修正案があるが、plan に反映しないまま実装子へ渡すと死んだ設計を作る。
下表のとおり全件 real と裁定した。

### 根拠 4 — 規模が 1 wave の実装・レビュー・変異検証に収まらない

レンズ B が AST 静的計数で C-family 103 node、D-family 117 node = 220 node に達すると実測し、
A/B/launcher を足すと plan v2 の上限 230 を超えると判定した。plan v2 自身も
「通常の 1 wave で 4 単位を安全に実装し 1 commit へ統合できる規模ではない」と述べている。

---

## 所見の real / refuted と採否 (2 巡目)

### レンズ A (2 巡目)

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A2-1 | plan v2 は前巡 8 所見のうち 4 件だけを完全に閉じた | **real** | 採用。閉じたのは claim 世代化・crash cut・壊れた tail・earlier-result 層 |
| A2-2 | v1/v2 readable 方針は現 core では単一 profile として成立しない。正規 1 段 v1 は列挙から漏れ、共有 root の 2 段 v1 残骸は列挙対象に入る | **real / blocker** | 採用。v1/v2 を別 `DomainProfile`・別 slot codec・別 layout とし、genesis schema を peek して dispatch する。3 種 (正規 1 段 v1・合成 2 段 v1・v2) の受理表を plan へ入れる |
| A2-3 | measurement ordinal を増やすだけの予算回避 | **refuted** | 採用しない。予算鍵は先頭 2 軸のままなので cap 10 で閉じる。ただし「第 11 start が拒否される負例」は登録する |
| A2-4 | `retryable-failure` は次 attempt を開く**認可**であり、pre-probe 除外の符号化と衝突する | **real / blocker** | 採用。**親裁定 2 の具体化を訂正する。** measurement retry 用遷移と recovery attempt 用遷移を別権限にする |
| A2-5 | 理由導出の入力を作る呼び手が campaign 側にいる | **real / blocker** | 採用。ただし下記「親の補足」を付す |
| A2-6 | 被覆の attempt 集合が producer 自己申告なので恒真化が残る | **real / blocker** | 採用。**親裁定 1 の具体化を訂正する。** schedule と admission claim から独立に導出した authoritative 集合と比較する |
| A2-7 | M6 と M9 の単一理由性が未確定 | **real / nit** | 採用。M6 は canonical JSON のまま N 以後の chain だけ切る入力へ、M9 は shape 保持で head だけ別の有効値へ再照準する |
| A2-8 | 親裁定 1・2・4 の**具体化**が反証された (目的自体は成立) | **real** | 採用。下記「親裁定の訂正」 |

### レンズ B (2 巡目)

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| B2-1 | 被覆が集合等値なので全単射にならない (重複 `attempt_id`・summary 改変を潰さない) | **real / blocker** | 採用。v5 の `attempts` を sessions から完全再導出し、exact key・ID 一意性・各 identity の一回出現を検査する |
| B2-2 | 新世代作成の crash が永久的な不完全世代を残す | **real / blocker** | 採用。非 64hex の staging directory 内で完成させ、directory rename で公開する |
| B2-3 | terminal 前 crash の状態表が既存 cut-6 再開と衝突する | **real / blocker** | 採用。journal-only / registry-pending / registry-terminal の 3 状態を round loop 前に分類する |
| B2-4 | `raw_output_sha256` に要求する 2 つの byte 列が一致しない (core の compact JSON と journal の newline 付き行) | **real / blocker** | 採用。`serialize_session_line(record)` を単一源にし、object 用 canonical digest とは別名にする |
| B2-5 | sealed reason 導出が caller の自己申告を再読するだけ | **real / blocker** | 採用。A2-5 と同一 |
| B2-6 | v1/v2 の具体的 codec が無い | **real / blocker** | 採用。A2-2 と同一 |
| B2-7 | proof inspector の設置位置が scope 外の verified recovery を壊す | **real / blocker** | 採用。v5 proof 用 current-generation inspector を**別 API** として新設し、既存 recovery reader と 4 軸 codec を保存する |
| B2-8 | `finished_iso` 追加が journal v3 の exact key 集合を破る | **real / blocker** | 採用。`finished_at` を session 外の認証済み terminal field に置き、journal session shape を変えない (レンズ B の代案を採る。journal v4 への版上げは受理面を広げるので採らない) |
| B2-9 | 素集合な file 所有だけでは独立 dispatch できない | **real / blocker** | 採用。根拠 2 のとおり 6 段へ組み替える |
| B2-10 | fanout 実数が見積もり上限を超える | **real** | 採用。根拠 4 |
| B2-11 | 稼働 3 wave を先に解消しないと統合の基準 hunk が定まらない | **real / blocker** | 採用。根拠 1 |
| B2-12 | 共有残骸が本番 freeze と現行 test へ衝突する懸念 | **refuted** | 採用。残骸は `db07b575` freeze 配下で本番は `315b1eb8`。test は一時 Git repository を作る。**本番と通常 test に影響しない** |
| B2-13 | 親裁定 5 の番号が brief と裁定正本で食い違う | **real / nit** | 採用。brief 側の世代列挙は「親裁定 6-a」とする |

---

## 親裁定の訂正 (1 巡目の裁定のうち具体化を直す)

| 1 巡目 | 目的 | 具体化の訂正 |
|---|---|---|
| 親裁定 1 (被覆) | **維持** | 比較の片方を producer 由来にしない。schedule と admission claim から独立導出した authoritative な planned attempt 集合を使い、集合等値でなく全単射で照合する (A2-6 + B2-1) |
| 親裁定 2 (pre-probe を台帳へ) | **維持** | `retryable-failure` で符号化しない。measurement retry の遷移と recovery attempt の遷移を別権限にし、pre-probe terminal が `attempt_ordinal` を自動認可しないことを transition policy に明記する (A2-4) |
| 親裁定 3 (全行 replay + prefix 比較) | **維持** | 訂正なし。両レンズとも反証していない |
| 親裁定 4 (不足入力 6 件) | **維持** | 理由導出は launcher が所有する生の事実 (probe / classification receipt / throughputs / exec failures / rep evidence) から再導出し、自己申告 field は比較対象にだけ使う (A2-5 + B2-5) |
| 親裁定 5 (実装単位) | **訂正** | A/B/C/D の 4 単位でなく、B1 → A → B2 → D1 → C → D2 の 6 段 (B2-9) |
| 親裁定 6 (共有 root に触れない) | **維持・明確化** | 「既存 bytes は書換えないが**読む**」を明記する。合成残骸と同 shape の fixture を横断予算 test へ入れる (B2-6)。世代列挙の規則は「親裁定 6-a」と呼ぶ (B2-13) |

### 親の補足 — A2-5 / B2-5 の実際の重さ

親が現物で確認した。現行 campaign の `excluded_reason` は**既に機械的に導出されている** —
凍結閾値を使う単一の純関数 `s8b_floor_stats.assess_session()` と固定の優先順位
(competing → launch → rep integrity → partial → performance → valid) で決まり、
自由選択は無い (`s8b_floor_campaign.py:6078-6109`)。
したがって D1032 の「性能量に到達する前に理由を固定する」は、**規則の凍結**という意味では
現行コードでも満たされている。

両レンズが指摘しているのはそこではなく**信頼境界**である。導出を実行しているのが campaign
(信頼境界の外) なので、規律 2 が想定する「最適化圧力が正しさゲートを攻撃する」状況では、
producer の変異がこの導出を書き換えられる。修正は同じ純関数を launcher 側から呼ぶだけで済み、
設計のやり直しではない。**採用する。**

---

## 変異事前登録 (DW-M01)

**登録しない。** 実装面の差分がゼロであり、plan v2 の変異位置は上記の訂正で確実に動く。
次 wave が plan v3 の確定と同時に登録する。plan v2 の候補 9 件と、A2-7 の再照準
(M6・M9)、A2-3 の追加負例 (第 11 start) は次 wave の出発点として insight へ残す。

---

## ユーザーへ返す裁定パッケージ

### 1. 実装順序 (親の推奨あり)

本件は **T-1851 前半 + T-2107 + T-1946 の 3 task 閉包**で、D1341 により 1 commit で land する。
親の推奨する進め方は次のとおり。

1. **先に稼働 3 wave (t2027、t2074 の 2 系統) を着地させる。** 本 wave の編集面と重なる。
2. plan v3 を起草し、本裁定の 13 blocker と 6 段分割の境界 (symbol・引数・戻り型) を確定する。
3. 6 段の実装単位を順に unlanded checkpoint として作り、統合後に 1 commit だけ land する。

### 2. 親裁定 1 (proof に試行の被覆を加える) — ユーザーが覆せる

D1337 が定めた `{row_count=N, chain_head_at_N}` だけでは、**genesis 1 行の台帳でも別 campaign の
台帳でも検証が通る。** 4 本の独立検査がこれを実測した。親は「被覆の追加は D1337 の変更ではなく
D1194 の実装である」と読んで採用した。覆す場合は「恒真な束縛のまま land してよいか」を示す必要がある。

### 3. 親裁定 4 の classification authority (新しい信頼の根) — ユーザーが覆せる

launcher の出力前分類方針を名指しする production 定数を新設する。既存の scheduler accounting
authority と同じ形で方針 bytes から digest を導出する。覆す場合は別の権限の置き場所を示す必要がある。

### 4. 実測で判明した既存の状態 (裁定不要。記録のため)

- 共有 admission root に、2026-08-27 の実装試行が残した schema v1 かつ 2 段 path の台帳
  (193 行) と consumption catalog (96 行) が実在する。凍結 hash は本番値ではなく、
  本番 campaign にも通常 test にも影響しない。削除も書換えもしていない。
- D880 が意図的に空にした回復権限 pin は変更していない。
