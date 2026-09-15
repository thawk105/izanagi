# 段 4 裁定 — [T-2505][T-2519][T-2607] t316 の条件関門と build 木の一致回復

wave: `t2607-t316-gate-tree` / base: `0600887d92538b3f34d894f9674d202d0a29a578`
入力: `s1-brief.md`、`s2-plan-out.md`、`s3-lensA-out.md`、`s3-lensB-out.md`
段 4 直前に裁定 inbox を再走査した。wave 開始後に local main は 1 commit も進んでいない。

## 1. 択一の裁定 — 案 B を採る。案 A は不採用。

**案 A (patch 由来 define を渡すのをやめ、条件関門ごと落とす) は不採用とする。**

根拠は実測ではなく既裁定である。

- **D1625 (ユーザー裁定)** は t316 の条件関門について「許可するのは … **どちらか 1 つに exact 一致**
  することだけであり」「**それ以外の緩和はしない**」と定め、却下欄で
  「**probe の exact 一致検査を外す — 受理集合を gate の表より広げる**」を明示的に却下している。
  親 brief が案 A で許容した `_condition_gate_family_valid` の撤去は、この exact pair 検査そのものである。
  別物だという主張はコード上成り立たない (`P:381-384` が reason/comparison の exact pair を見ている)。
- `verdict_s6` の拒否枝 4 本 (family 欠落 / evaluator 未発行 record / 受領証不一致 / 非 inert pair) は
  inert 要求の有無と**独立した**現行契約である。define を消しても、この 4 本を外さなければ S6 は go にならない。

**したがって「どれを採るかを実測で決める」というユーザー指示は、その前提が成立しない。**
案 A の不成立は経験的事実ではなく契約上の帰結であり、どんな測定値が出ても変わらない。
段 2 と段 3 の 2 レンズが独立に同じ結論へ達している。**実測は択一の決定ではなく、採った案が
目的状態へ到達するかの確認へ回す** (第 4 節)。この順序変更は本裁定の明示的な判断である。

なお段 2 が案 A 不成立の根拠に挙げたもののうち、「既存テストの契約は一切変更不可」という読みは
レンズ A が過剰解釈と判定した。親はこれを受け入れる。**ただし D1625 が独立に案 A を閉じるため、
結論は変わらない。**

**案 B (patch を materialize した使い捨て木を、関門と build の両方で使う) を採る。**

- `patchharness` の docstring (`H:24-27`) が `with checkout(pin) as sub: with applied(patch, pin, sub):`
  を逐語で正規形として定めている。契約違反ではない。
- `paper_story_a2_certification.py:693-712` が完全な先例である。使い捨て木へ patch を当て、
  **素の source_root を stock control** にし、同じ木を関門へ渡している。
- 2026-09-07 の一次資料 (`output/insights/2026-09-07_t2228-driver-gate-liveness/README.md`) が、
  A-2 と `backoff_sweep` driver 段の 2 例で `stock-inert-preprocess-root-location-only` の
  supply 緑を記録している。

## 2. 未使用変数の除去も同時に行う — 案 B だけでは閉じない

D1994 は赤の原因を 2 つ挙げ「どちらも単独で赤にする」と書いている。案 B は原因 1 だけを解く。
原因 2 (CCBench が参照しない 3 変数) は patch を当てても残り、**両アームで**未使用変数警告を出す。
F855 の恒久対応「driver から未使用変数を除去」が t316 へ未適用だったという前 wave の記録どおりである。

親が実測した結果、共有 configure list の `-D` のうち CCBench (patch 適用後) が参照しないのは
次の 3 件だけである。他の `CCBENCH_*` と `ENABLE_SANITIZER` は素の木の CMake に実在する。

- `-DRULE_LAUNCH_COMPILE=` (実効の ccache 抑止は `CMAKE_C/CXX_COMPILER_LAUNCHER=` 側)
- `-DIZANAGI_GFLAGS_SRC_HEAD=<pin>`
- `-DIZANAGI_GLOG_SRC_HEAD=<pin>`

