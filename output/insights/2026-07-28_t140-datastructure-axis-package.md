# [T-140] データ構造水準の変異軸 — 段階 A/B の設計結果と裁定パッケージ

**位置づけ:** `docs/axis-onboarding.md` の**段階 A 出口 + 段階 B** を実施した記録。段階 C 以降
(機構実装・偵察・LLM ループ) は実施していない。dev-wave 段 4 の親裁定は **実装しない**
(`4→7→8→9`) であり、コード差分は 0 byte。**したがって変異 matrix と受入全走は本 wave の対象外**
である (`DW-S04`)。

**結論:** 提案された「write set の格納形式」軸は、**条件付き採用にしない。段階 B へ差し戻す。**
軸そのものを捨てるかどうかはユーザー裁定 (§6)。

一次資料 = `2026-07-28_t140-review-verbatim/` (段 2 プラン 1 本 + 段 3 敵対相談 2 本の逐語)。

---

## 1. 段 1 の実測 (親、実コード裏取り)

| # | 事実 | 一次資料 |
|---|---|---|
| M1 | `write_set_` / `read_set_` の宣言は**編集面外** | `external/ccbench/cc/silo/include/transaction.hh:35-36` |
| M2 | 編集面の独立 hard-code は **4 箇所** (当初「3 箇所」と書いたのは過少計上) | `orchestrator/campaign/source_digest.py:68,71`、`hooks/guard_write.py:37`、`orchestrator/campaign/s6_proposal_rounds.py:120` |
| M3 | `assert_includes_match_head` が対象ソースの `#include` 行集合を HEAD に固定 | `source_digest.py:29-36,153-156` |
| M4 | `diff_quarantine.parse_template_file` は単一 marker 前提 | `diff_quarantine.py:537,560-561` |
| M5 | use site が要求する概念 (RandomAccessIterator / `erase` / `emplace_back` / `clear` / `size` / `back` / range-for)。**ただしこれを「container concept の確定」と呼ぶのは過大** (§3 A-1) | `transaction.cc:109,124,234,322,408` 他 |
| M6 | `WriteElement` は move-only (`std::unique_ptr<char[]>`)、`OpElement` は `std::string key_` | `silo_op_element.hh:38-80` |
| M7 | 動作点 = t48 / 1M / rr50 / rmw=false / `max_ope=10`。**「両 set は ~5 要素」は推論であって実測ではない** (撤回、§3 B-3)。実 set 長は zipf 0.9 の重複 key・`transaction.cc:529` の coalescing・read-own-write・早期 abort で別分布になる。**実 set-size 分布は未測定** | `pipeline.py:65-68`、`transaction.cc:529` |
| M8 | axis-onboarding §4 冒頭が「データ構造/型選択の軸」を既存 2 型の外と明示し、テンプレ改訂 + D41 水準レビューを要求 | `docs/axis-onboarding.md` §4 冒頭 |
| M9 | CCBench は C++20 要求。**環境事実 (pegasus02 / g++ 11.4 / g++-12 / g++-13 不在) は shell 実測であって file:line 裏取りではない** | `external/ccbench/cmake/CompileOptions.cmake:1` + shell |
| M10 | container 型が header の member 関数署名に露出 (`unlockWriteSet(std::vector<WriteElement<Tuple>>::iterator)`) | `transaction.hh:140`、`transaction.cc:367-368` |
| M11 | `:124-127` は erase 後に無効 iterator を `++` する UB。**「vector では 1 要素 skip」は言語保証ではない** (訂正) | `transaction.cc:124-127` |
| M12 | `include/backoff.hh:14` が大域 `using namespace std;` を宣言し `transaction.hh:9` が include | `external/ccbench/include/backoff.hh:14` |

### 生死確認 (`DW-G01`、使い捨て probe)

`write_set_`/`read_set_` に触れる行は 38 行、うち 6 行はコメントなので**実コード行は 32 行**。
そこから相異なる API パターンを抽出し、stock `std::vector` と非 std コンテナの双方で実体化した
(`g++-12 -std=c++20 -Wall -Wextra -fsyntax-only`)。

- **G1 は撤回した。** 当初「非修飾 `sort` が壊れるので `std::sort` への修飾が必須」と結論したが、
  M12 の大域 using-directive により**実 TU では通常の unqualified lookup で解決する**。probe に
  同 directive を足して再走し rc=0 を確認。**F29 型の誤り** (測定は正確、測定対象が命題と違った)。
- **G2 が支持する範囲 (レビュー後に更に縮小):** 「選んだ式と pointer iterator 代用型の構文成立」
  のみ。probe の要素型は実 `WriteElement<Tuple>` ではなく、候補型は **nested type ではなく
  namespace-scope template** であり、`-Werror` 無し・単一 TU・TRACE/ADD_ANALYSIS 未変化。
  **「データ構造 hole は構造的に実現可能」までは支持しない。**

---

## 2. 段 2 プランの要旨 (逐語 = verbatim/plan.md)

