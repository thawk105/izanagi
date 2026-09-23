# dev-wave の Codex 子 model を gpt-6-astra → gpt-6-sol へ移行 (2026-09-23)

- 依頼: 2026-09-23 ユーザー指示「gpt-6-sol が使えるようになったのでそちらへ移行したい、reasoning は medium」。
- 決定: 本 wave の decisions fragment (slug `dev-wave-codex-model-sol`、`docs/spool/decisions/2026-09-23-dw-codex-model-sol-1.md`、D 番号は land の fold が付ける)。
- 段構成: 軽量版 (DW-C00)。段 2・3 と段 6 レビュー子は省略 (設計択一なし・正しさ防壁非該当・受理集合は model 名の値だけ)。
  brief = `brief.md`、段 4 裁定と変異事前登録 = `s4-adjudication.md`。

## 1. 生死確認 (段 1、DW-G01)

`codex exec -m gpt-6-sol -c model_reasoning_effort=medium --sandbox read-only` を 1 回 (2026-09-23 07:59 JST 前後、job tmp で、サブスク = ChatGPT ログイン、ANTHROPIC / OPENAI_API 系 env は 0 件)。
rc=0、出力 `PONG`、log header `model: gpt-6-sol` / `provider: openai` / `reasoning effort: medium`。

## 2. 変更

| commit | 内容 |
|---|---|
| e39e43c9c | docs: DW-O01 の model 権威行を `gpt-6-sol` へ (V2 形式を保持、親 role=author scope=docs) |
| b8c9c6cbe | check_docs.py の literal、test_check_docs.py 2 か所、test_dev_wave_launch_authority.py 2 か所を sol へ (Codex author の patch を所有 3 path に限って適用) |

段 1 で scope 外と判定したもの: `test_s8b_ratified_freeze.py` の `model=gpt-6-astra` (AI-Agent trailer 文法の例示値。DW-O01 を読まない)、D2137 (docs 同期の手順で sol でもそのまま成立)、過去記録の astra 表記 (規律 7)。

## 3. 実装子 (段 5)

- 1 回目 `s5-author-A` (08:06〜08:10 JST): codex exit 0・12 call・受領証 `recorded_model=gpt-6-sol` / `recorded_effort=medium` だが、`evidence_status=invalid` / `launcher_rc=1` / `outcome=not_accepted`。原因は子が `orchestrator/tests/test_check_docs.py` を `cat` で全体表示し、5756 / 5779 行の非 NFC 文字を含む event 行 (473,605 byte、stdout 19 行目) が起動器の NFC 検査に落ちたこと (F223 の再発)。差分 (commit 311bbb50c) は裁定どおりの 5 行だったが不採用。
- 2 回目 `s5-author-A2` (08:14〜08:17 JST、同 unit で base から branch `dev-wave-sol-unit-a-r2` を切り直し、prompt に「5740〜5800 行を表示しない・全体を cat しない」を追加): `outcome=accepted`・`launcher_rc=0`・12 call・`recorded_model=gpt-6-sol`・`recorded_effort=medium`。commit 77ab8046b、patch sha256 `5e7a43f165ead7b1118dd07024bb2b1122dece2fb6318f140219522760f16c7d`。1 回目と内容同一。報告 = `s5-author-A2-out.md`、prompt = `s5-author-A2-prompt.md`。
- 本 wave の実装子自体が、改訂後の docs から gpt-6-sol / medium を導出して走った最初の Codex 子である。

## 4. 検査

- login の `python3 tools/check_docs.py`: 違反なし (b8c9c6cbe)。
- 導出の実測 (`launch_authority.snapshot_authority` + `derive_launch`、b8c9c6cbe の木): authority v2、全段 (plan / consult sol・luna / author / review / fix / focus) の model = `gpt-6-sol`。effort は author / review / fix / focus = medium (docs)、plan / consult = 呼び出し側指定 (unbound、従来どおり)。
- 焦点走 (計算ノード Pegasus 要求 18930、08:22〜08:23 JST、b8c9c6cbe): test_check_docs.py・test_dev_wave_launch_authority.py・consumer の test_codex_worker_launch.py・test_s8c_preregistration_invariant.py と DW-O26 の inventory 4 群 (test_campaign.py・test_official_perf_closure.py・p3 namespace・test_p3_b4_wiring_probe.py) の 8 file で 1437 passed / 11 skipped、rc=0。

## 5. 変異 (段 6、`mutation/`)

独立 clone (main = b8c9c6cbe) で `tools/mutation_worktree.py --runner-mode dispatch`。runner = `run_tests.py --force-dispatch test_check_docs.py test_dev_wave_launch_authority.py -q -rf`。

- probe (spec sha256 `5b85da86dc0a17f54481d4d13b78699963819a7324da290bc671e95bfd04646b`、全件 SURVIVED 登録で期待 node を収集): baseline 要求 19028 が 08:51 から約 20 分 PRR に滞留したが qdel せず待って完走。m0 SURVIVED、m1 / m2 は想定どおり MISMATCH (観測 node を収集)。
- final (spec sha256 `033a8cf8467d0470115e28a2849ee1da80aed166930b084ee254f4ebac1aa78b`、要求 19113〜19140、09:19〜09:30 JST): **KILLED 2 / SURVIVED 1 / MISMATCH 0、registered 3 すべて matching**。

| id | 変異 | 結果 | 赤の node (完全集合) |
|---|---|---|---|
| m0 | check_docs.py の literal 直後にコメント 1 行 (等価) | SURVIVED (期待どおり) | なし |
| m1 | check_docs.py の literal だけ astra へ戻す | KILLED | test_check_docs.py の `test_dev_wave_model_pin_rejects_dw_o01_authority_drift`、`test_dev_wave_model_pin_contract_is_time_invariant` |
| m2 | docs の DW-O01 行だけ astra へ戻す | KILLED | test_dev_wave_launch_authority.py の `test_all_stage_models_match_independent_docs_cross_check`、`test_snapshot_and_derive_current_authority_positive`、effort の docs 独立照合 5 件 (review / author / fix×2 / focus) |

注: 実 repo へ check_docs を当てる `test_dev_wave_model_pins_accept_current_docs_contract` は growth hold (D335) の対象で pytest では skip されるため、m1 / m2 のどちらでも赤の集合に入らない。実 repo の docs と literal の整合は `tools/check_docs.py` 本体の実行 (親の検査) が担保する。m2 で effort の照合試験 5 件も赤になるのは、これらが DW-O01 を含む docs 権威 snapshot 全体を独立照合と比べるためで、赤の理由は m2 の 1 行だけに絞れる (他の置換なし)。

## 6. 切り替わりの時点

起動器は投入時点の `--repo-root` の docs から model を導出する。本 wave が local main へ着地した後に始まる wave (とその子 worktree) から gpt-6-sol になる。着地前に始まって走っている wave は、自分の木の docs どおり gpt-6-astra のまま走り終える。
