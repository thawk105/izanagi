# 段 4 裁定 — [T-139] land 2 session 1

段 2 (NO-GO / blocker 3)、段 3 lensA (NO-GO / blocker 5)、lensB (NO-GO / blocker 9) を裁定する。
親自身の実測で確定した新事実 (F-新) も含む。

## 0. 親が段 4 で確定した決定的事実 (レンズ所見ではない)

**F-新1. 承認 manifest は本 session では発行できない。**
承認済み `record-items-v2.md` §7 が「**conformance vectors** (正例 1 本と §6 の各制約に対する負例
1 本以上) を実装 wave が発行し、**その digest を approval manifest が pin する**」と定める。
vectors は §6 の cross-field 制約と §7.1 の 20 制約に対応する試験資材であり、固定 semantic
validator と同じ session に属する (本 session の scope 外)。
したがって本 session で manifest を発行すると、**承認済み要件が要求する key を欠くか、
存在しない vectors の digest を pin するか**のいずれかになる。どちらも承認契約違反である。

→ **manifest 実体の発行は、固定 semantic validator + conformance vectors を作る session へ移す。**
これは段 2・両レンズが指摘した「consumer 不在」とは独立の、承認文書由来の順序制約である。

## 1. 所見の real / refuted と採否

| # | 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| 1 | 段2/A1/B1 | resolver に consumer が無く §S7 #1〜#3 は 1 度も発火しない | **real** | scope 外 → 裁定パッケージ **RP-1** |
| 2 | A2 | resolver source 自身が descendant commit で自己承認できる | **real** | scope 外 → **RP-2** |
| 3 | A3/B7 | Git trust root が未完 (loader・repo-local config・commit-graph・alternates・common-dir) | **real** | policy 未裁定 → **RP-2** |
| 4 | A4 | 祖先条件は実行時刻を証明しない (post-hoc merge で pre-`F_r` 測定を laundering) | **real** | scope 外 (submit 層が要る) → **RP-1** |
| 5 | 段2/A5/B7 | §S7 #3 は consumer 不在で閉じられない | **real** | 後続 session → **RP-3** |
| 6 | A6 前半 | `compose_core` が `_validate_erratum_registry()` を呼ばず、承認分類が合成経路に無い | **real** | **本 session で採用 (lane A)** |
| 7 | A6 後半 | `BlobRef` が `str` subclass を許し、`actual != ref.sha256` を恒偽にできる | **real** | **本 session で採用 (lane B)** |
| 8 | A7 | D264 非 export 検査が旧名 `verify_receipt` しか禁じず、R5 の新名 `verify_prereg_receipt` を見ていない | **real** | **本 session で採用 (lane A)** |
| 9 | 段2/B3/A7 | 親 brief の「6 blob」は誤り。正は target core 1 + approved blobs 6 = **7 三つ組** | **real** | brief 訂正済み |
| 10 | A (再計算) | 親 brief の「承認 blob path を pin する 2 箇所」は誤り。当該 2 箇所は**草案** path の pin で、承認 v2 path の pin は **0 箇所** | **real** | brief 訂正済み |
| 11 | B5 | 承認済み S15 erratum は `new_sha256`・`expected_composed_sha256` を持たない。一律必須化すると承認済み文書が parse 不能、一律 optional 化すると exact-key 閉集合が壊れる | **real** | **本 session で採用 (lane A、erratum_id 別 exact grammar)** |
| 12 | B4 | 段 2 の `approval_manifest_ref` 追加は D234 署名の変更である | **real** | manifest 延期により本 session では発生しない → **RP-1** へ記録 |
| 13 | B6 | D282 payload の `alpha_reservation` 節が段 2 の manifest key 一覧に無い | **real** | manifest 延期により moot → **RP-1** へ記録 |
| 14 | A1 後半 | conformance vectors digest が段 2 の manifest key 一覧に無い | **real** | **F-新1 の根拠。manifest 延期の決定理由** |
| 15 | 段2/B8 | 親の (P1) A/B 2 分割は成立しない。実質 3 lane 並列 → 1 lane 直列 | **real** | **(P1) 撤回** |
| 16 | B9 | 多段 resolver の変異は前段に mask され単一理由帰属を証明できない | **real** | resolver 延期により対象縮小。残る変異は `first_rejecting_node` を記録する |
| 17 | B10 | spool fragment の `base` が stale で最終 land を止める | **real** | **最終 session へ送る** (今直しても後続 carry で再び stale になる、という B の理由を採る) |
| 18 | B (N1/N2 評価) | 親の外部依存判定は pilot・`b03` については正しいが、「基礎実装も全て blocked」と読むのは過大 | **real** | 採用。基礎実装は進める |
| 19 | A6 末尾 | 短い `_S7_OLD_TEXT="較正"` 自体は受理を広げない (固定 core で出現 exact 2、増えれば件数検査が fail-closed)。`DRAFT_ERRATA=∅` も恒真ではない | **refuted** (親 brief 側の懸念が否定された) | 段 3 lensA prompt の懸念 4 を取り下げ |
| 20 | 段2 blocker 2 | (P2) の「Git 実体 digest を受領証へ記録」は承認済み schema に field が無い | **real** | **(P2) 撤回**。記録は行わない |

