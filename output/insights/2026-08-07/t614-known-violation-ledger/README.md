# [T-614] provenance 監査の既知違反台帳 (案 3) — 実装 wave (2026-08-07)

裁定 = worklog (284)。案 3 (既知違反台帳) + `run_tests.py` の受入形でない走行への 1 行警告 +
受入条件「台帳導入前に、既定の全走が 6 違反を実際に報告することの検証」。
正本の材料 = `output/insights/2026-08-07_red-test-audit/README.md`。

計測 checkout = `.claude/worktrees/dev-wave-t614-provenance-ledger`
(branch `worktree-dev-wave-t614-provenance-ledger`、起点 `c9990bc2`、local main `a9159bac` を取り込み済み)。
submodule `external/ccbench` は初期化済み。実行環境は Pegasus。

## 結論

**6 SHA の固定台帳を実装し、監査は既知と新規を分離して rc を新規だけで決めるようになった。**
実装後も既定の全走は **rc=1** である。新規違反は `3f2c43d7` の 1 件だけで、これは裁定の 6 SHA に
含まれない。台帳へ入れることは**しなかった** — ユーザーが 2026-08-07 に同 commit へ
「今回だけ免除して land する。**防壁の恒久的な緩和はしない**」と裁定済みであり (worklog 285)、
台帳への追加はその恒久緩和にあたるためである。恒久的な処置は裁定パッケージで返す。

## 受入条件の検証 (台帳導入前、起点 `c9990bc2`)

| 走行 | 結果 |
|---|---|
| 既定の全走 `check_ai_provenance.py` | **rc=1、1660 件中 7 違反** — 裁定の 6 SHA を全部報告 |
| `--range 50c1ef4e..HEAD` | rc=1、1659 件中 7 違反 (既定と同一の finding 集合。差の 1 件は policy commit 自身で違反なし) |

**受入条件は「指定 6 SHA がすべて既定の全走で報告されること」として充足した。**
実測は 7 違反であり、「厳密に 6 件」という読みでは不成立である (段 3 レンズ 3 の指摘を採用)。

### T-300 退行説は refuted、ただし rc=0 の発生原因は unresolved

裁定文は「既定走行 rc=0 / `--range` rc=1 の不一致 (T-300 checker 改修後の疑い)」を挙げていたが、
本 wave では**再現しなかった**。

- 既定範囲は `policy(50c1ef4e) + --ancestry-path 50c1ef4e..HEAD` (1659) で、素の
  `rev-list 50c1ef4e..HEAD` も 1659。両者は同一の 7 違反・同一 rc=1 を返す。
- 段 3 レンズ 3 が `git blame` で範囲式が初出 commit `50c1ef4e` のまま不変であること、
  T-300 系 5 commit (`97ed862f` `743aae5f` `661de100` `498b191d` `4ede1299`) が範囲式を
  変更していないこと、裁定期の 5 commit で ancestry-path と素の範囲の件数が一致し
  checker blob も同一であることを確認した。

**したがって「T-300 の退行」は refuted で、本 wave に解消対象は無い。**
ただし rulings session が rc=0 を見た**原因は unresolved** である。当時の cwd・HEAD・実行経路・
生コマンドが保存されていない。「解消済み」とは記録しない。

## 実装したもの

### (A) 既知違反台帳 — `tools/check_ai_provenance.py`

- `KnownViolationSpec(commit, expected_finding_kind, ruling)` の frozen 定数 6 件。
  `ruling` は `worklog(284) 2026-08-07 /rulings`。7 件目の `3f2c43d7580b…` は含まない。
- finding は `NormalFinding(text, ledger_kind)` の単一列にした。**平行 tuple を作らない** —
  長さ不一致で新規違反が黙って落ちる失敗モードを構造的に消すため (段 3 の 3 レンズが一致して指摘)。
