# 段 1 brief — [T-816] 手順 4 (gitlink 前進 + trace v1 拒否化)

wave: `dev-wave-t816-step4` / branch `worktree-dev-wave-t816-step4` / 起点 main `23c8e7c4`
worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4`

## scope (ユーザー依頼そのもの)

1. `external/ccbench` の gitlink を `d706650cdb31e442bef45b9b4216951d4fb40969` →
   `511c9538e4e8efa54b45cda62e72389ed3b706ec` へ前進。
2. 承認定数 2 個を更新: `orchestrator/campaign/pin.py:CURRENT_PIN` ("d706650" → "511c953")、
   `orchestrator/campaign/s8b_approved.py:CCBENCH_FULL_SHA` (40 hex)。
3. verifier の trace 形式を **v2 必須**へ切り替える。v1 (5 token の `C`) を拒否し、
   v2 (`C <txid> <thid> <epoch> <tid> <read_count> <write_count>` + txn 末尾 `E <txid>`) を受理する。
   宣言件数と実 R/W 行数の不一致、`E` の欠落・重複は integrity 違反として verdict を
   indeterminate に倒す (FN-2 を閉じる本体。certified を偽で出さない = 絶対規律 2)。
4. `orchestrator/tests/test_verifier.py:642 test_characterization_txn_tail_loss_is_false_green`
   を反転する (FN-2 が閉じたので false-green ではなくなる)。
5. `tools/check_trace0_preprocess_identity.py` を **land 対象 tip** で
   `--old d706650… --new 511c9538…` で通す。
6. 変異事前登録に「v1 形式へ戻す変異」を含める。

## 確定済みユーザー裁定と、それを覆した新事実

- 手順 3 完了は一次控え `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-12-t816-step3-push-approval.md`。
  親が `git ls-remote` で remote 実在を実測済み (`refs/heads/izanagi-trace-t816-fn2` = `511c9538…`、
  `refs/heads/izanagi-trace` = `d706650` のまま、`c9c1a9c` は remote に無い)。
- **(N1)** `[T-837]` Q1 (a) の記録は「`511c953` を `c9c1a9c` の上へ乗せ直してから push」だったが、
  実際に push されたのは `d706650` を親とする `511c9538`。控えの mtime は裁定 01:08 < push 承認 01:16 で
  ユーザーの行為が後。**ユーザーの行為と本依頼を優先する。** 副作用 = `[T-167]` の `c9c1a9c` は
  remote に無く孤立し、次の pin 前進まで write-intent shadow は入らない (成果物影響: FN-2 の
  「同時欠落」型は本 wave 後も残る)。
- **(N2)** `[T-837]` Q2 (a) / `[T-838]` の記録は「SI も v2 化してから v1 を無差別拒否」。本依頼は
  今 wave での v1 拒否化。**親が実測した新事実**: 生きた verify 経路は `pipeline.py:1024` と
  `silo_ladder_rung1.py:2862` の 2 箇所だけで、build 対象は `cc/silo/ycsb_silo.exe` のみ
  (`silo_ladder_rung1.py:2211`)。**SI trace を verify する生きた経路は存在しない。**
  よって今日の受理集合の実損はゼロで、依頼どおり無差別拒否を実装する。
  成果物影響 = SI を将来 verify するには先に SI の v2 化が要る (`[T-838]` として残す)。

## 不変条件

- 絶対規律 2: 拒否側へ倒す変更のみ。**v1 を受理し続ける fail-open を作らない。**
  形式不明・件数不一致・`E` 欠落はすべて拒否側 (ParseError または integrity 違反)。
- 絶対規律 1: 変更は Python 側だけ。submodule のソースは 1 byte も編集しない。
- `test_s8b_approved` の「実 gitlink == `CCBENCH_FULL_SHA`、`CURRENT_PIN` はその prefix」は維持。
- 歴史的 pin (`dff0f1e` / `028f34d`) と、それを literal 保持する凍結 driver は張り替えない (pin.py 契約)。

## (P1)〜(P4) — 親の provisional 裁定であり攻撃対象

- **(P1)** 「承認定数 2 個」で閉じる。だが親は `silo_ladder_rung1.py:50 PIN`、
  `silo_ladder_rung1_contract.py:543 base_commit`、`test_p3_build_authority_cli.py:86
  _EXPECTED_REPO_STOCK_PIN`、`orchestrator/tests/s1_expected_goldens.py` など **d706650 を literal
  保持する箇所を他に 10 箇所以上実測している**。どれが「live な pin (前進必須)」でどれが
  「凍結 golden (据置)」かの分類が未確定。**ここが最大の未知で、段 2・3 の第一の攻撃対象。**
- **(P2)** v2 受理の実装位置は `orchestrator/verifier/parse.py` の `_parse_file`。`C` は 7 field で
  unpack、`E` は新 tag。件数照合は `E` を見た時点 (または `parse_trace_dir` 末尾) で行い、
  新 `ParseIssues` フィールド (framing 違反) 経由で `core.py` の integrity へ配線する。
- **(P3)** fixture 移行が本 wave の主質量。v1 `C` を持つ fixture は 16 ファイル / 11 ディレクトリ、
  `test_verifier.py` の `_tmp_trace(` 呼びは 28 箇所、ほかに `test_campaign.py` に trace literal。
  **すべて v2 へ移行する。** 「甘くして緑」ではなく、各 fixture の意図 (anomaly の形) を保ったまま
  正しい件数と `E` を付ける。
- **(P4)** gitlink の前進 (submodule pointer + `.gitmodules` 不変) は **親の git 操作**として行う。
  理由 = codex sandbox は network fetch できず submodule pointer を進められない。
  ソースファイルの編集 (定数・parser・テスト・fixture) は**すべて Codex `role=author` の実装子**が書く。

## 成果物の形

- コード: `orchestrator/verifier/parse.py` (+ 必要なら `core.py` / `model.py`)、`pin.py`、`s8b_approved.py`。
- テスト: `test_verifier.py` の反転 + v2 の正例・負例 (v1 拒否、件数不一致、`E` 欠落)、fixture 16 本の移行。
- 検査: `tools/check_trace0_preprocess_identity.py` を land 対象 tip で 1 回実走 (`--cxx g++-12`、
  `--expect-paths cc/silo/transaction.cc`)。
- 変異: v1 形式へ戻す変異を含む事前登録 matrix。

## 並列分割方針

依存が一直線 (parser → テスト → fixture) なので **実装子は 1 本**。段 3 の敵対相談は
2 レンズ並列 (正しさ境界 / pin 閉包)。受理集合が変わり正しさ防壁に触るため軽量版にはしない。

## 環境

受入・実測は Pegasus login node (worktree 内)。計算ノードは不要 (ビルドは checker が
`g++-12` を login で使う。worklog 445 で実績あり)。
