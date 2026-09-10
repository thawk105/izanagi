# 裁定パッケージ — toolchain 束縛を実装し、4 件を裁定へ返す

wave `dev-wave-t783-toolchain-binding` / branch `worktree-dev-wave-t783-toolchain-binding` /
base main `67760fdb` → 取り込み後 `b13b7ea8`。

起票根拠 = worklog 412 の [T-783] S-1〜S-4 (全問推奨で裁定済み)、worklog 403 の [T-747] (B)、
worklog 413 の [T-781] (保留終端)。手順の正本 = `docs/phase3-8b-restart-runbook.md`。

---

## 0. 結論を先に

**依頼は「[T-783] を裁定どおり実装 → [T-747] (B) の toolchain 束縛を receipt 側へ実装し
混用不可を機械検査で固定 → 同 wave で [T-748] の W-2 床値実測へ進む」だった。**

| 依頼 | 状態 |
|---|---|
| [T-783] S-1〜S-4 の実装 | **完了** (S-3 の attempt 脚を除く。§2 の 1) |
| [T-747] (B) の toolchain 束縛を receipt 側へ | **完了** |
| 混用不可を機械検査で固定 | **完了** (§1) |
| [T-748] W-2 の床値実測 | **投入不可** (§3)。キュー投入は行っていない |

裁定へ返すのは 4 件 (§2)。うち 2 件は**裁定時点で未見の新事実**によるもので、
`DW-S04` に従い親は不採用にせず再裁定へ戻している。

---

## 1. 「混用不可」の機械的な固定 — 何が止まるようになったか

一次資料を最新まで辿って定義を確定した。

- worklog 383 ([T-747] 初回裁定 (a)): 「**既存 `linux-baremetal` 床値との混用は不可**
  (環境束縛量として Pegasus で新規取得)」
- worklog 403 ([T-747] 再裁定 (B)、最新): 「toolchain 束縛は env contract へ field を足さず
  契約の外へ置く — contract 内 `calibration_ref` の実 calibration bytes を derived toolchain
  authority とし…**toolchain 混用不可の趣旨は不変**」

**したがって「混用」= 環境・世代をまたぐ床値の混用**である
(親 brief の provisional 裁定 P6 は「cc/cxx の対の混用」と誤解しており、撤回した)。

実装は次のとおり固定した。

- `contract.calibration_ref` の calibration に `acquisition_receipt` が**無い**契約
  (= legacy の `linux-baremetal`) は、**receipt 不在で fail-closed に拒否**する。
- `acquisition_receipt` が**ある**契約 (= `pegasus` gen1 / gen2) では、実 toolchain が
  **その世代の登録値と一致する場合だけ** build を通す。

**この拒否が恒真に眠っていないことは実測で確認できた** — 段 6 の焦点実測で
`test_s8b_ratified_freeze.py` の 3 件が「legacy 較正で実 floor core を回す fixture」だったため
実際に拒否されて赤くなった。gate は緩めず、fixture 側を `acquisition_receipt` つきの
合成 v2 較正へ追随させて閉じた。

`contract_sha256` は不変なので、発効記録・floor protocol・selector 予測封印の 3 pin は生きている。

---

## 2. 裁定へ返す項目

### S-3'. attempt 実測値の脚を実 provenance にするか (新事実 2 件)

S-3 = (a)「shell の `$ATTEMPT_DIR` 値を driver へ渡す」は裁定済みだが、**実装していない**。
裁定時点で未見だった事実が 2 件ある。

1. **production wrapper の official 注入拒否は、引数名を明示列挙した dict である**
   (`s8b_floor_campaign.py:2763-2790`、親が実コードで確認)。新引数 `attempt_toolchain` を足すと、
   **列挙に加えない限り注入拒否を素通りする** — official 経路で caller が用意した toolchain 値を
   「実測」として受理する穴が開く。これは規律 2 (正しさゲートを緩める変異を採用しない) に触れる。
   逆に列挙へ加えると、将来の正規 official は必須値を渡した瞬間に必ず赤になる。
2. **attempt snapshot を job 識別子へ束縛する設計が無い。** PBS job ID・submission nonce・
   execution receipt・raw file hash のいずれとも結びついていないため、そのまま入れると
   **caller 注入値を「実測」と記録する恒真な緑**になる。

**択**: (a) 注入拒否の列挙を変更して実 provenance 化する (束縛設計を先に決める) /
(b) attempt dir を job 識別子へ束縛する設計を先に起票し、実装はその後 /
(c) 「caller-provided observation」へ降格し、official の防御としては数えない。

**親の推奨は (b)。** (a) は束縛設計が無いまま拒否集合を触ることになり、順序が逆である。
(c) は「shell が記録した値と build が観測した値が食い違っても検出しない」を残すため、
そもそも三者照合を求めた動機と噛み合わない。

### S-2'. 成果物へ binding report を載せるか (新事実 1 件)

