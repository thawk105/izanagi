---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2620-zombie-residual
seq: 1
title: [T-2620] 残存数計数のゾンビ除外について D2044 項 21 の確認手番 — 実 process の負例 4 種 + receipt 合成負例 1 種で現行と Z 除外 (変異 M1) の receipt・sidecar・checker への映り方を固定し、Z 除外では正常終了のゾンビのみ残存が clean と同値になることを実測した (test のみ、受理集合不変、採否は裁定へ、branch worktree-dev-wave-t2620-zombie-residual)
---

## 本文

- D2044 項 21 と command 引数の範囲で 1 wave。一次資料は `output/insights/2026-09-20/t2620-zombie-residual/README.md` (負例表・Z 除外の観測表・変異台帳・裁定パッケージ)。
  専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2620-zombie-residual/HANDOFF.md`。production は 1 byte も変えず、受理集合も変えていない。
- 段 1 前の生死 probe (login): subreaper 無しでは孫ゾンビは init が回収して残存 0、subreaper (prctl 36) が回収しなければ `Z` が PGID に残り現行計数 1 (F973 の機序)。
  「読取不能」は実 process から作れない (hidepid 無し)。段 3 相談 1 本 (2 レンズ) は must-fix 6 を出し全採用 (forced-stop 経路の N2b 追加、混在 N4 追加、N3 は receipt 合成負例に、harness の順序固定、失敗経路の teardown、観測 dict の 1 回比較)。
- 段 5 Codex author 1 本 (4 分): fake mode 3 つ + subreaper harness + test 5 本。焦点走 (計算ノード) 216 passed / 11.55 s。統合 commit `29a07dbc0`。
  変異 (独立 clone、計算ノード、各 run 32〜38 秒): 新 test 側 M0 等価 SURVIVED / M1 Z 除外 KILLED {N2a, N2b, N4} / M2' normal_reap 化け KILLED {N1, N2a, N4} / M3 checker 束縛削除 KILLED {N3} (期待 node 完全一致)、旧 HEAD `b7f970dfa` 側は 4 変異全 SURVIVED (新 test だけが検出)。
- 段 6 レビュー 2 本は両方 NO-GO (harness が生存子を殺さず外の祖先へ渡す、harness timeout 時に launcher を test が所有しない、共有 helper の signature 変更、rc 97 が観測に届かない、M1 の kill 定義が N2b/N4 で「受理集合の変化」でない) → fix1 (`2758e5eeb`、焦点走 216 passed)。M1 の kill 意味は erratum: N2a = 受理の変化、N2b/N4 = receipt field (residual / termination_verified) の変化。
- fix1 commit の変異本走は **baseline が赤で中止**: 216 test 並列で N2a・N4 の sidecar に `unknown_sources_seen: ["proc_stat_read_error"]` が入った (`final_count` は正しい)。`_group_member_count` の `/proc` 全走査が無関係な process の消滅を読んで一時 `None` → 再 poll で最終値は正しいが sidecar が履歴を保持する。test 側の `[]` 固定が負荷依存 (自分起因) → fix2 (`bf9ca498d`) で「`proc_stat_read_error` 以外を含まない」の真偽値に正規化、`final_count` / `final_unknown_source` の固定は維持。焦点走 216 passed、変異本走を fix2 commit で取り直し (結果は insight §6)、焦点再レビュー 1 本 (結果は insight verbatim)。
  この一時 unknown は現行 launcher の負荷依存の潜在的な偽拒否経路 (期限到達時の走査で `None` → 不受理) でもあり、scope 外として insight §8 に記録のみ (起票は裁定で判断)。
- 結論 (insight §1): 現行は 4 種とも拒否。Z 除外 (M1) では正常終了のゾンビのみ残存 (N2a) が accepted True / launcher_rc 0 になり、receipt にも sidecar にも区別できる field が無い。強制停止後のゾンビ (N2b) は residual 0 / verified True へ変わるが limit で不受理のまま。生存子 (N1)・混在 (N4) は拒否が続く。現行でも receipt は S と Z を識別していない (1 と 1)。
- 限界: 読取不能の e2e 無し、transient ゾンビの受入負荷での挙動未実測、受入負荷での決定性は 1 走の緑だけ、`T`/`D`/`X`/`x`・PID namespace は未再現。
- 工数: codex 7 本 (consult 1、author 1、review 2、fix 2、focus 1)、計算ノード job = 焦点走 3 + 変異 4 走 (baseline 赤で中止 1 を含む、各 ≤ 5 run) + provenance 監査 2 + 受入 1、login で probe 1 と DW-O19 局所走 1。

## 次の一手差分

### 更新

- [T-2620] **P2・ユーザー裁定待ち (Z 除外の採否)**: D2044 項 21 の確認手番は完了。`output/insights/2026-09-20/t2620-zombie-residual/README.md` §7 の (a) 在籍数の契約を維持 / (b) Z だけ除外 (回収不全が receipt から消える、受理集合が広がる) / (c) 非 Z 残存数と Z 数を分けて記録し受理条件への結び方は別裁定。
  実測: Z 除外では正常終了のゾンビのみ残存が clean と同値 (accepted True)、強制停止後は limit で不受理のまま、生存子・混在は拒否が続く。T-2622 (subreaper 再導入の是非) と併せて決めるのが筋。
  base: ab68fb05048a37a4856009e8f1ef08928e739b19071d7f9c3618f98ee5359e54
