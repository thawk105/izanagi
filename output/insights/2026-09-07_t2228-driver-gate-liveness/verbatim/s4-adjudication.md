# 段 4 裁定 — dev-wave-t2228-driver-gate-liveness

親 = Claude Opus 5 / 2026-09-07 JST / 基点 main `d19d2182f` (段 4 直前に再確認、動いていない)

## 0. 親自身の実測による plan の反証 (最上位)

段 2 plan と段 3 の 2 本はいずれも、s1 の freeze に `BACKOFF_FIXED=-1` の cell が
**存在するかどうか**を確かめていない。親が production の凍結入力そのものを読んで確かめた。

`output/s1-freeze/measurement_freeze.json` の 18 cell を、production の
`s1_direct_comparison.schedule_for_role` で develop / floor / block1 / block2 の
4 role すべてについて展開した結果:

| configuration | 関門対象 macro と値 | inert か |
|---|---|---|
| `backoff_fixed_best` | `BACKOFF_FIXED` = 2 / 5 / 10 | 非 inert |
| `system_gate`, `ident_all` | `BACKOFF_TRIGGER_GATING` = 1 (既定 0) | 非 inert |
| `sort_best` | `SORT_VARIANT` = 1 (既定 0) | 非 inert |
| `p2_2_flag_opt`, `stock_common` | 無し | request 0 件 |

**裁定 0-a (real / 採用):** `s1_direct_comparison` は production の凍結入力からは
inert request を一度も構築しない。段 2 plan の s1 runner
(`next(row for row in schedule if flags["BACKOFF_FIXED"] == -1)`) は `StopIteration` になる。
plan の s1 設計を**不採用**とする。

**裁定 0-b (採用):** s1 の測定対象を次の 2 つに置き換える。
1. 到達性の実測 — production の `schedule_for_role` を実際に呼び、18 cell の
   関門対象 macro と値、および inert request が 0 件であることを列挙して記録する。
   これは「無いことの実測」であり、静的な読みの再掲ではない。
2. s1 が実際に走らせる経路の関門 — `write-heavy:backoff_fixed_best`
   (`BACKOFF_FIXED=10`、非 inert) を production の `prepare_cell` へ通す。
   この cell の supply 腕も同じ cmake configure を `configure_args` 無しで走らせるため、
   本 wave の中心仮説 (FetchContent base 未供給) はこの経路で検証できる。
   加えて `p2_2_flag_opt` (関門対象 macro ゼロ) も 1 件通し、record が 0 件で
   関門が発火しないことを実測する。

**裁定 0-c (採用):** 依頼文の「3 driver の inert 経路」に対する s1 の答えは
「production では inert 経路が構築されない (到達不能)」であり、緑でも赤でもない。
insight にはそう書く。緑と書くことも赤と書くことも誤りである。

## 1. 段 3 lens A の所見