S-2 (a) の条件「残る穴を**手順書と成果物へ**明記する」のうち、**手順書の脚は本 wave で閉じた**
(`docs/phase3-8b-restart-runbook.md` §5「R-4 の決着」)。**成果物の脚は実装していない。**

**新事実**: 再凍結の authoritative consumer は manifest / result の top-level key を
exact 集合で検査し、余分な key を必ず拒否する
(`s8b_ratified_freeze.py` の `_MANIFEST_KEYS` / `_RESULT_KEYS` と `_exact_keys`、親が確認)。
追記すると**生成した床値成果物が再凍結を通らず、oracle が binary を certified source として
受理できなくなる**。schema 改版と consumer 改修を同じ land に含める必要があり、
裁定した scope を超える。

**択**: (a) schema 改版 + consumer 改修 + manifest↔result↔calibration 一致検査を 1 wave で /
(b) 既存 schema が許す versioned extension として設計し直す / (c) 手順書だけで足りるとする。

**親の推奨は (a)。** (c) は「成果物だけを見て、どの toolchain で作られたかを再検証できない」
状態を恒久化する。(b) は現行 schema に拡張点が無いため、実質 (a) と同じ規模になる。

### S-5'. authority の完全性 (cxx version / cmake path / module_list / bytes hash)

いずれも receipt に無い、または観測経路が無いため**束縛していない**。手順書に明記済みで、
「後続の certified 判定でこれらを検査済みと見なしてはならない」と書いた。
authority へ加えるには calibration の再発行 (S-2 (b)) が要る。

**択**: (a) [T-657] の世代交代と同じ wave へ寄せる (親の当初推奨のまま) / (b) 独立 wave / (c) 現状維持。
**親の推奨は (a)。** 単独で再発行すると発効順序が floor protocol と selector 封印の作り直しを誘発する。

### S-6'. floor / silo ladder 以外の producer へ広げるか

段 3 レンズ B が列挙した scope 外の層 — calibration receipt producer、floor-like scoping producer
(`pegasus_floor_scoping`。records/threads/clocks だけを照合し toolchain は未束縛)、
between-run noise floor、trace/performance candidate producer (`pipeline` / `loop`。site resolver は
使うが receipt 束縛なし)、certified admission。

**択**: (a) contract-aware な build 境界へ 1 本置いて全 producer を守る / (b) 必要になった層から個別に /
(c) 現状維持。**親の推奨は (b)。** (a) は S-1 の裁定時に「1 wave に収まらない」として却下されており、
現時点でも同じ判断が成立する。

---

## 3. [T-748] W-2 が投入できない理由 (実測 3 点、独立に成立)

| # | 塞いでいるもの | 実測 |
|---|---|---|
| 1 | official の無条件拒否 | `s8b_floor_campaign.py:207-217` が `mode=="official"` を無条件 raise |
| 2 | pilot は再凍結に使えない | `:2453` と `:3174` により pilot は `eligible_for_refreeze=False` |
| 3 | 投入 shell が official 固定 | `tools/pegasus/floor_campaign.sh:962`。job-result payload も `"mode":"official"` literal |

W-1 = [T-781] は worklog 413 で「official 受理集合は空集合のまま維持・A 系列の後まで保留」と
裁定済みである。**第 1 世代で実測する方針 ([T-748]) は維持したまま、W-1 の再裁定を待つ。**
段 3 レンズ B も独立に同じ結論に達している (「権威ある W-2 を今日走らせる抜け道はありません」)。

---

## 4. 親 brief の訂正 (レンズが正した親の主張)

| 主張 | 判定 |
|---|---|
| 「A-2 の gate は pilot 床値 campaign で runnable today」 | **refuted**。`submit_floor.sh` に pilot 切替は無い |
| P6「cc と cxx が同一 toolchain 由来であることを固定する」 | **refuted**。固定できるのは「登録済み対と一致」まで |
| M-8「cmake を束縛すると恒真な赤」 | **login 限定**。compute (bnode005) の cmake は登録値と一致する 3.25.0 |
| M-5 / M-6 の一般化 | compute 側の `gcc` / `g++` の realpath と version は**未確認のまま** |

最後の項は手順書へ書いた — **初回の実 run で gate が拒否したら、それは正しい fail-closed であって
bug ではない。gate を緩めて通してはならない。**

---

## 5. 検査結果

- 焦点 10 file = **494 passed / 2 skipped / rc=0** (計算ノード)
- provenance 全史監査 = rc=0 (2463 件、新規違反なし)
- 変異 = 登録 14 件 → **12 KILLED / 1 SURVIVED / 1 MISMATCH**、erratum と再照準を経て
  **13 KILLED / 1 MISMATCH** (M07 は予測 node が狭すぎただけで殺されている)
- 段 6 レビュー 2 本はいずれも **NO-GO**、real 所見 3 件。fix 3 巡 + 変異由来の追加 1 本で閉じた
