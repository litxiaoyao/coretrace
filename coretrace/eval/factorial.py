"""Paired source-cluster estimates for mass × conditional interventions."""

def summarize_factorial(rows, *, seed=42, bootstrap_reps=2000):
    import numpy as np
    arms = ['native', 'mass_only', 'conditional_only', 'both']
    tables = {arm: {r['id']: r for r in rows if r['method'] == arm} for arm in arms}
    ids = sorted(tables['native'])
    if not ids or any(set(tables[arm]) != set(ids) for arm in arms):
        raise ValueError('Complete paired factorial arms required')
    values = np.array([[int(tables[arm][i]['correct']) for arm in arms] for i in ids])
    groups = {}
    for index, identifier in enumerate(ids):
        cluster = tables['native'][identifier]['cluster_id']
        if any(tables[arm][identifier]['cluster_id'] != cluster for arm in arms):
            raise ValueError('Factorial cluster assignments differ')
        groups.setdefault(cluster, []).append(index)
    parts = list(groups.values())
    sizes = np.array([len(g) for g in parts])
    contrasts = {
        'mass_effect_receiver_conditional': values[:, 1] - values[:, 0],
        'mass_effect_donor_conditional': values[:, 3] - values[:, 2],
        'conditional_effect_native_mass': values[:, 2] - values[:, 0],
        'conditional_effect_fixed_mass': values[:, 3] - values[:, 1],
        'interaction': values[:, 3] - values[:, 1] - values[:, 2] + values[:, 0],
    }
    rng = np.random.default_rng(seed)
    draw = rng.integers(0, len(parts), (bootstrap_reps, len(parts)))
    report = {}
    for name, delta in contrasts.items():
        sums = np.array([delta[g].sum() for g in parts])
        distribution = sums[draw].sum(1) / sizes[draw].sum(1)
        report[name] = dict(estimate=float(delta.mean()),
                           paired_cluster_CI95=np.quantile(distribution, [.025, .975]).tolist())
    return dict(n=len(ids), clusters=len(parts), contrasts=report,
                bootstrap_seed=seed, bootstrap_reps=bootstrap_reps,
                interaction_formula='Accuracy(both) - Accuracy(mass_only) - Accuracy(conditional_only) + Accuracy(native)',
                population='Shared-context discovery quadruplets; paired diagnostic, not independent test generalization')