read-only codex 1 本 (`gpt-5.6-sol`、`reasoning=max`)。285 行。
軸名 `silo-writeset-storage`、SOURCE_REL = `cc/silo/include/transaction.hh`、単一 marker の中で
完全型を合成させ、hole 外は alias 化で吸収する設計。編集面 3 定義への `transaction.hh` 追加を
**自ら【編集面制限の弱化】とラベル**し、人間承認が必要と明記した。段階 B 出口条件 12 点を提示し、
本 wave で実装しうる項目は **なし** と回答した ((P3) 支持)。

---

## 3. 段 3 敵対相談 (逐語 = verbatim/lensA.md, lensB.md) と親の裁定

read-only codex 2 本並列、異なるレンズ。**両レンズが独立に reject へ収斂した。**
所見は blocker 17 / must-fix 3。親が独立に裏取りし、**refuted 0 件**。以下は主要所見のみ。

### 3.1 軸の建て付けそのものを否定する所見

| ID | 所見 | 親の裁定と裏取り |
|---|---|---|
| B-5 | **container は正しさの分岐に乗っている** | **real (最重要)**。`transaction.cc:529` = `if (searchWriteSet(s, key)) goto FINISH_WRITE;` → update は container の答え次第で `emplace_back` を丸ごと飛ばす。`read` も `:215-220` で read-own-write 判定に使う。よって「格納形式だけを変える」という建て付けが誤りで、変わるのは**意味論**である。emplace 点で観測する保存則検査は構造的に fail-open |
| A-5 | **per-instance 状態で trace build と perf build を実行時に判別できる** | **real。絶対規律 1 への直撃**。TRACE build だけが `:403-405,:421-425,:601-623` で追加走査を行う。合成 class に呼出回数状態を持たせれば `#if TRACE` を書かずに両 build を分岐でき、diff-of-diffs (`source_digest.py:240-269`) は preprocess 後ソース差分しか見ないので捕まらない。**trace 側に正しい集合を見せ perf 側で落とす**構成が成立する |
| B-1 / B-4 / A-10 | **三すくみ** | **real**。「任意 C++ = 機械列挙不能」(T-140 の動機) と「構成的安全保証」と「偵察可能性」は同時に満たせない。`docs/axis-onboarding.md` §3-D は構成的安全保証ができない軸を B へ差し戻すと定める。安全な有限 DSL に閉じれば機械列挙可能に戻り、動機が消える |
| B-3 | 現動作点の地形が未実証 | **real**。M7 撤回のとおり |
| B-2 | 3 候補の比較が非対称 | **real**。格納形式にだけ任意 C++ を許し、他 2 候補を有限順列・分割へ狭めた比較になっている |

### 3.2 trace / verifier の死角 (どの軸でも効く)

- **W 行 emit (`:601-607`) と lock 被覆検査 (`:614-623`) は同じ `write_set_` を再走査する。**
  container が要素を落とすと **W 行も X 行も出ず**、verifier には「write が少ないだけの完全に
  直列化可能な履歴」に見える。**落とすほど速くなり、かつ certified になる。**
- 既存 permutation 保存 assert (`:403-425`) は `sort()` の前後しか括らず、`delete_record` (`:117`)
  内の erase も emplace 欠落も見ない。
- `Integrity` の 9 フィールド (`orchestrator/verifier/model.py:126-142`) に保存則の欄はない。
  `missing_txids` はトランザクション丸ごとの欠落しか見ない。
- A-7: shadow が body を持たなければ、保存則照合の後に `op_` を UPDATE→INSERT へ変えることで
  lock も body 書込も飛ばせる。`parse.py:116-126` は op 値を検証せず、`dsg.py:61-70` は
  key と commit しか使わない。

### 3.3 親 brief への攻撃 (すべて受け入れた)

M2 過少計上 / M5・M7 過大 / M9 の「すべて file:line 裏取り済み」という表現が不正確 /
G2 の「hole 内 nested type」という事実記述が誤り。M1・M3・M4・M6・M8・M10・訂正後 M11・
撤回後 G1 には追加の過大表現なしと判定された。

---

## 4. 親の裁定 (段 4)

**判定 1 — 実装しない (`4→7→8→9`)。** (P3) を支持する。両レンズとも「本 wave で実装しうる項目は
なし」と回答し、部分 landing (編集面・pin・digest だけ先行) は identity と受理集合の整合を壊す。

**判定 2 — (P1) を差し戻す。** 「難所が最も濃いから第一候補」は採用理由になっていない。
性能機序は未実測で、最も広い信頼境界を先に開く選択になっている。

**判定 3 — (P2) を差し戻す。** 単一 marker が保証するのは物理行の封じ込めだけで、任意 C++ 型の
constructor / iterator / destructor の意味的逸脱を閉じない。`diff_quarantine.py:14-20` は
自ら「C++ 意味論の完全性は当モジュールに載せない」と明記しており、未定の shape gate を
後付け前提にして採用と判定することはできない。

