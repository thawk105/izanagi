実装完了です。commit は作成せず、所有対象2ファイルだけを変更しました。親所有の未追跡 wave artifacts には触れていません。

変更概要:

- [check_ai_provenance.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py)
  - `6b64d21` 専用の immutable singleton を追加。
  - raw物理1行と隔離canonical valueをexact検査。
  - selected set内の一意性、membership、strict descendant、target実欠落、correction通常greenを要求。
  - targetのmissing findingだけを抑止し、他findingを保持。
  - `forward-corrected=1 target=... correction=...` を出力。
  - correction入りmessage-fileを限定preflightとして検査・表示。
  - `merge-base` の予期しないrcを実行不能rc=2へ変更。
- [test_check_ai_provenance.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py)
  - production literal、実targetの2-parent topologyをpin。
  - `T^!`、`C^!`、`T^1..C`、sibling、duplicate、順序不変性を追加。
  - continuation、body-only/body+valid、全field drift、CAB・別commit・correction自身のfinding保存を追加。
  - message-file preflight、通常message-file、unrelated history、parser/ancestry failureを追加。

実走結果:

- provenance test全体: `101 passed in 3.01s`
- production literal meta-test単独: `1 passed`
- `py_compile`: rc=0
- 指定2ファイルの `git diff --check`: rc=0
- `check_codex_agents.py`: rc=0
- `check_docs.py`: 違反なし
- 標準checker: 期待どおり `533件中1違反`
  - 対象: `6b64d21753d2...`
  - 理由: `AI-Agent trailer がない`

現在の受理・拒否挙動:

- 受理: targetとexact correctionが同じselected setにあり、correctionがstrict descendant、targetが実際にmissing、correction自身が通常greenの場合のみ。
- 拒否: target-only、correction-only、sibling、duplicate、field drift、continuation/body偽装、targetが既にvalid、correction自身に通常違反がある場合。
- correction成立後もtarget/CAB、別commit、merge-side、correction commit自身のfindingは残ります。
- 通常message-fileの既存受理集合と成功出力は不変です。
- correction入りmessage-fileはpreflight成功を明示し、commit後のhistory監査を必須と表示します。

所有外への波及可能性は、stdoutを完全一致で読むcallerがforward-corrected行を認識する必要がある点と、親が作るcorrection commit messageをexact payload・通常greenにする必要がある点です。共有fixture、設定、docs、consumerコードは変更していません。

## 総括

plan v2のコード・テスト実装は完了しました。未解決の赤は、correction commit前である現HEADの対象1件のみで、意図した停止状態です。