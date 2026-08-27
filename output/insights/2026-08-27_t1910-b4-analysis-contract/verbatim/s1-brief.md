# 段 1 brief — [T-1910] B-4 分析契約の一括凍結 + [T-1913] 実行責任者の記入

- wave: `dev-wave-t1910-b4-analysis-contract` / branch `worktree-dev-wave-t1910-b4-analysis-contract`
- base main: `dd6621397`
- 対象文書: `docs/phase3-b4-reflux-ablation-preregistration.md` (発効前 draft、`LIVING_DOCS`)

## scope (この wave で行うこと)

1. **分析契約の一括凍結 (D1082)** — 次の 4 項目を同じ変更単位で凍結する。
   (a) 赤 precursor の母集合、(b) 最小重要効果、(c) n (と検定単位)、(d) primary outcome の純関数。
2. **最小重要効果は pilot と独立に固定する。** pilot の権限を「n と分散上限の導出」だけに限定する
   規範を同時に置く (4 項目を同じ pilot から導出すると導出関数が恒真化する)。
3. **§5 の「実行責任者・開始時刻」欄へ実行責任者 `thawk105` を記入する** ([T-1913])。
   ユーザーが 2026-08-27 に確定。控え = `inputs/ruling-inbox-run-owner.md`。開始時刻は未定のまま。
4. §9 (HARKing 境界) へ、本凍結の時点で新たに閲覧した B-4 結果が無いことを記録する。

## scope 外 (触らない)

- `docs/phase3-main-experiment.md` — S-1 freeze が bytes を pin する (F78)。1 byte も触らない。
- §5.1 の「対象 driver と軸」bullet、§7.2、§8、§10 の probe 記述 — **並行稼働中の wave
  `dev-wave-t1769-b4-wiring-probe` (同じ base `dd6621397`、段 1) の編集面**。F606 の走査を
  branch tip・worktree dirt・repo 外 job dir の 3 面で行い、この 1 本だけが hit した。
- 文書の発効。§6 の前提条件は本 wave 後も未充足のままであり、B-4 は実走できない。

## 不変条件 (破ったら止まる)

- **§5 は機械的な固定表である。** `orchestrator/campaign/p3_b4_admission_record.py` が
  `## 5.` と `### 5.1` の間の非空行をちょうど 12 行 (`|欄|値|`, `|---|---|`, 10 行) と要求し、
  行ラベル 10 件を NFKC 正規化後の exact 集合で照合する。**行の追加・削除・ラベル改変・
  表の外への散文追加は checker を壊す。** 逐語 = `inputs/admission-section5-contract.py.txt`。
- 値セルは非空かつ予約 sentinel (`未記入`/`要記入`/`TBD` 等) を含まないことが admission の
  条件である。**本 wave 後も全欄が揃わないため admission は閉じたままでなければならない。**
- 値セルに説明文・条件を書かない (§0)。規範は §5.1 と §7 に置く (§0)。
- `LIVING_DOCS` 規律 — 可変状態の再掲と行番号参照を書かない。
- **凍結は結果を見る前に行う。** B-4 の実走結果は存在しない (§9 の 2 件は正式標本外)。
  既成事実化しない。正しさゲート (§4)・全件報告規則 (§7.1) を緩める方向の変更をしない。

## 親の provisional 裁定 (P。攻撃対象。子は守らず攻撃せよ)

- **(P1) 実装面の差分ゼロ (docs のみ)。** primary outcome を Python の純関数として実装しない —
  B-4 データが存在せず発火する consumer が無い (`DW-G04`)、規律 5 (段階導入)。
- **(P2) 最小重要効果は §5 の固定表へ行を足さず、新設 subsection (§5.2 想定) に置く。**
- **(P3) §5 の 3 欄 (母集合 / n と検定単位 / primary outcome) は、凍結定義そのものではなく
  凍結定義への参照を値として持つ。** 定義本文はセルに書かない (§0)。
- **(P4) 実行責任者欄は「実行責任者 = `thawk105`、開始時刻 = 未記入」の複合セルにする。**
  sentinel が残るため admission は閉じたままで、fail-closed が保たれる。
- **(P5) 最小重要効果は確率優越 A の尺度で固定する。** 具体値は段 2 の plan と段 4 の裁定で確定する。
- **(P6) n は数値を今は確定できない。** 凍結するのは「凍結済み母集合 + 事前固定した最小重要効果 +
  pilot 由来の分散上限」から n を出す導出関数と、検定単位 = block である。

## 成果物影響 (`DW-G05`)

この 4 項目が凍結されない限り B-4 は実走できず、論文 §8 の機序証拠 (規律 3 の還流が効くか) は
空欄のままになる。結果を見てから凍結すると、母集合・効果量・n の境界を都合よく選べるため、
成果物に載る B-4 の判定 (成立 / 不成立 / 判定不能) が証拠として無価値になる。
実行責任者 1 行が入らない限り、他の欄が揃っても §6 前提条件 1 により実走は禁止のままである。

## 成果物の形

- `docs/phase3-b4-reflux-ablation-preregistration.md` の差分 1 本 (§5 の 4 セル + 新 subsection + §9)。
- spool fragment (worklog / decisions)。insights は逐語を置く。

## 並列分割方針

受理集合 (admission の値セル契約) と正しさ防壁 (事前登録の拘束力) に触るため軽量版にしない。
段 2 plan 1 本 (read-only)、段 3 敵対相談 2 本 (lane sol / luna)、段 6 レビュー 2 本。
実装面の差分がゼロなら段 5 の Codex 実装子は不要 (docs 本文は親が書く)。
