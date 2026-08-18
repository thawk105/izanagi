# [T-1086] oracle 実走後の store 再読を報告 receipt で塞ぐ

2026-08-18、branch `worktree-dev-wave-t1086-report-receipt`。
2026-08-15 /rulings 全件の裁定 (報告の receipt で塞ぐ) の実装。

## 何を塞いだか

oracle 実走の**前**には二重防壁があった。

- 第一防壁: `s8b_oracle_driver._prepare_v2_execution` が run marker 作成前に、全 schedule 行の
  store 実体の存在と full sha256 一致を検査する。
- 第二防壁: `pipeline` が build 直後・trace/bench 起動前に `expected_perf_sha256` と厳密照合する
  (TOCTOU)。

実走が終わってから observations を書くまでの窓には、これに相当するものが無かった。
`s8b_oracle_report` も `s8b_oracle_judge` も store bytes を一度も読み直していない。
本 wave はそこへ receipt を置いた。

## 設計

- `build_observations` に keyword-only `reverified_freeze: ReverifiedFreeze | None` を足し、
  official 経路 (`main()`) だけが authority token として渡す。exact type と manifest 側
  freeze sha256 との一致を検査する。
- 期待 SHA の唯一の源は `ReverifiedFreeze.binaries_by_cell[cell_id]["binary_sha256"]`。
  run 自身が WAL に書いた `build_done.perf_bin_sha256` は使わない。
- store は component ごとに `O_NOFOLLOW` で開き、leaf を `fstat` で regular file と確認し、
  1 MiB chunk で hash する。字句が非正規な `store_path`・symlink・非 regular leaf は
  `ReportError` で拒否し、**store の不在 (output_root 不在を含む) は `missing`** として
  receipt に記録する。
- observations に `store_reverification` (outer は `{state, cells}`、cell は
  `{cell_id, store_path, expected_sha256, actual_sha256, state}`) を載せる。
- judge は report の定数を import しない独立な closed schema 定数で再検査し、
  欠落・空・部分集合・重複・outer と cell の矛盾・SHA と state の矛盾・mismatch・missing を
  `top_reasons` へ積む。**outer の `state` は cell から再導出**し、自己申告を信じない。
  `judge_oracle` の呼び出し規約 (位置引数 1 + keyword 3) と judge CLI は不変。

## この receipt が保証しないこと

- **連続不変性ではない。** 保証は「report が各 store を読んだ瞬間に freeze の SHA と一致した」
  ことだけである。一時改変後に読み取り前へ復元された場合と、読み取り後の差し替えは検出しない。
- **封印でも偽造耐性でもない。** store と receipt を同時に改変されれば determinate へ到達できる。
  これは [T-1103] が明示的に見送った面と同一であり、本 wave の scope 外である。
  主張の限度は「単独 oracle 改竄まで」。
- **certified 選択値や台帳行は現 checkout では変わらない。** `layer3_report` が
  「No certified-selection consumer exists in this checkout」と明記している。
  本 wave が実際に変えるのは observations report / oracle verdict / combined verdict まで。

## 変異 matrix

| attempt | spec | 結果 | 位置づけ |
|---|---|---|---|
| 1 | `mutation-spec-probe1.json` | baseline PASSED、5 KILLED / 7 MISMATCH / SURVIVED 0 | **probe**。期待 node の完全集合を得るための走行 |
| 2 | `mutation-spec-v2.json` | baseline PASSED、10 KILLED / 2 MISMATCH / SURVIVED 0 | 本走 |
| 3 | `mutation-spec-v3.json` | **baseline FAILED** | 無関係なフレークで中止 (下記) |
| 4 | `mutation-spec-v3.json` | baseline PASSED、2 KILLED / MISMATCH 0 | 残り 2 件の本走 |

**最終: baseline PASSED、12/12 KILLED、SURVIVED 0、MISMATCH 0。**

### probe が必要だった理由 — 防御の層を 2 度読み違えた

事前登録した「resolve containment を削る」変異は、敵対レビュー 2 本が独立に
「後段の symlink 検査に先取りされる等価変異」と指摘した。containment + 親/leaf の `S_ISLNK` を
同時に削る形へ直しても、symlink 負例 2 件は緑のままだった。真因は、`S_ISLNK` 検査が
`lstat` の型検査 (`S_ISDIR` / `S_ISREG`) と冗長で、実際に拒否している層ではなかったことである。
`os.stat(..., follow_symlinks=False)` の結果に対する型検査それ自体が symlink を弾き、
さらに `O_NOFOLLOW` が `ELOOP` で 3 番目の防壁になっていた。
型検査 2 件を除去対象へ加えて初めて負例が反転し KILLED になった。

同型の重複は字句検査にもあった。字句検査だけを削っても `..` の負例は resolve containment が
受けて緑のままで、赤になったのは絶対 path・制御文字・backslash の 3 例だけだった。

**教訓: 多層防御は望ましいが、変異の期待 node を「層の名前」で書けると仮定してはいけない。**
拒否の名前ではなく拒否の効果で層を数える。

### source hash pin による道連れ (F226 と同型)

`test_s8b_oracle_manifest.py` の `PIN_GATE_SPEC_RAW` は `s8b_oracle_report.py` /
`s8b_oracle_judge.py` / `s8b_oracle_artifacts.py` の source SHA-256 を literal で埋め込む。
親が一時変異で実測したところ、`s8b_oracle_report.py` を 1 byte 変えるだけで同 file の
100 件中ちょうど 2 件が赤になる。

- `test_build_approved_valid_fixture_output_depends_only_on_spec_pin`
- `test_reviewed_spec_has_independent_canonical_bytes_and_sha_literal`

`test_reviewed_spec_requires_canonical_bytes_without_trailing_lf` は**影響しない**
(末尾 LF 拒否が generator 検証より先に発火するため)。
production 側は `s8b_oracle_spec.APPROVED_SPEC_SHA256` が `None` のため未発火であり、
赤くなるのは test golden だけである。全 12 変異の期待 node にこの 2 件を含めた。

## フレーク 2 件

いずれも本 wave の差分から到達不能で、単独走で再現しなかった。

- `test_t126_pegasus_tools.py::test_submit_rejects_symlink_component_hidden_drift_and_skip_worktree`
  — attempt 2 の M6 に混入。attempt 1 の同一変異では登録どおりちょうど 4 件だった。
- `test_campaign_claim.py::test_two_real_processes_racing_acquire_have_exactly_one_winner`
  — attempt 3 の baseline を落とし、その attempt を丸ごと無効にした。単独走は 26 件全緑。

## 裁定パッケージ (本 wave では実装しない)

1. **実走前 gate の `s8b_oracle_driver._store_sha256`** も symlink を辿り、regular file を確認せず、
   `read_bytes()` で全体を一括確保する。report 側と同じ穴だが本 wave の変更面ではなく、
   族一般化に必要な独立 2 例が揃っていない。
2. **store と receipt の同時改変**に対する耐性。[T-1103] が見送った偽造耐性の面と同一。

## 成果物

- `verbatim/` — 段 1〜7 の子成果物 (brief、plan、敵対相談 2 本、裁定、実装、レビュー 2 本、
  fix 2 巡、main 先行取り込み)
- `mutation/` — 4 attempt 分の spec と台帳、事前登録 v2