- 台帳の妥当性検査 (40 桁小文字 hex / SHA 重複なし / kind が閉集合内 / 裁定 ID 非空 / 各型) は
  **import 時ではなく history 分岐内の既存 `try` の内側**で lazy に行い、破損は rc=2。
  import 時に raise すると rc=2 契約が壊れ `--message-file` まで巻き添えになる。
- full SHA 完全一致かつ種別一致の finding だけを **entry あたり 1 件**既知にする。
  同種の 2 件目以降、別種 finding、別 SHA、短縮 SHA は新規に残る。
- **stale** = 台帳 SHA が selected set 内で期待種別の finding が 0 件。**rc=2** とする
  (新規違反には数えない — 裁定の「rc は新規のみで決める」を厳密に守るため。
  台帳の整合性破綻は provenance 違反ではなく監査機構自身の破綻である)。
  診断は `expected-finding-missing checker-regression-suspected` と
  `policy-epoch-not-visible non-authoritative-invocation` に分ける。
- 既知の SHA・種別・件数は **rc=0 経路と rc=1 経路の両方で stdout の末尾側**へ出す
  (dispatch 成功時に親へ戻るのは末尾 4 KiB のため)。既知 0 件のときの逐語は完全に不変。
- `--message-file`、forward correction (`PR-C01`〜`PR-C03`)、waiver の挙動は不変。

### (B) 受入形でない走行への警告 — `tools/run_tests.py`

`main()` の最初期 (site 判定・dispatch・bounded 再実行・3 preflight より前) で、
`_is_acceptance_run()` が False なら stderr へ 1 行出す。段 2 プランの「実行子側に置く」案は
**却下した** — dispatch 成功時に親へ戻る子 stderr は末尾 4 KiB だけなので、pytest の出力に
押し出されて手元から消えるという実測根拠があった (段 3 レンズ 2)。

bounded 子では、親が生成した**正規形式** (正の PID・16 桁 lower-hex・正の canonical decimal cap) の
marker pair を確認したときだけ抑止する。空・malformed・形式不一致では警告を維持する。
dispatch 子には一意な marker が無いため、親と子の各 1 行 (計 2 行) を許容する — 不可視より
二重表示を選んだ。経路別の行数は direct=1 / bounded=1 / dispatch=2 / bounded→dispatch=2。

受理集合、pytest argv、3 つの acceptance-only gate の順序と rc、終了 rc、suite fingerprint は不変。

## 段 6 で潰した欠陥 (レビューが無ければ land していたもの)

| # | 欠陥 | 誰が見つけたか |
|---|---|---|
| F1 | 台帳 validator の型破損が `TypeError` になり rc=2 契約が壊れる | レビュー 1 |
| F2 | **off-HEAD の部分 range で正常な既知 entry が偽 stale (rc=2)** | レビュー 1 |
| F3 | 変異 M1 (SHA 前方一致への退行) を殺すテストが無い — 生成 SHA が共通 prefix を持たない | レビュー 2 |
| F4 | 変異 M4 の control が恒真 (自分で台帳を空にしてから空を確認していた) | レビュー 2 |
| F5 | 裁定が明示要求した correction / waiver 合成テストが未追加 | レビュー 2 |
| F6 | 警告が bounded 子で二重表示 (既存 marker があるのに無条件出力していた) | レビュー 1・2 |

### F2 の fix が fail-open を作り、焦点再レビューが差し戻した

**本 wave で最も危なかった箇所。** F2 の 1 巡目 fix は「policy epoch が現在の `HEAD` から見えない
なら台帳 entry を stale 判定から外す」形にした。偽赤は消えたが、**checker の expected finding 生成が
壊れた場合に rc=0・known 公開なしで通る fail-open** になり、追加テストがその fail-open を
期待値として固定していた。焦点再レビューが `regressed` と判定し、規律 2 (正しさゲートを緩めない)
違反として差し戻した。

