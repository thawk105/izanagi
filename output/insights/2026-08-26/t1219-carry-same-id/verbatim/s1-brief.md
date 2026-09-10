# 段 1 brief — [T-1219] worklog carry 検査の同一 ID 化 (D837 択 c)

## scope
`tools/check_docs.py` の worklog carry 検査を、参照先 entry の実在検査から
「参照先 entry の `### 次の一手` に**同じ ID** が在ること」まで強める。
実測済みの既存違反 4 件は既知違反台帳へ登録し、赤にするのは新規発生だけ。
編集面は `tools/check_docs.py` と `orchestrator/tests/test_check_docs.py` の 2 file に限る。
既存 archive・worklog 本文は 1 byte も変えない (凍結アーカイブ非接触)。

## 確定済みユーザー裁定
- D837 = 択 (c) 採用。択 (b)「実在検査に留める」は不採用と確定済み。段 4 で覆さない。
- 母集合が空でも緑になる件数だけの gate にしない。上限と期待母数を対で検査し positive control を付ける。
- 実装面のため Codex `role=author` が必須 (D95)。親は実装面を直接編集しない。

## 実測 (brief 前に確認済み、覆す新事実なし)
- 既存違反はちょうど 4 件。すべて `docs/archive/worklog-phase3-0731-77.md`、すべて参照先 entry (73)。
  `[T-208]` `[T-209]` `[T-210]` `[T-211]`。entry (73) の次の一手は T-177..T-206 を持つが
  T-207 以降を持たない (T-207/T-201 は (74) 参照で違反ではない)。legacy 形
  `- [T-NNN] 変わらず ((73) 参照)` である。
- 母集合: carry 参照 404,326 件、次の一手トップレベル項目 412,401 件、索引できた entry 957 件。
  **現行検査は target で collapse するので実質 957 件しか見ていない。** 母数の 0.24% である。
- コスト: 全 traversal 1 回 = 1.69 秒 / 23MB。baseline `check_docs.py` = 10.52 秒 / 157MB / rc=0。
- pin 閉包 (DW-O09): `tools/check_docs.py` に live な bytes pin なし。`codex_reasoning_ab.py` の
  TRACKED_HASHES は既に live と乖離した歴史 snapshot、`spool_fold.py` は fold 時の動的 closure digest。
  SELF_LIMITS に本 file は無い。凍結成果物の bytes は変わらない (DW-O09/O10 は成立しない)。
- 編集面重複: `tools/check_docs.py` を merge-base 比較で変更した稼働 branch は 0 件。
  worktree 未 commit で当該 file を持つのは `dev-wave-acceptance-parallel-dispatch` のみだが、
  その staged blob は main の現行 blob と同一 (既 land) であり実質重複しない。
- 族の独立 2 例 (DW-G03): F58 (ID 再利用で内容消失) と F79 (3 エントリ消失で 675 参照が宙吊り)。
  どちらも「存在検査は通るが内容は失われる」型。族一般化の条件を満たす。

## 既存被覆と純増検出力 (性質で検索)
- 既存 (a): `_validate_entry_universe` — carry の参照先 entry 番号が全域 universe に実在するか。
- 既存 (b): `check_transition` — **隣接**エントリ間で「前の ID が後続または見送り台帳に現れる」か。
  向きは前進のみ、対象は隣接のみ。
- **純増**: carry stub が**後退方向に任意の過去 entry を名指す**とき、その参照先に**同じ ID** が
  在るか。(a) は ID を見ず、(b) は後退参照を見ない。純増検出力は「参照先は実在するが別 ID を指す
  壊れた鎖」ちょうど 1 性質である。

## 不変条件
1. 既存 archive・worklog の bytes を変更しない。既知違反は台帳登録だけで解消する。
2. 既存テストの期待値を反転・緩和・skip・削除しない (F80)。
3. 母集合が空・部分でも緑にならない。`numbered_archive_input_complete` が偽なら
   現行の実在検査と同じく fail-closed で停止し、緑を返さない。
4. 既知違反台帳は「登録総数 = 固定値」と「登録項目ごとの観測数 = 期待値」を対で検査する。
   登録したのに観測されなくなった項目も赤にする (`KNOWN_PLACEHOLDER_DEBTS` と同型)。
5. 既知違反台帳の key は archive の再ローテーションで腐らないものにする。行番号と file path を
   同一性の key にしない (entry 番号は全域一意で universe 検査が保証する)。
6. 台帳への追加はユーザーの明示裁定のみ。子が新規違反を台帳へ足して緑化してはならない。
7. `check_docs.py` の総所要が baseline 10.52 秒から倍化しない (追加 traversal は 1 回まで)。

## 成果物影響 (DW-G05)
実装しない場合、`docs/worklog.md` と archive の「次の一手」の carry 鎖が別 ID を指したまま増え、
`/rulings` の裁定収集が参照解決に失敗して**裁定項目を取りこぼす**。F58/F79 では実際に
ユーザー裁定 6 件が正本から消えた。実装すると `python3 tools/check_docs.py` の受理集合が変わり、
新規の carry ID 不一致で rc=1 になる (既存 4 件は受理のまま)。

## 判断が割れうる前提 (親の provisional 裁定、攻撃対象)
- **(P1)** 既知違反台帳の key を `(carry を書いている entry 番号, task_id, target entry 番号)` にする。
  file path と行番号は key に含めない。
- **(P2)** carry 参照は現行の `dict[int, _CarryReference]` collapse をやめ、
  `(target, task_id)` 粒度で保持する。実在検査 (a) の挙動は変えず、後方互換にする。
- **(P3)** 「期待母数」の検査は carry 参照の実測母数に下限を固定して行う。
  下限は単調増加する量にだけ張り、腐らない値にする (具体値は段 2 で提案させる)。
- **(P4)** 参照先 entry の次の一手が索引できない (ID 導入前 archive で section 不在) 場合は、
  違反にせず**別の finding として区別**し、黙って通さない。
- **(P5)** positive control は最低 3 本 — (i) 新規 ID 不一致が赤、(ii) 登録済み 4 件は緑、
  (iii) 母集合が空/縮退したとき赤。加えて実 repo で rc=0 を保つ回帰。

## 成果物の形
- `tools/check_docs.py`: 検査の強化 + 既知違反台帳 (4 件) + 期待母数/上限の対検査。
- `orchestrator/tests/test_check_docs.py`: positive control と既知違反台帳の自己検査。
- docs: 段 7 で spool fragment (worklog / decisions は D837 に既決のため必要分のみ)。

## 並列分割方針
編集面が 2 file の単一機構なので段 5 の実装子は 1 本。段 2 プラン 1 本、段 3 敵対相談 2 レンズ並列
(sol = 検査の抜け穴・恒真化、luna = 台帳設計と腐敗耐性)、段 6 レビュー 2 本 + fix。
受理集合が変わるため軽量版は使わない (DW-C00)。

## 受入・実測環境
worklog は Pegasus を正本とする。受入全走は `tools/dev_wave_wait.py acceptance --lease-optional`
経由で計算ノードへ dispatch する。親の焦点走・単体走は login node で行う。
