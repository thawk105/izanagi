# T-2000 brief

- scope: 現行 `buildcache.build` と `buildcache.build_v2` を変更せず、Pegasus の同一 compute node 内で paired cold build を行い、取得経路・成否・wall・外部 network 依存を比較する。
- scope 外: build 呼出しの移行、admission/正しさ gate の緩和、汎用 dependency transport/cache、正式性能値、次 wave の実装。
- 確定裁定: D1217/D412 に従い変更前に測る。キュー混雑だけでは投入を止めない。後続変更が必要でも D95 Codex author の別変更単位へ返す。
- 不変条件: 同じ CCBench commit、同じ genome、trace-disabled、同じ compiler、同じ依存 pin 3 本、同じ node、fresh cache miss を arm 間で固定する。
- 不変条件: legacy/v2 の本番関数と site gate を通し、mock/monkeypatch や CMake の直接模倣を裁定根拠にしない。
- 不変条件: legacy network arm が取得した 3 source の HEAD を policy pin と照合し、v2 は検証済み永続 cache の private copy を `FETCHCONTENT_SOURCE_DIR_*` で供給する。
- 不変条件: 規律1/2を緩めない。probe は trace-disabled build のみで、correctness/certification/性能優劣を主張しない。
- 成果物: 再現用の T-2000 専用 pytest probe、raw JSON、比較 digest、移行/現状維持の裁定材料、worklog fragment。
- 実測環境: `tools/run_tests.py --force-dispatch` から既存 `tests` dispatcher を 1 回起動し、1 pytest process 内で全 arm を順次実行する。
- 最小 arm: legacy + proxy、legacy + proxy 無効、build_v2 + source-dir + proxy 無効。network 依存は「proxy 無効で失敗し、同一 pin の proxy arm は成功」の組で観測する。
- wall: 各 arm の production build call 全体を monotonic clock で測り、失敗 arm は失敗までの wall と stage/cause を記録する。異なる transport の wall は診断値で、性能評価へ流用しない。
- 既存被覆: D412 は SOURCE_DIR 無しの floor 型 configure/build 成功 5.520 秒を示すが、legacy 対 build_v2 の同一 node paired 比較ではない。
- 既存被覆: D424 は job-local `FETCHCONTENT_BASE_DIR` を採り SOURCE_DIR を渡さない。現行 build_v2 は 3 本の SOURCE_DIR seam を持つが legacy は持たない。
- (P1) compute node では proxy 無効の legacy が外部取得段で失敗し、source-dir v2 は成功する。親の provisional 裁定であり段2/3の攻撃対象。
- (P2) production `build()` / `build_v2()` を同じ prepared source/admission で直接呼べる最小 probe が成立する。親の provisional 裁定であり段2/3の攻撃対象。
- DW-G05: 未測定のまま移行すると build closure と依存 provenance を不要に変えうる。paired probe が無ければ「proxy が事実上必須」という T-2000 の前提を裁定根拠にできない。
- 分割: manager は brief/裁定/実走/記録のみ。read-only Codex で plan と異なる2レンズを取り、実装面は必要な場合だけ隔離 D95 author 1本へ T-2000 専用 probe を委ねる。
