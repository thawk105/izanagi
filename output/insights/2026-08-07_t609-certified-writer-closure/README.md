# [T-609] certified writer の閉包 — wave 逐語一式 (2026-08-07)

wave = `dev-wave-t609-certified-writer-closure` /
branch = `worktree-dev-wave-t609-certified-writer-closure` / 起点 = `bb824d8b`

worklog の該当エントリが要約の正本。ここは逐語と機械成果物の凍結先である。

## 何をしたか

環境契約による認可の強制点を、campaign ループ (`loop.run_campaign`) ではなく
**certified を実際に書く `pipeline.evaluate`** へ移した。必須 keyword-only 引数
`authorization_contract` を新設し、layout / WAL / build のいずれよりも前に 5 条件を検査する。
PBS wrapper 2 本には、最初の script 書込みより前に静的 admission preflight を置いた。

## 実測

| 項目 | 値 |
|---|---|
| 受入全走 | 7199 passed / 20 skipped / rc=0 (`acceptance-4`) |
| 受入の推移 | 110 failed → 4 failed → 0 failed |
| 変異 | 7/7 KILLED、SURVIVED 0、MISMATCH 0、期待 node と実測 node 全件一致 |
| 変異 baseline | PASSED (333 passed / 9 skipped) |
| provenance | 1724 件、新規違反なし |
| 実装 commit | `f91db60d` (36 files) → fix `05fa1772` / `ea30806c` / `bb60878b` |

## この成果が主張できない範囲

- 認可の事実は campaign identity にも WAL COMMIT にも残らない。したがって
  **proof chain へ束縛された閉包ではない**。この束縛は [T-530] の残件。
- shell 側で言えるのは次に限る。
  > PBS が job body を開始した後、当該 wrapper が明示的に管理する durable output および
  > scratch を初めて変更する前に、submission / source identity・current registry・
  > protocol / control・calibration bytes・compute-site の静的 read-only admission を完了する。
  > qsub 側の receipt / ledger、PBS spool / prologue / epilogue、scheduler が作る `$TMPDIR`、
  > filesystem atime、full hardware attestation probe の scratch は対象外である。
- `attestation_mode="required"` の hardware attestation は最初の書込みより前に行えていない。

## ファイル

| ファイル | 内容 |
|---|---|
| `brief.md` | 段 1 brief (実測 8 件と provisional 裁定 P1〜P5。**4 件は後段で反証された**) |
| `s2-plan.md` | 段 2 プラン起草 (P1 を build-v2 混同として却下) |
| `s3-lensA.md` / `s3-lensB.md` | 段 3 敵対 2 レンズ (must-fix 8 / 10、両方 NO-GO) |
| `s4-ruling.md` | 段 4 裁定 = plan v2、変異事前登録、scope 外 5 件の裁定パッケージ |
| `s5-a.md` / `s5-b.md` | 段 5 実装子報告 (Python 層 / shell 層) |
| `s6-lensC.md` / `s6-lensD.md` | 段 6 敵対レビュー 2 レンズ (must-fix 6 / 4、両方 NO-GO) |
| `s6-adjudication.md` | 段 6 所見の裁定表 R1〜R11 と fix 指示 |
| `s6-fix-a.md` / `s6-fix-b.md` / `s6-fix2.md` / `s6-fix3.md` / `s6-fix4.md` | fix 各巡の報告 |
| `mutation-spec.json` | 変異事前登録 (spec sha256 = `b565e8b9de9548be5656ca0afd2f6e2924fa0ce386f9472b248cb3450a75e658`) |
| `mutation-ledger.json` | 変異本走の台帳 |

## 差し戻した fix

fix 第 3 巡は、campaign ループへ「呼び先の signature を検査し、認可引数を受け取らない相手には
その引数を落として呼ぶ」互換分岐を入れていた。注入された評価関数を無認可で呼べるようにする
fail-open であり、採用せず差し戻した。`s6-fix3.md` はその逐語を含む。
