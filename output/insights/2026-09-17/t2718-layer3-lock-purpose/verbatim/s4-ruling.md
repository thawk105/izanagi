# 段 4 裁定 — [T-2718] (2026-09-17、親)

裁定 inbox 再走査: local main 1042a1bc9 から前進なし、main の worklog / decisions に T-2718 の新裁定なし。

## 所見の裁定

| 所見 | 判定 | 採否 | scope | 対応 |
|---|---|---|---|---|
| A-1 decode bytes と admission digest が束縛されず、755→795 の読取り窓で差し替えられる | **本変更に帰属する回帰としては refuted、既存の弱点としては real** | 不採用 (実装しない) | scope 外 | 現行 code でも同じ窓で任意の現行 63 lock B' を差し込める (identity 置換は既に可能)。旧 grammar を B に加えても能力は増えない。並行書き手を仮定する仮想リスク向けの検査新設はユーザー引数 (「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」) と DW-G05 で禁じられている。**裁定パッケージ候補**として worklog 次の一手へ新規項目で送る (同一 bytes の decode + digest 束縛)。変異にも載せない |
| A-2 P2 の等価性が射影範囲では未証明 | real (検証要求) | 採用 | scope 内 | 親が wal.py 840/894/946 (receipt helper は lock を取らない)、1000-1200 (lock を消費するのは `_knowledge_lock_binding` の呼び出しだけ) を読み確認。B-4 が独立に同結論。加えて test に「binding 不一致 (level 片方だけ / 桁不正) で object 渡しと identity 渡しが同じ `AttemptTopologyError` を出す」拒否 parity を 1 本足す |
| A-3 必須 enum dispatch は D1653 の boolean 緩和でない | refuted | — | — | 採用可。D1653/D422 適合を確認 |
| A-4 固定入力で certified 昇格の迂回なし | refuted | — | — | 不変条件 I1 の裏取り |
| A-5 P4 は 63 対照 1 本からの外挿 | real | 採用 | brief 文言 | P4 を「予測」に改め、修正後に exact-62 3 本それぞれで例外全文・cause・lock/WAL bytes 不変を記録する (probe は 3 本 + 63 対照 + exact-24 1 本) |
| A-6 / B-1 「中央 admission の受理集合と一致」は過大 | real | 採用 | brief 文言 | 「歴史 grammar を理由とする 755 行の再拒否を解消する。材料レポート固有の入力条件 (ancestry・records/threads・WAL・calibration・schema) は不変」へ限定 |
| B-2 実在 3 本の完全生成は scope 内で不可能 | real | 採用 (縮小を確定) | 裁定パッケージ候補 | 依頼文「実在 3 本で材料レポートが生成できる」は、paper-story 認証 campaign の search_config (records/threads 不在) が材料レポートの形に合わないため、本 wave の scope (読取り経路のみ) では到達できない。本 wave の正例は「合成 exact-62/24 で完全生成」+「実在 3 本が 755 行を通過し 63 対照と同じ到達点 (838 行) で止まる」。paper-story 形の材料レポート対応は別項目として worklog 次の一手へ送る。ブロックしない |
| B-3 consumer 取り残しなし | refuted | — | — | plan の一覧を確定 (T:2258、T:2279 の 2 件だけ追随) |
| B-4 identity 渡しは WAL 経路全体で等価 | refuted (懸念) | 採用 | — | P2 確定 |
| B-5 completeness 比較は generator hash を除外しない | real | 採用 (記録のみ) | nit | 既存 persisted report との fresh 比較は本 file を編集した過去の全 wave と同じく generator hash で差が出る (規律 7、記録は無効化されない)。insight に 1 行 |
| B-6 enum 境界ケース | real | 採用 | test | `CampaignReadPurpose("HISTORICAL_RAW")` は正例、`class S(str)` の値と同名・同値 member を持つ別 Enum は負例 |
| B-7 committed repo は rewrite helper の依存でない | real | 採用 | test | 正例は `support._committed_closure_repo` + `_REPO_ROOT` monkeypatch + 実 admission (先例 T:1891) で通す。admission の monkeypatch は使わない |
| M6 の説明訂正 | real | 採用 | 変異 | 「型検査を消すと不正 purpose が通常 decoder へ落ち、正常 63 lock で TypeError が出なくなる」 |

## plan v2 (段 2 plan + 上記)

