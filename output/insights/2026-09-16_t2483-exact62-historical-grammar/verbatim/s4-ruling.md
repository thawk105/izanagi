# 段 4 裁定 — [T-2483] exact-62 の campaign lock を読む経路

裁定日: 2026-09-16。main は wave 開始時から不変 (`d97c423bd`)。裁定 inbox の再走査でも
本件に関わる新しい裁定は無かった。

## 1. 所見の裁定

| 所見 | 判定 | 対応 |
|---|---|---|
| A-1 certified への迂回受理経路は確認できない | refuted (疑いが成立しない) | 採用。不変条件 1・2 の裏取りとして記録する |
| A-2 encode / resume も通常 decoder の拒否を回避できない | refuted | 採用 |
| A-3 既存否定テストの恒真化は起きない。ただし現行 63 から worker を落とす parameter は exact-62 と同形 | real | 採用。当該 parameter は**通常 decoder の拒否**を守るので残す。新しい歴史 superset には worker ではなく未知 path を使う |
| A-4 二重検査は成立するが、authority は元 wire 順序の独立再検査ではない | real (説明の訂正) | 採用。記録にそう書く。追加 gate は作らない |
| A-5 epoch の通常型への誤分類が最大 risk | real | 採用。変異事前登録の中心に据える |
| A-6 親の実測は射程を超えて一般化していた | real (親の訂正) | 採用。§4 で射程を限定し直す |
| A-7 受理は grammar 単位であり「3 本だけ」ではない | real (説明) | 採用。D1653 は個体 hash allowlist を却下済み。ユーザー引数の「3 本に限定」は**調査と収載 grammar の限定**と読む (他 grammar を一緒に収載しない)。個体 gate は作らない |
| B-1 固定 known-answer が無いと宣言順の同時変更で緑になる | real | **採用・must-fix**。D1652 に従い固定 E1 文字列と宣言順 path hash を literal で置く |
| B-2 間接 consumer が未棚卸し。`layer3_report` は歴史 admission 後に通常 decoder で再拒否する | real | 採用。成果物の主張を中央歴史 API に限定する。`layer3_report` の修正は **scope 外**とし新規台帳項目にする |
| B-3 実 3 本の確認到達点が未定義 | real | 採用。§3 で到達点を確定する |
| B-4 変更面は production 2 + test 2 で「2 file」は過少 | real (nit) | 採用。brief の数字を訂正。実装子は 1 本のまま |
| B-5 (P1)・scope 文言・既存否定テストの疑いは反証 | refuted | 採用。(P1) を確定へ昇格する |

親が独立に確認した根拠: `layer3_report.py:112-120` の `_read_campaign_lock` は
`campaign_lock.decode_campaign_lock` を無条件に呼んでおり、purpose を見ない。B-2 は real。

## 2. プラン v2 (確定)

段 2 プランを次の補正つきで採用する。

1. `orchestrator/campaign/campaign_lock.py`
   - `T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS` を**独立した ordered literal** として新設する。
     現行 tuple の slice にしない。値は `2a9ba783f^` の `CONTRACT_LOADER_RELATIVE_PATHS` と一致させる。
   - `_validate_pre_t733_historical_authority` は**一般化せず兄弟関数を足す**。
     既存 exact-24 の検証順・例外文面・返却値を 1 文字も変えない
     (既存 2 テストが `match="歴史 grammar"` で文面に依存しているため)。
   - `HistoricalCampaignLockAuthority.__post_init__` の grammar 白名単に新 tuple を足す。
   - `decode_historical_campaign_lock` を 現行 / exact-62 / exact-24 の 3 分岐にする。
     未知入力を exact-24 として受ける fallback を作らない。
2. `orchestrator/campaign/artifact_admission.py`
   - exact-62 固有の scope 定数 2 本を独立文字列として新設する。現行定数への alias にしない。
     現行定数 (`CAMPAIGN_VERIFIER_EPOCH_SCOPE` 等) は**触らない** ([T-2482] の持ち分)。
   - `HistoricalCampaignVerifierEpoch` が許す `(identity_scope, excluded_scope)` の組に
     exact-62 の組を足す。field を独立に許して混成を通さない。
   - `_RecordedCampaignVerifierEpoch.__post_init__` の「歴史型なら exact-24」という無条件の固定を、
     scope の組と記録 tuple・blob map 順序の対応検査に変える。通常型は現行 tuple のまま。
   - `_verify_committed_loader_binding` の明示 path 版分岐に exact-62 を足す。
     exact-62 を `binding_from_authority` へ流さない。
   - `_recorded_campaign_verifier_epoch` に exact-62 の分岐を足す。
   - **epoch hash 式は変えない。** scope 文字列を preimage へ足さない (exact-24 の既存 epoch が動く)。
3. テスト
   - 段 2 プラン §6 の codec 4 node・admission 5 node を採る。
   - **must-fix (B-1):** 正例の期待 epoch と期待 path hash は、production の新定数からも
     期待列からも再計算しない**固定文字列**として置く。D1652 の要求どおり、
     production と期待 literal を同時に並べ替えても落ちる形にする。
   - 新しい歴史 superset の負例に `verify_fanout_worker.py` を使わない (既知の現行 63 になる)。
   - 既存テストの期待値を変更しない。
4. `orchestrator/campaign/layer3_report.py` は**触らない**。
5. 通常 decoder / encode / resume / certified admission は不変。

### 新 validator の禁止 (署名で書く)

`_validate_t733_exact62_historical_authority(value) -> HistoricalCampaignLockAuthority` は、
`value` が次のいずれかなら `CampaignLockCodecError` を送出しなければならない。

