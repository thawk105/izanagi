# T-146 段 6 review 裁定

- review 2本は rc=0 / 形式 gate pass、双方 NO-GO。
- fix 前 snapshot は一時 patch `s6-pre-fix-integrated.patch` として採取し、
  sha256 `6b49e9dde92d73381af5937f52f4e501fdc967670fb291bae2b6ccb278efa0e7` を確認した。
  恒久記録には patch 自体を含めず、この hash と以下の裁定を残す。
- real / blocker: bind が pathname を作らず失敗した場合も `getsockname()` を要求し、既存 sandbox の
  exact-reason SKIP を EPERM failure へ承認なく縮小した。
- fix: bind failure 後に nofollow で pathname を観測し、不在なら ownership syscall を呼ばず `False`。
  present の場合だけ bound address を観測する。既存 bind-failure test は `getsockname()` が呼ばれない
  ことを load-bearing にする。
- real / blocker: 現 EPERM/EIO fixture は pathname present のため、M-T146-B
  (`except FileNotFoundError` → `except OSError`) が同じ例外を再送出して等価になる。
- fix: EPERM/EIO は real unlink 後に元例外を投げる断面へ変更する。FNF-present と pending `False`
  の FNF-after-real-unlink も追加し、例外種別 × pathname状態 ×元 verdict を閉じる。
- real / blocker: `-rf -rs` は後者が勝ち FAILED node を失う。targeted / mutation は `-rfs` を使い、
  rc、FAILED、SKIPPED node/reasonを分離記録する。
- real / recording: pre-fix は旧穴3、FNF分岐のregression guard、既存identity再固定＋新policyを
  別分類し、全 parameterを同じ新規欠陥として数えない。
- refuted: M-T146-A / C の帰属、direct pathname観測、plain runner / xdist / full runner到達、
  preexisting FileExistsError policy。
- scope 外: close→unlink順序pin、arbitrary close複合fault、hostile writer、production partial-bind。
  現 test acceptance / product artifactに追加影響を書けないため must-fixへ昇格しない。
- fix は helperと同じparameter matrixが相互依存するため、所有1ファイルの単一 workspace-write
  authorへ返す。
