---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-06
wave: dev-wave-t459-resume-topology
seq: 2
---

## {{D:incomplete-attempt-recovery}}. 中断 attempt は identity 照合済み seam で recovery-abort し、自動回復は build 完了前の crash に限る

**決定:**

1. `build_start` 済みで terminal に達しない attempt は、identity を照合した resume seam で
   exact な recovery-abort record を追記して終端させてから再評価する。追記後の再評価は
   従来どおり新しい attempt を開始する。
2. **自動回復するのは、対象 attempt の `build_start` 以後にその attempt の record
   (`build_done` / `verify_done` / `bench_done`) が 1 つも無い場合だけとする。**
   それ以外、および trigger 系 campaign・回復回数上限到達・既存 topology 違反・
   単一 variant の複数 active・truncated tail と active attempt の併存では、
   **1 byte も書かずに専用例外で停止する**。
3. 走査・既存 topology 検査・生成 suffix 検査・追記は、WAL fd の排他ロックを保持したまま
   1 区間で行う。いずれかの検査に落ちたら最初の write より前に停止する。
4. 追記する record は `abort` stage の exact key 集合だけを持つ。receipt を持つ attempt には
   同一の receipt SHA を伝播し、持たない attempt には載せない。attempt topology の validator は
   この exact key 集合を要求する (受理集合の縮小)。
5. 回復の reason は retryable terminal として扱い、同 run 内で再評価させる。
6. 回復 seam は `build_start` を書きうる全 entry point の、停止判定・checkpoint・
   provenance 書き込みより前に置く。

**理由:**

- 未終端 attempt を残したまま再評価すると二つ目の `build_start` が入り、以後の replay と
  artifact admission が campaign 単位で拒否する。実行時に committed と報告された結果が
  後から失効するため、成果物 (certified 選択・report・台帳参照) が事後に消える。
- 「crash 後は再評価する」は既存の保証であり、異常検知で停止する一本の設計は後退になる。
  終端 record を足して topology を満たす形だけが、検査を緩めずに両立させる。
- 回復対象を build 完了前に限るのは、並行 run が起きた場合に生存側が後から書く record を
  必ず inactive attempt への record として loud に拒否させるためである。測定・検証の signal は
  build 完了後にしか出ないので、この限定により「回復後に正しさ signal だけが静かに紛れ込む」
  列が構成できなくなる。
- 回数上限は、決定的に落ちる attempt で「回復 + 新 attempt」が無限に積み上がるのを防ぐ。

**却下した選択肢:**

- **同一 attempt ID を再開する状態機械** — build 途中状態と admission receipt の再現契約が要り、
  replay state は ID・receipt SHA・stage しか保持しない。
- **検知したら常に停止する (自動回復なし)** — crash 後の再評価という既存保証を後退させる。
- **campaign 全体の実行所有権 (lease) を同 wave で導入する** — 運用契約を変える設計択一であり、
  裁定を経ずに既成事実化しない。本 wave は回復対象を狭めることで安全側に倒し、
  lease は裁定へ返す。
- **read 経路の書き込み除去や trigger provenance の schema 拡張の同時実施** — いずれも独立に
  審査すべき変更で、同 wave に混ぜると回復本体の検証が薄まる。
