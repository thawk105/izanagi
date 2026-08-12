## 契約別判定

- (a) 破壊あり。alpha は部分保留 module の既存 E 経路を止める。
- (b) 現案どおり fallback と bytes 比較を維持すれば破壊根拠なし。
- (c) golden 自体は編集面外で、A が正常なら維持可能。
- (d) `_HOLD_ROWS` を変更しなければ 30 entry pin は維持可能。ただし並行 wave の entry 追加とは衝突する。

## BLOCKER: sentinel の import 自体が test hold の解除口になる

根拠: `s2-plan.md:28-33,51-69` は `sys.modules` の `conftest` / `orchestrator.tests.conftest` に sentinel があれば即 return する。sentinel は conftest の import 時点で設定される設計である。実際の conftest は `conftest.py:41-75` で import 時に registry を読む。

失敗シナリオ:

```text
python3 -c 'import runpy, orchestrator.tests.conftest; runpy.run_path("orchestrator/tests/test_campaign_import_invariant.py", run_name="__main__")'
```

pytest session も collection hook も起動していないが、package conftest の import だけで sentinel が入り、guard は return する。既存 token 無しで `_run()` が held node を実行できる。

成果物影響: `growth_test_hold_inventory()` は 30 件のままなのに、未認可の direct runner が held node を実行する。受理集合、実行台帳、保留報告が再び runner 依存になる。

提案: sentinel は module import ではなく、実際の pytest session が有効化した opaque state にする。package conftest の事前 import を拒否する負例を contract test に追加する。

## BLOCKER: alpha は部分保留 module の正しい E 経路を先に遮断する

根拠: guard 挿入位置は `s2-plan.md:88-95` で、`pytest.main()` より前である。対象の実行部は `test_env_attestation.py:1359-1360`、`test_s8b_binding_driftguards.py:536-540`、`test_codex_reasoning_ab.py:4269-4270` にある。

失敗シナリオ: `python3 test_env_attestation.py` では、guard が先に実行されるため conftest の sentinel がまだ存在しない。`pytest.main()` は conftest を読む前に `SystemExit(2)` となる。brief の実測 `103 passed, 1 skipped` と `17 passed, 1 skipped` は、いずれも rc=2 に変わる (`brief.md:44-51`)。

成果物影響: certified の数値そのものより、二重 runner の受理集合と実行証跡が縮小する。既存の緑を「保留拒否」と誤分類し、report と台帳の runner parity が壊れる。

提案: P2 は beta へ戻すか、alpha を採るなら二重 runner 契約を明示的に変更し、README と acceptance scope を同時に改訂する。現 brief の provisional beta のまま実装へ進めない。

## MAJOR: README allowlist と plain runner meta-test が新挙動を表現できない

根拠: README は allowlist 対象を direct invocation の no-op と定義している (`orchestrator/tests/README.md:122-126`)。`test_ruleops.py:3452`、`test_s8b_holdout_freeze.py:1219`、`test_s8b_oracle_driver.py:4928` は EOF で、静的検索上 `__main__` と `pytest.main` がない。3 file は allowlist にある (`README.md:137,149,151`)。

一方、plan はこの 3 file にも top-level guard を置き、direct invocation を rc=2 にする (`s2-plan.md:93-106,154-158`)。

失敗シナリオ: `python3 test_ruleops.py` は従来の no-op ではなく refusal になる。しかし `test_plain_runner_coverage.py:35-41,60-86` は guard を見ず、no `__main__` かつ allowlist 済みとして緑のままになる。

成果物影響: plain runner の契約、allowlist、実行結果の意味が不一致になる。将来 `__main__` を guard 無しで追加しても、現 meta-test 単独では guard の存在を検査しない。

提案: held module を「通常 harness」「pytest-only no-op」「explicit token 無しでは refusal」の3分類として README と meta-test に追加する。guard を refusal signal として検査し、段 7 の記録だけで済ませない。

## MAJOR: A no-op 検査が自分で sentinel を作る

根拠: contract module は先に `orchestrator.tests.conftest` を import している (`test_growth_test_holds_contract.py:17`)。plan の A 検査はこの process で guard を直接呼ぶだけである (`s2-plan.md:195-199`)。また既存の collection 検査 (`test_growth_test_holds_contract.py:173-223`) は synthetic item に対する hook 検査で、実 module import ではない。

失敗シナリオ: top-level `conftest` への sentinel 結線が壊れていても、contract test 自身の package import で `orchestrator.tests.conftest` 側だけが有効なら A no-op 検査は通る。実際の pytest collection では held module が refusal する可能性が残る。

成果物影響: A の skip 受理集合、hold metadata、`test_real_repo_serialization.py:35-70` の held serial node の収集結果を緑と誤認する。

提案: 実 conftest を使う fresh subprocess で held node を collection し、rc=0、skip 1 件、refusal 無しを確認する。package alias を事前 importした process は A の証拠にしない。

## MAJOR: 並行 wave との論理衝突

根拠: plan は registry row を変更しない (`s2-plan.md:84-106`)。そのため `_HOLD_ROWS` 自体との同一 tuple の機械的衝突は現時点では見えない。しかし 30 entry pin は `test_growth_test_holds_contract.py:30-32,117-120` に固定されている。並行 wave の優先 land は brief にも明記されている (`brief.md:117-121`)。

失敗シナリオ: 並行 wave が entry を追加すると count、key digest、row digest が変わり、現 contract は赤になる。古い定数を維持して緑に戻すと、新しい hold を台帳から隠す。

成果物影響: hold inventory の count、key hash、受理集合、ユーザー向け保留台帳が不正になる。

提案: 並行 wave を先に land し、registry と contract pin を再読する。entry 追加を採るなら新 ruling と brief を確定してから digest を更新し、機械的 merge で 30 件を温存しない。

## MINOR: production hold は scope 外に残る

根拠: production hold は `freeze_verification_hold.py:14,16-38,54-65` の `HELD=True` と 21 check id で管理され、consumer は `s8b_holdout_freeze.py:876-888`、`s8b_oracle_driver.py:198-241` で参照する。env / CLI 解除口がないことは `test_freeze_verification_hold.py:92-97` が固定している。

通常の `--noconftest` はこの production hold を解除しないため、test runner と同型の bypass は静的には確認できない。ただし `HELD` は mutable global で、テスト側には `mock.patch(..., "HELD", False)` の release positive control がある。

成果物影響: production 側の 21 checks は本 wave 後も held marker のままで、exact bytes 検証済みとは扱えない。T-930 が production hold まで閉じたように報告してはならない。

提案: production hold の解除 authority と mutation seam は別 wave の裁定パッケージへ返す。T-930 では production 側に env を追加しない。

## P2 / P3

- P2: alpha は現行 E 契約を壊すため反対。beta か、明示的な契約変更が必要。
- P3: B の collection error rc=2、E の refusal rc=2 は fail-closed として妥当。module-level skip は rc=0 になり、bypass を成功扱いするため採らない。

## 実効性

guard 1 行削除時に名前を挙げられる赤は次のとおり。

- campaign guard 削除: proposed binding test の exact import/call assert、B の `returncode == 2`、E の `returncode == 2` が落ちる (`s2-plan.md:170-237`)。
- ruleops guard 削除: binding test と E の refusal assert が落ちる。
- 残る 6 file の guard 削除: plan 上は binding test のみが直接検出する。runtime の file-specific assertion はないため、A/B/E の実挙動まで検証したとは言えない。

## 総括

判定: STOP

最も危険なのは、package conftest の事前 importだけで sentinel が有効になり、pytest enforcement 無しで held test を実行できる点である。pytest は実行していない。