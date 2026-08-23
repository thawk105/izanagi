---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-23
wave: dev-wave-t1580-shard-default-pegasus
seq: 2
---

## {{D:shard-default-on-pegasus}}. 受入全走の shard 分割を Pegasus LOGIN の受入形で既定有効にし、K は login admission が dispatch を選んだときだけ 2 にする

**決定:** D710 の「既定は無効のままとする」を改訂する。`IZANAGI_ACCEPTANCE_SHARDS` が
未設定または空のとき、次をすべて満たす走行は **K=2** とし、満たさない走行は **静かに K=1** へ
縮退する (rc=16 で止めない)。

- 受入形である (`_is_acceptance_run`。`PYTEST_ADDOPTS` / `PYTEST_PLUGINS` が空を含む)
- site が Pegasus LOGIN である
- 外側 argv が空か `--force-dispatch` 単独である
- positional target が無い
- 内部 shard spec が無い
- **ローカル bounded scope の子でない**

明示 `1` は適格性によらず K=1 の opt-out、明示 `2` / `3` は不適格なら従来どおり rc=16 で止まる
(D710 の「黙って K=1 へ丸めない」保証は明示経路のものとして維持する)。

**既定の K=2 は login admission が計算ノードへ dispatch すると決めた場合にだけ効かせる。**
admission ブロックを迂回するのは明示 `2` / `3` と `--force-dispatch` だけとする。
CAP_OOM 後の fallback dispatch にも K を渡す。

**理由:**
- ユーザー裁定 (2026-08-23):「queue 待ちというのは基本あまり考えなくてよい」。
  D710 が既定無効の根拠にしていた「片方が毎回 queue 待ちを引くので総所要は負ける」は、
  設計制約として採らない。
- ただしこの裁定は **queue 待ちの長さを性能判断から外す**ものであって、
  「queue が停止していても投げる」でも「login の memory admission を無視する」でもない。
  分割経路が admission を迂回すると、queue 無効時にローカルで走れた受入が投げられなくなり、
  login の資源判定も外れる。**本決定が変えるのは「dispatch される走行を何本に割るか」だけで、
  「どこで走るか」は変えない。**
- 既定経路の不適格を rc=16 にしない理由は、既定経路は運用者が何も要求していない経路であり、
  ここで止めると焦点走・非 Pegasus 実行がすべて壊れるからである。
- bounded scope の子を非適格に含めるのは、ローカル実行の子が再び分割 dispatch へ入る再帰を
  断つためである。

**K=2 を選ぶ根拠 (速度最適ではない):**
- D710 の実測で K=3 の最遅 shard 143.92 秒は K=2 の 138.57 秒を下回らず、
  排他鎖 103.0 秒 + 固定費 12.86 秒の床に当たっている。K を上げても床は動かないまま
  request 数・queue skew・故障面だけ増える。よって **故障面の小さい保守的な初期値**として 2 を選ぶ。
- **「K=2 は 20〜30 秒速い」という一般化は取り下げる。** D710 は運用者が明示的に opt-in した
  少数走の観測であり、既定化後は時間帯を選ばない全受入が K=2 になる。D713 が禁じる
  「当該走の排他鎖を将来の硬い床にする」一般化に当たる。
- queue 待ち timeout (900 秒)、walltime、shard deadline (5100 秒) は変更しない。
  activation policy だけを変え、timeout は **未再測定の初期値**として据え置く。
  K=2 が期待値で有利になる単発失敗率の上限は概算 11〜19% 未満だが、この失敗率は未計測である。

**却下した選択肢:**
- 既定を K=3 にする — 床が動かないのに request 数と故障面だけ増える。
- 既定不適格を rc=16 で止める — 焦点走と非 Pegasus 実行を全部壊す。
- admission を迂回したまま既定化する — queue 無効時のローカル退避と login の資源判定という
  既存の配置契約を破る。2 レンズが独立に反証した。
- 受入 receipt へ shard 情報を足して land で検査する — 3 tool の受理条件を変える変更であり、
  別 ID が所有する独立の裁定を要する。**したがって receipt は今も K と gate 通過を証明しない。**
