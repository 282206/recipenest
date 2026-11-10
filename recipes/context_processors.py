from django.conf import settings
from django.db import DatabaseError

from .views import cuisine_counts, home_url


def site(request):
    """Values every page needs: footer cuisine links and the Quick browse / Rate page addresses."""
    try:
        footer = [(info, home_url({}, cuisine=info["name"])) for info, _ in cuisine_counts()]
    except DatabaseError:   # before `migrate` has been run
        footer = []
    return {
        "footer_cuisines": footer,
        "QUICK_BROWSE_URL": settings.QUICK_BROWSE_URL,
        "RATE_URL": settings.RATE_URL,
    }
