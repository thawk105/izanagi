# 所見

## 1. T1-2 / T1-3 を迂回して実行値を変更できる

- **区分**: must-fix
- **成果物影響**: `BACKOFF_FIXED=20` と記録された candidate が実際には `now_backoff=30` で走り、certified 選択、fitness 帰属、材料レポート、WAL の genome 表示が binary と食い違う。
- **根拠**:
  - 再束縛検査は `now_backoff` の前後に代入・増減 token が直接ある場合しか拒否しない: `orchestrator/campaign/backoff_hole_grammar.py:458-479`
  - 帰属検査は最初の `now_backoff = <数値>` と `coder.value` の一致しか見ない: `orchestrator/campaign/p3_s4_loop.py:923-954`
  - 次は grammar、既存 effect gate、帰属検査を静的にすべて通るが、実行時に値を 30 へ変更する。
    ```cpp
    double now_backoff = 20;
    [](double& x) { x = 30; }(now_backoff);
    ```
  - lambda parameter による二重宣言も、内側の `now_backoff` の直後が `)` なので宣言として数えられない:
    ```cpp
    double now_backoff = ([](double now_backoff) {}(1), 20);
    ```
    宣言検出の条件は `backoff_hole_grammar.py:402-447`。
  - D39 決定 7 は「`flags['BACKOFF_FIXED']` と hole literal を coder の value で揃える」と要求する: `docs/decisions.md:1142-1149`
  - 親裁定の T1-2 / T1-3: `s4-adjudication.md:50-54`
- **scope 判定**: 本 wave の scope 内。T1-2 / T1-3 と D39 決定 7 の実装不足である。

## 2. 正準化は閉じていない

- **区分**: must-fix
- **成果物影響**: `20`、`20.0`、`20.00`、外周空白違いが同じ genome 値の別 `src_token`、variant、cache entry、iteration として certified 選択と試行台帳へ重複する。
- **根拠**:
  - 数値 token の表記は捨てられ、spelling を検査していない: `orchestrator/campaign/backoff_hole_grammar.py:279-284`
  - 数学的整数の float は明示的に受理する: `backoff_hole_grammar.py:483-498`、`orchestrator/tests/test_p3_s4_loop.py:461-483`
  - `render_hole()` は受領文字列をそのまま挿入し、`quarantine()` もその bytes を書く: `orchestrator/campaign/p3_s4_loop.py:177-187,303-306`
  - variant ID は `src_token` を preimage に含む: `orchestrator/campaign/pipeline.py:117-123`
  - D174 は「受理した文字列をそのまま materialize せず、書込み直前に emitter の正準 bytes へ解決」と決定している: `docs/decisions.md:8587-8609`
  - 親裁定は B-4 を「T1-6 が同時に閉じる」としたが、現物は閉じていない: `s4-adjudication.md:86`
- **scope 判定**: 本 wave の scope 内。親裁定の明白な誤りである。

## 3. 裁定外の token / nesting cap と control-flow 拡張が受理集合を縮める

- **区分**: must-fix
- **成果物影響**: 現 role が生成可能な `<式>` が build 前に `BACKOFF_GRAMMAR` へ落ち、探索候補数、reject WAL、最終選択集合が無承認で変わる。
- **根拠**:
  - 親の T1-7 は type / raw-size preflight だけで、token 数・nesting 深さを規則に含めていない: `s4-adjudication.md:55`
  - 実装は 1024 token、nesting 64 を追加した: `orchestrator/campaign/backoff_hole_grammar.py:40-43,295-305`
  - 65 重括弧という role 上有効な `<式>` を拒否する期待値まで固定している: `orchestrator/tests/test_p3_s4_loop.py:450-458`
  - 親の T1-4 は `goto`、`return`、`throw`、label、`break`、`continue` を列挙した: `s4-adjudication.md:52`
  - 実装は `if`、`else`、`switch`、loop、`try/catch` まで追加した: `backoff_hole_grammar.py:162-166`
  - role は initializer を `<式>` としか限定していない: `.claude/agents/coder-v4-autonomous.md:52-63`
  - 親自身が式内部の lambda・call・comma などの狭化には role、ledger、adapter、manifest の同時改訂と明示承認が必要とした: `s4-adjudication.md:57-63`
- **scope 判定**: 本 wave の scope 内。ユーザー承認を得るか、裁定された規則まで戻す必要がある。

## 4. 新 subtype の critic consumer が rule ID を落とし、誤ったヒントへ分岐する

