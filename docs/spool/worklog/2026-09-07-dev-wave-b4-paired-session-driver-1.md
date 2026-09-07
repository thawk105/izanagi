---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-b4-paired-session-driver
seq: 1
title: B-4 対照対 driver を候補と参照の 1 session 形へ直し、reference 数と D の式を凍結する (コード + docs、branch worktree-dev-wave-b4-paired-session-driver)
---

## 本文

D1699 の実装 wave。設計判断は {{D:b4-paired-session-is-the-probe-bracket}}、
{{D:b4-mid-probe-preserves-detection}}、{{D:b4-freeze-binds-self-consistency-only}}。
一次資料は `output/insights/2026-09-07_b4-paired-session-driver/`。

**起動時の重複検査 (依頼が明示的に要求):** 稼働 worktree 全件を対象 2 file の pathspec に絞って
走査し、未着地の変更を持つ worktree は 0 件だった。`.codex/worktrees/t2341-author` だけが作業ツリーに
差分を持つが、両 file とも内容 hash が main の blob と一致する着地済みの残骸である。
走査中に一時的に引っかかった B-4 の 2 worktree は `worktree add` の進行中で、完了後は clean だった。
低速な全件走査と高速な pathspec 走査の 2 本で同じ結論を得た。

**並行 wave との面の調整:** T-2140 (§5 floor 欄の発効) は D1695 / D1699 が未着地であることを
理由に自ら降りた。事前登録文書側の wave は §5.1.1 を 1 byte も触らないと明言し、§11.2 の
費用の目安には「内訳は D1699 後に組み替えになるので実装確定後に書き直す」と明記して着地した。
床値の読み手側の wave は本 wave の 2 file を編集しないと明言し、schema 版が上がったときは
**未知の版を fail-closed で拒否する**設計にすると回答した。

**親の実測事実の誤りを段 3 が 2 件暴いた。** (1) summary の consumer は現時点で**存在しない**
(`p3_b4_material_report.py:242` が `floor=None` を無条件に渡す)。「唯一の consumer」は将来の
consumer だった。(2) 「main 全体で pin は 2 台帳だけ」は不正確で、変更対象のテスト自身も
schema 識別子を literal pin していた。いずれも設計判断は変えなかったが、記録として残す。

**棄却した所見:** 段 3 の「2 回の測定呼び出しを 1 区間で包むのは D1699 が却下した読み替えの
再実施である」は却下した。根拠は {{D:b4-paired-session-is-the-probe-bracket}} に書いた背理である。
段 3 の「床値と受理集合の単調性が逆」も却下した。所見は受理集合を tie 集合と読んでいたが、
指示対象は certified として受理される主張の集合である。床値 0 はどんな微差も雑音とみなさない
ことを意味し、雑音水準の差が実在の勝ちとして certified されるので受理集合は広がる。
段 6 の 3 件 (finalizer の probe status 再導出、読み込み後 spec の差し替え、binary の TOCTOU) は
いずれも base 版に同型が存在することを現物で確認し、本 wave の後退ではないとして scope 外にした。

**セッション異常:** 段 5 の実装子が model call 上限 100 に当たり SIGTERM で停止した
(`stop_reason=max_model_calls`)。ただし実装自体は完成しており、止まったのは最終報告の作成中だった。
親が作業ツリーを検査し、焦点走 245 件緑と裁定 8 項目の充足を現物で確認して採用した。
call を浪費した要因は 2 つで、context 不一致による `apply_patch` の再試行と、
子が自前の smoke test を heredoc で走らせようとして guard に拒否されたことである。
段 6 の fix 子には「テストの実走は親が行う。guard に拒否されたらそれ以上 call を使わず
未実走と書け」と明記し、上限を 200 へ上げた。fix 子は 1 回で完走した。

