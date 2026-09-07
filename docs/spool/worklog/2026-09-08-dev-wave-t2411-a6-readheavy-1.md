---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2411-a6-readheavy
seq: 1
title: [T-2411] A-6 read-heavy 認証を実際に投入し、初めて測定が取れた — 判定は reject (採用版が 5.78% 遅い) (コード + テスト + policy + 認証成果物 + insight、branch worktree-dev-wave-t2411-a6-readheavy、変異 4/4 KILLED)
---

## 本文

- **A-6 read-heavy の認証を 2 回投入し、2 回目 (`a6-20260908b`、request `982234.nqsv`) が完走した。**
  判定は `reject`、effects `-5.78%`。2 cell とも正しさは certified で、性能で採用版が stock に
  負けた。**論文 §8 の read-heavy は、正しさの側だけ外挿から実測へ変わった。** 詳細は
  `output/insights/2026-09-08_t2411-a6-readheavy-submitted/README.md`、認証成果物は
  `output/insights/2026-09-08_t2411-paper-story-a6-certification/`。
- 1 回目 (`a6-20260908a`、`982055.nqsv`) は 36 秒で止まったが、**前走が止まった条件 gate は
  越えていた** — 止まった地点は 2 cell の受理が済んだ後の受理証跡の書き込みである。
  根本原因は **Lustre に `renameat2(RENAME_NOREPLACE)` が無い**こと (実測: /work と /home で
  EINVAL、ノード内蔵の /tmp で成功)。`os.link` による上書き禁止を弱めない代替経路を足した。
- **main 側の別 wave (`31ec382a7`) が同じ欠陥へより弱い修復を先に着地させていた。**
  受入の post-claim merge が競合し (`stage=merge rc=70 source_rc=1`)、Codex `role=author` の
  合成子に合成させて親が merge を確定した。production は本 wave の形 (許可 errno 3 種・
  `follow_symlinks=False`・link 直後に publish 成立・後始末は best-effort)、テストは両 wave の
  7 本すべてを保持している。main 側の形は、link 成功後に後始末が失敗すると**publish 済みなのに
  失敗を返し再実行が `EEXIST` で永久拒否される**筋を残していた ({{D:a2-noreplace-link-publish}})。
- 段 3 レンズ A が挙げた「代替が source symlink を辿って proof を差し替えられる」は
  **現環境では再現しない**と実測した (Linux の `os.link` は既定でも symlink を辿らない)。
  対策の `follow_symlinks=False` は意図の pin として入れ、変異 matrix の分母には入れていない。
- **変異事前登録を 2 件、実装後に再照準した (erratum)。** 段 6 レビュー B が M1・M3 の単独帰属
  不成立を示したため、`DW-M01` に従って実効 gate へ当て直した。合成後 tip で 4/4 KILLED、
  期待 node と完全一致、baseline PASSED。
- **公開 (`collect`) が 2 段で止まり、運用上の制約が 2 件わかった** ({{F:a6-collect-publish-blockers}})。
  (1) 投入した checkout から実行しないと `qsub -v is not bound to workload and current pin` で
  止まる — 投入時に記録した policy の絶対 path と照合するため。(2) 公開先が 2026-09-02 の
  失敗時 README で埋まっており空の新しい leaf が要る。後者は policy の
  `tracked_destination` を更新して解いた。**`_protocol_preimage` に含まれない key なので
  `protocol_sha256` は前後で同一** (実計算で確認)。走行時と公開時で policy bytes が
  異なる事実は insight に明記した。
- **所要 73 分のうち約 70 分は正しさ検査だった** (48 スレッド × 約 7 分 × 10 回)。ビルドは 15 秒、
  性能計測は 17 秒。投入器は workload 単位では既に分割しており、直列なのは workload の内側である。
  ユーザー指摘により、分割禁止の根拠として**ノード間の性能差を挙げてはならない**ことを確認した
  (runbook 明示)。効くのは処置とノードの完全交絡だけで、それは量を比べる計測にしか効かず、
  真偽値を返す正しさ検査には効かない。実際の障害は実行ファイルの同一性検査である
  ({{D:a6-verification-fanout-axis}})。
- エージェント工数: codex 子 7 本 (plan 1 / consult 2 / author 2 / review 2)、いずれも
  `gpt-5.6-sol` reasoning=xhigh。親の焦点走 2 本・変異 2 巡・受入 2 回は計算ノードへ dispatch した。
- **ポーリングの無駄をユーザーから 2 度指摘された。** 待ち手を張った後も状態確認の tool call を
  100 ターン近く繰り返しており、情報は 1 つも増えていなかった。待ち手を張った時点で
  ターンを終える運用へ直した。

## 次の一手差分

### 完了

- [T-2411] A-6 read-heavy 認証を実投入し、`a6-20260908b` が完走して判定 `reject`
  (effects -5.78%、2 cell とも correctness certified) を得た。阻害要因だった Lustre の
  `renameat2` 非対応を局所修復し、main 側の独立修復と合成した。認証成果物を公開した。
  remaining: none
  base: 7e004e7a20fdd67af1264beaa79bad3a7ba9a5e5d6ef65bce0936b2d9dcbbea8

### 新規

- {{T:a6-verification-node-fanout}} **P1・新規**: 認証 campaign の正しさ検査をノードへ
  分割できるようにする。実測では 73 分中 70 分が 48 スレッドの直列性検査 10 回で、1 ノード内では
  並べられない。分割の障害はノード間差でも交絡でもなく、`perf_bin_sha256` の照合 (ノードを跨いで
  建て直すと bytes が変わる) と現行 policy の形である。1 回建てた実行ファイルを配る形か
  再現可能ビルドかを先に決める。着手前に最安の生死確認 (別ノードで同一 bytes のまま動くか) を行う。
- {{T:a6-readheavy-negative-effect}} **P2・新規**: read-heavy で採用版が stock より 5.78% 遅い
  という測定を、反復 attempt で確かめるか、機序として説明する。現状は 1 attempt・5 標本の
  中央値比較であり、`a4_noise_floor_status` は `open` のままである。
