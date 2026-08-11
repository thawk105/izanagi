# 段 1 brief — [T-810] 測定装置の実装 (slice 1: 事前登録の凍結と非流入の背骨)

## scope

**この wave で作る。** protocol §9.1 の item 2 (機械可読な事前登録 artifact + digest) と、
item 1 の (c) 測定 runner の argv allowlist、(d) repo 外専用 root の方針注入、
(e) §6.3 の単一 fail-closed validator。**キューへは一切投入しない。**

**この wave では作らない (後続 wave)。** (a) N-job group barrier・共有 release・取り消し marker・
coordinator 側の開始ばらつき測定・N 件 exact な完了 verifier、(b) T-810 専用 PBS wrapper、
(f) 並走ガードの機械化、(g) 予算 admission。**したがって本 wave の完了は §9.1 を充足しない** —
第 1 段承認を求められる状態にはまだ到達しない。この事実を land 報告に明記する。

## 確定済みユーザー裁定 (2026-08-12)

1. 「測定装置を作る」。実装・凍結・受入まで作り、投入はしない。
2. 事前登録値は **N=13・R=10** (protocol 本文)。裁定パッケージ s4 §5 Q3 の「N12/R12」は、
   段 6 焦点レビューが assurance 計算式の誤りを摘出する前の stale 値なので採らない。

## 段 1 実測 (brief 前の前提検査)

- CCBench head = `d706650cdb31e442bef45b9b4216951d4fb40969`、§2 の pin と一致 (worktree で実測)。
- T-810 の実装は 0 byte (`tools/` `orchestrator/` に該当 module なし、grep 0 件)。
- 再利用可能な既存機構: `orchestrator/campaign/durable_root.py` の `DurableRootPolicy` /
  `WriteCapability` (239 行)。`tools/mutation_fanout.py` (1880 行) の group manifest・
  qstat identity parser・orphan 検出は**後続 wave の (a)(f) の素材**であり本 wave では触らない。
- **DW-G01 生死確認 (親が repo 外の使い捨て probe で実測)。** §6.3 の「filesystem を歩いて
  gitignored 未追跡まで走査」を repo root へ素朴に適用すると **158,011 file / 185 秒**。
  うち `.claude/` が **4.44 GB (全体 4.83 GB の 92%)** で、実体は並行 dev-wave の worktree 群。
  `.git` と `.claude` を除くと **12,627 file / 7.8 秒**。

## 親の provisional 裁定 (攻撃対象)

**(P1) 走査面は `.git` と `.claude/` を除いた repo 内容に限る。** 並行 dev-wave が
`.claude/worktrees/` を常時書き換えるため、含めると validator は投入前後で必ず差分を出し、
**恒常的に赤い = 測定が永久に承認へ到達しない gate** になる。除外は §6.1 の禁止領域
(calibration の attempt / staging / 登録先、campaign WAL、freeze journal、trial registry、
環境契約 registry) を 1 つも落とさない — いずれも `output/` と `orchestrator/` の下にある。
この「落とさない」ことを test で機械的に示す。

**(P2) `DurableRootPolicy` は (d) の方針注入に使うが、(e) の検出には使わない。** §6.1 が
「その API を呼ぶ経路の path 検査にすぎない・協調的 allowlist であって能力遮断ではない」と
明記しているため、検出側が同じ API に依存すると迂回面をそのまま継承する。(e) は独立に歩く。

**(P3) 凍結 artifact は `tools/pegasus/policies/t810_prereg_v1.json` に置き、digest を repo 内の
test が pin する。** 既存 policy JSON 群と同居させ、loader が実行時に digest 一致を検証する。

## 不変条件

- 既存 protocol の受理集合・凍結 bytes・proof chain・certified 選択結果を 1 byte も変えない。純増のみ。
- 絶対規律 2: 本 wave が作るのは fail-closed gate であり、緩める方向の変更を一切入れない。
- 親は実装面を直接編集しない (Codex `role=author` が書く)。親は brief・裁定・統合 commit・記録のみ。
- キューへ投入しない (ユーザー裁定)。

## 成果物の形

1. `tools/pegasus/policies/t810_prereg_v1.json` — §2 の測定 literal、§3.1 の build preimage 要求、
   §3.3 / §3.4 の閾値、§4 の N・R と設計目標と assurance 再現条件、§5.1 の区間式、§5.3 の対応表と
   gate 定義、§5.4 の終端状態表と retry 規則、§6.2 の期待集合と状態別 presence matrix。
2. 1 の loader + digest 検証 module (runner が実行時に照合する経路)。
3. 測定 runner の argv allowlist (calibration certify 系の実行を拒否する)。
4. §6.3 の単一 fail-closed validator の CLI — 投入前と投入後に同一実行し、inventory 差分が
   空でなければ非 0。
5. 上記それぞれの test。

## DW-G05 成果物影響

- **(4)(3) を作らない場合:** 測定 job が calibration 登録先・campaign WAL・freeze journal・
  trial registry へ書いても**誰も検出できず**、certified な選択結果と proof chain の受理集合が
  無言で汚染される。
- **(1)(2) を作らない場合:** runner が実行時に事前登録との一致を検証できず、N・R・閾値・
  判定規則の事後変更が検出されない = §5.3 / §5.4 の事後選択の余地が開く。

## 並列分割方針

実装子 2 本、所有ファイルを分離する。

- **子 A** = 凍結 artifact schema (1) + loader / digest 検証 (2) + その test。
- **子 B** = §6.3 validator (4) + argv allowlist (3) + repo 外 root 方針注入 (d) + その test。
