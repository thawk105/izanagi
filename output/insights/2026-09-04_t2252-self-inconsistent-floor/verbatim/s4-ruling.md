# 段 4 裁定 — [T-2252] 自己整合しない較正を層 3 の within-run 床値に使わない

基準 commit 764fdf202 (local main は wave 開始後に動いていない)。段 2 plan と段 3 の 2 レンズ
(sol = 正しさ境界、luna = 既裁定整合・scope) を読み、親が所見ごとに裁定した。

## 所見の裁定

| # | 出所 | 所見 | 性質 | 採否 | 裁定 |
|---|---|---|---|---|---|
| B1 | luna | `calibration_verify.py` の共有 frozenset は新しい production 例外台帳で、材料レポートの generator hash にも束縛されない | real | 採用 | 宣言は **`layer3_report.py` 自身**の module 定数に置く (consumer-local)。`test_env_contract.py` の test-local 集合は独立 oracle として**変更しない** |
| A6 | sol | `calibration_verify.py` は silo ladder runtime binding と T126 code identity に入り、bytes 変更は無関係な identity を前進させる | real | 採用 | 同上。B1 と同じ結論に独立に到達 |
| A2 | sol | pin の path だけ除外すると、g1 と同 bytes の直下 copy / hardlink が別名で置かれた場合に一致が戻る。D1537 の「環境系列を一致なしに保つ」は現在の配置 (pegasus 直下 within-run 0 件) に依存する | real | 採用 | 除外を **系列単位**にする: 有効契約の `calibration_ref` (path, sha256) が宣言集合に入るなら、その campaign の within_run 候補を **空**にする (直下 record も候補にしない)。between_run は従来どおり |
| A4 | sol | path 単位除外では「一致候補 2 件で重複エラー」だった campaign が「直下 1 件の新規一致」へ転じる受理拡大が起きる | real | 採用 | A2 の系列単位除外で同時に閉じる。新規一致は 0 件になる |
| A3 | sol | brief (P2) の「`_validated_pin_path` を呼ばずに除外」は SHA 不一致・directory 外・非 file の fail-closed を隠す | real (brief の欠陥、plan は是正済み) | 採用 | **検証を先に完遂**する。`Layer3ReportError` と `pin-file-missing` は従来どおり確定し、その後に within_run の候補形成だけを止める |
| B2 | luna | 新 status `self-inconsistent-awaiting-healthy-generation` は裁定が要求せず、g2 発効後の歴史的 g1 lock に対して語義が古くなる | real | 一部採用 | 新しい **status 値は足さない** (`validated` / `pin-file-missing` は従来の意味のまま)。ただし within_run の search 詳細に理由 key を **1 つ**だけ足す (下記)。理由: 成果物に理由が無いと「pin は validated、候補 0 件、値 None」という説明不能な null が残り、D1374 の趣旨 (一致の根拠を成果物へ明記) に反する。値は世代の状態を言わない固定文字列にする |
| B3 | luna | 成果物影響の記述が不完全 (g1-pinned v2 report は None へ、全新規 report の `meta.generator.sha256` が変わる) | real | 採用 (記述) | 本裁定の「成果物影響」に書く。実装追加なし |
| B4 | luna | brief の「schema はキー集合を凍結」は広すぎる | real | 採用 (記述) | 段 7 の記録で狭める |
| A5 | sol | 既存 7 report の主張根拠は隣接 lock の v1 確認まで要る。dossier と T2136 の変異台帳に g1 値の写しがある | real (過大一般化、結論は不変) | 採用 (記述) | 親が実測: 7 件の隣接 `campaign.lock` はすべて authority なし (v1)。既存 report・dossier・変異台帳は**再発行しない** |
| B5 | luna | 宣言参照は「却下された自己整合性再検査」に当たらない | refuted | — | 一文の区別を採る: 再検査 = samples/tolerance を読み述語を再実行すること。宣言参照 = authority が解決した (path, sha256) を裁定済み identity と比較すること |
| B6 | luna | テストは空実装・握り潰しで緑にならない | refuted | — | g2 正例は activation 全鎖の証明とは報告しない |
| A1 | sol | `_registered_clock_self_audit` は恒真でない | refuted | — | 同 audit は本 wave で変更しない |

