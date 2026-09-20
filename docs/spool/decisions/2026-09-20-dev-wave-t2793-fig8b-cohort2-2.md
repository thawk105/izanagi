---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2793-fig8b-cohort2
seq: 2
---

## {{D:fig8b-reproduction-column-two-blocks}}. B-10 右 tail の再現欄付き後継図 fig8b は主結果と独立再現を縦 2 block で併記し、役割と順序を生成器の定数で固定し、cohort をまたぐ統計を provenance に置かない

**決定:** 事前登録 2026-09-19 追記 項 2 (D2157) が求める「fig8 の再現欄」は、凍結 fig8 の bytes を変えず、後継図
`docs/paper-story/figures/fig8b_b10_static_tail_cohort2` として作る。形は次のとおりで、同じ生成器
`tools/plotting/plot_b10_static_tail_formal.py` の `--reproduction-cohort 2` 経路が生む。

- **縦 2 block (4 行 × 3 列)。** 上 block = 主結果 cohort 1 (fig8 と同じ集団報告・同じ pin・同じ計算)、下 block = 独立再現 cohort 2。
  各 block は fig8 と同じ 2 行 (throughput / abort 率)。y 軸は workload-local かつ cohort-local で、同一 panel に 2 cohort を重ねない。
- **役割と順序は定数。** `COHORTS` 表が 1 = primary、2 = reproduction を持ち、CLI は `2` だけを受理し (cohort 2 単独の図は作らない)、
  closure 検査は provenance の位置ごとの (cohort, role) 対を固定 literal と照合する。CLI からも provenance の改変からも主従を入れ替えられない。
- **合成しない。** provenance (schema v2) は `cohorts[]` に cohort ごとの記録を持ち、top-level の key 集合を固定して cohort をまたぐ
  統計 field (プール平均・統合 verdict・差・比・一致度) を構造で持てなくする。`claim_boundary.cohorts_pooled` は `false` で、closure は
  境界辞書の一致とは別にこの値を独立に検査する。
- **言い方。** caption は事前登録 §4.5 の固定表現を各 cohort へ独立に適用し、「2 つの cohort をプールしない・一致度として評価しない」
  「同じ verdict が出たことを固定表現以上に読まない」を明記する。`performance_certified: false` は両 cohort に付ける。
- **v1 経路は不変。** `--reproduction-cohort` を省いた経路の受理集合・射影 (caption / artist / closure v1 / 展開 argv / 図番号の正規表現)
  は byte 同一で、着地済み fig8 の provenance v1 の検査はそのまま通る。図番号の英字 suffix (`fig8b_`) を受理するのは v2 経路だけ。

**理由:**
- 追記 項 2 は「主結果と独立再現を区別して併記」、項 3 は「合成しない」、cohort 2 の稿 §2.6 は「近さを一致度として評価しない」を
  定める。同一 panel の重ね描きは標本の合成ではないが、共有 y 軸で近さの視覚評価を誘い、役割の区別も弱くなる。縦 2 block は
  併記の最も素直な形で、FIGURE_CONVENTIONS §4 (重ね描きは機序目的のときだけ) にも触れない。
- 役割を CLI で選べる設計は、結果後に主従を選ぶ余地 (D2157 が塞いだもの) を図の側で再び開く。定数で閉じる。
- provenance の top-level を固定すると、プール項の混入が「検査で見つける」ではなく「構造で入らない」になる。局所 assertion に留め、
  汎用 validator・gate・台帳へは広げない (依頼の scope 外)。

**却下した選択肢:**
- 2 行 × 3 列に 2 cohort を marker 違いで重ねる — コンパクトだが上の理由で不採用 (段 3 consult の条件付き支持どおり)。
- cohort 2 単独の図 (`--cohort 2`) — 再現欄は主結果と併記する形でしか意味を持たない (追記 項 2)。
- 凍結 fig8 の provenance / bytes を更新して再現欄を足す — 凍結物は上書きしない (figures/README.md 冒頭の規則、絶対規律 7)。
- 「1 ページに入る」を README に書く — 描画寸法 (7.2 × 10.6 in) は実測だが、掲載寸法での可読性は投稿テンプレートでしか確かめられない。
