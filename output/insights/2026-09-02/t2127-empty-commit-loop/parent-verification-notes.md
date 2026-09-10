# 親による段 2 プランの裏取り (段 4 裁定の入力)

段 3 の 2 レンズと独立に、親がコードを読んで確かめた事実。

## 1. consumer 在庫の実測 (プランの指摘を受けた再測定)

`grep -rl` で file 数として測り直した。`.claude/worktrees` と `orchestrator/tests/` を除外。

- `CERTIFIED_ACCEPTANCE` を名前で参照する production file: **20**
- `require_persisted_certified_commit` を呼ぶ production file: **9** (外部 8 + 定義元)
- **和集合 = 22** (プランの表と一致)
- 差分 2 件は `backoff_repro.py` と `paper_story_a2_certification.py`。
  `CERTIFIED_ACCEPTANCE` を名前で持たず helper だけを呼ぶ。名前 grep 1 本では落ちる。

**プランの「未指名 1 file」は存在しない。** 親の初回記載「10 file」が誤りで、正しくは 9 file
(外部 8 + 定義元 1)。プランの「8 + 定義元 = 9」が正しい。この未解決項目は閉じてよい。

## 2. 直接 22 file は consumer の全閉包ではない (名前 grep で見つからない経路の実在)

`replay.load_landscape()` は certified view を内部で取得し、committed 評価値を配る。
その呼び手は次の 5 箇所で、**うち 2 file は 22 の表に載っていない**。

- `orchestrator/campaign/search_baselines.py:304` → 直後に `assert_complete` (保護あり)
- `orchestrator/campaign/guided.py:204` → 直後に `assert_complete` (保護あり)
- `orchestrator/campaign/guided.py:225` (`cmd_evaluate`) → `assert_complete` なし
- `orchestrator/campaign/guided.py:252` (`trial_result`) → `assert_complete` なし
- `orchestrator/campaign/replay.py:293` → 直後に `assert_complete` (保護あり)

`search_baselines.py` と `guided.py` は `CERTIFIED_ACCEPTANCE` も
`require_persisted_certified_commit` も名前で持たない。**間接 consumer である。**

保護なしの 2 箇所の挙動 (親が実測ではなくコード読解で確認):
- `guided.py:225` → `replay.replay_evaluate` が landscape に無い genome で `KeyError` を送出。fail-closed。
- `guided.py:252` → `winner_tied_set` が空集合になり `reached=False`。誤った肯定は出さない。

→ **プランが非ゼロ要求を `load_landscape` の中へ置く判断は正しい。**
呼び手ごとに置く設計だと、この 2 file を名前 grep で取りこぼす。
ただし裁定文には「直接 22 + `load_landscape` 経由の間接」と書き、22 を全閉包と呼ばない。

## 3. 「要求する」分類のうち 1 件は既存策で足りている疑い (反実仮想の検査)

`backoff_overthrottle.py` をプランは「要求する」に分類する。しかし同 file の
`require_complete_bindings` (`:150-159`) は
`set(bindings) != expected` で落とす。commit 0 件なら `bindings` は空、`expected` は
`genomes(tag)` で非空なので、**既存の exact 集合一致検査が先に赤を出す**。

→ ここへ非ゼロ helper を足しても、**その helper だけが殺す変異が存在しない**恐れがある
(`DW-M02` の所見ゼロ裏取り、機構の必要性は反実仮想で確かめる)。
段 4 で「足す/足さない」を裁定する。足すなら「同じ回に他 gate が赤を出さない」ことを
変異で示すこと。示せないなら `DW-G05` により足さない (足りる既存策がある)。

同じ検査を `backoff_sweep_report.py`、`backoff_extended_sweep_report.py`、
`layer3_report.py` の certifying 経路、`autonomous_trial_completeness.py` の
certifying chain にも適用する。

## 4. 親が exact 述語まで辿った consumer (プランの表との突き合わせ用)

いずれも commit 0 件を自前で処理しており、誤った certified 主張は出さない。
プランの「要求しない」分類と一致する。

- `s6_sort_sweep.py:541` — `certified = commit is not None` を variant ごとに判定
- `s1_report.py:338-345` — `len(commits) != 1` を明示拒否
- `layer3_report.py:634-637` — commit 無しを `commit-event-absent` で棄却側へ
- `critic/digest.py:701-746` — commit のある variant だけ返す
- `backoff_sweep_report.py:65,77-79` — 空なら `静的点が無い → skip`
- `p3_s4_red.py:231-234` — 棄却の読み出し専用
- `replay.py:186-225` — variant ごとに `certified_of`
- `paper_story_a2_certification.py:2762-2776` — `if commit is not None:` の枝だけ
- `autonomous_trial_completeness.py:4916-4926` — **負例側の制御**。
  failure campaign は certified 受入で拒否されねばならない。
  admission 層で 0 件を拒否すると abort-only campaign に対して恒真化する。

## 5. 版のずれ (記録)

段 3 の 2 レンズは 04:07 に起動し、親は 04:10 に brief の consumer 在庫を訂正した
(22/10 → 20/9/和 22)。レンズが読んだ brief は訂正前の可能性がある。
レンズ B は在庫の網羅性を独立に検査する指示を受けているため、
指摘が来たら訂正済みであることを裁定文に書く。

## 6. 反実仮想の検査 — 「非ゼロを要求する」6 箇所の必要性

各箇所について「非ゼロ helper を置かなくても、同じ入力で別の gate が先に赤を出すか」を
コードで確かめた。出すなら、その helper だけが殺す変異は存在せず、恒真な保証である。