- `authority` の key 集合が `AUTHORITY_KEYS` と厳密一致しない
- `contract_loader_blob_sha256s` の key 列が
  `tuple(sorted(T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS))` と厳密一致しない
  (subset 61 / superset 63 / 同数別集合 62 / 順序違い 62 をすべて含む)
- 62 path のいずれかの digest が 64 桁 hex でない
- `activation_serial` が正の exact int でない

**通る正例:** 実在する
`/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907b/jobs/rr5/campaigns/paper-story-a2-rr5-paper-story-a2-certification-rr5-1af9fc2b/campaign.lock`
の `authority` object。これは受理され、宣言順で再構成された blob map を持つ
`HistoricalCampaignLockAuthority` を返す。

## 3. 受入到達点 (B-3 の補正)

親が repo 外で実行し、逐語を insight へ残す。

- **必達 A:** 実 3 本それぞれで `decode_historical_campaign_lock_bytes` が成功し、
  `recorded_contract_loader_relative_paths` が exact-62 tuple である。
- **必達 B:** 実 3 本それぞれで
  `require_campaign_verifier_epoch(<campaign dir>, purpose=CampaignReadPurpose.HISTORICAL_RAW)` が
  `HistoricalCampaignVerifierEpoch` (`state == "E1"`) を返す。
- **測定 C:** 実 3 本それぞれで
  `require_admitted_campaign(<campaign dir>, purpose=CampaignReadPurpose.HISTORICAL_RAW)` を実行する。
  成功すれば記録する。**後段の gate (activation / WAL topology / receipt など) が拒否したら、
  その拒否理由をそのまま記録し、gate を 1 つも緩めない。** 拒否が出た場合は新規台帳項目にする。
  測定 C の結果は必達条件ではない — 本 wave が直すのは decode 層だからである。
- **bytes 不変:** 実行の前後で 3 本の `campaign.lock` と `runs/wal.jsonl` の sha256 が変わらない。
- **到達しないと明記すること:** `layer3_report` 経由の材料レポートは、本 wave 後も
  exact-62 を読めない (通常 decoder で再拒否される)。

## 4. 親の実測の射程訂正 (A-6)

`measured-facts.md` の 3 主張を次の射程に限定して記録する。

- 「3 本とも同一 grammar」= 3 本の `contract_loader_blob_sha256s` の **key 列**が一致する、
  という意味に限る。digest 値・記録 commit・activation・WAL の一致は測っていない。
  sorted な wire から宣言順は復元できないので、宣言順の権威は記録 commit の実コードである
  (段 2 子と段 3 レンズ B が独立に AST 比較して親の写しと一致を確認した)。
- 「並行編集なし」= 2026-09-16 の測定時点で、114 branch の `main...<branch>` 差分と
  116 worktree の作業ツリーにおける**指定 2 file** に限る。テスト file・他 file・
  列挙外 checkout・測定後の編集には及ばない。
- 「T-2125 は発火しない」= 3 本の `search_config.build_admission` が測定時の
  `_current_policy().as_preimage()` と一致する、という意味に限る。
  admission 全経路の成功を測ったものではない。

## 5. 変異事前登録 (DW-M01)

段 2 プラン §8 の対を採る。単一理由性は実装後に確認する。次の 1 件は**登録しない**。

- 「wire 順序一致を集合比較へ緩める単独変異」— canonical JSON 検査に mask されて生存しうる
  (プラン自身が指摘)。実効 gate である `HistoricalCampaignLockAuthority.__post_init__` の
  宣言順検査へ再照準し、authority 直接構築の負例で殺す。

登録する変異と落ちるべき node (実装後に anchor と node 集合を spec へ確定する):

| 変異 | 落ちるべき node |
|---|---|
| exact-62 decoder 分岐を削除 | codec 正例 |
| authority 白名単から exact-62 tuple を削除 | codec 正例 + authority 直接構築の正例 |
| 62 literal の 1 path を置換 | codec 正例の固定期待 tuple + admission 正例の固定期待 epoch |
| 62 literal の宣言順を 2 要素入れ替え | admission 正例の**固定** E1 文字列 (B-1 の must-fix がここで効く) |
| authority の宣言順検査を集合比較へ | authority 直接構築の負例 |
| exact-62 の committed blob 検証を省略 | 62 path 全件 parameter の committed mismatch 負例 |
| exact-62 epoch を通常 `CampaignVerifierEpoch` で返す | admission の歴史型正例 (A-5 の中心) |
| epoch の入力順を sorted wire 順へ | admission 正例の固定 E1 文字列 |
| scope と map の対応検査を緩める | scope 混成の負例 |
| 通常 decoder を exact-62 受理へ緩める | 通常 decoder 拒否の負例 + 既存 `test_v2_rejects_each_missing_enforcement_source_blob_key[verify_fanout_worker.py]` |

## 6. scope 外として台帳へ送るもの

- `layer3_report._read_campaign_lock` が purpose を見ず通常 decoder を呼ぶため、
  中央の歴史 admission を通った lock でも材料レポート生成段で再拒否される (B-2)。
  **新規台帳項目**にする。本 wave では直さない。
- `CAMPAIGN_VERIFIER_EPOCH_SCOPE` / `..._EXCLUDED_SCOPE` の文面が現行 63 と食い違う ([T-2482])。
- 旧 grammar 8 / 12 / 14 / 25 / 27 の収載 ([T-2345]。実在 corpus 未観測で条件不成立)。
- [T-2125] の policy 版上げ問題。
