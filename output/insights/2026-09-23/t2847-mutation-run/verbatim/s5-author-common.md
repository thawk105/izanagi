# 段 5 author 共通契約 ([T-2847] mutation-run)

正本: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/s4-ruling.md (段 4 裁定。R2 発火診断・R3 workload・R4 期待・R7 所有)。
設計: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/s2-plan.md の「patch 設計 (14 本)」表、
発火条件: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/codex/s3-consult-a.md の「patch ごとの発火条件」表と F02〜F06。
どれか読めなければ即停止し、その旨だけを書いて終われ。

## 権限と境界

- 編集してよいのは、prompt が名指した所有 path だけ。docs (`*.md`) は編集しない。commit しない (起動器が終端で commit する)。
- `external/ccbench` (submodule) の作業木・index を変更しない。patch は submodule 外の scratch (`<unit worktree>/.t2847-scratch/`、終了前に削除) に `external/ccbench/cc/silo/transaction.cc` などを複写して編集し、`git diff --no-index` で作って header の path を `a/cc/silo/transaction.cc` / `b/cc/silo/transaction.cc` (既存 `patches/broken-silo-*.patch` と同じ形、`diff --git a/... b/...` 行つき) に直す。
- 各 patch は `git -C external/ccbench apply --check <patch>` (作業木を変えない) が fuzz なし・rc=0 で通ること。既存 patch と同時に当てる前提は無い (単独適用)。
- 壊し patch を baseline に混ぜない (規律 2)。verifier・driver・condition gate の判定を変える編集はしない。

## patch の形 (全 14 本)

1. 1 patch = 1 機構。新設する裸マクロは表の 1 個だけ (`IZANAGI_BREAK_<名前>`、`CCBENCH_` の外)。
2. 変更はすべて `#if IZANAGI_BREAK_<名前>` … `#else` (元の文そのまま) … `#endif`、または元の文を変えない追加だけの `#if IZANAGI_BREAK_<名前>` … `#endif` に閉じる。`#ifdef` は使わない。**macro 未定義で preprocess 後が pin と一致すること** (inert)。`unifdef` があれば `unifdef -UIZANAGI_BREAK_<名前>` の出力と元 file の diff が空であることを確かめ、無ければ無いと書き、枝ごとに目視で説明する。
3. `#if IZANAGI_BREAK_<名前>` の出現回数 (site 数) を patch ごとに数えて報告する (登録 author が使う)。
4. **発火診断 (段 4 裁定 R2 の契約、全 patch 共通):**
   - macro 有効時だけ、file 内 static の `std::atomic<uint64_t>` を relaxed で加算: `reached` (変異枝に入った)、`changed` (元コードと異なる挙動を実際に生んだ。条件は相談 A の表と下の prompt 個別指示)、`committed` (changed を 1 回以上含んだ取引のうち commit() が true を返した数。thread_local bool を begin() で false、changed 時に true、commit 成功で true なら加算)、必要なら extra。
   - 出力は process 終了時に 1 回だけ、namespace-scope の static object の destructor から `stderr` へ 1 行: `T2847_FIRED slug=<slug> reached=<n> changed=<n> committed=<n>` (extra があれば ` <名前>=<n>` を続ける)。**文字列に `IZANAGI_` を含めない。**
   - race 区間 (lock 保持中、payload 複写と TID 再読の間など) に I/O を置かない。加算は relaxed atomic だけ。
   - ycsb の実行が static destructor を走らせる終了経路 (main の return / exit) かを `external/ccbench/cc/silo/ycsb_silo.cc` (または該当 main) と `common/` で確かめて報告する。走らない経路なら代案 (例: 終了直前の既存の結果出力箇所) を patch 内で提案し、その理由を書く。
5. build はしない (login node の build は拒否される。親が計算ノードで build する)。g++ の `-fsyntax-only` で構文だけ確かめられるなら試し、include 不足で通らないならそう書く。

## 報告 (最終メッセージ)

- patch ごと: path、macro、site 数、変更位置 (pin の file:line)、changed / committed / extra の条件、`apply --check` の rc、inert の確かめ方と結果、構文確認の結果 (未実施ならそう書く)。
- 緑には実走したコマンドと範囲を併記。実走できなかったものは「実装済み・未実走」と書く。
- 所有外への波及 (登録が要る test・table) の静的列挙。
- 見出し「## 総括」を最後に置く。
