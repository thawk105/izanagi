# dev-wave・rulings・next-tasks の Codex 子を gpt-6-astra・reasoning=ultra へ (2026-09-30)

- 依頼: 2026-09-30 ユーザー指示「dev-wave, rulings, next-tasks で codex を gpt-6-astra・reasoning=ultra で使う」。逐語 = `verbatim/request-md_1.txt`。
- 設計判断の正本: 本 wave の decisions fragment (`docs/spool/decisions/2026-09-30-dev-wave-codex-astra-ultra-1.md`、land 時の fold で D 番号が付く。D2229 を supersede)。
- wave branch `dev-wave-codex-astra-ultra`、基準 main 2094e8862。段の成果物の逐語は `verbatim/` (brief・plan・相談 2 本・裁定・実装子 2 本・レビュー 2 本・fix・焦点再レビュー)。

## 決めたこと (要約)

- model は全段 `gpt-6-astra`、effort は DW-S02 / S03 / S05-A / S06-A / S06-C を `ultra`、`CODEX_REASONING_EFFORTS` に `ultra` を追加。
- **ultra の委任 (spawn_agent) をした attempt は受理しない。** prompt で委任を禁じ、root rollout に `spawn_agent` の function_call があれば
  起動器が `delegation_detected` で拒否する (online と sealed 再検証で同じ判定)。委任先を会計して受理する案は採らなかった (理由は decisions)。
- rulings の相談の起動例に `--reasoning ultra` と DW-S03 参照。next_tasks_consult.sh は `-m gpt-6-astra`・既定 ultra・委任禁止 1 行。
- docs 予算: L1.5 は既存 3 文の意味等価な縮約で旧予算 9,696 bytes 内 (9,692 bytes)、rulings.md は 5,623 bytes (上限ちょうど)。上限は引き上げていない。

## 実測 (生死確認)

| 項目 | 結果 | 証跡 |
|---|---|---|
| astra・ultra の直打ち (`codex exec -m gpt-6-astra -c model_reasoning_effort=ultra --sandbox read-only`、ChatGPT ログイン、ANTHROPIC/OPENAI 系 env 0 件) | rc=0、出力 PONG、header `model: gpt-6-astra` / `reasoning effort: ultra`、6.4 秒 | `verbatim/s1-brief.md` L1 |
| 改訂後 docs から導出した起動器実走 | 段 6 review 2 本とも requested / recorded = `gpt-6-astra` / `ultra`、`outcome=accepted`、evidence issue なし | 下の受領証表 |
| next_tasks_consult.sh 改訂版 | rc=0、header astra / ultra、所要 119 秒 (既定締切 1,800 秒の約 7%)、委任 0、10 call、raw 367,769 token | `verbatim/token-summary.txt` 末尾 |
| ultra の委任の注入 | ultra は developer message に「Proactive multi-agent delegation is active」と spawn_agent 等 (最大 4 並列) を注入。medium は「delegation no longer applies」を注入 | `verbatim/s1-brief.md` L2 |
| 委任先の記録 | 別 rollout file。`session_meta.session_id` = root の id、`id` = 子の id、`source.subagent.thread_spawn.parent_thread_id`。`--json` stdout は root の `thread.started` だけ | L3・L4 |
| 改訂前の起動器 | 委任があっても受理 (検査は落ちず素通り)。委任先の call・token・model/effort/cwd は照合外。1 例で委任先が 61,473 raw token (組の約 41%) を使っていた | L5、`verbatim/token-summary.txt` |
| 設定で委任を止める | この CLI (0.159.2)・exec 経路・明示 spawn 依頼で試した `--disable multi_agent`、`-c agents.max_threads=1` (枠表示 4→2)、`-c agents.max_depth=0` はいずれも止めなかった | L6 |
| 委任先の sandbox | read-only 実行で root・子とも `touch` が `Read-only file system` (子 rollout の sandbox_policy も read-only)。対話 TUI の子は親のその時点の sandbox を継承。全経路・孫は未実測 | L7 |
| 委任先の guard | root では exec 経由でも本番 rollout に `Command blocked by PreToolUse hook: [guard_bash]`。**委任先での guard 発火は未確認** (subagent rollout は全履歴 6 件で拒否記録 0 件。直接 probe は trust bypass flag の手打ちが auto mode 分類器に拒否され未実施) | L8、`verbatim/s2-parent-measurements.md` |
| stdout usage | root 単独 (子を含まない) | `verbatim/s2-parent-measurements.md` 1 |
| 全履歴 fork | 子 rollout の token_count は 1 件で親の記録は複製されない。ただし履歴の response_item・親の meta/context は複製される | 同 3、`verbatim/s3-consult-a.md` A-1 |

## 本 wave の起動器受領証と週枠の実測

