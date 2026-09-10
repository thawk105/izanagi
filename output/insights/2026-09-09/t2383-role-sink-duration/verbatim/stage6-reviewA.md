## 裁定との照合

- C1: 実装済み。binding は反復前の `:1858` で1回だけ計算され、`:1886-1888` から helper へ渡される。引数省略 caller は `:244`、`:3463` に残り、`campaign_lock_test_support.py:23-36` の `binding is None` 経路を従来どおり通る。
- C1 の live capture: 減っていない。各 wire は helper の `:223` と production critic 経路の `p3_autonomous_workload_trial.py:3363` で2回 admission を行い、いずれも `artifact_admission.py:1118` の live closure capture を通る。32 wire 合計64回である。
- C2: 実装済み。module 定数は `:56`、局所 worker は `:1860`、ordered `executor.map` は `:1959-1968`。共有 collection の変更は main thread のみである。
- C3: 実装済み。4 role と `trusted_variants`、`secret_records` の `== 32` は `:1970-1975` にあり、全横断 assert の先頭 `:1976` より前である。
- C4: wire を返すという指定は `:1942` と `:1963-1964` に実装されている。ただし失敗診断の目的には不足がある。詳細は should-fix。
- C5: 実装済み。`:1847-1851` は被覆命題、逐次スケジュールの除外、逐次時だけ混入する欠陥を失うことを明記している。
- 変更前の per-iteration 6 種はすべて維持されている。`do_build` は `:1885`、4 role の件数は `:1916-1918`、variant 一致は `:1924-1927`、candidate label 不一致は `:1928-1930`、build start 件数は `:1932-1937`、build attempt ID 非混入は `:1938-1941`。
- これらは `run_wire` の返却前にあり、成功時には `executor.map(run_wire, range(32))` の全結果を消費するため、全32 wire で実行される。
- 旧横断 assert 7 種は条件を変えず `:1976-1995` に残る。skip、xfail、期待値反転、fixture hash 差し込み、揮発 payload の固定化は差分にない。

## must-fix

該当なし。受理集合または成果物の値を変える被覆欠落は静的検査では見つからなかった。

## should-fix

- 事象: C4 の wire 診断は成功した worker にしか効かない。worker 内 assert や例外では tuple が返らないため、失敗した wire が例外文に含まれる保証がない。
- 根拠: worker の検査は `orchestrator/tests/test_p3_autonomous_workload_trial.py:1885-1941`、wire の返却はその後の `:1942`、取得は `:1962-1964`。失敗した future では取得処理まで到達しない。
- 成果物影響: certified 選択、レポート、台帳の値と受理集合には影響しないが、変異失敗や flake の wire 特定ができず、裁定 C4 の診断目的を満たさない。

## nit

追加の nit はない。

## 変異の発火判定

- M1: KILLED。planner 記録への wire 混入は planner 一意性検査 `:1976` が殺す。
- M2: KILLED。coder 記録への wire 混入は coder 一意性検査 `:1977` が殺す。
- M3: KILLED。auditor `correctness_digest` の差異は除外 pointer 外であり、正規化後一意性 `:1979-1982` が殺す。
- M4: KILLED。`raw_variant == expected_variant` は同じ変異済み関数を使うため単独では恒真だが、32 variant 検査 `:1984` と secret `variant` 検査 `:1985-1995` が殺す。
- M5: KILLED。RAW projection では candidate label が raw variant と一致し、`:1928-1930` が殺す。build attempt ID 混入時は `:1939-1941` も殺す。
- M6: KILLED。injected drive の `do_build=True` は `:1885` が殺す。
- M7: KILLED。任意 role の二重記録は各 worker の `len(payload_bytes) == 1`、`:1916-1918` が殺す。
- M8: KILLED。critic を先頭1件だけ append すると `len(sink_bytes["critic"]) == 32`、`:1973` で赤になる。これは critic 横断 assert `:1983` より前であり、1件で恒真になる問題を確実に遮断する。
- M9: KILLED。`:1962` が map iterator を消費し、worker 例外を捕捉する処理はない。context manager は終了待ちを行うが例外を抑止しないため、`:1970` 以降の横断 assert へ到達しない。

## scope 外の real 所見

- 対象 node は `report["status"] == "complete"` を検査せず、`:1920` で直ちに先頭 generation を読む。partial report を完全走として扱いうる既存問題であり、裁定 §6-4 の再裁定候補である。
- `_AUDITOR_D_POINTERS` は `:1729` に定義されるが exact 集合を pin する assert がない。D 集合の意図しない拡張をこの node 自身では検出できない。裁定 §6-3 の scope 外事項である。
- 逐次時だけ wire を混ぜる欠陥が決定的には捕まらなくなる点は real だが、裁定 §1 で明示的に受容済みであり、本 wave の修正対象ではない。

## 総括

C1〜C3、C5、および旧来の被覆 assert は保持されている。  
64回の production live closure capture は維持され、減ったのは test helper の recorded-head binding 計算だけである。  
M1〜M9 はすべて赤になる静的経路があり、M4 の単体比較だけが恒真でも後段検査が殺す。  
blocker はないが、C4 は worker 例外時の wire 診断を実現できていない。  
pytest は指定どおり実行していない。