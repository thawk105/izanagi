# 段 6 レビュー所見の裁定 (fix 投入前)

両レビューとも **NO-GO**。所見を real/refuted・must-fix/scope 外へ裁定する。
親の追加実測を根拠に、レビュアの誤りも 1 件訂正する。

## 親の訂正 (レビュー 2 の事実誤認)

- **レビュー 2 §未走行の穴 / §consumer 波及 は走行済み file を取り違えている。**
  親が実走した 179 passed の 3 file は `test_s8b_holdout_freeze.py` /
  `test_s8b_oracle_manifest.py` / `test_s8b_ratified_freeze.py` である
  (`run_focus_tests.sh` の argv、job 901556)。
  **未走行なのは `test_s8b_oracle_driver.py` / `test_s8b_oracle_report.py` /
  `test_s8b_oracle_judge.py` と `test_plain_runner_coverage.py`** である。
  → レビュー 2 の「静的に赤 node は空集合」という結論自体は有用なので、
  **親が fix 後に実測して裏を取る**。

## must-fix (fix 子へ渡す)

| # | 所見 | 裁定 | 単位 |
|---|---|---|---|
| F-1 | **cell-product gate が holdout 全欠落を受理する** (R1-1 / R2-1 が独立に指摘) | **real・BLOCKER・採用**。期待積を schedule ではなく **freeze の全 holdout** から導き、`schedule_holdouts == set(freeze["holdouts"])` を先に要求する。holdout 欠落の negative test を足す | B |
| F-2 | **measurement_closure が HEAD blob でなく worktree bytes を採る** (R1-2) | **real・採用**。`_blob_at_head()` の bytes と worktree bytes の**完全一致を要求**し、不一致 (dirty) なら candidate を拒否する (fail-closed 方向)。現行の「worktree hash を採る」正例テストは拒否期待へ反転する | A |
| F-3 | **v2 専用 module の eager import が v1 の import 境界を変える** (R1-4) | **real・採用**。`env_contract` は import 時 validation と process-wide fork callback を持つため、v1 API の import 可否が v2 依存に従属する。**v2 関数内の遅延 import へ移す**。v1 API が v2 依存の import 失敗下でも動くことの regression test を足す | A |
| F-4 | **canonical bytes の assert が production serializer と自己参照** (R1-5) | **real・採用**。独立の raw bytes literal と独立 SHA-256 literal を置く (非 ASCII / key 順 / 末尾 LF を含む)。schedule hash は既に独立 literal なので対象外 | A + B |
| F-5 | **`-0.0` が budget として受理される** (R1-6) | **real・採用** (MINOR だが narrowing で安価)。負符号ゼロを拒否する。total / per-holdout 双方に negative test | A |
| F-6 | **MU-2 / MU-3 / MU-5 / MU-6 が単一理由でない** (R2-3) | **real・採用**。`DW-M01` に従い**実効 gate へ再照準**する。MU-2 = 固定 path 検査が先に発火し canonical namespace 分岐が到達不能 → **死んだ分岐を残さない形へ整理**し、実効 gate 側で登録。MU-3 = parent nofollow と leaf exclusivity の 2 変異へ分割。MU-5 = 二重 `None` gate を**一箇所へ集約**。MU-6 = 完全な valid spec fixture で行動差を見る | A + B |
| F-7 | **candidate の出力先 parent directory が実 repo に無く CLI が一件も生成できない** (R2-5) | **real・採用**。writer が固定 candidate root を**安全に作成**する (固定 path 限定・symlink 拒否を維持)。作れないなら機構が発火しえない | A + B |
| F-8 | **新 module が untracked** (R2-6) | **real・親が対応済み**。統合 commit `66ec0e0e` で `git add` 済み | 親 |

## scope 外 → 裁定パッケージへ (段 4 で裁定済みの再確認)

- **R2-2 (budget approval が ratified proof chain に残らない)**: real。段 4 で
  「transition table の変更を伴うため実装せず裁定へ返す」と裁定済み。**変更しない。**
- **R2-4 / R1 の関連 (reviewed spec が driver / report の trust chain に入っていない)**: real。
  段 4 で「manifest schema へ `spec_sha256` を伝播させる案は scope 拡大」と裁定済み。**変更しない。**
  ただし F-1 の holdout 束縛は choke point 側で閉じられるため fix に含める。
- **R2「誰も呼ばない機構」**: real だが既知。production 到達しているのは `verify_manifest` の
  cell-product gate だけであり、これは段 4 の裁定どおり。裁定パッケージへ明記する。

## refuted

- なし (すべての所見が real。ただし R2 の走行済み file の同定は誤りで、上記のとおり親が訂正した)。
