# [T-2067] (b)(c)(d) — 床値選択の公開迂回口と、実導出の経路別被覆

- 日付: 2026-09-03
- branch: `worktree-dev-wave-t2067-bcd-selection-closure`
- 基準 commit: `dc9a060d3` (local main と乖離 0)
- 正本: `docs/archive/worklog-phase3-0902-1202.md` の [T-2067] 本文、D1503、D1504

## 何をしたか

ユーザー裁定により (b)(c)(d) だけを実装した。(a) oracle report / verdict / judge への選択強制、
(e) s8c C06 予算群、(f) 起動証明書の実時間性は scope 外。

### (c) 公開迂回口を塞ぐ

`orchestrator/campaign/s8b_oracle_manifest.py` の 3 関数を private へ改名した。

| 旧名 | 新名 |
|---|---|
| `build_manifest` | `_build_manifest` |
| `build_manifest_from_ratified` | `_build_manifest_from_ratified` |
| `write_manifest` | `_write_manifest` |

関数本体・serializer・create-only 動作・例外型・引数は 1 文字も変えていない。改名と呼出し側の
追随だけである。public に残るのは選択 gate を通る `build_approved_manifest` だけになった。

test caller の改名は 25 箇所。内訳は `test_s8b_oracle_manifest.py` 20 件、
`test_s8b_oracle_report.py` 3 件、`test_s8b_oracle_driver.py` 2 件。
production の内部 caller は `build_approved_manifest` 内の 1 箇所だけである。

公開面の負例として `test_ungated_manifest_apis_are_not_public` を 1 本足した。
旧 3 名が module の public attribute として解決できないことを parametrize で固定する。

### (d) 実導出を launch 経路と consumer 経路へ通す

`orchestrator/tests/test_s8b_ratified_verify.py` へ、実 earlier official run を設置する helper と
genuine な正例・負例を対で足した (新規 4 node)。

| node | 何を固定するか |
|---|---|
| `test_launch_validate_rejects_genuine_eligible_earlier_official_run` | 導出 True の earlier run を launch 経路が rule-mismatch で拒否する |
| `test_launch_validate_accepts_genuine_ineligible_earlier_resume` | 導出 False の earlier run を launch 経路が受理する |
| `test_g1_selection_helper_rejects_genuine_eligible_earlier_official_run` | 同じ拒否を consumer 経路 (狭い API) で固定する |
| `test_g1_selection_helper_accepts_genuine_ineligible_earlier_resume` | 同じ受理を consumer 経路で固定する |

設置するのは `result.json` / `manifest.json` / `journal.jsonl` と
`.git/izanagi/s8b-holdout-admission-v1` の admission 台帳だけである。
**`launch_certificate.json` は作らない** — 選択走査 (`s8b_holdout_freeze.py:1842-1853,1877-1909`) は
earlier run の certificate を読まず、`validate_selected_certificate` は選択済み run 用で
launch / consumer 経路では既定 False だからである。

既存の stub 版 2 test (`test_launch_validate_rejects_floor_selection_rule_mismatch`,
`test_g1_selection_helper_rejects_rule_mismatch`) は D1504 のとおり
「gate が呼ばれた事実と引数」を固定する検査点として、行内容・期待値・monkeypatch を変えずに残した。

### (b) 母集合の数え直し

未強制の load-only consumer は **4 群**で確定した。

| 入口 | 呼び方 | 帰属 |
|---|---|---|
| `orchestrator/campaign/s8b_oracle_report.py:2547` | load + reverify | (a) scope 外 |
| `orchestrator/campaign/s8b_oracle_judge.py:749` | load + reverify | (a) scope 外 |
| `orchestrator/campaign/s8b_verdict.py:828` | load + reverify | (a) scope 外 |
| `orchestrator/campaign/p3_autonomous_workload_trial.py:4710` | load only (C06 予算) | (e) scope 外 |

強制済みの対照は `s8b_oracle_manifest.py:1205`、`s8c_result_judge.py:2078`、
`s8b_oracle_driver.py:664` と `:1351`。
**`s8b_oracle_driver.py:496` は強制点ではない** — private core 内の self-load であり、
public v2 wrapper はこの形で到達させない。先行 wave の整理を訂正した。

## 親の probe が前提を狭めた

正本 (archive worklog 1202) の (d) は「実導出を走らせて rule-mismatch を出す test が repo に無い」と
していた。**これは現行 main では偽である。**
`test_s8b_holdout_freeze.py::test_v2_candidate_rejects_later_run_using_derived_earlier_eligibility` が
2026-08-29 (commit `31426fb9a`) から存在し、`_install_real_floor_selection_runs` で実 earlier run を
作って実導出を通している。

親が `_derive_floor_selection_eligibility` を無条件 `False` へ一時変異させて実測した
(DW-O19、即時復元・非 commit、復元 bytes は
`7904d47b36fa87ac40dac0c2da1a114d4b04000ed5a8c15f17b89523b9ebbdb0` で一致)。