| # | 所見 | 判定 | 処置 |
|---|---|---|---|
| A-1 | sweep は模擬でない (`run_workload` が production 本体、`main` は引数解析のみ) | refuted (= 攻撃不成立) | plan どおり `run_workload` を使う |
| A-2 | repro は seam liveness であって production 入口からの到達性ではない | **real** | 採用。成果物の表現を「`_conditioned_backoff_patch()` の liveness」に限定する |
| A-3 | s1 も同様に `run_role` の ledger / schedule 制御を迂回する | **real** | 採用。裁定 0-b と併せ、結論を exact cell と configuration に限定する |
| A-4 | node-local clone は root 束縛の monkeypatch ではない | refuted | 設計を維持 |
| A-5 | `stock_comparison` は分岐スイッチでなく整合性表明。実際の分岐は `_is_inert_value` | **real** | 採用。記録の文言を直す |
| A-6 | supply 腕は実 preprocess 比較である | refuted (= 恒真でない) | 記録に使う |
| A-7 | meaning 腕は owner-TU 実行でも stock 木比較でもなく、単独 TU の枝選択 | **real** | 採用。緑の意味を insight に明記する |
| A-8 | `unestablished` は use class によらず admission を通る | **real** | 採用。`unestablished_meaning_macros` を必ず記録する |
| A-9 | 対象 `-1` request が unestablished のまま通る形は 3 driver には無い | refuted | 記録するが懸念として書かない |
| A-10 | 恒真な保証 3 件 (fresh checkout の pinned-clean / 選んだ cell が -1 / admission の自己参照) | **real** | 採用。保証として数えない |
| A-11 | brief の s1 stock-root 条件が誤り | **real** | 採用。訂正する |
| A-12 | brief の「resolve なし」は captured root については誤り | **real** | 採用。「driver 呼び出し時は未 resolve、captured は resolve 済み」と直す |
| A-13 | brief の関門呼び出し行範囲が 3 箇所ともずれている | **real、親が実物で検算済み** | 採用。正: `backoff_sweep.py:378-392` / `backoff_repro.py:72-83` / `s1_direct_comparison.py:916-921` |
| A-14 | brief の「3 driver とも inert request は作られる」は広すぎる | **real** | 採用。裁定 0-a により s1 では**作られない**が正しい |
| A-15 | sweep の 2 点 screening admission を通常 7 値 family の admission の代用にしない | **real** | 採用。主張を inert arm に限定する |

## 2. 段 3 lens B の所見

| # | 所見 | 判定 | 処置 |
|---|---|---|---|
| B-1 | `_ccbench_dir()` は outer worktree ごとに別 path (親 brief の「共有 submodule」は不正確) | refuted + 訂正 | 「同じ outer checkout 内では共有」と直す |
| B-2 | sweep/repro は stock checkout でなく base tree 自体に patch する | **real** | 採用。driver 別 node-local clone を必須にする |
| B-3 | flock は `$TMPDIR` 依存でノードを跨がない | **real** | 採用。driver 別 clone で閉じる |
| B-4 | 強制終了で patch と worktree metadata が残る。`exec` すると shell の EXIT trap も走らない | **real** | 採用。**`exec` を禁止**し、trap を必ず走らせる。scratch path は再利用しない |
| B-5 | 対象 production 関数に赤を緑へ変える経路は無い | refuted | 設計を維持 |
| B-6 | s1 の 1 cell 緑を driver 全体の緑にすると偽の緑になる | **real** | 採用 (裁定 0-b / 0-c で解消) |
| B-7 | sweep は screening が abort でも `ok=True` になりうる | **real** | 採用。`summary.aborted == 0` と `committed == 期待数` を `ok` の条件に足す |
| B-8 | 0 request・0 record を admitted 扱いにはしない | refuted | ただし裁定 0-b で「record 0 件」自体を s1 の測定項目にする |
| B-9 | 3 driver 完走の機械判定が無い | **real、ただし処置は最小** | 1 job 1 process で 3 driver を順に走らせ、payload に実行した driver 集合を残す。新しい台帳・gate は作らない (scope 外) |
| B-10 | official output root 検査は scratch 束縛で足りる | refuted (条件付き) | 設計を維持 |
| B-11 | build cache の置き場所が plan の表と違う (`<ccbench source>/build-variants`) | **real** | 採用。表を直す。node-local clone 内なので隔離は成立 |
| B-12 | s1 の session ledger / 予算台帳は `prepare_cell` 直呼びでは進まない | refuted | 設計を維持 |
| B-13 | create-only writer が atomic でも durable でもない | **real** | 採用。temp へ書いて fsync し、最終 path へ create-only で publish する |
| B-14 | 最終 JSON は repo 内 `output/insights/` に置く予定で layout 検査の外 | **real** | 採用。**probe は repo 外の evidence dir にだけ書く**。insight への収容は親が段 7 で行う |
| B-15 | PBS の stdout/stderr の行き先が未指定 | **real** | 採用。`-o` / `-e` を repo 外の evidence dir へ明示する |
| B-16 | driver を別 job にすると node / toolchain / network が揃わない | **real** | 採用。**3 driver を 1 job・1 node・1 process で順に走らせる** (裁定 3) |
| B-17 | single tenant 検査は瞬間検査 | **real、ただし本 wave では受容** | 採用して記録する。関門は timing 測定ではないので再測要件にはしない。sweep の screening 値は本 wave の主張に使わない |
| B-18 | 2 時間 walltime は機械的上界でない (後段 build に timeout 無し) | **real** | 採用。walltime 3 時間、driver ごとに JSON を**その driver 終了直後に**書く |
| B-19 | repro/s1 の network 状態が未束縛 | **real** | 採用。network 状態を payload に**記録するだけ**にする。判定には使わず、retry も cache 注入もしない |
| B-20 | 誤 pin での緑は作らない | refuted | 設計を維持 |
| B-21 | `git clone --shared` は object 寿命が origin 依存 | **real** | 採用。alternates を使わない自己完結 clone にする |
| B-22 | 容量・inode 対策が宣言だけ | **real、ただし処置は最小** | scratch の空き容量を起動時に記録する。閾値 gate は作らない (scope 外) |
| B-23 | 「production を 1 行も変えない」に機械保証が無い | **real** | 採用。import した production 4 file の sha256 を payload に**記録する** (gate にはしない)。読み手が base と照合できる |
| B-24 | `s1_direct_comparison.py` の bytes 不変にも機械保証が無い | **real** | B-23 と同じ処置で閉じる |