## D1537 の読み

- 「健全な世代が発効するまで一致なしのまま保つ」の主語は**当該環境系列** (有効契約が自己整合しない較正を pin する campaign 群) である。pin の path 1 本ではない。
- 「発効後に値は自然に埋まる」は、発効後に生産される g2-pinned の新 campaign を指す。既存の g1-pinned campaign は発効後も一致なしのまま (authority は不変)。
- 却下肢「層 3 で自己整合性を再検査する関門」= 層 3 が samples/tolerance から述語を再実行すること。本 wave はそれをしない。層 3 は authority が解決した (path, sha256) を、裁定で確定した exact identity の集合と比較するだけ。

## プラン v2 (実装する内容)

編集面は **2 file** だけ: `orchestrator/campaign/layer3_report.py`、`orchestrator/tests/test_layer3_report.py`。
`orchestrator/tests/test_env_contract.py`、`orchestrator/campaign/calibration_verify.py`、
`orchestrator/campaign/env_contract.py` は **触らない**。

1. **宣言** (`layer3_report.py` module 定数): D1537 で確定した自己整合しない較正の exact identity
   集合。型は `frozenset[tuple[str, str]]` (`(calibration_ref.path, calibration_ref.sha256)`)、要素は
   pegasus g1 (`output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json`,
   `753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49`) の 1 件だけ。docstring に
   D1537 の裁定 ID と「削除は登録簿から外れたとき (T-419 U-1/U-2)」を書く。effective-clock の再検査は
   しない。
2. **除外** (`_calibration_floors`): 現行どおり `_validated_pin_path` を**先に**呼ぶ (例外・
   `pin-file-missing` は不変)。その後、`contract_pin` の `(path, sha256)` が宣言集合に入るなら、
   **within_run の候補形成をこの campaign で行わない** (pin 由来も直下 record 由来も
   `candidates["within_run"]` へ append しない)。between_run の候補形成・pin-only 除外・一致判定は不変。
   結果として within_run は `no-matching-env-record` (schema の第 2 枝) になる。
   pin file が missing でも contract の (path, sha256) が宣言集合に入れば同じく除外する (判定の入力は
   契約の ref であって file の有無ではない)。
3. **理由の記録**: within_run の search 詳細の `contract_pin` object に key を 1 つ足す。
   key 名は実装子が決めてよいが、値は世代の状態を言わない固定文字列 1 つ
   (例: `"within_run_exclusion": "self-inconsistent-calibration"`)。`status` は従来の値のまま。
   between_run 側の `contract_pin` には足さない。schema は編集しない (`search` は自由な object)。
   `candidate_files` / `scanned_files` / `skipped_no_floor_block` の意味は変えない。
4. `_contract_calibration_pin`、`_validated_pin_path`、`_floor_protocol_and_basis`、
   `build_report` の接続点は変えない。

## テスト (実装する内容)

既存テストの期待値を変えてよいのは次の **3 件だけ**。他の既存テストの期待値・literal・pin は変えない。

- `test_pegasus_v2_adds_only_contract_pin_not_registered_glob` (:3467): within_run は `value None` /
  `provenance no-matching-env-record` / `source None`、search の `contract_pin.status == "validated"`、
  理由 key の存在と値、`candidate_files == []`。g2 file を同じ `registered/` に置いても glob 候補に
  ならないことは維持。between_run の `contract_pin` には理由 key が無い。改名可。
- `test_nested_exploration_root_resolves_contract_pin_by_suffix` (:3672): nested root でも同じく None。
- `test_nested_exploration_root_uses_direct_floor_when_pin_file_is_missing` (:3705): pegasus g1
  authority で pin file が無く直下 `within.json` がある場合、within_run は **None** になる (系列単位
  除外)。`between_run.search.contract_pin.status == "pin-file-missing"` の assert は維持。

