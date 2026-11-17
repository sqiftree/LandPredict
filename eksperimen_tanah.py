"""CLI kompatibel; model dan evaluasi berada dalam package tanah."""
from tanah.config import FEATURES, KEY, ROOT, TARGET
from tanah.experiment import main, run
from tanah.models import LocalSingularError, estimate

if __name__ == '__main__':
    main()
