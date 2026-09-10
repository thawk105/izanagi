# 段 4 裁定 — [T-2228] screening 関門への FetchContent base 供給

親 (claude, manager) が段 2 プランと段 3 レンズ A / B の全所見を裁定する。

## 裁定 0 — 親 brief の不変条件 1 を訂正する (レンズ A must-fix 1 / real / 採用)

brief は「受理集合を変えない」「赤入力は赤のまま」と書いたが、**文字どおりには成立しない。**
本変更の目的そのものが、準備済み dependency の未供給だけを理由に前段で赤になっていた入力を、
本来の supply 判定へ進ませることである。

**訂正後の不変条件 1:** 関門の**判定式・既定値・stock 比較・meaning 腕・admission 条件は
1 行も変えない。**受理集合は「準備済み FetchContent base の未供給だけを理由に
`preprocess-failed` で止まっていた呼び出し」が判定へ進む分だけ**制御された拡張**になる。
記録では「緩めていない」ではなく「制御された拡張」と書く (D1721 の形)。

**はみ出しの明示 (レンズ A / real / 採用):** 共有 base が変えるのは masstree の `config.h` だけでなく、
masstree / mimalloc / googletest の FetchContent population 全体である。したがって
「`config.h` 欠落だけが消える」とは書かない。「準備済み base の未供給に起因する前段赤が消える」と書く。

## 裁定 1 — (P1) は「経路の代理」と明記する (両レンズ / real / 採用)

`expected_toolchain_manifest is not None` は**供給の権限を表す述語ではなく、
現行 call graph 上で backoff screening 経路を選ぶ代理**である。実装はこの形を採るが、
記録と docstring では代理であることを明記する。

- **プランの「`None` test があるので将来の水平展開はできない」という主張は削除する** (レンズ B / real)。
  helper を直接 `None` で呼ぶ test は、caller が manifest を渡すように変わっても緑のままである。
  この test は「現在 `None` 経路が非発火であること」だけを固定する。
- 新しい policy gate・driver-id 判定・boolean knob は**足さない** (仮想リスク向けの gate 追加は scope 外)。

## 裁定 2 — load-bearing 正例を必須にする (両レンズ must-fix / real / 採用)

プランの正例は、prepare を stub にしたうえで既存 fixture `condition_meaning_gate/supplied` を使う。
この fixture は `FETCHCONTENT_BASE_DIR` を無害に参照するだけなので、
**供給が実際には何も届けていない実装でも緑になる。**恒真である。

**要求する形:** 供給が無ければ赤、供給があれば緑になる fixture を 1 つ作る。

- fixture の owner TU は、**準備済み base の中にしか存在しない header** を include する。
- test 側の prepare 代役は、渡された `fetchcontent_base_dir` の中へその header を実際に置く。
  つまり prepare の**返り値ではなく副作用**が正例を成立させる。
- 同じ fixture で、prepare 代役を「何も置かない」形に変えると赤になることを負例で示す。
  これが「供給が load-bearing である」ことの実測である。
- **実 CCBench の masstree を unit test で build しない。**時間予算に収まらず、
  `patchharness` の実 repo アクセス登録も要る。合成 fixture で機構の生死を示す。

これは仮想リスク向けの検査の新設ではなく、**本 wave が入れる機構そのものの正例**である。

## 裁定 3 — 計算ノードでの生死確認は本 wave の scope 外 (両レンズ must-fix / real / 不採用)

両レンズが「実 CCBench の screening 関門を供給後に通す生死確認が要る」と must-fix にした。
**所見は real である。しかし本 wave では実装しない。**

- ユーザーの依頼は「本題の実装だけ」であり、計算ノードでの本走はその外にある。
- D1666 も同じ形を採った — driver 段の供給を実装した wave と、関門の生死を実測した wave
  (T-2228 の一次資料を産んだ wave) は別である。
- したがって本 wave は **「screening 関門が緑になった」とは名乗らない。**
  名乗れるのは「driver 段と同型の供給を screening 関門へ入れた」ことだけである。
- 生死確認は「次の一手」へ起票する。再訪条件は「現行の正規入口 (CLI) から
  `screening_fixed_us=2` の最小 screening を計算ノードで走らせ、baseline の stock 腕まで
  緑 record を得ること」とする。

## 裁定 4 — 観測者効果の非対称は本変更に帰属しない (レンズ A must-fix 3 / refuted)

レンズ A は「per-genome の prebuild が baseline (settle あり) と候補 (settle なし) の
熱状態を非対称にする」と must-fix にした。**親が現物で反証した。**

`pipeline.evaluate` は関門の後に `_prepare_evaluation_core` で variant の**完全 build** を行い、
その後で `_bench_prepared` を走らせる (`orchestrator/campaign/pipeline.py:1949-1985`)。
つまり関門と計測の間には既に分単位の build が挟まっており、これは baseline と候補の両方で起きる。
関門の前に 20 秒の masstree build を足しても、計測直前の熱状態を支配するのは variant build である。
`do_settle` の baseline / 候補の非対称は**本変更以前から存在する設計**であり、
本変更に帰属しない。settle を足す案は計測の意味論を動かすので採らない (規律 7)。

**ただし記録には残す** — 「関門前の作業量が増えたこと」は事実であり、insight に 1 行書く。

## 裁定 5 — 「実測で確かめた前提」の括りを直す (両レンズ / real / 採用)

brief の同節のうち、caller 数・manifest 転送・`prepare` の必須 keyword・canonical source root は
**静的確認**であって実測ではない。「20 秒程度」は D1666 の単一観測 (20.2 秒) の引用であって
本 wave の反復測定ではない。記録では「静的確認」と「引用した単一観測」を実測と書き分ける。

