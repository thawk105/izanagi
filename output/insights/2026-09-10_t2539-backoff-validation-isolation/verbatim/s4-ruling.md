# 段 4 裁定 — [T-2539]

## 親の誤りの訂正 (両レンズが独立に指摘)

`brief.md` が `docs/decisions.md:403` を **D2** と書いたのは誤りで、正しくは **D22**
(見出しは `docs/decisions.md:395`)。実際の D2 は 22 行目で、完全形式証明を scope 外とする決定である。
以後 D22 と呼ぶ。D22 が根拠に引く `transaction.cc:517-540` と `:154-157` は現在の submodule 実体と
ずれている (現在の validation は 383-493、no-wait 即 abort は 160-164)。
**D22 の参照更新は本 wave の scope 外**とし、裁定パッケージ候補へ送る。
本 checker は D22 の逐語より強い断定をしない。

## 所見の裁定

### レンズ A

- **A1 正例の全編集消費の証拠がない — real / 採用。** CMake leg だけで PASS でき、
  `include/backoff.hh` の編集を取り落としても負例は赤のままになる。これは正例側の恒真化であり、
  ユーザーが要求した「恒真でないことを示す」に直接反する。JSON へ `classified_edits` と
  `unconsumed_edits` を出し、正例で全 span 分類済み・未消費 0 を固定する。
- **A2 部分的過大閉包の対照が足りない — real / 採用。** 同じ `transaction.cc` 内の
  validation 非到達関数を触る **decoy PASS patch** と、`unlockWriteSet(iterator)` を触る
  **深さ 2 の FAIL patch** を足す。これで閉包が BFS で実際に歩いていることを固定する。
  **decoy と深さ 2 の patch は `patches/` へ置かず、test 内の tmpdir で生成する** (patches/ の
  bytes と構成は B-10 事前登録が pin しているため)。
- **A3 「純 timing」は判定式から導けない — real / 採用 (verdict 文言として)。**
  `Backoff::backoff()` 冒頭へ `throw 0;` を足す patch は closure と交差しないが純 timing ではない。
  verdict は「静的非交差」に限定する。副作用検査は新設しない (scope 外)。
- **A4 共有 header の全 owner TU への一般化 — real / 採用 (claim boundary として)。**
  `Backoff::backoff` の明示呼出しは CCBench 全体に 10 箇所ある。本 checker は Silo の root TU
  しか解析しない。JSON へ `owner_tus=["cc/silo/transaction.cc"]` を出し、他 protocol へ
  一般化しないことを明記する。他 protocol の解析は実装しない (依頼は Silo に閉じている)。
- **A5 root 不在 test が現 interface で作れない — real / 採用。**
  内部 `analyze(repo_root, patch)` を CLI から分離し、不在 root を渡す unit test を可能にする。

### レンズ B

- **B1 静的非交差 → 認証転用の飛躍 — real / 採用 (verdict 文言と報告の枠として)。**
  `Backoff::backoff()` は abort cleanup 後に呼ばれるので、待ち時間を変えれば次の transaction が
  読む版・lock 競合・validation の成功失敗の**系列**が変わる。コードが同一でも実行される
  判定の系列は同一でない。**したがって本 checker は「既存 1 group 認証を未実行 schedule へ
  拡張する licence」にはならない。** 補助根拠に留まる。これは worklog にもそう書く。
- **B2 checker は純 timing を証明しない — real / 採用。** A3 と同族。verdict 文言で閉じる。
- **B3 `commit()` 除外は狭すぎる — real / 採用は「境界の明示」まで。**
  `if (validationPhase() || true)` は closure と交差せず PASS になる。ただし
  `commit()` を V へ入れるのは「validation 経路」の定義を自然な読み (validationPhase と
  その呼び先) から変える行為であり、依頼の本題を超える。**V は下向き呼び先閉包のままとし、
  verdict へ「validation 結果の consumer は覆わない」と明記する。**
  V の拡張は裁定パッケージ候補へ送る。
- **B4 `writePhase()` 除外は狭すぎる — real / 採用は B3 と同じ扱い。**
  verdict へ「write/writeback の正しさは非保証」と明記する。V は広げない。
- **B5 D22 の識別子と行が stale — real / 採用済み** (冒頭の訂正)。D22 の更新は scope 外。
- **B6 `PASS` / `accepts` の語り口が規律 2 を弱めうる — real / 採用。**
  verdict 名を licence を含意しない語へ変え、非保証を機械可読 evidence に載せる。
  **実走で anomaly を検出した variant は本 verdict にかかわらず即 reject する**ことを
  出力と test の両方に書く。

