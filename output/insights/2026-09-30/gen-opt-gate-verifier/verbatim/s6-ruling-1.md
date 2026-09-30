# 段 6 裁定 1 — レビュー A・B の所見 (統合 commit 2a05bf81a + U1 snapshot `u1-snap1/`)

- 入力: `review-a.md`・`review-b.md` (受理 rc=0)、親の焦点走 `focus-u2-1.log` (189 passed)。snapshot: U2 = `u2-a1.patch` (sha256 28c639ff…)、U1 = `u1-snap1/` (`u1-snap1.sha256`)。

| 所見 | 裁定 | 処置 |
|---|---|---|
| 親 (既知) D5 の emitter 名 | real must-fix | 判定器の `GATE_EMITTER_CALLS` の受け渡し関数名を U1 の実物 `izanagi_trace::set_gate_txid(` に揃える。U1 と同じ名前の最小 source で D5 の正例 test を置く |
| A-R1 D2a が同じ key の 2 度目以降の外部読みを照合しない | real must-fix | その key への自分の書きより前の R/M の読みは、何度目でも R 行が指す版の刻印 (genesis は key 整数) と照合する。2 度目だけ誤る fixture を足す |
| A-R2 / B-B3 起動器が report の key 名と合わない | real must-fix | 起動器 v3 の読み取りを production の投影 (`report.py` の `gate_witness` 節の実 key) に合わせる。2a05bf81a の report が出す JSON の実例 (fixture から作る) で prereg 評価関数を自己確認 |
| A-R3 ycsb.hh 冒頭の `#line 17` | real must-fix (親が F の hunk で検算: F は 16 行目が空行、17 行目が gflags include。他の `#line` 108/109/127/132/142/166 は正しい) | `#line 16` に直す |
| A-R4 / B-B5 発生条件の gate を全条件に掛けている | real should | 条件別にする: X は発生条件 2 つが各 ≥1 を要し、B は B1 committed ≥1、S は D2b 合計 ≥1、N は記述のみ (計数を報告) |
| A-R5 M9・M10 の kill が KeyError 頼み | real should | 判定器の V と UPDATE の W の対応・thread 集合の照合を、それぞれ 1 か所の明示検査で構造化した到達不能にする (KeyError に頼らない)。変異 M9・M10 はその 1 か所を外す形で単一理由になるようにする |
| B-B1 D1(b2) の包含の向き | **refuted** | `("d1b2", q_read, reads.keys())` と `failed = not set(observed).issubset(expected)` は `reads ⊆ q_read` を検査しており設計どおり (b1 は `first_read ⊆ reads`)。ただし B8 の読みやすさの所見は採る |
| B-B4 未了の負例・CLI rc・変異 | real (一部) | 足す: B5 型 (後の読み手の刻印と V の食い違い) の fixture、要求時の gate 一部欠落・読取不能の CLI rc。N2 は判定器 fixture の水準では N1 と同じ履歴になる (方策は待機の長さしか変えない) ので fixture を作らず、[T-2889] の実走に回す。M3 の fixture が赤理由どおり働くことは B1 が refuted なので現状どおり。変異の本走は親が harness で行う |
| B-B6 Q の thid 不一致を到達不能に分類 | real should | 書式として読めた Q の thid が file の thid と違う場合は D1(c) として数える |
| B-B7 計算ノードの実走が未了 | real (予定どおり) | 親が fix 後に投入する |
| B-B8 `_check_gate` の詰め込み | real nit → 採用 (局所) | 到達可能性の読み込み、D1、D2 の照合を小さい関数に分け、各集合の包含の向きを名前で示す。挙動は変えない |

fix は所有で 2 本に分ける (素集合): fix-u1 = t2884-u1 の scratch (ycsb.hh の `#line`、起動器 v3)、fix-u2 = t2884-u2 の判定器 5 file と `test_verifier_gate_witness.py`。規模の上限: fix-u2 は production の差分 ±300 行・test 追加 250 行、fix-u1 は ±120 行。
