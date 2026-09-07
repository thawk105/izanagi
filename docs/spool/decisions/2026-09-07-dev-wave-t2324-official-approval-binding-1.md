---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: dev-wave-t2324-official-approval-binding
seq: 1
---

## {{D:floor-official-submitter-requires-approval-argument}}. 床値 official の投入器は実投入で承認引数を必須にし、job script は D926 の形を保つ

**決定:** D926 は「不一致 (空文字を含む) は build と driver より前に fail-closed で止める」を定めたが、
**承認 env が未設定の場合について何も定めていない。** 投入 script が固定 official になった以上、
承認なしの実投入は必ず driver 拒否で終わるので、この穴を次の層分けで閉じる。

- **投入器 `tools/pegasus/submit_floor.sh` は、非 dry-run で承認引数が無ければ拒否する。** 位置は
  argv 検証の直後、submission staging root の検査・`SUBMISSION_DIR` の作成・payload staging・
  claim root 作成・`qsub` のいずれよりも前。`--dry-run` は免除する。
- **job script `tools/pegasus/floor_campaign.sh` は D926 の形を literal に保つ。** 承認 env が
  未設定なら flag を渡さず (driver が拒否する)、設定済みで空文字または submission nonce と不一致なら
  build と driver より前に `submit_binding` で停止し、一致したときだけ driver argv へ承認 flag を
  1 個 append する。空文字と不一致は別の文言にする。

**理由:**

- 未設定のまま job を通すと、承認なしの通常投入が payload staging・PBS 投入・receipt 照合・
  割当予約・依存 build を消費してから driver で拒否され、しかも失敗記録の段が
  「driver が非 0」と誤分類される。段 3 の敵対レンズが独立に構成し、親が行順で検算した。
- 投入器で止めれば標準投入経路では何も消費されない。人間が引数を渡さない限り投入が成立しないだけで、
  flag の付与は job 側の nonce 一致に依然として従属するので、D461 が却下した
  「wrapper で無条件に承認 flag を渡す」には当たらない。
- job 側で未設定も止めると、標準経路では append が実質無条件になり、D926 が却下した
  「固定 official wrapper が承認を無条件 append する」と静的検査で見分けが付かなくなる。
  条件付き append を条件付きのまま保つ。
- 空文字と不一致を同じ文言にまとめると、輸送欠落・空値輸送・別 nonce 輸送を failure artifact から
  判別できない。文言を分ければ診断が識別可能になる。**ただし受理集合の歯にはならない** —
  承認値は 32 桁小文字 hex と検証済みの nonce と比較されるので、空文字は不一致分岐でも必ず拒否される。
- raw `qsub` で承認 env を省いた非標準経路は build を消費してから driver で止まるが、
  D461 / D926 がその経路を明示的に保証範囲外としているので機構を足さない。

**却下した選択肢:**

- **job 側でも未設定を fail-closed にする** — 上記のとおり append が実質無条件になる。
- **brief の不変条件を弱めて未設定を driver 拒否に委ねるだけにする** — 標準投入経路で
  確定した無駄と誤分類された failure artifact を作り続ける。
- **raw `qsub` 経路のために failure stage を精密化する** — 保証範囲外の経路へ機構を足すことになる。
- **`--dry-run` も承認引数を要求する** — 投入 interface の点検が承認を要求することになり、
  PBS を消費しない操作に承認の意味を持ち込む。

## {{D:floor-official-approval-gate-keeps-its-position}}. 床値 official の承認 gate は診断 env の取り込みより後の現在位置から動かさない

**決定:** `s8b_floor_campaign._assert_official_permitted` の呼出し位置を変更しない。
`floor_job_checkpoint.take_checkpoint_environment` が `os.environ.pop` を行う位置より後のままとする。
`orchestrator/tests/test_pegasus_floor_tools.py` の
`test_floor_driver_consumes_checkpoint_environment_before_core_dispatch` も変更しない。

**理由:**

- 前倒しが解決するのは「未承認 official の直接 API 呼出しで `os.environ` が pop されること」だけで、
  artifact も一回性 key も filesystem も動かない。拒否後は process が終わる。
- この pop は**計測される子 process に診断用 env を継承させない**ための無条件の隔離であり、
  上記テストが番人を 1 つ据えた 1 本の無条件テストで押さえている。gate を前倒しすると、
  このテストを承認状態で条件分岐する 2 本に割る必要があり、無条件の保証が条件付きへ弱まる。
- D926 が要求するのは「承認検証を claim 予約より後へ置かないこと」であり、現在位置は
  `campaign_claim.acquire_claim` と holdout observation reservation の両方より前である。
  既存テストが public 経路の書き込み 0 回を既に固定している。
- 段 2 plan と段 3 の 2 レンズはいずれも前倒しを妥当と判定したが、**3 者とも親 brief の
  誤った不変条件 (「副作用より前」) を基準にしていた。** 直すべきは不変条件の書き方である。
  正しい不変条件は「build 呼出し・driver 子 process 起動・cell claim 予約・一回性 key の消費・
  filesystem 書き込みより前」である。

**却下した選択肢:**

- **gate を `take_checkpoint_environment` より前へ動かす** — 上記のとおり無条件の隔離保証を
  条件付きへ弱める対価に見合う利得が無い。
- **診断 env の取り込み自体を承認後へ遅らせる** — 隔離の目的 (計測される子への継承を防ぐ) から
  すると、取り込みは早いほうが正しい。
