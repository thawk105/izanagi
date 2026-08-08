# [T-671] + t530 件 6 段 4 裁定 — real/refuted、採否、scope、パッケージ確定

段 3 は 2 レンズとも **NO-GO** (A=sol / must-fix 11・nit 1、B=luna / must-fix 7・nit 3)。
本 wave は設計 wave であり、**実装しない**。`DW-S04` に従い段 5・6 を飛ばして `4→7→8→9`。
変異 matrix は同条項で免除、受入全走は免除しない。

## 親が独立に再測して確定した事実 (レンズの主張の検証)

1. **B-02 は real (親が再現)**: `orchestrator/campaign/p3_s4_loop.py:878` が `layout.ensure()` →
   `ident.ensure_resumable_attempts()` を実行してから `run_campaign` を呼ぶ。
   `run_campaign` 内部だけを直しても「durable write より前に停止」は成立しない。
2. **B-09 は real (親が再測)**: dev-wave reference の実測は core 8,655 / workers 4,526 /
   mutation 3,689 / operations 8,329 = **aggregate 25,199 / cap 25,200 (残り 1 byte)**。
   前 wave (エントリ 319) 時点の 16 bytes からさらに縮んだ。個別残は mutation 61 / operations 71。
   `check_docs.py` は現状 rc=0 (違反なし)。
3. **A-04 は real だが本 wave の plan の欠陥ではない**: `test_campaign.py:2513` の caller inventory は
   `expected_run_calls` が固定 dict、`ast.Name` のみ照合。かつ `direct_sinks` 側は
   `assert any(... for call in calls)` (:2553) なので、authority keyword を持つ呼出しが 1 本あれば
   同ファイルの他の呼出しは素通りする (`expected_run_calls` 側は `all(...)` で正しい)。
   **既存 gate の弱点**であり、[T-671] の所有ではない。新規起票候補としてパッケージへ返す。
4. **A-02 は real・構造的**: `certified_writer_preflight.py:85-100` は import 済み module の
   `__file__` をディスクから読み直す。実行中の bytes ではなくディスク上の bytes を検査するため、
   import 後の差し替えは検出できない。これは preflight を再利用するすべての案に残る限界であり、
   案の優劣を分けない (脅威モデルの明示で扱う)。
5. **B-01 は real で、親が段 2 完了直後に独立発見した事実と一致**:
   `orchestrator/campaign/p3_s4_loop_trigger_gating.py:92` に `_CAMPAIGN_ENV_KEY = "measurement_env"`
   が実在する (D125 決定 (2) の実装)。したがって R-B2 の「D13 の env 非 identity 規則を回復する」は
   **不正確** — `measurement_env` を残す限り env は依然 campaign id を分ける。
   `docs/orchestrator-design.md`「env は campaign 同一性に含めない」と D125 決定 (2) の緊張は
   本 wave が作ったものではなく既存である。

## 所見の裁定

### real・採用 (パッケージの設計軸そのものを変える)

| 所見 | 裁定 | パッケージへの反映 |
|---|---|---|
| A-01 / B-03 / B-05 (収束) | **real・親 brief の誤りを訂正** | 親 brief P1 は「silo と qualification の独立 2 実装があるから `DW-G03` を満たす」と書いたが、`DW-G03` が要求するのは**同型欠陥が異なる producer/consumer で 2 件再現すること**であって、既に binding を持つ実装が 2 つあることではない。かつ silo (`silo_ladder_rung1.py:254`) と qualification (`qualification/contract.py:38`) はどちらも loader 2 本より**広い**閉包を束縛しており、「exact 2-path」への縮約に根拠がない。**束縛閉包の選択を独立した択一 (R1) へ格上げする** |
| A-02 | real | 全案共通の残余として脅威モデル節に明記。案の優劣を分けない |
| A-03 / B-05 後段 | **real・本 wave の結論を支える** | `DW-G04` の発火 artifact / 計測 ID が**どの案にも存在しない**。既存 30 campaign は H も `build_admission` も持たないため、B の新 gate を現 production artifact で正に発火させられない。**実装の前提条件 (R7) として「先に発火計測を作る」を明示** |
| A-05 | real | v1 lane を残すすべての案に anti-downgrade 規則が要る。R3 の採用条件へ |
| A-08 | **real・親の実測 B の一般化を訂正** | 分裂の必要条件に `unfinished` は入らない。t530 は旧 root を探す前に current H で id/layout を確定するため、g1 campaign が terminal でも g2 で同じ論理入力を再実行すれば新 root ができる。「g2 活性化 → t530 land」の順序でも、無束縛 root と H 束縛 root が両方 WAL を持てば 2-hit になる。**成果物の形として「分裂」と「断絶」は区別できない** |
| A-09 | real | 境界比較の粒度 (H のみ / activation state 全体) を独立の択一 (R5) へ |
| A-10 | real | 順序案には authority-free な v1 を書ける窓がある。順序裁定 (R8) の条件へ |
| B-02 | real (親が再現) | 「書込み前停止」を実現する層を択一 (R6) へ |
| B-04 | real | v1 lock の位置づけ (read-only historical か条件付き resume 可か) を R3 の採用条件へ |
| B-06 | real | t530 の land を保留する順序を R8 に明記 |
| B-01 | real | D125 決定 (2) の `measurement_env` を保持するか supersede するかを択一 (R4) へ |
| B-10 | real | 核となる vertical slice と延期部分の分離を R7 の選択肢へ |
| B-08 | real | パッケージで実測・反実仮想・一般化を節単位で分離する |
| B-09 | real (親が再測) | `docs/dev-wave/**` へ規範文を足す実装は [T-664] の後。パッケージ本体は `output/insights/` (予算対象外) |

