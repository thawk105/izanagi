---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1148-verifier-opcount
seq: 1
---

## {{D:verifier-framing-violation-structured-return}}. verifier の予定操作数不一致を既存 dataclass 再利用で構造化返却する

**決定:** `orchestrator/verifier/parse.py` の `TxnFramingViolation` (kind/txid/expected・observed
reads・writes を完備) を新規 dataclass を発明せず再利用し、`orchestrator/verifier/model.py` の
`Integrity` へ `framing_violation_details: List[TxnFramingViolation]` として全件保持する。
`core.py` は既存の集計 int・text note ロジックを変えず、この新フィールドへの代入を1行追加する
だけにする。`report.py` の `result_to_dict()`/`render_text()` で構造化 serialize する。
「G2 anomaly と同型」とは cycle/SCC アルゴリズムの流用ではなく、**構造化 dataclass →
`VerifyResult` 格納 → `report.py` serialize** という返却の形の踏襲だと解釈する。

**理由:**
- `parse.py` は既に必要なフィールドを完備した構造化データを全件計算していたが、`core.py` が
  集計 int と先頭 5 件だけの平文 note に潰して捨てていた。既存データを流用するだけで閉じる。
- verdict/serializable/certified の判定ロジックへ一切触れない (絶対規律2) — 既存シグナルへの
  追加構造であり新しい正しさ判定ではない。
- `_VerificationCapability` の `_result_sha256` は `result_to_dict()` の projection をハッシュ
  入力にするため、新フィールドは `trace_dir` と同じ扱いで `projection["integrity"]` から
  pop しハッシュ安定性を保つ。

**却下した選択肢:**
- 新規 `OperationCountAnomaly` 相当の dataclass を発明する案 — `TxnFramingViolation` が既に
  必要なフィールドを完備しており、車輪の再発明になる。
- `orchestrator/critic/digest.py` へ専用の分類文言を今回同時に追加する案 —
  {{D:verifier-framing-violation-digest-classification-deferred}} で別途扱う。

## {{D:verifier-framing-violation-digest-classification-deferred}}. digest.py への専用分類行の追加は次wave以降へ延期する

**決定:** `orchestrator/critic/digest.py` の `lock_coverage_violations`/`write_intent_violations`
と対称な「分類: ...次手は...」行を `framing_violation_details` にも追加する案は、今回は実装せず
延期する。`Rejection.integrity` は無制約 dict でありパススルーは既に機能しているため、
延期してもデータそのものは (整形されない粗い形で) critic まで届く。

**理由:**
- 構造化データを JSON へ返す本体機能と、それを critic がどう見せるかは独立した価値単位であり、
  後者を切り離しても前者の価値は成立する (段階導入、規律5)。
- 分類行の文言には「宣言 read/write 件数の差分」を実際の DSG 依存辺 (ww/wr/rw) の特定であるかの
  ように読める誤解リスクがあり、より正確な文言の検討が要る。
- 分類行を書くコードは details の型・shape を検証しないと旧 WAL・不正 payload で renderer が
  例外化しうる。今回このコード自体を書かないためリスクごと避けられる。

**却下した選択肢:**
- 今回同時に分類行も実装する — 規律5 (盛らない) に反し、上記の文言・shape 検証という別途の
  設計判断を急いで済ませることになる。
- 分類行を永久に実装しない — 判断を保留しただけで、着手自体は否定しない。
