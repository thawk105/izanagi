結論は **NO-GO**。must-fix 4件です。指定資料はすべて読了し、編集・pytest・runner 実行はしていません。以下の動作確認は Git 2.34.1 の read-only probe です。

### A-1 — parsed trailer 出力を `splitlines()` すると偽 CAB を生成できる

- severity: **HIGH / must-fix**
- real/refuted: **real**
- file:line: [check_ai_provenance.py:110](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:110)、[check_ai_provenance.py:125](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:125)、[test_check_ai_provenance.py:106](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:106)
- `git interpret-trailers` は trailer 値中の bare CR (`0x0d`) を保持する。一方、Python の `splitlines()` は CR も行境界とみなす。
- 反例は本文側の raw CAB 1行と、最終 block の `X: value\rCo-Authored-By: phantom` + 有効な `AI-Agent: none`。Git 上の最終 block に CAB はないが、現実装は出力を偽の `Co-Authored-By` レコードへ分解し、`raw=1, parsed=1` として受理する。
- 放置時の受理集合: `--message-file` と policy 適用後の履歴で、分断 CAB message が不正に受理される。CR以外にも VT、FF、NEL、Unicode LS/PS が同型。
- 最小fix: Git の出力は LFだけで `split("\n")` し、予期しない非空・colonなしのLFレコードは fail-closed。bare CRおよび Unicode line-separator を trailer 値に埋めた負例を追加する。

### A-2 — cwd `/` は「repo 外」を保証しない

- severity: **HIGH / must-fix**
- real/refuted: **real**
- file:line: [check_ai_provenance.py:49](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:49)、[check_ai_provenance.py:79](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:79)、[test_check_ai_provenance.py:261](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:261)、[test_check_ai_provenance.py:304](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:304)
- system/global/env は除去されるが、`/.git` が存在すれば `/` の local config は読み込まれる。現在のホストでは `/` は repo ではなかったが、これは環境観測であって契約ではない。
- `trailer.foo.key=Co-Authored-By:` が local config にあれば、本文の分断 CAB と最終 `Foo:` が件数相殺する。テストは tmp repo の config を作るだけで、実際の parser cwd `/` に hostile local config がある条件を検査していない。`Path("/")` の literal assert は穴を固定している。
- 放置時の受理集合: root repo の alias により分断 CAB を受理し、separator/key 設定によって正常形を拒否する。全3モードがホスト依存になる。
- 最小fix: private な fresh temporary directory を parser cwd にし、そこを ceiling として repo discovery を遮断する。hostile ancestor/current repo config を置いたテストへ置換する。

### A-3 — canonical parser が CAB policy 前の AI-Agent 検査へ遡及している

- severity: **HIGH / must-fix**
- real/refuted: **real**
- file:line: [brief.md:9](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/brief.md:9)、[author.patch:589](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/author.patch:589)、[check_ai_provenance.py:151](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:151)、[check_ai_provenance.py:354](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:354)
- CAB findingだけが ancestry gate を通る。AI-Agent の base/scope/author は全履歴で新しい `--no-divider`・canonical config parserへ切り替わる。
- pre-policy message でも、`AI-Agent` の後に `---` と本文がある形は旧 parser の受理から新 parser の拒否へ、本文の `---` 後に最終 AI-Agent がある形は旧拒否から新受理へ変わる。
- 放置時の受理集合: CAB policy 導入前の default/range 履歴について、AI-Agent・scope・Codex author の既存受理集合が双方向に変化する。author報告の「495件、違反なし」は現物標本の互換観測であり、集合非遡及の証明ではない。
- 最小fix: 履歴では CAB policy 適用可否を先に決め、pre-policy commit の AI検査は legacy parser、policy commit以後と `--message-file` は canonical parserにする。別案として parser 移行を独立した受理集合変更として再裁定し、専用 cutoff と新Dを設ける。

### A-4 — `git log -S` は宣言した ancestry 全体・rename を見ていない