2 巡目で fail-closed へ倒し直した — **epoch の可視性にかかわらず常に stale rc=2** とし、
理由を 2 種に分けて診断する。偽赤側の指摘 (レビュー 1 所見 2) は、非権威な invocation での
過剰拒否として受け入れた。`PR-C03` が既に「権威は既定 full 監査か両 commit を含む range」と
定めており、degraded な走り方で rc=2 になるのは安全側である。

### 3 巡目 — 揮発値を焼き込んだテストを外した

2 巡目で追加された `test_default_history_reports_six_known_and_one_new` が
`assert len(stdout_lines) == 7` で赤になった。実際の stdout は 16 行 (waiver 8 行 + 集計 1 行 +
既知 6 行 + 集計 1 行) で、作者が waiver block を数え落としていた。しかし**行数を直さず削除した** —
このテストは実 repository の生きた監査結果 (違反件数・waiver 件数・特定 SHA) を期待値に
焼き込んでおり、無関係な wave が waiver を 1 つ増やすだけで赤になる。`DW-S05-C` の
「揮発する診断 payload を焼き込まない」に反する。台帳が実 6 commit に効くことは、実行場所にも
他 commit の増減にも依存しない `test_known_violation_ledger_matches_real_commit_findings` が固定する。

**「既定の全走が既知 6 / 新規 1 を返す」は観測値であって不変条件ではない。** 本 README と
worklog に実測として記録する。

## 実測一覧 (すべて本 worktree)

| 検査 | 結果 |
|---|---|
| 受入全走 `python3 tools/run_tests.py` (統合 + main 取り込み後) | **7131 passed / 20 skipped / rc=0** |
| 既定の全走 `check_ai_provenance.py` (統合 commit 後) | rc=1、1661 件中 **1 新規違反**、known-violations=6 |
| 同 (main 取り込み後) | rc=1、1670 件中 **1 新規違反**、known-violations=6 |
| incoming 範囲 `c9990bc2..a9159bac` の監査 | **rc=0、8 件・違反なし** (免除不要) |
| `python3 tools/check_docs.py` | rc=0 |
| provenance docs family | 8994 / 9000 bytes |
| 変異 matrix (9 件) | **SURVIVED 0**。KILLED 4 / MISMATCH 5、**全 9 件で登録 node が赤** |

**本 wave の commit は 1 件も違反に含まれない。** 監査の唯一の新規 finding は `3f2c43d7` である。

## 変異 matrix

spec = `mutation-spec.json` (sha256 `28d7a270e754d6f4a119c760de1f2cccadeed11e5509b0998038c8eaef60bd0a`)、
台帳 = `mutation-ledger.json`。runner は `tools/run_tests.py … -rf --force-dispatch`、
harness は `--runner-mode dispatch --detached`。

| ID | 変異 | 結果 | 登録 node が赤 | 追加で落ちた node |
|---|---|---|---|---|
| M1 | 台帳 lookup を full SHA exact から先頭 8 桁一致へ | KILLED | ✔ | 0 |
| M2 | finding 種別の一致検査を外し SHA 一致だけで抑止 | MISMATCH | ✔ | 1 |
| M3 | entry あたり 1 件制限を外す | KILLED | ✔ | 0 |
| M4 | 台帳を空にする | MISMATCH | ✔ | 13 |
| M5 | rc を「既知 + 新規」で決める (旧挙動) | KILLED | ✔ | 0 |
| M6 | 既知の stdout 公開を削る | KILLED | ✔ | 0 |
| M7 | stale 検出を外す | MISMATCH | ✔ | 2 |
| M8 | 非受入形の警告を削る | MISMATCH | ✔ | 11 |
| M9 | 受入形でも警告する | MISMATCH | ✔ | 1 |

MISMATCH はすべて**過剰検出** (登録した node は赤で、加えて別の node も落ちた) であり、
検出力の不足ではない。

### erratum — 変異本走の 2 回の中止

`mutation-ledger-run1-erratum.json` に初回を残す。いずれも harness の fail-closed が
正しく働いた結果で、変異の結果ではない。