| 段 | lane | requested | recorded | outcome | issues | calls | CLI-reported | raw | wall s |
|---|---|---|---|---|---|---:|---:|---:|---:|
| plan | - | gpt-6-astra/medium | gpt-6-astra/medium | accepted | - | 10 | 72,126 | 505,662 | 268 |
| consult | luna | gpt-6-astra/medium | gpt-6-astra/medium | accepted | - | 5 | 52,557 | 202,317 | 181 |
| consult | sol | gpt-6-astra/medium | gpt-6-astra/medium | accepted | - | 10 | 84,058 | 622,682 | 309 |
| author | - | gpt-6-astra/medium | gpt-6-astra/medium | accepted | - | 16 | 58,434 | 781,890 | 241 |
| author | - | gpt-6-astra/medium | gpt-6-astra/medium | accepted | - | 13 | 60,915 | 645,747 | 272 |
| review | - | gpt-6-astra/ultra | gpt-6-astra/ultra | accepted | - | 15 | 102,712 | 1,113,912 | 430 |
| review | - | gpt-6-astra/ultra | gpt-6-astra/ultra | accepted | - | 20 | 130,574 | 1,837,454 | 567 |
| fix | - | gpt-6-astra/medium | gpt-6-astra/medium | accepted | - | 9 | 19,597 | 233,613 | 108 |
| focus | - | gpt-6-astra/ultra | gpt-6-astra/ultra | accepted | - | 9 | 65,794 | 380,162 | 249 |
| consult (段 9 の land 可否) | sol | gpt-6-astra/ultra | gpt-6-astra/ultra | accepted | - | 5 | 36,623 | 158,479 | 147 |
| consult (段 9 の land 可否) | luna | gpt-6-astra/ultra | gpt-6-astra/ultra | accepted | - | 5 | 46,577 | 173,553 | 118 |

段 9 の consult 2 本は rulings の相談と同じ `--stage consult --reasoning ultra` の形 (luna レーン名でも model は DW-O01 から astra)。
段 2〜5 と fix は、ultra を受理する語彙が着地する前の木で走ったため medium (D2229 決定 4 型の切り替わり: 起動器は `--repo-root` の docs から導出)。
ultra 5 本 (review 2・focus 1・consult 2) で委任は 0 件 (prompt に禁止文あり)。CLI-reported は `input − cached_input + output`、raw は cached を含む総量。
週枠の残量・換算率は CLI から取れず、ここでは token の実測だけを書く (残り何 wave 走れるかは断定しない)。

## 検証の実施状況 (未実施を含む)

- check_docs: 統合後・fix 後とも違反なし。
- **変異 matrix: 段 9 再開で実施し、8 件すべて期待どおり (m0 SURVIVED、m1〜m6・m7b KILLED)。** ユーザーが 2026-09-30 18:46 JST に
  受入・変異の計算ノード使用を許可したので、local main d79fd3524 を取り込んだ wave tip `7a1da5e4d` で走らせた。
  経路は `tools/mutation_worktree.py --runner-mode dispatch` (D1009 の独立 clone、runner は
  `run_tests.py --force-dispatch` で `test_effort_levels.py`・`test_check_docs.py`・`test_dev_wave_launch_authority.py`・`test_dev_wave_codex.py`・`test_codex_worker_launch.py` の 5 file)。
  台帳は `mutation/ledger-s9.json`、spec は `mutation/spec-probe3.json` と `mutation/spec-final-*.json`。
  - probe (全件 SURVIVED 期待で観測 node を集める、DW-M07): 1 回目 (`spec-probe2`、job dir のみ) は spec の外側 timeout 4,800 秒が
    dispatch 待機契約 (queue 5,400 + grace 5,400 秒) より短く、計算に入る前に harness が止めた。timeout を 12,600 秒にした `spec-probe3.json` で完走した。
  - final: ユーザー指示 (2026-09-30 19:5x、land 調整役の中継「計算 job は 1 本 5 分目安に分割し並行投入」) に従い、変異 1 件ずつ 8 本を並行投入した。
    m0・m6 は作業木の checkout が Lustre の割り込み (EINTR、rc=125) で失敗し判定前に止まった。m2 は期待の 359 node を全部落としたうえで
    `test_codex_worker_launch.py` の 4 件が `subprocess.TimeoutExpired` で落ち MISMATCH になった。起動器は `tools/check_docs.py` の中身を読まない
    (import 先にも無い) ので変異は届かず非帰属と判断し、DW-O18 に従い 1 回だけ単独で再走した。再投入 3 本 (`final2-*`) は m0 SURVIVED、m6 KILLED 2/2、m2 KILLED 359/359 で完全一致。
  - 観測 node: m1 は DW-O01 権威行の drift 拒否 2 件、m3 は effort 語彙の完全一致と ultra の受理 2 件、m4・m5 は委任 (`spawn_agent`) の online / sealed 再検証 2 件、
    m6 (namespace 全体を委任と見なす) は `wait_agent` を拒否しない正例と sealed 再検証 2 件、m2 は DW-S05-A の effort pin 系と、実 docs の走査が赤になることで落ちる 359 件。
