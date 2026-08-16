---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: dev-wave-t1268-scope-cap-page-align
seq: 1
---

## 新規

### {{F:mutating-the-runner-poisons-local-mutation-runs}}. 変異対象が test runner 自身だと local 変異走行が自分を壊して停止する [計測汚染] [手順漏れ]

- 事象: `tools/run_tests.py` の cgroup 検査へ変異を注入する matrix を
  `--runner-mode local` で走らせたところ、`M6` (page size を引く `os.sysconf` の key 誤記) で
  harness が `rc=16 だが canonical stdout から failed node を確実に抽出できないため停止` を出して中止した。
  テストは 1 件も走っていない。先行する 5 変異は、その target 集合の予算がたまたま page 整列
  (既定 4 GiB か下限 clamp) だったために通っていただけである。
- 根本原因: local 経路では runner 自身が変異後の `tools/run_tests.py` である。
  変異が runner の bounded local 受入判定を壊すと、runner はテストを走らせる前に
  `dispatcher infrastructure failure` へ倒れる。変異の効果が「テストの赤」ではなく
  「runner の自壊」として現れるため、kill を数えられない。
- 恒久対応: `docs/dev-wave/mutation.md` `DW-M07` の既存規律
  (本走は `--runner-mode dispatch` を既定とし runner argv へ `--force-dispatch` を入れる) に従う。
  `--force-dispatch` は bounded local 経路自体を迂回するので、runner は変異の影響を受けない。
  同節が local を避ける理由として挙げていた「同一 target set の 2 巡目以降で予算 attest が落ちる」は
  {{D:scope-cap-exact-or-page-floor}} で解消されるため、**恒久的な理由である runner の自壊へ書き換えた**。
  本 wave は probe を local で組んだ手順違反で 9 走ぶんを失い、dispatch へ組み直して 8/8 KILLED を得た。
- 再発検知: 変異対象 file が runner の実行経路 (`tools/run_tests.py`、`orchestrator/campaign/login_headroom.py`、
  `tools/pegasus/` 配下) に含まれるなら local を選ばない。`PARSE_ERROR` かつ
  `rc=16` の組は「テストが落ちた」ではなく「runner が走らなかった」と読む。

### {{F:page-size-detector-collapses-when-fixtures-share-a-floor}}. page size を parametrize しても cap の選び方で検出力が消える [恒真ゲート] [テスト代表性]

- 事象: page 丸めを検査する新規テストが `cap = 3 * P + 17` を使っていた。`P = 65536` のとき
  `cap = 196625` で、正しい切り捨て値 `196608` は **4096 での切り捨て値とも一致する**。
  そのため「`os.sysconf` の戻り値を無視して 4096 を固定で使う」誤実装が
  page-4k / page-64k の両 node を通過してしまう。境界 cap (`1`, `P`, `P+1`) でも同様に一致する。
- 根本原因: page size を parametrize したこと自体で区別できると考え、
  **cap の剰余が 2 つの page size で異なる**ことを確かめていなかった。
  剰余 17 は 4096 でも 65536 でも同じ位置に落ちる。
- 恒久対応: detector を `cap = 3 * P + P // 4 + 17` に変えた。`P = 65536` では
  64 KiB 切り捨てが `196608`、4 KiB 切り捨てが `212992` となり必ず食い違う。
  変異 `M7-run-tests-hardcode-4096` を matrix へ登録し、
  **page-64k 側の 10 node だけを落とす**ことを実測で固定した。
- 再発検知: page size や単位を parametrize するテストでは、
  「別の候補値で計算しても同じ期待値になる cap」を選んでいないかを、
  対応する固定値変異 1 件で必ず裏取りする。

## supersede 追記

- F362 **supersede: 2026-08-17** — 原因は特定され修正が land した。予算は `ceil(peak * 5/4)` で、`memory.current` ピークが page 倍数 `k*4096` なら予算は `k*5120` となり `k % 4 != 0` のとき page 整列しない。`rc=16` はピーク台帳を更新しないため、当該 target 集合は**恒久的に**走らなくなる (「確率的」ではない)。恒久対応は {{D:scope-cap-exact-or-page-floor}}。