1. **`--runner-mode dispatch` + 素の runner** — baseline が `PARSE_ERROR`。
   runner が targeted 走行をローカル実行したため receipt 行が 0 件で、harness が
   「receipt 表示行が exactly one でない」として production write を開始しなかった。
2. **`--runner-mode local`** — collection 段が rc=16。
   `run_tests.py … --collect-only -q` が bounded scope の cgroup attestation
   (`memory.max / memory.oom.group を走行中に attest できない`) で落ちる。

**2 は本 wave の差分と無関係である。** `DW-O19` の手順で `tools/run_tests.py` を
起点 `c9990bc2` の版へ一時的に戻して同じ collection を走らせ、**同じ rc=16** を実測した
(復元後 `git diff HEAD` は空、変異 anchor も 1 件で健在)。通常の targeted 走行 (`--collect-only` 無し) は
同時刻に rc=0 で 178 passed だったので、`--collect-only` 特有の既存条件である。

最終的に `--force-dispatch` を runner へ足し、dispatch 経路で baseline を緑にして本走した。
なお login ノードでの `python3 -m pytest` 直起動は hook が拒否したため、迂回していない。

## 裁定パッケージ (ユーザーへ返す — 本 wave では実装しない)

1. **`3f2c43d7` の恒久的処置 (P1)。** 台帳追加は「防壁の恒久的な緩和」であり、ユーザーが
   2026-08-07 に明示的に拒んでいる。よって本 wave では入れず、既定監査は
   **既知 6 / 新規 1 / rc=1** のまま残る。原因は判明している — trailer 自体は在るが
   `AI-Agent:` と `Co-Authored-By:` の間の空行で Git が trailer block と認識していない。
   選択肢: (a) 現状維持 (1 件の手作業帰属が残る)、(b) 台帳へ追加 (恒久緩和を撤回する再裁定)、
   (c) 別経路 (`PR-C01` は correction の再開放を禁止)。
2. **既定範囲の `--ancestry-path` 盲点 (P2)。** policy 導入前から分岐した branch 上の違反 commit を
   後日 merge すると、素の range には入るが既定監査からは落ちる。本 wave の実測では現に no-op
   (1659 = 1659) だが将来の穴である。素の `policy..HEAD` へ変えるのは strict な強化だが裁定外。
3. **監査結果を消費しない層 (P3)。** `dev_wave_land.py` は `--message-file` preflight しか
   呼ばず full-history を強制しない。`tools/dev_waves/cli.py` は stdout/stderr を `DEVNULL` に
   捨てて rc だけ保持するため、既知 SHA と件数が receipt に残らない
   (「公開が唯一の抑止」という契約がこの層で成立しない)。
4. **stale → rc=2 の是非。** 裁定は rc semantics を「新規のみ」と定めた。台帳整合性の破綻を
   rc=2 で赤にするのは裁定の文言を超えない範囲で入れた fail-closed 不変条件である。不要なら外す。
5. **テスト名一意性の repo 全体 meta-test (nit)。** レビュー 2 が提案したが、新しい gate の新設は
   未裁定で `DW-G03` の独立 2 例も無いため見送った。現時点で重複名は 0 件 (静的検査で確認)。

## 逐語

- `s4-adjudication.md` — 段 4 裁定 (所見 20 件の real/refuted、plan v2、変異事前登録)
- `verbatim/s2-plan.md` — 段 2 プラン
- `verbatim/s3-lens1-detection.md` / `s3-lens2-integration.md` / `s3-lens3-fidelity.md` — 段 3 敵対 3 レンズ
- `verbatim/s6-review1-implementation.md` / `s6-review2-tests.md` — 段 6 敵対レビュー 2 本
- `verbatim/s6-focus.md` — 段 6 焦点再レビュー (F2 の退行を差し戻した)

いずれも `tools/check_codex_output.py` rc=0。
