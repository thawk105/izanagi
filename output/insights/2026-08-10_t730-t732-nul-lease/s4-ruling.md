# 段 4 裁定とプラン v2 — [T-730] / [T-732]

親が段 3 の所見を real/refuted・採用/不採用・scope 内/外へ裁定した結果。

## 親自身の実測 (段 4 で追加)

- `evidence_contract_sha256()` (s8c_preregistration.py:340) は `_strict_json` + canonical 化だけで
  **`load_contract_bytes()` を通らない**。凍結発行 (:1725) と凍結検証 (:1412) はこれを直接使う。
  → **A1 は real。** brief の「tree entry 名に NUL は入らないので凍結台帳に NUL path は存在しえない」
  という**理由は誤り**だった。正しい根拠は内容検査であり、現行契約
  `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json` に `u0000` は **0 件**。
  よって「再発行は不要」という結論は維持する。
- D239 (decisions.md:11172) は「取得できた 1 本だけが受入を投入し、**受入と land の終端で必ず解放する**」
  と定義済み。→ **B2 は refuted。** runbook 794 行は D239 と矛盾しておらず、
  裁定 (b) 不採用とも整合する。release の時期は変更しない。

## 裁定表

| ID | 判定 | 処置 |
|---|---|---|
| A1 freeze 層に NUL gate なし | real / **scope 外** | 実装しない。承認は `_safe_path` と `read_blob_at` の 2 層のみ。**裁定パッケージへ** |
| A2 `str` サブクラスの `__contains__` 偽装 | real / scope 内 | **採用**。`_safe_path` も exact `str` を作ってから検査し、その値を返す (D267 と同型) |
| A3 変異の expected_nodes は完全集合 | real / scope 内 | **採用**。下の事前登録で runner を固定し、赤 node の完全集合を登録する |
| A4 probe の結論束縛が弱い | real / scope 内 | **採用**。親が probe v2 (blob 型・完全 OID・full digest を assert) を作り出力を保存する |
| A5 `bytes` / PathLike の意味 | real / **scope 外** | **不採用**。保証は D267 どおり「単一文字列化後の `text` が API 上の path」に限定する。裁定パッケージへ小項目で添える |
| A6 `_batch_oids` 等の他 sink | real / nit | **不採用**。現 caller は定数 path のみで hostile path が届かない。将来接続時の再発リスクを worklog へ残す |
| B1 `取り直し` が暗黙 | real / scope 内 | **採用**。`acquired` 後に `git rev-parse main` を取り直すことを明記する |
| B2 lease 粒度の矛盾 | **refuted** | 不採用。D239 が既に「受入と land の終端で解放」と定義。変更しない |
| B3 canonical waiter script が無い | real / **scope 外** | **不採用**。新 script は実装面の新機構で「runbook 改訂」の範囲外。**裁定パッケージへ** |
| B4 待ち手が `*acquired*` glob 判定 | real / scope 内 (縮小) | **採用 (1 句)**。`state` は exact 比較し部分一致で判定しないと明記する |
| B5 merge commit の provenance | real / scope 内 | **採用**。`DW-O17` を明示参照し AI-Agent trailer を要求する |
| B6 TTL と 2 走の lifecycle | 一部 real / scope 内 (縮小) | **採用 (1 句)**: 2 走すると TTL 2400 秒を超えるので 2 走目の前に `claim` し直す。fencing/renewal 機構の新設は **不採用** (D239 の受容済み限界) |
| B7 merge 後も残る race | real / 表現 | **採用 (表現)**。「再走をなくす」ではなく「待機中に land 済みの差分を吸収する」と書き、残余 race を明記する |
| B8 F196 の記述が stale | real / scope 内 | **採用**。F196 へ「F197 で改訂・[T-732] (a) で正本化」の 1 行を spool fragment で追記する |
| B9 brief の「予算内」表現 | real / 訂正 | **採用**。runbook に byte 予算は無い (§7.0 の構造検査のみ)。worklog で訂正する |
| 段 2 の補正 (`HEAD..main` 非 0 のときだけ merge) | real | **採用** |

## プラン v2 — [T-730] (実装子が書く)

- **H1'** `_safe_path` (s8c_preregistration_evidence.py:183): 検査前に exact `str` を作り
  (`text = "".join((value,))` と同型)、`"\x00" in text or "\r" in text or "\n" in text` を検査する。
  以後は exact `str` を使い、返り値も exact `str` にする。`isinstance(value, str)` 前置と
  `_nonempty_string` より前という順序、reason code `contract-path-control-char` は維持する。
- **H2'** `read_blob_at` (s8c_preregistration.py:960): 既存 `text` の検査へ `"\x00"` の選言を足すだけ。
  reason code `path-control-char` を維持する。
- **H3'** core 側テスト: NUL alias の拒否 (`trailing-nul` / `embedded-nul`)。NUL 名のファイルは作らず、
  NUL 前の prefix blob を実在させ、`_legacy_unframed_blob` が prefix blob を返すことを**先に**立証する。
- **H4'/H5'** predicates 側テスト: 既存 CR/LF parametrize へ NUL を追加 (`required-nul`,
  `consumer-nul`, `trailing-nul`)。例外文字列に生の制御文字が出ないことも assert する。
