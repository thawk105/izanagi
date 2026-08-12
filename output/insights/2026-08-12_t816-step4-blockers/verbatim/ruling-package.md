# 裁定パッケージ — [T-816] 手順 4 が凍結証拠と衝突する (wave 停止)

```text
authority: dev-wave (背景 job) dev-wave-t816-step4 が段 3 敵対 2 レンズ + 親実測で起票 (2026-08-12)
branch: worktree-dev-wave-t816-step4 (起点 main 23c8e7c4、実装差分ゼロで停止)
性質: 絶対規律 2 (正しさゲート) と凍結成果物・proof chain に触る設計択一
一次資料: 同 job dir の s1-brief.md / s2-plan.md / s3-lens-a.md / s3-lens-b.md /
          measure-pin-advance.log
並走ガード: gitlink は d706650 のまま 1 bit も動かしていない。tree は clean。
```

## 0. 何が起きたか (要約)

依頼は 4 点 — gitlink 前進、承認定数 2 個、**trace v1 拒否化**、characterization 反転。
このうち **v1 拒否化と gitlink 前進の 2 つが、どちらも凍結成果物に衝突する**ことが実測で判明した。
裁定時点 (T-816 Q1〜Q3、T-837 Q1・Q2) には見えていなかった新事実である。
裁定パッケージ `output/insights/2026-08-11_t816-fn2-trace-v2/verbatim/ruling-package.md` の Q2 は
**SI だけ**を v1 拒否の障害として挙げていたが、実際の障害は SI ではない。

---

## Q1: v1 拒否化と、v1 のまま凍結された証拠をどう両立させるか (主問)

### 事実 (親が一次資料で実測)

- **git tracked の凍結 raw trace 4 本が v1 である。**
  `output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/correctness/traces/trace_0..3.log`。
  先頭行は `C 0 0 1 1` (5 token)。`git ls-files` で tracked を確認済み。
- **現行 verifier がこの実バイトを読み直す経路が生きている。**
  - `orchestrator/campaign/silo_ladder_rung1.py:2862` `validate_raw_bundle()` が
    `verify_trace_dir()` で再計算し、保存済み verifier JSON と exact 比較する。
  - `orchestrator/tests/test_silo_ladder_rung1_evidence.py:1061` が同じことをテストで行う。
    **つまり v2 専用化すると受入全走がここで赤になる** (静かに壊れるのではなく、赤で止まる)。
- これらの trace は `raw-manifest.json` に SHA-256 で pin されており、書き換えれば
  trace SHA → raw manifest → verifier JSON → evidence identity が連鎖的に変わる。
  **既に `all_pass=true` で certified された結果の proof chain を別物にする。**
- もう 1 つの生きた v1 生成経路: `orchestrator/campaign/s2_verify_calibration.py` は
  **歴史 pin `dff0f1e`** (`:62`) から `ycsb_silo.exe` を build して現行 verifier CLI へ渡す
  (`:260`, `:281`)。v2 導入より前の commit なので出力は必ず v1。
  `docs/phase3.md:282` が正本として指す再現経路である。
- SI (`cc/si/transaction.cc`) については、親は自動 campaign caller を発見できなかった。
  ただし公開 CLI (`orchestrator/verifier/cli.py:42`) は protocol を識別せず任意 trace dir を受ける。
  **SI は障害の主因ではない** — 主因は上記の凍結 v1 証拠と歴史 pin 再現経路である。

### 択一

- **(a) 親の推奨: 版識別を bytes 束縛で入れる二段構え。**
  現行 verifier は既定で **v2 専用 (v1 は拒否)** とし、FN-2 を新規 trace 全部に対して閉じる。
  例外は 1 つだけ — **`raw-manifest.json` に記録された SHA-256 と一致する bytes** に限り
  v1 reader を通す legacy 経路を設ける。「凍結証拠として登録済みの bytes だけが v1 で読める」
  という fail-closed な束縛なので、新しい trace が誤って v1 経路へ流れることはない。
  `s2_verify_calibration.py` は歴史再現 driver として同じ legacy 経路へ束縛する。
  - **利点**: 依頼どおり v1 を拒否でき、凍結証拠を 1 byte も書き換えない。
    例外が「登録済み hash と一致する bytes」に閉じているので受理集合の拡大が検証可能。
  - **代償**: verifier に版識別の層が 1 つ増える。実装量は本 wave で最大。
- **(b) 凍結証拠を v2 へ書き換えて 1 本化する。**
  trace 4 本を v2 化し、raw manifest・verifier JSON・evidence identity を再発行する。
  - **代償**: 既存 certified 結果の proof chain を書き換える。**親は推奨しない** —
    「歴史的な `all_pass=true` の証拠を別物へ差し替える」ことになり、
    絶対規律 2 の「正しさシグナルを後付けにしない」の精神に反する。
- **(c) v1 拒否化を延期し、本 wave では v2 受理 + framing 強制までとする。**
  parser は v1 と v2 の両方を受理するが、**v2 の C 行を見たら件数照合と `E` を強制**する。
  gitlink 前進後は silo の新規 trace はすべて v2 になるので、**実効的には FN-2 が閉じる**。
  凍結 v1 証拠と `s2_verify_calibration` はそのまま動く。
  - **代償**: 依頼の逐語「v1 拒否化」を満たさない。v1 形式の trace を後から食わせれば
    FN-2 は残る (fail-open が 1 本残る)。
    これは記録済みの `[T-837]` Q2 (a) / `[T-838]` の「SI も v2 化してから無差別拒否」と同じ方向。

