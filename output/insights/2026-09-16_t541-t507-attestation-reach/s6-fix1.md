## 直した内容

`_attest_fixture` が受け取った document の tolerance を `effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT` に揃えた。literal は追加していない。較正の検証と expected profile のハッシュ計算は代入後に行う。

帯の端は修正後の `verified.calibration.attestation_profile.effective_clock.tolerance_pct` から導かれ、直外はその端の `math.nextafter` で求められることを静的に確認した。

## 変更した file と行

- `orchestrator/tests/test_t126_qualification_driver.py:26`: policy module の import を追加。
- 同 file の263〜265行: fixture 内の tolerance を policy 定数に設定。
- `output/insights/2026-09-16_t541-t507-attestation-reach/s6-fix1.md`: 本報告を追加。依頼本文に `-o` の指定値がないため、指定された代替先に保存。

## 緑になる見込みの nodeid

赤から緑になる見込みの3件:

- `orchestrator/tests/test_t126_qualification_driver.py::test_t541_attest_accepts_matching_profile_with_v2_envelope`
- `orchestrator/tests/test_t126_qualification_driver.py::test_t541_attest_clock_band_boundary[endpoint-lower]`
- `orchestrator/tests/test_t126_qualification_driver.py::test_t541_attest_clock_band_boundary[endpoint-upper]`

緑を維持する見込みの5件:

- `orchestrator/tests/test_t126_qualification_driver.py::test_t541_attest_rejects_governor_mismatch`
- `orchestrator/tests/test_t126_qualification_driver.py::test_t541_attest_clock_band_boundary[just-outside-lower]`
- `orchestrator/tests/test_t126_qualification_driver.py::test_t541_attest_clock_band_boundary[just-outside-upper]`
- `orchestrator/tests/test_t126_qualification_driver.py::test_t541_attest_wraps_probe_exception`
- `orchestrator/tests/test_t126_qualification_driver.py::test_t541_attest_rejects_empty_comparisons`

## 実走できなかったもの

`python3 tools/run_tests.py orchestrator/tests/test_t126_qualification_driver.py -k t541 -v` は未実走。sandbox の preflight が rc=16 になるという前段の実測報告と job 投入禁止に従い、今回は再試行していない。親による実走が必要。

静的確認は `ast.parse`、`git diff --check` ともに成功。修正前のコピーとの比較で、今回のコード変更が上記 import と代入だけであることも確認した。

## 触っていないことの確認

今回、既存テストの期待値・共有 `_valid_document()`・policy 外 tolerance 拒否テストは変更していない。`t126_driver.py` の前段差分を保持し、`_attest` には触れていない。

`env_attestation.py`、`calibration_verify.py`、`env_contract.py`、policy 定数、較正 artifact、contract registry、比較 field 集合、全行 pass・非空要求は変更していない。揮発 payload の期待値への追加もない。

docs と `attest.sh` は未編集。commit・git add・ブランチ操作・job 投入は行っていない。

裁定へ返す候補3件（T-506 / D155 の loader 自己整合 gate、拒否時の比較行の保存・伝達、計算ノードで mismatch した場合の較正世代の扱い）は未実装。一次裁定は loader 自己整合 gate を同じ wave で扱うとしていたが、本 wave の引数が scope 外としたため、T-506 の carry は残る。

## 総括

実装済み・未実走。fixture の policy 不一致を修正し、受理3件と拒否5件が意図した比較条件へ到達する入力に揃えた。closed とは申告せず、実走結果の確認を親へ引き継ぐ。
