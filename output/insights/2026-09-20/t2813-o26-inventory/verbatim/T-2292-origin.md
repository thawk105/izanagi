- [T-2292] **P2・新規**: DW-O26 の「新規 test file を足す走は file 集合
  列挙のメタテストも焦点走に含める」は範囲が狭い。subprocess を起動する module を足すと、
  process 起動一覧と subprocess guard も落ちる (本 wave の受入で 4 件中 3 件がこれ)。
  DW-O26 は節全体が exact 契約で pin されているため、契約側の更新とセットで行う必要がある。
