# 段 6 所見の親裁定 — [T-455]

レンズ A (受理集合の漏れ) / レンズ B (過剰拒否・契約整合・検出力) の 2 本を read-only codex で並列実行。
両者とも rc=0、`tools/check_codex_output.py` rc=0。所見は 9 件 (real 6 / refuted 5、重複を含む)。

## real・scope 内 → 本 wave で fix (1 件)

### F-1 (= B-03 由来) sibling control が未裁定の拒否を pin していた

- **実測:** `tools/pegasus/README.md` §3 は `collect_receipt.py` を「job 終了後、**ログインノード**で」
  実行すると定めるが、hook はこれを rc=2 で拒否する (親が実 hook subprocess で再現)。
- **裁定:** real。ただし**拒否そのもの**は本 wave 前から存在し、scope 外 (下記 R-3)。
  scope 内なのは「本 wave の新テストが、その未裁定の拒否を*守るべき性質*として pin したこと」。
- **fix:** control を `collect_receipt.py` → `certify_calibration.sh` (計算ノード側 job script、
  login 手順として文書化されていない) へ差し替える。`hooks/guard_bash.py` の受理集合は不変。

## real・scope 外 → 裁定パッケージでユーザーへ返す (3 件)

### R-1 (= MF-A1 = B-01) sanctioned は path 粒度で、未計測 argv まで開く

- **実測:** `python3 tools/pegasus/fetch_third_party.py fetch --repo-root /work/alternate
  --cache-root /work/cache` は rc=0 で通る。`--repo-root` は別 repo の policy/pin を読み、
  そこから 3 repository を clone しうる。runbook は入力上限のない経路を `unknown` =
  `dispatch-required` と定める (`docs/pegasus-runbook.md:358-360`)、実測表は現 pin 限定 (`:406-417`)。
- **裁定:** real。ただし **scope 外**。理由は 3 つ。
  1. sanctioned 機構は**全 5 entry が path 粒度**であり、argv を測定 tuple へ束縛する仕組みが
     そもそも存在しない。本差分はこの性質を新設していない。
  2. 実効修正には argv/env を含む admission、CLI 自身の site gate、入力 cap のいずれかが要る。
     これはユーザーが**不採用にした択 (b)** (実測分類に基づく allowlist/denylist) の領域である。
  3. 裁定の前提を覆す「未見の新事実」ではない。runbook 自身が分類の pin 限定を land 済みで
     明記しており、裁定文はその runbook を根拠に引いている。よって `DW-STOP` の停止条件に当たらない。
- レンズ A は scope 内 must-fix と判定したが、レンズ B は scope 外と判定した。親は B を採る。
  A の主張する fix (comment での限定) は受理集合を 1 bit も閉じないため、DW-G05 の
  「実装しなければ成果物のどの値が変わるか」に対して有効な対処になっていない。

### R-2 (= SO-A2 = B-02) `-m <他 module>` の sanctioned 借用

- **実測:** `python3 -mpytest tools/pegasus/submit_certify.sh` は**本差分の前から** rc=0 で通る。
  借用抑止 `_provenance_script_borrow` は `check_ai_provenance.py` の basename にしか効かない。
  非 sanctioned な `exec_calibrate.py` では rc=2 で借用不可。
- **裁定:** real / scope 外。既存 sanctioned 4 entry で成立済みの族欠陥で、本 wave は 5 件目の
  別名を足すだけ。新しい欠陥類型ではない。親 brief (P2) を両レンズとも支持。

### R-3 (= B-03 の実体) land 済み login 手順が hook に拒否される — 独立 2 例目

- **実測:** `collect_receipt.py` の README §3 手順が rc=2 で拒否される。
- **裁定:** real / scope 外。**重要:** これは [T-455] (fetch_third_party.py) と**独立同型の 2 例目**
  であり、`DW-G03` の「族全体への制度一般化は同型欠陥が異なる producer/consumer で独立に
  2 件再現したときだけ許す」が**充足された**。すなわち、裁定時に射程が広いとして退けられた
  択 (b) (一律 `tools/pegasus/` 判定を実測済み分類に基づく allowlist/denylist へ変える) に、
  制度化の根拠が揃った。ユーザー再裁定へ返す。

## real だが既知限界の射程内 → 記録のみ (3 件)

- **SO-A3** path identity が字面束縛 (`realpath` を追わない、先行 `cd` を追わない)。
- **SO-A4** `xargs` 越しは head が `xargs` のままで素通り (本差分の前から)。
- **SO-A5** quoted `$(...)` / here-doc の backtick は sanctioned segment に隠れる (本差分の前から)。

いずれも `hooks/README.md` と D103/D105 が「hook が新規に閉じるのは非 sanctioned な綴りだけで、
script file 越し・`python3 -c`・Codex 子・ユーザー端末は原理的に見えない」と明記済みの射程内。
本差分が新しい類型を作っていない。insights へ逐語で残す。

## refuted (5 件)

- **RF-A6** wrapper (`bash -c` / `env` / `nohup` / `timeout`) 越しは最終 head が exact script になり、
  `;` `&&` `|` 改行での別 head 同居は segment 分割で拒否される。
- **RF-A7** 通常 argv で別 Pegasus 実行体を起動する形は通らない (module target が先に解決される)。
- **RF-A8 / B-R2** 追加テストの検出力は実在する。1 行削除で 2 node が確実に赤。
  恒真・site 指定漏れ・tuple 受け取り違い・揮発値の焼き込みはいずれも無い。
- **B-R1** `hooks/README.md` へ一覧を写していない (契約維持)。module 綴り
  `python3 -m tools.pegasus.fetch_third_party` も `_python_module_target` で解決され通る。

## 親 provisional 裁定の帰結

- **(P1)** 「1 行追加で足り分岐変更は不要」= **成立**。両レンズとも分岐変更の必要を示せていない。
  A が「refuted」としたのは実際には P1 の主張範囲外 (argv 束縛の話) であり、P1 自体は維持。
- **(P2)** 借用は scope 外 = **成立**。両レンズが支持。
- **(P3)** 軽量版で足りる = **成立**。成果物の受理集合は不変 (B-R2 / B の P3 評価が支持)。
  ただし段 6 レビュー 2 本を残した判断は正しかった (R-3 という独立 2 例目を発見した)。