- **区分**: must-fix
- **成果物影響**: critic は grammar 違反を構造化 rule として受け取れず、フレーム逸脱として次手を生成するため、reflux 後の proposal と certified 選択系列が変わる。
- **根拠**:
  - writer と WAL は `res.digest` を generic に保存するため新 subtype 自体は残る: `orchestrator/campaign/p3_s4_loop.py:350-371`
  - loader は `host-effect` 以外の `rule_id` を空文字へ上書きする。したがって `backoff-grammar` の rule ID も消える: `orchestrator/critic/digest.py:749-757`
  - renderer に `backoff-grammar` 分岐がなく、最後の「フレーム/hole 逸脱」ヒントへ落ちる: `orchestrator/critic/digest.py:1201-1216,1288-1305`
  - 新テストは非反射しか検査せず、`loaded[0].rule_id` や専用ヒントを検査しない: `orchestrator/tests/test_p3_s4_loop.py:578-612`
  - 実装子の「generic な固定診断として消費」という報告はこの欠落を隠している: `s5-author.md:59`
- **scope 判定**: 本 wave の scope 内。enum 追加の consumer 閉包に含まれる。

Consumer 全体の判定は次のとおり。

| consumer | 判定 |
|---|---|
| `record_diff_reject` | 新 digest をそのまま WAL へ保存し、落ちない |
| WAL parser / reader | stage と JSON 型の generic 検査であり、新 subtype で落ちない |
| `load_diff_rejections` | subtype は残るが rule ID を消すため不完全 |
| `render_rejections` / critic digest | 表示はされるが誤った一般分岐へ落ちる |
| `load_liveness_rejections` | `reason=="diff-quarantine"` で除外するため二重計上なし |
| layer3 report | abort payload を generic に保持する: `orchestrator/campaign/layer3_report.py:305-313,563-584` |
| preview / log の `.value` | generic で問題なし |
| enum 全 member 固定 test / golden | repo 内検索では該当なし。既存順序表 `diff_quarantine.py:529-532` は structural 4 subtype 専用で、網羅表ではない |

## 5. consumer closure テストは coder ingress を検査していない

- **区分**: must-fix
- **成果物影響**: 別名呼出し、別 helper、直接 `replace` / write、campaign 外 materializer が追加されてもテストが緑のままになり、文法外 coder bytes が build・COMMIT へ到達できる。
- **根拠**:
  - テストが列挙するのは `render_hole` という名前の直接 call だけ: `orchestrator/tests/test_p3_s4_loop.py:637-663`
  - alias、関数値経由、別 materializer、直接書込み、campaign directory 外は母集合に入らない。
  - 親裁定は「将来 coder テキスト経路が増えたとき黙って穴が開かない」ことを目的にした: `s4-adjudication.md:104-106`
  - D127 決定 3 は driver 内だけの gate では別 materializer が素通りすると決定している: `docs/decisions.md:6247-6250`
- **scope 判定**: 本 wave の scope 内。現時点の production bypass は静的には見つからないが、裁定された tripwire の目的を満たしていない。

## 6. commit message の実測記録が投影資料と整合しない

- **区分**: must-fix
- **成果物影響**: 実走 0 件の受理集合を「382 passed」として検証済みに見せ、材料レポートと採用判断が未実証の gate を緑扱いする。
- **根拠**:
  - commit `6935fcae` は「焦点走: 382 passed, 6 skipped」と記録する。
  - 実装子報告は正規 runner 3 回とも `child_started=false`、実走 nodeid 0 件と明記する: `s5-author.md:21-28,35-46`
  - commit の「32 形中 25 形から 15 形」について、変更されたテストには同一 32 形 corpus と 25/15 の count assertion がない。新規 positive は別の 12 形、negative も別 parametrization である: `orchestrator/tests/test_p3_s4_loop.py:302-423`
  - 「既存 7 形の subtype 保存」は、cap 内では structural → effect → grammar の順なので静的には整合する: `orchestrator/campaign/p3_s4_loop.py:264-302`
  - 「規律 2 が成立したとは書けない」は、Tier 2 式を明示受理しているため正しい: `test_p3_s4_loop.py:302-319`
- **scope 判定**: 本 wave の scope 内。後続で本当に走った receipt を示すか、実測表現を静的確認へ訂正する必要がある。

## 7. grammar version の identity 非束縛

- **区分**: 裁定パッケージ候補
- **成果物影響**: policy 世代を区別しない旧 WAL・cache・材料レポートが現 grammar の証拠として参照され得る。
- **根拠**:
  - variant ID は genome と source tokenだけ: `orchestrator/campaign/pipeline.py:117-123`
  - `SourceEvidence` に grammar policy/version はない: `orchestrator/campaign/source_digest.py:2096-2135`
  - 親も real と認めつつ Tier 2 (iii) へ返した: `s4-adjudication.md:65-68,84`