**3 件は関門へ渡す引数からだけでなく、共有 configure list そのものから除く。**
関門だけから除くと「検査する木と build する木を一致させる」不変条件を再び破る。
pin の provenance は `observe_s6` が `source_heads` / `source_identities` で別途記録しており失われない。

## 3. 所見の裁定

| # | 所見 | 判定 | 扱い |
|---|---|---|---|
| A1 | 案 A は D1625 と衝突 | **real** | 採用。案 A 不採用の根拠 (第 1 節) |
| A2 | 案 B は D1994/D1864/D1849 を復活させない | refuted | 記録のみ |
| A3 | 案 B 自体の恒真化は無い。ただし control のコピー元は危険箇所 | 半 real | 採用。**control は素の submodule を直接使う** (第 5 節) |
| A4 | 案 B の緑は永続 cache の残留生成物に依存する | **real** | 採用 (**記録の限定として**)。実装での予防は scope 外 (第 6 節) |
| A5 | 既存テストだけでは新配線の検出力が無い | **real** | 採用。配線検査を実装 scope に入れる (第 5 節) |
| A6 | 変異の帰属 (mask と到達不能) | **real** | 採用。事前登録へ反映 (第 7 節) |
| A7 | P1-1 の「義務消滅」は未証明 | real | 案 A 不採用により moot。記録のみ |
| A8 | P1-2 / P1-3 / 実在確認の一般化制限 | **real** | 採用。insight で範囲を限定して書く |
| A9 | 段 2 の「契約変更全面禁止」は過剰解釈 | real | 採用。第 1 節に明記済み |
| B1 | config.h 欠落層は (報告した cache では) 出ない | refuted | 記録のみ。A4 と対で範囲を限定 |
| B2 | root path 差の層は既に許可済み pair で通る | refuted | 記録のみ |
| B3 | sandbox 内 Git 書込みで破れる | refuted | 採用条件: **checkout / patch / revert は host 側**。requested は scratch 外へ置き read-only mount |
| B4 | `checkout → applied` は harness の逐語契約内 | refuted | 記録のみ |
| B5 | 並行 worktree add の競合 | refuted (nit) | 新規 lock は足さない |
| B6 | outside-control 短絡で cleanup が飛ぶ | refuted | 採用条件: 両 build を同じ context で包む |
| B7 | identity の再生産 | refuted (実装条件付き) | 採用。第 5 節の identity 仕様 |
| B8 | 時間予算が収まる根拠がない | **real** | 採用。確認走で内訳を取る (第 4 節) |
| B9 | login driver は install prefix が無くて成立しない | **real** | 採用。login driver を採らない (第 4 節) |
| B10 | `tools/run_tests.py` は pytest runner で build 入口ではない | **real** | 採用。同上 |
| B11 | 実測だけで択一できるという前提は成立しない | **real** | 採用。第 1 節に明記済み |
| B12 | 親の一般化 (先例・P1-2・P1-3・実在確認) | **real** | 採用。insight で範囲を限定して書く |

## 4. 実測の裁定 — 使い捨て login driver は作らない。確認は t316 の実経路で行う。

段 2 が設計した 90 行の login driver は**作らない。** 根拠は次の 3 つで、いずれも実測である。

- gflags / glog は source しか無く install prefix が存在しない (親が実測)。CCBench の
  `CMakeLists.txt:33-34` は両者を `find_package(... REQUIRED)` する。driver は依存 build から始まる。
- `tools/run_tests.py` は pytest を組み立てる runner であって任意 build の入口ではない (B10)。
  段 2 が置いた「runner 経由で build する」という空白は埋まらない。
- pegasus02 の load average は実測 180.74 / 192.03 / 183.33。ここで依存 build を回すのは
  遅いうえ共有ノードへの外乱になる。

**代わりに、実装後に t316 の実経路を計算ノードで 1 走させて確認する。**
確認する項目は次の 4 点で、いずれもこの経路でしか観測できない。

1. supply 腕が緑になり、発火した (reason_code, comparison) の組が
   `_INERT_CONDITION_GATE_PAIRS` のどちらかに exact 一致すること。