追加する負例 (それぞれ「何が起きたら赤か」を docstring に 1 文):
- **直下 copy**: pegasus g1 authority + `_copy_contract_calibration` + g1 bytes を
  `output/env/pegasus/calibration/direct-copy.json` へ複製 → within_run None (path 単位除外へ退行したら赤)。
- **系列単位**: pegasus g1 authority + pin validated + 直下に一致する within record (genome 付きでも
  無しでもよい) → within_run None、between_run は同じ campaign で直下 between-run record に一致する
  (between_run まで抑止したら赤、within_run が直下を採ったら赤)。

追加する正例:
- **健全 pin は採られる**: 実 registry の pegasus g2 `calibration_ref` と実 bytes を tmp の
  `registered/` へ置き、`_calibration_floors(..., contract_pin=g2_ref)` を直接呼ぶ → within_run は
  `env-record`、source が g2、`contract_pin.status == "validated"`、理由 key **なし**。
  activation を stub しない。「発効後の全鎖」の証明とは書かない。
- **宣言の実在束縛**: `layer3_report` の宣言集合が、`env_contract.GENERATIONS` の attestation
  `required` な全世代のうち effective-clock 自己比較 (`env_attestation.expected_comparison_values` +
  `execution_guard.effective_clock_comparison_passes`、実 bytes) に落ちる世代の (path, sha256) 集合と
  **等しい**ことを assert する (宣言の不足・過剰の両方向が赤)。`test_env_contract.py` の helper を
  import しない (独立 oracle のまま)。

既存の `test_contract_pin_sha_mismatch_fails_closed_before_floor_use` (:3555) は無変更で、検証前の
短絡を検出する負例として使う。

## 変異事前登録 (DW-M01、実装後に probe で node を機械確定する)

| ID | 変異 | 期待 | 赤にする層 (単一理由) |
|---|---|---|---|
| M1 | 除外条件を恒偽にする (常に候補形成) | KILLED | g1 の負例 3 件 + 直下 copy + 系列単位 |
| M2 | 宣言集合を空にする | KILLED | 宣言の実在束縛 (不足) + g1 負例 |
| M3 | 宣言集合に g2 の ref を足す | KILLED | 宣言の実在束縛 (過剰) + 健全 pin 正例 |
| M4 | 除外を pin 由来 path だけに戻す (直下 record は候補に残す) | KILLED | 直下 copy / 系列単位 / pin-missing の負例 |
| M5 | 除外を between_run にも適用する | KILLED | 系列単位の負例 (between_run 一致を assert) |
| M6 | 除外を `_validated_pin_path` の前に置き検証を飛ばす | KILLED | :3555 SHA 不一致 fail-closed |
| M7 | pin-missing のとき除外しない (validated 時だけ除外) | KILLED | :3705 の改訂負例 |
| M8 | 理由 key を書かない | KILLED | g1 負例の理由 key assert |
| M9 | 等価変異 (集合 literal の構文だけ変える、例 `frozenset({...})` → `frozenset([...])`) | SURVIVED | なし (harness の SURVIVED 検出の正例) |

受理集合を縮小する wave なので、承認外の過剰拒否の正例として M3 / M5 を含める。

## 成果物影響 (DW-G05)

- 既存の層 3 レポート 7 件 (すべて v1 lock、linux-baremetal) の noise_floor 値は変わらない。再生成しない。
  dossier・T2136 変異台帳にある g1 値の写しも再発行しない。
- 今後生産される pegasus v2 (g1 authority) campaign の層 3 レポートは within_run が None になる。
  現存する実 campaign にこの条件のものは 0 件。
- `layer3_report.py` の bytes が変わるので、今後生産される全 report の `meta.generator.sha256` が変わる
  (自己 provenance であり、凍結 golden はない)。
- certified 選択・受理集合・試行台帳・campaign lock・環境契約・activation record は変わらない。

## scope 外 (実装しない)

- 自己整合性の再検査 gate (D1537 却下肢)、共有台帳・manifest、宣言の一般化、`test_env_contract.py` の
  改変、activation の実施、新 status 値。
