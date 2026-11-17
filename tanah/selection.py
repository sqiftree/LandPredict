"""Nested regional validation; only outer-training indices reach selection."""
import numpy as np

from .models import LocalSingularError, estimate


def region_splits(groups, indices=None):
    """Yield (held-out region, training indices, validation indices)."""
    indices = np.arange(len(groups)) if indices is None else np.asarray(indices)
    for region in np.unique(groups[indices]):
        mask = groups[indices] == region
        yield region, indices[~mask], indices[mask]


def select_parameter(model, candidates, train, groups, x, y, distances, outer_region, audit):
    if len(candidates) == 1:
        return candidates[0]
    losses = []
    for parameter in candidates:
        errors = []
        failed = False
        for validation_region, fit, validation in region_splits(groups, train):
            try:
                predicted = estimate(model, parameter, fit, validation, x, y, distances)
                errors.extend(abs(y[validation] - predicted))
            except LocalSingularError as exc:
                failed = True
                audit['singular_failures'].append({
                    'stage': 'inner', 'outer_region': outer_region,
                    'validation_region': validation_region, 'parameter': parameter, 'error': str(exc),
                })
        loss = float(np.mean(errors)) if not failed else None
        audit['inner_scores'].append({
            'model': model, 'outer_region': outer_region, 'parameter': parameter,
            'MAE_Rp_m2': loss, 'valid': not failed,
        })
        losses.append(loss if loss is not None else np.inf)
    if not np.isfinite(losses).any():
        audit['status'] = 'failed_all_candidates_singular'
        raise LocalSingularError(f'Semua kandidat {model} gagal pada lipatan {outer_region}.')
    return candidates[int(np.argmin(losses))]
