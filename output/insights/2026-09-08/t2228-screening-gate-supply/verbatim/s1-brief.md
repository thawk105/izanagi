# 段 1 brief — [T-2228] screening 関門への FetchContent base 供給

## scope (これだけ)

`orchestrator/campaign/screening_driver.py` の `_run_condition_gate_for_genome` が
`condition_meaning_gate.capture_define_inputs` を呼ぶときの `configure_args` に、
D1666 が driver 段へ入れたのと同型の **準備済み FetchContent base の供給**を入れる。
供給の作り方は `buildcache.prepare_masstree_fetchcontent` を関門文脈で 1 度呼び、
同じ base を `-DFETCHCONTENT_BASE_DIR=<canonical base>` として関門へ渡し、関門の直後に閉じる
(`orchestrator/campaign/backoff_sweep.py:365-392` と同型)。

## 確定済みユーザー裁定 (D1733)

- 供給を入れるのは screening 関門 1 箇所だけ。
- **`backoff_repro` と `s1_direct_comparison` には入れない。**
- **pin の整合と freeze の再生成は行わない。**
- この 2 つへ広げないことが裁定の本体である。赤が見えても広げず、再訪条件
  (現行の正規入口から関門へ到達したことの実測) の話として記録に留める。
- 本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。

## 不変条件 (規律 2 を緩めない)

1. 関門の**判定式・受理集合・既定値・stock 比較・meaning 腕は 1 つも変えない。**
   変えるのは関門へ渡す configure 入力だけである。
2. `config.h` が無ければ preprocess を skip する形は D1666 が既に却下済み。採らない。
3. 検査する木と build する木は同じ patched source 木にする
   (prepare の `ccbench_dir` は関門へ渡す `source_root` と同一の canonical path)。
4. 関門が見た masstree `config.h` と計測 build が使う `config.h` の bytes 同一性は
   **束縛しない** (D1666 と同じ限界。閉包 hash の束縛は新規 gate に当たり scope 外)。
5. 供給を足しても、関門が赤を出す入力は赤のままである (正例と負例の両方を要求する)。

## 実測で確かめた前提 (親が本 wave で確認)

- 現行 `_run_condition_gate_for_genome` (`screening_driver.py:168-207`) は
  `configure_args=_condition_gate_base_configure_args(genome)` だけを渡し、
  `-DFETCHCONTENT_BASE_DIR` を 1 つも含まない。一次資料 §1.2 の赤の原因と一致する。
- `backoff_sweep.run_workload` の driver 段の一時 base は
  `if screening_enabled:` の**前に閉じる**ので、screening 関門は driver 段の base を再利用できない。
- `evaluate_candidate` の呼び手は 4 箇所ある —
  `backoff_sweep.py:258` と `:297`、`s6_sort_sweep.py:421`、`s8a_trigger_sweep.py:523`。
  **`expected_toolchain_manifest` を渡すのは backoff_sweep の 2 箇所だけ**で、
  `s6_sort_sweep` と `s8a_trigger_sweep` は渡さない (= `None`)。
- `prepare_masstree_fetchcontent` は `expected_toolchain_manifest` を必須 keyword に取る
  (`buildcache.py:2009-2017`)。
- 関門へ渡す `source_root` は `source_digest.resolve_evidence` の
  `os.path.realpath(os.path.abspath(sub))` (`source_digest.py:2345`) で、patched CCBench root である。
- prepare の所要は計算ノードで 20 秒程度 (D1666 の実測)。関門は genome ごとに走る。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1) 関門は共有関数なので、編集は `s6_sort_sweep` と `s8a_trigger_sweep` の経路にも届く。**
  D1733 は関門を関数名で名指ししており、この 2 経路には言及がない。
  親の provisional 裁定: **供給は `expected_toolchain_manifest` が実在する経路にだけ効かせ、
  `None` の経路は現行挙動 (供給なし) を 1 bit も変えない。**
  理由は DW-G04 — 供給が実測で必要と示されたのは backoff_sweep の screening 経路だけであり、
  未測の 2 経路へ発火させない。攻撃点: この条件は候補集合に含意されて恒真になっていないか
  (今日 manifest を渡すのは backoff_sweep だけなので、条件が経路名の代理になっている)。
- **(P2) prepare を呼ぶ回数と場所。** provisional 裁定: 関門 1 回につき一時 base を 1 つ作り、
  関門の直後に閉じる (D1666 と同型)。攻撃点: genome ごとに 20 秒が積むこと、
  および `_require_condition_gate_before_evaluation` の stock checkout との入れ子順序。
- **(P3) prepare の `site` 引数。** provisional 裁定: driver 段と同じ解決を使う。
  攻撃点: `evaluate_candidate` には site が引数として無く、`buildcache` の既定解決に頼ること。
- **(P4) prepare の失敗は関門の赤にしない。** provisional 裁定: prepare が落ちたら
  例外をそのまま上げて評価を止める (偽の緑を作らない)。攻撃点: 現行の abort 分類との整合。

## 成果物の形

- `orchestrator/campaign/screening_driver.py` の関門経路の変更。
- `orchestrator/tests/test_screening_driver.py` (および必要なら関連 test) の追加検査。
  最低限: 供給 argv の exact 形、prepare が 1 度だけ呼ばれること、
  prepare / 関門 / 後続 build の root 一致、`None` 経路の非発火、赤入力が赤のままである負例。
- worklog / insight / decisions への記録は親が行う。

## pin 閉包 (DW-O09) の一次走査結果

- `orchestrator/tests/test_official_perf_closure.py` が `screening_driver.py` を
  predicate 台帳に持つ (74, 132-136, 370, 625, 872 行)。追跡している callee 名は
  `probe_perf_availability` / `use_perf_from_receipt` / `evaluate` の perf 系だけである。
- `orchestrator/tests/test_ccbench_spawn_sites.py` は (file, function) 単位の spawn 台帳だが、
  `backoff_sweep.py` も `screening_driver.py` も未登録である
  (`prepare_masstree_fetchcontent` の subprocess は `buildcache` 内で起きるため)。
- D1666 の実装 commit `0ade09d5e` が触った test は 6 file で、
  spawn 台帳・perf 閉包台帳のどちらも含まない。
- **したがって親の暫定判断は「本変更は既存 pin 台帳の再登録を要さない」だが、
  これは段 2 で file:line で裏取りし、段 6 で焦点走により実測する。**

## 分割方針

軽量版ではなく段 2・3・6 の子を立てる。理由は DW-C00 —
本変更は正しさ防壁 (条件関門) の入力に触り、(P1) で設計択一が割れているためである。
段 5 の実装子は 1 本 (編集面が 1 関数 + その test に閉じるため)。
