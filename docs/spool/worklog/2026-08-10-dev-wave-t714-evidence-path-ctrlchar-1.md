---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t714-evidence-path-ctrlchar
seq: 1
title: 証拠 path の CR/LF を両防壁で fail-closed 拒否した — 同じ機序が NUL でも成立することを実測し裁定へ返す (コード + docs、受入 7860 passed / 20 skipped / 475.31 秒 / rc=0、変異 13/14 KILLED + M13 訂正再走 KILLED・SURVIVED 0、branch worktree-dev-wave-t714-evidence-path-ctrlchar)
---

## 本文

- **裁定の一次資料。** rulings-inbox §56 (2026-08-10、発話「推奨通りで」) の
  **[T-714] = (a) CR/LF fail-closed 拒否**。選択肢集合は (a) 両層で CR/LF 拒否 /
  (b) NUL 区切り入力への移行 / (c) 現状維持。(b)(c) は不採用。
- **裁定前提の実測 (blob OID で照合)。** `read_blob_at(HEAD, "CLAUDE.md\r")` は
  `"CLAUDE.md"` と同一 blob OID `1744da0e…` を返す。alias は実在した。
  一方で**裁定文の前提は部分的に不正確**だった — `_safe_path` は末尾 CR/LF を既に拒否しており、
  ただしその理由は path 検査ではなく `_nonempty_string` の `value != value.strip()` という
  **付随的**な効果である。埋め込み CR/LF は素通ししていた。裁定の方向は変わらないため止めず、
  段 4 で再確認して実装した。
- **段 3 で親の実測自身が反証された。** 初回 probe は blob の**長さ**しか比べておらず
  「同一 blob」を実証していなかった。レンズ A の指摘を受けて OID / sha256 比較の probe v2 へ
  差し替え、以後の主張はすべて v2 を根拠にした。
- **NUL で同型の穴が残ることを親が独立に実測した。** `"CLAUDE.md\x00not-the-contract-path"` も
  同じ blob OID を返す (git が要求行を NUL で切り詰めるため)。`strip()` は NUL を落とさないので
  `_safe_path` も素通しする。**裁定 (a) の文言は CR/LF であり、承認外の gate を親が足さない**
  ため実装せず、選択肢付きの裁定パッケージでユーザーへ返す ({{T:evidence-path-nul-alias}})。
  tab は alias しない (missing) ことも実測した。
- **段 6 の敵対レビュー 2 本が独立に同じ迂回路を見つけた。** f-string は `__str__` ではなく
  `__format__` を呼ぶため、`__format__` を上書きした `str` サブクラスは
  「検査時は安全な値、git へ渡すときだけ CR/LF 入り」を実現できた。検査済みの文字を
  exact `str` へ固定してから spec を組む形へ直した ({{D:evidence-path-identity-wall}})。
- **変異 matrix。** 事前登録 14 件のうち 13 件 KILLED、SURVIVED 0、TIMEOUT 0。
  M13 (`read_blob_at` を無条件拒否にする過剰拒否の正例) だけ MISMATCH で、
  失敗 node は登録した 2 件を**含む 3 件**だった。余分な 1 件は契約 blob を読む registry 統合
  テストで、過剰拒否が原因である。実装・テストの欠陥ではなく**親の事前登録が不完全**だった。
  初回台帳は消さず erratum として残し、期待集合を訂正した M13b を再走して KILLED (完全一致) を得た。
- **受入 lease の待ち手を自分の欠陥で約 40 分空費した。** `claim` の出力は JSON なのに、
  runbook の例が示す `status` の key=value 形式で待っていたため `state=acquired` が
  永久に一致しなかった ({{F:lease-claim-output-is-json}})。
- **段 8 の未統合候補。** M13 の教訓 (変異の期待 node には間接 caller の統合テストも含める) を
  `DW-M08` へ 1 行入れようとしたが、`docs/dev-wave/**` は L1 も L1.5 も予算満杯で入らなかった。
  重複規則 1 文の削除で 67 bytes 空けても 23 bytes 足りず、**予算は上げない**方針どおり見送った。
  教訓は本エントリと insights に残す。空ける手当てを伴う別 wave で再訪する。
- 逐語と台帳は `output/insights/2026-08-10_t714-evidence-path-ctrlchar/`。

## 次の一手差分

### 完了

- [T-714] 裁定 (a) を実装した。`read_blob_at` は git へ渡す値そのものに、`_safe_path` は
  `_nonempty_string` より前に CR/LF を明示拒否する。受理集合の縮小は CR/LF を含む path だけで、
  正常 path・定数経路・現行契約は無変化。
  remaining: none
  base: 80255ac7cd125c0e646aef9c9c2aa853b2f7a689084f6f3ac228186491d7cbc5

### 新規

- {{T:evidence-path-nul-alias}} **P2・新規 (ユーザー裁定待ち)**: NUL 付き path が prefix blob へ
  alias する。[T-714] と**同型の既存欠陥**で、CR/LF を塞いだ後も残る。実測では
  `CLAUDE.md\x00not-the-contract-path` が `CLAUDE.md` と同じ blob OID `1744da0e…` を返した
  (git が要求行を NUL で切り詰める)。`strip()` は NUL を落とさないため `_safe_path` も受理する。
  影響は [T-714] と同じで、`EvidenceRef` の path / hash 対応、12 述語の status、
  activation report digest、certified 選択・trial ledger の参照が誤証拠で満たされうる。
  選択肢は (a) NUL も同じ 2 層で拒否 (推奨、実 git path に NUL は入れられないため正当な path を
  失わない)、(b) C0 制御文字一般へ拡張 (tab は alias しないので同一性の観点では過剰)、
  (c) 現状維持。従属所見として、直接 `read_blob_at` を呼ぶ経路には `./` 系 alias が残るが
  契約経路は `_safe_path` が既に拒否する。詳細は
  `output/insights/2026-08-10_t714-evidence-path-ctrlchar/ruling-package.md`。
