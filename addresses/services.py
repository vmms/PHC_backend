from decimal import Decimal
from django.utils import timezone
from geopy.geocoders import Nominatim


ADDRESS_FIELDS = [
    "street",
    "city",
    "state",
    "zip_code",
    "country",
]


def build_address_query(address):
    parts = [
        address.street,
        address.zip_code,
        address.city,
        address.state,
        address.country,
    ]

    return ", ".join([str(p).strip() for p in parts if p])


def get_address_snapshot(address):
    if not address:
        return None

    return {
        field: getattr(address, field)
        for field in ADDRESS_FIELDS
    }


def address_has_changed(old_snapshot, address):
    if not address:
        return False

    new_snapshot = get_address_snapshot(address)

    return old_snapshot != new_snapshot


def geocode_address(address):
    query = build_address_query(address)

    if not query:
        return address

    try:
        geolocator = Nominatim(
            user_agent="PHC_backend_geocoder"
        )

        location = geolocator.geocode(
            query,
            timeout=10
        )

        if not location:
            return address

        address.latitude = Decimal(str(location.latitude))
        address.longitude = Decimal(str(location.longitude))
        address.geocoded_at = timezone.now()

        address.save(update_fields=[
            "latitude",
            "longitude",
            "geocoded_at",
        ])

    except Exception:
        return address

    return address