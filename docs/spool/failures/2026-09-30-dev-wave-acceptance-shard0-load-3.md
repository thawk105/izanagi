---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-30
wave: dev-wave-acceptance-shard0-load
seq: 3
---

## 新規

### {{F:prewarm-copied-consumer-timeout}}. 受入 controller の先行構築が consumer 側の待ち上限を写し、consumer の無い shard を終了処理で赤にした [手順漏れ] [テスト代表性]

- 事象: md_6 wave で、controller が collection 中に T-080 共有 base を先に組む prewarm を入れた。prewarm thread は可視 output の写しの完成を、worker の consumer が使う既存上限 `_T080_VISIBLE_OUTPUT_WAIT_S` (180 秒) で待ち、超えたら例外を記録して session 終了時に送出した。同時刻対照の 2 走 (親が 12 shard job と変異 job を同時に流し Lustre が混んだ) で、T-080 consumer を持たない shard-2 の写しが 180 秒を超え、子 rc 1 と report の pytest_rc 0 が食い違って受入全体が `report-invalid` になった。段 3 相談の所見 3 (consumer の無い shard に新しい失敗経路を作る) を段 4 で real と裁定し、構築の失敗・hang は扱ったが、写しを待つ段の上限を consumer の値のまま残した。単体 test (小 builder・写しを即公開) と焦点走では写しが遅い状況を作らず、検出したのは実受入の対照だった。
- 根本原因: 性能のための先行処理に、consumer が「間に合わなければ自分の test を赤にする」ための上限を流用した。consumer 側では上限超過はその test の赤で済むが、prewarm は consumer の有無にかかわらず全 shard で走るので、同じ上限が受入全体の赤に化けた。
- 恒久対応: memory `prewarm-must-not-fail-consumerless-shards` (先行処理は前提の遅延・失敗では静かに終え停止 event で止める、consumer の無い shard で赤にならないことを test と混雑条件の実受入で確かめる)。実装側の修正は branch `worktree-dev-wave-acceptance-shard0-load` の commit 4258b0c76 (prewarm は写しを finish の停止 event まで待ち、遅延・失敗では構築しない。正例 `test_t080_shared_base_prewarm_stop_before_snapshot_is_quiet`) にあるが、実装自体は同時刻対照で land 条件を満たさず main へ入れていない ({{D:t080-base-prewarm-not-landed}})。
- 再発検知: 受入の shard が `report-invalid` で落ち、dispatcher.log の traceback が session 終了処理 (`_finish_*`) を指すとき。先行処理を足す wave は、consumer の無い shard で先行処理が遅延・失敗しても session が赤にならないことを test で固定する。

## 再発

### F171

- **再発: 2026-09-30** — md_6 wave の新設 test が `sys.modules[__name__]` (pytest が読み込んだ test module) の builder を差し替えたが、conftest の prewarm は `importlib.import_module("orchestrator.tests.test_s8b_oracle_driver")` で別の module object を引くので差し替えが静かに空振りし、本物の builder が走って新設 4 本が赤になった (焦点走 1)。同じ理由で「写しを待つ」test は待ちを外す変異でも緑になりえた (検出力なし)。fix で conftest が使う module object の builder も差し替える fixture を足し、変異 M2 が当該 test を赤にすることを確かめた。

### F1078

- **再発: 2026-09-30** — md_6 wave の計測 runner 用の子木 (`as0-u2`) で、Codex 子の終了後に gitdir の `index.lock` が 0 byte で残り、起動器の終端 commit が `worktree-commit: failed reason=add-all` (起動器 rc=3) で 3 回とも落ちた (子自体は natural_exit、出力検査 rc=0)。成果物は repo に入れない計測 runner なので commit せず job dir へ退避した。同じ wave の別の子木 (`as0-u1`) では 3 回とも commit できた。
