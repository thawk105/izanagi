---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-t1027-acceptance-reds-checker
seq: 3
---

## 新規

### {{F:checker-replays-child-pytest-output-into-its-own-log}}. 帰属 checker が子の pytest 出力を親ストリームへ再掲し、機械解析される log を汚した [計測汚染] [テスト代表性]

- 事象: 単独 rerun の子から得た captured stdout / stderr を親の `sys.stdout` /
  `sys.stderr` へ書き戻していた。この checker のテストは
  `=== short test summary info ===` を含む偽 pytest log を注入 runner から返すため、
  pytest が失敗 test の captured stdout を報告に出すと、その走行の出力に
  **実在しない file の FAILED 行**と **2 つ目の summary block** が現れた。
  変異 matrix 1 巡目の 10 変異すべてで、失敗 node の抽出結果に実在しない
  `orchestrator/tests/test_example.py::...` が混入した。
- 根本原因: 正しさ裏取り (rerun の帰結を rc だけで判断しない) のために子出力を
  capture するようにした際、「従来は表示されていた」という誤前提から replay を足した。
  実際には変更前は capture して捨てており、表示はされていなかった。
- なぜ重いか: 受入 log を機械解析するのはこの checker 自身であり、
  summary block が 2 つあれば log を拒否する。**受入が赤のときにこそ壊れる**経路だった。
- 恒久対応: 子の pytest 出力を親の stdout / stderr へ出さない
  ({{D:unverifiable-input-must-not-yield-non-attributable}} の tool 実装)。
  `test_injected_rerun_output_is_not_replayed_to_checker_streams` が、
  偽 log を注入しても capsys の stdout / stderr に summary block と FAILED 行が
  現れないことを固定する。
- 再発検知: 上記 node に加え、変異 matrix の失敗 node 抽出そのものが検知器として働く
  (抽出結果に repo 非実在の nodeid が現れたら汚染である)。

### {{F:absolute-clean-gate-vs-self-inflicted-dispatch-residue}}. 自分が走らせた子の残骸で自分の clean gate を落とす [防壁の射程誤認]

- 事象: probe worktree の指紋を「ignored file も含めて完全に空」と要求する gate があるが、
  checker 自身が同じ worktree の中で pytest を dispatch する。計算ノードは共有
  ファイルシステム上の同じ path へ書くため `__pycache__` と `output/pegasus-dispatch/`
  が残り、赤を含む実 log では必ず rc=2 になった。
- 根本原因: gate を設計した時点では probe 内で子を走らせる経路が dispatch 化されておらず、
  「空であること」が達成可能だという前提が後から崩れた。
  前段の欠陥 (collect の打ち切り) が先に停止していたため、露出が遅れた。
- 恒久対応: 部分的。dispatch 成果物側は、検証済み nonce と fallback receipt を消したあと
  exact root が**空のときだけ** `rmdir` し、異物があれば保持して fail-closed にする
  (再帰削除・glob をしない)。**`__pycache__` 側は未対応** — 安全な解は
  producer の env allowlist へ `PYTHONDONTWRITEBYTECODE` を足すことだが、
  producer は本 wave の編集面の外でユーザー裁定へ返した。
- 再発検知: 親の実データ実走 (gate を新設・改修する wave の完了条件)。
  静的レビュー 2 本はこの型の欠陥を 1 件も出せず、実走が 5 件連続で出した。
