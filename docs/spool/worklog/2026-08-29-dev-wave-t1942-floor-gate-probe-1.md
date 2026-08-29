---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: dev-wave-t1942-floor-gate-probe
seq: 1
title: [T-1942] 床値実測の投入前ゲートを実測し、主経路の赤が無条件であることを確定した (docs のみ、branch worktree-dev-wave-t1942-floor-gate-probe、実装差分ゼロ・変異 matrix 免除)
---

## 本文

- ユーザー指示の停止条件が成立した。指示は「投入の直前に主経路の赤が解消しているかを実測し、
  未解消なら実装差分ゼロで塞いでいる箇所を記録して返す」。実測の結果**未解消**だったため、
  床値の測定・判定規則の凍結・反復数の凍結・campaign の投入をいずれも行わずに閉じた。
  凍結はゲートが緑の場合の条件付き手順だったので、条件不成立により実行していない。
- 測定の全文は `output/insights/2026-08-29_t1942-floor-gate-compiler-input/README.md`。
  要点は 3 つ。(a) D1192 の是正は現行 main に未実装で、落ちた job の manifest を現行コードへ
  通すと同一エラーを再現する。(b) 消える根は **2 クラス**あり、D1192 の裁定文は片方しか
  名指ししていない。(c) 赤は cache hit 条件ではなく**無条件**で、cache が空の初回実行でも落ちる。
- (c) は D1192 の前提「base が消えた後の cache hit で落ちる」を狭いと判定するものなので、
  推論だけで結論せず 2 方向から裏取りした。publish 手順のコード読解 (build 自身が
  `_discard_build_dir` で作業用 directory を破棄してから受領書発行へ進む) と、
  自前の新規 build を行った job `952631` が同じ段で落ちている実測が一致した。
- [T-2043] が「当日中に環境か main が変わった」と書いて未特定にしていた変更を特定した。
  環境ではなく main で、`0bc33ba8f` (2026-08-27 06:19) が `_external_entry` を新規導入している。
  この段を通過した最後の job `951456` (05:54) と、落ちた job `952615`/`952631` (14:02) の間に入る。
  同項が「原因ではない」と実測済みの `b215f1a27` (11:17) とは別物である。
- D1192 の射程を 2 クラスへ広げるかは裁定事項と判断し、実装せずユーザーへ返す
  ([T-2027] の更新に記した)。裁定文どおり 1 クラスだけ直しても主経路は赤のまま残る。
- 実装面の差分はゼロ。Codex 子は起動していない (docs-only の軽量版)。probe は repo 外に置き、
  repo へ入れていない。qsub は行っていないため、ノードの単独性確認は発火していない。

## 次の一手差分

### 更新

- [T-1942] **P2・[T-2027] 待ち**: 現行 Pegasus・workload 別の between-block 床値を実測する。
  判定床に使っている 0.030 は旧環境の write-heavy / balanced 由来で read-heavy を含まない。
  2026-08-29 に投入前ゲートを実測し、**主経路は未解消**と確定した
  (`output/insights/2026-08-29_t1942-floor-gate-compiler-input/README.md`)。
  赤は cache hit 条件ではなく無条件で、cache が空の初回実行でも受領書発行段で落ちる。
  [T-2027] の実装が landed し、実機で受領書発行段を通過することを確認してから再開する。
  base: 616b52f44cc38341af82ee9f224a7c35c10c061d4b626fb42def95f9a5503097
- [T-2027] **P1・裁定済み (2026-08-27 /rulings 全件、推奨どおり) → 実装待ち。射程の拡大はユーザー裁定待ち**:
  択 (1) 採用 — manifest に根の分類と根相対 path を持たせ、使用時に現在の canonical base へ
  束縛して再検証する (D1192)。**床値実測の主経路を現に止めているので最優先。**
  同じ赤を報告している別 wave の項目とは、選択肢集合を照合するまで 1 件へ束ねない。
  2026-08-29 の実測で、消える根が **2 クラス**あることが判明した。D1192 の裁定文が名指しする
  build cache の作業用 directory (`.staging-<PID>-<nonce>/_deps/…`、31 件) に加え、
  job 専用作業領域 (`/scr/0_<jobid>.nqsv/{gflags,glog}-install/include/…`、7 件) がある。
  **裁定文どおり 1 クラスだけ根相対化しても主経路は赤のまま残る**ため、射程を 2 クラスへ
  広げてよいかをユーザーへ返す。あわせて D1192 が「run 間の cache 再利用を失う」として却下した
  代替案は、赤が無条件である以上そもそも赤を直さない (却下理由自体は変わらない)。
  base: c66919d261f393921cc856ad896744d8c94633391702dedf3e72d4ca882aa0d4
- [T-2043] **P1・原因特定済み → [T-2027] の実装で閉じる**: 床値 job が binary admission receipt の
  発行段で落ちる赤。本文は
  `compiler input manifest の完全検証に失敗: external compiler input is unavailable`
  (`orchestrator/campaign/s8b_compiler_input.py:438` の `_external_entry()` が絶対 path の
  external input を `resolve(strict=True)` で解決できない)。
  2026-08-29 の実測で 2 点が確定した。(a) 原因は環境変化ではなく `0bc33ba8f` (2026-08-27 06:19)
  による `_external_entry` の新規導入で、通過した job `951456` (05:54) と落ちた job
  `952615`/`952631` (14:02) の間に入る。(b) 赤は cache hit 条件ではなく**無条件**で、
  cache が空の初回実行でも落ちる — build 自身が `buildcache.py:2712` で作業用 directory を
  破棄してから受領書発行へ進むためである ({{F:self-invalidating-input-manifest}})。
  是正は [T-2027] / D1192 が正本なので本項では実装せず、同項の landed 後に閉じる。
  base: 37e17b6210225eadc1604dd4481ef2998408433d67485e96046a68f36572ad11
