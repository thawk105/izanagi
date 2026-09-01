# 段 7 cross-protocol の実装残余を protocol 対応にする (T-2115、2026-09-01)

- **wave 種別:** `/dev-wave [T-2115] 段 7 cross-protocol の実装残余を進める`。
  裁定は 2026-08-11 に決着済み (D1360)、残るのは実装であるという前提で起票された。
- **基準 commit:** `2bf9cf387`。branch `worktree-dev-wave-t2115-cross-protocol-impl`。
- **実装 commit:** `0567282e7` (production 8 file + test 8 file、+1080/-64)。
- **成果物:** 本 insight + worklog / decisions fragment + 実装。

---

## 1. 何を実装したか

D1360 が名指しした実装残余 3 点と、公式成果物への接続を実装した。

| 残余 | 実装前 | 実装後 |
|---|---|---|
| genome 空間の登録 | `SPACES` は silo 1 件 | silo + mocc の 2 件 (mocc は 3 ブール・YCSB で 8 通り) |
| between-run floor の baseline | silo 固定の module 定数、出力 path にも protocol 軸なし | protocol から引く写像。silo の baseline と出力 stem は不変、mocc だけ stem に protocol が入る |
| 層 3 の floor 照合キー | (records, threads, workload) | (protocol, records, threads, workload) |
| 公式成果物への接続 | — | 層 3 material report の `noise_floor` に protocol と、legacy 一致の根拠を記録する |

整合部品として `screening_driver.load_between_run_floor` と 3 caller
(`backoff_sweep` / `s6_sort_sweep` / `s8a_trigger_sweep`) も protocol 対応にした。
これを外すと、同一 workload の第 2 protocol floor が置かれた瞬間に
**既存の silo screening が `matches=2` で全部落ちる**。

## 2. 実装しなかったこと (残余)

- **tictoc/cicada の登録。** D1360 の初手 mocc に従い、段階導入とした。
  `docs/phase3.md` 段 6 dormant (b) はこれで**閉じていない**。
- **within-run certified calibration (`output/env/*/calibration/registered/`) の閉包。**
  層 3 は calibration directory 直下しか走査せず、certified 側へ接続していない。
- **screening の照合キーに records/threads を足すこと。** 本 wave が作った欠陥でも
  悪化させる欠陥でもないため scope 外とした。
- **within-run producer (`orchestrator/calibrator/`) への protocol 記録。**
  producer は `--binary <ycsb_*.exe>` を手渡しで受け genome を記録しないため、
  既存の within-run 較正 record には protocol の手がかりが 1 文字も無い。

## 3. 規律 2 の境界をどう守ったか

現行 submodule pin (`511c9538`) に mocc の TRACE hook は無い
(`cc/mocc/transaction.cc` の TRACE 出現 0、silo は 15)。
一方で **mocc の build を止める層は他に無い** — `source_digest` の `ALLOWLIST` と
`EVOLVE_BLOCK_SOURCES` は既に `cc/mocc/transaction.cc` を含み (T-755 の trace-hook 目的)、
`buildcache` は `ycsb_{protocol}.exe` で protocol 汎用である。
between-run floor driver は `trace=False` で build し verifier を通さないため、
**ここが唯一の無防備な経路**だった。

そこで floor 生成の admission を置いた。設計上の要点は、これを固定 allowlist にしなかったことである。
`{"silo"}` と書くと「hook が無いから拒否している」という主張がコードの事実に束縛されず、
mocc の trace 移植が終わった後も拒否し続ける**恒真な検査**になる (段 3 検査 A の指摘)。
実装は CCBench の source を実際に読み、証拠が無ければ拒否側へ倒す。

## 4. 述語を実際に強くした 4 段階 (すべて親が実測して発見)

述語は段 5 の初版から段 6 の 2 巡を経て次のように狭まった。各段の穴は親の probe が実測で再現した。

| 段階 | 穴 | 実測 |
|---|---|---|
| 初版 | `cc/<protocol>/` 配下を全走査 | **コンパイルされない `decoy.cc` を 1 つ置くだけで False → True** |
| 初版 | コメント・dead branch を除去しない | include と `#if TRACE` が生きていれば、**フック呼出しがコメントアウトされていても True** |
| fix 1 巡目 | `#if 0` 除去が最初の `#endif` で終わる | **`#if 0` の中に `#if ... #endif` が入れ子だと後半が残り True** |
| fix 2 巡目 | — | 上記 3 つがすべて False。正例 (実 submodule の silo、CMakeLists の SOURCES に載る実フック) は True のまま |