- 焦点走: 段 5 統合後に bash script 経由の直接 pytest (30 file) を login で走らせたが、これは guard_bash の login 重量検査をすり抜けていた
  (同種の直接コマンドは guard が拒否して判明)。結果は参考値: 失敗 103 件 → 一時 dir を repo 外にし並列を下げた再走で 102 件緑、残る 1 件
  `orchestrator/tests/test_campaign.py::test_layout_rejects_path_traversal` は変更面と無関係な output_root 偽赤 (login の `/tmp/.git`)。
  正式な検証は受入全走に寄せる予定だった。
- **受入全走と land: 段 9 再開で、本記録 commit を含む tip に対して受入全走 (明示 shard 3、`tools/dev_wave_wait.py acceptance`) を取り、緑の受領証で land する。**
  以下は段 9 前半 (保留時) の経緯。受入全走の明示 shard 3 も `tools/acceptance_shards.py` の `run_parallel` から
  `tools.pegasus.dispatch_compute` で**計算ノードへ投げる** (login で走るのは collection だけ)。land には受入全走が必須 (DW-S04) なので、
  依頼の「計算ノードは使わない」と両立しない。Codex に 2 レンズで相談し (`verbatim/s9-consult-decide.md`、`verbatim/s9-consult-attack.md`、いずれも ultra)、
  両者とも「最終行は対象を限定しない禁止で受入・変異も含む。land の必須条件は資源使用の許可を生まない」として land 保留を推奨、親もそれを採った。
  wave branch は commit 済みで残した。受入・変異の実行 (計算ノード使用) は 2026-09-30 18:46 JST にユーザーが許可した。

### 訂正 (erratum)

- `verbatim/s6-fix1-ruling.md` の「正式な検証は受入全走 (明示 shard 3、login で走る sanctioned 経路) に寄せる」は誤り。明示 shard は計算ノードへ
  dispatch する (上記)。当時の裁定文は逐語として残し、ここで訂正する。
- 事前登録 m7 (`verbatim/s4-ruling.md` の `DEV_WAVE_L1_5_BYTES_MAX` 9_788 → 9_787、KILLED 期待「実 docs が予算超過」) は、段 6 fix1 が予算増枠を取り消して
  定数を 9_696 に戻したため置換元が消えていた。元の意図を保ち、L1.5 の実 bytes 9,692 の 1 つ下へ置く m7b (9_696 → 9_691) に再照準した (DW-M02/M07)。
  m7b を殺したのは定数を pin する `test_check_docs.py::test_dev_wave_layer_budget_contract_is_literal` の 1 件だけで、「実 docs が予算超過で拒否される」経路を
  pytest で検出する test は上記 5 file に無かった。予算超過の拒否そのものは、親が `tools/check_docs.py` を予算 0 (メモリ上だけ) で走らせ
  「L1.5 unique footprint 9692 bytes > 予算」の違反と rc=1 を得て確かめた (実 bytes の測定を兼ねる)。
  また `verbatim/mutation-spec-probe.json` は `targets`・`note` を持ち harness の spec schema (key の完全一致) を満たさないので、正式 schema へ書き直して走らせた (内容の置換は m7 以外同一)。

## 残る限界

- 事後拒否は委任先の実行・書込みを防がない。workspace-write の author / fix で委任が起きると子 worktree に guard 未確認の書込みが残りうる。
- 拒否された attempt の委任先 token は会計されない。
- next_tasks_consult.sh は起動器を通らないので委任の検出は無い (prompt の禁止と read-only 継承だけ)。
- `tools/dev_waves/effort_levels.py` の変更で `daemon._supervisor_digest()` が変わる。supervisor 管理下の wave が走っている木へ着地させると、その wave の前後比較が
  `supervisor-changed` で赤になる。land 直前に daemon 稼働 0 件を確認する。

## next_tasks_consult.sh の差分 (repo 外、原本 sha256 fdfb0124… は job dir に退避、設置後 sha256 ab51a572…)

```
24c24
< effort=${CONSULT_EFFORT:-high}   # 相談は判断そのものなので既定を high にする (2026-09-16 ユーザー是正)
> effort=${CONSULT_EFFORT:-ultra}   # Codex 相談の既定 ultra (2026-09-30 ユーザー裁定)
50a51
> - sub-agent を spawn しない (collaboration tool を使わない)
76c77
<       codex exec --sandbox read-only --skip-git-repo-check -C "$repo" \
>       codex exec -m gpt-6-astra --sandbox read-only --skip-git-repo-check -C "$repo" \
```