- severity: **HIGH / must-fix**
- real/refuted: **real**
- file:line: [check_ai_provenance.py:221](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:221)、[adjudication-plan-v2.md:9](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/adjudication-plan-v2.md:9)、[test_check_ai_provenance.py:425](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_ai_provenance.py:425)
- path付き `git log` の既定 history simplification は、最終treeへ寄与しない side branch を剪定する。したがって「祖先に policy change があるが merge resolution で落とされた」履歴を見逃し得る。
- rename detection 有効時、needleを含むファイルを `POLICY_PATH` へ内容不変renameすると `-S` の出現数は変わらず、`--follow` もないため旧pathの導入まで辿れない。さらに `diff.renames` の ambient config で結果が変わる。
- 放置時の受理集合: rename導入後または剪定されたpolicy branchのmerge後に、分断 CAB commitをpre-policy扱いして受理する。
- 最小fix: 少なくとも `git log --full-history --no-renames ... -S ... -- POLICY_PATH` とし、rename-in/out、policyを残す/落とすmerge、needle 0→2→1、`diff.renames` true/falseを固定する。

### 反証・非blocker

- **`--no-divider` 自体:** refuted。commit message の最終 block 解釈として正しく、正負テストもある。ただし適用epochはA-3で未解決。
- **raw regex:** refuted。SP/HTAB、case-insensitive、colon前空白、indent、bullet/quoteの現挙動はplan v2と一致する。fence内候補の独立テスト欠落は成果物値を現在変えないため nit/backlog。
- **AI-Agent/CAB finding併存:** refuted。[check_ai_provenance.py:153](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:153) でCABを先に保持し、欠落・形式・scope・`none` の早期returnでも返している。
- **message-file/default/range:** A-3を除けば refuted。message-file常時適用、pre-policy range受理、post-policy default/range拒否は別々に配線されている。
- **Git error:** refuted。parser・ancestry `_git` の非zeroは `RuntimeError` となり、mainでrc=2へ閉じる。
- **追加・削除・別lineage・needle複数:** rename/merge以外は実装上成立する。`bool(commits)` は複数hitを保持するが、複数needleの境界テスト欠落は nit。A-4 fix時に同梱すべき。
- **予算面:** refuted。[check_docs.py:162](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_docs.py:162) の独立registry、[check_docs.py:1466](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_docs.py:1466) のconsumer合流、9000/9001、allowlist非拡張はいずれも静的に整合する。

### 帰属・所有

**PASS。** [author-prompt.txt:11](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/author-prompt.txt:11) の所有4ファイルとpatchの4ファイルは一致し、現作業木のtracked差分も同じ4ファイルだけでした。`author.patch` は現差分と byte-for-byte 一致し、docs・commit・所有外実装ハンクはありません。Codex author不在ハンクを示す証拠はなく、untrackedなwave artifactは親所有の記録面です。authorのテスト成功報告は読んだだけで、本レビューの緑主張には採用していません。

## 総括

**NO-GO。** must-fix は4件です。第一に、Git出力へ保持されるbare CR等をPythonの`splitlines()`が新しいkey行として誤分解し、本文側の分断CABと偽parsed CABを件数相殺できるため、現gateの中心命題が直接破れています。第二に、cwd `/` は現在たまたまrepository外でも、`/.git`の不在を契約化できず、root local configによるalias相殺を閉じていません。第三に、CAB findingだけをepoch gateへ通す一方、共用canonical parserをAI-Agent・scope・Codex-authorの全旧履歴へ適用しており、briefの非遡及不変条件に反します。第四に、path限定の既定`git log -S`はhistory simplificationとrename detectionにより、plan v2が宣言した「各commitの全ancestryにあるchange」を表していません。追加・削除・線形別lineage、mode分岐、Git error、予算registry、raw grammar、finding併存は上記例外を除いて成立しています。実装帰属はGOで、patch全ハンクがCodex author unitの所有4ファイルに収まり、所有外変更はありません。しかし帰属が正しくてもcommit provenanceの機械受理集合には実際のfail-openと無裁定の遡及変更が残るため、このsnapshotをfix・焦点再レビュー前に段7へ送ってはいけません。編集およびpytest実行は行わず、検査緑も主張しません。