- **H6a'** 正例 (層 1): 埋め込み TAB を持つ path の契約が `load_contract_bytes` を**通る**。
- **H6b'** 正例 (層 2): 埋め込み TAB を持つ実ファイルを `read_blob_at` が**読める**。
  H6 を 2 test へ分けるのは、層 1 の過剰拒否変異と層 2 の過剰拒否変異を別 node で殺し分けるため。
- **H7'** (A2) 回帰テスト: `__contains__` を偽装した `str` サブクラス (埋め込み `\r` を持つ) を
  `_safe_path` へ渡すと `contract-path-control-char` で拒否される。
  exact `str` 固定を外すと reason が変わる (または受理される) ため単一理由で赤くなる。

**受理集合の縮小は NUL を含む path と、membership を偽装する `str` サブクラスだけ。**
NUL-free の exact `str` 入力の受理・拒否・reason は不変。C0 一般へ広げない。

## プラン v2 — [T-732] (親が書く、docs のみ)

`docs/pegasus-runbook.md` §7.3 の該当 bullet を置換し、次を満たす。

1. `acquired` の直後に**待ち手自身が** `git rev-parse main` で local main を取り直す (B1)。
2. `git rev-list --count HEAD..main` が**非 0 のときだけ** `git merge --no-ff --no-commit main` →
   `git commit -F <message file>`。`--ff-only` と `--no-edit` は使わない (段 2 補正)。
3. merge commit の provenance は `DW-O17` に従う (AI-Agent trailer) (B5)。
4. merge 後に `HEAD..main` を再検査し、0 でなければ投入しない。競合時は `git merge --abort` →
   `release` → 親へ戻す。
5. `claim` の判定は `state` の **exact 比較**とし、部分一致で判定しない (B4)。
6. claim loop・取り直し・merge・受入投入は同じ待ち手 script に置く。
7. 受入を 2 走すると TTL 2400 秒を超えるので 2 走目の前に `claim` し直す (B6)。
8. これで無くなるのは「待機中に land 済みの差分」による再走であり、
   再検査から投入までの残余 race は残る (B7)。

## 変異事前登録 (`DW-M01`)

runner = `orchestrator/tests/test_s8c_preregistration_core.py` と
`orchestrator/tests/test_s8c_preregistration_predicates.py` の 2 file (`--force-dispatch` 必須)。
expected_nodes は各変異で赤くなる **完全集合**を書く (A3)。

| # | 変異 (単独適用) | 期待赤 node (完全集合) |
|---|---|---|
| M1 | `_safe_path` の条件を **wave 前の逐語** `("\r" in ... or "\n" in ...)` へ戻す | predicates `[required-nul]`, `[consumer-nul]`, `[trailing-nul]` の 3 node |
| M2 | `read_blob_at` の条件を **wave 前の逐語** `"\r" in text or "\n" in text` へ戻す | core `test_read_blob_at_rejects_nul_alias[trailing-nul]`, `[embedded-nul]` の 2 node |
| M3 | `_safe_path` を C0 一般拒否 (`ord(ch) < 0x20`) へ過剰一般化 | H6a' の 1 node (層 1 の正例) |
| M4 | `read_blob_at` を C0 一般拒否へ過剰一般化 | H6b' の 1 node (層 2 の正例) |
| M5 | `_safe_path` の exact `str` 固定を外し元の value 上で検査する | H7' の 1 node |

- M1 / M2 は wave 前の実コードの形そのものである (禁止したい形の同型変異)。
- M3 / M4 は**承認外の過剰拒否**を検出する正例側の変異 (`DW-M01` の要求)。
- 単一理由性: M1 は層 2 に mask されない (`_safe_path` は `load_contract_bytes` 内で先に発火し、
  NUL path は git へ渡る前に契約 loader で止まる経路を測る)。M2 は `read_blob_at` の直接呼出しで測る。
  M5 は H7' が層 1 の exact 化だけを見るため単一。
- 実装後、`DW-M07` に従い anchor 逐語と期待 node を再検証してから本走する。
- 走行は `tools/mutation_worktree.py --commit <統合 commit>` の使い捨て worktree で行い、
  主 tree を変異させない (`DW-O19` の新経路)。

## 裁定パッケージ (ユーザーへ返す — 本 wave では実装しない)

1. **(A1) 凍結層の NUL gate。** `evidence_contract_sha256` は `load_contract_bytes` を通らないため、
   NUL path を含む契約を凍結記録へ束縛できる (発効は後段で `evidence-contract-invalid` に倒れる)。
   選択肢 = (a) 凍結発行・検証にも NUL-only 検査を広げる / (b) 「invalid contract も凍結可能だが
   発効不能」という現行境界を維持し保証文をそこへ狭める / (c) `load_contract_bytes` 全体を流用する
   (NUL 以外も拒否するので受理集合が変わる。非推奨)。親の推奨 = (a)。
   成果物影響 = (b) のままなら凍結台帳・proof chain の受理集合に NUL path 契約が残りうる。
2. **(A5) 非 `str` 入力の契約。** 保証を「単一文字列化後の `text`」に限定するか (現行・推奨)、
   `bytes` / PathLike 自体も検査対象にするか。後者は既存受理集合を変える。
3. **(B3) canonical な受入待ち手 script。** runbook の散文手順のままにするか、
   `tools/` に正本 script を新設して docs から参照するか。後者は実装面の新機構。
   成果物影響 = 散文のままなら consumer が merge を省いて受入を投入し、受入結果が land 不能になる。
