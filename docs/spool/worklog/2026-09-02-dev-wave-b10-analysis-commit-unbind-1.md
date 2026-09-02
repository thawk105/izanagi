---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-b10-analysis-commit-unbind
seq: 1
title: B-10 事前登録束縛から analysis_commit による再開拒否を外した — 検証器の意味の混在は既存の内容ハッシュ機構が既に塞いでいた (コード + docs、branch worktree-dev-wave-b10-analysis-commit-unbind、変異 4/4 KILLED)
---

## 本文

起点は entry 1186 の「ユーザーが束縛設計の欠陥を指摘し、実測で裏が取れた」節に別タスク候補として
残っていた項である。`PreregistrationBinding` に投入ツリーの HEAD (`analysis_commit`) が入っており、
`assert_resumable_binding` が完全一致を要求するため、**測定に無関係な commit を 1 つ打つだけで
分割走の再開が拒否され、完走済みのブロック記録まで棄却されていた。**

- **除去したのは commit 同一性による拒否 3 経路だけである。** `core()` の `analysis_commit`
  (束縛の完全一致比較と `binding_sha256` に流入)、過去ブロック記録の `analysis_commit` 照合、
  同じく `source_commit` を現行 HEAD と比べる照合。内容ハッシュ束縛は 1 つも外していない。
  `analysis_commit` の field 定義・形式検査・現行 HEAD の記録・レポート行・ブロック記録への
  書き出しは残した (規律 7 の「記録はやめない」)。
- **凍結された事前登録は要求していなかった。** 発効版 `docs/b10-backoff-shape-preregistration.md`
  (blob `ea910de32`) の §1 が列挙する束縛対象は「文書の blob SHA・その commit・patch SHA・式 SHA・
  spec SHA・解析コード SHA」で、解析コードの **commit は含まれない**。`registration_rules` の
  v4 閉集合も束縛 field に触れない。文書は 1 バイトも変更していない。根拠の裁定は D1253。
  D1059 が要求する「束縛の無い / 食い違う WAL は拒否する」は維持している。
- **段 3 の重大所見「検証器の意味が違う結果が混ざる」は実測で大部分を反証した。** 再開時に
  `ident.verify_against_lock` が contract-loader 束縛の 24 file を内容ハッシュで再検証しており、
  その閉包には pipeline・loop・wal・ident・artifact_admission と検証器一式が入っている。
  B-10 は `loop.py` の `ensure_resumable_wal` 経由でこの検査を通る (`require_environment_contract`
  の既定は真で、無効化するのは `guided.py` だけ)。`analysis_commit` はこの役目を担っていなかった。
  閉包外に残るのは calibrator の 2 file だけで、これは scope 外として裁定へ回した。
- **段 3 のもう 1 本が実在の取り残しを見つけた。** `test_ccbench_spawn_sites.py` の deferred gate
  台帳が対象 file の行番号を整数で固定しており、3 行削除で必ず赤になる。編集面に同 file を加えて
  2518/2914 → 2515/2911 へ更新した。**起動時の編集面重複検査 (branch tip + 全 worktree の
  未 commit 差分) では見つからない型である** — 重複ではなく、行位置に依存した別 file の検査だった。
- **別セッションから「発効済み事前登録の改訂にあたるのでは」という警告が来たが、文書 §1 の逐語
  照合と blob 一致で解消した。** 相手側も独立に裏を取り、警告を取り下げた。相手が最初に渡した
  編集面の衝突情報は 33 commit 前の snapshot に基づくもので、実際には既に land 済みだった。
- 段 6 の敵対レビュー 2 本はいずれも所見ゼロ。変異 4 件で裏を取り 4/4 KILLED、baseline 緑。
  M04 は「内容ハッシュ束縛を `core()` から外す」向きの変異で、これが KILLED であることが
  「規律 7 の名の下に内容束縛まで緩めてはいない」ことの証拠である。
- **計算ノードの待ち行列が混雑し、焦点走が 3 回続けて実行に至らなかった。** 2 回は queue 待ちの
  既定上限 15 分に掛かって tool 自身が job を取り消し、1 回は `qstat` 自体が 30 秒で時間切れに
  なって orphan hold が残った。hold は job の不在を `qstat -f` で確認し HEAD と tracked tree を
  確かめてから外した (手動 qdel はしていないので F47 の submission-disabled は発火していない)。
  4 回目が 13 秒で完走した。**テスト本体は 7.59 秒で、所要のほぼ全部が scheduler の待ちだった。**
  **3 回目と 4 回目はどちらも `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600` を付けており、
  3 回目は失敗している。したがって「待ちの上限を延ばしたから通った」とは言えない。** 4 回目は
  投入の 7 秒後に実行が始まっており、変わったのは待ち行列の空き (待機 38→、実行 51→) である。
  同 override が有効かどうかは、この wave の実測では判定できていない。
- **段 8 の候補 1 件は予算に阻まれて見送った。** `git worktree add` に相対 path を渡すと、
  隔離 session の cwd が wave worktree なので author worktree が内側へ入れ子で作られる
  (今回実測。撤去して作り直したので実害なし)。`DW-S05-A` へ 1 行足すと L1.5 の unique footprint
  が 9813 bytes となり予算 9696 bytes を超える。D782/D730 の手順では独立 3 例で例外収容だが
  実例は 1 件なので、安全義務を削って場所を作らず**実施しない**へ落とした。再発時に再検討する。

## 次の一手差分

### 新規

- {{T:b10-resume-binding-residual}} **P3・親の推奨は「現状維持」・ユーザー裁定**:
  B-10 の再開束縛で残った 2 件。(1) 計測値を読む `orchestrator/calibrator/benchparse.py` と
  `analyze.py` を内容束縛の閉包へ入れるか — 親は現状維持を推奨する (発火する運用が無く、
  閉包へ足すと B-10 以外の全 campaign の再開まで厳しくなる)。(2) 過去ブロック記録の
  `source_commit` / `analysis_commit` を receipt へ束縛して認証するか — 親は現状維持を推奨する
  (除去前も認証しておらず、守る対象が測定値でも correctness でもない)。
  詳細と選択肢は `output/insights/2026-09-02_b10-analysis-commit-unbind/ruling-package.md`。