## 3. 実行設計 (確定)

**1 job・1 node・1 process で 3 driver を順に走らせる。** 理由は B-16 である。
driver 間の緑/赤の差を driver の差として読むには、node image・compiler・network が
同一でなければならない。別 job に分けると `afterany` でも同一 node は保証されない。
親 brief の (P3)「別ノードへ同時投入」と段 2 plan の `afterany` 直列化はどちらも不採用。

実行順は **s1 → repro → sweep** とする。安い順に置き、sweep が長引いても
先の 2 件の結果が既に永続化されているようにする。

driver ごとの起動:

1. **s1** — production の `load_verified_freeze` → `schedule_for_role` で到達性を列挙 (裁定 0-b 1)。
   続けて `write-heavy:backoff_fixed_best` と `write-heavy:p2_2_flag_opt` の 2 cell を
   production の `prepare_cell(..., condition_use_class="certified-selection")` へ通す。
   `run_role` は呼ばない。
2. **repro** — node-local clone の `external/ccbench` を `dff0f1e` に置き、
   production の `_conditioned_backoff_patch(_genomes_reversed(10), cxx=...)` へ入る。
   併せて「現行 pin `511c953` の木では `assert_pinned_clean` が関門前に落ちる」ことを
   同じ job 内で 1 度実測する (clone を現行 pin に置いた状態で context に入る)。
3. **sweep** — production の `run_workload("write-heavy", ..., screening_enabled=True,
   screening_fixed_us=2)` を 1 度呼ぶ。`ok` の条件に `aborted == 0` を含める (B-7)。

root 隔離: driver ごとに node-local の自己完結 clone (alternates 無し、B-21)。
`buildcache._ccbench_dir()` も `ROOT` も monkeypatch しない。

## 4. `ok=True` の条件 (driver ごと)

初期値は必ず `ok=False`。次を全て満たしたときだけ `True`。

- s1 (到達性): `schedule_for_role` が 4 role とも成功し、18 cell の macro 列挙が得られ、
  inert request 件数が確定した (0 でも 0 以外でも確定すれば満たす)。
- s1 (cell 実走): 例外なく `prepare_cell` を抜け、`backoff_fixed_best` は
  `BACKOFF_FIXED` の supply / meaning 各 1 record と `admitted=True` の admission があり、
  `p2_2_flag_opt` は record 0 件・admission `None` である。