### real・scope 外 → パッケージで既出として明記 (二重起票しない)

| 所見 | 扱い |
|---|---|
| A-06 (raw reader / freeze / offline report の迂回) | **t530 裁定パッケージ件 2 と同一面**。新規起票せず、件 2 の射程が [T-671] の source binding にも及ぶことを注記する |
| A-07 (S8b private lock) | **t530 件 3 と同一面**。同上 |
| A-12 / B-07 (Layer3 の ref domain と D75 の field 命名) | 設計択一ではなく実装時の命名義務。実装 wave の前提条件として記録する |
| A-11 (R-B3 の lineage scan race) | R-B3 を fallback として残す場合の既知欠陥として R2 の選択肢に注記 |

### refuted

| 所見 | 反証 |
|---|---|
| A-04 を [T-671] の must-fix とすること | 指摘自体は real (親が再現) だが、既存 `test_campaign.py:2513` の弱点であって本 wave の plan が導入したものではない。[T-671] の scope で修正すると所有が割れる。**新規起票候補としてパッケージへ返す** |
| 「A の穴は g2 固有」という brief の含意 (A-10 が指摘) | 親も同意。loader 束縛の欠落は g1 でも成立しており、g2 活性化は**発覚の契機**であって発生条件ではない。パッケージの問題設定を訂正する |
| R-B2 が「D13 の env 非 identity を回復する」 | `measurement_env` (D125(2) 実装、`p3_s4_loop_trigger_gating.py:92`) が残る限り回復しない。R4 で明示的に決める |

## 親の provisional 裁定の帰趨

- **P1 (b) 系が最小 = 撤回**。`DW-G03` の読み違いをレンズ 2 本が独立に指摘し、親が再確認した。
  束縛閉包は独立の択一へ。
- **P2 (ever-active 解決で旧世代 resume) = 撤回**。段 2 が反証: `resolve_by_contract_sha256` は
  履歴検証用で、`authorize()` は terminal contract のみ発行する。旧 H での新規計測許可は
  **受理集合の拡大**であり、親が黙って選べない (R2 の選択肢 (c) として明示的にユーザーへ返す)。
- **P3 (活性化の追加前提にしない) = 条件付きで維持**。t530 を未 land のまま T-657 を先行させる限り
  B の発火条件は成立しない。ただし A-10 の無保護窓があるため、R8 で条件付きに書く。
- **P4 (同型軸・1 パッケージ) = 維持**。段 2 の共通原則 (ambient current は最初の durable write の
  authority 解決にだけ使い、exact identity を atomic lock へ固定する) を採用する。
- **P5 (受入環境) = 維持**。

## 変異事前登録 (`DW-M01`)

**免除**。実装差分ゼロの「実装しない」裁定であり、`DW-S04` の免除条項に該当する。
受入全走は免除しない。

## 成果物影響 (`DW-G05`)

- 本 wave が実装しないことの影響: certified 選択・材料レポート・試行台帳は現状のまま
  loader bytes を束縛せず、g2 活性化後も activation 参照だけの検証を通過し続ける。
  値・受理集合・参照はいずれも本 wave では変わらない。
- 実装しない代わりに得るもの: 束縛閉包・脅威モデル・受理集合の変更を、発火計測なしに
  親が既成事実化することを防ぐ (`DW-G04`)。