**(a) を推奨する理由:** 依頼の目的 (FN-2 を閉じる・v1 を拒否する) を満たしつつ、
凍結証拠を 1 byte も触らない唯一の案である。例外の範囲が「既に hash で pin された bytes」に
限定されるため、受理集合の拡大が機械的に検証でき、絶対規律 2 を緩めない。
(c) は安全だが fail-open を 1 本残し、(b) は proof chain を書き換えるので採れない。

---

## Q2: gitlink 前進が無効化する校正・凍結 artifact をどうするか

### 事実 (親が実測)

gitlink と承認定数 2 個 **だけ** を前進させた木で、対象 5 ファイルを走らせた実測:
`10 failed, 76 passed, 1 error` (`measure-pin-advance.log`)。

- **赤 10 件はすべて `orchestrator/tests/test_s8a_trigger_sweep.py`。**
  原因は 1 つ — `output/env/linux-baremetal/calibration/s8a_trigger_freq_t48.json` の
  `ccbench_commit: "d706650"` を `orchestrator/campaign/s8a_trigger_sweep.py:151` が
  現行 `PIN` と exact 比較して拒否する。
- **error 1 件は偽赤** (`ModuleNotFoundError: No module named 'tests'`、DW-O18 の import path 未確立)。
- **`test_s1_known_axes_freeze` / `test_s1_measurement_freeze` / `test_frozen_artifacts` は緑のまま通った。**
  しかし `output/s1-freeze/known_axes_freeze.json` と `measurement_freeze.json` は旧 pin を保持し、
  前者は実 submodule HEAD (`s1_known_axes_freeze.py:868`)、後者は `pin.CURRENT_PIN`
  (`s1_measurement_freeze.py:429`) と exact 比較される。生きた呼び手は
  `s1_report.py:790` と `s8b_oracle_driver.py:429`。
  **つまりこの 2 つは受入全走では検出されず、実行時に初めて壊れる。**
  両 JSON は `test_frozen_artifacts.py:38 FROZEN_MANIFEST` (23 entry) に byte SHA で pin されている。

### 択一

- **(a) 親の推奨: TRACE=0 同一性を根拠に、校正・freeze artifact の pin 束縛を
  「d706650 と 511c953 は計測上同一」として明示的に許容する。**
  本 wave の checker (`tools/check_trace0_preprocess_identity.py`) は、
  **TRACE=0 の正規化 preprocess 出力と include 活性が旧/新 pin で同一**であることを機械証明する。
  性能・abort 頻度の計測は TRACE=0 ビルドで行うので、**この pin 前進は計測値を変えない**。
  よって校正 artifact を再測定せず、pin 束縛の側に「同一性が証明された pin 集合」を持たせる。
  - **利点**: 再測定 (計算ノード時間) も凍結 artifact の書き換えも要らない。
    checker が既に作られている目的そのものに合致する。
  - **代償**: pin 束縛の受理集合が 1 → 2 に広がる。同一性証明を伴わない前進では使えない
    (使わせない gate が要る)。
- **(b) 校正を再測定し、S1 freeze を再発行する。**
  - **代償**: 計算ノード時間 + `FROZEN_MANIFEST` の SHA 更新 = 凍結成果物の再発行。
    proof chain の参照が動く。
- **(c) gitlink 前進を Q1 の実装と切り離し、pin は据え置いたまま v2 対応だけ入れる。**
  - **代償**: 依頼の逐語 (gitlink 前進) を満たさない。新 pin の trace は手元に無いので
    v2 の実データ検証ができない。

**(a) を推奨する理由:** この pin 前進の差分は `cc/silo/transaction.cc` の `#if TRACE` 内だけで、
TRACE=0 のビルドは byte 単位で同一であることが機械証明されている。
「計測値が変わらないと証明された前進」で計測 artifact を捨てるのは、証明を持ちながら使わない選択になる。
ただし受理集合を広げる変更なので、**無裁定では実施しない。**

---

## この裁定で変わらないこと

- 絶対規律 1〜6。
- 現行 gitlink `d706650` と、それに束縛された既存の凍結成果物・certified 結果 (本 wave は未変更)。
- `[T-167]` の `c9c1a9c` は remote にも本 worktree にも存在しない (`git ls-remote` / `cat-file` で確認)。
  `511c9538` は `d706650` を親とするため、write-intent shadow は次の pin 前進まで入らない。
  → `[T-837]` Q1 の「乗せ直し」は実行されなかった状態のまま。これも合わせて確認されたい。

## 参考: 段 3 が挙げたその他の real 所見 (Q1/Q2 の裁定後に実装へ回すもの)

1. **負の txid で false-green certified になる** (レンズ A blocker)。
   `C -1 0 2 1 0 0` / `E -1` は `expected=max(txid)+1` の式で `missing=-1` となり違反が立たない。
   `txid >= 0` の構文検査と負例が要る。**これは今の v1 parser でも成立する既存の穴である。**
2. cycle と framing 違反が共存したときの verdict 優先順位が brief とプランで矛盾している。
3. X / I 行を件数に数える誤りが、既存テストでは発火しない (すべて元から `certified=False` のため)。
4. 直後でない重複 `E` が structured integrity にならず `ParseError` に落ちる。
5. fixture 16 本の移行ミスが緑で残りうる (全 fixture へ `framing_violations == 0` の固定が要る)。
6. `patches/README.md:356` の trace 形式記述が v1 のまま (Silo/SI 両方の入力契約と明記されている)。
