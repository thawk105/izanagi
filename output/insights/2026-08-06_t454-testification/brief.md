# 段 1 brief — [T-454] テスト化 pass

repo: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification`
branch: `worktree-dev-wave-t454-testification` (base `616ef5db`)

## 背景 (実測済み)

- `docs/dev-wave/**` は 25,187 / 25,200 bytes (hard ceiling)。余白 13 bytes。
  個別 cap は core 8,534/9,600、workers 4,668/5,000、mutation 3,674/3,750、operations 8,311/8,400。
- 採録待ちの 4 件 (worklog (217)/(223)、inbox `2026-08-05-background-waiter-duplication.md`):
  - (a) 待ち手規約 3 条 — 1 条件 1 待ち手 / 生産者を止めたら待ち手も落とす / 待ち条件に生産者の死を含める
  - (b) `DW-O01` — 中断が残した `.done` を消さずに再投入すると前回分を完了と誤読する
  - (c) `DW-M05` — `pgrep -f` の照合語が待ち手自身に一致し、終了済み harness を実行中と誤読した
  - (d) `DW-M08` — kill は期待 node と実 node の完全一致判定である
- ユーザー裁定 (2026-08-06 /rulings): 「陳腐化規則の削除・テスト化で予算を空けて採録、
  入らない分だけ見送り」。**予算上限は上げない。**
- 本 wave のユーザー指示: 「削除実施と新 D 発効はまとめ裁定へ返す」。

## 段 1 前提実測 (親が実施済み、反証歓迎)

1. **(d) は既に機械強制 + テスト済み。** `tools/mutation_harness.py:1193` が
   `failed_keys == expected_keys` の完全一致で KILLED を決め、不一致は `MISMATCH` 終端になる。
   さらに `tools/mutation_harness.py:964-990` の collection preflight が
   「期待 node が pytest collection に実在しない」を fail-closed で拒否する。
   `orchestrator/tests/test_mutation_harness.py:330` (`collection に実在しない`) と
   同 `:348` (MISMATCH) が両方を pin している。→ **純増検出力ゼロ。**
2. **(c) の機械代替が存在する。** harness は `tools/mutation_harness.py:1814-1831` で
   repo ごとの lock file に `flock(LOCK_EX|LOCK_NB)` を取る。process 死で OS が解放するため、
   lock の取得可否が生死の権威になり `pgrep -f` は不要になる。現状 harness に生死 probe の
   subcommand は無い (`argparse` は `tools/mutation_harness.py:1859-` の単一 parser)。
3. **(a)(b) の機械代替は存在しない。** dev-wave の codex 子は `DW-O01` の
   `bash -c '<codex exec ...>; echo $? > <log>.done'` を素で組み立てており、実例は
   `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s3/{lensA,lensB}.done`。
   `tools/codex_worker_launch.py` は receipt 付きの別系統 (前景 bounded) で、
   `.done` 経路も待ち手も扱わない (`grep -n '\.done'` で 0 件)。

## scope

- **S1**: dev-wave 子の起動と待機を機械強制する tool を新設する。最低限
  (i) prompt 非空検査、(ii) 既存 `.done` の fail-closed 拒否、(iii) 同一条件の待ち手の重複起動拒否、
  (iv) 待ち条件に生産者 process の死を含める、(v) 完了判定を `.done` と exit code だけで行う。
  **本 wave 自身の段 3/5/6 の子起動で dogfood する** (`DW-G01` の生死確認と `DW-G04` の発火 path)。
- **S2**: `tools/mutation_harness.py` に lock ベースの生死 probe を足す。
  **本 wave の変異走行で dogfood する。**
- **S3**: S1/S2 の機械検査を pin する pytest を新設する。
- **S4**: `docs/dev-wave/**` の削除候補 (L2 × 発火実績なし × 機械代替済み) を列挙し、
  byte 会計と発火実績の反証検索結果を裁定パッケージにまとめる。**削除は実施しない。**

## 非 scope (明示)

- `docs/dev-wave/**` の本文編集。**本 wave では 1 byte も動かさない。**
- 新 D の発効。`docs/decisions.md` fragment は書かず、裁定パッケージへ返す。
- 予算上限 (`tools/check_docs.py` の `TextLimit`) の変更。
- (d) への追加実装・追加 docs。

## 不変条件

- 既存 gate を弱めない。テストの期待値を緩めない。
- `docs/dev-wave/**` の合計 bytes 不変 (25,187)。
- 実装子はコードとテストだけを編集し、docs 編集と commit をしない。
- 新 tool は既存 `DW-O01` 手順の**上位互換**とし、旧手順を壊さない
  (旧手順で起動済みの wave artifact を無効化しない)。

## 成果物影響 (`DW-G05`)

- S1 未実施: 残留 `.done` を完了と誤読すると、前 wave の子出力をレビュー結論として採用しうる。
  → insights の逐語と worklog の所見件数が実行と食い違い、裁定の根拠が別 wave の内容になる。
  出口なし待ち手の常駐は親の応答を通知で埋め、wave の停止判断を遅らせる (両方とも実害既発)。
- S2 未実施: harness 生死の誤読で走行途中の台帳を確定値として記録しうる。
  → 変異台帳の KILLED / SURVIVED 件数と、それを引用する worklog の値が誤る ((217) で誤読が発生)。
- S3 未実施: S1/S2 の義務が機械検査として固定されず、退行しても赤が出ない。
- S4 未実施: 予算が空かず (a) が docs にも機械検査にも入らない。
  → 待ち手 73 本常駐と同型の事故を止める正本が存在しないまま残る。
- (d): 影響なし (現状で既に機械強制 + テスト済み)。**見送りを提案する。**

## provisional 裁定 (親の暫定判断であり攻撃対象)

- **(P1)** ユーザー指示「削除実施と新 D 発効はまとめ裁定へ返す」を、
  「`docs/dev-wave/**` の本文を 1 byte も変えない」と読む。
- **(P2)** (a) 待ち手規約 3 条は docs 追記でなく、S1 の tool による機械強制で満たせる。
  よって採録に必要な bytes は「tool を指す 1 行」まで縮む (その 1 行の追記も裁定へ返す)。
- **(P3)** (d) は追加不要。
- **(P4)** S1 の tool は新規 file 1 本 + テスト 1 本に収め、既存 `codex_worker_launch.py` を
  改造しない (所有分離と回帰面の最小化)。
- **(P5)** 受入・実測は login node の `python3 tools/run_tests.py` 系で行い、
  全走は dispatch 経路を使う。変異は `tools/mutation_harness.py`。

## 分割方針

- 段 5 は 2 単位。U1 = S1 の tool + テスト (新規 file のみ)、
  U2 = S2 の harness probe + テスト (`tools/mutation_harness.py` と既存 test file)。所有は素集合。
- S4 は親が read-only で行い、codex レンズに反証させる。
