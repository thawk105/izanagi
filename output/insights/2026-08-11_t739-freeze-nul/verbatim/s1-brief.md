# 段 1 brief — [T-739] 凍結発行・検証層への NUL 検査拡張

## scope

`orchestrator/campaign/s8c_preregistration.py` の `evidence_contract_sha256()` が、evidence contract の
`path` field に NUL を含んでいても hash を返してしまう穴を fail-closed で塞ぐ。凍結発行
(`prepare_revision`, l.1725) と履歴検証 (l.1416) はこの関数を直接呼び、`load_contract_bytes()` を
通らないため、NUL path 契約を凍結記録 (`protected_sha256`) へ束縛できる。

## 確定済みユーザー裁定 (2026-08-10 /rulings、一次控え rulings-inbox §520)

- **(a) 採用**: 凍結発行・検証にも **NUL-only** 検査を広げる。
- (b) 「invalid contract も凍結可能だが発効不能」という現行境界の維持は**不採用**。
- (c) `load_contract_bytes` 全体の流用は**不採用** (NUL 以外も拒否し受理集合が変わるため)。

## 裁定前提の実測 (済、DW-S01)

`core.evidence_contract_sha256(NUL 入り契約)` → `524df6b9…f0e30` を返して受理。
`ev.load_contract_bytes(同)` → `contract-path-control-char` で拒否。前提は成立、覆す新事実なし。
NUL は raw byte でなく JSON の `\u0000` escape で到達する (strict JSON は生制御文字を拒否)。
**raw bytes の走査では検出できない。検査は parse 後の値に対して行う。**

## 既存被覆 (性質で検索) と純増検出力

既存の NUL 拒否は `_safe_path` (契約 loader) と `read_blob_at` (git へ渡す値) の 2 層のみ
([T-714] CR/LF、[T-730] NUL)。「契約 hash を計算する層」を対象にした NUL テストは 0 件。
**純増検出力 = `path` field に NUL を含む契約が凍結発行と履歴検証を通過してしまうことの検出。**

## 不変条件

1. NUL を含まない入力に対する受理集合・reason・reason 順序は 1 つも変えない。CR/LF・schema 違反は
   従来どおり `evidence_contract_sha256` を通る (それが (c) 不採用の意味である)。
2. 現行契約の hash は不変: `evidence_contract_sha256(現行 v1.json)` =
   `c4f3740202de302c9dafc9cecac39165bc2213ebf425d2da8cf7ede91b264471`。既発行の
   `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g1.json` は 1 byte も変えない。
3. 例外メッセージへ生の NUL を漏らさない (既存 2 層のテスト契約と同じ)。
4. 規律 2: 正しさゲートを緩める方向の変更を採らない。検査は fail-closed。

## 成果物の形

- 実装: `orchestrator/campaign/s8c_preregistration.py` に NUL 検査を 1 箇所追加。
- テスト: `orchestrator/tests/test_s8c_preregistration_core.py` を主とし、凍結発行・検証の
  E2E で「NUL path 契約が凍結できない」ことを固定する。
- docs: worklog / decisions / insights (段 7)。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 設置箇所** = `evidence_contract_sha256()` 内、`_strict_json` の後・`_canonical_bytes` の前。
  単一 choke point で発行 (l.1725) と検証 (l.1416) の両方を同時に閉じる。呼出し側 2 箇所へ個別に
  置くより閉包が強い。
- **(P2) 検査面** = parse 後の値を再帰走査し、**mapping の key が exact `"path"` かつ値が `str` で
  NUL を含む**ものだけを拒否する。理由: loader が path として読むのは
  `conditions[].required_evidence[].path` と `conditions[].consumer_requirement.path` の 2 箇所だけで、
  現行契約でも `path` key はこの 38 箇所しかない。全 string への一般化は `static_only_note` など
  loader が NUL を許す field まで拒否し、loader と凍結層の乖離を逆方向に作る。
- **(P3) reason code** = 新規 `evidence-contract-path-nul`。detail は入力由来文字列を素通しせず、
  `repr()` で escape した JSON pointer だけにする (先例: `read_blob_at` は detail なし、
  `_safe_path` は `repr(where)`)。
- **(P4) CR/LF は scope 外**。同層に同型の穴が残るが、(c) 不採用の射程に入るため段 4 で
  real / scope 外に裁定し、裁定パッケージでユーザーへ返す。本 wave では実装しない。

## 成果物影響 (DW-G05)

実装しない場合、凍結台帳 `output/s8c-preregistration/condition-freeze/*.json` の
`evidence_contract_sha256` / `protected_sha256` が NUL path を含む契約に束縛されうる。すなわち
proof chain の受理集合に「凍結はできるが発効すると `evidence-contract-invalid` で倒れる契約」が
残り、凍結記録が指す契約と実際に読める契約が別物になる。現行契約の NUL は 0 件なので既存成果物の
値は変わらない。

## 分割方針

実装面は 1 実装ファイル + テストで小さいため実装子は 1 本。段 3 の敵対レンズは 2 本
(`gpt-5.6-sol` → `gpt-5.6-luna`)、段 6 のレビューも 2 本。
**軽量版にはしない** — 正しさ防壁 (凍結・proof chain) に触り、受理集合が変わるため DW-C00 により
段 2・3・6 の敵対子を省略できない。

## 環境

Pegasus login node で pytest。受入全走は runbook §7.3 の lease を `claim` し `state=acquired` の
ときだけ背景投入する (並行 wave 6 本稼働中、待ちは 10〜30 秒周期)。