2. inside / outside の両 build が成功し `trace_disabled` が真であること。
3. S6 が `walltime` で blocked にならないこと (B8)。stage budget は実測で
   `probe_deadline_s=5100` / `s6_minimum_remaining_s=3600` / `ccbench_build_cap_s=1200` (片側)。
4. 受領証の `condition_gates` が従来 schema のまま記録されること。

投入 argv は前 wave の逐語と同形とする。

## 5. plan v2 — 実装仕様

`P` = `tools/pegasus/probes/t316_sandbox_backend_probe.py`、`T` = `orchestrator/tests/test_t316_sandbox_probe.py`。

1. **`observe_s6` (P:1989-2064)**
   - 既存の pin 照合と `_git_source_identity` 群を**そのまま維持**する。
   - 合格後、host 側で `patchharness.checkout(expected_ccbench_head, base_dir=<repo_root/external/ccbench>)`
     により使い捨て木 `requested_root` を作る。
   - `requested_root` に対し **patch を当てる前に** `_git_source_identity(requested_root, expected_ccbench_head)`
     を実行し、結果を `source_identities` の新 entry (例 `ccbench_requested_base`) として記録する。
     valid でなければ `failure_stage="source-identity"` で返す。
   - `patchharness.applied(<patches/silo-backoff-fixed.patch の絶対 path>, expected_ccbench_head,
     ccbench_dir=<requested_root>)` の内側で outside / inside の両 build を行う。
     **短絡経路でも context を抜けるようにし、`applied` の適用は 1 回だけにする。**
   - **patch 後の木に identity 検査を掛けない。** clean にならないので、掛ければ必ず赤になる。
     `source_identity_valid` は基底検査の結果であり、無条件代入をしない。

2. **`_execute_ccbench_build` (P:1825-1930)**
   - build 対象 `source` は `requested_root` (patch 済み) を受ける。
   - **`shutil.copytree(source, stock_copy)` を廃止する。** control は素の submodule を直接使う。
     新しい引数で受け取り、`capture_define_inputs` の `stock_root` へ渡す。
     (`capture_define_inputs` は source != stock を要求する。使い捨て木と submodule は別 path。)
   - 共有 `configure` list から次の 3 件を**除去**する。
     `-DRULE_LAUNCH_COMPILE=` / `-DIZANAGI_GFLAGS_SRC_HEAD=...` / `-DIZANAGI_GLOG_SRC_HEAD=...`
   - `-DCCBENCH_BACKOFF_FIXED=-1` は**維持**する。patch 済み木が供給するので未使用にならない。
   - 他の `-D` は変えない。実装子は残る全 `-D` について、patch 適用後の CCBench が参照することを
     確認して報告すること (親は `ENABLE_SANITIZER` と `CCBENCH_*` 7 件の実在を確認済み)。

3. **`_require_condition_gate` (P:1932-1986)**
   - `source` = `requested_root`、`stock_root` = 素の submodule。
   - `configure_args` から `-DCCBENCH_BACKOFF_FIXED=-1` を除く現行ロジックは維持する。
   - 拒否時の stderr 診断 (D1995) と例外は変えない。

4. **`_BOUND_RELATIVE_PATHS` (P:2303-2309)**
   - `patches/silo-backoff-fixed.patch` と `orchestrator/campaign/patchharness.py` を足す。
     新しい実行入力になるため。`.pbs` 側の束縛一覧も同じ commit で揃える。

5. **sandbox の read-only mount**
   - `requested_root` は scratch の外に置き、S6 profile の readonly roots へ追加する。
     scratch 内に置くと writable bind が後勝ちで source が書込可能になる (B3)。

6. **受領証と schema**
   - `SCHEMA_VERSION`、`condition_gates` の形、`_condition_gate_receipt_summary` は**変えない** (D1849)。
   - `source_identities` への entry 追加は識別子の記録であり schema 版を上げない。

