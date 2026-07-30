結論は NO-GO です。静的レビューのみで、pytest・mutation・編集は実施しておらず、green は主張しません。

差分前提は概ね成立しています。

- tracked diff は `orchestrator/tests/test_dev_waves_integration.py` だけで、author patch と完全一致
- production diff は 0 byte、staged diff なし
- `+291 / -24`、net は `+267`。したがって「291行純増」は正確には「291行追加」
- wave 成果物ディレクトリは untracked だが、別の実装ハンクではない

### B1 — blocker / real: sentinel 前後に無期限 hang 面が残る

`_ServeSelectProxy.wait_for()` は timeout なしです（`orchestrator/tests/test_dev_waves_integration.py:1261-1268`）。これを readiness、park、outcome、cleanup の4箇所から呼んでいます（`:1394-1398`, `:1415-1419`, `:1429-1432`, `:1463-1466`）。

具体的 interleaving:

1. main が thread を開始して `wait_for(LISTENER_BOUND, RETURNED, RAISED)` へ入る。
2. serve thread が `daemon.py:1591-1612` の profile永続化・lease・bind、または `:1614` の lease 検査で停止する。
3. select proxy に未到達なので trace は空、serve も return/raise せず、main は永久待機する。
4. `finally` に進めないため shutdown、release、thread回収、patch復元がすべて行われない。

mutation例は `daemon.py:1612` の直後に `threading.Event().wait()` を挿入するだけで再現します。さらに request handler を `daemon.py:1626-1637` で停止させれば、client の60秒 timeout後に cleanupへ入っても `:1463` の outcome待ちで再度永久停止します。

outcome観測後も `thread.join()` が無期限です（`:1475`）。`note_serve_returned()` が trace を通知した直後に thread が停止・starveすれば、sentinel到達済みでも受入全体が終了しません。T-137 の一次資料が明記する通り runner 全体の timeout はありません。

成果物影響: 固定 `join(120)` の偽赤を、受入結果・mutation台帳そのものを生成できない無期限 hang に置き換えています。

### MF1 — must-fix / real: daemon=False 変異が生存する

thread は `daemon=True` で構築されますが（`orchestrator/tests/test_dev_waves_integration.py:1380`）、その属性を検査していません。

具体的 mutation:

```python
threading.Thread(target=_serve, daemon=True)
# →
threading.Thread(target=_serve, daemon=False)
```

正常 shutdown では thread が回収されるため、trace、serve failure、join、patch復元はすべて同じでテストは通ります。M5 の期待する「daemon invariant 赤」は存在しません。段2 plan が要求していた start 前の `assert thread.daemon is True` も落ちています。

成果物影響: T-137 preservation の M5 が SURVIVE し、事前登録 mutation matrix を完了・認証できません。

### MF2 — must-fix / real: shape pin は過剰拒否と偽緑を同時に持つ

`_bind_or_validate_target_shape()` は最初の2要素を listener / relay と自己命名するだけです（`:1289-1305`）。実際の `SignalRelay` identity や、2要素が異なることを検証していません。

次の production mutationは target testを通過できます。

```python
select.select([bound.sock, relay.fileno()], [], [], 0.25)
# →
select.select([bound.sock, bound.sock], [], [], 0.25)
```

- proxy は両方を listener / relay として保存する
- request socket は ready なので real exchange は成功する
- `_observe()` は重複を捨てる（`:1255-1259`）
- shutdown は test が直接 Event を set するため、relay が poll から消えても最終 trace は一致する
- 一方、実 daemon の SIGINT/SIGTERM は relay pipe を監視しないため停止しなくなる

逆に、同じ意味の tuple 化や shutdown wake FD の追加は、`type(...) is list` と `len(readers) == 2`（`:1292-1294`）だけで偽赤になります。

成果物影響: signal shutdown を失った daemon を受理しつつ、意味等価または改善された poll 実装を拒否し、製品 daemon の受理集合不変を破ります。

### MF3 — must-fix / real: exact `0.25` は liveness 検出ではなく実装値 pin

`:1323-1327` は timeout が `0.25` と完全一致しなければ、最初の select で即失敗します。

- `0.25 → 0.1` は有限 poll と shutdown再評価を維持するのに偽赤
- `0.25 → 3600.0` は shutdown挙動へ到達する前に失敗するため、機能的 liveness kill ではなく diagnostic sensitivity pin
- `3 args` を一旦 shape として受け入れながら、後段で `None` timeout として別例外にするため分類も二段化している

M4 は `DW-M08` に従い functional KILL ではなく diagnostic pin と記録すべきです。有限性・許容上限を検査するなら、`0.1` 等の正例 mutation も必要です。

成果物影響: 正常な有限 poll 変更を受入集合から除外し、受入結果を production liveness ではなく非公開の実装定数へ束縛します。

### N1 — nit / real: 最小性を満たしていない

差分は +291/-24 です。8状態 Enum、6例外型、3 Event、Condition、trace、manual patch lifecycle が重複しており、制御状態と観測状態が二重管理されています。

単一の test-owned helper/context managerに、

- first-occurrenceではなく遷移を検査する Condition
- exchange/release の最小2 gate
- thread開始・shutdown・reap・patch復元
- 単一の typed failure＋reason

を集約すれば、同じ検出面をかなり小さくできます。行数自体は blocker ではありませんが、今回の無期限待ちと daemon assertion漏れを見落としやすくしています。

### refuted / conditional

- trace の happy-path順序自体は、現行実装については整合しています。listener select開始 → real exchange成功 → 次selectでpark → Event set → release → `serve_forever`正常return、という happens-before は `:1394-1444` で成立します。ただし重複を捨てるため「完全な一意 trace」ではなく、MF2の reader-role 偽緑を持ちます。
- early return は `_ServeParkNotReached`、`while True` は `_ServeLoopIgnoredShutdown`、Event set除去は `note_shutdown_set()` の primary failureとして、静的には狙った経路があります。いずれも未実走です。
- primary error保持、serve exceptionを第一失敗にする順序、thread回収後のpatch復元は、outcomeへ到達できる場合は正しいです（`:1374-1378`, `:1445-1494`）。B1 の hang時には保証されません。
- capability skip の誤記録という攻撃は refuted です。`s5-author.md:16-20` と `:44-45` は対象nodeの skipとreal roundtrip未実走を明記しています。ただし ad-hoc proxy probe は恒久テストではなく、GO証拠にはなりません。
- T-138 probeとT-136の定数・state/reason/side-effect assertionには tracked diffがなく、静的な弱体化は見つかりません。ただし preservation controlは未実走です。T-137だけはMF1で明確に弱まっています。

## 総括

- 判定: NO-GO
- fix必須:
  1. readiness/outcome/cleanup/join の無期限面を、runner-level containmentを含めて閉じる
  2. `daemon is True` assertionを追加しM5を殺す
  3. reader roleを実体へ束縛し、duplicate-listener偽緑を塞ぐ
  4. exact `0.25`・exact list shapeの過剰拒否を意味的契約へ縮める
- mutation前に必要な証拠:
  - capabilityのある環境で対象nodeが非skip PASS
  - final anchorの一意性と、外部ceiling下でpatch/thread/socketが必ず回収される fault probe
  - `daemon=False`、duplicate-listener、`0.1` finite timeout、tuple readers の正負 control
  - M1〜M7の旧版/新版 node・第一失敗・skip・timeout記録
  - T-136 PM1〜PM4とT-138正負probeの同一署名 preservation

現時点の非実走結果を green または KILL として記録してはいけません。