| 走行 | 結果 |
|---|---|
| baseline (4 file、`-k "selection or eligib"`) | 25 passed / 34.90s |
| 変異後 (同一集合) | 6 failed, 19 passed / 34.79s |

赤 6 件は**すべて** `test_s8b_holdout_freeze.py` (v2 candidate 経路) だった。
`test_s8b_ratified_verify.py` (launch + 狭い API)、`test_s8b_oracle_manifest.py`、
`test_s8c_result_judge.py` は全緑。

**したがって穴は「repo 全体で実導出が未検査」ではなく「launch 経路と consumer 経路が
実導出を一度も通らない」である。**(d) の対象はこの 2 経路に限られる。

### この数字の限界

**「6 failed」は `-k "selection or eligib"` filter 内の値であり、repo 全体の kill 数ではない。**
段 3 の 2 レンズが独立に、filter 外の
`test_s8b_holdout_freeze.py::test_v2_candidate_enumerates_and_reads_earlier_run_through_bound_dirfds`
(`:2364`) も実導出を通すことを指摘し、親が現物を読んで追認した。
1 走の観測から repo 全体へ一般化してはならない。

## 段 3 の敵対相談が採否を変えた 2 件

いずれも **D1504 が既に定めていた要求の履行**であり、scope 逸脱ではない。
D1504 は「機構そのものの証明は、実 loader と実 callee を通す genuine g1 の正例と負例に担わせる」と
書いている。

1. **段 2 プランの `sys.setprofile` による code frame 観測は採用しなかった。**
   レンズ A が「実導出の冒頭を `return True` に変える故障では同じ code frame と引数が観測され、
   後段は予定どおり rule-mismatch を出すので新規 test は緑のまま」と反証した。
   正例・負例の対がその役目を果たすため、profiler は機構を増やすだけである。
2. **fixture は `RatifiedFreeze` を直接構築せず、commit 後に `load_ratified_freeze(root)` で
   取り直す。** レンズ A が「実 loader を通らない」と指摘した。D1504 の却下選択肢に
   「loader と選択 assert の両方を stub する — 機構を一度も通らない緑になる」がある。

## 閉じていない範囲 (絶対規律 7 に従い明記する)

- **(c) の private 化は Python の命名規約であって機構的な封印ではない。**
  underscore 名を知る in-process の caller は `_build_manifest` / `_build_manifest_from_ratified` /
  `_write_manifest` を直接呼べる。ユーザーの依頼は「**公開**迂回口を塞ぐ」であり、
  seal token は scope 外とされた新機構なので採らなかった。加えて 25 箇所の test caller は
  低位構築面として正当に使っており、token を課すと既存 fixture を壊す。
- **`verify_manifest` (`s8b_oracle_manifest.py:1019`) は選択 token を要求しない。**
  builder の private 化では覆えず、(a) の裁定対象と重なる。裁定パッケージへ送る。
- **`_write_approved_manifest` は任意の exact `OfficialManifest` を candidate directory へ保存できる。**
  同じ限界に属する。

## 実測

すべて worktree `dev-wave-t2067-bcd-selection-closure`、基準 `dc9a060d3`、未 commit 差分あり。

| 走行 | 結果 |
|---|---|
| `test_s8b_ratified_verify.py` 単独 | 189 passed / 767.14s |
| `test_s8b_oracle_manifest.py` 単独 | 107 passed / 50.70s |
| `test_s8b_oracle_report.py` + `test_s8b_oracle_driver.py` | 395 passed, 6 skipped / 120.81s |
| 4 file 同時 | 10% 到達時点で赤 20 件超 (中止) |
| **全走 (正規の走行構成)** | **実装起因の赤 0 件** |

全走の唯一の赤は
`test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes` で、
「作業ツリーの非 output 変更は自分の 2 file だけ」という gate が本 wave の 5 file を検出したものである。
未 commit 差分が存在すること自体の帰結であり、統合 commit 後に自動解消する。

4 file 同時走の赤は全走で再現しなかった。焦点走の file 集合は正規の走行構成ではなく、
集合の作り方によって実装と無関係な赤が出る。詳細は failures 台帳の該当エントリ。

## 変異について

段 4 で M1〜M5 を事前登録したが、**本 wave では変異 harness を実走していない。**
段 3 のレンズ C が変異 X (実導出を常に False) と変異 Y (冒頭 return True) を静的に追跡し、
X が拒否側 2 node を、Y が受理側 2 node を赤にすることを確認した。
親が実測したのは変異 X 相当の一時変異 (probe) だけで、これは実装前の baseline に対するものである。
実装後の本走は未実施であり、緑とは申告しない。

## 子の実走状況

実装子と両レビュー子はいずれも codex sandbox の制約で pytest を開始できず、
正しく「実装済み・未実走」と申告した。実測はすべて親が行った。