## 2. provisional 裁定 (P1)〜(P5) の帰結

- **(P1) 撤回。** 2 分割は成立しない。本 session は下記 3 lane とする。
- **(P2) 撤回。** ambient PATH で解決してから digest を取るのは順序が逆で、かつ記録先 field が
  承認済み schema に無い。Git trust root の設計は **RP-2** としてユーザーへ返す。
- **(P3) 部分採用。** 単一 fd は必要条件だが不十分 (component walk・regular 検査・bounded read・
  read 前後 metadata が要る)。かつ consumer 不在で閉じられない。**RP-3** へ。
- **(P4) 条件付き成立。** 原理 (payload を先に読み manifest を後から照合すれば追加署名不要) は
  両レンズが認めた。ただし前提 (secure Git・trusted resolver・全 consumer の再導出) が未実装。
  本 session は**その原理の第 1 段だけ**を実装する (D282 payload の parse)。
- **(P5) 成立。** 複数 session と非 export は矛盾しない。ただし「非 export は security boundary
  ではない」という A の指摘を受け、`__all__` 検査を**保証**と呼ばず**衛生**と呼ぶ。

## 3. 本 session の実装 scope (plan v2)

**3 lane、編集ファイル所有は素集合。**

### lane A — erratum v2 + 合成経路の承認分類

所有: `orchestrator/preregistration/erratum.py`、`orchestrator/tests/test_t139_preregistration_binding.py`

1. `_validate_t139_core_s7_stresscheck_v1` を承認 v2 (2 operation) 用へ置換する。
   - operation 数 exact 2、index 集合 exact `{1,2}`。
   - locator 行 exact `{221, 333}`、old digest = `225268a9…8e89` / `a7852ad9…9952`。
   - new digest = `92fd7175…01a4` / `b8741cc9…b37fe`。
   - core 全体の `較正` 出現が exact 2 件で、その行集合が operation の対象行集合と一致。
   - 適用後の core に `較正` が 0 件。
2. **erratum_id 別 exact grammar** (所見 11)。S15 は旧 key 集合 (`new_sha256` なし・文書内合成値なし)、
   S7 v2 は `{operations, expected_composed_sha256}` + operation 6 key + `new_sha256` 必須。
   **承認済み S15 blob は再発行しない。**
3. `DRAFT_ERRATA` → 空、`APPROVED_ERRATA` は 2 ID。`_validate_erratum_registry` の分類検査を維持。
4. **`compose_core` / `compose_core_from_blobs` が `_validate_erratum_registry()` を必ず通る**
   (所見 6)。承認分類を合成経路の外に置かない。
5. test の `DRAFT_ERRATUM_*` を承認 v2 (path / commit `d0e76451…78d9` / sha256 `deedd71b…4df2`) へ差し替え、
   合成期待値を `dfb821a5…678c` (未承認草案) から `e0b0caea…8e0c` へ直す。
6. **D264 非 export 検査の禁止集合へ `verify_prereg_receipt` を足す** (所見 8)。
   R5 (a) が採る新名を現在の検査が見ていない。

*成果物影響:* 1〜5 が無いと承認済み core 合成を 1 度も再現できず、以後の全 manifest が
`composed_sha256` を持てない (certified 選択・材料レポート・試行台帳の preregistration 参照が全て不成立)。
6 が無いと半実装の verifier が export され、受領証が gate 未完のまま発効しうる。

### lane B — `BlobRef` の digest 比較迂回を塞ぐ

所有: `orchestrator/preregistration/blobref.py`、新規 `orchestrator/tests/test_t139_blobref_digest_binding.py`

- `_require_hex` / `_validate_repo_relative_path` が `str` subclass を素通しし、
  `actual != ref.sha256` が subclass の `__ne__` (反射側が優先される) で恒偽にできる (所見 7)。
- 検査済みの値を **exact `str`** へ正規化して保持し、digest 比較を subclass の `__eq__`/`__ne__` に
  依存しない形にする。`path` も同様に正規化する。

*成果物影響:* 塞がないと、64 桁 hex の `str` subclass 1 個で任意 blob が承認済み digest を
名乗れる。certified 選択・材料レポート・試行台帳の provenance が全て攻撃者の blob を指しうる。

### lane C — D282 承認 payload の parser (`F_r` 固定)

