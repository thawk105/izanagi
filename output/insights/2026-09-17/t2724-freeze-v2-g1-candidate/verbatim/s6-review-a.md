## 攻撃面 1〜8 の所見

**1. RA-1 — 実際の受理集合には、旧実装の admission 制約も含める必要がある。**

- **対象:** `s5-author.md`「受理集合の前後」、`s8b_holdout_freeze.py:1480`、`s8b_holdout_admission.py:851`。
- **主張:** 「前＝固定 protocol と一致する result」は必要条件の説明であり、producer 全体の受理集合としては不十分。
- **根拠:** 旧実装も後段 `_authority` で index authority を解決し、渡された protocol 文書との一致を要求する。
- **具体入力・前後:** A を固定 anchor、V を同一契約の正規版付き entry、R(P) を P に対応し他の全検査も満たす result とする。HEAD とファイルが安定している場合：

  | repo の状態 | 旧 producer | 新 producer |
  |---|---|---|
  | A のみ、現行契約に一致 | R(A) | R(A) |
  | A＋V、HEAD gitlink が V を選択、A≠V | 空集合 | R(V) |
  | A＋V、HEAD gitlink が A を選択 | R(A) | R(A) |
  | 複数候補で HEAD exact が一意でない | 空集合 | 空集合 |

  本番相当では R(A) は旧 admission で、R(V) は旧 hash 比較で拒否される。新たに通る具体入力は、新 fixture の `versioned_protocol=True` が構成する V 対応の result・manifest・admission 一式である。単独候補への fallback も既存 resolver の仕様どおりで、producer が別の候補選択を導入したわけではない。
- **是正案:** 報告を上表のように、早期 hash 検査と全段通過を区別して修正する。
- **重大度:** **should**。

未 commit の版付き entry、版付き bytes 改変、namespace の集合不一致は resolver が拒否する。producer の再読取りはその後の変更を検出できるが、同じ captured commit に対する `record.raw_bytes` と HEAD blob は既に同一なので、後続の二比較を独立した防壁とは数えられない。

なお V 選択時、anchor の worktree は strict validation のみで、HEAD bytes との一致は要求されない。例えば anchor の seed だけを有効値へ変更しても、V とその証拠が正しければ新経路はこの変更を理由に拒否しない。これは既存 resolver が committed anchor を lineage authority とする仕様に沿うが、「全 protocol の dirty を拒否」とは報告できない。

**2. RA-2 — 例外文言の互換変換は拒否能力よりテスト文言に結合している。**

- **対象:** `s8b_holdout_freeze.py:1396`、`test_s8b_holdout_freeze.py:1890`。
- **主張:** `reason.startswith(...)` は脆いが、fail-open 経路は作っていない。
- **根拠:** 分岐の成否によらず直後で `FreezeError` を送出する。
- **反例・入力:** campaign 側のエラー接頭辞だけを変更すると、同じ worktree 改変を拒否し続ける一方、互換文言を要求する test は赤になる。
- **是正案:** 変換を外して resolver の拒否文言に test を合わせる。安定した分類が必要なら、別途例外の reason code を使う。
- **重大度:** **nit**。

**3. 破れず —** `s8b_holdout_freeze.py:1404` の commit 比較は、HEAD が安定していれば成立するが、producer の capture 後、resolver の capture 前に同じ worktree の HEAD が動けば不一致になる。したがって恒真ではない。detached HEAD 自体は不一致を起こさず、別 worktree の独立した HEAD 移動も通常は影響しない。同じ root が参照する HEAD の移動だけが関係する。この比較は capture 間の競合を検出するもので、resolver 後まで HEAD を固定する保証ではない。

**4. 破れず —** `s8b_ratified_freeze.py:1035` の V1d は文書に記録された path を G/H/worktree で検査し、`:3606` の選択同一性検査も記録 path の generation blob を読むため、版付き path と整合する。`:2875` の `_SELECTOR_PROTOCOL_PATH` は selector journal の歴史的 protocol hash の検証用で、candidate の `floor_protocol.path` との同一性を要求していない。oracle・manifest・report 関連と campaign/tools の検索でも、今回の世代参照を固定 path に縛る消費者は見つからなかった。`s8c_result_judge.py:2045` も文書由来の path を使用する。既存 literal は、今回まとめて dynamic pointer 化する対象ではない。

**5. 破れず —** `s8b_holdout_freeze.py:2011` の追加は、現行の prefix 除外下では受理集合にも closure にも実効差を生まない。専用フィールドで記録する artifact を集合に明示するという裁定上の意図には沿う。独立した検査や新たな走査免除の効果としては数えない。

**6. 破れず —** `s8b_v2_freeze_fixture.py:779` で子 repo を commit し、`:787` でその HEAD を版付き文書へ記録、その後 `:912–913` の親 `git add -A`／commit が版付き file と embedded repo の gitlink を記録する。途中で子 HEAD を変更する処理はない。v5 分岐も `:867–868` で authority 利用前に commit するため、resolver の commit 済み要求と整合する。これは本文による静的確認であり、fixture 実走結果ではない。

**7. 破れず —** 指定 diff と現在の作業木の hunk 本文は3件とも一致した。走査除外、allowlist、admission、批准側、既存 test 期待値の変更はない。AST 確認では `FLOOR_PROTOCOL_REL` の代入が1件、`_run_git`・`_run_git_bytes`・`_run_git_z` 内の subprocess 起動が各1件、必須3呼出しも各1件で、台帳・述語の対象は維持されている。

**8. RA-3 — M3・M5 は現登録のままでは防壁の検証を完了できない。**

- **対象:** `s5-author.md`「変異 M0〜M5 の単一理由性」、`s8b_holdout_freeze.py:1412–1417`、`:1433`、`test_s8b_holdout_freeze.py:1810`。
- **主張:** author の未完了申告は正しい。現在の test による赤を、そのまま該当防壁の有効性の証拠にはできない。
- **根拠:** M3 は比較削除後も record bytes 比較や resolver が拒否する。M5 の既存 killer は提示されておらず、後段 admission にも freeze 検査がある。
- **反例・入力:** 固定 anchor の worktree seed 改変は、M3 適用後も別比較で拒否され、文言 match だけが赤になり得る。版付き改変は resolver が先に拒否する。
- **是正案:** 親で M3・M5 を再登録し、対象境界を分離する stub／spy 等を用いた検証と、実経路の拒否検証を区別して実走する。冗長と判断する比較については、その事実を記録し、独立防壁と数えない。
- **重大度:** **must-fix（検証完了条件。受理実装の欠陥指摘ではない）**。

所有範囲の裏取りでは、tracked 差分は申告どおり3ファイルのみで docs 差分もない。ただし「所有外 file 無変更」という無限定の表現は不可。author 自身が所有外 receipt の生成を申告しており、tracked diff だけではその副作用を否定できない。

## GO / NO-GO と条件

**静的な実装方針は GO。検証完了・統合判定は現時点で NO-GO。**

条件は以下のとおり。

- RA-1 の受理集合説明を訂正する。
- RA-3 の M3・M5 を再照準し、M0〜M5 の実測を記録する。
- 親が指定の焦点走と consumer 回帰確認を完了する。

今回、設計を超える候補選択や fail-open は確認しなかった。pytest・変異走は実行しておらず、テスト成功の判定はしていない。

## 総括

C-1 の修正は D460 の index authority と下流の文書参照に整合する。残る必須事項は変異検証の成立と実走確認である。受理集合の報告は、旧 admission により本番相当の集合が既に空だった点まで含めて訂正すべきである。