「関門は genome ごとに走る」も正確ではない (レンズ B / real / 採用)。terminal かつ
非 retryable な候補は関門より前に return し、baseline は `force=True` で必ず走る。

## 裁定 6 — 編集面は 3 関数である (レンズ B / real / 採用)

brief の「編集面が 1 関数 + test」は誤り。実際は
`_run_condition_gate_for_genome`、`_require_condition_gate_before_evaluation`、
`evaluate_candidate` の 3 関数を変更する。production の変更は `screening_driver.py` に閉じる。

## 裁定 7 — (P2)(P3)(P4) はプランどおり採用、ただし P3 の表現を直す

- **(P2) 採用。** 関門 1 回につき一時 base 1 つ、request 空判定の後・`capture_define_inputs` の直前、
  stock checkout の内側。関門直後に閉じる。
- **(P3) 採用、表現を訂正。** `site=None` を明示し `buildcache` の既定解決に任せる。
  ただし「driver 段と同じ解決を使う」ではなく「**関門ごとに `current_site()` を再観測する**」が正しい
  (レンズ B / real)。driver 段は開始時に解決した値を転送しているので、同じ観測値の転送ではない。
  `site` を `evaluate_candidate` の公開引数へ増やすことはしない。
- **(P4) 採用。** prepare の例外は捕捉しない。`evaluate_candidate` の candidate-abort 捕捉より前なので、
  偽の関門赤にも WAL の candidate abort にもならず、評価全体を停止する。

## 裁定 8 — 変異事前登録を作り直す (レンズ B must-fix / real / 採用)

プランの 12 件から、単一理由性 (`DW-M01`) と kill の意味 (`DW-M03`) に照らして再登録する。

- **M8 は削除。** `site=None` の省略は引数既定値と同じで**意味を変えない no-op** である。
  no-op を殺す exact 検査は機構の証拠にならない。固定 `"OTHER"` への差し替えだけを残す。
- **M5 を M5a (prepare 削除) と M5b (prepare 2 回) へ分割。**
- **M6 を M6a (`ccbench_dir` を `stock_root` へ) と M6b (非 canonical root へ) へ分割。**
  M6b は `buildcache` の absolute-directory 検査が先に拒否する可能性があるため、
  probe で赤理由が一つに絞れなければ登録から外す。
- **M1 / M3 / M4 は期待 node の完全集合を probe で採り直す。** レンズ B の指摘どおり、
  これらは複数 test を同時に赤にする。`DW-M07` に従い **probe は全件 SURVIVED で登録して
  観測 node を集め**、その後に完全集合で本登録する。
- **新規の M13 を足す。** 裁定 2 の load-bearing fixture に対し、
  「供給した base を `capture_define_inputs` へ渡さない」変異が、
  その正例だけを殺すことを示す。これが機構の帰属の中心である。

最終の変異 matrix は probe の観測 node が出た時点で確定する。

## 裁定 9 — pin 閉包は再登録不要 (両レンズ / 採用)

- perf 閉包・spawn 台帳・certified writer 閉包・line-number pin・file 全体 sha256 pin の
  いずれも再登録不要。親と両レンズが独立に同じ結論へ達した。
- `acceptance_duration_ledger.json` は新規 nodeid を持たないが、**受理条件ではない**
  (未知 nodeid は policy default で並ぶだけで、値・受理集合・参照を変えない)。手書き登録しない。
- **ただし裁定 2 で新しい fixture directory を作るので、fixture の在庫を数える exact 検査が
  無いことを実装子が確認する。**あれば登録する。

## 裁定 10 — scope 外の real 所見 (裁定パッケージへ)

実装しない。ユーザーへ返す。

1. **masstree autotools の CC/CXX が manifest へ束縛されない。** `prepare_masstree_fetchcontent` は
   top-level CMake の compiler は manifest から設定するが、masstree の custom command は
   `./configure` と `make` を CC/CXX 指定なしで実行し、親環境を継承する。
   生成される `config.h` の compiler 入力は manifest に束縛されない。D1666 の既知限界より広い。
2. **s6_sort_sweep と s8a_trigger_sweep の独自 preflight 関門も同型の base 未供給である。**
   本 wave では触らない。それぞれ正規入口での到達性の実測と裁定を要する。
3. **`backoff_repro` と `s1_direct_comparison`** は D1733 が明示的に禁じている。触らない。
   再訪条件だけを維持する。
4. **関門が見た `config.h` と計測 build の `config.h` の bytes 非束縛。** D1666 が受容した限界。
5. **screening 関門の生死確認 (裁定 3)。** 次の一手へ起票する。

## プラン v2 (段 5 の実装子への確定指示)

段 2 プランを次の 6 点で上書きし、残りはプランどおりとする。

1. 不変条件 1 の表現を裁定 0 のとおりにする (docstring・コメントに「受理集合不変」と書かない)。
2. 裁定 2 の load-bearing fixture と正例・負例を必ず作る。
3. `None` 経路の test に「将来の水平展開を防ぐ」という意味づけをしない (裁定 1)。
4. `site` の扱いを裁定 7 のとおりに書く (「driver 段と同じ解決」と書かない)。
5. 変異は裁定 8 の集合で probe する。実装子は変異を走らせない (親が段 6 で走らせる)。
6. production の変更は `screening_driver.py` の 3 関数に閉じる。
   `backoff_sweep.py` / `s6_sort_sweep.py` / `s8a_trigger_sweep.py` / `backoff_repro.py` /
   `s1_direct_comparison.py` / `buildcache.py` / `condition_meaning_gate.py` は編集しない。