**判定 4 — 軸を条件付き採用にしない。段階 B へ差し戻す。** 独立に成立する 3 つの理由があり、
どれ 1 つでも差し戻しに足りる: (a) container が正しさの分岐に乗っている (B-5)、
(b) 三すくみ (B-1/B-4/A-5/A-10)、(c) 地形の証拠がない (B-3)。

---

## 5. T-140 とは独立に確定した実在欠陥 (裁定パッケージ)

本 wave の副産物。いずれも**本 wave では修正していない**。

- **N1 (identity 核の新規の穴、現行本番に存在):** `source_digest` は対象ソースを**単体で**
  preprocess するため、実 TU 側だけで定義されるマクロに条件づけられたコードが digest では死ぬ。
  `cc/silo/ycsb_silo.cc:3` が `#define GLOBAL_VALUE_DEFINE` してから header 群を include する一方、
  `_cpp_normalize` の defines は Options.cmake 既定 + genome.flags だけ。同 pattern は
  **既に編集面にある `include/backoff.hh:123-125`** にも存在する。`source_digest` の docstring が
  列挙する既知の穴 (`__has_include` / computed include) に**この型は入っていない**。
  通常ループでは `diff_quarantine` の hole 外検査が止めるが、`pipeline.evaluate()` は
  `source_digest.resolve()` しか呼ばない (`pipeline.py:441-449`) ため **caller 依存**である。
- **N2 (ドリフト):** 編集面の独立 hard-code が 4 箇所 (M2)。`test_hooks.py:262-264` は
  2 つの `EVOLVE_BLOCK_SOURCES` 一致しか見ず、**`source_digest.ALLOWLIST` を参照するテストは
  repo に存在しない**。かつ正しい述語は部分集合ではなく **完全一致 + 型付き例外**である
  (部分集合だと「編集可能だが digest 対象外」のファイルを許す)。
- **N3 (CCBench の意味的問題):** `transaction.cc:529` により、同一トランザクション内で同じ key を
  2 回 update すると **2 回目の body が捨てられて `Status::OK` が返る** (first-write-wins)。
  上流への報告・PR 判断は人間へ委ねる (D16/D18/D20)。
- **N4 (CCBench の欠陥):** insert→delete が Masstree に absent+locked の ghost tuple を残す
  (`transaction.cc:83-109` → `tuple.hh:50-53` → `:123-136`)。abort cleanup (`:27-34`) は
  write set 内の INSERT しか消さない。YCSB は delete を出さないので現行では未発火。
- **N5 (どの軸でも効く死角):** §3.2 の trace / lock 被覆の自己整合的沈黙。

---

## 6. ユーザー裁定を求める事項

**択 a — 既に開いている編集面内の下位軸へ戻す。** `cc/silo/transaction.cc` の中だけで完結する
データ構造水準の穴が実在する: `searchWriteSet` の線形走査 (`:342-350`)、read set 検証順序
(`:450-474`)。`transaction.hh` の難所 (M1/M10) と信頼境界改変 (N2) を丸ごと回避できる。
ただし B-2 の非対称性批判に応えるため、**3 候補を同一の自由度・安全境界で再比較する**必要がある。
またこれらの穴も B-5 の問題 (container/探索が正しさの分岐に乗る) から自由ではない。

**択 b — 信頼済み実装群 + 宣言的パラメータの有限 DSL に閉じる。** 安全性を構成的に保証でき、
偵察 (段階 D) も使える。代償として**機械列挙可能に戻る**ため、「LLM が機械探索を上回る」主張は
降ろすことになる (roadmap §10 はもともとこれを成功条件にしていない)。

**択 c — 軸を捨て、[T-139] (劣化版 Silo の梯子) / [T-144] へ資源を移す。**

**親の推奨: 択 a を先に、ただし着手前に実 set-size 分布を測る。** 地形の有無が全候補の前提で
あり、`ADD_ANALYSIS` カウンタか短い計装で安く取れる。分布が小さく機序が立たなければ択 c。
択 b は「非列挙性」を主張の根拠から外す判断を伴うため、単独でユーザー裁定を要する。

**併せて裁定を求める:** N1・N2 を独立タスクとして起票してよいか (N1 は現行本番の identity 核に
関わるため優先度が高い)。N3・N4 の上流報告の要否。

---

## 7. 残存リスク

- 本 wave は**性能を一切測っていない**。地形の有無は未知であり、本文のどこにも地形の主張はない。
- 段 3 の 2 レンズはいずれも静的検査のみで、pytest を走らせていない (`DW-O05`)。
- 逐語には具体的な container 戦略名が含まれる (B-6、F12 型の文書経由リーク経路)。
  **これらを coder / planner の入力へ射影してはならない** (verbatim ディレクトリの README に明記)。
  現時点で coder へ届いた事実はなく、実測された勝ち点も存在しない。
- 択 a を採る場合、B-5 の「container が正しさの分岐に乗る」問題は解消しない。
  下位軸を変えても同じ検査設計 (API 意図を信頼側 shadow に記録し各消費 phase で独立照合) が要る。