- 変更 hunk: plan の #1〜#10 のまま。hunk #1 の exact 型検査は read_text より前 (M9 の根拠)。
- テスト: plan の 7 関数 + A-2 の拒否 parity 1 本 (parametrize で object / identity)。B-6 の境界ケースを `test_read_campaign_lock_rejects_non_exact_purpose` に含め、`CampaignReadPurpose("HISTORICAL_RAW")` の正例を `..._current_and_v1_by_purpose` に含める。
- fixture: `from orchestrator.tests import test_artifact_admission as support`、`support._committed_closure_repo(tmp_path)` + `monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)` + `support._new_schema_campaign(...)` (T:1891 と同じ issuing context) + `support._rewrite_as_t733_exact62_lock` / `support._rewrite_as_pre_t733_lock`。`build_report(campaign, generated_from_head="fixed", output_root=tmp_path)` を実 admission で呼ぶ。
- 固定期待値: exact-62 epoch = `E1:78920efc47f4eb280b956a8fb92abed16b888495db544b62b1a15bf1f61004e9` (support 591 行の既存 literal と同値を test 内に固定文字列で置く)。exact-24 epoch は実装子が実 admission を 1 回走らせて得た値を固定文字列として置く (実装から再計算しない。値の出所を完了報告に書く)。
- 規模上限: 実装 file 1 (layer3_report.py)、test file 1。他 file の編集は差し戻し。

## 変異事前登録 (B-057、位置と意味を確定。exact な old/new は実装後に同じ意味で埋める)

| id | category | 位置 | 変異 | 殺すはずの test |
|---|---|---|---|---|
| M01 | negative | `_read_campaign_lock` の分岐 | purpose 分岐を除去し常に `decode_campaign_lock` | historical exact grammar build_report 正例 (62/24) |
| M02 | negative | 同 | 分岐を反転 (HISTORICAL_RAW → 通常、それ以外 → 歴史) | 同上 + current/v1 の exact 返却型 test |
| M03 | negative | 同 | 常に `decode_historical_campaign_lock` | accepted 負例 (例外全文 + cause)、current/v1 の exact 返却型 test |
| M04 | negative | build_accepted_report の呼び出し | purpose を HISTORICAL_RAW へ | accepted 負例 (例外全文 `^campaign\.lock schema が不正$` + cause CampaignLockCodecError) |
| M05 | negative | build_report の呼び出し | purpose を CERTIFIED_ACCEPTANCE へ | historical 正例 |
| M06 | negative | exact 型検査 | `type(purpose) is not CampaignReadPurpose` の raise を除去 | non-exact purpose 負例 (正常 63 lock で TypeError) |
| M07 | negative | wal への受け渡し | `decoded_lock.identity` → `decoded_lock` | historical 正例 (knowledge provenance 検証に失敗) |
| M08 | negative | signature | `purpose` に既定値 `CampaignReadPurpose.HISTORICAL_RAW` を付ける | requires_purpose 負例 |
| M09 | negative | 型検査の位置 | 型検査を `path.read_text` の後へ移動 | non-exact purpose 負例の存在しない path ケース |
| M10 | positive (等価、SURVIVED 期待、expected_nodes 空) | `_read_campaign_lock` 内 | 意味を変えない書き換え (例: `if purpose is CampaignReadPurpose.HISTORICAL_RAW:` の分岐本体を局所変数経由にする) | 生存が期待。harness の SURVIVED 検出の正例 |

除外: 966 行の certified admission 削除、980 行の E1 gate 削除 (旧 grammar 入力は 937 で止まり到達不能)。A-1 の bytes 束縛変異 (scope 外)。
runner: `python3 tools/run_tests.py --force-dispatch -rf orchestrator/tests/test_layer3_report.py` (期待 node は login probe で採取)。

## 実 corpus の完了線 (A-5 / B-2)
修正後、exact-62 3 本 (t2364-20260907b rr5 / rr50、a6-20260908b rr95) + exact-24 1 本 (t2022-20260827 rr5) + 63 対照 1 本で `build_report` を呼び、(a) `_read_campaign_lock(purpose=HISTORICAL_RAW)` の成功と返却型、(b) `build_report` の例外全文と cause、(c) lock/WAL bytes 不変、(d) `_read_campaign_lock(purpose=CERTIFIED_ACCEPTANCE)` の拒否 (62/24) を 5 本それぞれ記録する。到達点は予測せず観測値を書く。
