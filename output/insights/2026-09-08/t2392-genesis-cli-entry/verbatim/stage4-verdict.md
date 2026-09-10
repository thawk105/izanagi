# 段 4 裁定 — [T-2392] / D1775

## 裁定: **足す** (D1775 の主文どおり実装する)

D1775 の停止条件「既存の orchestrator / producer 経路で起点の commit・argv・入力・lifecycle が
記録されるか。記録されているなら足さない」は、**発火しない**。よって主文が効く。

## 所見の real / refuted

| # | 所見 | 判定 |
|---|---|---|
| P1 | 起点の **commit** は記録され、受入が強制する | **refuted** (段 3 sol が反例を提示、親が現物で確認) |
| P2 | 起点の **入力** は起点行に記録され、受入が突き合わせる | **real** (採用、正式 issuer 内では成立) |
| P3 | 起点後の **lifecycle** は production driver が記録し、受入が射影を再導出する | **real** (採用、正式 issuer 内では成立) |
| P4 | 起点の **raw argv** は記録されない | **real** (採用、ただし射程は下記) |
| P5 | よって停止条件が成立し「足さない」 | **refuted** (不採用) |

**P1 を refuted にした理由 (段 3 sol、親が現物で確認):**

記録されるのは「起点を**作った** commit」ではなく「起点 1 行の blob を**含む**任意の commit」である。
`_assert_attempt_registry_history_append_only` の全史走査は、blob が前 commit と同一のとき
strict-prefix 検査を掛けない (`if previous is not None and canonical != previous and ...`、
`s8c_acceptance_receipt.py:1898`)。`_blob_at_commit(root, prereg_content_commit, path)` も
P に genesis-only blob が在ることしか見ず、P が導入 commit かを見ない (1638 行)。

→ 反例: commit G が起点を導入 → registry を変えない無関係な commit K → K を `P` として使う。
receipt に残るのは K であり、実際の導入 commit G ではない。
**したがって停止条件は 4 項目中 2 項目 (commit を厳密に読む場合と argv) で偽である。**

**P5 を不採用にした理由 (段 2 と段 3 luna が独立に同じ結論):**

- 停止条件は 4 項目の**連言**である。実測は commit=真 / argv=偽 / 入力=真 / lifecycle=真 なので、
  例外の前件は偽であり、例外は発火しない。
- 親が段 1 で採った「既存 2 入口も argv を記録しないから argv は数えない」という読みは、
  裁定文に無い有効性条件 (新入口が不足項目を改善できる場合だけ数える) を後から足していた。
  「既存 2 入口と同じ層」は**追加先を指定する句**であって、記録項目の比較基準ではない。
- D1775 は「記録されていない場合に足さない」を明示的に**却下**している。
- 例外の適用が不確かなときに親の読みでユーザーの主文を上書きするより、主文を実行する方が正しい。

**P4 の射程 (記録に残す):** 記録されないのは raw な起動文字列だけである。作成器の意味のある引数
(`freeze_id` / manifest path / manifest hash / 全 slot / `prereg_generation` / 再試行可能理由) は
すべて起点行に残る。追加する subcommand も raw argv を保存しないので、**P4 は本 wave で改善しない**。
これは scope 内の事実として記録し、argv 記録機構は新設しない (D1769)。

## 段 3 luna が出した純増 (親が現物で裏取り済み)

`create_attempt_registry_genesis` は `manifest_sha256` を**独立した引数**として受け取り、
`_SHA256_RE.fullmatch` による**形式検査だけ**を行う (`trial_registry.py:2494`、
`_SHA256_RE = re.compile(r"[0-9a-f]{64}")` は 115 行)。manifest 本体を読んで照合しない。
起点は create-only の不可逆な成果物なので、食い違う hash を渡すと、誤りは受入まで検出されない。

→ **CLI が manifest bytes から digest を導出することが、本 wave の実質的な純増である。**
provenance ではなく入力構築の保証だが、実在する欠陥を作成時点で塞ぐ。

## 確定 plan v2 (実装子はこれだけを行う)

編集してよい path は次の 2 つだけ。

### (1) `orchestrator/campaign/trial_registry.py`

`main` に第 3 subcommand `genesis` を足す。既存 `register` / `accept` の引数・出力・意味は変えない。
help 上の順序は `register`, `accept`, `genesis` とする。

引数はちょうど 5 個。

- `--manifest PATH` (必須)
- `--repo-root PATH` (必須)
- `--freeze-id TEXT` (必須)
- `--prereg-generation INT` (必須、`type=int`)
- `--slots-file PATH` (必須。strict UTF-8 JSON の top-level array)

**`--manifest-sha256` は足さない。** manifest bytes から導出する (上記の純増)。
**`--registry` は足さない。** 正本 path 以外は既存 `_attempt_registry_target` が拒否するため。
**`--retryable-failure-reasons` は足さない。** 既存の閉じた既定集合を使う。