- repro: 例外なく context を抜け、`BACKOFF_FIXED=-1` の inert request があり、
  supply / meaning 各 1 record が `green`、admission が `admitted=True`。
- sweep: repro と同じ条件に加え、`summary.aborted == 0`。

例外が起きた driver は `ok=False`・非 0 rc。例外の型・message・`reason_code` 属性
(無ければ `null`)・cause chain をそのまま記録する。message から reason code を推測しない。
retry・引数緩和・cache 注入・別 root への fallback を一切設けない (規律 2)。

## 5. 記録するが判定に使わないもの (metadata)

hostname、compiler の実 manifest、cmake の identity、network 到達性の観測、
scratch の空き容量、import した production 4 file の sha256、
`unestablished_meaning_macros`、campaign id、選んだ cell の ID と configuration と freeze pin。

## 6. 変異事前登録 (DW-M01)

実装面は probe 1 file + PBS 1 file + テスト 1 file。変異は probe の**正直さ**を守る位置に置く。
各変異は実装後に「同じ入力を拒否する層が前後・内側に無く赤理由が 1 つに絞れる」ことを確認する。

| ID | 位置 | 変異 | 殺す検査 |
|---|---|---|---|
| M1 | result builder の初期値 | `ok=False` を `ok=True` にする | record 発行前に例外が出た driver で `ok` が False であることを固定する検査 |
| M2 | supply 判定 | `terminal_status == "green"` の要求を落とす | 赤 supply record を与えたとき `ok=False` になることを固定する検査 |
| M3 | admission 判定 | `admitted is True` の要求を落とす | `admitted=False` の admission で `ok=False` になることを固定する検査 |
| M4 | 例外の直列化 | `reason_code` を message から推測する | `reason_code` 属性の無い `RuntimeError` で `null` になることを固定する検査 |
| M5 | sweep runner | `summary.aborted` を無視する | `aborted=1` の summary で `ok=False` になることを固定する検査 |
| M6 | evidence writer | create-only を上書きに変える | 既存の出力 path があるとき publish が拒否されることを固定する検査 |
| M7 | s1 到達性列挙 | inert request 件数を実測でなく定数 0 にする | inert cell を含む合成 freeze で件数が 1 以上になることを固定する検査 |

`DW-M08` の新旧両走は本 wave では不要 (新規 file であり旧 HEAD に対応物が無い)。
既存テストが同じ変異を捕まえないことを段 6 で確認し、捕まえるなら再照準する (F28)。

## 7. scope 外 — 実装せず裁定パッケージへ返す

1. `backoff_repro` と `s1_direct_comparison` へ FetchContent base を供給する修正
   (= 本 wave が測ろうとしている赤の直し方)。**規律 2 により本 wave では実装しない。**
2. `patchharness` への共有 filesystem 対応 lock と kill recovery の一般化。
3. 3 driver の完走を機械判定する aggregate manifest・台帳・gate の新設。
4. s1 の全 configuration・全 cell への被覆拡大。
5. `backoff_sweep` の通常 7 値 family admission の実測。
6. network 起因の赤を「driver の赤」と「環境不成立」に分ける policy の制定。
   本 wave は reason code と network 観測を両方記録するに留める。
7. 既存 campaign 成果物・凍結成果物の訂正や失効。
8. `certified-selection` で他 macro の `unestablished` を許す設計判断の再検討。

## 8. 成果物の表現 (段 7 で守る)

- 「3 driver の production 入口から inert 経路が通る」とは書かない。
  書いてよいのは「列挙した exact な seam に、exact な pin / root / compiler / configure 条件で
  入り、両腕の record と admission を観測した」までである。
- s1 は「inert 経路は production の凍結入力から到達不能」と書く。緑とも赤とも書かない。
- sweep は「2 点 screening の inert arm」と限定する。通常 sweep の family admission は未測定と書く。
- 予測 (段 2 plan と親の読み) は予測として節を分け、実測値と混ぜない。
