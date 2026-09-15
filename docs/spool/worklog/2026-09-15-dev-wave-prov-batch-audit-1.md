---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-15
wave: dev-wave-prov-batch-audit
seq: 1
title: 全史 provenance 監査の per-commit message 取得を一括化した — 検査範囲は一切変えず同条件で 1.5355 倍 (34.79 % 減)、成長比例は消えていない (コード + テスト、branch worktree-dev-wave-prov-batch-audit、変異 matrix = baseline PASSED・KILLED 7/7・SURVIVED 0・MISMATCH 0)
---

## 本文

- ユーザーが引数で起票した wave。逐語の要旨は「リポジトリの成長で比例して大きくなる受入全走等の
  研究開発で必ず踏むコストを解決してほしい。たとえば全史検査。1 万コミット近くあって何かするたびに
  1 万コミット検査するのは愚か」。全 9 段を回した (正しさ防壁に触るため `DW-C00` に従い
  敵対検証子を省かなかった)。設計判断は {{D:provenance-batch-message-fetch}} と
  {{D:cost-reduction-prefers-constant-over-scope}}。
- **範囲を削らずに定数を下げた。** 段 1 の費目分解 (逐次 n=200) で、全史監査 133.6 秒の
  **84.7 % が per-commit の `git show -s --format=%s` / `--format=%B` の起動**だと判明した。
  同じデータは `git log` 1 回・全史 0.49 秒で取れる。D908 が「全史監査を削るな」と裁定している
  ため、範囲は 1 件も変えていない。
- **親の見積もりが 2 度過大で、2 度とも段 3 / 実測に撃たれて撤回した。** 段 1 brief は
  「2 桁速くなる / 全史 5 秒」と書いたが、段 3 luna (L-1) が「逐次 n=200 の費目比率を
  `AUDIT_WORKERS=min(cpu,32)` の並列 wall へ直接適用できない」と指摘した。撤回して
  「4〜6 倍」に改めたが、**同条件の実測は 1.5355 倍 (34.79 % 減)** だった。
  成果として書けるのはこの値と「取得 subprocess を 2N 本から 1 本へ」の構造的事実だけである。
- **段 3 sol (S-1、blocker) が親 brief の論証の穴を当てた。** 親は「範囲を変えないので被覆等価は
  自明」と書いたが、**対象集合・件数・順序・OID 検証がすべて一致しても、OID と message の対応が
  ずれれば拒否が受理へ動く**。撤回し、「対象集合の一致 **かつ** OID ごとの文字列一致」へ訂正した。
  実装は OID を鍵にした辞書引きで、要求列と出力列を位置で結合しない。
- **親の測定設計の誤り (erratum)。** 旧新比較を「wave worktree (旧) 対 impl worktree (新)」で
  組んだため、checker の版だけでなく**実行経路**まで変わっていた。checker は
  `login_headroom.grant_budget()` の判定で計算ノードへ dispatch する。実測した判定は
  `Admission.DISPATCH` (観測余裕 179 MB / 実効天井 15 GB に対し使用量 16.2 GB、物理メモリは
  197 GB 空き) で、**負荷ではなく izanagi 自身の予算枠**である。1 回目の結果 (old 947 秒 /
  stdout 33612 B 対 new 65.6 秒 / stdout 4832 B) は無効で、新側の出力実体は dispatch のログだった。
  正しくは同一 worktree で版だけを差し替える。やり直した結果が上記 1.5355 倍である。
- **他 2 件の自分の誤り。** 変異 spec の `category` を推測で書いた (`CATEGORIES` は
  `{"negative","positive","both-layers"}` の閉集合)。anchor 検査 script が III-2 に誤検出を出した
  (`new` が `old` の部分文字列なので `new in text` が必ず真)。
- **棄却しなかった所見の扱い。** 段 3 は 9 所見すべて real。段 6 レビュー 2 本は **blocker 0**
  (R-1 nit、Q-1〜Q-3 should-fix、Q-4 nit)。**fix 子は起動しなかった** — real 所見のうち実装差分の
  欠陥を指すものが 1 件もなく、R-1 は親の変異登録、Q-2 / Q-3 は親の実測、Q-1 は報告文言、
  Q-4 は次の一手だったため。`DW-M02` に従い変異で裏取りした。
- **段 6 R-1 を受けて変異分類を訂正した。** I-4 (一括結果の OID 列で監査対象を上書き) の赤は
  「重複 finding の消失」であって受理集合差ではない。群 I から外した。
  `DW-M03` / `DW-M08` の「診断文字列だけの赤を kill にしない」に従う。
