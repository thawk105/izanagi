---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-23
wave: dev-wave-t2847-mutation-run
seq: 1
---

## {{D:t2847-mutation-run-scope-and-firing}}. 検出期待表の新規変異は silo の 14 本を patch にして実走し、「盲点」と「未発生」を発火診断で分ける

**決定:**
1. 設計書 (`output/insights/2026-09-22/t2847-verifier-detection-design/README.md` §4) の新規 18 変異のうち、現 pin `e9e477ca` の上で期待を検証できる silo の 14 本 (変異 11・正しさを保つ対照 3) を D16 の out-of-tree patch (`patches/broken-silo-*.patch`・`patches/control-silo-*.patch`、`CCBENCH_` 外の裸マクロ 1 個の `#if` 枝) にして実走する。mocc の 2 本は X/P の emitter が pin C の計装の内容なので、si の 2 本は現行 parser が si の旧形式 trace を拒否して変異の有無に関わらず parse error になるので、走らせない。
2. 新 macro は既存の壊し patch と同じく条件 gate の許可ドメインに登録し、既存 driver の `s2_verify_calibration._broken_build_and_verify` (patch 適用・condition gate・commit 証人つき verifier) で build・実走する。判定基準・供給経路の処理は変えない。
3. 各 patch の有効枝に発火診断 (変異枝に入った回数・元コードと違う挙動を生んだ回数・その取引が commit した回数) を置き、process 終了時に stderr へ 1 行出す。verdict が serializable の行は、変異が挙動を変えその取引が commit したときだけ「盲点として certified」、そうでなければ「未発生」とする。診断は verifier の判定に使わない。
4. 期待・workload・job 分割・分類の規則は投入前に事前登録し、期待と違う結果が出ても patch・workload を事後に期待へ寄せない。直すのは patch が意図した機構以外を変えていることを source で示せる実装の誤りだけで、初回の結果も記録に残す。
5. trigger-misattr の既存 driver (`s8a_trigger_coverage.main()`) は misattr の build を admission (source digest) に通し、現行の source digest が裸マクロを未知マクロとして fail-closed で拒否するため走らない。source digest の防壁は緩めず、misattr の build だけを他の壊し patch と同じ直 CMake 経路 (condition gate は通す、admission は通さない) にした repo 外の起動器の手順で走らせる。run と checks は driver の関数と式のままにする。

**理由:**
- 検出表は「verifier が捕まえなかった」と「変異がそもそも起きなかった」を分けないと、盲点を過大にも過小にも数える。trace にも verifier にも現れない変更 (値・取引内の読み・TID 規則) は、変異側で数えるしかない。
- 壊し build が buildcache・admission を通らない規約は `_broken_build_and_verify` の docstring が既に定める。s8a の misattr build だけがそれに外れていた。
- 事前登録と事後修正の分離は、実走で V20 の実装の誤り (公開版の番号付けが持ち込んだ版順の逆転) を見つけたときに、初回の結果を消さずに直す根拠になった。

**却下した選択肢:**
- source digest の `CONTEXT_MACROS` に misattr の裸マクロを登録する — 壊し macro を identity の文脈に加えることになり、壊し build を admission に通さない規約と逆向き。
- 発火を verdict だけから推す — 盲点の行はどれも S なので、発火の有無を区別できない。
- si の 2 本を E のまま走らせる — 無改変の si と同じ parse error になり、検出表に情報を足さない。
