# T-338 単位5: 実装しなかった vector authority resolver の設計メモ (将来 K2/K3 waveへの申し送り)

本書は `{{D:t338-unit5-vector-authority-fail-closed}}` (docs/decisions.md、2026-08-21) が
「今回は実装しない」と裁定した汎用 supersession chain resolver について、実装しなかった理由と、
将来これを実装する wave (T-139 K2/K3、実際に vector-bearing な approval payload を発行する wave)
が入力とすべき設計要件を記録する。**本書自体は設計を確定しない** — 次に着手する wave が段1 brief
・段2 codex plan で再検証すべき出発点である。

## なぜ実装しなかったか

D574 決定(4)は「vector index の期待 digest 三つ組は manifest 自身ではなく、有効な approval
payload に置く。resolver は `approval_fold_commit` から有効な payload を解決し、その payload の
三つ組と manifest の宣言を照合しなければならない」と定める。しかし 2026-08-21 時点で:

- `orchestrator/preregistration/approval_payload.py` は D282 専用の固定 fenced block parser
  であり (`_D282_HEADING_RE`、固定 commit `D282_DECISIONS_REF`)、D574 自身は D282 と同型の
  機械可読 payload を持たない (通常の decision 散文、`forward_supersedes` で自分を D282 の
  後継と宣言してもいない)。
- したがって「vector index 三つ組を持つ有効な approval payload」は今日のrepoに1件も実在しない。

段2 codex plan が提案した汎用 resolver (`_resolve_effective_approval`/`_DecisionRef`/
`_EffectiveApproval`、supersession chain walk、cycle 検出、複数 candidate 拒否を含む) を、
実在する入力artifactが無いまま実装すると:

1. **D563 token sealing 規約が欠落しやすい** — 段3敵対相談レンズBが、提案された型が単純な
   public dataclass (token 検査なし) であり、D563 が既に一度実際に踏んだ脆弱性 (偽造可能な
   manifest/binding) の再演になると指摘した。
2. **writer 入口の signature と resolver の入力経路が実は繋がらない** — resolver は
   `base_approval_fold_commit`/`approval_fold_commit`/`manifest_vector_index` を要求するが、
   `_publish_receipt` の入口は `repository_root`/`raw_bytes`/`binding` だけであり、既存の
   `_PreregBinding`/`PreregistrationRecord` にはこれらの値を運ぶ field が無い。
3. **二重 loader になりうる** — `_manifest.py` は既に `load_approval_payload()` を呼んで
   binding 発行時に D282 を読み込んでいる。新しい resolver が同じ loader をもう一度呼ぶと、
   検査の重複・整合性再確認の欠落を招きうる。

これら3件はいずれも「発火 artifact が無いまま実装した」ことに起因する具体的な実装欠陥であり、
DW-G04 (発火条件を満たす既存 artifact path が無い条件付き機能は設計メモに留める) と規律5
(盛らない) に照らし、今回は実装しないと裁定した。

## 将来 wave が入力とすべき設計要件

実際に vector-bearing な approval payload を発行する wave (K2/K3、または D574 準拠の新しい
exact-byte approval payload を発行する wave) が本機構を実装する際は、次を出発点にする。

1. **root の二段構成** (D574 決定5): `base_approval_fold_commit` (固定、D282 の fold commit
   `39d760985a5e37d20464c394760bf65596156566`) / `approval_fold_commit` (現在有効な decision の
   fold commit、初期値は base と同じ、将来 supersession 後は resolver が解決)。
2. **`forward_supersedes` の構造化**: 現行 `ApprovalPayload.forward_supersedes` は自由文字列の
   `tuple[str, ...]` であり、decision ID や commit の構造化参照ではない。successor payload を
   機械的に発見するには、これを構造化参照 (decision ID + fold commit の組) へ拡張する必要がある。
3. **cycle・欠落・複数候補の拒否**: supersession chain を辿る resolver は、循環参照・chain の
   途中欠落・複数の有効候補が同時に存在する状態を明示的に拒否する設計にする。
4. **writer 入口への配線**: `_publish_receipt` (または後継) が resolver の出力を受け取る経路を
   新たに設計する。既存の `_PreregBinding`/`PreregistrationRecord` を拡張するか、別の capability
   を新設するかは、その時点の凍結境界・D563 規約を踏まえて再検討する。
5. **D563 token sealing の継承**: 新しい型はすべて module-private capability token・
   keyword-only 必須引数・digest 固定後の凍結という既存規約に従う。単純な public dataclass に
   しない。
6. **二重 loader の回避**: `approval_payload.py`/`_manifest.py` の既存 `load_approval_payload()`
   呼び出しと重複しない設計にする (一度読み込んだ sealed authority を下流へ渡す、または
   二重読みにする場合は fold commit・root identity・bytes 一致を明示検査する)。

## 副産物: AST allowlist の import-alias 迂回という既知限界

単位5の別経路 publish 抑止 (`test_receipt_publish_call_sites_are_path_aware_and_allow_event_sink`)
は、`create_receipt_bytes`/`create_only_relative_bytes` への直接呼び出しを AST 走査で検出する。
親が変異検算中に、`import ... as <alias>` で別名 import して呼び出すとこの検査を迂回できることを
発見した。これは D563 が既に認めた「Python の private 名は import されれば偽造できる」という
限界と同種であり、今回は fix 対象にしなかった (意図的な迂回への防御ではなく、素朴な直接呼び出し
への抑止力として機能する軽量ガードという位置づけ)。将来、この抑止を強化する場合は、呼び出し名の
文字列一致ではなく import 解決先 (qualified name) を辿る実装にする必要がある。
