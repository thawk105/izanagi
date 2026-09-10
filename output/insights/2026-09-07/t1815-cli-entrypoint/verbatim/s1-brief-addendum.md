# 段 1 brief 追補 — 実プロセス検査の時間予算 (親が段 2 投入後に実測)

段 2 のプラン子を投入した後、親が login node で CLI の実所要を測った。この数字は
`brief.md` の段階では未測定だったので、追補として段 3 以降の全子へ渡す。

## 実測 (2026-09-07 19:15 JST, `/work/1/SFC/tanab/izanagi`, main cf4273f56)

`python3 -m orchestrator.campaign.s8c_gate_report` (real repo HEAD, rc=1) を 3 連走:

- 39.17 s / 114.16 s / 118.74 s
- 同時刻の `uptime` load average = 75.75 (1 分), 82.08 (5 分)
- 母集合: 同一 login node、並行 dev-wave 多数 (worktree add 7 本を含む) の混雑 regime。
  空き regime での所要は未測定であり、この分布をそのまま空き regime へ一般化してはならない。

## これが効く理由

- `activation_report_at` は指定 commit の `orchestrator/campaign/**` の blob を列挙・hash し、
  評価器が AST 到達可能性解析を回すため、**real repo を対象にすると本質的に重い**。
- 一方、`_activation_report_at` は core / evaluator / projection の 3 module について
  「commit の blob」と「live file の bytes」の一致を要求する
  (`s8c_preregistration.py:1888-1907`, `1769-1801`, `1804-1838`)。合わない場合は
  `*-absent-at-commit` / `*-blob-mismatch` で早期に倒れ、**評価器まで到達しない**。
  したがって「小さな合成 repo を作って安く同じ欠陥を踏ませる」ことはできない。
- 既存 suite は `test_s8c_gate_report.py::test_real_repo_head_is_only_compared_with_its_source_report`
  で real repo 評価を既に 2 回払っている。

## 段 3 以降で必ず攻撃・裁定すること

- **(P5)** 実プロセス検査を「real repo HEAD に対する full 評価の subprocess 起動」で作ると、
  混雑 regime で 1 case あたり 40〜120 秒かかる。4 case なら最悪 8 分で、
  auto-memory `test-time-regression-rule` の「suite 全体 5 分」を単独で超える。
  安く同じ欠陥を検出する設計があるなら、それを採る。無いなら case 数を最小化し、
  その根拠と実測を裁定へ書く。
- 安い候補として親が思いついたもの (採否は段 3・段 4 が決める。親は推していない):
  1. `s8c_gate_report.py` のファイルパス直接起動は、既存 `-m` 検査と同じく
     `--definitely-invalid` を渡せば **import 段で落ちるか rc=2 で即返るか**が分かれるので、
     full 評価を走らせずに ImportError の有無を判定できる (既存先例
     `test_s8c_gate_report.py:434-461`)。
  2. `s8c_preregistration.py` 側は、CLI を実プロセスで起動したうえで
     `sys.modules["orchestrator.campaign.s8c_preregistration"] is sys.modules["__main__"]`
     に相当する**構造**を直接観測すれば、full 評価を待たずに二重実体化の有無を判定できる。
     ただしこれは機構の pin であって受理集合の pin ではない。**恒真になっていないか**、
     **実装を直さずに通せてしまわないか**を必ず検査せよ。
  3. full 評価の end-to-end 等価検査は残すが 1 case に絞る。
- どの案を採るにせよ、**現行 HEAD で実際に落ちること**を親が実測して確認する。