- **実 object 欠落 / packed 形態からの復帰は実走確認していない** (段 6 Q-1)。現 fixture の
  `missing` は出力 record の欠落、`log-error` は注入例外であって実 object 欠落ではない。
- **受入は 4 回投げて 4 回目で `child-green`。1〜3 回目はすべて非帰属。** attempt 1 は 12 error
  (s8c 4 件が `git archive` の 10 秒 timeout、t1259 8 件が F945 同型の 30 秒 timeout)、
  attempt 2 / 3 は各 1 error (`real-repo lock deadline exceeded`、holders 4 プロセス READ)。
  **全件 `TimeoutExpired` / lock deadline であって assertion 失敗ではなく**、本 wave の差分
  (checker とそのテスト 2 file) から到達経路がない。単独再走は 269 passed / 218 passed で
  いずれも rc=0・非再現。**`flaky_test_holds.py` への hold 登録はしなかった** — 一過性の輻輳に
  対して恒久的に suite を弱めることになるため。受入非走行時に lock holders が 0 であることを
  実測し、**複数 wave の受入が共有 lock を奪い合う外部競合**だと確認して、leader 1 本・
  load 116.70 の下降局面で投げ直した。
- **実走の実測。** 実装子の自走 harness が 47 passed / 357 deselected (42.52 秒)。親の焦点走は
  consumer 9 file が **3149 passed / 8 skipped / 0 failed** (72.60 秒、計算ノード job 998969)。
  commit 後の全史監査 rc=0 (10105 件・新規違反なし・known-violations=56)。受入全走 attempt 4 が
  **23700 passed / 68 skipped / 赤 0** (`verdict=child-green`、tested_main `8c84f9239`、
  tested_tip `5fbc8926f`)。test 関数名は基底 201 から 209 へ増え、**消失 0・改名 0** を親が機械照合した。
- **変異は 2 pass。** `DW-M07` に従い probe (全件 SURVIVED 期待) で観測 node を集めてから
  KILLED 期待で本登録した。本走は baseline PASSED・**KILLED 7/7・SURVIVED 0・MISMATCH 0・
  matching 7**。観測 node は I-1=58 (OID 対応の破壊)、I-2=16 (message の rstrip)、
  I-3=1 (部分結果の採用)、I-5=8 (取得失敗時に旧経路へ戻さない)、II-1=37 (`%s` → `%f`)、
  III-1=1 (一括取得の常時無効化)、III-2=1 (oracle へも一括結果を渡す)。
- **成長比例は消えていない。定数が下がっただけである。** 一括化後も `_ai_agent_values` の
  per-commit subprocess、隔離 parse の tempdir、実装 path 取得、祖先索引・pickaxe が残る。
  「解消した」とは書かない。
- 逐語・変異台帳・コスト棚卸しは `output/insights/2026-09-15/prov-batch-audit/`。

## 次の一手差分

### 新規

- {{T:provenance-incremental-audit}} **P1・新規**: 全史 provenance 監査を差分監査にする。
  D908 の条件 (取り込み差分だけを対象とする独立監査を先に設計し、被覆が現行と等価であることを
  示す) を満たす形で設計する。等価性の骨子は「main は ff-only なので、前回検査済み tip が現 HEAD の
  祖先なら `ancestors(HEAD) = ancestors(audited_tip) ∪ (audited_tip..HEAD)`、前半は前回 rc=0 かつ
  checker の bytes が同一なら判定も同一」。祖先でない / checker の bytes が違う / 受領証が読めない
  ときは全史へ fallback する。受領証を書く主体と検査する主体が同じである限り改竄への完全な防壁には
  ならない (D387 と同型の限界) ことを主張せず明記する。
- {{T:provenance-residual-percommit-cost}} **P2・新規**: 一括化後に残る per-commit コストを
  順に潰す。段 3 luna の調査順位は trailer subprocess → 隔離 parse の filesystem 操作 →
  実装 path 取得 → 祖先索引 / pickaxe。祖先 bitset は長い履歴でメモリが二次的に増えうる。
  `_ai_agent_values` の `%(trailers)` 置換は ambient config を含む等価性証明を伴う場合だけ行う。
- {{T:provenance-real-object-failure-fixture}} **P3・新規**: 一括取得の実 object 欠落 /
  pack 破損からの復帰を、loose / packed 両形態の実 fixture で確認する。現 fixture の `missing` は
  出力 record の欠落、`log-error` は注入例外であって実 object 欠落ではない (段 6 Q-1)。