**現行の強さと限界。** これは text-level の検査であり、プリプロセッサ条件を評価しない
(literal `#if 0` だけを dead として扱う)。hook の意味論的正しさも、verifier が通ることも、
測定値の正しさも証明しない。目的は fail-closed の拒否であって hook 実在の証明ではない。
この限界は述語の docstring に逐語で書いてある。

## 5. canonical genome の解析を 1 箇所に置いた

floor JSON と WAL の両方が canonical genome から protocol を取る。初版は `|` の前を取るだけで、
`mocc|garbage`・`silo|B=x`・`silo|Z=1,A=0` (非整列)・`silo|A=1,A=2` (重複)・`silo|` (空 body) を
すべて受理していた (親の実測)。これは floor だけでなく **WAL からの campaign protocol 判定にも**
効いており、receiptless な `build_start` は他の exact parser を通らない。
現在は body を整数化して `Genome.canonical()` との完全一致を要求する。

## 6. within-run floor の legacy 扱い — 何を主張していないか

`noise_floor` block を持ち `genome` を持たない歴史的 record は silo campaign にだけ一致させる。
**これは「silo と確認した」という主張ではない。** 既存 2 件の within-run 較正 record には
protocol の手がかりが無く (file 全体に "silo" の文字列が 1 度も現れない)、
producer も genome を記録しない。したがって「legacy = silo」は**歴史についての仮定**であって
bytes から導ける事実ではない。層 3 report はこの一致の根拠を
`genome-absent-legacy-record` として明記し、確認済みの protocol とは書き分ける。

厳密に拒否する設計も検討したが、既存 silo campaign の within_run floor が
`no-matching-env-record` へ落ちて公式成果物の値が変わるため採らなかった。

## 7. 凍結成果物との関係

`orchestrator/campaign/genome.py` の SHA は
`known_axes_freeze.json` / `measurement_freeze.json` / `holdout_freeze.json` の 3 つに
source record として記録されており、実装前の bytes と一致していた。本 wave の変更でこれは stale になる。

**現に緑である gate は 1 つも赤にしていない。** 実測は次のとおり。

- `known_axes_freeze` の live tree 検証は **base commit の時点で既に赤**
  (`generator sha256 不一致 recorded=1d4d45a3… actual=9cc9f877…`)。source 一覧に到達しない。
- 同 artifact が参照する `backoff_sweep.py` / `s6_sort_sweep.py` / `s8a_trigger_sweep.py` の
  3 本は既に drift 済みで、source SHA が歴史記録であることを示している。
- 凍結層の live-bytes 検査はユーザー裁定で保留中 (`freeze_verification_hold.HELD = True`、21 件)。
- live bytes を `8e8abd7f…` と比べる pin は `.py` に 1 件も無い。
- `test_s1_known_axes_freeze.py` + `test_s8b_oracle_driver.py` は base で 160 passed / 15 skipped。

規律 7 に従い、当時の bytes という歴史的事実は変わらない。現行コードとの差は、それだけでは
何かを無効にする理由にならない。

## 8. 段 3・段 6 の検査が実際に効いた点

- 段 3 検査 A が「固定 allowlist は恒真な検査になる」と指摘し、設計を source 束縛へ変えた。
- 段 3 検査 B が「screening は protocol だけでなく records/threads も見ていない」と指摘し、
  scope 内外の線を引き直した (protocol だけを scope 内とした)。
- 段 6 レビュー A / B が別経路から同じ根 (genome body の不検証) に到達した。
- **段 5・段 6 の子は sandbox の制約で pytest を 1 件も実走できなかった。**
  create-only test の fixture path 誤り (機構を一度も通らずに赤になる) は、
  親の実走でしか見つからない型だった。

## 9. 見なかったことにしていない前提

- 本 wave は測定を 1 件も行っていない。mocc の floor も較正も実測していない。
  実測は人間の qsub 手番であり続ける (D87/D86(3))。
- `space_for()` に production caller は無い。mocc の登録は探索空間の宣言であって、
  certified な mocc campaign を成立させるものではない。
- 段 7 全体の発火条件 (D32 = 8b + 層 3 後) が充足したかは本 wave では判定していない。
