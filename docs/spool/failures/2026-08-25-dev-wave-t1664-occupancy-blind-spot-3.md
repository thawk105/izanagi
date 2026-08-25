---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1664-occupancy-blind-spot
seq: 3
---

## 新規

### {{F:occupancy-payload-conditional-key}}. producer が条件付きで落とす key を consumer が必須にしており、最も綺麗な入力だけが拒否された [恒真ゲート] [テスト代表性]

- 事象: `tools/check_worktree_occupancy.py` の `_report_payload` は
  `same_uid_cwd_unreachable` が空のとき payload から key ごと落としていた。一方
  `tools/dev_wave_cleanup.py` の `_assert_unoccupied` は同 key を必須 key に含めていた。
  その結果、**占有ゼロ・issue ゼロ・blind spot ゼロという最も綺麗な走査だけが**
  「occupancy payload lacks required fields」で拒否され、rc22 になっていた。
  blind spot が空の環境では worktree 撤去が構造的に一度も成立しない。
- 根本原因: producer 側の「診断は在るときだけ出す」という設計と、consumer 側の
  「schema の全 key を要求する」という設計が、**空集合の扱いで衝突**していた。
  両者を突き合わせる統合テストが無く、producer 側テストと consumer 側テストが
  それぞれ自前の fixture で緑になっていた (consumer 側 fixture は当該 key を常にハードコードしていた)。
  さらに実行環境 (Pegasus login node) では blind spot が常に 3 件で非空だったため、
  key が必ず出ており欠陥が隠れていた。
- 恒久対応: `_report_payload` が空 list でも同 key を常時出力する。
  実 checker の payload を `_assert_unoccupied` まで空の fake proc root で通す統合 node
  `test_assert_unoccupied_accepts_real_empty_proc_scan_payload` と、
  consumer の必須 key 契約を拒否理由まで逐語で pin する
  `test_assert_unoccupied_requires_same_uid_cwd_unreachable_field` を新設した。
- 再発検知: 変異走行で確認済み。key を落とす変異は 12 node を殺し、そこには既存の
  end-to-end 撤去 node (`test_landed_attached_worktree_is_removed` の 2 parameter、
  `test_reentry_states_run_only_remaining_cleanup` の 2 parameter、
  `test_forward_merged_landing_tip_is_used_for_cleanup` の 2 parameter、
  `test_real_occupancy_scan_rejects_live_process_cwd`) が含まれる。
  これらが赤になる事実が、欠陥が実在し環境で隠れていたことの裏づけである。

### {{F:tautological-guarantee-in-checker-docstring}}. 検査の説明文が実装より強い保証を謳い、その差が 2 度の設計失敗を跨いで残っていた [恒真ゲート]

- 事象: `tools/check_worktree_occupancy.py` の module docstring と argparse description は
  「同じ uid または uid 判定不能の観測不能 process は pid と comm を残る盲点として列挙するため、
  **worker でありうる process が一つでもあれば削除してはならない**」と書いていた。
  しかし実装の `status` 判定は blind list を一切見ず、consumer も非空を拒否しない。
  謳うだけで発火しない保証であり、読み手は「この検査は blind spot を守っている」と誤読する。
- 根本原因: F490 で述語を 2 度撤回したとき、**述語 (コード) だけを戻して説明文を戻さなかった**。
  説明文は「守る」と書いたまま、コードは「数えるだけ」に戻っていた。
  撤回の閉包に公開説明層が入っていなかった。
- 恒久対応: 説明を実装へ合わせ、「非阻害の診断として列挙するだけであり、非空でも status と rc は
  変わらず rc0 になりうる」と明記した。docstring と `--help` の両方を同一 commit で直した。
  今後この blind spot を撤去拒否へ倒すか否かの裁定は {{D:occupancy-blind-spot-undecidable}} に従う。
- 再発検知: 述語を撤回・変更する裁定では、同じ commit で module docstring と CLI の
  description を照合する。段 6 の契約レンズがこの型を独立に検出した実績がある。

## 再発

### F31

- **再発: 2026-08-25** — T-1664 の台帳本文は「再挑戦は lease 前提の設計から始める」と
  設計方向を明記していたが、親は段 1 brief で lease を scope 外に置いた。本文は開いていたので
  F31 の「本文へ当たらなかった」とは機構が違うが、**本文にある制約を下流の scope 決定へ
  継承しなかった**点で閉包は同じである。段 3 の敵対 2 レンズが独立に lease / 特権 observer /
  cgroup v2 へ収束して初めて露見し、段 4 で scope を裁定し直すことになった。
  `DW-S01` の「裁定要約が指す decision 本文と archive worklog を開き、食い違いは本文を優先する」は
  既にこの義務を課しており、新しい節は要らない。適用を怠った側の再発である。

### F492

- **再発: 2026-08-25** — 本 wave の codex 子 6 本のうち 1 本 (段 3 の consult sol) が
  `outcome=not_accepted` / `evidence_status=invalid` で成果物 md を書かなかった。
  親が検算すると `codex_exit_code=0`、`termination_verified=True`、`validator_rc=0`、
  `metering_status=complete`、`limit_trigger=None`、output hash 一致、events jsonl 全行妥当で、
  内容の欠陥ではなかった。F492 の暫定運用どおり attempt 出力を回収し
  `check_codex_output.py` rc=0 で採用した。本 wave の発生率は 1/6。