| 箇所 | 既存 gate が先に赤を出すか | 判定 |
|---|---|---|
| `backoff_sweep_report.py` return 前 | 出す。`:77-79` の `if not static: skip`。`static` は committed genome 由来なので、この分岐を抜けた時点で commit >= 1 が含意される | **恒真。足さない** |
| `backoff_overthrottle.py` binding 返却前 | 出す。`:150-159` の `require_complete_bindings` が `set(bindings) != expected` で raise。commit 0 件なら bindings は空、expected は非空 | **恒真。足さない** |
| `backoff_extended_sweep_report.py` return 前 | 出す。`:509-510` の `if len(perf_statuses) != 1: raise`。commit 0 件なら perf_statuses は空で len=0 | **恒真。足さない** |
| `replay.load_landscape` `:184-187` | 出さない。view 取得直後で、commit 投影より前に置かれる | **効く。足す** |
| `layer3_report.build_accepted_report` `:743-770` | **出さない。** 要求するのは acceptance receipt の certifying、trial 一致、admission_status=admitted、decision 不変、epoch E1 だけで、**どこも commit の存在を要求しない** | **効く。足す** |
| `autonomous_trial_completeness` certifying chain `:4960-4979` | 出さない。ここは**外部で作られた** persisted certifying Layer3 report を検査する側であり、producer 側の修正を前提にしてはいけない | **効く。足す** |

## 7. 成果物影響の 1 行 (DW-G05)

**放置すると `layer3_report.build_accepted_report` は、1 件も commit されず 1 件も検証されて
いない campaign に対して `certifying_input: True` の Layer3 report を発行できる。**
中身は全件 reject である。これが本 wave で受理集合が実際に変わる唯一の箇所であり、
scope と must-fix の根拠である。

## 8. 親の裁定案 (段 3 の所見と突き合わせて確定する)

- 共通 helper `admit_persisted_certified_commits()` と件数 field: プランどおり採用。
- 非ゼロ要求の配線は **6 箇所 → 3 箇所へ縮小**する
  (`replay.load_landscape`、`layer3_report.build_accepted_report`、
  `autonomous_trial_completeness` の certifying chain)。
  外した 3 箇所は `DW-G05` の「足りる既存策がある」に当たる。
- 外した 3 箇所には、代わりに**既存 gate が commit 0 件を拒否することを固定する回帰 test**
  を置くか、置かないかを段 4 で決める。置くなら「既存 gate の回帰 pin」であって
  本 wave の機構の存在証明ではないと明記する。

## 9. 実測 — 成果物影響はコード読解でなく既存テストが既に示していた

`orchestrator/tests/test_layer3_report.py:1825-1845` の現行 passing test は、
`_campaign(tmp_path, [_record("build_start", genome="g", src_token="s")])` すなわち
**build_start 1 件だけ、commit 0 件、verify_done 0 件の campaign** に対して
`build_accepted_report` を呼び、`report["certifying_input"] is True` と
`campaign_verifier_epoch.state == "E1"` を assert している。

**つまり「1 件も commit されず 1 件も検証されていない campaign から certifying な
Layer3 report が出る」ことは、既存テストが現に固定している。**
親のコード読解ではなく、repo 内の実物が示している。

## 10. 実測 — プランのテスト変更一覧に抜けがある

`layer3_report` の certifying 経路に非ゼロ要求を入れる probe
(`require_certified_campaign_view` を包み commit 0 件を拒否) を当てた結果:

- baseline: `test_layer3_report.py` 180 passed / 0 failed
- probe: **4 failed**
  - `test_accepted_report_requires_e1_and_records_epoch`
  - `test_certified_report_omits_current_verifier_conformance`
  - `test_render_accepted_persists_certifying_report`
  - `test_render_and_render_accepted_race_rejects_second_writer[render_accepted]`

**プランの「既存テストの扱い」節は `test_layer3_report.py` を 1 行も挙げていない。**
プラン自身が `layer3_report` を「条件付きで要求する」に分類しているのに、
その配線で赤くなる既存テストを列挙していない。段 4 の must-fix とする。

この 4 件は削除せず、fixture へ正当な commit + verify_done + receipt を足して
「commit のある campaign なら certifying report が出る」を保ち、
別途「commit 0 件では出ない」を新 node として足す (プランが
`test_artifact_admission.py` に採った 2 命題分割と同じ方針)。

## 11. 件数 field が何を証明し、何を証明しないか (裁定文へ明記する)

`CertifiedCampaignView` は `frozen=True, slots=True, init=False` で、
`_CERTIFIED_VIEW_TOKEN` を持つ custom `__init__` だけが発行できる
(`artifact_admission.py:327-362`)。プランの field 追加は構造上そのまま実装できる。

ただし正直に書くべき限界がある。プランの `__post_init__` 検査は
「件数 == immutable snapshot 内の commit record 件数」であり、これは **records から
導出できる値**である。したがって件数 field は次を証明する / しない。

- **証明する:** 誤った件数を発行できない (0 件を 1、1 件を 0 と偽れない)。
  consumer が件数を信頼してよい。
- **証明しない:** その commit が実際に `require_persisted_certified_commit` を
  通ったこと。件数だけ数えて検査を飛ばす実装でも `__post_init__` は通る
  (プランの変異 M1 がこれに当たり、kill するのは件数検査ではなく
  `test_persisted_commit_gate_rejects[*]` の側である)。

→ 件数 field は**共通入口の投影であって検証の証拠ではない**。
裁定文と worklog にこの区別を書き、「件数があるから検証済み」と読ませない。
実際の防壁は (a) 走査 loop が共通 helper 1 本であること と
(b) 非ゼロを要求する 3 箇所であり、件数 field はその橋渡しである。
