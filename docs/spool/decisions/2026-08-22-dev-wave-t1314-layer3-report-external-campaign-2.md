---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-22
wave: dev-wave-t1314-layer3-report-external-campaign
seq: 2
---

## {{D:layer3-output-root-cli}}. 層3材料レポートCLIの`--output-root`は既存APIの値をそのまま公開し、qualification-ancestry境界だけ実repo rootを優先する

**決定:** `orchestrator/campaign/layer3_report.py` の `main()` に `--output-root PATH`
(`type=Path` 相当、`default=None`) を追加し、`build_report()`/`render()` が既に受理している
`output_root` パラメータへそのまま配線する。CLI 省略時の挙動 (`output_root=None` →
`_DEFAULT_OUTPUT_ROOT`) は byte-for-byte 不変。`_resolve_campaign_dir()`・
`_reject_qualification_ancestry()` 本体・schema・certifying 経路
(`build_accepted_report`/`render_accepted`) は変更しない。

qualification-ancestry walk の境界だけは新設の `_qualification_ancestry_bound()` が計算する。
campaign が実 repo (`_DEFAULT_OUTPUT_ROOT.parent`) 配下にあるときは、caller が渡した
`output_root` がどれほど狭くても常に実 repo root まで歩く。campaign が真に実 repo の外にある
ときだけ、既存どおり `output_root` 由来の境界を使う。ただしその境界 (`output_root` の resolve
結果) が campaign 自身または campaign 配下にある場合は `Layer3ReportError` で拒否する
(campaign を自身の境界として使うことに正当な用途がないため)。

**理由:**
- D485 (`docs/decisions.md`) は `generated_from_head` の repo外 fallback を導入した際、
  「CLI も同じ穴を持つと明記済み」として先送りした。本 D はその穴を塞ぐ。
- `output_root` は「配置境界」と「calibration 参照先」を1引数に意図的に同居させる既存 API
  設計をそのまま踏襲する。分離は本 wave の scope 外 (D641 の official writer 用外部性検証も
  読み取り専用レポート生成には目的が異なるため移植しない)。
- caller が任意の `output_root` を選べるようになったことで、実 repo 配下の campaign に対して
  「実 repo root より狭い repo_root を作る output_root」を渡すと、祖先にある
  `qualification-marker.json` を検査せずに qualification 済み campaign を正式な Layer3
  材料として受理してしまう欠陥が新たに到達可能になった (段3 sol所見2)。3ケース
  (省略時/実repo配下で狭いoutput_root/真に外部) を手動trace + 実測 (mutation MUT-4/MUT-5) で
  検証し、省略時は既存と完全に同じ値になることを確認した。
- 真に外部の campaign でも、`output_root` が campaign 自身・配下を指すケースは
  ancestry walk をほぼ無効化する (段6 reviewA所見1)。output_root は campaign の外側にある
  という既存の暗黙の前提を明示的な guard として強制した。Windows形式pathの拒否は
  POSIX限定環境 (Pegasus) のため scope外とした (盛らない、規律5)。

**却下した選択肢:**
- 環境変数 (`IZANAGI_LAYER3_OUTPUT_ROOT`) を省略時 fallback にする — 省略時の挙動が
  実行環境依存になり CLI と Python API が分岐する。D641 の official root 環境変数と混同を招く。
- campaign 境界 root と calibration 参照 root を独立指定できるよう `main()`/`render()`/
  `build_report()` へ引数を追加する — 変更面が `render_accepted()` 等の certifying 呼び出しへ
  波及する危険があり、既存 `output_root` の互換性 fallback 規則も増える。分離を必要とする
  具体的証拠が無い。
- qualification-ancestry walk を repo_root の制約なく filesystem root まで無条件に歩く —
  共有ファイルシステム (Pegasus) の祖先ディレクトリに無関係な `qualification-marker.json` が
  存在した場合、既定 (`output_root` 省略) の経路まで巻き込んで誤検出する退行リスクがある。
