結論は **NO-GO** です。実装 commit 単体よりも、versioned artifact 発行後に既存の直接 pilot CLI／resume 経路が後段で壊れる点が major です。静的検査のみで、書き込み・pytest 実行はしていません。

## 所見 D-1 — 発行後、既存の直接 pilot CLI と legacy resume が後段で破断する

- 深刻度: **major**
- 根拠:
  - `orchestrator/campaign/s8b_floor_campaign.py:6842-6863`
  - `orchestrator/campaign/s8b_floor_campaign.py:931-963`
  - `orchestrator/campaign/s8b_floor_campaign.py:5825-5930`
  - `orchestrator/campaign/s8b_floor_campaign.py:6111-6142`
  - `orchestrator/campaign/s8b_holdout_admission.py:462-496`
- 再現の筋道:
  1. artifact commit 後、従来どおり直接 CLI に `--mode pilot --protocol output/s8b-freeze/floor_protocol.json` を渡す。
  2. CLI は legacy protocol をそのまま検証し、run directory 作成、binary build/store、manifest 発行まで進む。
  3. 最後の holdout reservation で `_authority()` が resolver を再実行する。
  4. index は 2 件なので resolver は HEAD gitlink に一致する versioned record を返す。
  5. `_authority()` は resolver の versioned document と caller の legacy document の不一致を `fixed protocol bytes do not match the supplied protocol` で拒否する。
  6. 発行前は候補 1 件なので同じ入力が legacy で通る。発行後だけ受理集合が反転する。
- 放置時の成果物影響: legacy SHA を持つ run directory、binary store、manifest が残る一方、pilot result・材料レポート・完了試行台帳は生成されず、既存 legacy resume も完走不能になる。
- 必要な処置: 発行前に直接 CLI の authority を解決するか、少なくとも resolver との一致を run directory 作成より前に拒否する。公開 CLI 裁定が必要なら、artifact 発行をその裁定まで止める。

## 所見 D-2 — W5 の「同じ HEAD から gitlink も読む」が単独候補で実装されていない

- 深刻度: **minor（nit、今回の NO-GO 根拠にはしない）**
- 根拠:
  - `orchestrator/campaign/s8b_floor_campaign.py:931-958`
  - `orchestrator/tests/test_s8b_protocol_builder.py:1093-1102`
  - 親裁定 `s4-adjudication.md` の W5
- 再現の筋道:
  1. committed legacy protocol だけを持ち、`external/ccbench` gitlink を持たない tmp repository を作る。
  2. `resolve_current_floor_protocol(root=repo)` を呼ぶ。
  3. `len(candidates) == 1` の早期 return により `_ccbench_gitlink()` は呼ばれず、legacy が受理される。
  4. 新設テスト自身が `gitlink_mock.assert_not_called()` でこの挙動を固定している。
- 放置時の成果物影響: 現実の発行後 repository は候補 2 件で gitlink を読むため、今回予定する certified 値への直接影響はない。ただし gitlink 欠落 repository を protocol authority 段で受理する契約差が残るため nit とする。

## 所見 D-3 — v2 candidate producer は official CLI の背後ではない

- 深刻度: **minor（条件付き consumer、今 wave の must-fix にはしない）**
- 根拠:
  - `orchestrator/campaign/s8b_holdout_freeze.py:1280-1341`
  - `orchestrator/campaign/s8b_holdout_freeze.py:1580-1617`
  - `orchestrator/campaign/s8b_holdout_freeze.py:1748-1760`
  - `orchestrator/campaign/s8b_holdout_freeze.py:1773-1814`
- 再現の筋道:
  - `s8b_holdout_freeze.py generate-v2-candidate --floor-result <official-v2-result> --budget <approved-budget>` は floor campaign の official CLI を経由せず、独立した公開 CLI から producer に入る。
  - budget approval が有効になった状態で、versioned protocol SHA を記録した official result を渡す。
  - producer は固定 `output/s8b-freeze/floor_protocol.json` を読み、legacy SHA と result の versioned SHA の不一致を `:1335-1336` で拒否する。
  - 現在は `BUDGET_APPROVAL_SHA256=None` かつ official result 0 件なので、この入力はまだ実在しない。親の「今日は休眠」という結論は維持できるが、「official CLI 拒否の背後」という理由は誤り。
- 放置時の成果物影響: budget ratification 後も v2 g1 candidate が生成されず、candidate の `floor_protocol`、後続 report、verdict の参照集合が空のままになる。

なお、versioned artifact は `EXCLUDED_PATHS = ("output/s8b-freeze/",)` により unknownness scan 全体から除外されるため、段 3 レンズ B が懸念した「versioned artifact が measurement closure に混入」は成立しません。根拠は `s8b_holdout_freeze.py:43,402-403,1532-1553` です。

## 所見 D-4 — official preflight は直接呼べるが、production input ではまだ到達不能

- 深刻度: **minor（条件付き consumer）**
- 根拠:
  - `orchestrator/campaign/s8b_floor_campaign.py:3663-3710`
  - `orchestrator/campaign/s8b_floor_campaign.py:3775-3778`
  - `orchestrator/campaign/s8b_floor_campaign.py:3877-3944`
  - `orchestrator/campaign/s8b_floor_campaign.py:5604-5608`