`args.command == "genesis"` の分岐を既存 `else` の前に置き、`create_attempt_registry_genesis` を
呼ぶ。出力は canonical JSON で `attempt_registry_path` / `manifest_sha256` / `slot_count`。

### (2) `orchestrator/tests/test_trial_registry.py`

**新しい test file を作らない。** 同 file は自走 harness (8201 行) と既存 CLI テスト (4915 行) を
既に持つので、ここへ足せば自走 harness 登録も受入所要台帳の新規行も不要になり、
main 取り込み時の台帳競合も起きない。

足すテスト:

- 正例: 妥当な manifest と、共通 `prereg_generation` を持つ slot 集合で `main(["genesis", ...])` が
  rc 0。正本 path に freeze 行がちょうど 1 行でき、**起点行の `manifest_sha256` が
  manifest bytes の sha256 と一致する**こと (導出の正例)。
- 拒否例 1: 同じ argv の再実行が create-only 違反で落ち、既存 bytes が不変であること。
- 拒否例 2: slot の 1 つの `prereg_generation` を `--prereg-generation` と食い違わせると、
  作成前に拒否され artifact ができないこと。
- 拒否例 3: `--slots-file` が JSON object / 重複 key / 非 UTF-8 / 非有限数なら拒否され、
  artifact ができないこと。
- 拒否例 4: 必須引数を 1 つ落とすと argparse が `SystemExit(2)` を出すこと。

## 変異事前登録 (DW-M01、実装前登録)

実装後に「同じ入力を拒否する層が前後にも内側にも無い」ことを各件で確認する。
確認できない件は登録から落とし、実効 gate へ再照準する。

- **M01**: `genesis` 分岐で、導出した digest を固定の形式妥当な定数へ差し替える。
  → 正例の digest 一致 assert が殺す。作成器は形式検査だけなので内側に拒否層は無い。
- **M02**: `genesis` 分岐で、`args.prereg_generation` でなく定数 `1` を渡す。
  → generation を 2 にした正例が殺す。
- **M03**: `--prereg-generation` を optional (既定値あり) にする。→ 拒否例 4 が殺す。
- **M04**: slots の decode を寛容な JSON decoder へ差し替える (重複 key / 非有限数を許す)。
  → 拒否例 3 が殺す。

## 不変条件 (実装子が破ってはならない)

- 受入 (`s8c_acceptance_receipt`、`assert_formal_attempt_registry_acceptance`) を弱めない。
- `output/s8c-preregistration/attempt-registry.jsonl` を本 wave で作らない。
- 凍結成果物の bytes を変えない。`trial_registry.py` に byte golden は無いことを親が確認済み
  (`test_paper_story_a1_paired.py` の literal goldens に同 path は無い)。
- C02 / C03 の静的形状要求は関数名ベースなので subcommand 追加では変わらない。
- 名指し外の gate・validator・検査・台帳・一般化を足さない (D1769)。

## scope 外の real 所見 (実装しない。裁定パッケージでユーザーへ返す)

段 3 sol が出した下記はいずれも real だが、受入契約または registry schema の変更を伴うので
本 wave の scope 外である (D1769)。段 7 で新規 T として記録し、ユーザー裁定へ返す。

1. 受入は「起点を導入した commit」を束縛していない (上記 P1 の反例)。束縛するかは設計択一。
2. standalone の receipt verifier は `prereg_effective_commit` が実在するか・P の直子か・
   measurement HEAD の祖先かを検査しない (正式 issuer だけが検査する)。
3. standalone verifier は lifecycle の意味を再導出しない。`_assert_git_history_append_only` は
   lifecycle JSON を parse せず、長さと hash を合わせた任意の非空 file を拒否できない。
4. standalone verifier は起点の `manifest_path` を receipt の `manifest_path` と比較しない
   (正式 issuer は比較する)。
5. `record_trial_terminal` は token を consumed にした後で ledger append を行うため、
   後段が落ちると start-only の行き止まりが残る。「driver が lifecycle を必ず閉じる」は恒真でない。
6. 起点 schema に作成時刻・実行者・実行 code 版の field が無く、exact-key 検査により追加もできない。
   **追加する `genesis` subcommand も、schema を変えない限りこれらを記録しない。**
   本 wave はこの穴を塞がない。塞ぐかは上記 1 と同じ設計択一に属する。

## 親が段 6 前に行う操作 (実装子の担当ではない)

`trial_registry.py` は A-1 の hash 済み source closure
(`paper_story_a1_paired.py:176` の `NON_CERTIFYING_SOURCE_RELATIVE_PATHS`) に含まれる。
**未 commit のまま焦点走・受入へ入ると contract-loader-drift で赤になる**ため、
実装子の編集後、親が焦点走の前に commit する。
