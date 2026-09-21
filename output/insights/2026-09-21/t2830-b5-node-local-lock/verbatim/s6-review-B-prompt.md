単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/verbatim/integrate-204eb77e6.diff — **レビュー対象** (統合 commit 204eb77e6 の全差分)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/s4-adjudication.md — 段 4 裁定・プラン v2・変異事前登録 (採らないと決めたものの一覧を含む)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/verbatim/T-2830-origin.md — 依頼の逐語 (「本題だけ。gate・検査・台帳の追加は scope 外」)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/brief.md — 親 brief (追補 2 まで)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/codex/s5-author-A1.md — author A1 の最終報告。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/codex/s5-author-A2.md — author A2 の最終報告。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/focus-f1.log — 親が実走した焦点走の log。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/tools/pegasus/b5_contrast_launch.py — 統合後。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/tools/pegasus/README.md — 統合後 (B-5 の節)。読めなければ即停止

## 親が実走したもの (この範囲だけが実測、他は未実走)

- 焦点走 f1 (計算ノード、統合 commit 204eb77e6 の木、12 file): rc=0、2,074 passed / 9 skipped、失敗 0。
- `check_docs.py` 違反なし、全史 provenance 監査 rc 0。変更 test 2 本の単独走 f2 は走行中。変異 matrix は未実走。

## レンズ B: 過剰・削除 (段 3 と同じレンズ、固定)

依頼は「本題だけ。gate・検査・台帳の追加は scope 外」。実装を守らせず検査する。各項目を real (過剰・誤り) / refuted で判定し、根拠を示す。

1. **プラン v2 を超えた変更:** 差分に、v2 に無い変更 (新しい検査・互換層・一般化・防御的コード・不要な import・docstring の過剰な書換え) はあるか。
   `from collections.abc import Mapping` の追加や型注釈の変更は、周辺コードの流儀に照らして必要か。
2. **test の過剰:** 追加した assert・helper (`_read_driver_environment`、runner 内の env 照合、main dry-run の出力比較) のうち、
   登録変異 (M1〜M9) の検出にも既存 3 経路の固定にも寄与しないものはあるか。削れるなら「残す最小の差分」を書く。
3. **test の不足による過剰な主張:** 逆に、README や commit message が test の検査範囲を超えて主張していないか
   (例: 「node-local lock が効く」「本走が投入可能」を、fake driver の環境伝播しか見ていない test で言っていないか)。
4. **README:** 追記した文は、依頼・裁定の範囲を超えていないか (新しい手順・義務・運用規則を作っていないか)。短くできるか。
5. **scope 外の記録:** s4-adjudication の「scope 外の記録」(path 重複拒否をしない、本走 launcher の一般化は別手番) は妥当か。
   実装がそれに反して一部を入れていないか。

## 制約

- sandbox は read-only で書込可能な tmp が無い。**静的検査だけでよい。** 実走していない事柄を「確認した」と書かない。
- 新しい gate・検査・台帳の提案は scope 外と明記し、裁定パッケージ候補として分けて返す。
- 予算が尽きそうなら、途中までの結論を出力形式どおりに書いて終える。

## 出力形式

項目 1〜5 を見出しで分け、各項目に判定と根拠。削る提案は「残す最小の差分」として具体的に。最後に `## 総括`。