- 再現の筋道:
  - Python caller は `_floor_preflight_freeze_allowlist(ROOT, ..., protocol_sha256=<versioned SHA>)` を official CLI なしで直接呼べる。
  - helper は legacy path の bytes を読む。現在は freeze verification hold により `:3707` の比較は保留されるが、返した allowlist は legacy path に versioned SHA を結び付ける。
  - 続く `clean_scan_digest()` は `:3939-3944` でその hash 不一致を拒否する。
  - 一方、production core は `:5608` で official を無条件拒否してから preflight へ進むため、monkeypatch なしの入力だけで現在ここへ到達する方法はない。
- 放置時の成果物影響: official 解禁時、versioned protocol の launch certificate、official result、report、試行台帳の受理集合は空になる。

## 発行後に赤くなる既存 pytest node の完全集合

**空集合、0 件です。**

実 repository の index を読む node は次の 3 node ですが、いずれも 2 件 index を許容する形へ変更済みです。

- `orchestrator/tests/test_s8b_protocol_builder.py::test_build_and_write_leave_repo_tree_unchanged[top-level]`
- `orchestrator/tests/test_s8b_protocol_builder.py::test_build_and_write_leave_repo_tree_unchanged[nested]`
- `orchestrator/tests/test_real_repo_serialization.py::test_protocol_builder_repo_tree_guard_is_wired_to_real_root`

根拠は `test_s8b_protocol_builder.py:1733-1760` です。legacy の存在だけを要求し、追加 record は sanctioned namespace 配下なら許容します。meta node は `test_real_repo_serialization.py:1045-1098` で同じ action を呼ぶだけです。

併せて確認した誤検出候補:

- `test_frozen_artifacts.py::test_manifest_shape_is_exact` の `len(FROZEN_MANIFEST) == 23` は実 directory を列挙せず、辞書自身だけを数えるため赤くならない。`test_frozen_artifacts.py:234-248`
- `test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control` は `output/s8b-freeze/` 全体が scan 除外なので赤くならない。
- `test_codex_worker_launch.py:1831` の `len(index)` は failure archive の JSONL index であり無関係。
- 指定された `conftest.py`、`growth_test_holds.py`、`test_hold_inventory.py`、`test_real_repo_serialization.py`、`test_growth_test_holds_contract.py` に、削除・改名された protocol test node の残存参照はない。

## 発行直後、未 commit の窓

この窓では committed-only が意図どおり fail-closed します。

赤または非 0 になるもの:

- `check-protocol-index`
- `resolve-current-protocol`
- certified writer の floor admission
- holdout admission の `_authority()`
- `tools/pegasus/floor_campaign.sh`
- 上記 real-repo test 3 node

artifact 単体の read-back、strict parse、導出 path、inheritance、canonical bytes、SHA 検査は resolver を使わないため実行可能です。repository に custom Git commit hook は構成されていないため、`git add` と commit 自体を阻む hook もありません。

したがって親の順序、

`発行 → artifact 単体検証 → commit → index/resolver 検証`

は成立します。ただし commit 前に通常の焦点テスト、`check-protocol-index`、resolver、floor shell を挟んではいけません。

## shell 変更の判定

shell ハンク自体に blocker は見つかりませんでした。

- resolver 呼出しは `tools/pegasus/floor_campaign.sh:954-961` の 1 回だけ。
- 値は driver `:992-996`、metrics 再読 `:1009-1010`、job-result `:1129-1132` で共有。
- resolver 失敗記録は driver fd 作成 `:981` と launch marker `:991` より前。
- 非 0、空、複数行、絶対 path は `floor_protocol_resolution` で終了する。
- resolver と本 driver は、計算ノードで選択済みの同じ `$PY` を使用する。`$PY` は `:224-244` で Python 3.10 以上へ解決されるため、PATH 差による新しい interpreter 分裂はない。
- resolver は gflags/glog build 後に置かれているので失敗時にも前処理コストは発生するが、certified 選択・レポート・試行台帳の値は変えないため nit に留める。

## 単位 B の申告の裏取り

`_test_holdout_authority()` は legacy-only repository を作り、gitlinkも作りません。根拠は `test_s8b_floor_campaign.py:431-469` です。

しかし実装 resolver は候補 1 件なら `s8b_floor_campaign.py:953-955` で gitlink を読まず fallback return します。したがって、単位 B が申告した「衝突する可能性」は**現実には衝突しません**。

一方、この fallback により大半の floor campaign tests は発行後の「候補 2 件＋HEAD gitlink exact」状態を踏みません。これは D-2 の coverage nit であり、既存テストが別理由で緑になる実例です。

**最終判定: NO-GO。**
コード commit 後ただちに artifact を発行するのではなく、D-1 の直接 CLI／resume authority を先に閉じるか、公開 CLI 裁定まで artifact 発行を延期すべきです。

## 総括

発行後に赤くなる既存 pytest node は 0 件で、指定台帳にも stale node はありません。
ただしテストが緑でも、従来の直接 legacy pilot CLI と legacy resume は発行後だけ後段拒否へ変わります。
その拒否は build、binary store、manifest 発行後なので、部分成果物を残して result と試行台帳を失います。
未 commit 発行窓では resolver 系検査が赤になるものの、親の artifact 単体検証から commit する順序自体は成立します。
shell は resolver を 1 回だけ呼び、失敗記録、fd、marker、3 consumer の順序も維持しています。
official preflight と v2 producer は現在休眠ですが、official CLI 拒否だけが到達防壁という説明は正確ではありません。
単位 B の legacy-only fixture は現実には衝突せず、単独候補 fallback により緑になります。
以上から、artifact 発行を含む現在の着地は NO-GO です。