**受入 1 回目の非帰属赤 8 件と、その判定根拠 (DW-O18)。** 受入全走 1 回目は
8 failed / 21293 passed / 68 skipped で rc=70 (`reason=child-verdict`) だった。
赤 8 件はすべて `orchestrator/tests/test_codex_worker_launch.py` である。**非帰属と判定した。**

1. 本 wave の差分は `orchestrator/campaign/floor_pair_driver.py` と
   `orchestrator/tests/test_floor_pair_driver.py` の 2 file だけで、赤の対象である
   `tools/codex_worker_launch.py` を 1 byte も変えていない。共有 fixture も変えていない。
2. 同一 tip で当該 file を単独再走したところ **8 件中 7 件が緑**になり、再現しなかった。
3. 再現した 1 件 `test_manifest_is_appended_while_correlated_session_is_running` は、
   実プロセスを起動して **3 秒だけ** manifest の出現を待つ時間依存テストである
   (`deadline = time.monotonic() + 3`)。判定時点の login node は load average 5.62 で、
   他 wave の `run_tests.py` が 23 本、codex 子が 3 本走っていた。
   署名一致ではなく assertion 本文 (`assert (None is not None)`、manifest 不出現) と
   実時間予算の構造から判定した。

同一 tip で受入を 1 回だけ再走する。

## 次の一手差分

### 新規

- {{T:b4-frozen-spec-hash-fixed-point}} **P1・新規 (段 3 の敵対相談が暴き、親が現物で確認)**:
  B-4 の凍結 spec は実リポジトリ上で作成できない。`load_frozen_spec` が
  「spec bytes == HEAD の blob」(`floor_pair_driver.py:1137-1139`) と
  「spec 内 `provenance.source_commit` == HEAD」(同 `:1182-1186`) を同時に要求するため、
  追跡 file である spec が自分自身を含む commit の hash を自分の中に書くことになり、
  hash の不動点になる。テストが緑なのは偽の VCS が定数を返すためである。
  **現状 driver は production で spec を 1 度も load できず、B-4 床値の実走を開始できない。**
  provenance 束縛の設計択一 (source_commit を親 commit へ束ねる / blob hash だけで束ねる /
  HEAD が source_commit の子孫であることを要求する 等) はユーザー手番。
- {{T:b4-rep-interleaved-measurement}} **P2・新規 (段 3 の敵対相談)**:
  side session の区間内で候補の全 rep が参照の全 rep に先行するため、区間内ドリフトが
  相殺されない。rep 単位で交互に測ればより強く相殺できる。D1699 は要求しておらず、
  D1641 §11.1 が測定手順の決定主体をユーザーに置いているため実装していない。
- {{T:b4-prereg-cost-paragraph-recomposition}} **P2・新規**:
  事前登録 §11.2 の費用の目安の段落を、reference が pair-sample あたり 2 件になった構成へ
  書き直す。加算ではなく内訳の組み替えになる。別 wave が数値だけを当て、構成の記述は
  本件の裁定範囲として括弧ごと残してある。**正式標本の実走前に必要。**
- {{T:b4-preexisting-floor-driver-gaps}} **P3・新規 (段 6 の敵対レビュー、いずれも base から存在)**:
  finalizer が probe の status を raw の returncode / stdout / stderr から再導出しない、
  読み込み後の spec を `dataclasses.replace` で差し替えられる、binary の hash 検査から spawn までに
  path が差し替わりうる、`probe_fn` が caller から差し替えられる、の 4 件。
  本 wave の後退ではないので scope 外とした。閉じるかどうかは別の裁定。
- {{T:b4-probe-completeness-pair-coverage}} **P3・新規 (変異走行の両層同時変異)**:
  finalizer の probe 3 件完備検査と、それを mask する `_probe_payload_status` の None 拒否は
  互いに冗長で、両層を同時に外すと通る。出荷コードはどちらか一方で必ず弾くので保護されているが、
  **その対を同時に検査するテストが無い。** 事前登録した KILLED 期待は満たされなかった。
