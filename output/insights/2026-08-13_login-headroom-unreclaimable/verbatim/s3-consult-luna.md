静的レビュー結論: 段 2 プランはそのままでは通せない。算術自体は妥当だが、既存の裁定・peak 台帳・サイト判定・実機測定の揺らぎを含めると、「実装すれば local 実行が通る」という結論は成立しない。pytest、変異実走はしていない。

## 実際に確認した consumer

- `orchestrator/campaign/login_headroom.py`  
  admission、grant、reservation、peak recall の本体。
- `tools/run_tests.py:1014-1113,1726-1831`  
  login admission、queue fallback、local/dispatch 判定、peak 記録。
- `tools/check_ai_provenance.py:1903-2020,2371-2501`  
  同じく provenance の admission と peak 記録。
- `tools/mutation_fanout.py:1286-1295,1571-1575`  
  `login_headroom.reserve()` の実 consumer。
- `tools/mutation_fanout.py:479-549` の `memory_current_bytes` は別系統の測定証跡であり、今回の `LoginHeadroom` とは別物。
- `buildcache.py`、S2/S3/S5/S8A は `site_policy.heavy_work_refusal` を先に使うため、今回の変更だけでは build の login admission は変わらない。

## 実機照合

`hostname` は `pegasus02`、UID は `31609`。対象の `/sys/fs/cgroup/user.slice/user-31609.slice/memory.stat` には、実際に次のキーが存在した。

- `file_dirty`
- `file_writeback`
- `slab_reclaimable`

実機の `memory.stat` は多数の追加キーを含み、各行は `key value\n` 形式だった。現行 parser は未知キーを無視し、順序と総キー数も要求しないため、fixture のキー数・順序の違い自体は例外原因にならない。一方、fixture の値の組み合わせは実機の意味を十分に再現していない。

## 所見 1: 正本の裁定と実装計画が衝突している

- 深刻度: blocker
- file:line: `docs/pegasus-runbook.md:351-365`、`docs/decisions.md:9932-9958`、`plan-out.md:9-85`
- 再現条件: プランどおりコードとテストだけを変更し、D209 と runbook を更新せずに wave を完了する。
- これを直さないと何が起きるか: 正本は依然として「判定量は raw `memory.current`」「file cache 減算は不採用」と記載されたままになる。実装、運用手順、将来の保守判断が異なるポリシーを指し、完了後もどの admission が正しいか確定しない。

これは単なる docs 漏れではなく、既存裁定を変更する scope である。親へ返す裁定パッケージに、D209 の supersede と runbook の更新を含めるべきである。

## 所見 2: 旧定義の peak を新定義に無標識で混ぜる

- 深刻度: must-fix
- file:line: `orchestrator/campaign/login_headroom.py:891-918`、`tools/run_tests.py:1465-1484`、`tools/check_ai_provenance.py:2323-2342`
- 再現条件: 既存の `.peak` ファイルを残したまま、判定量だけを unreclaimable に変更する。実機には旧形式の `tests-full.peak` が存在し、`peak_bytes=4294967296` だった。
- これを直さないと何が起きるか: `peak_bytes` は単位こそ bytes だが、旧記録は bounded child の raw charged `memory.current` peak であり、新しい `unreclaimable_bytes` ではない。新定義の判定に無標識で混ぜると意味の違う値を比較する。

親 brief の 12.32 GiB / 7.15 GiB を使うと、reserve 後の概算余力は約 4.85 GiBである。既存 `tests-full` peak に計画の 1.25 倍を適用すると 5 GiB となり、unreclaimable が減っていても dispatch になる。

peak を安全側の「scope raw current の予算上限」として残すなら、診断にその意味を明記するべきである。新定義の peak として扱うなら、metric/schema version を追加し、旧記録を拒否または再計測する必要がある。黙って混ぜてはならない。

reservation は `estimate_bytes` という追加予算なので、現行のまま「unreclaimable 観測量に加算する安全側の予算」と定義すればよい。ただし、その不変条件を診断と docs に明記すべきである。

## 所見 3: 前段 gate により、実装しても admission が変わらない経路がある