- 1 つの PBS request で 2 ノードを取る (`#PBS -b 2`) — queue 要求を 1 回にできる筋だが、
  現 dispatcher は 1 ノード・1 結果・1 ログを前提としており、別 wave の裁定対象とする。

**受容した既知の限界 (本 wave では直さない):**
- 適格判定の後に `PYTEST_ADDOPTS` を process 内で書き換える窓は残る。ただしこれを行えるのは
  `tools/run_tests.py` の import graph に既に入っているコードだけで、そこを取れる攻撃者は
  runner の rc を直接偽造できるため、既定化による権限の上乗せはない。
- login collection は `os.environ` の全複製で走り、compute 側は allowlist で走るため、
  collection を変える env が両側で食い違いうる。実測では `PYTHONPATH` が login にだけ存在し
  allowlist 外だが、D710 の K=2 実測走は gate 3 を通って `14383 passed / 96 skipped` で緑であり、
  現に発火していない。
- 共通 conftest や自動 plugin が集合を縮めた場合、gate 2 と gate 3 は同じ縮小集合へ同意する。
  これは K=1 にも同じくある canonical oracle 不在の限界で、既定化が新設する穴ではない。
- bounded scope の cgroup attestation が shard 拒否より先に走るようになった。rc はどちらも 16 で、
  成果物の値・受理集合・参照は変わらない。

## {{D:aggregate-no-verdict-attestation}}. 分割走で失われる no-verdict 自動再試行を、全 shard 未起動を証明できるときだけ集約 attestation で復元する

**決定:** 分割走の合成失敗経路で、次をすべて満たすときだけ外側 stderr へ
`IZANAGI_DISPATCH_OUTCOME_V1` 行を **ちょうど 1 本**出す。

- 親が保持する shard 結果に `child_started == True` が 1 件も無い
- 全 shard の `dispatcher.log` から marker 行がちょうど 1 本ずつ取れる
- その全 payload が `child_started == False` かつ `reason == "queue-wait-timeout"` かつ
  `child_rc is None`
- 走査した log が改行で終わっている (writer が途中で落ちた log を確定証拠にしない)

1 つでも満たさなければ **1 本も出さない**。成功走と gate 失敗走では出さない。

**理由:**
- `tools/dev_wave_wait.py` の `_retry_evidence_reason()` は受入ログ中の marker 行を数え、
  0 本なら `dispatch-attestation-missing` を返して**再試行しない**。marker を出すのは
  `tools/pegasus/dispatch_compute.py` であり、分割時は fork した shard worker の stdout / stderr が
  `shard-N/dispatcher.log` へ退避されるため、外側ログに 1 本も現れない。
- したがって既定化は、現行 K=1 が持っていた「queue 待ちタイムアウト + 未起動なら 1 回自動再試行」
  という回復を**全受入から奪う**。受入全走は wave あたり原則 1 回で、落ちれば全走をやり直す。
  分割で速くしながら回復性を落とすのは目的に反する。
- 再試行を許すのは「全 shard が確かに未起動」という**積極証拠**があるときだけとする。
  証拠が欠ければ出さない側へ倒すので、fail-closed の向きは保たれる。
- 親の `child_started` を条件に含めるのは、log 側の主張だけを信じると、実際には pytest child が
  起動していた走行を再試行して重複実行や既存 job との競合を起こせるためである。

**却下した選択肢:**
- 消費側 (`tools/dev_wave_wait.py`) を変えて shard log を読ませる — 受入 receipt と待ち手の
  受理条件を変える変更であり、別の裁定を要する。
- 常に marker を出す — 起動済みの走行を再試行させる。
- 何もせず自動再試行の喪失を受容する — 分割で速くする目的に対し、回復性の低下が相殺する。
- 同一 UID 敵対者を想定した log の fstat 前後比較・`O_NOFOLLOW`・regular-file 検査 —
  研究最優先・プロトタイプ基準の既定方針に従い見送る。