- **scope 判定**: 本 wave の scope 外。現 commit の単独修正へ混ぜず、policy migration として裁定すべき。

## 8. t441.m03 の変異期待が誤っている

- **区分**: nit
- **成果物影響**: certified 値は変わらないが、mutation report が「受理集合を広げる変異」を kill したと誤記する。
- **根拠**:
  - 親は空実装検査除去を受理集合変異として登録した: `s4-adjudication.md:121-124`
  - 宣言必須検査が空実装を引き続き拒否するため、変わるのは rule ID だけ: `s5-author.md:31,44-47`
- **scope 判定**: 本 wave の scope 内。

# trigger / sort 非影響と preflight 判定

guard は部分一致や `in` ではなく、preflight と本 grammar の両方で exact `marker_id == MARKER_ID` である: `orchestrator/campaign/p3_s4_loop.py:226-233,295-302`。

中核 6 call site はすべて別の exact marker を渡す。

| 軸 | call site | marker |
|---|---|---|
| sort | `p3_s4_loop_sort.py:156` | `silo-writeset-sort` |
| sort | `p3_s4_loop_sort.py:456` | 同上 |
| sort | `p3_s4_loop_sort.py:564` | 同上 |
| trigger | `p3_s4_loop_trigger_gating.py:421` | `silo-backoff-trigger-gating` |
| trigger | `p3_s4_loop_trigger_gating.py:890` | 同上 |
| trigger | `p3_s4_loop_trigger_gating.py:1007` | 同上 |

追加 caller も `s6_sort_sweep.py:333,354`、`s8a_trigger_sweep.py:434,456`、`p3_autonomous_workload_trial.py:1595`、`s1_verify_extime_calibration.py:342`、`s1_direct_comparison.py:666` で各軸定数を渡す。したがって production 15 call site のうち backoff の `p3_s4_loop.py:1061,1069` だけが新 gate 対象で、trigger / sort の受理集合は静的には不変である。

`assert_value_literal_consistent()` の preflight は marker 分岐を持たないが、production caller は backoff の `run_one_iteration()` 1 点だけ: `p3_s4_loop.py:1039`。trigger / sort sibling driver はこれを呼ばない。type/raw-size は path read・render より前、value gate は attribution 後かつ `int()` 前にあり、T1-7 の位置は正しい。

# 独自判断 6 件の scope 分類

| 実装子の判断 | 分類 | 判定 |
|---|---|---|
| 4096 code point/byte、1024 token、nesting 64 | 裁定を超えた過剰拒否 | raw cap 自体は T1-7 内だが、token/nesting は未裁定で、有効な `<式>` を拒否する |
| 数学的整数の `20.0` value を許可 | 裁定の射程内 | 無損失 `int()` という T1-6 には合う。ただし hole spelling の正準化を閉じない |
| 分岐・loop・try/catch を追加拒否 | 裁定を超えた過剰拒否 | 親の凍結 token 集合と Tier 2 の式開放を超える |
| `001`、suffix、`1..0` 等を grammar で落とさない | 裁定の射程内 | Tier 2 を狭めない方針に合う。build 失敗は certification 前に落ちる |
| value gate を AttributionMismatch 後、`int()` 前へ配置 | 裁定の射程内 | T1-7 と既存理由の優先順位を両立する |
| closure を `render_hole` call 集合と定義 | 裁定を下回る不足 | helper 名の閉包であって coder ingress / materializer 閉包ではない |

D127 決定 1 に関する親の読みは本文上妥当である。`docs/decisions.md:6238-6239` は「複数行の raw comparator」と「sort 軸」を明記しており、backoff の文型固定一般を禁じてはいない。ただし `<式>` の狭化には同じ producer/consumer 非互換の論理が当たり、今回の追加 cap・追加 control-flow 拒否はその承認境界を越えている。

## 総括

- **must-fix は 6 件**。最も危険なのは、別名参照を介した `now_backoff` 書換えが T1-3 と帰属検査を通り、`BACKOFF_FIXED=20` の certified candidate を実値 30 で走らせられる点である。
- commit `6935fcae` は現状では採用不可。少なくとも T1-2/T1-3 の抜け、正準化、無承認過剰拒否、critic consumer、closure tripwire、実測記録の6件を直して再レビューする必要がある。
- 親裁定で誤っている点は、(1) T1-6 が `20` / `20.0` / `20.00` の多重 identity を同時に閉じるという判断、(2) 現 lexical T1-3 で D39 の実行値帰属を守れるという前提、(3) `render_hole` call inventory が将来の coder ingress を固定するという設計、(4) t441.m03 を受理集合変異とした登録である。D127 決定 1 の sort 固有という読み自体は誤りではない。

pytest、build、mutation harness は実行していない。以上は静的検査のみである。