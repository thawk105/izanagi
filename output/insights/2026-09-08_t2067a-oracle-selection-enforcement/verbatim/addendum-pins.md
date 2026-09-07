# brief への追補 — 凍結 pin 閉包の補完 (親が独立の走査子と検算で得た)

段 1 brief の「凍結 pin の閉包」節は **byte hash 型の pin しか見ていなかった。**
独立走査で、対象 file には**構造 pin** (path 列挙・呼出し元集合・呼出し回数・guard 式・行番号) が
別に掛かっていることが分かった。以下を brief の同節へ足したものとして扱う。

## 1. 編集で確実に赤になる pin (再 pin が要る)

`orchestrator/tests/test_s8b_oracle_manifest.py` の `PIN_GATE_SPEC_RAW` (63–102 行) に
report / judge の source sha256 が literal で焼かれている。fixture
`_install_reviewed_spec_sources` (同 file:219) が **live の (編集後の) report.py / judge.py を
tmp root へ複製**し、`_validate_generators` (`s8b_oracle_manifest.py:458–498`) が
実 byte hash と literal を突き合わせるため、旧 literal のままだと不一致で赤になる。

赤になるのは少なくとも次の 2 node (親が現物で確認):

- `orchestrator/tests/test_s8b_oracle_manifest.py::test_reviewed_spec_has_independent_canonical_bytes_and_sha_literal` (1159 行)
- `orchestrator/tests/test_s8b_oracle_manifest.py::test_build_approved_valid_fixture_output_depends_only_on_spec_pin` (1367 行あたり)

`PIN_GATE_SPEC_SHA256` (63 行) はその blob の sha なので連動して更新が要る。
**F226 の実測前例**と同型であり、変異事前登録の期待 node には常にこの pin test 群を含める。

## 2. 今回の変更では赤にならないと親が検算した pin (子は「掛かっている」と挙げたもの)

いずれも「掛かってはいるが、今回の追加行では発火しない」。**実測ではなく静的読解による判断**なので、
実装後の焦点走・受入で実際に緑であることを確かめること。

- `orchestrator/tests/test_official_perf_closure.py:27` `_TRACKED_CALLS` —
  追跡する呼出し名の閉集合に `assert_g1_floor_selection_identity` は**含まれない**
  (親が現物で確認: build_perf_observation / evaluate / use_perf_from_receipt など 14 個)。
  よって `_REVIEWED_PREDICATES` の呼出し回数 Counter も動かない。
  ただし `_REVIEWED_PREDICATES` が数えるのは `_assess_window` / `_measurement_conditions` /
  `_combined_measurement_conditions` / `run_block` であり、**`main()` は対象外**である点も併せて根拠。
- `orchestrator/tests/test_official_perf_closure.py:44` `_REVIEWED_PERF_FILES` —
  path の exact 集合。file を増減・改名しないので動かない。
- `orchestrator/tests/test_official_perf_closure.py:266` `_REVIEWED_GUARDS` —
  `if` guard の式の literal 一致。今回 guard 式を触らない。
- `orchestrator/tests/test_s8b_oracle_manifest_contract.py:29` `VERIFY_EXPECTED_CONSUMERS` /
  `:16` `LOADER_EXPECTED_CONSUMERS` — `verify_manifest` と loader の**呼び手 file 集合**の完全一致。
  今回は呼び手を増やさず減らさないので動かない (親が 87–104 行で確認)。
- `orchestrator/tests/test_ccbench_spawn_sites.py:2899` — `s8b_oracle_driver.py` の
  **literal 行番号 1788** を焼いている。**driver.py は本 wave で編集しない**ので動かない。
  逆に言えば、もし driver.py へ 1 行でも足す設計へ倒れるなら、この pin が必ず赤になる。
- `orchestrator/tests/test_s8b_oracle_artifacts.py:252` — schema alias の AST 検査。
  トップレベル代入を触らないので動かない。
- `orchestrator/tests/test_env_contract.py:94` `V2_ENV_NEUTRAL_MODULES` — driver.py に
  env 固有 literal を持ち込まない限り動かない。

## 3. (P1) への追加材料

`verify_manifest` に選択 token を要求させる案を採ると、上記のうち

- `orchestrator/tests/test_s8b_oracle_manifest_contract.py::test_verify_manifest_public_and_seal_wrapper_signatures_require_approved_spec`
  (107 行あたり、`inspect.signature` で kwonly 引数を検査)

が signature 変更で赤になり、`VERIFY_EXPECTED_CONSUMERS` の 4 file すべてと
test helper 群 (`test_s8b_oracle_driver.py::_verify_manifest` ほか) の呼出しを直す必要が出る。
**これは (P1) の暫定裁定 (token 化しない) を支持する材料だが、決め手ではない。**
D1526 の「防壁の非対称を残す」という理由と突き合わせて段 4 で裁定する。

## 4. production 側の凍結成果物

`orchestrator/campaign/s8b_oracle_spec.py:23` の `APPROVED_SPEC_SHA256` は `None`。
`output/s8b-oracle-spec/reviewed_spec.json` も `output/s8b-oracle-manifest-candidates/` も存在しない。
`output/s8b-freeze/holdout_freeze.json` の `generator` field が焼くのは `s8b_holdout_freeze.py` だけで、
本 wave の 5 file は現れない。**production 側で有効な凍結 pin は現在ゼロで、
払うのは test 側 golden の再 pin だけ**という brief の結論は維持される。