7. **追加する配線検査 (T)** — A5 と B-M4〜M6 の穴を埋める。既存 test の期待値は 1 つも変えない。
   - 関門へ渡した requested root と、両 build の `-S` が**同一 path**であること。
   - control が patch 前の素の submodule であること (patch 済み木のコピーでないこと)。
   - `applied` が両 build を包み、patch 適用が 1 回だけであること。
   - requested の**patch 前**基底 identity 検査が wrong HEAD と dirty を拒否すること。
   - 共有 configure list に CCBench 未参照変数が含まれないこと。
     **性質での検査にせず、除去した 3 変数名を実体として名指しする。**

## 6. scope 外 (実装しない)

- `condition_meaning_gate.py` の変更。stderr 規則・`_INERT_CONDITION_GATE_PAIRS`・受理集合はそのまま。
- `buildcache.prepare_masstree_fetchcontent` の t316 への導入。A-2 と `backoff_sweep` の
  2 つの緑はどちらも準備済み base を使っており、t316 は永続 cache を直指しする (A4)。
  **しかしこれは「cache が掃除されたら赤に戻る」という仮想リスクであり、本題の修正ではない。**
  ユーザー指示の「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」に従い実装しない。
  **代わりに insight へ「この cache 状態に限る」と範囲を明記する。**
- 関門呼び出しへの `deadline_ns` 伝播 (既存挙動。B8 は確認走で見る)。
- 並行 worktree add 用の新しい lock (B5、nit)。
- 案 A の実装。

## 7. 変異事前登録 (DW-M01)

実装前に登録する。harness は `tools/mutation_harness.py`。期待 node は完全集合とする。
**既存 test が KILL するもの**と、**本 wave の新規配線検査が KILL するもの**を分けて登録する。

| ID | 変異位置 | 受理集合への影響 | 期待 KILL |
|---|---|---|---|
| M1 | `_require_condition_gate` の admission 拒否を無効化 | 赤 family でも正常終了 | 既存: 拒否 helper の stderr/例外検査 |
| M2 | `_condition_gate_family_valid` の inert pair 判定を恒真化 | 非 inert の admitted family を go | 既存: requested/default 差の拒否検査 |
| M3 | reason / comparison の交差組を許容 | 契約違反の組を go | 既存: 交差組拒否検査 (monkeypatch で前段 gate から隔離済み) |
| M4 | 関門へ渡す root だけを requested 木にし、build は素の木へ戻す | build と無関係な関門証拠で go | **新規: root 同一性検査** |
| M5 | control のコピー元を patch 済み requested 木へ変える | patch 既定枝の変更を両側で共有 | **新規: control 出所検査** |
| M6 | requested の patch 前基底 identity 検査を無条件真にする | wrong HEAD / dirty 基底を受理 | **新規: 基底 identity 検査** |
| M7 | 除去した 3 変数のうち 1 件を共有 configure list へ戻す | 未使用変数警告で関門が再び赤 | **新規: 未参照変数不在の検査** |

帰属の注意 (A6)。
- M1 は `verdict_s6` だけを見る test では前段の再拒否に隠れる。helper を直接呼ぶ検査を期待 node にする。
- legacy vocabulary の test は family 作成中に gate が拒否して `verdict_s6` に到達しないので、
  **どの変異の KILL 証拠にも数えない。**
- 各変異は実装後に単一理由性を確認する。前後・内側の層が同じ入力を先に拒否するなら登録し直す。

## 8. 不変条件 (実装子への拘束)

1. 検査する木と build する木は同一であること。
2. `condition_meaning_gate` を変更しない。stderr 規則と exact pair の表を緩めない。
3. 既存テストの期待値を反転・緩和・skip・削除しない。赤なら実装側が誤りとする。
   期待値が誤りだと判断したら実装を変えず報告して止める。
4. `SCHEMA_VERSION` と受領証の形を変えない (D1849)。
5. `CCBENCH_TRACE=0` の trace-disabled 検査と既存の source identity 検査を維持する。
6. D1995 の「拒否理由を job stderr へ出す」挙動を維持する。
7. 仮想リスク向けの gate・検査・台帳・一般化を足さない。
