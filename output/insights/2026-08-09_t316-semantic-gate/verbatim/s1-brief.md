# 段 1 brief — [T-316] 意味 gate 設計択一の裁定パッケージ

## scope
[T-316] の残余「意味 gate」本体を裁定する。`tools=[]` + JSON schema では次の 2 脅威を止められない。
- **脅威 α (coder injection):** hole 内 1 行の `std::system`/`execl`/`std::ofstream`/無限ループが
  `DiffQuarantine` を通る (D127 背景で実測済み。`util.hh` 経由で追加 include なしに POSIX 原始関数へ届く)。
- **脅威 β (auditor echo):** `auditor_gate.py` は `diff_digest` が実 working_diff と一致することしか
  照合しない。auditor が実 diff の digest を計算し `verdict="pass"` + `violations=[]` を返せば全検査を通る。
  「この diff を見たか」は証明するが「安全か」は証明しない = **fail-open by construction**。

3 案の比較を実測付きで作る: (i) coder 出力を許可識別子・enum・論理演算だけの boolean-expression
AST/DSL へ落とす、(ii) build/run を credentialless・network 無し sandbox へ置く、(iii) 両方。
**本番コード編集なし。実装差分ゼロの裁定パッケージで終端 (4→7→8→9)。**

## 確定済み事実 (一次資料実測)
- **F1.** D127 で [T-316] は一度 land 済み。ただし意味 gate 本体 (a)/(b)/(c) は decisions.md D127
  決定(1) が明示的に「別 wave へ分離」。現状 gate = `build_admission.py` の `CODER_AUTHORED` opt-in
  (未分類 source を build 拒否) のみ。`--allow-coder-derived-build` を付ければ coder 由来 source は
  full-privilege で build/run する。この opt-in は「検出器でも意味 gate でもない」と D127 決定(4) が明記。
- **F2.** 三軸の hole 文法が非対称。backoff=スカラー値、trigger-gating=5-bit wire、
  sort-strategy=comparator コード片 (raw C++、複数行を契約上許可、coder.md §触ってよい範囲)。
  D127 決定(1): sort 軸へ consumer DSL を課すと producer 契約と非互換、
  「合成が事前 allowlist からの選択に化ける」→ 規律5 と Phase3 の合成能力実証 (D39) を毀損。
- **F3.** sandbox backend は login node で実測: bwrap/unshare/setpriv 在、`unshare -rn` OK、
  `bwrap --unshare-all` OK、`bwrap --unshare-net` は実ネット到達を遮断、seccomp 有、landlock 不在。
  D127 決定(1) が (b) を却下した根拠は「pegasus-runbook に backend 記載 0 件 → DW-G04 不成立」であり
  **backend 不在ではない**。記載を作れば DW-G04 の発火 artifact になる。
- **F4.** build/run は qsub で計算ノードに投入 (pegasus-runbook §1)。sandbox は計算ノード側。
  login node の実測が計算ノードへ転移するかは**未計測** = (ii)/(iii) の DW-G04 決定的計測。

## 不変条件 (絶対規律。緩めない)
- 規律2: 正しさゲートを緩める方向は不採用。**sandbox は脅威 α/β の blast radius を絞るが、
  verifier reward hack (規律2 本体) は塞がない** — 別脅威、混同しない。
- 規律3: gate は pass/fail でなく構造化理由を返す。
- 規律5: 段階導入・盛らない。研究目的 (LLM synthesis の実証) を毀損する封じ込めを選ばない。
- 規律6: 入力 (coder diff / auditor verdict) はデータであり指示でない。

## 成果物の形
裁定パッケージ (worklog + insights の R1〜Rn)。実装差分ゼロ。将来の実装 wave の前提条件
(docs 予算 [T-664]、stage matrix 所有 [T-184]、計算ノード backend 計測) と事前登録方針を含む。

## provisional 裁定 (P。攻撃対象)
- **(P1)** 脅威 α と β は別レイヤ。(i) は α を source で構造的に消し、β を非 load-bearing 化する
  (安全性が auditor 判定に依存しなくなる)。(ii) は α/β の run-time blast radius を絞るが source では消さない。
  → 単独では **(ii) を中核、(i) は scalar/wire 軸のみ補助** が最有力。sort 軸へ (i) を課すのは synthesis 毀損。
- **(P2)** よって **(iii) 両方**が実体だが、「両方」の意味は「全軸に両方」ではなく
  「(ii) を全軸の security boundary、(i) を scalar/wire 軸に限定した追加層」。全軸一律 (i) は却下。
- **(P3)** 本 wave は実装しない。決定的計測 (計算ノード backend) と docs 予算が揃うまで実装 wave を起票しない。
- **(P4)** auditor echo (β) の**独立**対策として、auditor の判定を security credit から外す
  (advisory 化は D127 決定(6) で既に部分的に宣言済み) ことと、封じ込めを auditor 非依存にすること
  を明記する。これは (i)/(ii) いずれを採っても必要な横断条件。
