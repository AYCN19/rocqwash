theorem lp_mirror_funext : ∀ (A B : Type) (f g : A → B), (∀ x, f x = g x) → f = g :=
  fun f g h => funext h
