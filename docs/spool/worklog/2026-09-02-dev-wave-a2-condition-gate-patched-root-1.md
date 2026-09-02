---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-a2-condition-gate-patched-root
seq: 1
title: A-2 が関門で止まっていたのは patch 未適用の木を渡していたからで、直すと隠れていた関門があと 2 層出た (コード + docs + insight、branch worktree-dev-wave-a2-condition-gate-patched-root、変異 5/5 KILLED)
---

## 本文

- ユーザー依頼は「A-2 の実走が `condition_meaning_gate` に阻まれる原因を確定して直す。受理集合は
  広げない」。原因は確定し、拒否理由 4 件のうち赤 3 件を消した。残り 1 件は関門本体の性質のため
  裁定へ返した。
- **引数が既定としていた修正方針を、実測で覆して段 4 で再裁定した。** 既定は「patch 由来の
  cache 変数を、定義しない木へ渡さない」だったが、その向きでは inert supply arm が自明に緑になり
  D1198 が禁じた形になる。正しい向きは逆で、関門へ patch 済みの木を渡すことだった。
  なお敵対相談の指摘により、親が最初に書いた「その案では関門全体が恒真」は過大な一般化と判明した
  (恒真になるのは inert arm だけで、adopted arm と meaning arm は赤のまま残る)。却下の結論は
  変えず、理由を訂正した。
- **段 2 プランは revert 位置を誤っていた。** 関門だけを patch 文脈へ入れ、`run_campaign` の前に
  revert する形を「利点」として書いていた。それでは関門が検査する木と campaign が build する木が
  別になる。段 4 で親が覆し、patch 文脈が `run_campaign` と raw payload 書き出しまでを含む形にした。
- **敵対相談 (実効性レンズ) が実在の障害を 1 件出した。** A-2 は rr5 / rr50 の 2 job が同じ
  CCBench root を共有して別ノードで走るため、共有木を書き換える設計は採れない。
  `patchharness._tree_lock` はノード局所の flock で、ノードを跨いで排他にならない。
  同レンズの他 2 件 (patch が pin へ当たらない懸念、`/tmp` 容量) は親の実測で否定した
  (`git apply --check` rc=0、CCBench checkout は 15MB)。
- 敵対相談 (正しさレンズ) が挙げた「adopted 値が 1000 以上なら meaning が赤」は、A-2 の adopted が
  10 と 5 なので該当せず refuted。
- 実装子が新しく足した件数 pin (`source.count(...) == N`) の較正を 2 度続けて誤った。親が
  `inspect` で実測して正しい値を確定し、さらに「増えた 1 箇所が関門呼び出しの中にある」ことを
  縛る assertion を足させて、件数だけの弱い pin に退化させなかった。
- 計算ノードへ 2 回投入した (attempt `a2gate-20260902a` / `a2gate-20260902b`)。いずれも
  Elapse 32 秒、`driver_rc=2`。1 回目で `configure-failed` と `materialized-branch-invalid` の
  消滅を確認し、2 回目で masstree `config.h` 不在の消滅と `BACKOFF_FIXED` の runtime-meaning が
  緑になったことを確認した。**4 cell の緑は未達**で、理由は下の裁定待ち。
- 拒否メッセージが `evidence.detail` を保持するようになった。これが無ければ 2 層目・3 層目の
  切り分けに毎回 login node での再現が要る。実際、1 回目の投入で初めてノード側の実 stderr が読めた。
- 変異は事前登録 5 件すべて KILLED。probe (全件 SURVIVED 期待) で観測 node を集めてから本走した。
  `M4-REJECTION-DETAIL-DROPPED` は受理集合を変えず診断だけを pin する変異である。
- 詳細と裁定パッケージは `output/insights/2026-09-02_a2-condition-gate-patched-root/`。
- 段 8 の自己改善候補は 2 件出たが、いずれも入口・reference を編集せず記録に留めた。
  (a) 実装子が新設する件数 pin の較正ミスは、既存の `DW-S05-C` (期待値へ揮発値を焼き込まない、
  理由と件数を固定する) の射程で読める。(b) 「login node が `require_heavy_work_site` で拒否する
  機構は probe を login で回さず最初から dispatch する」はマシン固有の事実なので、横断 docs では
  なく Pegasus runbook 側の話題である。どちらも 3 層の byte 予算を消費して増やす価値が現時点では
  無いと判断した。

## 次の一手差分

### 新規

- {{T:a2-inert-root-path}} **P1・ユーザー裁定待ち**: A-2 の inert (stock) 比較が
  `preprocess-root-dependent-builtin` で必ず赤になる。`capture_define_inputs` は stock root と
  source root が別 path であることを要求し、CCBench の `include/debug.hh` が `__FILE__` を使うため、
  guard が構造的に常時発火する。関門側で root path を正規化してから bytes を比較する案
  (親の推奨) を含め 4 案を裁定パッケージに出した。受理集合に触るので実装していない。

- {{T:a2-noinline-meaning}} **P2・ユーザー裁定待ち**: `BACKOFF_NOINLINE` の runtime-meaning が
  常に `unestablished` のまま `paper` に受理される。`MEANING_SUPPORTED_MACROS` が
  `BACKOFF_FIXED` だけで、driver も witness declaration を作らない。厳格化は受理集合を
  **狭める**変更なので独断で入れていない。

- {{T:condition-gate-driver-sweep}} **P2・新規**: 関門は T-1999 / D1198 で driver 全体へ
  義務化されたが、A-2 経路では 1 層目で落ちていたため 2 層目以降が一度も実行されていなかった。
  `backoff_sweep` / `backoff_repro` / `s1_direct_comparison` の inert 経路も同じ未実行の可能性が
  ある。実際に通るかを driver ごとに実測する。