- 深刻度: must-fix
- file:line: `tools/run_tests.py:1702-1737,1811-1831`、`tools/check_ai_provenance.py:2398-2461`、`orchestrator/campaign/site_policy.py:30-84`
- 再現条件:
  - `--force-dispatch` を指定する。
  - bounded scope または dispatch exemption に該当する。
  - `--message-file` の provenance preflight のように admission を意図的に省略する。
  - qsub/qstat または `/opt/nec/nqsv` の証拠が無く、`pegasus0N` が `OTHER` と分類される。
  - queue が DIS/INA、または queue 状態不明のまま dispatch 経路に入る。
- これを直さないと何が起きるか: 前半は仕様上の bypass なので、unreclaimable 実装を変えても local admission は変わらない。特に site 証拠不足で `OTHER` になった場合は login admission 自体を通らず、local 実行へ進むため、実機分類の失敗がより重大である。

`--force-dispatch`、bounded scope、疑わしい site の heavy-work refusal はそれぞれ既存の意図された境界であり、今回の変更で除去してはならない。site 証拠不足時の分類は別裁定として扱うべきである。

また、build 系は `buildcache.py:1018-1033`、`orchestrator/campaign/s2_verify_calibration.py:235-243` などが先に heavy-work refusal を行う。今回の `login_headroom` 変更で build が local 化されると主張するなら、その主張は誤りである。

## 所見 4: P2 の required 縮小は、親の対案より運用上弱い

- 深刻度: must-fix
- file:line: `orchestrator/campaign/login_headroom.py:338-354`、`plan-out.md:46-58`、`handoff.md:88-92`
- 再現条件: `required` を現行の `{anon,file,shmem,file_dirty,file_writeback}` から `{anon}` に縮め、`file_dirty` などが欠けた環境で `memory.current` fallback を返す。
- これを直さないと何が起きるか: 現行はキー欠落で `None` となり dispatch だった環境が、変更後は観測成功扱いとなり、raw `memory.current` 判定で local を許す可能性がある。数値としては保守的でも、観測契約を緩めて欠落を隠す。

P2 の「fallback する値を raw current にする」こと自体は、非負の統計値が正しく取得できている限りメモリ量について fail-closed である。しかし「旧 required key の欠落を観測成功に変える」点は、運用上の fail-closed ではない。

親の対案、すなわち「現行 5 キーは required のまま、`slab_reclaimable` だけ optional。slab 欠落時は unreclaimable を unknown として raw current fallback」が妥当である。この実機では 5 キーも slab も存在するため、通常運用のコストはゼロである。

cgroup v2 の異なる kernel/configuration で各キーが欠落しうる具体的な組み合わせは、既存知識だけでは断定できず不確かである。そのためこそ、欠落時の degrade は保守的にすべきである。

## 所見 5: 診断は「何が原因で落ちたか」をまだ表せない

- 深刻度: must-fix
- file:line: `orchestrator/campaign/login_headroom.py:831-856,1055-1074`、`plan-out.md:78-85`
- 再現条件: raw current では余裕があるが unreclaimable と予約または peak を加えると境界を超える。あるいは slab 欠落で current fallback になる。
- これを直さないと何が起きるか: 運用者は、raw current、unreclaimable、予約、estimate、reserve、旧 peak、未知値のどれが dispatch 原因か判別できない。特に「実装後も local にならない」事象を queue や site の問題と誤診する。

少なくとも次を同一診断に出すべきである。

- raw `memory.current`
- 算出した unreclaimable、または unknown
- 実際の判定占有量
- 欠落キー名
- reserved、estimate、固定 reserve
- effective ceiling、required、available
- peak の metric/schema (`scope memory.current` など)

## 所見 6: fixture は parser 形式には合うが、算術と変異帰属には弱い

- 深刻度: must-fix
- file:line: `orchestrator/tests/test_login_headroom.py:34-44,86-98`、`plan-out.md:91-128`
- 再現条件: `_observation()` の固定値 `file=2, shmem=3, dirty=4, writeback=5` を使い続け、slab だけを追加する。
- これを直さないと何が起きるか: `file < shmem + dirty + writeback` なので、通常 fixture の clean file は常に clamp で 0 になる。clean cache 減算や dirty/writeback の扱いの変異が、実機に近い正の clean file のケースで検証されない。

変異ごとの静的判定は次のとおり。

