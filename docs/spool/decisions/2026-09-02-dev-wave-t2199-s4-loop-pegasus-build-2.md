---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-02
wave: dev-wave-t2199-s4-loop-pegasus-build
seq: 2
---

## {{D:s4-loop-stays-on-pegasus}}. 段 4 loop の実行場所は Pegasus とし、cygnus へ退避しない

**決定:** 段 4 coder 自律 loop を実走させる場所は Pegasus 計算ノードとする。`linux-baremetal`
(cygnus) へ退避する案は採らない。到達させる手段は、段 4 loop へ site-aware な環境契約配線を
移植することであり、`p3_s4_loop_trigger_gating.py` に既にある形を写す。

**理由:**
- D59 は正式計測の正本 env-tag を `linux-baremetal` に据え置いたが、Pegasus の env 契約は
  その後 registry へ登録され、g1 が current activation になっている。実行場所として Pegasus を
  選ぶことは D59 の据置と衝突しない — 混ぜないことだけが不変条件である。
- ユーザーの確定方針は「cygnus は使えるが使わない。新規 evidence は Pegasus」である
  (2026-08-05)。これを覆すには実測の根拠が要る。
- 移植先の形は新設ではない。`p3_s4_loop_trigger_gating.py` の `_admit_env_contract()` が
  site を契約へ写像し (未知 site は fail-closed)、`_campaign_cfg_for_site()` が identity へ束縛し、
  `authorize(contract.env_tag)` を渡す。同型の兄弟実装が既に review を通っている。

**却下した選択肢:**
- **cygnus で走らせる** — 起草子が「直ちに安い」として推奨した。費用比較の cygnus 側が
  過去の成功 4 iteration、Pegasus 側が目的の異なる 6 投入であり、沈んだ費用を将来費用として
  読んでいる。起草子自身が現在の cygnus 到達性を未確認と書いた。**到達不能とは判定していない。**
- **`p3_s4_loop.py` の env_tag 固定のまま Pegasus で走らせる** — `execution_guard.py` の
  認可検査が build より前に拒否する。この拒否は Pegasus の値が `linux-baremetal` の系列へ
  混入するのを防ぐためのものであり、迂回しない。
- **job script 側の PATH wrapper で環境差を吸収する** — 受理集合の変更になる
  ({{F:path-wrapper-changes-acceptance-set}})。