所有: 新規 `orchestrator/preregistration/approval_payload.py`、新規 `orchestrator/tests/test_t139_approval_payload.py`

- `F_r` = `39d760985a5e37d20464c394760bf65596156566` の `docs/decisions.md` を既存
  `read_pinned_blob` で読み、`decision_kind = t139-preregistration-approval-supersession/v1` の
  `text` fence を **exact 1 件**抽出して `ApprovalPayload` を構成する。
- 全 key を扱う: `forward_supersedes` / `preserved` / `target_core` / `approved_blobs` (6 role) /
  `erratum_application_order` / `composed_sha256` / `not_approved_as_record_items_root` /
  `operational_boundary` / `alpha_reservation`。**未知 key・欠落 key・重複 key・fence 複数・
  見出し複数はすべて fail-closed。**
- Unicode 正規化を行わない。fence delimiter 長を追跡する。
- **manifest は扱わない** (F-新1 により本 session では発行しない)。
- **`__init__.py` へ export しない** (D264)。

*成果物影響:* 現在 D282 payload を読む test は **0 件**。parser が無ければ resolver は
「台帳 → manifest の第 1 矢印」の起点を持てず、§S7 #1 は着手できない。

### 本 session で実装しないもの (明示)

approval manifest 実体、`resolve_effective_preregistration`、`PreregBinding`、Git trust root の
強化、raw snapshot API、受領証 writer / semantic validator / conformance vectors、`a13` consumer、
submit / PBS / driver / collector、correctness 還流、certified 側 consumer、pilot 投入。

**記録上の状態は `foundation-only` とし、§S7 #1〜#3 を「満たした」と書かない。**

## 4. 変異事前登録 (`DW-M01`)

各変異は実効 gate へ照準し、前後層に先取りされないことをコードで確認したうえで登録する。
resolver を延期したため、B9 が警告した多段 mask は lane C の parser 内に限定される。
lane C の変異は `first_rejecting_node` を matrix へ記録する。

| ID | lane | 変異位置 | 期待 |
|---|---|---|---|
| M1 | A | operation 数検査を `== 2` → 無効化 | KILLED |
| M2 | A | `較正` 出現件数検査 (exact 2) を無効化 | KILLED |
| M3 | A | 適用後 `較正` 0 件検査を無効化 | KILLED |
| M4 | A | index 2 の new digest 照合を無効化 | KILLED |
| M5 | A | `compose_core` の `_validate_erratum_registry()` 呼び出しを削除 | KILLED |
| M6 | A | D264 禁止集合から `verify_prereg_receipt` を削除 | KILLED |
| M7 | B | `_require_hex` の exact `str` 正規化を削除 (**wave 前の実コードの形**) | KILLED |
| M8 | C | fence exact 1 件検査を「1 件以上」へ緩める | KILLED |
| M9 | C | 未知 key 拒否を無効化 | KILLED |
| M10 | C | `approved_blobs` の role 数 exact 6 検査を無効化 | KILLED |

M7 は wave 前の実コードそのものの形 (`isinstance(value, str)` のみ) を変異として登録する。

## 5. ユーザーへ返す裁定パッケージ (段 7 で `package.md` として起票)

- **RP-1 — E2E gate の支配点。** resolver を書いても呼ぶ側が無い限り §S7 #1・#2 は発火しない。
  land 2 を「resolver + 最初の consumer を同一 session で land する」形へ組み替えるか、
  現状の分割を維持して発火を最終 session まで待つか。D234 署名変更 (所見 12)、
  `alpha_reservation` の manifest 上の扱い (所見 13) を同束で問う。
- **RP-2 — Git / resolver の trust root policy。** 本環境の `/usr/bin/git` は
  owner `uid/gid = 65534/65534` で、「root 所有必須」を採ると本環境を拒否する。
  どこまでを OS の信頼に委ね、どこから digest closure を持つか。resolver source 自身の
  identity 束縛 (所見 2) を含む。
- **RP-3 — raw snapshot consumer の閉包。** snapshot API 単体でなく全 `fileRecord` consumer への
  結線をいつ・どの session で行うか。
- **RP-4 — 公表 core `b03` と pilot の解除条件。** 段階 2 の凍結承認 + fold の後で何を確認すれば
  pilot 投入可とするか。

## 6. 停止しなかった理由

`DW-S04` は「承認済み裁定を止めてよいのは裁定時点で未見の新事実がある場合だけ」と定める。
F-新1 (manifest は conformance vectors digest を pin する義務がある) は S7 裁定時点で未見であり、
manifest 発行の順序を変える。ただしこれは**承認済み裁定の否定ではなく順序の確定**であり、
S6 (a) が認めた複数 session 分割の内側に収まる。よって親は不採用にせず、
RP-1〜RP-4 をユーザー再裁定へ返しつつ、確定済みの 3 lane を進める。