- `memory.current` 判定へ戻す変異: 計画の明示ベクトル `current=1000,file=500,shmem=100,dirty=60,writeback=40,slab=50` を直接注入できれば殺せる。
- clean cache の減算を落とす変異: 同じベクトルでは期待値 650 に対し 950 になるため、明示注入できれば殺せる。
- dirty を回収可能側へ入れる変異: 同じベクトルでは期待値 650 に対し 590 になり、明示注入できれば殺せる。ただし、実機 brief の差が 24 KiB しかないケースを確実に殺すテストにはなっていない。

したがって、計画の算術テストを direct `LoginHeadroom` 生成だけでなく、`_observation()` の引数として file、shmem、dirty、writeback、slab を差し替えられる形にする必要がある。さらに dirty 24 KiB と dirty 0 を admission 境界に置き、local/dispatch が反転するテストを追加すべきである。変異実走はしていないため、現時点で「3 変異を殺せる」とは報告できない。

## 所見 7: 親の実測から local 通過を一般化できない

- 深刻度: blocker
- file:line: `handoff.md:24-29`、`orchestrator/campaign/login_headroom.py:409-425`、`tools/run_tests.py:1030-1067`
- 再現条件: 1 回の観測値 `memory.current=12.32 GiB`、unreclaimable 約 7.15 GiB だけから、実装後の全 local 実行を予測する。
- これを直さないと何が起きるか: admission は実行時の再観測、reserved、estimate、固定 reserve、旧 peak、queue 状態、site 分類に依存する。観測が変われば再び dispatch または no-execution になる。

read-only probe でも短時間に値が変動し、別 snapshot では `memory.current` が約 12.85 GB から約 10.68 GB、file と dirty も変化した。さらに `memory.current` と `memory.stat` は `login_headroom.py:409-425` で別々に読み取られるため、同一時点の原子的な組ではない。

支持できる結論は、「その snapshot、予約なし、peak の制約なし、対象 estimate が余力内、queue/site gate が許可する場合には local になりうる」である。「実装すれば local 実行が通る」ではない。親が実測する際は、必ず `tools/run_tests.py` または `tools/check_ai_provenance.py` の実経路で確認すべきである。

## 所見 8: mutation fanout の scope とテスト網羅が不明確

- 深刻度: must-fix
- file:line: `tools/mutation_fanout.py:1286-1295,1571-1575,1853-1872`、`plan-out.md:158-167`
- 再現条件: 対象テストだけを通し、mutation fanout の実 `reserve()` 経路や、別系統の certified `memory.current` 測定を検証しない。
- これを直さないと何が起きるか: shared な `_decision_locked` の変更自体は fanout に波及するが、fanout 固有の caller 契約、receipt、bounded scope、別測定証跡との整合は未検証のままになる。逆に build の local 化まで scope に含めると、実際には別 gate を変更していないため過大主張になる。

fanout を今回の admission policy の consumer として含めるなら、実 caller を使うテストを追加する。含めないなら、「login_headroom の共有判定を利用するが、fanout の certified peak policy は別裁定」と明示して scope 外に戻すべきである。

## P2 と運用判定

親の provisional P2 より、親の対案を採用する。

- 現行 5 キーは required のままにする。
- `slab_reclaimable` のみ optional にする。
- slab 欠落時は unreclaimable unknown とし、raw `memory.current` に fallback する。
- 現行 5 キーの欠落、malformed、overflow は従来どおり `None` として dispatch する。
- 診断には fallback の理由と欠落キー名を残す。

これは gate を緩めず、実機では追加コストがなく、未知環境では local を許す方向へ観測失敗を変えない。なお、実機の三キーが将来も常に存在することまでは、この静的確認だけでは保証できない。

## 総括

- blocker: D209/runbook が raw `memory.current` を正本としており、コードだけの変更では裁定不整合が残る。
- blocker: 単一 snapshot から「実装すれば local」と一般化できず、旧 peak・予約・queue・site gate が結果を変える。
- must-fix: 旧 raw-current peak を新 unreclaimable 判定へ無標識で混ぜない。
- must-fix: required 5 キー据え置き、slab optional degrade、診断強化、dirty 24 KiB 境界テストを追加する。