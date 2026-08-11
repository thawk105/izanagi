# [T-787] 段 1 brief — 凍結発行・検証層で CR/LF path を fail-closed 拒否する

## scope と確定裁定

- 裁定 (worklog 408、確定): [T-787] = (a) CR/LF を含む証拠 path の契約を、NUL と同じ扱いで
  凍結発行・履歴検証の層でも fail-closed 拒否する。設計は D281 (単一 choke point) の CR/LF 拡張、
  [T-739] 実装と同型に揃える。現行契約に該当 0 件のため移行なし。
- 編集面: `orchestrator/campaign/s8c_preregistration.py` の choke point 検査 1 関数と、
  `orchestrator/tests/test_s8c_preregistration_core.py` のみ。発効層
  (`s8c_preregistration_evidence.py` `_safe_path`) は触らない。

## 段 1 実測 (親、2026-08-11)

- 穴の実在: CR / LF 入り path 契約は `evidence_contract_sha256` を通り hash を返す
  (CR: `00205cec…`、LF: `e7e1e585…`)。同じ契約は発効層が `contract-path-control-char` で拒否
  → 「凍結可能だが発効不能」の非対称が CR/LF に実在。
- NUL 入りは凍結層が `evidence-contract-path-nul` で拒否 (T-739 実装は生きている)。
  NUL+CR 併存も理由語は NUL (現状の優先順)。
- 現行契約 hash は `c4f3740202de302c…` (worklog 406 の値と一致、CR/LF 該当 0 件、移行なし)。
- pin 閉包 (DW-O09 判定): module bytes は FROZEN_MANIFEST 非対象。理由語
  `evidence-contract-path-nul` の消費は module 内 raise 1 箇所とテストのみ。
  `freeze_reason_code` は report の揮発 field。条件 09/10 不成立。
- 既存被覆 (性質で検索): 凍結層の CR/LF **拒否**被覆は 0。逆に
  `test_evidence_contract_hash_accepts_non_nul_path_controls` (4 param、exact hash 固定) が
  「CR/LF は凍結層で受理」を固定しており、本 wave の反転対象。発効層は
  `contract-path-control-char`、`read_blob_at` 層は `path-control-char` で被覆済み (別層、scope 外)。
  純増検出力 = 凍結層の CR/LF 拒否のみ。

## 不変条件

1. 受理集合の変化は 1 点だけ: parse + canonical 化に成功する入力のうち、key exact `path` の
   `str` 値に CR (U+000D) または LF (U+000A) を含むものが新たに拒否される。path 以外の field の
   CR/LF、NUL を含まない schema 違反、その他の制御文字は従来どおり通る (過剰拒否しない)。
2. NUL 入り入力の拒否理由語・pointer・優先順位は 1 つも変わらない (NUL+CR 併存は NUL 語のまま)。
3. 現行契約 hash `c4f3740202de302c…` と既発行 g1 record の `protected_sha256` は不変。
4. 検査位置は canonical 化成功の後・hash 返却の前 (D281 のまま)。走査は明示 stack、
   detail は `repr(JSON pointer)` だけで生 path を載せない。
5. 契約 schema の検証はしない (load_contract_bytes の流用は D281 で却下済み)。

## 親の provisional 裁定 (攻撃対象)

- (P1) 理由語: NUL は `evidence-contract-path-nul` のまま、CR/LF は新語
  `evidence-contract-path-crlf`。node 内の検査順は NUL → CR/LF とし、既拒否入力の理由を変えない。
  (代案: 発効層に合わせた統一語 `…-control-char` へ改名 — NUL の診断契約が変わり
  T-739 のテスト群を書き換えるため採らない)
- (P2) 実装形: 既存 `_assert_no_nul_in_contract_paths` を同一走査内で拡張し
  `_assert_no_control_chars_in_contract_paths` へ改名 (私有 helper、外部消費なしは実測済み)。
  検査関数の追加・走査の二重化はしない (choke point 1 箇所・走査 1 回を保つ)。
- (P3) テスト形: [T-739] と同型 — 38 path 位置の全数 parametrize を CR/LF にも適用、
  中間位置、NUL との併存優先順位、非 path field の CR/LF escape 受理 (exact hash)、
  現行契約 hash 不変、を固定。既存の CR/LF 受理固定テスト 4 param は拒否側へ反転。

## 成果物影響 (DW-G05)

実装しない場合、凍結台帳・proof chain の受理集合に CR/LF path 契約が残り、凍結・履歴検証は
通るのに発効時だけ `contract-path-control-char` で倒れる非対称が残置される (T-787 起票逐語)。

## 分割方針・段構成

- 正しさ防壁 + 受理集合の変更なので敵対検証子は省かない: 段 2 起草 1 本 → 段 3 レンズ 2 本並列
  (`gpt-5.6-sol` / `gpt-5.6-luna`) → 段 4 裁定 + 変異事前登録 → 段 5 実装子 1 本
  (module + tests を単独所有) → 段 6 レビュー 2 本並列 + fix + 変異 matrix + 受入全走 → 段 7〜9。
- 変異事前登録は wave 前の実コードの形 (NUL-only 検査) の revert 変異を必ず含める。
- 受入・実測環境: Pegasus。テスト実走は親が担う (子 sandbox は pytest 不可、DW-O05)。
  変異 runner は dispatch recipe (`--force-dispatch`)。受入全走は背景投入 + lease claim。
