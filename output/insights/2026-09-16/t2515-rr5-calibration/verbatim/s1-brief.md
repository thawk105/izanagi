# [T-2515] 段 1 brief — write-heavy (rr5) の accepted 認定較正を取得する

wave branch `worktree-dev-wave-t2515-rr5-accepted-calibration` / 起点 main `262c2993e`。

## 研究前進

`docs/phase3.md` §8b「workload 次元のループ入力化」は、read/write 比率を型付き descriptor として
ループ入力にすることを次の主経路に置いている。その前提である t48 / pegasus の accepted 較正は
rr50 と rr95 が揃い、**write-heavy (rr5) だけが 1 件も無い**。T-2534 が 2026-09-13 に silo/rr5 を
投入したが `cache_floor_warning` 起因の `selection-invalid` で棄却され、迂回せず裁定へ返している。
その裁定 (D1986 項 1) の実装 = D2026 が 2026-09-15 に main へ着地したので、順序待ちは解けた。

**完了判定:** `output/env/pegasus/calibration/registered/` に silo/rr5 の record が 1 件増え、
その `quality.status` が `accepted`、`cache_floor_warning` が false であること。
`docs/phase3.md` §8b の T-2515 行が「accepted 取得済み」へ変わること。

## 確定済みユーザー裁定

- **D1986 項 1** — 選択規則へ取りこぼし率下限を足す。条件 3 つ = workload 非依存、走らせ直す前に
  規則を登録、**今回の rr5 の却下記録は却下のまま残し緑へ読み替えない**。下限 0.50% は動かさない。
- **D2026** — その登録そのもの。`632754bbc` が main の祖先であることを実測済み。
  同決定は「較正を走らせ直すのは本決定が main へ着地した後に限る」と書いている。
- **D1641 決定 2** — 測定は認可済みで操作は AI 委任。ユーザー裁定を待たずに走らせてよい。
- **D15** — 較正は (env, thread, 代表 workload) でキーする。下限基準は maxrss ≥ 4×L3 の最小 N。

## 不変条件 (緩めない)

1. **迂回して accepted を作らない。** accepted は `orchestrator/calibrate.py --certify` が計算ノード上で
   判定・publish した結果だけを指す。親が JSON を書いて registered へ置くことはしない。
2. **選択規則・`cache_floor` (0.50%)・`l3_multiple` (4.0)・飽和閾値・結果 schema を触らない。**
   1 行でも触れたら規律 2 違反であり、この wave の目的そのものが失われる。
3. **2026-09-14 の却下記録 (`attempts/0_995806.nqsv`) は却下のまま残す。** 再解析も上書きもしない。
4. 却下が再発したら、通すための修正をせず、実測値を添えて裁定へ返す。
5. 走行中に書き換えてよいのは `output/` 配下だけ (投入時点の作業ツリーが source identity)。

## scope

- **入る:** silo / rr5 の認定較正を 1 本投入し、accepted なら登録する。third-party staging の hydrate。
  記録 (worklog / insights / phase3 の該当行 / spool fragment)。
- **入らない:** mocc/rr5・tictoc/rr5 (T-2224 が「本題の必要条件でない」として明示的に外した)。
  選択規則や品質判定の改修。within-run floor の本走。branch `...calib-rr95-rr5` の逐語回収 (下記 P1)。
  仮想リスク向けの gate・検査・台帳の追加。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 依頼の前提「未着地 6 commit を回収する」は、すでに main で完了している。** 内容で照合した:
  `35a740cd4` が 5 commit の必要差分を合成済み、2026-09-15 の別 wave が残る 17 file を byte 一致で
  回収済み (`output/insights/2026-09-10/t2515-rr95-rr5-calibration/`)、`559bcbc29` の conftest 部分は
  T-2579 が実装済みで `test_t1259_*.py` は blob 同一。さらに `3dbf7ea1d` の関門 argv 修正は
  D1936 項 6 が `run_condition_gate` ごと撤去したため**対象が消滅している**。
  → **回収作業は行わない。** 依頼者へは実測で報告する。
- **(P2) 再走で accepted になる見込みは高い。** 却下試行の実測系列へ現行 `find_saturation` を
  適用した probe は records=2,000,000 / miss 1.392% / `cache_floor_warning=False` を返した。
  `selection-invalid` を立てていたのは `cache_floor_warning` だけで、他の却下理由は当時 0 件、
  within-run CV = 0.0135 (上限 0.05)。ただし**これは予測であって保証ではない**。新しい run は
  新しい測定であり、accepted になるまで accepted と書かない。
- **(P3) この wave に実装面 (D95 決定 2) の差分は無い見込み。** 変えるのは docs と `output/` 配下の
  成果物だけ。実装面が必要と判明した時点で Codex `role=author` の実装子へ回す。

## 成果物

1. `output/env/pegasus/calibration/registered/calibration-<sha16>.json` (job が publish)
2. `output/env/pegasus/calibration/attempts/0_<id>.nqsv/` 一式 (job が書く)
3. `output/insights/2026-09-16/t2515-rr5-calibration/README.md` — 投入条件、測定値、選択根拠、
   却下試行との差分、限界
4. `docs/phase3.md` §8b の T-2515 行の更新、spool fragment (worklog / decisions は必要時のみ)

## 分割方針

段 2 plan 1 本、段 3 敵対相談 2 本 (レンズ A = 規律 2 と honesty、レンズ B = 運用と失効前提)。
実装面が無ければ段 5・6 の実装子は立てず、測定・記録は親が担う。
