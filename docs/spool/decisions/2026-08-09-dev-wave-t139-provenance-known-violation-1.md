---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-09
wave: dev-wave-t139-provenance-known-violation
seq: 1
---

## {{D:land-ff-only-provenance-gate}}. land の ff-only だけに全史 provenance 監査を課し、no-op と recovery は監査しない

**決定:** `tools/dev_wave_land.py` は、**これから ff-only を行う land** =
`locked_main != tested_tip` のときだけ、全史 provenance 監査を自ら走らせて rc を確認する。
赤なら `RC_PROVENANCE = 29` で拒否し、main を 1 bit も変えない。逃がし道 (CLI flag、環境変数、
「赤でも警告だけ」) は作らない。監査は **lock を解放してから**実行し、lock を取り直して
全検査をやり直す。receipt は `tip_sha` / `checker_blob_sha` / `executed_bytes_sha` /
`returncode` を束縛し、lock 内で再照合する。timeout は 480 秒。

`already-landed` の no-op と active fold transaction の recovery は**監査を起動しない**。

**D239 の「land の権威は変えない。lock・ff-only・監査は不変」を、本 D が supersede する。**
D239 の他の決定 (受入窓の lease による直列化、通知の advisory 性) は変わらない。
D239 が「land へ新しい直列化機構を足す理由はない」と述べたのは lease の設計判断であり、
本 D が足すのは直列化機構ではなく受理条件である。

**理由:**
- 検査 rc をパイプで喪失する型 (F37) が同日・3 wave・3 親で独立に再発し、
  実害は 22 commit / 1 commit / 検出は偶然だった。`DW-O17` は既に単独 rc を要求しており、
  **文章による注意喚起では防げないことが実測で確定した。**
- 効かせる場所を land の関門にするのはユーザー裁定である。3 例とも「気づかず land した」ことで
  被害が出たため、ここで止めれば親の習慣に依存しない。
- **監査を lock の外へ出す**のは、checker が login 完結せず Pegasus 計算ノードへ dispatch
  しうるためである。dispatch 既定は queue 900 秒 + walltime 2400 秒 + grace 300 秒で、
  lock 内に置くと global な land lock を最大で数十分保持する。lock は `LOCK_EX|LOCK_NB` なので、
  その間の並行 wave は `lock-busy` で弾かれ続ける。同時に、lock を先に取ることで
  「lock 保持中は 2 秒未満で `lock-busy` を返す」既存契約と D102 の順序を保つ。
- **監査した木と land する木の同一性**は commit SHA と checker blob/実行 bytes の SHA で束縛する。
  同じ commit SHA は同じ superproject tree を表すため、lock 内で SHA が変わっていないことを
  確かめれば足りる。監査前後で main/wave の HEAD・collision path 集合・control-plane identity も
  照合し、checker の副作用で受理集合が広がる経路を塞ぐ。
- **no-op と recovery を除外する**のは、どちらも `locked_main == tested_tip` = wave の commit が
  既に main に入っている状態でしか到達せず、**新しい commit を admit しない**ためである。
  recovery は fold commit を作るが、それは既に admit 済みの commit に対する記帳である。
  除外しないと `already-landed` の idempotency が壊れ、途中状態の canonical 3 台帳が固着する。
- 実行体を wave tip 側の checker にするのは、self-weakening を許容するからではなく
  **main 側では機能しないから**である。checker は repo root を cwd でなく
  `Path(__file__).resolve().parent.parent` から決めるため、ff-only 前の main 側実行体は
  main の履歴しか監査せず tip を一切見ない。既知違反台帳も実行体のソース内定数なので、
  main 側実行体は既知違反を新規登録する wave を恒久 deadlock させる。

**却下した選択肢:**
- **監査を lock 内に置く** — 敵対検証 2 本が独立に blocker とした。global lock を dispatch の
  queue 待ちごと保持し、並行 wave を連鎖的に `lock-busy` へ落とす。
- **`--range` で軽くする** — `DW-O17` の「range は補助で、correction を含むときは full 監査だけが
  権威」と衝突する。
- **timeout 3900 秒** — 受入 lease の TTL 2400 秒と親の前景 600 秒上限の双方を破る。
  滞留時は fail-fast で拒否し再試行に回す方が、lease を失効させるより害が小さい。
- **hook / wrapper script による強制** — wrapper は使わなければ迂回でき、hook は Claude の
  Bash 面しか見ない。ユーザー裁定が land の関門を指定した。
- **recovery も含めて一律に監査する** — 台帳が before/after 混在で固着する。
  admit をしない経路を止めても違反は 1 件も防げない。
- **逃がし道を残す** — 規律 2 が名指しする reward hack の形であり、D95 と同型。

**閉じない残余 (別 scope):** tip 側の land helper と checker が可変であるという協調境界そのもの。
`tools/dev_wave_land.py` は自らを「悪意ある writer に対する sandbox ではない」と宣言しており、
親は既に tip 側 helper を実行している。本 D は**この境界を悪化させないが解消もしない**。
land 経路を通らない main 更新も覆わない。immutable trust root の設計はユーザー裁定へ返した。
