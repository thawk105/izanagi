# [T-816] 手順 4 — trace v1 拒否化と gitlink 前進が凍結証拠に当たった

```text
authority: none
default_effect: no-state-change
wave: dev-wave-t816-step4 / branch worktree-dev-wave-t816-step4
起点 main: 23c8e7c4
実装差分: ゼロ (gitlink は d706650 のまま 1 bit も動かしていない)
```

可変状態の正本は worklog 末尾と現行 phase doc であり、本 directory はその射影ではない。
裁定パッケージの一次控えは
`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-12-t816-step4-blockers.md`。

## 何が起きたか

[T-816] の手順 4 (gitlink 前進・承認定数 2 個・**trace v1 拒否化**・characterization 反転) を
実装しようとしたところ、**v1 拒否化と gitlink 前進の両方が凍結成果物に衝突する**ことが判明した。
裁定時点 ([T-816] Q1〜Q3、[T-837] Q1・Q2) には見えていなかった新事実であるため、
DW-STOP に従い段 4 でユーザー裁定へ差し戻した。

`output/insights/2026-08-11_t816-fn2-trace-v2/verbatim/ruling-package.md` の Q2 は
v1 拒否の障害として **SI (`cc/si/transaction.cc`) だけ**を挙げていた。実際の障害は SI ではない。

## 親が一次資料で実測した事実

1. **git tracked の凍結 raw trace 4 本が v1 である。**
   `output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/correctness/traces/trace_0..3.log`
   の先頭行は `C 0 0 1 1` (5 token)。`raw-manifest.json` に SHA-256 で pin されている。
   `orchestrator/campaign/silo_ladder_rung1.py:2862` (`validate_raw_bundle`) と
   `orchestrator/tests/test_silo_ladder_rung1_evidence.py:1061` が、この実バイトを現行
   `verify_trace_dir()` に通して記録済み verifier JSON と exact 比較する。
   **v2 専用化すると受入全走がここで赤になる。**
2. **歴史 pin からの再現経路が v1 を作る。**
   `orchestrator/campaign/s2_verify_calibration.py:62` は `PIN = "dff0f1e"` を固定し、
   そこから `ycsb_silo.exe` を build して現行 verifier CLI へ渡す (`:260`, `:281`)。
   v2 導入より前の commit なので出力は必ず v1。`docs/phase3.md:282` が指す再現経路である。
3. **gitlink 前進だけで 10 件が赤になる。**
   gitlink と承認定数 2 個 (`pin.CURRENT_PIN`、`s8b_approved.CCBENCH_FULL_SHA`) だけを進めた木で
   対象 5 ファイルを走らせた実測は `10 failed, 76 passed, 1 error`。
   赤 10 件はすべて `orchestrator/tests/test_s8a_trigger_sweep.py` で、原因は 1 つ —
   `output/env/linux-baremetal/calibration/s8a_trigger_freq_t48.json` の `ccbench_commit: "d706650"`
   を `orchestrator/campaign/s8a_trigger_sweep.py:151` が現行 `PIN` と exact 比較して拒否する。
   error 1 件は `ModuleNotFoundError: No module named 'tests'` の**偽赤** (DW-O18)。
4. **S1 freeze の破れは受入では検出されない。**
   `output/s1-freeze/known_axes_freeze.json` と `measurement_freeze.json` は旧 pin を保持し、
   前者は実 submodule HEAD (`s1_known_axes_freeze.py:868`)、後者は `pin.CURRENT_PIN`
   (`s1_measurement_freeze.py:429`) と exact 比較される。生きた呼び手は `s1_report.py:790` と
   `s8b_oracle_driver.py:429`。両 JSON は `test_frozen_artifacts.py:38 FROZEN_MANIFEST` に
   byte SHA で pin されている。**テスト 3 本 (`test_s1_known_axes_freeze` /
   `test_s1_measurement_freeze` / `test_frozen_artifacts`) は緑のまま通った。**
5. **pin 閉包は「承認定数 2 個」では閉じない。**
   `grep -rn "d706650" --include=*.py orchestrator/ tools/ hooks/` は 42 行 / 23 ファイル。
   段 2 の分類は A(前進必須)=23 / B(据置)=19。非 Python の `patches/ledger.json:10` も対象。
6. **`[T-167]` の `c9c1a9c` は remote にも本 worktree にも存在しない** (`git ls-remote` と
   `git cat-file -t` で確認)。`511c9538` は `d706650` を親とするため、write-intent shadow は
   次の pin 前進まで入らない。`[T-837]` Q1 の「乗せ直し」は実行されなかった状態のままである。

## 段 3 が挙げた、裁定後に実装へ回す real 所見

1. **負の txid で false-green certified になる (既存の穴)。** `C -1 0 2 1 0 0` / `E -1` は
   `expected = max(txid)+1` の式で `missing = -1` となり違反が立たない
   (`orchestrator/verifier/parse.py:213`)。**これは v2 化とは独立に、現行 v1 parser でも成立する。**
   `txid >= 0` の構文検査と負例が要る。
2. cycle と framing 違反が共存したときの verdict 優先順位が brief とプランで矛盾している
   (`orchestrator/verifier/model.py:205` は cycle を先に返す)。
3. X / I 行を件数に数える誤りが既存テストでは発火しない (すべて元から `certified=False` のため)。
4. 直後でない重複 `E` が structured integrity にならず `ParseError` に落ちる。
5. fixture 16 本の移行ミスが緑で残りうる。全 fixture へ `framing_violations == 0` の固定が要る。
6. `patches/README.md:356` の trace 形式記述が v1 のまま (Silo/SI 両方の入力契約と明記されている)。

## 逐語

`verbatim/` に段 1 brief、段 2 プラン、段 3 敵対 2 レンズ、裁定パッケージを凍結した。
