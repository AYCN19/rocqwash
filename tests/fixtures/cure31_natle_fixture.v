(* cure31 fixture — nat-le premise lift and drop-wrap forms (cure_pack v1.1
   cure13/cure14), mirroring the red-station shapes of the 20261103 wash
   campaign (premise lift + bridge wrap at the consumption point; the
   constant-tail exact station must stay untouched by the intros-tail guard). *)

Theorem abg_gnprf_replay : forall f pf k,
  (gnPrf f pf <= k)%nat -> NatOK f pf k.
Proof.
  intros f pf k Hk.
  split.
  - exact (gnPrf_replay f pf k Hk).
  - apply loeb_tid_eq. exact (gnPrf_replay_eq abg_fzz abg_axz).
Qed.

Theorem natle_pair : forall n m : nat, (n <= m)%nat -> n < m.
Proof.
  intros n m H. apply Nat.lt_le_trans with m. apply Nat.le_refl. exact H.
Qed.