### refuted (両レンズが自ら否定したもの、親も同意)

- 負例が patch 適用失敗で赤くなる疑い (3 patch とも `git apply --check` rc=0)。
- 負例が既定 OFF guard で消える疑い (raw branch を残す設計なので消えない)。
- sort comparator を閉包へ入れる判断 (妥当。lock 順序を決めるため)。
- patch 内容を指示として解釈する経路 (data として解析する設計)。
- 既存策だけで足りる疑い (`condition_meaning_gate.py` は動的到達性・正しさを証明しないと明記、
  `source_digest` は identity と許可 path の防壁)。

## brief の過剰制約の解除 (段 2 が返した未解決)

brief の「既存 file を変更するプランにしてはならない」は
`patches/*`、`orchestrator/campaign/condition_meaning_gate.py`、
`orchestrator/campaign/source_digest.py` に限る。
**新規 test file に伴う受入所要台帳への追記は必須であり scope 内である** (F902 が正本手順を定める)。
台帳は `python3 tools/update_acceptance_duration_ledger.py --add-only <実走 JUnit>` だけで作る。
手編集・推定値は禁止。台帳生成は実装面なので Codex `role=author` が行う。
段 6 の焦点走には `orchestrator/tests/test_acceptance_schedule_order.py` を必ず含める。

## プラン v2 (段 5 の実装対象)

段 2 プランを土台に、上の採用所見を織り込む。

1. `tools/check_silo_validation_isolation.py` — 段 2 プランの設計どおり。
   raw-config union の call closure (preprocess を使わず全 `#if` 枝を残す)、
   in-memory post-image mapping、implicit comparator edge、CMake macro の token 走査。
   加えて: `analyze(repo_root, patch)` を CLI から分離 (A5)、
   JSON へ `classified_edits` / `unconsumed_edits` / `owner_tus` / `claim_boundary` を追加 (A1/A4)、
   verdict 名を licence 非含意の語にする (B6)。
2. `orchestrator/tests/test_silo_validation_isolation.py` — 段 2 プランの node 群に加えて、
   decoy PASS (深さ非到達関数)、深さ 2 FAIL、未消費 0 の固定、claim boundary の固定を足す。
   自走 harness (`_run()` + `__main__`) を付ける。

## 変異事前登録 (DW-M01)

実装前に登録する。各変異は単一理由であることを実装後に確認する。
期待 node は probe (全件 SURVIVED) で観測してから確定する (DW-M07 / DW-M08)。

| ID | 変異位置 | 意図 | 期待 |
|---|---|---|---|
| M1 | closure BFS の探索を深さ 0 で打ち切る | 推移閉包が実際に歩いているか | KILLED (深さ 1 負例と closure test) |
| M2 | `std::sort` の implicit comparator edge を張らない | comparator edge の実在 | KILLED (closure test) |
| M3 | `unconsumed_edits` を常に空にする | 正例側の恒真化検出 (A1) | KILLED (正例 test) |
| M4 | `ERROR` の rc を 0 にする | fail-closed の実在 | KILLED (ERROR test 群) |
| M5 | closure を `transaction.cc` 全体へ広げる | 過大閉包の検出 (A2) | KILLED (decoy PASS test) |
| M6 | CMake macro leg を落とす | macro 検査の実在 | KILLED (正例 macro evidence test) |

## 不変条件 (再掲・段 5 へ継承)

- `patches/*.patch`、`condition_meaning_gate.py`、`source_digest.py` は不可触。
- 検査の入力は submodule 現物。fixture の古い snapshot を使わない。
- 既存テストの期待値を変えない。受理集合を広げない。
- 規律 2 は緩めない。anomaly を検出した variant は即 reject。
- gate 新設・他 patch への一般化・V の拡張・副作用検査は実装しない (裁定パッケージへ)。

## 裁定パッケージ候補 (ユーザーへ返す。本 wave では実装しない)

1. V を validation 結果の consumer (`commit()` の control edge) と `writePhase()` へ広げるか
   (レンズ B3/B4)。広げれば「correctness logic に触れない」というより強い主張が書けるが、
   「validation 経路」の定義が変わる。
2. D22 の行番号参照 (`transaction.cc:517-540`、`:154-157`) が現物とずれている件の更新。
3. 他 protocol (cicada / mvto / oze など 10 箇所) の owner TU への一般化。
