BLOCKER: fixture / parametrize の opt-in 経路が必須の実走条件を満たしていない

根拠: 段 4 は実走確認を必須としている `s4-ruling.md:66-67,123`. 実装は `functools.wraps` を使い `growth_test_holds.py:216-236`, 合成 fixture + parametrize 検査も追加している `test_growth_test_holds_contract.py:516-546`. しかし author 自身が未収集 rc=16 と報告している `s5-author.md:21-31,42`.

失敗シナリオ: installed pytest で fixture signature または `pytestmark` が期待どおり解決されない場合, exact token で解除しても held node が fixture error または parametrize 未展開になる. 静的には `__wrapped__` と `pytestmark` が保存される構造だが, 実走の代替にはならない.

成果物影響: 30 entry の `explicit-user-command` 解除契約が実際には利用不能となり, hold 台帳の release condition と実行事実が食い違う.

提案: 少なくとも `test_opt_in_runs_held_fixture_and_parametrize_shape` を親環境で実走し `2 passed` を確認する. 加えて実在する parametrized held node 1 件の collection を exact token 下で確認する. 成功するまで land 不可.

MAJOR: `103 passed, 1 skipped` は過剰拒否の検出力に不要な全 file 件数 pin

根拠: `test_growth_test_holds_contract.py:627-635`. 段 4 の事前登録にも同 literal がある `s4-ruling.md:84-86,98`.

失敗シナリオ: `test_env_attestation.py` に無関係な passing test を 1 本追加しただけで出力が `104 passed, 1 skipped` となり赤になる. skip の追加でも同様. wrapper の受理集合が正しくても並行 wave を拒否する.

成果物影響: acceptance の受理集合が T-930 と無関係な test 数に依存し, 正当な将来 wave が偽赤で land 不能になる.

提案: full file runner を維持するなら `rc == 0`, bypass prefix 不在, hold marker 存在, passed 数が 1 以上という意味契約を検査する. より局所的には合成 namespace に registered held 関数と non-held sentinel を同居させ, sentinel の identity と実行可能性が不変であることを検査する. M3 の検出力の核は non-held 関数が拒否されないことであり, `103` ではない. 段 4 literal の変更になるため親裁定で置換する.

## 契約別判定

- 二重 runner: 破壊なし. README 契約は `README.md:105-126`, 機械検査は `test_plain_runner_coverage.py:35-86`. 既存 `_run()` / `pytest.main()` と allowlist は無変更.
- conftest copy / plain-import fail-open: 破壊なし. fallback は `conftest.py:41-55`, bytes copy 契約は `test_pytest_failure_digest.py:542-550`. 両 file とも無変更.
- canonical serialization: 静的には破壊なし. wrapper は名前と marker を保存し, 既存 dict key への再代入なので collection 順も変えない. golden と順序検査は `test_real_repo_serialization.py:522-615` で無変更.
- 30 entry pins: count, key digest, row digest は `test_growth_test_holds_contract.py:37-39,124-127` のまま. `_HOLD_ROWS` と release condition も `growth_test_holds.py:65-160` で無変更.
- fixture / parametrize: 静的構造は妥当. 実在する parametrized held 関数は `test_codex_reasoning_ab.py:1013-1021,2345-2350`. ただし上記 BLOCKER の実走証拠がない.
- guard 忘れ: 機械検出できる. registry 由来 file 集合と top-level call を `test_growth_test_holds_contract.py:316-396,429-455` が検査する. 新 held file は literal 集合でも赤になる.
- 末尾 import: 8 file とも `# noqa: E402` があり, 段 4 指定どおり全 test 定義後かつ `__main__` 前. import 順による blocker はない.
- 並行 wave: entry 追加領域 `growth_test_holds.py:65-160` と新 API `growth_test_holds.py:212-271` は分離され, textual conflict は起こしにくい. entry 増加時に count / digest / held-file pin が赤になる semantic conflict は意図された再確認 gate.
- 報告一致: author の非変更主張は差分と一致する. 未実走も明記されており隠蔽はない. レビュー中に親側で同じ 10 file patch が `f4681b60` へ commit されたため現在の clean 状態は author 報告時点との矛盾ではない.
- scope: production, 新 env, CLI flag, 設定 file の追加なし.

## 総括

NO-GO.

最も危険なのは exact-token 下の fixture / parametrize 実行が必須条件であるにもかかわらず未実走な点. これを実測で閉じ, `103 passed, 1 skipped` の脆い literal を意味ベースの検査へ置換してから再レビューすべき.